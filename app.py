from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3

from ml.parser import extract_text_from_pdf, extract_entities
from ml.matcher import calculate_match_percentage
from ml.gpt_feedback import get_resume_feedback, rewrite_resume_for_job
# Flask setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

# File extension checker
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class
class User(UserMixin):
    def __init__(self, id_, email, password):
        self.id = id_
        self.email = email
        self.password = password

def get_user_by_email(email):
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return User(*row) if row else None

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database/users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return User(*row) if row else None

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user_by_email(request.form['email'])
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('upload'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect('database/users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        conn.close()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        resume_file = request.files.get('resume')
        jd_file = request.files.get('job_description')
        jd_text_input = request.form.get('jd_text')
        jd_text = ""

        # Handle resume upload
        if not resume_file or not allowed_file(resume_file.filename):
            flash('Invalid or missing resume file.')
            return redirect(request.url)

        resume_filename = secure_filename(resume_file.filename)
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
        resume_file.save(resume_path)
        resume_text = extract_text_from_pdf(resume_path)
        resume_skills = extract_entities(resume_text)

        # Handle JD file or pasted text
        if jd_file and allowed_file(jd_file.filename):
            jd_filename = secure_filename(jd_file.filename)
            jd_path = os.path.join(app.config['UPLOAD_FOLDER'], jd_filename)
            jd_file.save(jd_path)

            print("[DEBUG] JD file saved at:", jd_path)

            try:
                with open(jd_path, 'r', encoding='utf-8') as f:
                    jd_text = f.read()
                print("[DEBUG] Extracted JD text from TXT:", jd_text[:300])
                print("[DEBUG] JD file size:", os.path.getsize(jd_path))
                print("[DEBUG] JD text raw (repr):", repr(jd_text[:300]))

            except Exception as e:
                print("[ERROR] Failed to read JD file:", str(e))
                flash("Error reading job description file.")
                return redirect(request.url)

        #     if jd_filename.lower().endswith('.pdf'):
        #         jd_text = extract_text_from_pdf(jd_path)
        #     else:  # .txt
        #         with open(jd_path, 'r', encoding='utf-8') as f:
        #             jd_text = f.read()
        #             print("[DEBUG] Extracted JD text from TXT:", jd_text[:300])

        # elif jd_text_input and jd_text_input.strip():
        #     jd_text = jd_text_input.strip()
        #     print("[DEBUG] Extracted JD text from textarea:", jd_text[:300])

        # else:
        #     flash('Please upload a JD file or paste JD text.')
        #     return redirect(request.url)

        # print("JD TEXT PREVIEW:", jd_text[:300])  # Debugging output
        jd_skills = extract_entities(jd_text)
        try:
            gpt_suggestions = get_resume_feedback(resume_text, jd_text)
        except Exception as e:
            print("[DEBUG] GPT Error:", e)
            gpt_suggestions = "⚠️ GPT feedback could not be generated due to quota limits."
        


        def calculate_match_percentage(resume_skills, jd_text):
            jd_skills = extract_entities(jd_text)
            matched_skills = list(set(resume_skills).intersection(set(jd_skills)))
            match_percent = (len(matched_skills) / len(jd_skills)) * 100 if jd_skills else 0
            print("[DEBUG] Resume skills:", resume_skills)
            print("[DEBUG] JD skills:", jd_skills)
            print("[DEBUG] Matched skills:", matched_skills)
            print("[DEBUG] Match percentage:", match_percent)
            return match_percent, matched_skills
        match_percentage, matched_skills = calculate_match_percentage(resume_skills, jd_text)



        return render_template("dashboard.html",
                               resume_text=resume_text,
                               jd_text=jd_text,
                               skills=resume_skills,
                               matched_skills=matched_skills,
                               match_percent=match_percentage,
                               gpt_feedback=gpt_suggestions)

    return render_template('upload.html')



@app.route('/rewrite-resume', methods=['POST'])
@login_required
def rewrite_resume():
    data = request.get_json()
    resume_text = data.get('resume_text', '')
    jd_text = data.get('jd_text', '')
    if not resume_text or not jd_text:
        return jsonify({'error': 'Missing resume or job description text.'}), 400
    try:
        rewritten = rewrite_resume_for_job(resume_text, jd_text)
        return jsonify({'rewritten_resume': rewritten})
    except Exception as e:
        return jsonify({'error': f'AI rewrite failed: {str(e)}'}), 500


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect('database/users.db')
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, password TEXT)")
    conn.close()
    app.run(debug=True)

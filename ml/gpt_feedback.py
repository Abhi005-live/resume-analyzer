import google.generativeai as genai
import os
from dotenv import load_dotenv

def _get_model():
    load_dotenv(override=True)
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    return genai.GenerativeModel("gemini-1.5-flash")

def get_resume_feedback(resume_text, jd_text):
    model = _get_model()
    prompt = f"""You are an expert resume advisor. Given the resume and job description below, give 4 lines of constructive feedback for improvement.

Resume:
{resume_text}

Job Description:
{jd_text}

Feedback:"""
    response = model.generate_content(prompt)
    return response.text.strip()


def rewrite_resume_for_job(resume_text, jd_text):
    model = _get_model()
    prompt = f"""You are an expert resume writer. Rewrite the resume below so it is perfectly tailored to the job description.
- Keep all real experience and skills, but rephrase bullet points to match JD keywords.
- Add a strong professional summary at the top targeting this role.
- Highlight the most relevant skills prominently.
- Use ATS-friendly formatting (plain text, clear sections).
- Do NOT fabricate experience or skills.

Resume:
{resume_text}

Job Description:
{jd_text}

Rewritten Resume:"""
    response = model.generate_content(prompt)
    return response.text.strip()

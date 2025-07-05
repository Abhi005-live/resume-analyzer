import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text

def extract_entities(text):
    skills = []
    with open('ml/skills.txt', 'r', encoding='utf-8') as f:
        skill_set = set([line.strip().lower() for line in f if line.strip()])

    text_lower = text.lower()

    for skill in skill_set:
        if skill in text_lower:
            skills.append(skill)
    return skills
    print("Extracted skills:", skills)



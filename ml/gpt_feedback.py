import openai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=api_key)

def get_resume_feedback(resume_text, jd_text):
    prompt = f"""You are an expert resume advisor. Given the resume and the job description below, give 4 lines of constructive feedback for improvement.

Resume:
{resume_text}

Job Description:
{jd_text}

Feedback:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content.strip()

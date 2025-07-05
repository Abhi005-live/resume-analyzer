# ml/matcher.py

def calculate_match_percentage(resume_skills, jd_skills):
    if not resume_skills or not jd_skills:
        return 0

    resume_skills_set = set([skill.lower() for skill in resume_skills])
    jd_skills_set = set([skill.lower() for skill in jd_skills])

    matched_skills = resume_skills_set.intersection(jd_skills_set)
    match_percentage = (len(matched_skills) / len(jd_skills_set)) * 100

    return round(match_percentage, 2)

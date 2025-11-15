import re
from typing import Dict
import os
from langdetect import detect
import json



import scoring.education_scoring as ec
import scoring.experience_scoring as ex
import scoring.technical_skill_scoring as ts
import scoring.soft_skills_scoring as ss
import scoring.tools_and_certificates_scoring as tc



def clean_text(text: str) -> str:
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def extract_field(block: str, field_name: str) -> str:

    pattern = rf"{field_name}\s*:\s*(.*?)(?=\n\w+?:|\Z)"
    match = re.search(pattern, block, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return clean_text(match.group(1))
    return ""


def parse_candidate_block(block: str) -> Dict[str, str]:

    filename = extract_field(block, "filename")
    file_size = extract_field(block, "file_size")
    mimetype = extract_field(block, "mimetype")
    cv_summary = extract_field(block, "cv_summary")
    full_name = extract_field(block, "full_name")
    phone = extract_field(block, "phone")
    email = extract_field(block, "email")
    address = extract_field(block, "address")
    
    education_text = extract_field(block, "education")
    experience_text = extract_field(block, "experience")
    hard_skills = extract_field(block, "hard_skills")

    # Soft skills có thể nằm ở personal_skills hoặc tương tự
    soft_skills_text = extract_field(block, "personal_skills")
    if not soft_skills_text:
        soft_skills_text = extract_field(block, "soft_skills")

    # certificates gồm reference / certifications / awards
    certificates_text = " ".join([
        extract_field(block, "certificates"),
        extract_field(block, "awards"),
    ])
    
    #tools
    tools_text = " ".join([
        extract_field(block, "tools"),
    ])

    # Summary gồm objective + cv_summary + summary
    summary_text = extract_field(block, "cv_summary")
    activities_text = extract_field(block, "activities")

    return {
        "filename": filename,
        "file_size": file_size,
        "mimetype": mimetype,
        "cv_summary": cv_summary,
        "full_name": full_name,
        "phone": phone,
        "email": email,
        "address": address,
        "experience": experience_text,

        "education": education_text,
        "hard_skills": hard_skills,
        "soft_skills": soft_skills_text,
        "activities": activities_text,
        "certificates" : certificates_text,
        "tools": tools_text,
        "summary": summary_text,
    }


def get_last_candidate(file_path: str) -> Dict[str, str]:
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Tách theo đường kẻ ----------------------------------------
    blocks = re.split(r"-{5,}", content)
    blocks = [b.strip() for b in blocks if b.strip()]

    if not blocks:
        raise ValueError("Không tìm thấy ứng viên nào trong file")

    last_block = blocks[-1]
    return parse_candidate_block(last_block)

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang  # 'vi', 'en', 'fr', ...
    except:
        return 'unknown'






def main():
    filename = 'demo_data.csv'
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../results/{filename}'))
    candidate = get_last_candidate(file_path)
    
    #------- Extracted fields -------
    candidate_file = candidate["filename"]
    candidates_filesize = candidate["file_size"]
    candidate_mime_type = candidate["mimetype"]
    candidate_cv_summary = candidate["cv_summary"]
    candidate_name = candidate["full_name"]
    candidate_phone = candidate["phone"]
    candidate_email = candidate["email"]
    candidate_address = candidate["address"]
    candidate_experience = candidate["experience"]
    candidate_education = candidate["education"]
    candidate_hard_skills = candidate["hard_skills"]
    candidate_soft_skills = candidate["soft_skills"]
    candidate_activities = candidate["activities"]
    candidate_certificates = candidate["certificates"]
    candidate_tools = candidate["tools"]
    
    jd_certificates = "We are hiring a Marketing Manager with experience in business management, finance, and digital marketing."
    jd_experiences = """
    We are looking for a Backend Developer with experience in PHP, Laravel, and MySQL.
    The candidate should have knowledge of API development, teamwork, and React integration.
    """
    jd_technical_skills = {
        'title': 'Senior Backend Developer',
        'requirements': 'Required: PHP, Laravel, MySQL. Prefer: Docker, AWS',
        'skills': 'PHP Laravel MySQL REST API'
    }
    jd_soft_skills = 'Looking for candidate with strong leadership and communication skills'
    jd_tools_and_certificates ={
        'requirements': """
        Tools:
        - Version Control (Github, GitLab, Git)
        - API Testing
        - Collaboration (Jira)
        - Design (Figma)
        
        Certificates:
        - AWS Certified Solutions Architect
        - Certified ScrumMaster (CSM)
        - PMP Certification
        - IELTS 5.0
        """,
    }
    
    
    #print(detect_language(json.dumps(candidate, ensure_ascii=False)))
    print("ứng viên: ", candidate_name)
    
    #------ EDUCATION SCORING ------
    print("\n=== CHẤM ĐIỂM HỌC VẤN ===")
    print( "Tổng điểm học vấn: ",json.dumps(ec.score_education(candidate,jd_certificates)["total_score"], ensure_ascii=False, indent=4), "/ 100đ")

    
    #------ EXPERIENCE SCORING ------
    print("\n=== CHẤM ĐIỂM KINH NGHIỆM ===")
    print("Tổng điểm kinh nghiệm: ",json.dumps(ex.score_experience(candidate,jd_experiences, 250)["total_score"], ensure_ascii=False, indent=4),"/ 250đ")
    
    
    #------ TECHNICAL SKILLS SCORING ------
    print("\n=== CHẤM ĐIỂM KỸ NĂNG CHUYÊN MÔN ===")
    print("Tổng điểm Kỹ năng chuyên môn: ",json.dumps(ts.score_technical_skills(candidate,jd_technical_skills, 250)["total_score"], ensure_ascii=True, indent=4), "/ 250đ")
    
    
    #------ SOFT SKILLS SCORING ------
    print("\n=== CHẤM ĐIỂM KỸ NĂNG MỀM ===")
    print("Tổng điểm kỹ năng mềm: ",json.dumps(ss.score_soft_skills(candidate,jd_soft_skills, 150)["total_score"], ensure_ascii=False, indent=4),"/ 150đ")
    
    #------ TOOLS AND CERTIFICATES SCORING ------
    print("\n=== CHẤM ĐIỂM CÔNG CỤ VÀ CHỨNG CHỈ ===")
    print("Tổng điểm Công cụu và chứng chỉ: ",json.dumps(tc.score_tools_and_certificates(candidate,jd_tools_and_certificates, 150)["total_score"], ensure_ascii=False, indent=4), "/ 150đ")





main()
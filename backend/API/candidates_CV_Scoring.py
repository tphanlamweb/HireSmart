import re
from typing import Dict
import os
from langdetect import detect
import json



#from scoring.education_scoring import EducationScorer
import scoring.experience_scoring as ex
import scoring.technical_skill_scoring as ts

#ec = EducationScorer()



def clean_text(text: str) -> str:
    """Làm sạch chuỗi: bỏ khoảng trắng thừa, ký tự lạ."""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def extract_field(block: str, field_name: str) -> str:
    """
    Tìm đoạn text bắt đầu bằng 'field_name:' và lấy nội dung theo dòng hoặc đến khi gặp field khác.
    """
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
#------ EDUCATION SCORING ------
def scoring_education(e_data):
    jd_text = "We are hiring a Marketing Manager with experience in business management, finance, and digital marketing."
    target_description = "Ứng viên có trình độ đại học hoặc cao hơn trong lĩnh vực quản trị kinh doanh, tài chính, marketing hoặc công nghệ thông tin"
    print("e data = ",e_data)
    print("\njd text: ", jd_text, "\n\ntarget description: ", target_description,"\n")
    return 0# ec.score_education(e_data, jd_text)


def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang  # 'vi', 'en', 'fr', ...
    except:
        return 'unknown'
    
#------ EXPERIENCE SCORING ------
def scoring_experience(exp_data):
    jd_text = """
    We are looking for a Backend Developer with experience in PHP, Laravel, and MySQL.
    The candidate should have knowledge of API development, teamwork, and React integration.
    """
    print("JD : ",jd_text)
    return ex.score_experience(exp_data, jd_text, 250)

def scoring_technical_skills(cv_data):
    jd_data = {
        'title': 'Senior Backend Developer',
        'requirements': 'Required: PHP, Laravel, MySQL. Prefer: Docker, AWS',
        'skills': 'PHP Laravel MySQL REST API'
    }
    return ts.score_technical_skills(cv_data, jd_data, 250)

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
    
    
    
    
    
    #print(detect_language(json.dumps(candidate, ensure_ascii=False)))
        
    #------ EDUCATION SCORING ------
    print("\n=== CHẤM ĐIỂM HỌC VẤN ===")
    #print("final education score:", scoring_education(candidate["education"]))

    #------ EXPERIENCE SCORING ------
    print("\n=== CHẤM ĐIỂM KINH NGHIỆM ===")
    #print(scoring_experience(candidate)["total_score"])
    
    #------ TECHNICAL SKILLS SCORING ------
    print("\n=== CHẤM ĐIỂM KỸ NĂNG CHUYÊN MÔN ===")
    for key , value in scoring_technical_skills(candidate).items():
        print(f"\n{key}: {value}")

main()
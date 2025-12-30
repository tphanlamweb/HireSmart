import re
from typing import Dict
import os
from langdetect import detect
import json
import concurrent.futures
import logging

from backend.dataAndModels.config import DATABASE_URL

import backend.API.scoring.education_scoring as education_scoring
import backend.API.scoring.experience_scoring as experience_scoring
import backend.API.scoring.technical_skill_scoring as technical_skill_scoring
import backend.API.scoring.soft_skills_scoring as soft_skills_scoring
import backend.API.scoring.tools_and_certificates_scoring as tools_and_certificates_scoring
import backend.API.scoring.similarity_scoring as sim_scoring
import backend.dataAndModels.candidates_table as candidates_table
from backend.API.job_routes import build_jd_full_from_db


# def clean_text(text: str) -> str:
#     if not text:
#         return ""
#     text = str(text)
#     text = re.sub(r"[\n\r\t]+", " ", text)
#     text = re.sub(r"\s{2,}", " ", text)
#     return text.strip()

# def extract_field(block: str, field_name: str) -> str:
#     pattern = rf"{field_name}\s*:\s*(.*?)(?=\n\w+?:|\Z)"
#     match = re.search(pattern, block, flags=re.DOTALL | re.IGNORECASE)
#     if match:
#         return clean_text(match.group(1))
#     return ""

# def parse_candidate_block(block: str) -> Dict[str, str]:

#     filename = extract_field(block, "filename")
#     file_size = extract_field(block, "file_size")
#     mimetype = extract_field(block, "mimetype")
#     cv_summary = extract_field(block, "cv_summary")
#     full_name = extract_field(block, "full_name")
#     phone = extract_field(block, "phone")
#     email = extract_field(block, "email")
#     address = extract_field(block, "address")
    
#     education_text = extract_field(block, "education")
#     experience_text = extract_field(block, "experience")
#     hard_skills = extract_field(block, "hard_skills")

#     # Soft skills có thể nằm ở personal_skills hoặc tương tự
#     soft_skills_text = extract_field(block, "personal_skills")
#     if not soft_skills_text:
#         soft_skills_text = extract_field(block, "soft_skills")

#     # certificates gồm reference / certifications / awards
#     certificates_text = " ".join([
#         extract_field(block, "certificates"),
#         extract_field(block, "awards"),
#     ])
    
#     #tools
#     tools_text = " ".join([
#         extract_field(block, "tools"),
#     ])

#     # Summary gồm objective + cv_summary + summary
#     summary_text = extract_field(block, "cv_summary")
#     activities_text = extract_field(block, "activities")

#     return {
#         "filename": filename,
#         "file_size": file_size,
#         "mimetype": mimetype,
#         "cv_summary": cv_summary,
#         "full_name": full_name,
#         "phone": phone,
#         "email": email,
#         "address": address,
#         "experience": experience_text,

#         "education": education_text,
#         "hard_skills": hard_skills,
#         "soft_skills": soft_skills_text,
#         "activities": activities_text,
#         "certificates" : certificates_text,
#         "tools": tools_text,
#         "summary": summary_text,
#     }

# def get_last_candidate(file_path: str) -> Dict[str, str]:
    
#     with open(file_path, "r", encoding="utf-8") as f:
#         content = f.read()

#     # Tách theo đường kẻ ----------------------------------------
#     blocks = re.split(r"-{5,}", content)
#     blocks = [b.strip() for b in blocks if b.strip()]

#     if not blocks:
#         raise ValueError("Không tìm thấy ứng viên nào trong file")

#     last_block = blocks[-1]
#     return parse_candidate_block(last_block)

# def detect_language(text: str) -> str:
#     try:
#         lang = detect(text)
#         return lang  # 'vi', 'en', 'fr', ...
#     except:
#         return 'unknown'

def education_score(cv ,jd):
    education = education_scoring.score_education(cv, jd)
    
    return {
        "total_score": education["total_score"],
        "max_score": 100
    }

def experience_score(cv ,jd, max_score):
    experience = experience_scoring.score_experience(cv, jd, max_score)
    return {
        "total_score": experience["total_score"],
        "max_score": experience["max_score"]
    }

def technical_skill_score(cv ,jd, max_score):
    technical_skills = technical_skill_scoring.score_technical_skills(cv, jd, max_score)
    return {
        "total_score": technical_skills["total_score"],
        "max_score": technical_skills["max_score"]
    }
    
def soft_skills_score(cv ,jd, max_score):
    soft_skills = soft_skills_scoring.score_soft_skills(cv, jd, max_score)
    return {
        "total_score": soft_skills["total_score"],
        "max_score": soft_skills["max_score"]
    }

def tools_and_certificates_score(cv ,jd, max_score):
    tools_and_certificates = tools_and_certificates_scoring.score_tools_and_certificates(cv, jd, max_score)
    return {
        "total_score": tools_and_certificates["total_score"],
        "max_score": tools_and_certificates["max_score"]
    }

def sim_score(cv ,jd, max_score):
    try:
        similarity = sim_scoring.relevance_scoring(cv, jd, max_score)
        # Handle cases where relevance_scoring fails and returns None or unexpected type
        if not similarity or not isinstance(similarity, dict):
            logging.error("sim_score: invalid similarity result: %r", similarity)
            return {"total_score": 0, "max_score": max_score}

        total = similarity.get("total_score")
        maxs = similarity.get("max_score", max_score)

        if total is None:
            logging.error("sim_score: similarity missing 'total_score': %r", similarity)
            total = 0

        return {"total_score": total, "max_score": maxs}
    except Exception:
        logging.exception("sim_score: exception while computing similarity")
        return {"total_score": 0, "max_score": max_score}
    
def scoring_summary(candidate, jd_full):

    print("\n=== CHẤM ĐIỂM HỌC VẤN ===")

    # khởi pool (max_workers tùy chỉnh theo môi trường)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        f_education   = ex.submit(education_score, candidate, jd_full)
        f_experience  = ex.submit(experience_score, candidate, jd_full, 250)
        f_technical   = ex.submit(technical_skill_score, candidate, jd_full, 250)
        f_soft        = ex.submit(soft_skills_score, candidate, jd_full, 150)
        f_tools       = ex.submit(tools_and_certificates_score, candidate, jd_full, 150)
        f_sim         = ex.submit(sim_score, candidate, jd_full, 150)

        # lấy kết quả (sẽ chờ nếu chưa xong)
        education = f_education.result()["total_score"]
        print("Tổng điểm học vấn: ", json.dumps(education, ensure_ascii=False, indent=4), "/ 100đ","\nEducation:", candidate.get("education"))

        experience = f_experience.result()["total_score"]
        print("Tổng điểm kinh nghiệm: ", json.dumps(experience, ensure_ascii=False, indent=4), "/ 250đ","\nExperience:", candidate.get("experience"))

        technical = f_technical.result()["total_score"]
        print("Tổng điểm Kỹ năng chuyên môn: ", json.dumps(technical, ensure_ascii=False, indent=4), "/ 250đ","\nHard Skills:", candidate.get("hard_skills"))

        soft = f_soft.result()["total_score"]
        print("Tổng điểm kỹ năng mềm: ", json.dumps(soft, ensure_ascii=False, indent=4), "/ 150đ","\nSoft Skills:", candidate.get("soft_skills"))

        tools = f_tools.result()["total_score"]
        print("Tổng điểm Công cụ và chứng chỉ: ", json.dumps(tools, ensure_ascii=False, indent=4), "/ 150đ","\nTools:", candidate.get("tools"), "Certificates:", candidate.get("certificates"))

        sim = f_sim.result()["total_score"]
        print("Tổng điểm Tương đồng AI: ", json.dumps(sim, ensure_ascii=False, indent=4), "/ 150đ","\nSummary", candidate.get("cv_summary"))

    total_score = education + experience + technical + soft + tools + sim
    print("\n=== TỔNG ĐIỂM ỨNG VIÊN ===")
    print("Tổng điểm ứng viên: ", json.dumps(total_score, ensure_ascii=False, indent=4), "/ 1000đ")

    return total_score



def score_candidate(candidate, db=None):

    try:
        jd_full = build_jd_full_from_db(candidate.get("job_id"), db)
    except TypeError:
        # In case upstream helper signature changed, try calling without db
        jd_full = build_jd_full_from_db(candidate.get("job_id"))

    #print(detect_language(json.dumps(candidate, ensure_ascii=False)))

    return int(scoring_summary(candidate, jd_full))
    
    
#main()


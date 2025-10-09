# scoring_cv.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re
import os
import csv
import pandas as pd
import numpy as np

router = APIRouter(prefix="/scoring", tags=["CV Scoring"])
model = SentenceTransformer("all-MiniLM-L6-v2")

# =======================
# 🎯 Điểm tối đa cho từng nhóm
# =======================
#---------------------------- MOCK ----------------------------#
MAX_POINTS = {
    "education": 100,
    "experience": 200,
    "technical_skills": 300,
    "soft_skills": 100,
    "tools_and_certs": 100,
    "semantic": 200
}

# =======================
# 📌 Priority weight
# =======================
#---------------------------- MOCK ----------------------------#
PRIORITY_WEIGHT = {
    "high": 1.5,
    "medium": 1.0,
    "low": 0.5
}

# =======================
# 📝 Mock JD tiêu chí
# =======================
#---------------------------- MOCK ----------------------------#
MOCK_CRITERIA = [
    {"section": "technical_skills", "info_title": "Python", "priority": "High"},
    {"section": "technical_skills", "info_title": "React", "priority": "High"},
    {"section": "technical_skills", "info_title": "Docker", "priority": "Medium"},
    {"section": "soft_skills", "info_title": "Leadership", "priority": "Medium"},
    {"section": "soft_skills", "info_title": "Communication", "priority": "High"},
    {"section": "education_summary", "info_title": "Bachelor of Computer Science", "priority": "High"},
    {"section": "certifications_summary", "info_title": "PMP", "priority": "Low"},
    {"section": "work_experience_summary", "info_title": "Fullstack Developer 2+ years", "priority": "High"},
]

# =======================
# 🧠 CV Schema
# =======================
class ParsedCV(BaseModel):
    technical_skills: Optional[str] = ""
    soft_skills: Optional[str] = ""
    tools_and_technologies: Optional[str] = ""
    programming_languages: Optional[str] = ""
    frameworks_and_libraries: Optional[str] = ""
    work_experience_summary: Optional[str] = ""
    education_summary: Optional[str] = ""
    certifications_summary: Optional[str] = ""
    languages_summary: Optional[str] = ""
    notable_projects: Optional[str] = ""
    cv_summary: Optional[str] = ""

# =======================
# 🧹 Utils
# =======================
def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip() if text else ""

# =======================
# 🧮 Main scoring
# =======================
def score_cv_against_criteria(cv: ParsedCV):
    cv_dict = {field: normalize(getattr(cv, field, "")) for field in cv.model_fields}
    score_breakdown = {k: 0 for k in MAX_POINTS.keys() if k != "semantic"}

    # Đếm số tiêu chí theo nhóm
    group_counts = {g: 0 for g in score_breakdown.keys()}
    for c in MOCK_CRITERIA:
        section = c["section"]
        if "technical" in section:
            group_counts["technical_skills"] += 1
        elif "soft" in section:
            group_counts["soft_skills"] += 1
        elif "education" in section:
            group_counts["education"] += 1
        elif "work_experience" in section:
            group_counts["experience"] += 1
        elif "certifications" in section or "tools" in section:
            group_counts["tools_and_certs"] += 1

    # Chấm điểm từng tiêu chí
    for criterion in MOCK_CRITERIA:
        section = criterion["section"]
        keyword = normalize(criterion["info_title"])
        priority = PRIORITY_WEIGHT.get(criterion["priority"].lower(), 1.0)

        # Nhóm điểm tương ứng
        if "technical" in section:
            group = "technical_skills"
        elif "soft" in section:
            group = "soft_skills"
        elif "education" in section:
            group = "education"
        elif "work_experience" in section:
            group = "experience"
        elif "certifications" in section or "tools" in section:
            group = "tools_and_certs"
        else:
            continue

        base_points = MAX_POINTS[group] / max(group_counts[group], 1)
        if keyword in cv_dict.get(section, ""):
            score_breakdown[group] += base_points * priority

    return score_breakdown

# =======================
# 🌐 Semantic scoring
# =======================
def semantic_score(cv: ParsedCV):
    cv_text = " ".join([normalize(getattr(cv, f, "")) for f in cv.model_fields])
    jd_text = " ".join([c["info_title"] for c in MOCK_CRITERIA])

    if not cv_text or not jd_text:
        return 0

    embeddings = model.encode([cv_text, jd_text])
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return sim * MAX_POINTS["semantic"]


def load_cv_from_csv(file_path: str) -> ParsedCV:
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            raise ValueError("CSV file is empty.")
        first_row = rows[0]   # 🔸 chỉ test 1 CV
        return ParsedCV(**first_row)
    
    
    

# =======================
# 🚀 API Endpoint
# =======================
#@router.post("/")
def score_cv(cv_data: ParsedCV):
    try:
        detail_scores = score_cv_against_criteria(cv_data)
        semantic = semantic_score(cv_data)
        total_score = round(sum(detail_scores.values()) + semantic, 2)

        return {
            "total_score": float(total_score),
            "breakdown": {**detail_scores, "semantic": round(semantic, 2)}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    

    
filename = 'demo_data.csv'
csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../results/{filename}'))

print("\n\n\n\n\n\n",score_cv(load_cv_from_csv(csv_path)))


from fastapi import APIRouter, UploadFile, File, Form, Depends
from matplotlib.pylab import record
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
import httpx, json, re, pdfplumber, base64, os
from backend.src.ai import manager as ai_manager
import asyncio, random
import time
from PIL import Image
import pytesseract
import docx2txt
from io import BytesIO
from rapidfuzz import process
import backend.API.getcandidate as g
from backend.dataAndModels.config import get_db
from backend.API.getcandidate import print_candidate
from backend.dataAndModels.candidates_table import insert_candidates as insert 
import logging
import re
from typing import Dict
import os
from langdetect import detect
import json
import concurrent.futures

     # ← thêm dependency
router = APIRouter()


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
    job_id = extract_field(block, "job_id")

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
        "job_id": job_id,
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

@router.get("/test_insert_last_candidate")
def main(db: Session = Depends(get_db)):
    test_file = "/Users/thanhphan/HireSmart/backend/results/demo_data.csv"
    candidate = get_last_candidate(test_file)
    print("\n\n\n\n\n\n\n\n\nLast candidate extracted:",candidate)
    for k, v in candidate.items():
        print(f"{k}: {v}")
        
    insert(candidate, db)  # Insert vào bảng candidates
    return {"status": "success", "message": "Inserted last candidate from test file.", "candidate": candidate,}

from fastapi import FastAPI, UploadFile, File, APIRouter
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
import re
import pdfplumber
import base64
import pandas as pd
import os

router = APIRouter()



CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "results", "demo_data.csv")


# Static
static_dir = os.path.dirname(os.path.abspath(__file__))
router.mount("/static", StaticFiles(directory=static_dir), name="static")

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    "AIzaSyDbZr4J9HIaALo5gl5MMRpoKV2Jkma-YbY"
)
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
)

async def extract_cv_with_gemini(full_text: str = "", pdf_bytes: bytes | None = None) -> dict:
    """Call Gemini to extract structured CV fields as JSON."""
    system_instruction = (
        """
    You are an information extraction assistant. 
    Your task is to extract information from a Vietnamese CV and return the result strictly in JSON format with the following fields:

    {
    "full_name": "...",
    "email": "...",
    "phone_number": "...",
    "date_of_birth": "...",
    "gender": "...",
    "nationality": "...",
    "hometown": "...",
    "permanent_address": "...",
    "skills": "...",
    "education": "...",
    "work_experience": "...",
    "certifications": "...",
     "languages": "...",
    "other_info": "..."
    }

    ⚠️ Important extraction rules:
    - Only extract **information explicitly found** in the CV.
    - If a field is **missing or cannot be found**, set its value to `"n/a"`.
    - Do not hallucinate or guess missing data.
    - Do not return extra fields beyond the ones listed above.
    - Clean and normalize the data as much as possible (e.g., remove formatting artifacts, multiple spaces, bullet symbols, etc.)
    - If multiple pieces of information are found for the same field (e.g., several certifications), join them into a single string separated by semicolons.

    Return ONLY valid JSON. Do not add any explanation or text outside the JSON.
    """
    )
    
    json_schema_hint = {
        "full_name": "",
        "email": "",
        "phone": "",
        "date_of_birth": "",
        "gender": "",
        "address": "",
        "linkedin_url": "",
        "portfolio_url": "",

        "technical_skills": "",
        "soft_skills": "",
        "tools_and_technologies": "",
        "programming_languages": "",
        "frameworks_and_libraries": "",

        "work_experience_summary": "",
        "education_summary": "",
        "certifications_summary": "",
        "expired_certifications": "",
        "languages_summary": "",
        "notable_projects": "",
        "awards_and_honors": "",
        "publications": "",
        "volunteer_experience": "",
        "hobbies_and_interests": "",

        "cv_summary": ""
    }

    prompt = (
        f"{system_instruction}\n\n"
        f"Văn bản CV:\n" + full_text[:15000]
    )

    parts = [{"text": (
        "Trích xuất các trường sau ở dạng JSON thuần (không markdown,"
        " không ```), tuân thủ schema: " + json.dumps(json_schema_hint, ensure_ascii=False)
        + ".\nChỉ in JSON.\n\n" + prompt
    )}]
    # Nếu không trích xuất được text (CV scan), gửi trực tiếp PDF cho Gemini
    if (not full_text or len(full_text.strip()) < 20) and pdf_bytes:
        parts.append({
            "inlineData": {
                "mimeType": "application/pdf",
                "data": base64.b64encode(pdf_bytes).decode("utf-8")
            }
        })

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": parts
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(GEMINI_API_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()

    # Navigate response structure
    text = ""
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass

    if not text:
        return {}

    # Remove markdown fences if any
    fenced = re.search(r"\{[\s\S]*\}", text)
    raw_json = fenced.group(0) if fenced else text

    try:
        return json.loads(raw_json)
    except Exception:
        # Last attempt: strip backticks and retry
        cleaned = raw_json.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except Exception:
            return {}

def extract_with_regex(full_text: str) -> dict:
    """Simple regex-based extraction as a fallback when LLM misses fields."""
    try:
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", full_text)
        phone_match = re.search(r"(?:\+?84|0)(?:\s|\.)?(?:\d{3})(?:\s|\.)?\d{3}(?:\s|\.)?\d{3,4}", full_text)
        # Heuristic for name: first non-empty line that is not email/phone and has letters
        first_lines = [ln.strip() for ln in full_text.splitlines()[:10] if ln.strip()]
        candidate_name = ""
        for ln in first_lines:
            if (email_match and email_match.group(0) in ln) or (phone_match and phone_match.group(0) in ln):
                continue
            if 2 <= len(ln.split()) <= 6 and re.search(r"[A-Za-zÀ-ỹ]", ln):
                candidate_name = ln
                break

        # Skills heuristic: capture section after heading like Skills/Kỹ năng
        skills_match = re.search(r"(?i)(skills|kỹ\s*năng)[:\-]?\s*(.+)", full_text)
        skills_value = skills_match.group(2).strip() if skills_match else ""

        return {
            "name": candidate_name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "skills": skills_value
        }
    except Exception:
        return {}

@router.post("/upload_cv")
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Chỉ chấp nhận file PDF"}

    # Đọc nội dung PDF
    # Đọc nội dung PDF
    text_content = ""
    # Lưu bytes để fallback nếu CV là scan
    pdf_bytes = file.file.read()
    file.file.seek(0)
    with pdfplumber.open(file.file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_content += page_text + "\n"

    # Gọi Gemini để trích xuất cấu trúc
    parsed_info = await extract_cv_with_gemini(text_content, pdf_bytes=pdf_bytes)
    fallback_info = extract_with_regex(text_content)

    # Chuẩn hoá cột và điền giá trị mặc định nếu thiếu
    columns = [
        "email", "full_name", "phone", "date_of_birth", "gender", "address",
        "linkedin_url", "portfolio_url",
        "technical_skills", "soft_skills", "tools_and_technologies",
        "programming_languages", "frameworks_and_libraries",
        "work_experience_summary", "education_summary",
        "certifications_summary", "expired_certifications", "languages_summary",
        "notable_projects", "awards_and_honors", "publications",
        "volunteer_experience", "hobbies_and_interests",
        "filename", "cv_summary", "file_size", "mimetype"
    ]

    record = {
        "email": "",
        "full_name": "",
        "phone": "",
        "date_of_birth": "",
        "gender": "",
        "address": "",
        "linkedin_url": "",
        "portfolio_url": "",

        "technical_skills": "",
        "soft_skills": "",
        "tools_and_technologies": "",
        "programming_languages": "",
        "frameworks_and_libraries": "",

        "work_experience_summary": "",
        "education_summary": "",
        "certifications_summary": "",
        "expired_certifications": "",
        "languages_summary": "",
        "notable_projects": "",
        "awards_and_honors": "",
        "publications": "",
        "volunteer_experience": "",
        "hobbies_and_interests": "",

        "filename": file.filename,
        "cv_summary": "",
        "file_size": len(pdf_bytes),
        "mimetype": file.content_type or "application/pdf"
    }
    
    if isinstance(parsed_info, dict):
        for k, v in parsed_info.items():
            if k in record and v:
                record[k] = v
                

    for k, v in fallback_info.items():
        if k in record and not record[k] and v:
            record[k] = v

    new_data = pd.DataFrame([record]).reindex(columns=columns, fill_value="")

    # Nếu chưa có file CSV thì tạo mới, có rồi thì append
    if not os.path.exists(CSV_FILE):
        new_data.to_csv(CSV_FILE, index=False)
    else:
        new_data.to_csv(CSV_FILE, mode='a', header=False, index=False)
        print( f"Đã trích xuất và lưu {file.filename} vào {CSV_FILE}")
        print( {k: record.get(k, "") for k in columns if k not in ("filename", "content")})
        print( text_content[:500] + "..." if len(text_content) > 500 else text_content)

    return {
        "message": f"Đã trích xuất và lưu {file.filename} vào {CSV_FILE}",
        "parsed": {k: record.get(k, "") for k in columns if k not in ("filename", "content")},
        "text": text_content[:500] + "..." if len(text_content) > 500 else text_content
    }

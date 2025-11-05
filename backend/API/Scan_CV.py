from fastapi import APIRouter, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
import httpx, json, re, pdfplumber, base64, os
from PIL import Image
import pytesseract
import docx2txt
from io import BytesIO
from rapidfuzz import process

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

def clean_text(text) -> str:
    """Làm sạch chuỗi, xử lý cả list/dict."""
    if text is None:
        return ""
    if isinstance(text, list):
        text = " ".join(str(x) for x in text)
    elif isinstance(text, dict):
        text = json.dumps(text, ensure_ascii=False)
    text = str(text)
    text = text.replace("\\n", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    # Xóa khoảng trắng thừa trước dấu câu, giữ 1 khoảng trắng sau dấu chấm
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    text = re.sub(r"([.,;:!?])(?=\S)", r"\1 ", text)
    return text.strip()

def deduplicate_fields(record: dict) -> dict:
    """Loại bỏ lặp trong các trường text dài (education, skills, v.v.)"""
    for key, value in record.items():
        if isinstance(value, str) and len(value) > 20:
            parts = re.split(r"[.\n]", value)
            seen = set()
            result = []
            for p in parts:
                p = clean_text(p)
                if p and p not in seen:
                    seen.add(p)
                    result.append(p)
            record[key] = ". ".join(result)
    return record

def fix_email_format(email: str) -> str:
    """Chỉnh sửa các lỗi thường gặp trong email do OCR."""
    if not email:
        return ""
    email = email.strip().replace(" ", "").replace("..", ".")
    email = email.replace("gmaicom", "gmail.com").replace("gmai.com", "gmail.com")
    email = re.sub(r"(@[A-Za-z0-9.-]+)\.$", r"\1", email)

    if re.match(r".+@.+\.[a-zA-Z]{2,}$", email) is None and not email.endswith(".com"):
        email += ".com"
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', email)
    return match.group(0) if match else ""

def ensure_sentence_end(text: str) -> str:
    """Bổ sung dấu chấm cuối nếu thiếu"""
    if text and not re.search(r"[.?!]$", text):
        return text + "."
    return text


KNOWN_SKILLS = [
    "Laravel Framework", "Back End", "Bootstrap", "React", "Vue.js",
    "Machine Learning", "Big Data", "PHP", "Node.js",
    "Microsoft Word", "Microsoft Excel", "Digital Illustration",
    "Typography", "Branding and Identity Design"
]

def clean_skills_text(raw_text: str) -> str:
    """Chuẩn hóa danh sách kỹ năng, sửa lỗi OCR nhẹ & chuẩn format."""
    if not raw_text:
        return ""
    parts = re.split(r"[,\n;]+", raw_text)
    cleaned_skills = []
    for p in parts:
        skill = p.strip()
        if not skill:
            continue
        match, score, _ = process.extractOne(skill, KNOWN_SKILLS)
        cleaned_skills.append(match if score > 70 else skill)
    # Loại trùng lặp, giữ thứ tự
    seen = set()
    final = []
    for s in cleaned_skills:
        if s not in seen:
            seen.add(s)
            final.append(s)
    return ", ".join(final)

# ==========================
# Gọi Gemini API để trích xuất CV
# ==========================
async def extract_cv_with_gemini(full_text: str = "", file_bytes: bytes | None = None, mime_type: str = None) -> dict:
    system_instruction = """Bạn là trợ lý trích xuất thông tin từ CV tiếng Việt. 
Hãy phân tích và trả về đúng JSON, KHÔNG có giải thích. 
Đặc biệt: 
- Trường 'skills' phải được liệt kê rõ ràng, cách nhau bằng dấu phẩy, không viết liền nhau.
- Email phải đúng định dạng.
- Các đoạn văn bản nên giữ đúng câu, không tự ý chèn khoảng trắng sau dấu chấm.
- phần references mỗi thông tin cách nhau bằng dấu |
- Chỉ trả về các trường sau(nếu không có dữ liệu thì đặt "n/a"):
    1. address
    2. experience
    3. education
    4. hard_skills
    5. soft_skills
    6. activities
    7. certificates
    8. tools
    9. cv_summary
    """

    json_schema_hint = {
        "full_name": "",
        "email": "",
        "phone": "",
        "date_of_birth": "",
        "gender": "",
        "address": "",
        "linkedin_url": "",
        "portfolio_url": "",
        "career_objective": "",
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
        "cv_summary": "",
        "skills": ""
    }

    parts = [
        {"text": f"{system_instruction}\n\nDưới đây là văn bản CV:\n{full_text[:15000]}"},
    ]

    if (not full_text or len(full_text.strip()) < 20) and file_bytes and mime_type:
        parts.append({
            "inlineData": {
                "mimeType": mime_type,
                "data": base64.b64encode(file_bytes).decode("utf-8")
            }
        })

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"responseMimeType": "application/json"}
    }

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(GEMINI_API_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()

    text = ""
    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass

    fenced = re.search(r"\{[\s\S]*\}", text)
    raw_json = fenced.group(0) if fenced else text

    try:
        return json.loads(raw_json)
    except:
        cleaned = raw_json.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except:
            return {}


def extract_with_regex(full_text: str) -> dict:
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", full_text)
    phone_match = re.search(r"(?:\+?84|0)(?:\s|\.)?(?:\d{3})(?:\s|\.)?\d{3}(?:\s|\.)?\d{3,4}", full_text)
    first_lines = [ln.strip() for ln in full_text.splitlines()[:10] if ln.strip()]
    for ln in first_lines:
        if (email_match and email_match.group(0) in ln) or (phone_match and phone_match.group(0) in ln):
            continue
        if 2 <= len(ln.split()) <= 6 and re.search(r"[A-Za-zÀ-ỹ]", ln):
            name = ln
            break
    return {
        "full_name": name if 'full_name' in locals() else "",
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0) if phone_match else ""
    }


@router.post("/upload_cv")
async def upload_cv(
    fullName : str = Form(...),
    email : str = Form(...),
    phone : str = Form(...),
    position : str = Form(...),
    file: UploadFile = File(...)):
    
    filename = file.filename.lower()
    file_bytes = await file.read()
    text_content = ""
    mime_type = file.content_type

    # PDF
    if filename.endswith(".pdf"):
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text_content += (page.extract_text() or "") + "\n"

    # Ảnh
    elif filename.endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(BytesIO(file_bytes))
        text_content = pytesseract.image_to_string(image, lang="vie+eng")

    # DOCX
    elif filename.endswith(".docx"):
        with open("temp_doc.docx", "wb") as temp:
            temp.write(file_bytes)
        text_content = docx2txt.process("temp_doc.docx")
        os.remove("temp_doc.docx")

    else:
        return {"error": "Định dạng không hỗ trợ. Chỉ nhận PDF, JPG/PNG hoặc DOCX."}

    # Làm sạch text trước khi gửi lên Gemini
    text_content = clean_text(text_content)

    # Gọi Gemini
    parsed_info = await extract_cv_with_gemini(text_content, file_bytes, mime_type)
    fallback_info = extract_with_regex(text_content)

    # Gộp kết quả
    record = {
        
        "filename": filename,
        "file_size": len(file_bytes),
        "mimetype": mime_type,
        "cv_summary": "",
        **{k: "" for k in fallback_info.keys()},
        **{k: "" for k in parsed_info.keys()},
        "full_name": fullName,
        "email": email,
        "phone": phone,
        "position": position
    }

    for k, v in parsed_info.items():
        if v:
            record[k] = clean_text(v)
    for k, v in fallback_info.items():
        if not record.get(k) and v:
            record[k] = clean_text(v)

    # Loại bỏ lặp nội dung trong các trường dài
    record = deduplicate_fields(record)

    # Hậu xử lý cụ thể
    if record.get("email"):
        record["email"] = fix_email_format(record["email"])

    if record.get("skills"):
        record["skills"] = clean_skills_text(record["skills"])

    for key in ["objective", "cv_summary", "experience", "education"]:
        if record.get(key):
            record[key] = ensure_sentence_end(record[key])

    # Ghi CSV theo dạng key,value dễ đọc
    with open(CSV_FILE, "a", encoding="utf-8") as f:
        for k, v in record.items():
            f.write(f"{k}: {v}\n")
        f.write("-" * 40 + "\n")

    return {
        "message": f"Đã trích xuất thông tin từ {filename}",
        "parsed": record,
        "text": text_content[:500] + "..." if len(text_content) > 500 else text_content
    }
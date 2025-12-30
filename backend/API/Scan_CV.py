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


router = APIRouter()

# Limit concurrent Gemini requests to avoid bursts (tune as needed)
_GEMINI_SEMAPHORE = asyncio.Semaphore(2)
_GEMINI_429_COUNT = 0
_GEMINI_429_THRESHOLD = 5
_GEMINI_COOLDOWN_SECONDS = 60
_GEMINI_COOLDOWN_UNTIL = 0.0

CSV_FILE = os.path.join(os.path.dirname(__file__), "..", "results", "demo_data.csv")

# Static
static_dir = os.path.dirname(os.path.abspath(__file__))
router.mount("/static", StaticFiles(directory=static_dir), name="static")




# GEMINI API is deprecated in this file. Replaced by local Ollama model (qwen2.5:7b).
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDigUC7KifbZTvp9DJvYeRrHpwIkKlkNCE")
# GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"



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
    # Programming languages
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Golang", "Rust",
    "C", "C++", "C#", "PHP", "Ruby", "Swift", "Kotlin", "Scala", "Objective-C",
    "R", "MATLAB", "Perl", "Haskell", "Elixir", "Erlang", "Dart", "Lua",
    "Shell", "Bash", "PowerShell",

    # Frontend frameworks / libraries
    "React", "React.js", "React Native", "Next.js", "Gatsby", "Vue.js", "Nuxt.js",
    "Angular", "Svelte", "SvelteKit", "Ember.js", "Backbone.js",

    # CSS / UI
    "HTML", "CSS", "Sass", "Less", "Tailwind CSS", "Bootstrap", "Material UI",
    "Ant Design", "Chakra UI", "Styled Components", "Semantic UI",

    # Backend frameworks
    "Node.js", "Express", "Koa", "NestJS", "FastAPI", "Flask", "Django",
    "Spring", "Spring Boot", "Hibernate", "ASP.NET Core", ".NET", "Laravel",
    "Symfony", "Ruby on Rails", "Sinatra", "Phoenix", "Play Framework",

    # Mobile
    "Android", "iOS", "Android SDK", "Xcode", "Flutter", "Ionic", "Cordova",
    "Xamarin",

    # Databases
    "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis", "Cassandra", "MariaDB",
    "Oracle", "Microsoft SQL Server", "DynamoDB", "BigQuery", "Elasticsearch",

    # Big data / streaming
    "Hadoop", "Spark", "Kafka", "Flink", "Hive", "Airflow",

    # Machine learning / data science
    "TensorFlow", "PyTorch", "scikit-learn", "pandas", "NumPy", "SciPy", "Keras",
    "XGBoost", "LightGBM", "Hugging Face", "spaCy", "NLTK", "OpenCV", "Dask",

    # DevOps / Cloud / Infra as Code
    "Docker", "Kubernetes", "Helm", "OpenShift", "EKS", "GKE", "AKS",
    "Terraform", "Pulumi", "Ansible", "Chef", "Puppet", "Vagrant",
    "AWS", "Azure", "GCP", "Amazon Web Services", "Google Cloud Platform",
    "Azure DevOps",

    # CI/CD
    "Jenkins", "GitHub Actions", "GitLab CI", "CircleCI", "Travis CI", "ArgoCD",

    # Monitoring / logging / observability
    "Prometheus", "Grafana", "ELK", "Elasticsearch", "Logstash", "Kibana",
    "Datadog", "Sentry", "New Relic",

    # Messaging / queues
    "RabbitMQ", "ActiveMQ", "ZeroMQ", "Amazon SQS", "Redis Streams", "NSQ",

    # APIs / protocols
    "REST", "GraphQL", "gRPC", "WebSocket", "OpenAPI", "Swagger", "JSON", "XML",

    # Security / auth
    "OAuth2", "OpenID Connect", "JWT", "SAML", "SSL/TLS", "bcrypt", "OWASP",

    # Testing / QA
    "pytest", "unittest", "Jest", "Mocha", "Chai", "Jasmine", "Selenium",
    "Cypress", "Playwright", "Puppeteer", "JUnit", "TestNG",

    # Build tools / package managers
    "npm", "yarn", "pnpm", "pip", "pipenv", "poetry", "maven", "gradle",
    "composer", "gem", "cargo", "go modules",

    # VCS / collaboration / IDEs
    "Git", "GitHub", "GitLab", "Bitbucket", "VS Code", "Visual Studio",
    "IntelliJ IDEA", "PyCharm", "Eclipse", "NetBeans", "Sublime Text", "Vim",
    "Emacs", "Xcode", "Android Studio",

    # Data engineering / analytics
    "ETL", "Data Pipelines", "Snowflake", "Redshift", "Presto", "Trino",

    # Other useful stacks and concepts
    "Microservices", "Serverless", "Lambda", "Cloud Functions", "CDN", "CI/CD",
    "Infrastructure", "Observability", "Performance Tuning", "Load Balancing",
    "Caching", "Varnish", "Redis Cache",

    # Design / prototyping / misc
    "Figma", "Sketch", "Adobe Photoshop", "Adobe Illustrator",

    # Office / docs (OCR helpers)
    "Microsoft Word", "Microsoft Excel", "Google Docs", "Google Sheets",

    # Fallback generic entries
    "Back End", "Front End", "Full Stack", "DevOps", "SRE", "Data Science",
    "Machine Learning Engineer", "AI", "NLP", "Computer Vision"
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


def ocr_image_bytes(image_bytes: bytes, lang: str = "vie+eng") -> str:
    """Chạy OCR trên hình ảnh (bytes) và trả về text."""
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        return pytesseract.image_to_string(img, lang=lang)
    except Exception as e:
        logging.warning("ocr_image_bytes failed: %s", e)
        return ""

# ==========================
# Gọi Gemini API để trích xuất CV
# ==========================
async def extract_cv_with_gemini(full_text: str = "", file_bytes: bytes | None = None, mime_type: str = None) -> dict:
    # NOTE: This function name is preserved for compatibility but the implementation
    # now uses a local Ollama model (qwen2.5:7b) via the centralized ai manager.
    system_instruction = """Bạn là trợ lý trích xuất thông tin từ CV tiếng Việt. 
Hãy phân tích và trả về đúng JSON, KHÔNG có giải thích. 
Đặc biệt: 
- Trường 'skills' phải được liệt kê rõ ràng, cách nhau bằng dấu phẩy.
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
    10. gender
    """

    # Build a single prompt for Ollama (we avoid sending binary data)
    prompt = f"{system_instruction}\n\nDưới đây là văn bản CV:\n{full_text[:15000]}"

    max_retries = 3
    backoff_base = 2.0

    # reuse existing circuit/counter variables for cooldown behavior
    global _GEMINI_429_COUNT, _GEMINI_COOLDOWN_UNTIL
    now = time.time()
    if _GEMINI_COOLDOWN_UNTIL and now < _GEMINI_COOLDOWN_UNTIL:
        logging.warning("extract_cv_with_gemini: skipping LLM call due to cooldown until %s", _GEMINI_COOLDOWN_UNTIL)
        return {}

    async with _GEMINI_SEMAPHORE:
        data = {}
        for attempt in range(1, max_retries + 1):
            try:
                # Call OpenAI Chat Completions API asynchronously
                openai_key = os.getenv("OPENAI_API_KEY")
                if not openai_key:
                    raise RuntimeError("OPENAI_API_KEY not set")
                model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
                async with httpx.AsyncClient(timeout=30.0) as client:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": full_text[:15000]}
                        ],
                        "max_tokens": 700,
                        "temperature": 0
                    }
                    headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
                    resp = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                    resp.raise_for_status()
                    j = resp.json()
                    text = j.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Expect the model to output a JSON object; extract the first JSON-looking block
                fenced = re.search(r"\{[\s\S]*\}", text)
                raw_json = fenced.group(0) if fenced else text
                parsed = json.loads(raw_json)

                # Normalize into previous 'data' shape so downstream parsing stays the same
                data = {"candidates": [{"content": [{"parts": [{"text": raw_json}]}]}]}

                # reset counters on success
                _GEMINI_429_COUNT = 0
                _GEMINI_COOLDOWN_UNTIL = 0.0
                break

            except Exception as e:
                logging.warning("Ollama request exception on attempt %s: %s", attempt, e)
                if attempt < max_retries:
                    wait = backoff_base * (2 ** (attempt - 1)) + random.random()
                    await asyncio.sleep(wait)
                    continue
                logging.error("Ollama request failed after retries: %s", e)
                data = {}
                break

    if not isinstance(data, dict) or not data:
        logging.info("extract_cv_with_gemini: returning empty result after retries")
        return {}

    text = ""
    try:
        text = data["candidates"][0]["content"][0]["parts"][0]["text"]
    except Exception:
        pass

    fenced = re.search(r"\{[\s\S]*\}", text)
    raw_json = fenced.group(0) if fenced else text
    logging.debug("extract_cv_with_gemini raw_json (truncated): %s", (raw_json or "")[:2000])

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


def normalize_phone_number(phone: str) -> str:
    # Bỏ tất cả ký tự không phải số
    digits = re.sub(r'\D', '', phone)

    # Chuẩn hóa đầu số theo quy ước Việt Nam
    if digits.startswith("84"):
        digits = "0" + digits[2:]
    elif digits.startswith("0"):
        pass  # giữ nguyên
    else:
        # Trường hợp số không có 0 hoặc 84 ở đầu → tự thêm số 0
        # Bạn có thể thay đổi logic tùy nhu cầu
        digits = "0" + digits

    return digits


@router.post("/upload_cv")
async def upload_cv(
    fullName : str = Form(...),
    email : str = Form(...),
    phone : str = Form(...),
    position : str = Form(...),
    job_id: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)     # ← thêm dependency
):
    
    filename = file.filename.lower()
    file_bytes = await file.read()
    filebyte2 = file_bytes
    text_content = ""
    mime_type = file.content_type

    # PDF
    if filename.endswith(".pdf"):
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            # First try native text extraction
            for page in pdf.pages:
                text_content += (page.extract_text() or "") + "\n"

            # If extracted text is very small, fall back to OCR on each page
            if not text_content.strip() or len(text_content.strip()) < 50:
                logging.info("PDF text extraction returned little content; falling back to OCR per page")
                ocr_text = ""
                for page in pdf.pages:
                    try:
                        pil_img = page.to_image(resolution=150).original
                        if pil_img is not None:
                            # ensure RGB
                            pil_img = pil_img.convert("RGB")
                            ocr_text += pytesseract.image_to_string(pil_img, lang="vie+eng") + "\n"
                    except Exception as e:
                        logging.warning("PDF page OCR failed: %s", e)
                text_content = ocr_text or text_content

        # parsed_info isn't available yet here; printing moved after LLM call
    # Ảnh
    elif filename.endswith((".png", ".jpg", ".jpeg")):
        # Dùng OCR cho file ảnh
        text_content = ocr_image_bytes(file_bytes, lang="vie+eng")

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
    # In ra terminal phần text đã trích xuất từ file để dễ kiểm tra
    try:
        print("\n--- Extracted text (start) ---\n")
        print(text_content)
        print("\n--- Extracted text (end) ---\n")
    except Exception:
        # bảo đảm không làm vỡ luồng nếu in gặp lỗi encoding
        print("[Warning] Unable to print extracted text due to encoding issues.")

    # Gọi Gemini
    parsed_info = {}  # <-- ensure defined even if API call fails
    try:
        parsed_info = await extract_cv_with_gemini(text_content, file_bytes, mime_type)
    except httpx.HTTPStatusError as e:
        print("\n\n\n\n\n\n\n\n\n\n\nGemini HTTP error:", e)
        parsed_info = {}
    except Exception as e:
        # Bắt thêm các lỗi khác (mạng, timeout, parsing...)
        print("\n\n\n\n\n\n\n\n\n\n\nGemini unexpected error:", e)
        parsed_info = {}
    fallback_info = extract_with_regex(text_content)
    clear_phone = normalize_phone_number(phone)
    clear_filename = filename.replace(" ", "")

    
    # Gộp kết quả
    record = {
        
        "filename": clear_filename,
        "file_size": len(file_bytes),
        "mimetype": mime_type,
        "filedata": base64.b64encode(filebyte2).decode("utf-8"),
        "cv_summary": "",
        **{k: "" for k in fallback_info.keys()},
        **{k: "" for k in parsed_info.keys()},
        "full_name": fullName,
        "email": email,
        "phone": clear_phone,
        "position": position,
        "job_id": job_id
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

    print_candidate(record)
    insert(record, db)  # Insert vào bảng candidates
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
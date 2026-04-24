# app.py - REWRITTEN
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.API.Scan_CV import router as scan_cv
from backend.API.dashboard import router as dashboard
from backend.API.Email_send_respon.render_mail import router as email_renderer
from backend.API.Email_send_respon.send_mail import router as email_sender
from backend.API.Email_send_respon.verify_mail import router as email_verifier
<<<<<<< Updated upstream
# Import router từ file Scan_CV (giả sử scan router khai báo: router = APIRouter() trong Scan_CV.py)
=======
from backend.dataAndModels.test_dtb import router as test
from backend.API.job_routes import router as job_router
from backend.dataAndModels.test_data_scoring import router as test_scoring
>>>>>>> Stashed changes

# ──────────────────────────────────────────────
# Đường dẫn thư mục
# HireSmart/
# ├── backend/
# │   └── API/
# │       └── app.py   ← file này
# └── frontend/
#     ├── html/        ← các file .html
#     ├── Styles/      ← CSS + JS
#     └── templates/   ← ảnh, logo
# ──────────────────────────────────────────────
BASE_DIR     = Path(__file__).resolve().parent.parent.parent  # HireSmart/
FRONTEND_DIR = BASE_DIR / "frontend"
HTML_DIR     = FRONTEND_DIR / "html"
STYLES_DIR   = FRONTEND_DIR / "Styles"
TEMPLATES_DIR= FRONTEND_DIR / "templates"

app = FastAPI(title="HireSmart API")

# ── CORS ──────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

<<<<<<< Updated upstream
# Mount thư mục frontend để truy cập file tĩnh (ví dụ: /frontend/index.html hoặc /frontend/Styles/style.css)
STATIC_DIR = FRONTEND_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
# Serve frontend/html hoặc frontend/static tùy có thư mục nào
if FRONTEND_DIR.exists():
    # ưu tiên frontend/static nếu tồn tại, nếu không dùng frontend/html
    static_dir = FRONTEND_DIR / "static" if (FRONTEND_DIR / "static").exists() else FRONTEND_DIR / "html" if (FRONTEND_DIR / "html").exists() else FRONTEND_DIR
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    # mount templates nếu có thư mục templates bên trong html
    templates_dir = FRONTEND_DIR / "html" / "templates"
    if templates_dir.exists():
        app.mount("/templates", StaticFiles(directory=str(templates_dir)), name="templates")

# favicon route (tránh 404)
favicon_path = static_dir / "favicon.ico"
@app.get("/favicon.ico")
async def favicon():
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    raise HTTPException(status_code=404, detail="favicon not found")

# Include router chứa /upload_cv và các route khác
=======
# ── Static files ──────────────────────────────
# Truy cập: /Styles/style.css  /templates/logo-2.png
if STYLES_DIR.exists():
    app.mount("/Styles", StaticFiles(directory=str(STYLES_DIR)), name="Styles")

if TEMPLATES_DIR.exists():
    app.mount("/templates", StaticFiles(directory=str(TEMPLATES_DIR)), name="templates")

# ── API Routers ───────────────────────────────
>>>>>>> Stashed changes
app.include_router(scan_cv)
app.include_router(dashboard)
app.include_router(email_renderer, prefix="/email", tags=["email"])
app.include_router(email_sender,   prefix="/email", tags=["email"])
app.include_router(email_verifier, tags=["email"])

# ── HTML Routes ───────────────────────────────
# Phục vụ tất cả file .html theo tên
# Ví dụ: /Home.html  /Login.html  /dashboard.html
HTML_PAGES = [
    "Home", "Login", "Recruitment", "recruitment",
    "Create_job", "Job_list", "dashboard", "profile", "bulk_email"
]

def _serve_html(name: str) -> HTMLResponse:
    """Đọc file HTML và trả về, tự động sửa đường dẫn tương đối."""
    path = HTML_DIR / f"{name}.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{name}.html không tồn tại")
    content = path.read_text(encoding="utf-8")
    # Sửa đường dẫn tương đối ../Styles/ và ../templates/ thành /Styles/ /templates/
    content = content.replace("../Styles/", "/Styles/")
    content = content.replace("../templates/", "/templates/")
    content = content.replace("../html/", "/")
    return HTMLResponse(content)

<<<<<<< Updated upstream
# Route gốc trả về index.html nếu tồn tại, else trả thông báo
@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = FRONTEND_DIR / "Recruitment.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<pre>API is running. Use /upload_cv to submit PDF CV.</pre>")
=======
@app.get("/", response_class=HTMLResponse)
async def root():
    """Trang chủ → Home.html"""
    return _serve_html("Home")

@app.get("/favicon.ico")
async def favicon():
    fav = TEMPLATES_DIR / "favicon.ico"
    if fav.exists():
        return FileResponse(str(fav))
    raise HTTPException(status_code=404)

@app.get("/{page_name}.html", response_class=HTMLResponse)
async def serve_page(page_name: str):
    """
    Serve bất kỳ file HTML nào theo tên.
    VD: /Home.html  /Login.html  /dashboard.html
    """
    return _serve_html(page_name)

# Thêm vào app.py
@app.get("/html/Login.html", response_class=HTMLResponse)
async def login_page():
    path = FRONTEND_DIR / "html" / "Login.html"
    return path.read_text(encoding="utf-8")
>>>>>>> Stashed changes

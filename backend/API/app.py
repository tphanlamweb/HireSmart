# app.py
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.API.Scan_CV import router as scan_cv
from backend.API.dashboard import router as dashboard
from backend.API.Email_send_respon.render_mail import router as email_renderer
from backend.API.Email_send_respon.send_mail import router as email_sender
from backend.API.Email_send_respon.verify_mail import router as email_verifier
from backend.dataAndModels.test_dtb import router as test
from backend.API.job_routes import router as job_router
from backend.dataAndModels.test_data_scoring import router as test_scoring
# Import router từ file Scan_CV (giả sử scan router khai báo: router = APIRouter() trong Scan_CV.py)

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # d:\Cap 1\HireSmart
FRONTEND_DIR = BASE_DIR / "frontend"   # thư mục chứa index.html và các file tĩnh

app = FastAPI(title="HireSmart API")

# CORS (cho phép frontend truy cập)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # trong production hãy giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount thư mục HTML
HTML_DIR = FRONTEND_DIR / "html"
if HTML_DIR.exists():
    app.mount("/html", StaticFiles(directory=str(HTML_DIR)), name="html")

# Mount thư mục CSS/JS
STYLES_DIR = FRONTEND_DIR / "Styles"
if STYLES_DIR.exists():
    app.mount("/Styles", StaticFiles(directory=str(STYLES_DIR)), name="Styles")

# Mount thư mục templates
TEMPLATES_DIR = FRONTEND_DIR / "templates"
if TEMPLATES_DIR.exists():
    app.mount("/templates", StaticFiles(directory=str(TEMPLATES_DIR)), name="templates")

# Nếu bạn có thư mục static bên trong frontend (ví dụ frontend/static), có thể mount thêm:
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
app.include_router(scan_cv)
app.include_router(dashboard)
app.include_router(email_renderer, prefix="/email", tags=["email"])
app.include_router(email_sender, prefix="/email", tags=["email"])
app.include_router(email_verifier, tags=["email"])
app.include_router(job_router)
app.include_router(test)
app.include_router(test_scoring)


# Route gốc trả về Recruitment.html
@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = FRONTEND_DIR / "html" / "Recruitment.html"
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()
    return HTMLResponse("<pre>API is running. Visit /Recruitment.html to start.</pre>")
# app.py
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.API.Scan_CV import router as scan_cv
from backend.API.dashboard import router as dashboard
from backend.API.Email_send_respon.render_mail import router as email_renderer
from backend.API.Email_send_respon.send_mail import router as email_sender
from backend.API.Email_send_respon.verify_mail import router as email_verifier

# ⬇⬇⬇ THÊM DÒNG NÀY
from backend.API.login import router as login_router

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="HireSmart API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static
STATIC_DIR = FRONTEND_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Routers
app.include_router(scan_cv)
app.include_router(dashboard)
app.include_router(email_renderer, prefix="/email", tags=["email"])
app.include_router(email_sender, prefix="/email", tags=["email"])
app.include_router(email_verifier, tags=["email"])

# ⬇⬇⬇ THÊM ROUTER LOGIN VÀO ĐÂY
app.include_router(login_router, prefix="/login", tags=["login"])

# Home
@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = FRONTEND_DIR / "Recruitment.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<pre>API is running. Use /upload_cv to submit PDF CV.</pre>")

# app.py
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend.API.scan_CV import router as sc
from backend.API.dashboard import router as db
# Import router từ file Scan_CV (giả sử scan router khai báo: router = APIRouter() trong Scan_CV.py)

BASE_DIR = Path(__file__).resolve().parent
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

# Mount thư mục frontend để truy cập file tĩnh (ví dụ: /frontend/index.html hoặc /frontend/Styles/style.css)


# Nếu bạn có thư mục static bên trong frontend (ví dụ frontend/static), có thể mount thêm:
STATIC_DIR = FRONTEND_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include router chứa /upload_cv và các route khác
app.include_router(sc)
app.include_router(db)


# Route gốc trả về index.html nếu tồn tại, else trả thông báo
@app.get("/", response_class=HTMLResponse)
async def read_root():
    index_path = FRONTEND_DIR / "Recruitment.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<pre>API is running. Use /upload_cv to submit PDF CV.</pre>")
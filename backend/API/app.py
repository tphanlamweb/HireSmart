<<<<<<< Updated upstream
from flask import Flask, render_template


app = Flask(__name__)
=======
# app.py
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from API.Scan_CV import router as sc
from API.dashboard import router as db
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import router từ file Scan_CV (giả sử scan router khai báo: router = APIRouter() trong Scan_CV.py)

BASE_DIR = Path(__file__).resolve().parent
# Frontend thật ở HireSmart/frontend (2 cấp trên API)
FRONTEND_DIR = BASE_DIR.parent.parent / "frontend"   # thư mục chứa HTML/CSS/JS

app = FastAPI(title="HireSmart API")

# CORS (cho phép frontend truy cập)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # trong production hãy giới hạn origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount toàn bộ thư mục frontend để phục vụ tài nguyên tĩnh (CSS/JS/ảnh)
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
>>>>>>> Stashed changes

root = ''
@app.route(f"/{root}")
def list_users():
    return render_template(f"{root}.html")

<<<<<<< Updated upstream
if __name__ == "__main__":
    app.run(debug=True)
    
    
    
    
    
=======

# Route gốc trả về index.html nếu tồn tại, else trả thông báo
@app.get("/", response_class=HTMLResponse)
async def read_root():
    # File HTML nằm trong frontend/html
    index_path = FRONTEND_DIR / "html" / "Recruitment.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse("<pre>API is running. Use /upload_cv to submit PDF CV.</pre>")
>>>>>>> Stashed changes

from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from pydantic import BaseModel
from typing import List

from backend.API.Email_send_respon.create_token import (
    create_tokens_for_ids,
    save_to_csv,
    OUTPUT_FILE,
)


#   mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
DB_USER = "root"                # 🧑‍💻 Tên user MySQL
DB_PASSWORD = "123456"          # 🔑 Mật khẩu MySQL
DB_HOST = "localhost"           # 🖥️  Địa chỉ server (hoặc IP)
DB_PORT = "3306"                # 🌐 Cổng mặc định của MySQL 
DB_NAME = "HireSmart"           # 📂 Tên cơ sở dữ liệu bạn đã có

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tạo engine kết nối đến MySQL
engine = create_engine(DATABASE_URL)


metadata = MetaData()
metadata.reflect(bind=engine)  # 🔍 Tự động tải cấu trúc tất cả bảng có sẵn

# 🔧 Sửa đường dẫn template — tính từ file dashboard.py hiện tại
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # d:\Cap 1\HireSmart
TEMPLATES_DIR = BASE_DIR / "frontend" / "html"

print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
print(f"[DEBUG] TEMPLATES_DIR: {TEMPLATES_DIR}")
print(f"[DEBUG] TEMPLATES_DIR exists: {TEMPLATES_DIR.exists()}")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()


class CandidateIds(BaseModel):
    candidate_ids: List[int]

@router.get("/candidates")
def read_users(db: Session = Depends(get_db)):
    try:
        users_table = metadata.tables["candidates"]  # ⚠️ Đổi tên bảng ở đây
    except KeyError:
        raise HTTPException(status_code=404, detail="Bảng 'candidates' không tồn tại trong DB!")

    result = db.execute(users_table.select()).fetchall()
    return [dict(row._mapping) for row in result]

@router.get("/table/{table_name}")
def read_table(table_name: str, db: Session = Depends(get_db)):
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail=f"Bảng '{table_name}' không tồn tại!")

    table = metadata.tables[table_name]
    result = db.execute(table.select()).fetchall()
    return [dict(row._mapping) for row in result]

@router.get("/dashboard", response_class=HTMLResponse)
def get_candidates_tables(request: Request):
    try:
        datatable = metadata.tables["candidates"]  # ⚠️ Đổi tên bảng ở đây
        print("candidates tables: \n")  # In ra tên các cột của bảng
        conn = engine.connect()
        data = conn.execute(
            select(
                datatable.c.id,
                datatable.c.full_name,
                datatable.c.overall_cv_score,
                datatable.c.phone
            )
        ).fetchall()
        return templates.TemplateResponse("dashboard.html", {"request": request, "users": data})
    
    except Exception as e:
        print(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_tokens")
def create_tokens_endpoint(body: CandidateIds):
    """
    Nhận danh sách ID ứng viên từ front-end và tạo token cho CHỈ các ứng viên đó.
    Đồng thời lưu file candidate_with_token.csv để dùng cho gửi email hàng loạt.
    """
    try:
        rows = create_tokens_for_ids(body.candidate_ids)
        if not rows:
            raise HTTPException(
                status_code=400,
                detail="Không tìm thấy ứng viên hợp lệ với danh sách ID đã gửi.",
            )

        # Lưu file CSV để dùng cho bước gửi email hàng loạt
        save_to_csv(rows, OUTPUT_FILE)

        return JSONResponse(content=rows)
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] create_tokens_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))





from fastapi import FastAPI, Depends, HTTPException, APIRouter
import pymysql
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from typing import List
from pydantic import BaseModel
from backend.dataAndModels.config import DATABASE_URL

from backend.API.Email_send_respon.create_token import (
    create_tokens_for_ids,
    save_to_csv,
    OUTPUT_FILE,
)




# Tạo engine kết nối đến MySQL
engine = create_engine(DATABASE_URL, echo=True)

metadata = MetaData()
metadata.reflect(bind=engine)  # 🔍 Tự động tải cấu trúc tất cả bảng có sẵn

# Sửa đường dẫn template — tính từ file dashboard.py hiện tại
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # d:\Cap 1\HireSmart
TEMPLATES_DIR = BASE_DIR / "frontend" / "html"
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
        users_table = metadata.tables["audit_logs"]  # ⚠️ Đổi tên bảng ở đây
    except KeyError:
        raise HTTPException(status_code=404, detail="Bảng 'candidates' không tồn tại trong DB!")

    result = db.execute(users_table.select()).fetchall()
    return [dict(row._mapping) for row in result]





@router.get("/dashboard", response_class=HTMLResponse)
def get_candidates_tables(request: Request):
    try:
        datatable = metadata.tables["candidates"]
        print("[DEBUG] Loading candidates from database...")
        
        with engine.connect() as conn:
            result = conn.execute(
                select(
                    datatable.c.id,
                    datatable.c.full_name,
                    datatable.c.overall_cv_score,
                    datatable.c.phone,
                    datatable.c.application_status,  # Lấy cột status từ database
                )
            ).fetchall()

        data = []
        for row in result:
            data.append({
                "id": row.id if hasattr(row, 'id') else row[0],
                "full_name": row.full_name if hasattr(row, 'full_name') else row[1],
                "overall_cv_score": row.overall_cv_score if hasattr(row, 'overall_cv_score') else row[2],
                "phone": row.phone if hasattr(row, 'phone') else row[3],
                "application_status": row[4] if len(row) > 4 else 'suitable',

            })

        print(f"[DEBUG] Loaded {len(data)} candidates")
        return templates.TemplateResponse("dashboard.html", {"request": request, "users": data})

    except KeyError as e:
        error_msg = f"Bảng 'candidates' không tồn tại trong database: {e}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=404, detail=error_msg)
    except Exception as e:
        error_msg = f"Lỗi khi load dashboard: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/bulk-email", response_class=HTMLResponse)
def bulk_email_page(request: Request, ids: str = ""):
    """
    Trang chọn template email cho danh sách ứng viên đã chọn.
    """
    id_list = []
    if ids:
        for raw in ids.split(","):
            raw = raw.strip()
            if not raw:
                continue
            try:
                id_list.append(int(raw))
            except ValueError:
                continue

    candidates = []
    if id_list:
        datatable = metadata.tables.get("candidates")
        if datatable is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy bảng 'candidates'.")

        columns = [
            datatable.c.id,
            datatable.c.full_name,
            datatable.c.email,
        ]
        if "phone" in datatable.c:
            columns.append(datatable.c.phone)

        stmt = select(*columns).where(datatable.c.id.in_(id_list))

        with engine.connect() as conn:
            rows = conn.execute(stmt).fetchall()
            for row in rows:
                data = dict(row._mapping)
                candidates.append(
                    {
                        "id": data.get("id"),
                        "full_name": data.get("full_name", ""),
                        "email": data.get("email", ""),
                        "phone": data.get("phone", ""),
                    }
                )

    templates_table = metadata.tables.get("email_templates")
    template_rows = []
    if templates_table is not None:
        stmt_tpl = select(
            templates_table.c.id,
            templates_table.c.template_name,
            templates_table.c.template_type,
        ).order_by(templates_table.c.template_name.asc())

        with engine.connect() as conn:
            template_rows = [dict(row._mapping) for row in conn.execute(stmt_tpl).fetchall()]

    return templates.TemplateResponse(
        "bulk_email.html",
        {
            "request": request,
            "candidate_ids": id_list,
            "selected_candidates": candidates,
            "email_templates": template_rows,
        },
    )


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





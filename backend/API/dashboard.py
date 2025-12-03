from fastapi import FastAPI, Depends, HTTPException, APIRouter
<<<<<<< HEAD
import pymysql
from sqlalchemy import create_engine, MetaData, Table, select
=======
from sqlalchemy import create_engine, MetaData, Table, select, update
>>>>>>> 8527fe4 (up date verify)
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


@router.get("/tables/{table}")
def read_users(table :str, db: Session = Depends(get_db)):
    try:
<<<<<<< HEAD
        users_table = metadata.tables["audit_logs"]  # ⚠️ Đổi tên bảng ở đây
=======
        table_name = table
        users_table = metadata.tables[table_name]  # ⚠️ Đổi tên bảng ở đây
>>>>>>> 8527fe4 (up date verify)
    except KeyError:
        raise HTTPException(status_code=404, detail="Bảng 'candidates' không tồn tại trong DB!")

    result = db.execute(users_table.select()).fetchall()
    return [dict(row._mapping) for row in result]

<<<<<<< HEAD

=======
@router.get("/table/{table_name}")
def read_table(table_name: str, field: str = None, db: Session = Depends(get_db)):
    """
    Đọc dữ liệu từ bảng. Nếu có field, chỉ trả về cột đó.
    """
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail=f"Bảng '{table_name}' không tồn tại!")
    
    table = metadata.tables[table_name]
    
    if field:
        if field not in table.c:
            raise HTTPException(status_code=404, detail=f"Cột '{field}' không tồn tại trong bảng '{table_name}'!")
        column = table.c[field]
        with engine.connect() as conn:
            field_data = conn.execute(select(column)).fetchall()
        return [row[0] for row in field_data]
    else:
        result = db.execute(table.select()).fetchall()
        return [dict(row._mapping) for row in result]
>>>>>>> 8527fe4 (up date verify)



@router.get("/dashboard", response_class=HTMLResponse)
def get_candidates_tables(request: Request):
    try:
        datatable = metadata.tables["candidates"]
        print("[DEBUG] Loading candidates from database...")
        
        with engine.connect() as conn:
<<<<<<< HEAD
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

=======
            # Lấy các cột cần thiết, bao gồm application_status nếu có
            columns = [
                datatable.c.id,
                datatable.c.full_name,
                datatable.c.overall_cv_score,
                datatable.c.phone,
            ]
            # Thêm application_status nếu cột tồn tại
            if "application_status" in datatable.c:
                columns.append(datatable.c.application_status)
            
            result = conn.execute(select(*columns)).fetchall()
            
            # Convert Row objects to dict để template dễ truy cập
            data = []
            for row in result:
                row_dict = {
                    "id": row.id if hasattr(row, 'id') else row[0],
                    "full_name": row.full_name if hasattr(row, 'full_name') else row[1],
                    "overall_cv_score": row.overall_cv_score if hasattr(row, 'overall_cv_score') else row[2],
                    "phone": row.phone if hasattr(row, 'phone') else row[3],
                }
                # Thêm application_status nếu có
                if "application_status" in datatable.c:
                    row_dict["application_status"] = getattr(row, 'application_status', None) or "suitable"
                else:
                    row_dict["application_status"] = "suitable"  # Mặc định nếu không có cột
                data.append(row_dict)
        
>>>>>>> 8527fe4 (up date verify)
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


class UpdateStatusRequest(BaseModel):
    candidate_id: int
    status: str


@router.get("/candidates")
def get_candidates_api():
    """
    API endpoint trả về danh sách ứng viên dạng JSON để dashboard có thể reload.
    """
    try:
        datatable = metadata.tables.get("candidates")
        if datatable is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy bảng 'candidates'.")
        
        columns = [
            datatable.c.id,
            datatable.c.full_name,
            datatable.c.overall_cv_score,
            datatable.c.phone,
        ]
        if "application_status" in datatable.c:
            columns.append(datatable.c.application_status)
        
        with engine.connect() as conn:
            result = conn.execute(select(*columns)).fetchall()
        
        data = []
        for row in result:
            row_dict = {
                "id": row.id if hasattr(row, 'id') else row[0],
                "full_name": row.full_name if hasattr(row, 'full_name') else row[1],
                "overall_cv_score": row.overall_cv_score if hasattr(row, 'overall_cv_score') else row[2],
                "phone": row.phone if hasattr(row, 'phone') else row[3],
            }
            if "application_status" in datatable.c:
                row_dict["application_status"] = getattr(row, 'application_status', None) or "suitable"
            else:
                row_dict["application_status"] = "suitable"
            data.append(row_dict)
        
        return JSONResponse(content={"candidates": data})
    except Exception as e:
        print(f"[ERROR] get_candidates_api: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-status")
def update_candidate_status(body: UpdateStatusRequest, db: Session = Depends(get_db)):
    """
    Cập nhật application_status của ứng viên trong database.
    """
    try:
        datatable = metadata.tables.get("candidates")
        if datatable is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy bảng 'candidates'.")
        
        if "application_status" not in datatable.c:
            raise HTTPException(
                status_code=500,
                detail="Cột 'application_status' không tồn tại trong bảng 'candidates'."
            )

        # Kiểm tra ứng viên có tồn tại không
        stmt_check = select(datatable.c.id).where(datatable.c.id == body.candidate_id)
        with engine.connect() as conn:
            result = conn.execute(stmt_check).fetchone()
            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Không tìm thấy ứng viên với ID {body.candidate_id}."
                )

        # Cập nhật status
        stmt_update = (
            update(datatable)
            .where(datatable.c.id == body.candidate_id)
            .values(application_status=body.status)
        )

        with engine.begin() as conn:
            conn.execute(stmt_update)

        return JSONResponse(
            content={
                "success": True,
                "message": f"Đã cập nhật trạng thái của ứng viên {body.candidate_id} thành '{body.status}'.",
                "candidate_id": body.candidate_id,
                "new_status": body.status
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] update_candidate_status: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật trạng thái: {str(e)}")





from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import backend.dataAndModels.config as db_config




DATABASE_URL = db_config.DATABASE_URL

# Tạo engine kết nối đến MySQL
engine = create_engine(DATABASE_URL)
conn = engine.connect()

metadata = MetaData()
metadata.reflect(bind=engine)  # 🔍 Tự động tải cấu trúc tất cả bảng có sẵn
templates = Jinja2Templates(directory="frontend/html")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter()


@router.get("/table/{table_name}/{field}")
def read_table(table_name: str,field: str, db: Session = Depends(get_db)):
    """
    🔹 API tổng quát: Lấy dữ liệu từ bất kỳ bảng nào bằng tên bảng trên URL.
    Ví dụ: GET /table/products  → lấy dữ liệu từ bảng 'products'
    """
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail=f"Bảng '{table_name}' không tồn tại!")

    
    table = metadata.tables[table_name]
    if field not in table.c:
        raise HTTPException(status_code=404, detail=f"Cột '{field}' không tồn tại trong bảng '{table_name}'!")

    column = table.c[field]
    #result = db.execute(table.select()).fetchall().with_only_columns([column])
    #field_result = db.execute(table.select(field))
    #return [dict(row._mapping) for row in result]
    field_data = conn.execute(select(column)).fetchall()
    return [row[0] for row in field_data]


@router.get("/dashboard" , response_class=HTMLResponse)
def get_candidates_tables(request: Request):
    datatable = metadata.tables["candidates"]  # ⚠️ Đổi tên bảng ở đây
    print( "candidates tables: \n")  # In ra tên các cột của bảng
    
    data = conn.execute(select(datatable.c.overall_cv_score,datatable.c.full_name,datatable.c.address)).fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "users": data})





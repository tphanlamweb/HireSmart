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


metadata = MetaData()
metadata.reflect(bind=engine)  # 🔍 Tự động tải cấu trúc tất cả bảng có sẵn
templates = Jinja2Templates(directory="./frontend/html")



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



router = APIRouter()


@router.get("/dashboard" , response_class=HTMLResponse)
def get_candidates_tables(request: Request):
    datatable = metadata.tables["candidates"]  # ⚠️ Đổi tên bảng ở đây
    print( "candidates tables: \n")  # In ra tên các cột của bảng
    conn = engine.connect()
    data = conn.execute(select(datatable.c.overall_cv_score,datatable.c.full_name,datatable.c.address)).fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "users": data})


    


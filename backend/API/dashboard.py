from fastapi import FastAPI, Depends, HTTPException, APIRouter
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path


#   mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
DB_USER = "root"                # 🧑‍💻 Tên user MySQL
DB_PASSWORD = "Lovecode@05"     # 🔑 Mật khẩu MySQL
DB_HOST = "localhost"           # 🖥️  Địa chỉ server (hoặc IP)
DB_PORT = "3306"                # 🌐 Cổng mặc định của MySQL
DB_NAME = "HireSmart"  # 📂 Tên cơ sở dữ liệu bạn đã có

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tạo engine kết nối đến MySQL
engine = create_engine(DATABASE_URL)


metadata = MetaData()
# Đường dẫn template tuyệt đối tới HireSmart/frontend/html
templates_dir = Path(__file__).resolve().parent.parent / "frontend" / "html"
templates = Jinja2Templates(directory=str(templates_dir))



SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



router = APIRouter()



@router.get("/candidates")
def read_users(db: Session = Depends(get_db)):
    if "candidates" not in metadata.tables:
        # Reflect lười biếng nếu chưa có schema
        metadata.reflect(bind=engine)
    if "candidates" not in metadata.tables:
        raise HTTPException(status_code=404, detail="Bảng 'candidates' không tồn tại trong DB!")

    users_table = metadata.tables["candidates"]
    result = db.execute(users_table.select()).fetchall()
    return [dict(row._mapping) for row in result]


@router.get("/table/{table_name}")
def read_table(table_name: str, db: Session = Depends(get_db)):
    if table_name not in metadata.tables:
        metadata.reflect(bind=engine)
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail=f"Bảng '{table_name}' không tồn tại!")

    table = metadata.tables[table_name]
    result = db.execute(table.select()).fetchall()
    return [dict(row._mapping) for row in result]


@router.get("/dashboard" , response_class=HTMLResponse)
def get_candidates_tables(request: Request):
    if "candidates" not in metadata.tables:
        metadata.reflect(bind=engine)
    if "candidates" not in metadata.tables:
        raise HTTPException(status_code=404, detail="Bảng 'candidates' không tồn tại trong DB!")
    datatable = metadata.tables["candidates"]
    print( "candidates tables: \n")  # In ra tên các cột của bảng
    with engine.connect() as conn:
        data = conn.execute(select(datatable.c.id,datatable.c.full_name,datatable.c.phone)).fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "users": data})


    


from sqlalchemy import create_engine, MetaData, Table, select
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import sessionmaker, Session



#   mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
DB_USER = "root"                # 🧑‍💻 Tên user MySQL
DB_PASSWORD = "tPhan186%40"          # 🔑 Mật khẩu MySQL
DB_HOST = "localhost"           # 🖥️  Địa chỉ server (hoặc IP)
DB_PORT = "3306"                # 🌐 Cổng mặc định của MySQL
DB_NAME = "HireSmart"  # 📂 Tên cơ sở dữ liệu bạn đã có

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
metadata = MetaData()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session


#   mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
DB_USER = "root"                # 🧑‍💻 Tên user MySQL
DB_PASSWORD = "tPhan186%40"          # 🔑 Mật khẩu MySQL
DB_HOST = "localhost"           # 🖥️  Địa chỉ server (hoặc IP)
DB_PORT = "3306"                # 🌐 Cổng mặc định của MySQL
DB_NAME = "HireSmart"  # 📂 Tên cơ sở dữ liệu bạn đã có

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tạo engine kết nối đến MySQL
engine = create_engine(DATABASE_URL)


metadata = MetaData()
metadata.reflect(bind=engine)  # 🔍 Tự động tải cấu trúc tất cả bảng có sẵn


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



app = FastAPI(title="FastAPI + MySQL Reflection Example")



@app.get("/users")
def read_users(db: Session = Depends(get_db)):
    """
    Ví dụ: Lấy toàn bộ dữ liệu từ bảng 'users'
    🔸 Chỉ cần đổi 'users' thành tên bảng khác nếu bạn muốn.
    """
    try:
        users_table = metadata.tables["users"]  # ⚠️ Đổi tên bảng ở đây
    except KeyError:
        raise HTTPException(status_code=404, detail="Bảng 'users' không tồn tại trong DB!")

    result = db.execute(users_table.select()).fetchall()
    print(result)
    return [dict(row._mapping) for row in result]


@app.get("/table/{table_name}")
def read_table(table_name: str, db: Session = Depends(get_db)):
    """
    🔹 API tổng quát: Lấy dữ liệu từ bất kỳ bảng nào bằng tên bảng trên URL.
    Ví dụ: GET /table/products  → lấy dữ liệu từ bảng 'products'
    """
    if table_name not in metadata.tables:
        raise HTTPException(status_code=404, detail=f"Bảng '{table_name}' không tồn tại!")

    table = metadata.tables[table_name]
    result = db.execute(table.select()).fetchall()
    return [dict(row._mapping) for row in result]


@app.get("/")
def root():
    """
    Trang chào - liệt kê tất cả các bảng hiện có trong database.
    """
    return {"database": DB_NAME, "tables": list(metadata.tables.keys())}


datatable = metadata.tables["candidates"]  # ⚠️ Đổi tên bảng ở đây
print( "candidates tables: \n")  # In ra tên các cột của bảng
conn = engine.connect()
for row in conn.execute(select(datatable.c.id,datatable.c.full_name,datatable.c.phone)).fetchall():
    print(row)
    


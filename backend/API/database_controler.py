"""
=============================================
🔗 FastAPI + SQLAlchemy Reflection + MySQL
Tự động kết nối và phản chiếu (reflect) các bảng có sẵn trong cơ sở dữ liệu.
=============================================
"""

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker, Session

# ============================================================
# 1️⃣ CẤU HÌNH KẾT NỐI DATABASE (Connect String)
# ------------------------------------------------------------
# Mẫu connect string chuẩn:
#   mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
# Thay đổi thông tin bên dưới cho phù hợp với máy bạn
# ============================================================

DB_USER = "root"                # 🧑‍💻 Tên user MySQL
DB_PASSWORD = "tPhan186%40"          # 🔑 Mật khẩu MySQL
DB_HOST = "localhost"           # 🖥️  Địa chỉ server (hoặc IP)
DB_PORT = "3306"                # 🌐 Cổng mặc định của MySQL
DB_NAME = "HireSmart"  # 📂 Tên cơ sở dữ liệu bạn đã có

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tạo engine kết nối đến MySQL
engine = create_engine(DATABASE_URL)

# ============================================================
# 2️⃣ TỰ ĐỘNG TẢI CẤU TRÚC CÁC BẢNG CÓ SẴN (REFLECTION)
# ------------------------------------------------------------
# MetaData() giúp lưu trữ cấu trúc các bảng trong DB
# reflect() sẽ quét toàn bộ các bảng hiện có
# ============================================================

metadata = MetaData()
metadata.reflect(bind=engine)  # 🔍 Tự động tải cấu trúc tất cả bảng có sẵn

# Kiểm tra xem đã load được bảng nào (có thể in ra để debug)
print("✅ Loaded tables:", metadata.tables.keys())

# ============================================================
# 3️⃣ TẠO SESSION LÀM VIỆC VỚI DATABASE
# ------------------------------------------------------------
# SessionLocal giúp bạn mở/đóng kết nối với DB khi thực hiện query
# ============================================================

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# 4️⃣ KHỞI TẠO ỨNG DỤNG FASTAPI
# ============================================================

app = FastAPI(title="FastAPI + MySQL Reflection Example")

# ============================================================
# 5️⃣ VÍ DỤ CỤ THỂ: LẤY DỮ LIỆU TỪ BẢNG CÓ SẴN
# ------------------------------------------------------------
# Bạn chỉ cần đổi tên bảng trong dòng:
#     users_table = metadata.tables["<tên_bảng_của_bạn>"]
# ============================================================

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


datatable = metadata.tables["audit_logs"]  # ⚠️ Đổi tên bảng ở đây
print( "audit_log tables: \n",datatable.columns.keys())  # In ra tên các cột của bảng
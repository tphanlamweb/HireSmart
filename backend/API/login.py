from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import random, string, requests

# ==============================
# CONFIG
# ==============================
try:
    from backend.dataAndModels.config import DATABASE_URL  # prefer shared config
except Exception:
    DATABASE_URL = "mysql+pymysql://root:@localhost/hiresmart"  # fallback, edit if needed


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==============================
# CONNECT MYSQL
# ==============================
engine = create_engine(DATABASE_URL)
metadata = MetaData()

users_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(255)),
    Column("email", String(255)),
    Column("password_hash", String(255)),  # store hashed password
    Column("full_name", String(255)),
    Column("phone", String(20)),
    Column("role_id", Integer),
    Column("is_active", Integer)
)

otps = {}
SessionLocal = sessionmaker(bind=engine)

# ==============================
# ROUTER
# ==============================
router = APIRouter()

# ==============================
# MODELS
# ==============================
class LoginModel(BaseModel):
    email: str
    password: str

class ResetPasswordModel(BaseModel):
    email: str
    otp: str
    new_password: str

# ==============================
# DB SESSION
# ==============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================
# 1️⃣ LOGIN
# ==============================
@router.post("/login")
def login(data: LoginModel, db=Depends(get_db)):

    user = db.execute(
        users_table.select().where(users_table.c.email == data.email)
    ).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại")

    if not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Sai mật khẩu")

    if user.is_active != 1:
        raise HTTPException(status_code=403, detail="Tài khoản bị khóa")

    return {
        "message": "Đăng nhập thành công",
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role_id": user.role_id
    }

# ==============================
# 2️⃣ QUÊN MẬT KHẨU
# ==============================
@router.post("/forgot-password")
def forgot_password(email: str = Form(...), db=Depends(get_db)):

    user = db.execute(
        users_table.select().where(users_table.c.email == email)
    ).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Email không tồn tại")

    otp = ''.join(random.choices(string.digits, k=6))
    otps[email] = otp

    print(f"OTP cho {email}: {otp}")

    return {"message": "OTP đã được gửi vào email"}

# ==============================
# 3️⃣ RESET PASSWORD
# ==============================
@router.post("/reset-password")
def reset_password(data: ResetPasswordModel, db=Depends(get_db)):

    if data.email not in otps or otps[data.email] != data.otp:
        raise HTTPException(status_code=400, detail="OTP không đúng")

    new_hashed = pwd_context.hash(data.new_password)

    db.execute(
        users_table.update()
        .where(users_table.c.email == data.email)
        .values(password_hash=new_hashed)
    )
    db.commit()

    del otps[data.email]

    return {"message": "Đổi mật khẩu thành công"}

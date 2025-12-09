from fastapi import APIRouter, HTTPException, Depends, Form
from pydantic import BaseModel
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
import random, string, requests

# ==============================
# CONFIG
# ==============================
DATABASE_URL = "mysql+pymysql://root:@localhost/hiresmart"

GOOGLE_CLIENT_ID = "194527014663-6smkugkc8ci5s4f7algohiir2j1k3tsi.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

GOOGLE_REDIRECT_URI = "http://127.0.0.1:8000/login/google-callback"

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
    Column("password_hash", String(255)),
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

# ==============================
# 4️⃣ TẠO URL LOGIN GOOGLE
# ==============================
@router.get("/google")
def google_login():
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )
    return {"url": google_auth_url}

# ==============================
# 5️⃣ GOOGLE CALLBACK
# ==============================
@router.get("/google-callback")
def google_callback(code: str, db=Depends(get_db)):

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_res = requests.post(token_url, data=data).json()
    access_token = token_res.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Google login failed")

    userinfo = requests.get(
        "https://openidconnect.googleapis.com/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = userinfo["email"]
    name = userinfo.get("name", "Google User")

    db_user = db.execute(
        users_table.select().where(users_table.c.email == email)
    ).fetchone()

    if not db_user:
        default_password = pwd_context.hash("google_default_pwd")

        db.execute(
            users_table.insert().values(
                username=email.split("@")[0],
                email=email,
                password_hash=default_password,
                full_name=name,
                role_id=3,
                is_active=1
            )
        )
        db.commit()

    return {"message": "Đăng nhập Google thành công", "email": email}

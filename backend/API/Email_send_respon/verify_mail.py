import csv
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import MetaData, create_engine, select, update
from backend.dataAndModels.config import DATABASE_URL

router = APIRouter()

# ==============================
# Config & constants
# ==============================
DB_USER = "root"
DB_PASSWORD = "123456"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "HireSmart"

TOKEN_FILE = Path(__file__).resolve().parents[2] / "results" / "candidate_with_token.csv"

# ==============================
# Database setup
# ==============================
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

candidates_table = metadata.tables.get("candidates")

if candidates_table is None:
    raise RuntimeError("Không tìm thấy bảng 'candidates' trong cơ sở dữ liệu.")


# ==============================
# Helpers
# ==============================
def read_token_map() -> dict[int, str]:
    """
    Đọc file CSV candidate_with_token.csv và trả về dict mapping candidate_id -> token.
    Bỏ qua các dòng trống hoặc không hợp lệ.
    """
    if not TOKEN_FILE.exists():
        return {}

    token_map: dict[int, str] = {}
    with TOKEN_FILE.open("r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Bỏ qua dòng trống
            if not row or not any(row.values()):
                continue
            try:
                candidate_id = int(row.get("id", 0))
            except (TypeError, ValueError):
                continue
            token = row.get("token", "").strip()
            # Chỉ thêm vào map nếu có cả candidate_id và token hợp lệ
            if candidate_id > 0 and token:
                token_map[candidate_id] = token
    return token_map


def find_candidate_by_token(token: str, token_map: Optional[dict[int, str]] = None) -> Optional[int]:
    """
    Tìm candidate_id dựa vào token. Trả về None nếu không tìm thấy.
    Nếu token_map được cung cấp, sử dụng nó; nếu không, đọc từ CSV.
    """
    if token_map is None:
        token_map = read_token_map()
    
    token = token.strip()
    for candidate_id, stored_token in token_map.items():
        if stored_token.strip() == token:
            return candidate_id
    return None


def update_application_status(candidate_id: int, new_status: str) -> bool:
    """
    Cập nhật application_status của ứng viên trong database.
    Trả về True nếu thành công, False nếu không tìm thấy ứng viên.
    """
    if "application_status" not in candidates_table.c:
        print("[ERROR] Cột 'application_status' không tồn tại trong bảng 'candidates'")
        raise HTTPException(
            status_code=500,
            detail="Cột 'application_status' không tồn tại trong bảng 'candidates'."
        )

    print(f"[DEBUG] Tạo UPDATE statement: candidate_id={candidate_id}, new_status={new_status}")
    stmt = (
        update(candidates_table)
        .where(candidates_table.c.id == candidate_id)
        .values(application_status=new_status)
    )

    # Sử dụng engine.begin() để đảm bảo transaction được commit
    with engine.begin() as conn:
        result = conn.execute(stmt)
        rows_affected = result.rowcount
        print(f"[DEBUG] UPDATE đã thực thi, rows_affected={rows_affected}")
        
        # Kiểm tra lại sau khi update
        check_stmt = select(candidates_table.c.application_status).where(
            candidates_table.c.id == candidate_id
        )
        check_result = conn.execute(check_stmt).fetchone()
        if check_result:
            print(f"[DEBUG] Xác nhận: application_status hiện tại trong DB = '{check_result[0]}'")
        
        return rows_affected > 0


# ==============================
# Routes
# ==============================
@router.get("/verify", response_class=HTMLResponse)
def verify_email_token(token: str = Query(..., description="Token xác nhận từ email")):
    """
    Endpoint xử lý xác nhận email khi người dùng nhấn vào link trong email.
    URL: /verify?token=<token>
    
    Khi nhận được token hợp lệ:
    1. Tìm candidate_id tương ứng với token
    2. Cập nhật application_status thành 'accepted' trong database
    3. Trả về trang HTML thông báo kết quả
    """
    if not token or not token.strip():
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Xác nhận thất bại</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                    .container { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .error { color: #e74c3c; font-size: 24px; margin-bottom: 20px; }
                    .message { color: #666; line-height: 1.6; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">❌</div>
                    <h1>Xác nhận thất bại</h1>
                    <p class="message">Token không hợp lệ hoặc đã hết hạn.</p>
                </div>
            </body>
            </html>
            """,
            status_code=400
        )

    # Đọc token map từ CSV
    token_map = read_token_map()
    print(f"[DEBUG] Đã đọc {len(token_map)} token từ file candidate_with_token.csv")
    if token_map:
        print(f"[DEBUG] Các candidate_id có token: {list(token_map.keys())}")
    
    # Tìm candidate_id từ token
    candidate_id = find_candidate_by_token(token, token_map)
    
    if candidate_id is None:
        print(f"[WARNING] Không tìm thấy candidate_id cho token: {token[:20]}...")
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Xác nhận thất bại</title>
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }
                    .container { background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .error { color: #e74c3c; font-size: 24px; margin-bottom: 20px; }
                    .message { color: #666; line-height: 1.6; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">❌</div>
                    <h1>Xác nhận thất bại</h1>
                    <p class="message">Không tìm thấy ứng viên với token này. Vui lòng kiểm tra lại link trong email.</p>
                </div>
            </body>
            </html>
            """,
            status_code=404
        )

    # Cập nhật application_status thành 'accepted'
    try:
        print(f"[DEBUG] Bắt đầu cập nhật application_status cho candidate_id={candidate_id} thành 'accepted'")
        success = update_application_status(candidate_id, "accepted")
        print(f"[DEBUG] Kết quả cập nhật: success={success}")
        
        if not success:
            print(f"[ERROR] Không tìm thấy ứng viên với ID {candidate_id} trong database")
            raise HTTPException(
                status_code=404,
                detail=f"Không tìm thấy ứng viên với ID {candidate_id}."
            )
        
        print(f"[SUCCESS] Đã cập nhật thành công application_status='accepted' cho candidate_id={candidate_id}")

        # Lấy thông tin ứng viên để hiển thị
        stmt = select(
            candidates_table.c.id,
            candidates_table.c.full_name,
            candidates_table.c.email,
        ).where(candidates_table.c.id == candidate_id)

        with engine.connect() as conn:
            row = conn.execute(stmt).fetchone()
            candidate_name = row.full_name if row else "Ứng viên"

        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html lang="vi">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Xác nhận thành công</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5; }}
                    .container {{ background: white; padding: 40px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .success {{ color: #27ae60; font-size: 48px; margin-bottom: 20px; }}
                    h1 {{ color: #2c3e50; margin-bottom: 20px; }}
                    .message {{ color: #666; line-height: 1.8; font-size: 16px; }}
                    .candidate-name {{ color: #2563eb; font-weight: bold; font-size: 18px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">✅</div>
                    <h1>Xác nhận thành công!</h1>
                    <p class="message">
                        Cảm ơn bạn <span class="candidate-name">{candidate_name}</span> đã xác nhận email.
                    </p>
                    <p class="message">
                        Trạng thái ứng tuyển của bạn đã được cập nhật thành <strong>"Đã chấp nhận"</strong>.
                    </p>
                    <p class="message" style="margin-top: 30px; color: #999; font-size: 14px;">
                        Bạn có thể đóng trang này.
                    </p>
                </div>
            </body>
            </html>
            """
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi cập nhật trạng thái: {str(e)}"
        )


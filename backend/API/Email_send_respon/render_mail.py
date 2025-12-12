import csv
import os
import re
from collections import UserDict
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import MetaData, create_engine, select
from backend.dataAndModels.config import DATABASE_URL

router = APIRouter()

# ==============================
# Config & constants
# ==============================


# URL base cho link xác nhận email. Trong production, set biến môi trường VERIFY_EMAIL_URL
# Ví dụ: export VERIFY_EMAIL_URL="https://yourdomain.com/verify?token="
VERIFICATION_BASE_URL = os.environ.get("VERIFY_EMAIL_URL", "http://127.0.0.1:8000/verify?token=")

TOKEN_FILE = Path(__file__).resolve().parents[2] / "results" / "candidate_with_token.csv"

# ==============================
# Database setup
# ==============================
engine = create_engine(DATABASE_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

candidates_table = metadata.tables.get("candidates")
email_templates_table = metadata.tables.get("email_templates")

if candidates_table is None:
    raise RuntimeError("Không tìm thấy bảng 'candidates' trong cơ sở dữ liệu.")
if email_templates_table is None:
    raise RuntimeError("Không tìm thấy bảng 'email_templates' trong cơ sở dữ liệu.")


# ==============================
# Pydantic schemas
# ==============================
class BulkEmailRequest(BaseModel):
    template_id: int = Field(..., description="ID mẫu email cần sử dụng")
    candidate_ids: List[int] = Field(..., description="Danh sách ID ứng viên được chọn")
    extra_context: Dict[str, str] = Field(default_factory=dict, description="Các biến bổ sung cho template")


# ==============================
# Helpers
# ==============================
class SafeDict(UserDict):
    """Dict trả về chuỗi rỗng nếu key không tồn tại (tránh KeyError khi format)."""

    def __missing__(self, key):
        return ""


def read_token_map() -> Dict[int, str]:
    """
    Đọc file CSV candidate_with_token.csv và trả về dict mapping candidate_id -> token.
    Bỏ qua các dòng trống hoặc không hợp lệ.
    """
    if not TOKEN_FILE.exists():
        return {}

    token_map: Dict[int, str] = {}
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


def format_template(template: Optional[str], context: Dict[str, str]) -> str:
    if not template:
        return ""
    return template.format_map(SafeDict(context)).strip()


def add_verify_button_to_email(body: str, verify_link: str) -> str:
    """
    Tự động thêm button xác nhận vào email body nếu có verify_link.
    Button sẽ được thêm vào cuối email nếu chưa có.
    """
    if not verify_link or not verify_link.strip():
        return body
    
    # Kiểm tra xem body đã có verify_link hoặc button verify chưa
    # (kiểm tra bằng cách tìm link verify trong body)
    if "/verify?token=" in body or "{verify_link}" in body:
        # Nếu đã có, chỉ cần thay thế placeholder {verify_link} nếu có
        body = body.replace("{verify_link}", verify_link)
        return body
    
    # Tạo HTML button đẹp
    verify_button_html = f"""
    <div style="text-align: center; margin: 30px 0;">
        <a href="{verify_link}" 
           style="display: inline-block; 
                  padding: 15px 30px; 
                  background-color: #2563eb; 
                  color: #ffffff; 
                  text-decoration: none; 
                  border-radius: 8px; 
                  font-weight: bold; 
                  font-size: 16px;
                  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            ✅ Xác nhận ứng tuyển
        </a>
    </div>
    <p style="text-align: center; color: #666; font-size: 12px; margin-top: 10px;">
        Hoặc copy link sau vào trình duyệt: <br>
        <a href="{verify_link}" style="color: #2563eb; word-break: break-all;">{verify_link}</a>
    </p>
    """
    
    # Nếu body là HTML, thêm button vào
    if _looks_like_html(body):
        # Thêm button trước thẻ đóng </body> hoặc vào cuối
        if "</body>" in body.lower():
            body = body.replace("</body>", verify_button_html + "</body>")
        else:
            body = body + verify_button_html
    else:
        # Nếu là plain text, thêm link đơn giản
        body = body + f"\n\n---\nXác nhận ứng tuyển: {verify_link}"
    
    return body


def _looks_like_html(text: str) -> bool:
    """Kiểm tra xem text có phải HTML không."""
    return bool(text and re.search(r"<\/?\w+[^>]*>", text))


def fetch_email_template(template_id: int) -> Dict:
    stmt = (
        select(
            email_templates_table.c.id,
            email_templates_table.c.template_name,
            email_templates_table.c.template_type,
            email_templates_table.c.subject_template,
            email_templates_table.c.body_template,
        )
        .where(email_templates_table.c.id == template_id)
    )
    with engine.connect() as conn:
        row = conn.execute(stmt).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy template id = {template_id}")
    return dict(row._mapping)


def fetch_candidates(candidate_ids: List[int]) -> List[Dict]:
    if not candidate_ids:
        return []

    columns = [
        candidates_table.c.id,
        candidates_table.c.full_name,
        candidates_table.c.email,
    ]

    if "job_title" in candidates_table.c:
        columns.append(candidates_table.c.job_title)
    if "position" in candidates_table.c:
        columns.append(candidates_table.c.position)
    if "overall_cv_score" in candidates_table.c:
        columns.append(candidates_table.c.overall_cv_score)

    stmt = select(*columns).where(candidates_table.c.id.in_(candidate_ids))

    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return [dict(row._mapping) for row in rows]


def build_context(candidate: Dict, extra_context: Dict[str, str], token_map: Dict[int, str]) -> Dict[str, str]:
    token = token_map.get(candidate["id"])
    inferred_job_title = (
        candidate.get("job_title")
        or candidate.get("position")
        or extra_context.get("job_title")
        or extra_context.get("position")
        or ""
    )
    context = {
        "candidate_name": candidate.get("full_name", ""),
        "candidate_email": candidate.get("email", ""),
        "job_title": inferred_job_title,
        "position": inferred_job_title,
        "company_name": extra_context.get("company_name", "HireSmart"),
        "interview_date": extra_context.get("interview_date", ""),
        "interview_time": extra_context.get("interview_time", ""),
        "interview_location": extra_context.get("interview_location", ""),
        "custom_message": extra_context.get("custom_message", ""),
        "token": token or "",
        "verify_link": f"{VERIFICATION_BASE_URL}{token}" if token else "",
    }
    # Ưu tiên các biến bổ sung nếu người dùng truyền vào
    context.update(extra_context)
    return context


# ==============================
# Routes
# ==============================
@router.get("/templates")
def list_email_templates():
    """Trả về danh sách template email khả dụng."""
    stmt = select(
        email_templates_table.c.id,
        email_templates_table.c.template_name,
        email_templates_table.c.template_type,
        email_templates_table.c.subject_template,
        email_templates_table.c.body_template,
    ).order_by(email_templates_table.c.template_name.asc())

    with engine.connect() as conn:
        rows = conn.execute(stmt).fetchall()

    return [dict(row._mapping) for row in rows]


@router.post("/render-bulk")
def render_bulk_emails(payload: BulkEmailRequest):
    """Render nội dung email cho nhiều ứng viên dựa vào 1 template."""
    if not payload.candidate_ids:
        raise HTTPException(status_code=400, detail="Danh sách ứng viên không được để trống.")

    template = fetch_email_template(payload.template_id)
    candidates = fetch_candidates(payload.candidate_ids)

    if not candidates:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên phù hợp.")

    token_map = read_token_map()
    print(f"[DEBUG] Đã đọc {len(token_map)} token từ file candidate_with_token.csv")
    if token_map:
        print(f"[DEBUG] Các candidate_id có token: {list(token_map.keys())}")
    
    emails = []
    missing_candidates = []
    missing_tokens = []

    for candidate in candidates:
        # Lấy token từ CSV cho ứng viên này
        candidate_token = token_map.get(candidate["id"])
        if not candidate_token:
            missing_tokens.append(candidate["id"])
            print(f"[WARNING] Không tìm thấy token cho candidate_id={candidate['id']} trong CSV")
        
        context = build_context(candidate, payload.extra_context, token_map)
        subject = format_template(template.get("subject_template"), context)
        body = format_template(template.get("body_template"), context)
        
        # Tự động thêm button xác nhận vào email nếu có verify_link
        verify_link = context.get("verify_link", "")
        if verify_link:
            body = add_verify_button_to_email(body, verify_link)

        if not candidate.get("email"):
            missing_candidates.append(candidate["id"])
            continue

        emails.append(
            {
                "candidate_id": candidate["id"],
                "candidate_name": candidate.get("full_name", ""),
                "email": candidate.get("email", ""),
                "subject": subject,
                "body": body,
            }
        )

    response = {
        "template": {
            "id": template["id"],
            "name": template["template_name"],
            "type": template["template_type"],
        },
        "emails": emails,
        "skipped_candidate_ids": missing_candidates,
        "missing_token_ids": missing_tokens,  # Thêm thông tin về các ứng viên không có token
    }
    
    if missing_tokens:
        print(f"[WARNING] Có {len(missing_tokens)} ứng viên không có token trong CSV: {missing_tokens}")
    
    return response
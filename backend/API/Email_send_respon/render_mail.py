import csv
import os
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

VERIFICATION_BASE_URL = os.environ.get("VERIFY_EMAIL_URL", "https://yourdomain.com/verify?token=")

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
    if not TOKEN_FILE.exists():
        return {}

    token_map: Dict[int, str] = {}
    with TOKEN_FILE.open("r", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                candidate_id = int(row.get("id", 0))
            except (TypeError, ValueError):
                continue
            token = row.get("token")
            if candidate_id and token:
                token_map[candidate_id] = token
    return token_map


def format_template(template: Optional[str], context: Dict[str, str]) -> str:
    if not template:
        return ""
    return template.format_map(SafeDict(context)).strip()


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
    emails = []
    missing_candidates = []

    for candidate in candidates:
        context = build_context(candidate, payload.extra_context, token_map)
        subject = format_template(template.get("subject_template"), context)
        body = format_template(template.get("body_template"), context)

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
    }
    return response
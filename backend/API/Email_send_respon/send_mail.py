"""
Endpoints để gửi email hàng loạt thông qua Gmail SMTP.
Sử dụng chung payload với render_mail.BulkEmailRequest.
"""

import os
import re
import smtplib
import ssl
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from fastapi import APIRouter, HTTPException

from .render_mail import BulkEmailRequest, render_bulk_emails

router = APIRouter()

# ==============================
# SMTP configuration
# ==============================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SMTP_EMAIL", "hiresmart2525@gmail.com")
APP_PASSWORD = os.getenv("SMTP_PASSWORD", "kefh hlov mtjc oiis")

logger = logging.getLogger(__name__)


def _looks_like_html(text: str) -> bool:
    return bool(text and re.search(r"<\/?\w+[^>]*>", text))


def _build_message(to_email: str, subject: str, content: str):
    """
    Trả về MIMEMultipart message có cả plain và html (nếu cần).
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject or "(No Subject)"

    plain = re.sub(r"<[^>]+>", "", content or "")
    msg.attach(MIMEText(plain, "plain"))

    if _looks_like_html(content):
        msg.attach(MIMEText(content, "html"))

    return msg


def send_email(server: smtplib.SMTP, to_email: str, subject: str, content: str):
    """
    Gửi 1 email sử dụng connection SMTP đã mở (server).
    """
    if not to_email:
        raise ValueError("Thiếu địa chỉ email người nhận.")
    msg = _build_message(to_email, subject, content)
    server.send_message(msg)


@router.post("/send-bulk")
def send_bulk_emails(payload: BulkEmailRequest):
    """
    Gửi email cho nhiều ứng viên dựa trên template đã chọn.
    Payload giống với /email/render-bulk (template_id, candidate_ids, extra_context).
    """
    render_result = render_bulk_emails(payload)
    emails = render_result.get("emails", [])

    if not emails:
        raise HTTPException(
            status_code=400,
            detail="Không có email hợp lệ để gửi. Kiểm tra lại template hoặc danh sách ứng viên.",
        )

    failed: List[dict] = []
    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, APP_PASSWORD)

            for email in emails:
                to = email.get("email")
                subject = email.get("subject", "")
                body = email.get("body", "")
                try:
                    send_email(server, to, subject, body)
                except Exception as exc:  # pylint: disable=broad-except
                    logger.exception("Failed to send to %s", to)
                    failed.append(
                        {
                            "candidate_id": email.get("candidate_id"),
                            "email": to,
                            "error": str(exc),
                        }
                    )
    except Exception as conn_exc:
        raise HTTPException(status_code=500, detail=f"SMTP connection failed: {conn_exc}")

    sent_count = len(emails) - len(failed)
    return {
        "template": render_result.get("template"),
        "total": len(emails),
        "sent": sent_count,
        "failed": failed,
        "skipped_candidate_ids": render_result.get("skipped_candidate_ids", []),
    }

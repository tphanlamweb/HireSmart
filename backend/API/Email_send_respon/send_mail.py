import os
import smtplib
import ssl
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import APIRouter
from render_mail import render_mail

router= APIRouter()

CANDIDATE_FILE= os.path.join(os.path.dirname(__file__), "results","candidate_with_token.csv")

# cấu hình SMTP Gmail
SMTP_SEVER= os.getenv("SMTP_SEVER","smtp.gmail.com")
SMTP_PORT= int(os.getenv("SMTP_POST",587))
SMTP_EMAIL= os.getenv("SMTP_EMAIL","your_email@gmail.com")
SMTP_PASSWORD= os.getenv("SMTP_PASSWORD","your_app password")

def send_email(to_email: str, subject: str, content: str):
    """
    Gửi email văn bản thuần (plain text) qua SMTP Gmail.
    """
    message= MIMEMultipart()
    message["from"]= SMTP_EMAIL
    message["To"]= to_email
    message["Subject"]=subject
    message.attach(MIMEText(content,"plain"))
    
    context=ssl.create_default_context()
    with smtplib.SMTP(SMTP_SEVER,SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(SMTP_EMAIL,SMTP_PASSWORD)
        server.send_message(SMTP_EMAIL,to_email,message.as_string())
        
@router.post("/send_mail/{candidate_id}")
def send_mail_to_candidate(candidate_id: int):
    """
    Gửi email cho 1 ứng viên theo ID.
    """
    if not os.path.exists(CANDIDATE_FILE):
         return {"error": "Không tìm thấy file ứng viên."}
     
    df = pd.read_csv(CANDIDATE_FILE)
    candidate = df.loc[df['id'] == candidate_id]

    if candidate.empty:
        return {"error": f"Không tìm thấy ứng viên id = {candidate_id}"}

    row = candidate.iloc[0]
    to_email = row.get("email")
    full_name = row.get("full_name")
    position = row.get("position", "your applied position")
    token = row.get("token")

    if not to_email:
        return {"error": "Ứng viên không có email."}

    # ✅ Sử dụng hàm render từ file Render_mail.py
    content = render_mail(full_name, position, token)

    try:
        send_email(to_email, f"Application Confirmation - {position}", content)
        return {"message": f"✅ Email đã gửi tới {to_email}"}
    except Exception as e:
        return {"error": f"Gửi email thất bại tới {to_email}", "detail": str(e)}

@router.post("/send_mail_all")
def send_mail_to_all():
    """
    Gửi email cho tất cả ứng viên trong file CSV.
    """
    if not os.path.exists(CANDIDATE_FILE):
        return {"error": "Không tìm thấy file ứng viên."}

    df = pd.read_csv(CANDIDATE_FILE)
    sent_count = 0
    failed = []

    for _, row in df.iterrows():
        to_email = row.get("email")
        full_name = row.get("full_name")
        position = row.get("position", "your applied position")
        token = row.get("token")

        if not to_email:
            failed.append({"email": None, "reason": "Thiếu email"})
            continue

        content = render_mail(full_name, position, token)

        try:
            send_email(to_email, f"Application Confirmation - {position}", content)
            sent_count += 1
        except Exception as e:
            failed.append({"email": to_email, "reason": str(e)})

    return {
        "total": len(df),
        "sent": sent_count,
        "failed": failed
    }


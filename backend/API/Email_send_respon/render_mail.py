import os
import pandas as pd
from fastapi import APIRouter

router = APIRouter()

# 📝 Đường dẫn đến file ứng viên có token
CANDIDATE_FILE = os.path.join(os.path.dirname(__file__), "results", "candidate_with_token.csv")

# URL xác thực cơ bản(thay bằng domain thật khi deploy)
BASE_VERIFILE_URL= "https://yourdomain.com/verify?token="

# Mẫu nội dung Email 
EMAIL_TEMPLATE= """
Hi {full_name},

Thank you for applying for the {position} position at our company.

Please confirm your application by clicking the following link:
👉 {verify_link}

If you did not perform this action, please ignore this email.

Best regards,  
HR Department
"""

@router.get("/render_mail/{candidate_id}")
def render_mail(candidate_id: int):
    # API: Render nội dung mail cho ứng viên dựa vào ID trong file CSV
    if not os.path.exists(CANDIDATE_FILE):
        return{"error":"Không tìm thấy file candidate_with_token.csv"}

    df = pd.read_csv(CANDIDATE_FILE)
    candidate= df.loc[df['id']== candidate_id]    
    
    if candidate.empty:
        return{"error":f"Không tìm thấy ứng viên có id = {candidate_id}"
               }
    row = candidate.iloc[0]
    Verify_link = BASE_VERIFILE_URL + str(row["token"])
    
    # Render nội dung email từ template
    mail_content= EMAIL_TEMPLATE.format(
        full_name=row.get("full_name",""),
        position=row.get("position","your applied postion"),
        Verify_link=Verify_link
        
    )
    return {
        "id": int(row["id"]),
        "email": row.get("email", ""),
        "token": row.get("token", ""),
        "mail_content": mail_content.strip()
    }
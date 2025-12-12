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

# Sử dụng trực tiếp DATABASE_URL được cấu hình trong backend.dataAndModels.config
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


# ==============================
# Template-specific context mapping
# ==============================
def get_template_specific_fields(template_type: str) -> Dict[str, Dict[str, any]]:
    """
    Trả về mapping các trường thông tin bổ sung cho từng loại template.
    Format: {
        "field_name": {
            "required": bool,      # Trường bắt buộc hay không
            "default": str,        # Giá trị mặc định nếu không có
            "description": str     # Mô tả trường
        }
    }
    """
    # Chuẩn hóa template_type (loại bỏ khoảng trắng, chuyển thành chữ thường)
    template_type = template_type.strip().lower()
    
    # Ánh xạ các tên template (tiếng Việt/tiếng Anh) sang template_type chuẩn
    template_type_mapping = {
        "interview_invitation": "interview_invitation",
        "mời phỏng vấn": "interview_invitation",
        "mời phỏng vấn vòng 1": "interview_invitation",
        "interview invitation": "interview_invitation",
        "interview invitation round 1": "interview_invitation",
        
        "rejection": "rejection",
        "từ chối": "rejection",
        "từ chối ứng viên": "rejection",
        "rejection letter": "rejection",
        
        "offer": "offer",
        "đề nghị": "offer",
        "offer letter": "offer",
        "đề nghị việc làm": "offer",
        
        "acceptance": "acceptance",
        "xác nhận": "acceptance",
        "offer acceptance": "acceptance",
        
        "welcome": "welcome",
        "chào mừng": "welcome",
        "welcome letter": "welcome",
    }
    
    # Chuẩn hóa template_type
    normalized_type = template_type_mapping.get(template_type, template_type)
    
    template_fields = {
        "interview_invitation": {
            "interview_date": {"required": False, "default": "", "description": "Ngày phỏng vấn / Interview Date"},
            "interview_time": {"required": False, "default": "", "description": "Giờ phỏng vấn / Interview Time"},
            "interview_location": {"required": False, "default": "", "description": "Địa điểm phỏng vấn / Interview Location"},
            "job_title": {"required": False, "default": "", "description": "Vị trí ứng tuyển / Job Title"},
            "company_name": {"required": False, "default": "HireSmart", "description": "Tên công ty / Company Name"},
            "custom_message": {"required": False, "default": "", "description": "Ghi chú thêm / Additional Notes"},
        },
        "rejection": {
            "job_title": {"required": False, "default": "", "description": "Vị trí ứng tuyển / Job Title"},
            "company_name": {"required": False, "default": "HireSmart", "description": "Tên công ty / Company Name"},
            "rejection_reason": {"required": False, "default": "", "description": "Lý do từ chối / Rejection Reason"},
            "feedback": {"required": False, "default": "", "description": "Phản hồi / Feedback"},
            "custom_message": {"required": False, "default": "", "description": "Thông điệp tùy chỉnh / Custom Message"},
        },
        "offer": {
            "job_title": {"required": False, "default": "", "description": "Vị trí được đề xuất / Offered Position"},
            "company_name": {"required": False, "default": "HireSmart", "description": "Tên công ty / Company Name"},
            "start_date": {"required": False, "default": "", "description": "Ngày bắt đầu / Start Date"},
            "salary": {"required": False, "default": "", "description": "Mức lương / Salary"},
            "offer_details": {"required": False, "default": "", "description": "Chi tiết đề nghị / Offer Details"},
            "response_deadline": {"required": False, "default": "", "description": "Hạn chấp nhận / Response Deadline"},
            "custom_message": {"required": False, "default": "", "description": "Ghi chú thêm / Additional Notes"},
        },
        "acceptance": {
            "job_title": {"required": False, "default": "", "description": "Vị trí công việc / Job Title"},
            "company_name": {"required": False, "default": "HireSmart", "description": "Tên công ty / Company Name"},
            "start_date": {"required": False, "default": "", "description": "Ngày bắt đầu / Start Date"},
            "onboarding_info": {"required": False, "default": "", "description": "Thông tin onboarding / Onboarding Information"},
            "contact_person": {"required": False, "default": "", "description": "Người liên hệ / Contact Person"},
            "custom_message": {"required": False, "default": "", "description": "Ghi chú thêm / Additional Notes"},
        },
        "welcome": {
            "job_title": {"required": False, "default": "", "description": "Vị trí công việc / Job Title"},
            "company_name": {"required": False, "default": "HireSmart", "description": "Tên công ty / Company Name"},
            "start_date": {"required": False, "default": "", "description": "Ngày bắt đầu / Start Date"},
            "work_location": {"required": False, "default": "", "description": "Địa điểm làm việc / Work Location"},
            "custom_message": {"required": False, "default": "", "description": "Ghi chú thêm / Additional Notes"},
        },
    }
    
    # Trả về các trường cho template_type chuẩn hóa, hoặc trường chung nếu không tìm thấy
    if normalized_type in template_fields:
        return template_fields[normalized_type]
    
    # Template mặc định/chung: chỉ có các trường cơ bản
    return {
        "job_title": {"required": False, "default": "", "description": "Vị trí công việc / Job Title"},
        "company_name": {"required": False, "default": "HireSmart", "description": "Tên công ty / Company Name"},
        "custom_message": {"required": False, "default": "", "description": "Thông điệp tùy chỉnh / Custom Message"},
    }


def process_extra_context_for_template(
    extra_context: Dict[str, str], 
    template_type: str
) -> Dict[str, str]:
    """
    Xử lý và lọc extra_context theo template_type.
    Chỉ giữ lại các trường phù hợp với loại template và điền giá trị mặc định nếu thiếu.
    """
    # Chuẩn hóa template_type
    template_type_mapping = {
        "interview_invitation": "interview_invitation",
        "mời phỏng vấn": "interview_invitation",
        "mời phỏng vấn vòng 1": "interview_invitation",
        "interview invitation": "interview_invitation",
        "interview invitation round 1": "interview_invitation",
        
        "rejection": "rejection",
        "từ chối": "rejection",
        "từ chối ứng viên": "rejection",
        "rejection letter": "rejection",
        
        "offer": "offer",
        "đề nghị": "offer",
        "offer letter": "offer",
        "đề nghị việc làm": "offer",
        
        "acceptance": "acceptance",
        "xác nhận": "acceptance",
        "offer acceptance": "acceptance",
        
        "welcome": "welcome",
        "chào mừng": "welcome",
        "welcome letter": "welcome",
    }
    
    normalized_type = template_type_mapping.get(template_type.strip().lower(), template_type)
    template_fields = get_template_specific_fields(normalized_type)
    processed = {}
    
    # Xử lý từng trường được định nghĩa cho template này
    for field_name, field_config in template_fields.items():
        raw_value = extra_context.get(field_name)
        # Chuyển đổi sang string và strip nếu có giá trị
        if raw_value is not None:
            value = str(raw_value).strip()
        else:
            value = ""
        
        # Nếu không có giá trị, sử dụng default
        if not value:
            value = field_config.get("default", "")
        
        processed[field_name] = value
    
    # Cho phép thêm các trường tùy chỉnh khác (không nằm trong danh sách định nghĩa)
    # nhưng vẫn ưu tiên các trường đã được xử lý ở trên
    for key, value in extra_context.items():
        if key not in processed:
            processed[key] = str(value).strip() if value is not None else ""
    
    return processed


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


def format_email_body(body: str, template_type: str) -> str:
    """
    Format email body để hiển thị đẹp và chuyên nghiệp với xuống dòng đúng cách.
    Xử lý cho tất cả các loại email.
    """
    if not body:
        return ""
    
    # Chuyển đổi các line breaks thành format HTML phù hợp
    # Double line breaks = paragraph break
    # Single line breaks = <br>
    
    # Tách body thành các đoạn dựa trên double line breaks
    paragraphs = body.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Kiểm tra xem có phải HTML không
        is_html = bool(re.search(r'<[^>]+>', para))
        
        if not is_html:
            # Plain text: format đẹp
            # Xử lý các dòng trong paragraph
            lines = para.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                formatted_lines.append(line)
            
            # Join các dòng với <br> và wrap trong <p>
            if formatted_lines:
                # CHANGED: màu chữ mặc định cho email gửi đi -> đen
                formatted_para = '<p style="margin: 0 0 18px; color: #000; line-height: 1.75;">' + '<br>'.join(formatted_lines) + '</p>'
                formatted_paragraphs.append(formatted_para)
        else:
            # HTML: giữ nguyên nhưng đảm bảo formatting đúng
            # Nếu chưa có <p> tag, wrap trong <p>
            if not re.search(r'<p[^>]*>', para, re.IGNORECASE):
                formatted_para = '<p style="margin: 0 0 18px; color: #000; line-height: 1.75;">' + para + '</p>'
            else:
                formatted_para = para
            formatted_paragraphs.append(formatted_para)
    
    return '\n'.join(formatted_paragraphs)


def format_template(template: Optional[str], context: Dict[str, str]) -> str:
    if not template:
        return ""
    
    # Loại bỏ các placeholder {format} và {interviewer} trước khi render
    template = re.sub(r'\{format\}', '', template, flags=re.IGNORECASE)
    template = re.sub(r'\{interviewer\}', '', template, flags=re.IGNORECASE)
    
    # Xóa các dòng chứa "Format:" hoặc "Interviewer:" (cả HTML và plain text)
    # Pattern: có thể có dấu "- " hoặc "• " hoặc không, sau đó là "Format:" hoặc "Interviewer:"
    # Xử lý cả HTML tags (<li>, <p>, <div>, etc.) và plain text
    lines = template.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Xóa dòng nếu chứa Format: hoặc Interviewer:
        # Pattern bao gồm:
        # - Plain text: "- Format:", "Format:", "• Format:", " - Format:"
        # - HTML: "<li>Format:</li>", "<p>Format:</p>", "<strong>Format:</strong>", etc.
        # - Có thể có text trước và sau
        line_to_check = line.strip()
        
        # Kiểm tra nếu dòng chứa Format: hoặc Interviewer:
        # Bỏ qua các dòng có pattern như "- Format:" hoặc "Format:" hoặc trong HTML tags
        if re.search(r'[-•\s]*\s*(Format|Interviewer)\s*:\s*', line, re.IGNORECASE):
            # Kiểm tra xem có phải là dòng chỉ chứa Format/Interviewer không
            # (loại bỏ các tag HTML và whitespace)
            content_only = re.sub(r'<[^>]+>', '', line).strip()
            if re.match(r'^[-•\s]*\s*(Format|Interviewer)\s*:?\s*$', content_only, re.IGNORECASE):
                continue
            # Nếu có text khác ngoài Format/Interviewer, thử loại bỏ phần Format/Interviewer
            # Ví dụ: "Interview Details: - Time: - Format: - Interviewer:" -> "Interview Details: - Time:"
            line = re.sub(r'[-•\s]*\s*(Format|Interviewer)\s*:\s*', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\s+-\s*$', '', line)  # Xóa dấu "- " ở cuối nếu còn
            # Nếu dòng trở nên trống sau khi xóa, bỏ qua
            if not line.strip() or line.strip() in ['-', '•', ':', '- :', '• :']:
                continue
        
        cleaned_lines.append(line)
    
    template = '\n'.join(cleaned_lines)
    
    # Render template với context
    result = template.format_map(SafeDict(context)).strip()
    
    # Clean up sau khi render: xóa các pattern còn sót lại
    # Xóa các dòng chứa "- Format:" hoặc "- Interviewer:" sau khi render
    result_lines = result.split('\n')
    final_lines = []
    for line in result_lines:
        # Kiểm tra lại sau khi render (có thể có giá trị được thay thế)
        if re.search(r'[-•\s]*\s*(Format|Interviewer)\s*:\s*', line, re.IGNORECASE):
            content_only = re.sub(r'<[^>]+>', '', line).strip()
            # Nếu dòng chỉ chứa Format/Interviewer với giá trị rỗng hoặc không có giá trị
            if re.match(r'^[-•\s]*\s*(Format|Interviewer)\s*:\s*$', content_only, re.IGNORECASE):
                continue
            # Loại bỏ phần Format/Interviewer khỏi dòng
            line = re.sub(r'[-•\s]*\s*(Format|Interviewer)\s*:\s*[^\s]*\s*', '', line, flags=re.IGNORECASE)
            line = re.sub(r'\s*-\s*$', '', line)  # Xóa dấu "- " ở cuối
        
        # Loại bỏ các dòng trống hoặc chỉ chứa dấu phân cách
        if line.strip() and line.strip() not in ['-', '•', ':', '- :', '• :']:
            final_lines.append(line)
        elif final_lines and final_lines[-1].strip():  # Giữ một dòng trống giữa các đoạn
            final_lines.append('')
    
    result = '\n'.join(final_lines)
    
    # Clean up các dòng trống thừa (hơn 2 dòng trống liên tiếp)
    result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
    
    # Clean up các pattern "- " hoặc "• " ở đầu dòng nếu không có nội dung sau
    result = re.sub(r'^[-•]\s*$', '', result, flags=re.MULTILINE)
    
    return result.strip()


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
    <p style="text-align: center; color: #000; font-size: 12px; margin-top: 10px;">
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


def _format_body_by_template_type(body: str, template_type: str, context: Dict[str, str]) -> str:
    """
    Format email body dựa trên template type để hiển thị đẹp và chuyên nghiệp.
    Xử lý xuống dòng, spacing, và formatting cho từng loại email.
    """
    if not body:
        return body
    
    # Kiểm tra xem body đã có HTML không
    is_html_body = bool(re.search(r'<[^>]+>', body))
    
    # Nếu đã là HTML và có structure tốt, chỉ cần format nhẹ
    if is_html_body and re.search(r'<p[^>]*>|<div[^>]*>', body, re.IGNORECASE):
        # Body đã có HTML structure, chỉ format các phần đặc biệt
        # Format Interview Details, Offer Details, etc.
        if template_type == "interview_invitation":
            body = _enhance_interview_details_html(body, context)
        elif template_type == "offer":
            body = _enhance_offer_details_html(body, context)
        elif template_type == "welcome":
            body = _enhance_welcome_details_html(body, context)
        
        return body
    
    # Nếu là plain text hoặc HTML đơn giản, format lại toàn bộ
    # Tách thành các đoạn dựa trên double line breaks
    paragraphs = body.split('\n\n')
    formatted_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Kiểm tra xem có phải HTML không
        is_html = bool(re.search(r'<[^>]+>', para))
        
        if template_type == "interview_invitation":
            formatted_para = _format_interview_invitation_para(para, is_html, context)
        elif template_type == "rejection":
            formatted_para = _format_rejection_para(para, is_html, context)
        elif template_type == "offer":
            formatted_para = _format_offer_para(para, is_html, context)
        elif template_type == "acceptance":
            formatted_para = _format_acceptance_para(para, is_html, context)
        elif template_type == "welcome":
            formatted_para = _format_welcome_para(para, is_html, context)
        else:
            formatted_para = _format_default_para(para, is_html)
        
        if formatted_para:
            formatted_paragraphs.append(formatted_para)
    
    # Join các đoạn
    result = '\n\n'.join(formatted_paragraphs)
    
    # Clean up
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()


def _enhance_interview_details_html(body: str, context: Dict[str, str]) -> str:
    """Enhance HTML body cho interview invitation."""
    # Không cần enhance Interview Details - giữ nguyên format
    return body


def _enhance_offer_details_html(body: str, context: Dict[str, str]) -> str:
    """Enhance HTML body cho offer email."""
    if re.search(r'(Offer Details|Chi tiết đề nghị)', body, re.IGNORECASE):
        if not re.search(r'<div[^>]*Offer Details', body, re.IGNORECASE):
            body = re.sub(
                r'((Offer Details|Chi tiết đề nghị).*?)(?=<p|<div|</body|$)',
                r'<div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 16px 20px; margin: 20px 0; border-radius: 6px;">\1</div>',
                body,
                flags=re.IGNORECASE | re.DOTALL
            )
    return body


def _enhance_welcome_details_html(body: str, context: Dict[str, str]) -> str:
    """Enhance HTML body cho welcome email."""
    if re.search(r'(Start Date|Ngày bắt đầu|Work Location)', body, re.IGNORECASE):
        if not re.search(r'<div[^>]*(Start Date|Work Location)', body, re.IGNORECASE):
            body = re.sub(
                r'((Start Date|Ngày bắt đầu|Work Location|Địa điểm làm việc).*?)(?=<p|<div|</body|$)',
                r'<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px 20px; margin: 20px 0; border-radius: 6px;">\1</div>',
                body,
                flags=re.IGNORECASE | re.DOTALL
            )
    return body


def _format_interview_invitation_para(para: str, is_html: bool, context: Dict[str, str]) -> str:
    """Format paragraph cho interview invitation email."""
    # Kiểm tra xem có phải Interview Details không
    if re.search(r'(Interview Details|Chi tiết phỏng vấn)', para, re.IGNORECASE):
        if not is_html:
            # Nếu là plain text, format Interview Details một cách rõ ràng
            # Extract các thông tin từ context
            interview_date = context.get("interview_date", "").strip()
            interview_time = context.get("interview_time", "").strip()
            interview_location = context.get("interview_location", "").strip()
            
            # Format Interview Details thành HTML box đẹp
            # CHANGED: dùng màu chữ đen (#000) cho email gửi đi
            details_html = '<div style="background: rgba(255, 255, 255, 0.05); border-left: 3px solid #60a5fa; padding: 16px 20px; margin: 20px 0; border-radius: 4px; color: #000;">'
            details_html += '<strong style="color: #000; font-size: 15px;">Interview Details:</strong><br>'
            
            if interview_date:
                details_html += f'<span style="display: block; margin-top: 8px;">📅 <strong>Date:</strong> {interview_date}</span>'
            if interview_time:
                details_html += f'<span style="display: block; margin-top: 4px;">⏰ <strong>Time:</strong> {interview_time}</span>'
            if interview_location:
                details_html += f'<span style="display: block; margin-top: 4px;">📍 <strong>Location:</strong> {interview_location}</span>'
            
            details_html += '</div>'
            
            return details_html
        else:
            # Nếu đã là HTML, chỉ cần đảm bảo có giá trị đủ
            # Kiểm tra xem có thiếu ngày không
            if "interview_date" in para or "{interview_date}" in para:
                # Template đã có placeholder, chỉ cần giữ lại
                return _format_default_para(para, is_html)
            else:
                # Nếu thiếu ngày, try thêm từ context
                interview_date = context.get("interview_date", "")
                if interview_date and "Date:" not in para and "Ngày:" not in para:
                    # Thêm ngày vào Interview Details
                    para = re.sub(
                        r'(Interview Details|Chi tiết phỏng vấn)([:\s]*)',
                        rf'\1\2 📅 {interview_date}<br>',
                        para,
                        flags=re.IGNORECASE,
                        count=1
                    )
                return _format_default_para(para, is_html)
    
    # Nếu không phải Interview Details, format bình thường
    return _format_default_para(para, is_html)


def _format_rejection_para(para: str, is_html: bool, context: Dict[str, str]) -> str:
    """Format paragraph cho rejection email."""
    return _format_default_para(para, is_html)


def _format_offer_para(para: str, is_html: bool, context: Dict[str, str]) -> str:
    """Format paragraph cho offer email."""
    # Format offer details nếu có
    if re.search(r'(Offer Details|Chi tiết đề nghị|Mức lương|Salary)', para, re.IGNORECASE):
        if not is_html:
            para = '<div style="background: #f0fdf4; border-left: 4px solid #10b981; padding: 16px 20px; margin: 20px 0; border-radius: 6px;">' + para + '</div>'
    return _format_default_para(para, is_html)


def _format_acceptance_para(para: str, is_html: bool, context: Dict[str, str]) -> str:
    """Format paragraph cho acceptance email."""
    return _format_default_para(para, is_html)


def _format_welcome_para(para: str, is_html: bool, context: Dict[str, str]) -> str:
    """Format paragraph cho welcome email."""
    # Format welcome information nếu có
    if re.search(r'(Start Date|Ngày bắt đầu|Work Location|Địa điểm làm việc)', para, re.IGNORECASE):
        if not is_html:
            para = '<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px 20px; margin: 20px 0; border-radius: 6px;">' + para + '</div>'
    return _format_default_para(para, is_html)


def _format_default_para(para: str, is_html: bool) -> str:
    """Format paragraph mặc định cho tất cả các loại email."""
    if is_html:
        # Nếu đã là HTML, đảm bảo styling đúng và line breaks hợp lý
        # Kiểm tra xem có <p> tag chưa
        if not re.search(r'<p[^>]*>', para, re.IGNORECASE):
            # Wrap trong <p> nếu chưa có, nhưng giữ nguyên line breaks
            para = '<p style="margin: 0 0 18px; color: #000; line-height: 1.75;">' + para + '</p>'
        else:
            # Đảm bảo <p> tags có styling đúng
            para = re.sub(
                r'<p([^>]*)(?<!\bstyle=)([^>]*)>',
                r'<p\1\2 style="margin: 0 0 18px; color: #000; line-height: 1.75;">',
                para,
                flags=re.IGNORECASE
            )
        return para
    else:
        # Plain text: format đẹp với xuống dòng đúng cách
        lines = para.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Giữ nguyên các dòng, chỉ loại bỏ whitespace thừa
            formatted_lines.append(line)
        
        if formatted_lines:
            # Join các dòng với <br> để giữ xuống dòng
            formatted_para = '<p style="margin: 0 0 18px; color: #000; line-height: 1.75;">' + '<br>'.join(formatted_lines) + '</p>'
            return formatted_para
    
    return para


def _remove_format_interviewer_lines(text: str) -> str:
    """
    Loại bỏ các dòng hoặc phần chứa "Format:" và "Interviewer:" khỏi text.
    Xử lý cả HTML và plain text.
    """
    if not text:
        return text
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Kiểm tra xem dòng có chứa Format: hoặc Interviewer: không
        # Pattern: có thể có "- ", "• ", hoặc HTML tags, sau đó là Format/Interviewer:
        if re.search(r'[-•\s<>/]*\s*(Format|Interviewer)\s*:\s*', line, re.IGNORECASE):
            # Lấy nội dung text thuần (bỏ HTML tags)
            text_content = re.sub(r'<[^>]+>', '', line).strip()
            
            # Nếu dòng chỉ chứa Format/Interviewer (với hoặc không có giá trị)
            if re.match(r'^[-•\s]*\s*(Format|Interviewer)\s*:?\s*', text_content, re.IGNORECASE):
                # Kiểm tra xem có giá trị sau dấu hai chấm không
                match = re.search(r'(Format|Interviewer)\s*:\s*(.+)$', text_content, re.IGNORECASE)
                if not match or not match.group(2).strip():
                    # Không có giá trị, bỏ qua dòng này
                    continue
                else:
                    # Có giá trị nhưng có thể rỗng, vẫn bỏ qua
                    continue
            
            # Nếu dòng chứa Format/Interviewer nhưng có text khác, thử loại bỏ phần Format/Interviewer
            # Ví dụ: "Interview Details: - Time: - Format: - Interviewer:" 
            # -> Loại bỏ " - Format:" và " - Interviewer:"
            line = re.sub(r'\s*[-•]\s*(Format|Interviewer)\s*:\s*[^\s<]*\s*', '', line, flags=re.IGNORECASE)
            # Xóa các dấu phân cách thừa ở cuối
            line = re.sub(r'\s*[-•]\s*$', '', line)
            line = re.sub(r'\s*:\s*$', '', line)
            
            # Nếu dòng trở nên trống hoặc chỉ còn dấu phân cách, bỏ qua
            if not line.strip() or line.strip() in ['-', '•', ':', '- :', '• :', 'Interview Details:', 'Interview Details']:
                continue
        
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines)
    
    # Clean up các dòng trống thừa
    result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)
    
    # Xóa các pattern còn sót lại trong HTML
    # Ví dụ: <li>Format:</li> hoặc <p>Format:</p>
    result = re.sub(r'<([^>]+)>\s*[-•\s]*(Format|Interviewer)\s*:\s*</\1>', '', result, flags=re.IGNORECASE)
    result = re.sub(r'<([^>]+)>\s*[-•\s]*(Format|Interviewer)\s*:\s*[^<]*</\1>', '', result, flags=re.IGNORECASE)
    
    return result.strip()


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


def build_context(
    candidate: Dict,
    extra_context: Dict[str, str],
    token_map: Dict[int, str],
    include_verification: bool,
    template_type: str,
) -> Dict[str, str]:
    """
    Xây dựng context cho việc render email template.
    
    Args:
        candidate: Thông tin ứng viên từ database
        extra_context: Thông tin bổ sung từ người dùng (chưa được xử lý)
        token_map: Map candidate_id -> token (cho email mời phỏng vấn)
        include_verification: Có cần token verification không
        template_type: Loại template email (để xử lý extra_context phù hợp)
    """
    # Chuẩn hóa template_type trước khi xử lý
    template_type_mapping = {
        "interview_invitation": "interview_invitation",
        "mời phỏng vấn": "interview_invitation",
        "mời phỏng vấn vòng 1": "interview_invitation",
        "interview invitation": "interview_invitation",
        "interview invitation round 1": "interview_invitation",
    }
    
    normalized_type = template_type_mapping.get(template_type.strip().lower(), template_type)
    
    # Xử lý extra_context theo template_type
    processed_context = process_extra_context_for_template(extra_context, normalized_type)
    
    token = token_map.get(candidate["id"]) if include_verification else None
    inferred_job_title = (
        candidate.get("job_title")
        or candidate.get("position")
        or processed_context.get("job_title")
        or processed_context.get("position")
        or ""
    )
    verify_link = f"{VERIFICATION_BASE_URL}{token}" if include_verification and token else ""
    token_value = token if include_verification else ""
    
    # Context cơ bản luôn có
    context = {
        "candidate_name": candidate.get("full_name", ""),
        "candidate_email": candidate.get("email", ""),
        "job_title": inferred_job_title,
        "position": inferred_job_title,
        # Token/link chỉ dùng cho email mời phỏng vấn
        "token": token_value or "",
        "verify_link": verify_link if include_verification else "",
    }
    
    # Thêm các trường đã được xử lý từ processed_context
    # Ưu tiên processed_context để đảm bảo các trường template-specific được xử lý đúng
    for key, value in processed_context.items():
        context[key] = value
    
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
    template_type = template.get("template_type", "")
    
    # Chuẩn hóa template_type
    template_type_mapping = {
        "interview_invitation": "interview_invitation",
        "mời phỏng vấn": "interview_invitation",
        "mời phỏng vấn vòng 1": "interview_invitation",
        "interview invitation": "interview_invitation",
        "interview invitation round 1": "interview_invitation",
    }
    
    normalized_type = template_type_mapping.get(template_type.strip().lower(), template_type)
    include_verification = normalized_type == "interview_invitation"
    
    candidates = fetch_candidates(payload.candidate_ids)

    if not candidates:
        raise HTTPException(status_code=404, detail="Không tìm thấy ứng viên phù hợp.")

    token_map: Dict[int, str] = {}
    if include_verification:
        token_map = read_token_map()
        print(f"[DEBUG] Đã đọc {len(token_map)} token từ file candidate_with_token.csv")
        if token_map:
            print(f"[DEBUG] Các candidate_id có token: {list(token_map.keys())}")
    
    emails = []
    missing_candidates = []
    missing_tokens = []

    for candidate in candidates:
        # Lấy token từ CSV cho ứng viên này (chỉ với template mời phỏng vấn)
        candidate_token = token_map.get(candidate["id"]) if include_verification else None
        if include_verification and not candidate_token:
            missing_tokens.append(candidate["id"])
            print(f"[WARNING] Không tìm thấy token cho candidate_id={candidate['id']} trong CSV")
        
        context = build_context(
            candidate, 
            payload.extra_context, 
            token_map, 
            include_verification,
            normalized_type
        )
        subject = format_template(template.get("subject_template"), context)
        body = format_template(template.get("body_template"), context)
        
        # Xóa các dòng chứa "Format:" và "Interviewer:" một lần nữa sau khi render
        body = _remove_format_interviewer_lines(body)
        
        # Format email body cho tất cả các loại template
        body = _format_body_by_template_type(body, normalized_type, context)
        
        # Thêm custom_message vào email nếu có (cho interview_invitation)
        if normalized_type == "interview_invitation" and context.get("custom_message"):
            custom_msg = context.get("custom_message", "").strip()
            if custom_msg:
                if "{custom_message}" not in body and custom_msg not in body:
                    if "</body>" in body.lower():
                        body = body.replace("</body>", f"\n\n<p><strong>Ghi chú thêm:</strong> {custom_msg}</p>\n</body>")
                    elif "{verify_link}" in body:
                        body = body.replace("{verify_link}", f"\n\n<p><strong>Ghi chú thêm:</strong> {custom_msg}</p>\n{{verify_link}}")
                    elif "/verify?token=" in body:
                        verify_pattern = r'(Xác nhận ứng tuyển[:\s]|<a[^>]*verify|href="[^"]*verify[^"]*")'
                        if re.search(verify_pattern, body, re.IGNORECASE):
                            body = re.sub(
                                verify_pattern,
                                f'<p><strong>Ghi chú thêm:</strong> {custom_msg}</p>\n\\1',
                                body,
                                count=1,
                                flags=re.IGNORECASE
                            )
                        else:
                            body = body + f"\n\n<p><strong>Ghi chú thêm:</strong> {custom_msg}</p>"
                    else:
                        body = body + f"\n\n<p><strong>Ghi chú thêm:</strong> {custom_msg}</p>"
        
        # Tự động thêm button xác nhận vào email nếu có verify_link
        verify_link = context.get("verify_link", "")
        if include_verification and verify_link:
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
        "missing_token_ids": missing_tokens if include_verification else [],
    }
    
    if include_verification and missing_tokens:
        print(f"[WARNING] Có {len(missing_tokens)} ứng viên không có token trong CSV: {missing_tokens}")
    
    return response
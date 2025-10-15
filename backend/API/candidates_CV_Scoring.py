import re
from typing import Dict
import os


def clean_text(text: str) -> str:
    """Làm sạch chuỗi: bỏ khoảng trắng thừa, ký tự lạ."""
    if not text:
        return ""
    text = str(text)
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def extract_field(block: str, field_name: str) -> str:
    """
    Tìm đoạn text bắt đầu bằng 'field_name:' và lấy nội dung theo dòng hoặc đến khi gặp field khác.
    """
    pattern = rf"{field_name}\s*:\s*(.*?)(?=\n\w+?:|\Z)"
    match = re.search(pattern, block, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return clean_text(match.group(1))
    return ""


def parse_candidate_block(block: str) -> Dict[str, str]:
    """
    Từ một khối thông tin của 1 ứng viên → Trích ra 6 trường chính.
    """
    education_text = extract_field(block, "education")
    experience_text = extract_field(block, "experience")
    skills_text = extract_field(block, "skills")

    # Soft skills có thể nằm ở personal_skills hoặc tương tự
    soft_skills_text = extract_field(block, "personal_skills")
    if not soft_skills_text:
        soft_skills_text = extract_field(block, "soft_skills")

    # certificates gồm reference / certifications / awards
    certificates_text = " ".join([
        extract_field(block, "certificates"),
        extract_field(block, "awards"),
    ])
    
    #tools
    tools_text = " ".join([
        extract_field(block, "tools"),
        extract_field(block, "awards"),
    ])

    # Summary gồm objective + cv_summary + summary
    summary_text = " ".join([
        extract_field(block, "objective"),
        extract_field(block, "cv_summary"),
        extract_field(block, "summary"),
        extract_field(block, "activities")
    ])

    return {
        "education": education_text,
        "experience": experience_text,
        "skills": skills_text,
        "soft_skills": soft_skills_text,
        "certificates" : certificates_text,
        "tools": tools_text,
        "summary": summary_text,
    }


def get_last_candidate(file_path: str) -> Dict[str, str]:
    """
    Đọc toàn bộ file → tách ứng viên theo '----' → lấy ứng viên cuối.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Tách theo đường kẻ ----------------------------------------
    blocks = re.split(r"-{5,}", content)
    blocks = [b.strip() for b in blocks if b.strip()]

    if not blocks:
        raise ValueError("Không tìm thấy ứng viên nào trong file")

    last_block = blocks[-1]
    return parse_candidate_block(last_block)


if __name__ == "__main__":
    filename = 'demo_data.csv'
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f'../results/{filename}'))
    candidate = get_last_candidate(file_path)

    print("\n=== DỮ LIỆU ỨNG VIÊN CUỐI ===")
    for key, value in candidate.items():
        print(f"\n{key.upper()}:\n{value}")
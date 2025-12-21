import pymysql
from fastapi import APIRouter
from backend.dataAndModels.candidates_table import insert_candidates as insert

conn = pymysql.connect(
    host="127.0.0.1",
    user="root",
    password="tPhan186@",
    database="HireSmart",
    ssl_disabled=True,
)

print("Kết nối thành công!")

router = APIRouter()


@router.get("/insert")
async def insert_test():
    try:
        test_candidate = {
            "full_name": "Nguyễn Văn A",
            "email": "nguyenvana@example.com",
            "phone": "+84901234567",
            "address": "Hanoi, Vietnam",

            # Các trường dùng cho scoring
            "hard_skills": "Python, Flask, SQLAlchemy, Docker, AWS",
            "experience": "3 years as Backend Developer at ExampleCorp. Built REST APIs with Flask and SQLAlchemy. Deployed services using Docker and AWS.",
            "cv_summary": "Experienced backend engineer focused on API development and cloud deployment.",
            "education": "B.Sc. Computer Science, ABC University",
            "tools": "Git, Docker, Postman, Terraform",
            "certificates": "AWS Certified Developer - Associate",
            "soft_skills": "Teamwork, Communication, Problem solving",

            # File / metadata
            "filename": "nguyenvana_cv.pdf",
            "mimetype": "application/pdf",
            "file_size": 23456,
            # filedata có thể là base64 string (hệ thống sẽ thử decode), đây là ví dụ text base64
            "filedata": "VGhpcyBpcyBhIHRlc3QgZmlsZS4=",  # b"This is a test file."
            
            # job_id: có thể là int hoặc numeric string; nếu DB không cho NULL, gửi giá trị hợp lệ
            "job_id": 1
        }
        insert(conn, test_candidate)
    except Exception as e:
        return {"status": "error", "message": str(e)}
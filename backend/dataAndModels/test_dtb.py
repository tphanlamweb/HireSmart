import pymysql
from fastapi import APIRouter
from backend.dataAndModels.candidates_table import insert_candidates as insert
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, MetaData, Table, select
from backend.dataAndModels.config import DATABASE_URL

print("Kết nối thành công!")
engine = create_engine(DATABASE_URL)


router = APIRouter()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency cung cấp session cho các route FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get("/insert")
def insert_test(db: Session = Depends(get_db)):
    try:
        test_candidate = {
            "full_name": "Nguyễn Văn BBB",
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
        insert(test_candidate, db)
        return {"status": "success", "message": f"{test_candidate['full_name']}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
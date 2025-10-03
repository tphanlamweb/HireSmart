from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np



def build_cv_text(cv_data):
    parts = [
        f"Name: {cv_data.get('name', '')}",
        f"Experience: {cv_data.get('experience', '')}",
        f"Skills: {', '.join(cv_data.get('skills', []))}",
        f"Education: {cv_data.get('education', '')}",
        f"Certificates: {', '.join(cv_data.get('certificates', []))}"
    ]
    return ". ".join(parts)










def CV_Scoring(job_description, cvs):

    # Dữ liệu đầu vào
    print("Job Description:\n", job_description)
    print("CVs:\n")
    print("CV :", cvs)

    # Load mô hình NLP
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded: all-MiniLM-L6-v2\n")

    # Biểu diễn dữ liệu thành vector
    job_vector = model.encode([job_description])
    
    if isinstance(cvs, str):
        cv_texts = [cvs]
    else:
        cv_texts = cvs
    cv_vectors = model.encode(cv_texts)

    print("Job description vector shape:", job_vector.shape)
    print("CVs vector shape:", cv_vectors.shape)
    print("\n")


    # Tính similarity và chấm điểm
    scores = cosine_similarity(job_vector, cv_vectors)[0][0]
    return round(scores*100000)

    













# Data 
data_extracted = {
    "name": "Nguyen Van A",
    "experience": "3 years as Python developer at ABC Corp.",
    "skills": ["Python", "Django", "REST API"],
    "education": "Bachelor of Computer Science",
    "certificates": ["AWS Certified Developer"]
}

job_description = """
We are looking for a software engineer with strong Python skills,
experience in REST API development, and knowledge of cloud technologies.
"""





cvs = build_cv_text(data_extracted)
print("CV Text:\n", cvs)

print(f"\nĐiểm của CV {data_extracted.get('name', '')} : {CV_Scoring(job_description, cvs):,}")


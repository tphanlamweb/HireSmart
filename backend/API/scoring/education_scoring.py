from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

# ✅ Dùng mô hình LaBSE để hỗ trợ đa ngôn ngữ tốt hơn
# Bạn có thể thay bằng "distiluse-base-multilingual-cased-v2" nếu muốn nhẹ hơn
model_name = 'sentence-transformers/LaBSE'
model = SentenceTransformer(model_name)

# Rule-based degrees
degrees = {
    "phd": 100, "tiến sĩ": 100,
    "master": 80, "thạc sĩ": 80,
    "bachelor": 60, "đại học": 60,
    "college": 40, "cao đẳng": 40
}

# Danh sách mẫu ngành học phổ biến (tiếng Việt + Anh)
field_list = [
    "kế toán","accounting",
    "tài chính","finance",
    "quản trị","management",
    "marketing",
    "công nghệ thông tin","information technology","it",
    "data science",
    "machine learning",
    "ngôn ngữ","language",
    "thiết kế","design",
    "kinh tế","economics",
    "logistics",
    "nhân sự","human resources",
    "bán hàng","sales"
]

def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text

# ===== AI-generated relevant keywords from JD =====
def generate_relevant_keywords(jd_text: str, threshold: float = 0.6) -> list:
    """
    Tự động chọn các ngành học liên quan từ JD dựa trên embedding cosine similarity.
    threshold: mức similarity để coi là ngành liên quan
    """
    jd_text = clean_text(jd_text)
    jd_emb = model.encode([jd_text])[0]

    keywords = []
    for field in field_list:
        field_emb = model.encode([field])[0]
        sim = cosine_similarity([jd_emb], [field_emb])[0][0]
        if sim >= threshold:
            keywords.append(field)
            print(f"[DEBUG] Matched field: {field} (similarity={sim:.2f})")
    return keywords

# ===== Rule-based nâng cao =====
def score_education_rule(cv_text: str, relevant_keywords: list) -> float:
    cv_text = clean_text(cv_text)
    score = 0
    for degree, base_score in degrees.items():
        if degree in cv_text:
            score = base_score
            break
    if any(keyword in cv_text for keyword in relevant_keywords):
        score += 10
    return min(score, 100)

# ===== Semantic similarity =====
def score_education_semantic(cv_text: str, target_description: str) -> float:
    cv_text = clean_text(cv_text)
    target_description = clean_text(target_description)
    embeddings = model.encode([cv_text, target_description])
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim * 100)

# ===== Kết hợp =====
def score_education(cv_text: str, jd_text: str, target_description: str) -> float:
    relevant_keywords = generate_relevant_keywords(jd_text)
    print("Relevant keywords for education scoring:", relevant_keywords)

    rule_score = score_education_rule(cv_text, relevant_keywords)
    print("Rule-based education score:", rule_score)

    semantic_score = score_education_semantic(cv_text, target_description)
    print("Semantic education score:", semantic_score)

    final_score = 0.7 * rule_score + 0.3 * semantic_score
    print("Final combined education score:", final_score)

    return round(final_score, 2)


# ==== Test ví dụ ====
if __name__ == "__main__":
    cv_text_vi = "Nguyễn Văn A, Thạc sĩ Quản trị Kinh doanh, Đại học Duy Tân, chuyên ngành Marketing"
    cv_text_en = "John Doe, Master of Business Administration, Duy Tan University, major in Marketing"
    jd_text = "We are hiring a Marketing Manager with experience in business management, finance, and digital marketing."
    target_description = "Ứng viên có trình độ đại học hoặc cao hơn trong lĩnh vực quản trị kinh doanh, tài chính, marketing hoặc công nghệ thông tin"

    print("\n📄 CV Tiếng Việt:", score_education(cv_text_vi, jd_text, target_description))
    print("\n📄 CV Tiếng Anh:", score_education(cv_text_en, jd_text, target_description))
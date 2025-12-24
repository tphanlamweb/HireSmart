from sklearn.metrics.pairwise import cosine_similarity
import re
import numpy as np
from functools import lru_cache
from typing import List, Tuple
from backend.src.ai import manager as ai_manager


"""Tối ưu bằng cách cache model và embeddings (model được quản lý trong ai.manager)"""

# ✅ Compile regex một lần
clean_pattern = re.compile(r"[^\w\s]")

# Rule-based degrees
degrees = {
    "phd": 100,
    "tiến sĩ": 100,
    "master": 80,
    "thạc sĩ": 80,
    "bachelor": 60,
    "đại học": 60,
    "college": 40,
    "cao đẳng": 40,
    "phổ thông": 20,
    "trung cấp": 20,
}

# Field list
field_list = [
    "kế toán",
    "accounting",
    "tài chính",
    "finance",
    "quản trị",
    "management",
    "marketing",
    "công nghệ thông tin",
    "information technology",
    "it",
    "data science",
    "machine learning",
    "ngôn ngữ",
    "language",
    "thiết kế",
    "design",
    "kinh tế",
    "economics",
    "logistics",
    "nhân sự",
    "human resources",
    "bán hàng",
    "sales",
]

# Pre-compute và cache embeddings của tất cả fields via ai_manager
field_embeddings = ai_manager.get_embeddings(field_list, batch_size=32)

@lru_cache(maxsize=1000)
def clean_text(text: str) -> str:
    """Cache kết quả clean text"""
    text = text.lower()
    text = clean_pattern.sub(" ", text)
    return " ".join(text.split())  # Remove extra whitespace

def generate_relevant_keywords(
    jd_text: str, threshold: float = 0.6
) -> List[str]:
    """
    Tối ưu: encode JD một lần, so sánh với tất cả fields cùng lúc
    """
    jd_text = clean_text(jd_text)

    # ✅ Encode JD một lần via ai_manager
    jd_emb = ai_manager.get_embeddings([jd_text], batch_size=32)[0]

    # ✅ Tính similarity với tất cả fields cùng lúc (vectorized)
    similarities = cosine_similarity([jd_emb], field_embeddings)[0]

    # ✅ Filter và return
    keywords = []
    for field, sim in zip(field_list, similarities):
        if sim >= threshold:
            keywords.append(field)
            print(f"[DEBUG] Matched field: {field} (similarity={sim:.2f})")

    return keywords

def score_education_rule(cv_text: str, relevant_keywords: List[str]) -> float:
    """Rule-based scoring"""
    cv_text = clean_text(cv_text)
    score = 0

    # Tìm degree cao nhất
    for degree, base_score in degrees.items():
        if degree in cv_text:
            score = base_score
            break

    # Bonus nếu có keyword liên quan
    if any(keyword in cv_text for keyword in relevant_keywords):
        score += 10

    return min(score, 100)

def score_education_semantic(cv_text: str, target_description: str) -> float:
    """Semantic similarity scoring"""
    cv_text = clean_text(cv_text)
    target_description = clean_text(target_description)

    # ✅ Batch encode cả 2 texts cùng lúc via ai_manager
    embeddings = ai_manager.get_embeddings([cv_text, target_description], batch_size=32)

    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim * 100)

def score_education(
    cv_text: str,
    jd_text: str,
    rule_weight: float = 0.7,
    semantic_weight: float = 0.3,
) -> Tuple[float, dict]:
    """
    Kết hợp rule-based và semantic scoring
    Returns: (final_score, details_dict)
    """
    # --- Normalize inputs: đảm bảo là string (fix lỗi TypeError khi truyền dict)
    def _to_text(x):
        if x is None:
            return ""
        if isinstance(x, dict):
            # join các trường thường gặp; an toàn hơn so với str(dict)
            parts = []
            for k in ['degree','institution','major','description','education','school','field']:
                if k in x and x[k]:
                    parts.append(str(x[k]))
            # fallback: nếu không có keys phổ thông, join all values
            if not parts:
                parts = [str(v) for v in x.values() if v]
            return " ".join(parts)
        if isinstance(x, (list, tuple, set)):
            return " ".join(str(i) for i in x)
        return str(x)

    cv_text = _to_text(cv_text)
    jd_text = _to_text(jd_text)


    # Step 1: Extract relevant keywords
    relevant_keywords = generate_relevant_keywords(jd_text)

    # Step 2: Rule-based score
    rule_score = score_education_rule(cv_text, relevant_keywords)

    # Step 3: Semantic score
    semantic_score = score_education_semantic(cv_text, jd_text)

    # Step 4: Combine
    final_score = rule_weight * rule_score + semantic_weight * semantic_score

    details = {
        "total_score": round(final_score, 2),
        "rule_score": rule_score,
        "semantic_score": semantic_score,
        "relevant_keywords": relevant_keywords,
    }

    return details

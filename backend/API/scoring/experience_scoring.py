"""
Module chấm điểm phần Experience của CV
"""

import re
from datetime import datetime
from difflib import SequenceMatcher


def _extract_years_from_experience(experience_text):
    """
    Trích xuất tổng số năm kinh nghiệm từ text với nhiều format khác nhau
    
    Args:
        experience_text: String chứa thông tin kinh nghiệm
    
    Returns:
        float: Tổng số năm kinh nghiệm
    """
    if not experience_text or experience_text.lower() == 'n/a':
        return 0
    
    # Mapping tên tháng sang số
    month_mapping = {
        # English
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12,
        # Vietnamese
        'tháng 1': 1, 'tháng 01': 1, 'tháng một': 1,
        'tháng 2': 2, 'tháng 02': 2, 'tháng hai': 2,
        'tháng 3': 3, 'tháng 03': 3, 'tháng ba': 3,
        'tháng 4': 4, 'tháng 04': 4, 'tháng tư': 4,
        'tháng 5': 5, 'tháng 05': 5, 'tháng năm': 5,
        'tháng 6': 6, 'tháng 06': 6, 'tháng sáu': 6,
        'tháng 7': 7, 'tháng 07': 7, 'tháng bảy': 7,
        'tháng 8': 8, 'tháng 08': 8, 'tháng tám': 8,
        'tháng 9': 9, 'tháng 09': 9, 'tháng chín': 9,
        'tháng 10': 10, 'tháng mười': 10,
        'tháng 11': 11, 'tháng mười một': 11,
        'tháng 12': 12, 'tháng mười hai': 12
    }
    
    total_months = 0
    found_periods = []
    
    # Helper function để convert tên tháng thành số
    def get_month_number(month_str):
        month_lower = month_str.lower().strip()
        return month_mapping.get(month_lower, None)
    
    # Pattern 0: Month YYYY - Month YYYY (Jan 2024 - March 2025, January 2020 - Dec 2022)
    pattern0 = re.findall(r'([A-Za-z]+)\s+(\d{4})\s*[-–]\s*([A-Za-z]+)\s+(\d{4})', experience_text)
    for start_month_str, start_year, end_month_str, end_year in pattern0:
        start_month = get_month_number(start_month_str)
        end_month = get_month_number(end_month_str)
        if start_month and end_month:
            months = (int(end_year) - int(start_year)) * 12 + (end_month - start_month)
            if months > 0:
                found_periods.append((start_year, end_year, months))
                total_months += months
    
    # Pattern 1: MM/YYYY - MM/YYYY (03/2019 - 09/2020)
    pattern1 = re.findall(r'(\d{1,2})/(\d{4})\s*[-–]\s*(\d{1,2})/(\d{4})', experience_text)
    for start_month, start_year, end_month, end_year in pattern1:
        months = (int(end_year) - int(start_year)) * 12 + (int(end_month) - int(start_month))
        if months > 0:
            found_periods.append((start_year, end_year, months))
            total_months += months
    
    # Pattern 2: MM-YYYY - MM-YYYY (03-2019 - 09-2020)
    pattern2 = re.findall(r'(\d{1,2})-(\d{4})\s*[-–]\s*(\d{1,2})-(\d{4})', experience_text)
    for start_month, start_year, end_month, end_year in pattern2:
        months = (int(end_year) - int(start_year)) * 12 + (int(end_month) - int(start_month))
        if months > 0 and (start_year, end_year, months) not in found_periods:
            found_periods.append((start_year, end_year, months))
            total_months += months
    
    # Pattern 3: YYYY/MM - YYYY/MM (2019/03 - 2020/09)
    pattern3 = re.findall(r'(\d{4})/(\d{1,2})\s*[-–]\s*(\d{4})/(\d{1,2})', experience_text)
    for start_year, start_month, end_year, end_month in pattern3:
        months = (int(end_year) - int(start_year)) * 12 + (int(end_month) - int(start_month))
        if months > 0 and (start_year, end_year, months) not in found_periods:
            found_periods.append((start_year, end_year, months))
            total_months += months
    
    # Pattern 4: YYYY - YYYY (2018 - 2021)
    pattern4 = re.findall(r'(?<!\d)(\d{4})\s*[-–]\s*(\d{4})(?!\d)', experience_text)
    for start_year, end_year in pattern4:
        months = (int(end_year) - int(start_year)) * 12
        if months > 0 and (start_year, end_year, months) not in found_periods:
            found_periods.append((start_year, end_year, months))
            total_months += months
    
    # Pattern 5: Month YYYY - present/now/current (Jan 2019 - present)
    pattern5_text = re.findall(r'([A-Za-z]+)\s+(\d{4})\s*[-–]\s*(present|now|current|hiện tại|nay)', 
                               experience_text, re.IGNORECASE)
    for start_month_str, start_year, _ in pattern5_text:
        start_month = get_month_number(start_month_str)
        if start_month:
            months = (datetime.now().year - int(start_year)) * 12 + (datetime.now().month - start_month)
            if months > 0:
                total_months += months
    
    # Pattern 6: MM/YYYY - present/now/current/hiện tại (03/2019 - present)
    pattern6 = re.findall(r'(\d{1,2})/(\d{4})\s*[-–]\s*(present|now|current|hiện tại|nay)', 
                          experience_text, re.IGNORECASE)
    for start_month, start_year, _ in pattern6:
        months = (datetime.now().year - int(start_year)) * 12 + (datetime.now().month - int(start_month))
        if months > 0:
            total_months += months
    
    # Pattern 7: YYYY - present/now/current/hiện tại (2019 - present)
    pattern7 = re.findall(r'(?<!\d)(\d{4})\s*[-–]\s*(present|now|current|hiện tại|nay)', 
                          experience_text, re.IGNORECASE)
    for start_year, _ in pattern7:
        months = (datetime.now().year - int(start_year)) * 12
        if months > 0:
            # Check if not already counted in other patterns
            if not any(start_year == sy for sy, ey, m in found_periods):
                total_months += months
    
    # Pattern 8: Tháng X năm YYYY - Tháng Y năm ZZZZ (Vietnamese)
    pattern8 = re.findall(r'tháng\s+(\d{1,2})\s+năm\s+(\d{4})\s*[-–]\s*tháng\s+(\d{1,2})\s+năm\s+(\d{4})', 
                          experience_text, re.IGNORECASE)
    for start_month, start_year, end_month, end_year in pattern8:
        months = (int(end_year) - int(start_year)) * 12 + (int(end_month) - int(start_month))
        if months > 0 and (start_year, end_year, months) not in found_periods:
            total_months += months
    
    # Pattern 9: X years/năm (3 years, 5 năm kinh nghiệm)
    pattern9 = re.findall(r'(\d+(?:\.\d+)?)\s*(?:years?|năm)\s*(?:kinh nghiệm|experience)?', 
                          experience_text, re.IGNORECASE)
    if pattern9 and total_months == 0:  # Chỉ dùng nếu không tìm thấy pattern khác
        years = float(pattern9[0])
        total_months = int(years * 12)
    
    return round(total_months / 12, 1)


def _calculate_duration_score(years):
    """
    Tính điểm dựa trên thâm niên (thang 0-100)
    
    Args:
        years: Số năm kinh nghiệm
    
    Returns:
        int: Điểm duration (0-100)
    """
    if years < 0.5:
        return 30
    elif years < 1:
        return 50
    elif years < 2:
        return 70
    elif years < 3:
        return 85
    else:
        return 100


def _detect_experience_level(experience_text):
    """
    Tự động phát hiện cấp độ kinh nghiệm (thang 0-100)
    
    Args:
        experience_text: String chứa thông tin kinh nghiệm
    
    Returns:
        int: Điểm level (0-100)
    """
    if not experience_text or experience_text.lower() == 'n/a':
        return 0
    
    text_lower = experience_text.lower()
    
    # Professional experience markers
    professional_markers = ['senior', 'lead', 'manager', 'director', 'company', 'corp', 
                           'inc', 'ltd', 'developer', 'engineer']
    
    # Freelance/Contract markers
    freelance_markers = ['freelance', 'freelancer', 'contract', 'consultant', 'independent']
    
    # Personal/Academic markers
    personal_markers = ['personal project', 'side project', 'github', 'capstone', 
                       'thesis', 'course project', 'university project']
    
    # Internship markers
    internship_markers = ['intern', 'internship', 'trainee', 'thực tập']
    
    # Check markers
    if any(marker in text_lower for marker in professional_markers):
        return 100
    elif any(marker in text_lower for marker in freelance_markers):
        return 80
    elif any(marker in text_lower for marker in personal_markers):
        return 60
    elif any(marker in text_lower for marker in internship_markers):
        return 40
    else:
        # Default: có kinh nghiệm nhưng không rõ loại
        return 70


def _calculate_text_similarity(text1, text2):
    """
    Tính độ tương đồng giữa 2 đoạn text
    
    Args:
        text1: String thứ nhất
        text2: String thứ hai
    
    Returns:
        float: Điểm tương đồng (0-1)
    """
    if not text1 or not text2:
        return 0
    
    text1 = text1.lower()
    text2 = text2.lower()
    
    # Simple similarity using SequenceMatcher
    return SequenceMatcher(None, text1, text2).ratio()


def _calculate_keyword_matching(cv_text, jd_text):
    """
    Tính điểm matching dựa trên keywords chung
    
    Args:
        cv_text: Text từ CV
        jd_text: Text từ JD
    
    Returns:
        float: Điểm matching (0-1)
    """
    if not cv_text or not jd_text:
        return 0
    
    # Chuyển về lowercase và tách từ
    cv_words = set(re.findall(r'\b\w+\b', cv_text.lower()))
    jd_words = set(re.findall(r'\b\w+\b', jd_text.lower()))
    
    # Loại bỏ stop words đơn giản
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                  'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                  'could', 'should', 'may', 'might', 'must', 'can'}
    
    cv_words -= stop_words
    jd_words -= stop_words
    
    if not jd_words:
        return 0
    
    # Tính Jaccard similarity
    intersection = cv_words & jd_words
    union = cv_words | jd_words
    
    if not union:
        return 0
    
    return len(intersection) / len(union)


def _calculate_relevance_score(cv_data, jd_data):
    """
    Tính điểm độ liên quan giữa CV và JD (thang 0-100)
    
    Args:
        cv_data: Dict chứa thông tin CV
        jd_data: Dict hoặc String chứa thông tin JD
    
    Returns:
        int: Điểm relevance (0-100)
    """
    # Chuẩn bị text từ CV
    cv_text = ' '.join([
        str(cv_data.get('position', '')),
        str(cv_data.get('experience', '')),
        str(cv_data.get('hard_skills', '')),
        str(cv_data.get('soft_skills', ''))
    ])
    
    # Chuẩn bị text từ JD
    if isinstance(jd_data, dict):
        jd_text = ' '.join([
            str(jd_data.get('title', '')),
            str(jd_data.get('description', '')),
            str(jd_data.get('requirements', '')),
            str(jd_data.get('skills', ''))
        ])
    else:
        jd_text = str(jd_data)
    
    # Tính similarity
    text_sim = _calculate_text_similarity(cv_text, jd_text)
    keyword_match = _calculate_keyword_matching(cv_text, jd_text)
    
    # Kết hợp 2 phương pháp
    relevance_score = (text_sim * 0.4 + keyword_match * 0.6) * 100
    
    return int(relevance_score)


def score_experience(cv_data, jd_data, max_score=100, weights=None):
    
    # Thiết lập weights mặc định
    if weights is None:
        weights = {
            'relevance': 0.5,
            'duration': 0.3,
            'level': 0.2
        }
    
    # Validate weights
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Tổng weights phải bằng 1.0, hiện tại: {total_weight}")
    
    # 1. Tính các điểm thành phần (thang 0-100)
    relevance_score_100 = _calculate_relevance_score(cv_data, jd_data)
    
    experience_text = cv_data.get('experience', '')
    years = _extract_years_from_experience(experience_text)
    duration_score_100 = _calculate_duration_score(years)
    
    level_score_100 = _detect_experience_level(experience_text)
    
    # 2. Chuyển đổi về thang điểm max_score
    relevance_score = (relevance_score_100 / 100) * max_score * weights['relevance']
    duration_score = (duration_score_100 / 100) * max_score * weights['duration']
    level_score = (level_score_100 / 100) * max_score * weights['level']
    
    # 3. Tính tổng điểm
    total_score = round(relevance_score + duration_score + level_score, 2)
    
    # 4. Tạo mô tả chi tiết
    details = f"Ứng viên có {years} năm kinh nghiệm. "
    
    if relevance_score_100 >= 70:
        details += "Kinh nghiệm rất phù hợp với JD. "
    elif relevance_score_100 >= 50:
        details += "Kinh nghiệm khá phù hợp với JD. "
    else:
        details += "Kinh nghiệm chưa thực sự phù hợp với JD. "
    
    if level_score_100 >= 90:
        details += "Kinh nghiệm chuyên nghiệp."
    elif level_score_100 >= 70:
        details += "Có kinh nghiệm thực tế."
    else:
        details += "Kinh nghiệm còn hạn chế."
    
    return {
        'total_score': total_score,
        'max_score': max_score,
        'breakdown': {
            'relevance_score': round(relevance_score, 2),
            'duration_score': round(duration_score, 2),
            'level_score': round(level_score, 2)
        },
        'years_of_experience': years,
        'details': details
    }
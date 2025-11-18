"""
relevance_scoring.py
Chấm điểm độ liên quan giữa CV và JD đơn giản
Chỉ join text và so sánh bằng embeddings hoặc Ollama
"""

import requests
import json
from sentence_transformers import SentenceTransformer
import os


# ============= CONFIGURATION =============

_embedding_model = None

def get_embedding_model():
    """Load embedding model (lazy loading)"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    return _embedding_model


# Ollama config
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_TYPE = 'llama3.2:1b'
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', OLLAMA_TYPE )

# ============= TEXT PREPARATION =============

def _join_cv_text(cv_data):
    """Join tất cả thông tin CV thành 1 đoạn text"""
    parts = []
    
    # Position/Title
    if cv_data.get('position'):
        parts.append(f"Position: {cv_data['position']}")
    
    # Summary
    if cv_data.get('cv_summary'):
        parts.append(f"Summary: {cv_data['cv_summary']}")
    
    # Experience
    if cv_data.get('experience'):
        parts.append(f"Experience: {cv_data['experience']}")
    
    # Education
    if cv_data.get('education'):
        parts.append(f"Education: {cv_data['education']}")
    
    # Skills
    if cv_data.get('hard_skills'):
        parts.append(f"Technical Skills: {cv_data['hard_skills']}")
    
    if cv_data.get('soft_skills'):
        parts.append(f"Soft Skills: {cv_data['soft_skills']}")
    
    # Tools
    if cv_data.get('tools'):
        parts.append(f"Tools: {cv_data['tools']}")
    
    # Certificates
    if cv_data.get('certificates'):
        parts.append(f"Certificates: {cv_data['certificates']}")
    
    # Activities
    if cv_data.get('activities'):
        parts.append(f"Activities: {cv_data['activities']}")
    
    return '\n'.join(parts)


def _join_jd_text(jd_data):
    """Join tất cả thông tin JD thành 1 đoạn text"""
    if isinstance(jd_data, str):
        return jd_data
    
    parts = []
    
    if jd_data.get('title'):
        parts.append(f"Title: {jd_data['title']}")
    
    if jd_data.get('company'):
        parts.append(f"Company: {jd_data['company']}")
    
    if jd_data.get('description'):
        parts.append(f"Description: {jd_data['description']}")
    
    if jd_data.get('requirements'):
        parts.append(f"Requirements: {jd_data['requirements']}")
    
    if jd_data.get('responsibilities'):
        parts.append(f"Responsibilities: {jd_data['responsibilities']}")
    
    if jd_data.get('skills'):
        parts.append(f"Skills: {jd_data['skills']}")
    
    if jd_data.get('benefits'):
        parts.append(f"Benefits: {jd_data['benefits']}")
    
    return '\n'.join(parts)


# ============= OLLAMA METHOD (SMART) =============

def _check_ollama_available():
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def relevance_scoring(cv_data, jd_data, max_score):
    
    if not _check_ollama_available():
        print("ollama not available")
        return None
    
    # Join texts
    cv_text = _join_cv_text(cv_data)
    jd_text = _join_jd_text(jd_data)
    
    # Truncate if too long (keep first 2000 chars each)
    cv_text = cv_text[:2000]
    jd_text = jd_text[:2000]
    
    prompt = f"""Compare this CV with the Job Description and evaluate the match.

CV:
{cv_text}

Job Description:
{jd_text}

Evaluate how well this candidate fits the job. Consider:
1. Skills match (technical and soft skills)
2. Experience relevance
3. Role/position fit
4. Overall qualification

Return ONLY a JSON object (no markdown, no extra text):
{{
  "score": 85,
  "fit_level": "Excellent fit",
  "recommendation": "Highly recommended for interview",
  "strengths": ["Strong technical skills", "Relevant experience"],
  "gaps": ["Missing certification X"],
  "summary": "Brief explanation of the match"
}}

Score scale: 0-100
- 85-100: Excellent fit
- 70-84: Good fit
- 55-69: Fair fit
- 0-54: Poor fit"""
    
    try:
        print(f"Calling Ollama ({OLLAMA_MODEL})...")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.3,
                    "num_predict": 400
                }
            },
            timeout=30
        )

        
        result_text = response.json()['response']
        
        # Clean up
        result_text = result_text.strip()
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]
        result_text = result_text.strip()
        
        # Parse JSON
        result = json.loads(result_text)
        
        # Scale score to max_score
        ollama_score = result.get('score', 50)
        scaled_score = round((ollama_score / 100) * max_score, 2)
        
        return {
            'total_score': scaled_score,
            'max_score': max_score,
            'fit_level': result.get('fit_level', 'Unknown'),
            'recommendation': result.get('recommendation', 'N/A'),
            'strengths': result.get('strengths', []),
            'gaps': result.get('gaps', []),
            'summary': result.get('summary', ''),
            'method': 'ollama' + ' ' + OLLAMA_TYPE,
            'model': OLLAMA_MODEL,
            'details': result.get('summary', 'AI analysis completed')
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response: {result_text[:200]}")
        return print("none by JSON error")
    except Exception as e:
        print(f"Ollama failed: {e}")
        return print("none by exception")

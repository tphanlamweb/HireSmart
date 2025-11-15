"""
soft_skills_scoring_ollama.py
AI-Enhanced Soft Skills Scoring with Ollama (Local LLM)
Hybrid: Rule-based (fast) + Ollama (smart, free, local)
"""

import requests
import json
import os

# ============= OLLAMA CONFIGURATION =============

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')  # Lightweight model
USE_AI = True  # Always available if Ollama is running


def _check_ollama_available():
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False


def _llm_extract_soft_skills(text, jd_context=""):
    """
    Dùng Ollama để extract soft skills + evidence
    Chỉ gọi khi cần (unknown terms, complex context)
    """
    if not _check_ollama_available():
        print("Ollama not available. Falling back to rule-based only.")
        return None
    
    prompt = f"""Analyze this professional experience and extract soft skills.

Experience text:
{text[:1000]}

Job context (if any):
{jd_context[:300]}

Return ONLY valid JSON format (no markdown, no extra text):
{{
  "soft_skills": [
    {{
      "skill": "leadership",
      "evidence": "Led team of 5 developers",
      "confidence": 0.9
    }}
  ],
  "action_verbs": ["led", "managed", "coordinated"],
  "achievements": [
    {{
      "text": "Improved performance by 40%",
      "type": "quantified",
      "impact": "high"
    }}
  ]
}}

Focus on:
1. Soft skills actually demonstrated (not just mentioned)
2. Action verbs that prove the skills
3. Quantifiable achievements
4. Be concise - only include clear evidence

IMPORTANT: Return ONLY the JSON object, nothing else. No explanations, no markdown."""
    
    try:
        # Ollama API call
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",  # Force JSON output
                "options": {
                    "temperature": 0.3,
                    "num_predict": 600,  # Max tokens
                }
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"Ollama API error: {response.status_code}")
            return None
        
        result_text = response.json()['response']
        
        # Clean up response (remove markdown if present)
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
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print(f"Raw response: {result_text[:200]}")
        return None
    except requests.exceptions.Timeout:
        print("Ollama request timeout (60s)")
        return None
    except Exception as e:
        print(f"Ollama extraction failed: {e}")
        return None


def _should_use_llm(cv_data, jd_data, rulebased_result):
    """
    Quyết định có cần gọi LLM không
    Chỉ gọi khi:
    1. Rule-based score thấp (<50%) - có thể miss skills
    2. CV có nhiều text nhưng ít skills detected
    3. JD có yêu cầu phức tạp
    """
    # Case 1: Score quá thấp - có thể bị miss
    if rulebased_result['total_score'] < 0.5 * rulebased_result['max_score']:
        return True
    
    # Case 2: CV dài nhưng ít skills - suspicious
    experience_length = len(str(cv_data.get('experience', '')))
    detected_skills = len(rulebased_result['summary']['matched_skills'])
    
    if experience_length > 500 and detected_skills < 2:
        return True
    
    # Case 3: JD yêu cầu nhiều soft skills
    jd_text = str(jd_data)
    if len(jd_text) > 300 and 'soft skill' in jd_text.lower():
        return True
    
    return False


def _merge_results(rulebased_result, llm_result, max_score):
    """
    Combine rule-based + LLM results
    Strategy: LLM fills gaps, not replace
    """
    if not llm_result:
        return rulebased_result
    
    # Extract LLM insights
    llm_skills = [s['skill'] for s in llm_result.get('soft_skills', [])]
    llm_evidence = {s['skill']: s['evidence'] 
                    for s in llm_result.get('soft_skills', [])}
    llm_achievements = llm_result.get('achievements', [])
    
    # Boost score if LLM found additional evidence
    additional_skills = set(llm_skills) - set(rulebased_result['summary']['matched_skills'])
    
    if additional_skills:
        # Give bonus for LLM-discovered skills
        bonus = min(15, len(additional_skills) * 5)  # Max +15 points
        
        new_total = min(max_score, rulebased_result['total_score'] + bonus)
        
        # Update details
        details = rulebased_result['details']
        details += f" Ollama phát hiện thêm {len(additional_skills)} skills."
        
        return {
            **rulebased_result,
            'total_score': new_total,
            'details': details,
            'ai_enhanced': True,
            'ai_provider': f'ollama-{OLLAMA_MODEL}',
            'ai_additional_skills': list(additional_skills),
            'ai_evidence': llm_evidence
        }
    
    return {
        **rulebased_result,
        'ai_enhanced': True,
        'ai_provider': f'ollama-{OLLAMA_MODEL}',
        'ai_additional_skills': []
    }


def score_soft_skills_ai(cv_data, jd_data, max_score=100, weights=None, force_ai=False):
    """
    AI-Enhanced Soft Skills Scoring with Ollama
    
    Strategy:
    1. Chạy rule-based trước (fast, free)
    2. Nếu cần thiết, gọi Ollama (smart, free, local)
    3. Merge results
    
    Args:
        cv_data: CV dictionary
        jd_data: JD dictionary/string
        max_score: Max points
        weights: Custom weights
        force_ai: Force Ollama call (for testing)
    
    Returns:
        Enhanced result with optional Ollama insights
    """
    
    # Phase 1: Rule-based scoring (always run)
    rulebased_result = score_soft_skills_rulebased(cv_data, jd_data, max_score, weights)
    
    # Phase 2: Check if Ollama available
    if not _check_ollama_available():
        return {
            **rulebased_result,
            'ai_enhanced': False,
            'ai_available': False,
            'ai_error': 'Ollama not running'
        }
    
    # Phase 3: Decide if LLM needed
    use_llm = force_ai or _should_use_llm(cv_data, jd_data, rulebased_result)
    
    if not use_llm:
        return {
            **rulebased_result,
            'ai_enhanced': False,
            'ai_skipped': 'Score sufficient, Ollama not needed'
        }
    
    # Phase 4: Ollama enhancement
    print(f"Calling Ollama ({OLLAMA_MODEL})...")
    experience_text = str(cv_data.get('experience', ''))
    jd_context = str(jd_data)[:300]
    
    llm_result = _llm_extract_soft_skills(experience_text, jd_context)
    
    # Phase 5: Merge results
    final_result = _merge_results(rulebased_result, llm_result, max_score)
    
    return final_result





# ============= UTILITY FUNCTIONS =============

def test_ollama_connection():
    """Test Ollama connection and list available models"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✓ Ollama is running at {OLLAMA_BASE_URL}")
            print(f"Available models: {[m['name'] for m in models]}")
            return True
        else:
            print(f"✗ Ollama responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Ollama not available: {e}")
        print(f"Make sure Ollama is running: ollama serve")
        return False


def set_ollama_model(model_name):
    """Change Ollama model"""
    global OLLAMA_MODEL
    OLLAMA_MODEL = model_name
    print(f"Ollama model set to: {model_name}")


def score_soft_skills_rulebased(cv_data, jd_data, max_score=100, weights=None):
    """
    Rule-based soft skills scoring (Enhanced Hybrid):
    - Match skills between CV and JD
    - Bonus from evidence (action verbs near skill mentions)
    - Behavioral indicator bonus (distinct action verbs present)
    - Achievement bonus (quantified results / keywords / digits)
    Returns dict with keys: total_score, max_score, summary, details
    """
    def to_skill_set(x):
        if not x:
            return set()
        if isinstance(x, (list, tuple, set)):
            items = x
        else:
            items = [s.strip() for s in str(x).split(',')]
        return set(s.lower() for s in items if s)

    cv_skills = to_skill_set(cv_data.get('soft_skills', ''))
    if isinstance(jd_data, dict):
        jd_skills = to_skill_set(jd_data.get('soft_skills', ''))
    else:
        jd_skills = to_skill_set(jd_data)

    matched_skills = sorted(list(cv_skills & jd_skills))

    # Base score: proportion of JD skills matched (fallback to CV size if JD empty)
    denom = len(jd_skills) or max(len(cv_skills), 1)
    base_score = int(round(max_score * (len(matched_skills) / denom)))

    experience = str(cv_data.get('experience', '')).lower()

    # Action verbs and achievement cues
    action_verbs = [
        'led', 'managed', 'coordinated', 'mentored', 'organized', 'negotiated',
        'presented', 'facilitated', 'supervised', 'implemented', 'initiated',
        'collaborated', 'communicated', 'resolved', 'influenced'
    ]
    achievement_keywords = [
        'improved', 'increased', 'reduced', 'decreased', 'grew', 'won', 'award',
        'achieved', 'delivered', 'resulted', 'saved', '%', 'percent'
    ]

    # Evidence: matched skill appears near an action verb
    evidence_count = 0
    for skill in matched_skills:
        idx = experience.find(skill)
        if idx != -1:
            window = experience[max(0, idx - 60): idx + len(skill) + 60]
            if any(v in window for v in action_verbs):
                evidence_count += 1

    # Behavioral: count distinct action verbs present in experience
    behavioral_count = sum(1 for v in action_verbs if v in experience)

    # Achievement: presence of digits or achievement keywords
    achievement_count = 0
    if any(ch.isdigit() for ch in experience):
        achievement_count += 1
    achievement_count += sum(1 for kw in achievement_keywords if kw in experience)

    # Bonuses (clamped)
    evidence_bonus = min(15, evidence_count * 4)       # up to +15
    behavioral_bonus = min(5, behavioral_count * 1)    # up to +5
    achievement_bonus = min(10, achievement_count * 2) # up to +10

    total_score = min(max_score, base_score + evidence_bonus + behavioral_bonus + achievement_bonus)

    details = (
        f"Base={base_score}; evidence_count={evidence_count}, behavioral_count={behavioral_count}, "
        f"achievement_count={achievement_count}; bonuses: evidence+{evidence_bonus}, "
        f"behavioral+{behavioral_bonus}, achievement+{achievement_bonus}."
    )

    return {
        'total_score': int(total_score),
        'max_score': int(max_score),
        'summary': {
            'cv_skills': sorted(list(cv_skills)),
            'jd_skills': sorted(list(jd_skills)),
            'matched_skills': matched_skills,
            'evidence_count': evidence_count,
            'behavioral_count': behavioral_count,
            'achievement_count': achievement_count
        },
        'details': details
    }
    
def score_soft_skills(cv_data, jd_data, max_score=100, weights=None, use_ai='auto'):
    """
    Smart soft skills scoring with Ollama
    
    Args:
        cv_data: CV dictionary
        jd_data: JD dictionary/string
        max_score: Maximum score
        weights: Custom weights
        use_ai: 'auto' (default), True (force), False (never)
    
    Returns:
        Scoring result dictionary
    """
    if use_ai == False or use_ai == 'never':
        return score_soft_skills_rulebased(cv_data, jd_data, max_score, weights)
    
    return score_soft_skills_ai(cv_data, jd_data, max_score, weights, 
                                force_ai=(use_ai == True or use_ai == 'always'))
    
    
    
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# ============= CONFIGURATION =============

_embedding_model = None

def get_embedding_model():
    """Load embedding model (lazy loading)"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    return _embedding_model


# ============= SOFT SKILLS DATABASE =============

SOFT_SKILLS_CATEGORIES = {
    'communication': [
        'communication', 'verbal communication', 'written communication', 
        'presentation', 'public speaking', 'articulate', 'listening',
        'negotiation', 'persuasion', 'reporting',
        'giao tiếp', 'trình bày', 'thuyết trình', 'đàm phán'
    ],
    'teamwork': [
        'teamwork', 'team player', 'collaboration', 'cooperative', 
        'team collaboration', 'cross-functional', 'interpersonal',
        'partnership', 'team building',
        'làm việc nhóm', 'hợp tác', 'đồng đội'
    ],
    'leadership': [
        'leadership', 'lead', 'manage', 'mentor', 'coaching', 
        'team lead', 'project management', 'delegation', 'motivate',
        'supervise', 'guide', 'influence', 'inspire',
        'lãnh đạo', 'quản lý', 'dẫn dắt', 'chỉ đạo'
    ],
    'problem_solving': [
        'problem solving', 'analytical', 'critical thinking', 'troubleshooting',
        'decision making', 'logical thinking', 'creative thinking',
        'strategic thinking', 'root cause analysis',
        'giải quyết vấn đề', 'phân tích', 'tư duy', 'quyết định'
    ],
    'time_management': [
        'time management', 'organization', 'prioritization', 'planning',
        'multitasking', 'deadline', 'efficient', 'productivity',
        'scheduling', 'task management',
        'quản lý thời gian', 'tổ chức', 'ưu tiên', 'sắp xếp'
    ],
    'adaptability': [
        'adaptability', 'flexibility', 'learning agility', 'quick learner',
        'open-minded', 'resilience', 'versatile', 'change management',
        'pivot', 'adjust',
        'thích nghi', 'linh hoạt', 'học hỏi', 'thay đổi'
    ],
    'creativity': [
        'creativity', 'innovative', 'creative thinking', 'imagination',
        'out-of-box thinking', 'brainstorming', 'ideation', 'design thinking',
        'sáng tạo', 'đổi mới', 'ý tưởng'
    ],
    'attention_to_detail': [
        'attention to detail', 'detail-oriented', 'meticulous', 'thorough',
        'accuracy', 'precision', 'quality-focused', 'careful',
        'tỉ mỉ', 'cẩn thận', 'chính xác', 'chi tiết'
    ],
    'work_ethic': [
        'work ethic', 'dedicated', 'committed', 'reliable', 'responsible',
        'self-motivated', 'proactive', 'initiative', 'disciplined',
        'driven', 'persistent',
        'trách nhiệm', 'tận tâm', 'chủ động', 'kiên trì'
    ],
    'emotional_intelligence': [
        'emotional intelligence', 'empathy', 'self-awareness', 'social skills',
        'conflict resolution', 'patience', 'understanding', 'compassion',
        'thấu hiểu', 'đồng cảm', 'kiên nhẫn'
    ]
}

SOFT_SKILL_SYNONYMS = {
    'communicate': 'communication',
    'communicator': 'communication',
    'present': 'presentation',
    'presenter': 'presentation',
    'collaborate': 'collaboration',
    'cooperative': 'teamwork',
    'team work': 'teamwork',
    'leader': 'leadership',
    'leading': 'leadership',
    'manage': 'leadership',
    'manager': 'leadership',
    'solve problems': 'problem solving',
    'problem-solving': 'problem solving',
    'analytical thinking': 'analytical',
    'organize': 'organization',
    'organized': 'organization',
    'adapt': 'adaptability',
    'flexible': 'flexibility',
    'creative': 'creativity',
    'detail oriented': 'attention to detail',
    'detail-oriented': 'attention to detail',
    'hard working': 'work ethic',
    'hardworking': 'work ethic',
    'hard-working': 'work ethic',
}

# Role-specific soft skills importance
ROLE_SOFT_SKILLS = {
    'backend': ['problem solving', 'attention to detail', 'analytical', 'teamwork'],
    'frontend': ['creativity', 'attention to detail', 'communication', 'problem solving'],
    'fullstack': ['problem solving', 'time management', 'adaptability', 'teamwork'],
    'lead': ['leadership', 'communication', 'decision making', 'mentoring'],
    'senior': ['leadership', 'mentoring', 'problem solving', 'communication'],
    'manager': ['leadership', 'communication', 'time management', 'delegation'],
    'devops': ['problem solving', 'adaptability', 'teamwork', 'proactive'],
    'designer': ['creativity', 'communication', 'attention to detail', 'empathy'],
    'qa': ['attention to detail', 'analytical', 'communication', 'patience'],
}


# ============= ACTION VERBS MAPPING =============

ACTION_VERBS_TO_SOFT_SKILLS = {
    # Leadership verbs
    'led': ['leadership', 'decision making'],
    'lead': ['leadership', 'decision making'],
    'managed': ['leadership', 'time management'],
    'manage': ['leadership', 'time management'],
    'coordinated': ['leadership', 'organization'],
    'coordinate': ['leadership', 'organization'],
    'supervised': ['leadership'],
    'supervise': ['leadership'],
    'directed': ['leadership', 'decision making'],
    'delegated': ['leadership', 'time management'],
    'mentored': ['leadership', 'communication'],
    'coached': ['leadership', 'communication'],
    'trained': ['leadership', 'communication'],
    'guided': ['leadership'],
    'inspired': ['leadership', 'emotional intelligence'],
    
    # Teamwork verbs
    'collaborated': ['teamwork', 'communication'],
    'cooperated': ['teamwork'],
    'partnered': ['teamwork', 'communication'],
    'contributed': ['teamwork', 'work ethic'],
    'assisted': ['teamwork'],
    'supported': ['teamwork', 'emotional intelligence'],
    'worked with': ['teamwork'],
    
    # Communication verbs
    'presented': ['communication'],
    'communicated': ['communication'],
    'explained': ['communication'],
    'discussed': ['communication'],
    'negotiated': ['communication', 'problem solving'],
    'persuaded': ['communication'],
    'reported': ['communication'],
    'documented': ['communication', 'attention to detail'],
    'articulated': ['communication'],
    
    # Problem solving verbs
    'solved': ['problem solving'],
    'resolved': ['problem solving'],
    'analyzed': ['problem solving', 'analytical'],
    'investigated': ['problem solving', 'analytical'],
    'troubleshot': ['problem solving'],
    'debugged': ['problem solving', 'attention to detail'],
    'optimized': ['problem solving', 'analytical'],
    'improved': ['problem solving', 'creativity'],
    'enhanced': ['problem solving', 'creativity'],
    'redesigned': ['problem solving', 'creativity'],
    'refactored': ['problem solving', 'attention to detail'],
    
    # Initiative/Proactivity verbs
    'initiated': ['work ethic', 'leadership'],
    'proposed': ['creativity', 'communication'],
    'drove': ['leadership', 'work ethic'],
    'pioneered': ['creativity', 'leadership'],
    'launched': ['leadership', 'work ethic'],
    'introduced': ['creativity', 'communication'],
    'established': ['leadership', 'work ethic'],
    
    # Achievement verbs
    'achieved': ['work ethic', 'problem solving'],
    'accomplished': ['work ethic'],
    'delivered': ['work ethic', 'time management'],
    'completed': ['work ethic', 'time management'],
    'exceeded': ['work ethic'],
    'attained': ['work ethic'],
    
    # Organization verbs
    'organized': ['organization', 'time management'],
    'planned': ['organization', 'time management'],
    'scheduled': ['time management'],
    'prioritized': ['time management', 'decision making'],
    'streamlined': ['organization', 'problem solving'],
    
    # Adaptability verbs
    'adapted': ['adaptability'],
    'adjusted': ['adaptability'],
    'pivoted': ['adaptability', 'problem solving'],
    'transformed': ['adaptability', 'creativity'],
    'migrated': ['adaptability', 'problem solving'],
}


# ============= ACHIEVEMENT PATTERNS =============

ACHIEVEMENT_PATTERNS = {
    'quantified': [
        r'(\d+)%\s+(?:increase|improvement|growth|boost|enhancement)',
        r'(?:increased|improved|grew|boosted|enhanced)\s+(?:by\s+)?(\d+)%',
        r'(?:reduced|decreased|cut)\s+(?:by\s+)?(\d+)%',
        r'saved\s+\$?(\d+(?:,\d{3})*(?:\.\d+)?)',
        r'generated\s+\$?(\d+(?:,\d{3})*)',
        r'managed\s+(?:team\s+of\s+)?(\d+)\s+(?:people|members|developers|engineers)',
        r'led\s+(?:team\s+of\s+)?(\d+)',
        r'completed\s+(\d+)\s+projects',
        r'delivered\s+(\d+)\s+(?:projects|features|releases)',
    ],
    'time_based': [
        r'(?:delivered|completed|finished)\s+(?:on\s+time|ahead\s+of\s+schedule)',
        r'reduced\s+(?:delivery\s+)?time\s+(?:by\s+)?(\d+)%',
        r'faster\s+(?:by\s+)?(\d+)%',
        r'within\s+(?:deadline|timeline|schedule)',
    ],
    'quality_based': [
        r'improved\s+quality',
        r'zero\s+(?:defects|bugs|errors)',
        r'(\d+)%\s+(?:accuracy|precision)',
        r'enhanced\s+(?:user\s+)?(?:experience|satisfaction)',
    ],
    'scale_based': [
        r'scaled\s+(?:to\s+)?(\d+)',
        r'handled\s+(\d+(?:,\d{3})*)\s+(?:users|requests|transactions)',
        r'managed\s+(\d+)\s+(?:projects|tasks)',
    ],
    'recognition': [
        r'awarded?',
        r'recognized',
        r'promoted',
        r'selected',
        r'nominated',
        r'won',
        r'received\s+(?:award|recognition)',
    ]
}


# ============= HELPER FUNCTIONS =============

def _normalize_soft_skill(skill):
    """Chuẩn hóa soft skill"""
    if not skill:
        return ''
    
    skill_lower = skill.lower().strip()
    skill_lower = re.sub(r'[^\w\s\-]', '', skill_lower)
    skill_lower = re.sub(r'\s+', ' ', skill_lower)
    
    if skill_lower in SOFT_SKILL_SYNONYMS:
        return SOFT_SKILL_SYNONYMS[skill_lower]
    
    return skill_lower


def _extract_soft_skills_from_text(text):
    """Trích xuất soft skills từ text"""
    if not text or text.lower() == 'n/a':
        return []
    
    text_lower = text.lower()
    found_skills = []
    
    # Check all known soft skills
    for category, skills in SOFT_SKILLS_CATEGORIES.items():
        for skill in skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                normalized = _normalize_soft_skill(skill)
                if normalized not in found_skills:
                    found_skills.append(normalized)
    
    # Extract from common patterns
    patterns = [
        r'soft skills?:?\s*([^.\n]+)',
        r'key strengths?:?\s*([^.\n]+)',
        r'personal skills?:?\s*([^.\n]+)',
        r'core competenc(?:y|ies):?\s*([^.\n]+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            skills = re.split(r'[,;|]', match)
            for skill in skills:
                normalized = _normalize_soft_skill(skill.strip())
                if normalized and len(normalized) > 2:
                    found_skills.append(normalized)
    
    return list(set(found_skills))


def _get_soft_skill_category(skill):
    """Xác định category của soft skill"""
    skill_norm = _normalize_soft_skill(skill)
    
    for category, skills in SOFT_SKILLS_CATEGORIES.items():
        for known_skill in skills:
            if skill_norm == known_skill or skill_norm in known_skill or known_skill in skill_norm:
                return category
    
    return 'other'


# ============= 1. EVIDENCE-BASED SCORING (40%) =============

def _detect_skill_evidence(text, skill):
    """
    Tìm bằng chứng về soft skill trong experience/activities
    Returns: evidence score (0-100)
    """
    if not text:
        return 0
    
    text_lower = text.lower()
    skill_lower = _normalize_soft_skill(skill)
    score = 0
    
    # Evidence patterns cho từng loại soft skill
    evidence_patterns = {
        'communication': [
            r'present(?:ed|ing)?\s+(?:to|at|for)',
            r'communicat(?:e|ed|ing)\s+with',
            r'spoke\s+(?:to|with|at)',
            r'client\s+(?:meeting|presentation|interaction)',
            r'stakeholder\s+(?:communication|engagement)',
            r'report(?:ed|ing)\s+to',
        ],
        'leadership': [
            r'lead\s+(?:a\s+)?team',
            r'manage(?:d)?\s+\d+\s+(?:people|members|developers)',
            r'mentor(?:ed|ing)?',
            r'coach(?:ed|ing)?',
            r'supervise(?:d)?',
            r'guide(?:d)?\s+team',
            r'direct(?:ed)?\s+team',
        ],
        'teamwork': [
            r'work(?:ed)?\s+with\s+team',
            r'collaborate(?:d)?\s+with',
            r'cross-functional\s+team',
            r'team\s+of\s+\d+',
            r'partnered\s+with',
            r'coordinated\s+with',
        ],
        'problem_solving': [
            r'solve(?:d)?\s+(?:complex|technical|critical)',
            r'troubleshoot(?:ed|ing)?',
            r'debug(?:ged)?',
            r'optimize(?:d)?',
            r'improve(?:d)?',
            r'resolve(?:d)?',
            r'fix(?:ed)?',
        ],
        'time_management': [
            r'manage(?:d)?\s+multiple\s+projects',
            r'prioritize(?:d)?',
            r'(?:met|meet)\s+deadline',
            r'on\s+time',
            r'delivered\s+on\s+schedule',
            r'concurrent\s+projects',
        ],
    }
    
    category = _get_soft_skill_category(skill)
    
    # Direct mention
    if skill_lower in text_lower:
        score += 25
    
    # Evidence from patterns
    if category in evidence_patterns:
        for pattern in evidence_patterns[category]:
            if re.search(pattern, text_lower):
                score += 12
    
    # Check for quantifiable achievements
    for pattern_type, patterns in ACHIEVEMENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                score += 8
                break
    
    return min(100, score)


def _calculate_evidence_score(cv_data, matched_soft_skills):
    """Calculate evidence-based score (40%)"""
    experience_text = ' '.join([
        str(cv_data.get('experience', '')),
        str(cv_data.get('activities', '')),
        str(cv_data.get('cv_summary', ''))
    ])
    
    if not matched_soft_skills:
        if _extract_soft_skills_from_text(experience_text):
            return 40  # Has soft skills but no match
        return 0
    
    evidence_scores = []
    for cv_skill, jd_skill, _ in matched_soft_skills:
        evidence = _detect_skill_evidence(experience_text, cv_skill)
        evidence_scores.append(evidence)
    
    avg_evidence = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0
    
    return int(avg_evidence)


# ============= 2. BEHAVIORAL ANALYSIS (35%) =============

def _extract_action_verbs(text):
    """Extract action verbs from text"""
    if not text:
        return []
    
    text_lower = text.lower()
    found_verbs = []
    
    for verb in ACTION_VERBS_TO_SOFT_SKILLS.keys():
        # Look for verb at start of sentence or after punctuation
        pattern = r'(?:^|[.•\n])\s*' + re.escape(verb) + r'\b'
        matches = re.findall(pattern, text_lower, re.MULTILINE)
        found_verbs.extend([verb] * len(matches))
    
    return found_verbs


def _map_verbs_to_soft_skills(action_verbs):
    """Map action verbs to soft skills with frequency"""
    skill_scores = {}
    
    for verb in action_verbs:
        if verb in ACTION_VERBS_TO_SOFT_SKILLS:
            soft_skills = ACTION_VERBS_TO_SOFT_SKILLS[verb]
            for skill in soft_skills:
                if skill not in skill_scores:
                    skill_scores[skill] = 0
                skill_scores[skill] += 1
    
    return skill_scores


def _calculate_behavioral_score(cv_data, jd_soft_skills):
    """Calculate behavioral analysis score (35%)"""
    experience_text = str(cv_data.get('experience', ''))
    
    # Extract action verbs
    action_verbs = _extract_action_verbs(experience_text)
    
    if not action_verbs:
        return 30  # Neutral score if no action verbs
    
    # Map to soft skills
    skill_frequency = _map_verbs_to_soft_skills(action_verbs)
    
    # Normalize JD skills
    jd_normalized = [_normalize_soft_skill(s) for s in jd_soft_skills]
    
    # Calculate match score
    matched_count = 0
    total_frequency = 0
    
    for jd_skill in jd_normalized:
        jd_category = _get_soft_skill_category(jd_skill)
        
        # Check if any behavioral evidence for this category
        for inferred_skill, freq in skill_frequency.items():
            if _get_soft_skill_category(inferred_skill) == jd_category:
                matched_count += 1
                total_frequency += freq
                break
    
    if not jd_normalized:
        # If no JD soft skills, score based on total verb diversity
        return min(100, len(skill_frequency) * 15)
    
    # Calculate score
    match_rate = matched_count / len(jd_normalized)
    frequency_bonus = min(30, total_frequency * 3)  # Bonus for frequency
    
    behavioral_score = int((match_rate * 70) + frequency_bonus)
    
    return min(100, behavioral_score)


# ============= 3. ACHIEVEMENT-BASED SCORING (25%) =============

def _extract_achievements(text):
    """Extract quantified achievements from text"""
    if not text:
        return []
    
    achievements = []
    text_lower = text.lower()
    
    for achievement_type, patterns in ACHIEVEMENT_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                achievements.append({
                    'type': achievement_type,
                    'text': match.group(0),
                    'value': match.group(1) if match.groups() else None
                })
    
    return achievements


def _score_achievement_quality(achievement):
    """Score individual achievement quality"""
    achievement_type = achievement['type']
    value = achievement['value']
    
    # Base scores by type
    base_scores = {
        'quantified': 25,      # Highest - has numbers
        'recognition': 20,     # High - external validation
        'scale_based': 18,     # Good - shows scope
        'time_based': 15,      # Good - shows efficiency
        'quality_based': 12,   # Moderate - subjective
    }
    
    base = base_scores.get(achievement_type, 10)
    
    # Bonus for high impact numbers
    if value and achievement_type == 'quantified':
        try:
            num = int(re.sub(r'[^\d]', '', value))
            if num >= 50:
                base += 10
            elif num >= 30:
                base += 5
        except:
            pass
    
    return base


def _map_achievements_to_soft_skills(achievements, jd_soft_skills):
    """Map achievements to soft skills they demonstrate"""
    achievement_to_skills = {
        'quantified': ['problem solving', 'analytical', 'work ethic'],
        'time_based': ['time management', 'work ethic', 'organization'],
        'quality_based': ['attention to detail', 'work ethic'],
        'scale_based': ['leadership', 'time management', 'organization'],
        'recognition': ['work ethic', 'leadership', 'communication'],
    }
    
    soft_skill_scores = {}
    
    for achievement in achievements:
        quality_score = _score_achievement_quality(achievement)
        related_skills = achievement_to_skills.get(achievement['type'], [])
        
        for skill in related_skills:
            if skill not in soft_skill_scores:
                soft_skill_scores[skill] = 0
            soft_skill_scores[skill] += quality_score
    
    return soft_skill_scores


def _calculate_achievement_score(cv_data, jd_soft_skills):
    """Calculate achievement-based score (25%)"""
    experience_text = str(cv_data.get('experience', ''))
    
    # Extract achievements
    achievements = _extract_achievements(experience_text)
    
    if not achievements:
        return 20  # Low score if no achievements
    
    # Map achievements to soft skills
    achievement_scores = _map_achievements_to_soft_skills(achievements, jd_soft_skills)
    
    # Normalize JD skills
    jd_normalized = [_normalize_soft_skill(s) for s in jd_soft_skills]
    
    # Calculate match
    matched_score = 0
    for jd_skill in jd_normalized:
        jd_category = _get_soft_skill_category(jd_skill)
        
        # Check if achievements demonstrate this skill
        for inferred_skill, score in achievement_scores.items():
            if _get_soft_skill_category(inferred_skill) == jd_category:
                matched_score += min(score, 30)  # Cap per skill
                break
    
    # Normalize to 0-100
    if jd_normalized:
        achievement_score = int((matched_score / (len(jd_normalized) * 30)) * 100)
    else:
        # No JD skills - score based on total achievements
        achievement_score = min(100, len(achievements) * 20)
    
    return min(100, achievement_score)


# ============= SEMANTIC MATCHING =============

def _semantic_soft_skill_matching(cv_soft_skills, jd_soft_skills, threshold=0.70):
    """Semantic matching cho soft skills"""
    if not cv_soft_skills or not jd_soft_skills:
        return {
            'matched': [],
            'unmatched_jd': jd_soft_skills,
            'extra_cv': cv_soft_skills
        }
    
    model = get_embedding_model()
    
    cv_texts = [f"soft skill {s}" for s in cv_soft_skills]
    jd_texts = [f"required soft skill {s}" for s in jd_soft_skills]
    
    cv_embeddings = model.encode(cv_texts)
    jd_embeddings = model.encode(jd_texts)
    
    similarity_matrix = cosine_similarity(cv_embeddings, jd_embeddings)
    
    matched = []
    matched_jd_indices = set()
    matched_cv_indices = set()
    
    for j, jd_skill in enumerate(jd_soft_skills):
        similarities = similarity_matrix[:, j]
        best_cv_idx = np.argmax(similarities)
        best_score = similarities[best_cv_idx]
        
        cv_skill = cv_soft_skills[best_cv_idx]
        
        # Boost if same category
        cv_cat = _get_soft_skill_category(cv_skill)
        jd_cat = _get_soft_skill_category(jd_skill)
        
        if cv_cat == jd_cat and cv_cat != 'other':
            best_score = max(best_score, 0.85)
        
        if best_score >= threshold:
            matched.append((cv_skill, jd_skill, float(best_score)))
            matched_jd_indices.add(j)
            matched_cv_indices.add(best_cv_idx)
    
    unmatched_jd = [jd_soft_skills[i] for i in range(len(jd_soft_skills)) if i not in matched_jd_indices]
    extra_cv = [cv_soft_skills[i] for i in range(len(cv_soft_skills)) if i not in matched_cv_indices]
    
    return {
        'matched': matched,
        'unmatched_jd': unmatched_jd,
        'extra_cv': extra_cv
    }


# ============= MAIN SCORING FUNCTION =============

def score_soft_skills(cv_data, jd_data, max_score=100, weights=None):
    """
    Hàm chính: Chấm điểm Soft Skills với Enhanced Hybrid Approach
    
    Args:
        cv_data (dict): Thông tin CV
            - soft_skills: String/list soft skills
            - experience: String kinh nghiệm
            - activities: String hoạt động
            - cv_summary: String tóm tắt
        
        jd_data (dict/str): Thông tin JD
        
        max_score (int): Điểm tối đa (default: 100)
        
        weights (dict): Trọng số (default: None)
            {
                'evidence': 0.40,
                'behavioral': 0.35,
                'achievement': 0.25
            }
    
    Returns:
        dict: {
            'total_score': float,
            'max_score': int,
            'breakdown': {...},
            'summary': {...},
            'details': str
        }
    """
    
    # Default weights - Enhanced Hybrid
    if weights is None:
        weights = {
            'evidence': 0.40,
            'behavioral': 0.35,
            'achievement': 0.25
        }
    
    # Validate weights
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Tổng weights phải bằng 1.0, hiện tại: {total_weight}")
    
    # ===== Extract CV soft skills =====
    cv_soft_skills = []
    
    soft_skills_field = cv_data.get('soft_skills', '')
    if isinstance(soft_skills_field, list):
        cv_soft_skills.extend(soft_skills_field)
    else:
        cv_soft_skills.extend(_extract_soft_skills_from_text(str(soft_skills_field)))
    
    # Extract from experience
    experience = cv_data.get('experience', '')
    if experience and experience != 'n/a':
        cv_soft_skills.extend(_extract_soft_skills_from_text(str(experience)))
    
    # Extract from activities
    activities = cv_data.get('activities', '')
    if activities and activities != 'n/a':
        cv_soft_skills.extend(_extract_soft_skills_from_text(str(activities)))
    
    # Extract from summary
    summary = cv_data.get('cv_summary', '')
    if summary and summary != 'n/a':
        cv_soft_skills.extend(_extract_soft_skills_from_text(str(summary)))
    
    cv_soft_skills = list(set([_normalize_soft_skill(s) for s in cv_soft_skills if s]))
    
    # ===== Extract JD soft skills =====
    jd_text = ''
    if isinstance(jd_data, dict):
        jd_text = ' '.join([
            str(jd_data.get('title', '')),
            str(jd_data.get('requirements', '')),
            str(jd_data.get('description', ''))
        ])
    else:
        jd_text = str(jd_data)
    
    jd_soft_skills = _extract_soft_skills_from_text(jd_text)
    jd_soft_skills = list(set([_normalize_soft_skill(s) for s in jd_soft_skills if s]))
    
    # If no explicit soft skills in JD, infer from role
    if not jd_soft_skills:
        jd_lower = jd_text.lower()
        for role, default_skills in ROLE_SOFT_SKILLS.items():
            if role in jd_lower:
                jd_soft_skills.extend(default_skills)
                break
        
        # Default soft skills if still empty
        if not jd_soft_skills:
            jd_soft_skills = ['teamwork', 'communication', 'problem solving']
    
    # ===== Semantic matching =====
    matching_result = _semantic_soft_skill_matching(cv_soft_skills, jd_soft_skills)
    
    # ===== Calculate 3 scores =====
    evidence_score = _calculate_evidence_score(cv_data, matching_result['matched'])
    behavioral_score = _calculate_behavioral_score(cv_data, jd_soft_skills)
    achievement_score = _calculate_achievement_score(cv_data, jd_soft_skills)
    
    # ===== Calculate Total Score =====
    total_score_100 = (
        evidence_score * weights['evidence'] +
        behavioral_score * weights['behavioral'] +
        achievement_score * weights['achievement']
    )
    
    total_score = round((total_score_100 / 100) * max_score, 2)
    
    # ===== Prepare Summary =====
    matched_skills = [jd_skill for _, jd_skill, _ in matching_result['matched']]
    missing_skills = matching_result['unmatched_jd']
    
    # Extract stats for details
    action_verbs = _extract_action_verbs(str(cv_data.get('experience', '')))
    achievements = _extract_achievements(str(cv_data.get('experience', '')))
    
    # Calculate diversity
    cv_categories = set([_get_soft_skill_category(s) for s in cv_soft_skills])
    cv_categories.discard('other')
    
    # Generate details
    match_rate = len(matched_skills) / len(jd_soft_skills) * 100 if jd_soft_skills else 0
    
    details = f"Soft skills: {len(matched_skills)}/{len(jd_soft_skills)} matched ({match_rate:.0f}%). "
    
    if evidence_score >= 70:
        details += "Có bằng chứng tốt trong kinh nghiệm. "
    elif evidence_score >= 40:
        details += "Có đề cập nhưng thiếu bằng chứng cụ thể. "
    else:
        details += "Thiếu bằng chứng về soft skills. "
    
    if len(action_verbs) >= 10:
        details += f"Tìm thấy {len(action_verbs)} action verbs. "
    
    if len(achievements) >= 3:
        details += f"Có {len(achievements)} thành tựu được lượng hóa. "
    elif len(achievements) == 0:
        details += "Thiếu thành tựu cụ thể. "
    
    if len(cv_categories) >= 4:
        details += "Soft skills đa dạng."
    
    return {
        'total_score': total_score,
        'max_score': max_score,
        'breakdown': {
            'evidence': {
                'score': round(evidence_score * max_score * weights['evidence'] / 100, 2),
                'weight': weights['evidence'],
                'raw_score': evidence_score
            },
            'behavioral': {
                'score': round(behavioral_score * max_score * weights['behavioral'] / 100, 2),
                'weight': weights['behavioral'],
                'raw_score': behavioral_score
            },
            'achievement': {
                'score': round(achievement_score * max_score * weights['achievement'] / 100, 2),
                'weight': weights['achievement'],
                'raw_score': achievement_score
            }
        },
        'summary': {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'cv_categories': list(cv_categories),
            'total_cv_soft_skills': len(cv_soft_skills),
            'action_verbs_count': len(action_verbs),
            'achievements_count': len(achievements),
            'match_rate': round(match_rate, 1)
        },
        'details': details
    }
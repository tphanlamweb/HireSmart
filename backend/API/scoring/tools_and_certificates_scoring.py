"""
tools_and_certificates_scoring.py
Chấm điểm Tools & Certificates
"""

import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


# ============= CONFIGURATION =============

_embedding_model = None
model_name: str = "sentence-transformers/LaBSE"
def get_embedding_model():
    """Load embedding model (lazy loading)"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model


# ============= TOOLS DATABASE =============

TOOL_CATEGORIES = {
    'ide_editor': [
        'vscode', 'visual studio code', 'intellij', 'pycharm', 'webstorm',
        'sublime text', 'atom', 'vim', 'emacs', 'eclipse', 'netbeans',
        'visual studio', 'android studio', 'xcode'
    ],
    'version_control': [
        'git', 'github', 'gitlab', 'bitbucket', 'svn', 'mercurial',
        'sourcetree', 'gitflow', 'github actions', 'gitlab ci'
    ],
    'collaboration': [
        'jira', 'confluence', 'trello', 'asana', 'slack', 'microsoft teams',
        'notion', 'monday.com', 'clickup', 'basecamp', 'teams'
    ],
    'api_testing': [
        'postman', 'insomnia', 'swagger', 'openapi', 'soapui',
        'rest client', 'graphql playground', 'curl'
    ],
    'design': [
        'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
        'invision', 'zeplin', 'canva', 'affinity designer'
    ],
    'database_tools': [
        'mysql workbench', 'phpmyadmin', 'pgadmin', 'mongodb compass',
        'dbeaver', 'datagrip', 'sql server management studio', 'navicat'
    ],
    'devops_tools': [
        'docker', 'kubernetes', 'jenkins', 'travis ci', 'circleci',
        'terraform', 'ansible', 'vagrant', 'nginx', 'apache'
    ],
    'monitoring': [
        'prometheus', 'grafana', 'datadog', 'new relic', 'elk stack',
        'splunk', 'sentry', 'logstash', 'kibana'
    ],
    'productivity': [
        'microsoft office', 'google workspace', 'excel', 'word', 'powerpoint',
        'google sheets', 'google docs', 'notion', 'evernote'
    ]
}

TOOL_SYNONYMS = {
    'vs code': 'vscode',
    'visual studio code': 'vscode',
    'vs': 'visual studio',
    'github actions': 'github',
    'ms teams': 'microsoft teams',
    'ms office': 'microsoft office',
    'g suite': 'google workspace',
    'k8s': 'kubernetes',
    'ps': 'photoshop',
    'ai': 'illustrator',
    'xd': 'adobe xd',
}


# ============= CERTIFICATES DATABASE =============

CERTIFICATE_CATEGORIES = {
    'cloud': [
        'aws', 'azure', 'gcp', 'google cloud', 'cloud practitioner',
        'solutions architect', 'devops engineer', 'security specialty'
    ],
    'programming': [
        'oracle certified', 'microsoft certified', 'python institute',
        'java certification', 'certified developer'
    ],
    'project_management': [
        'pmp', 'prince2', 'agile', 'scrum master', 'csm', 'psm',
        'safe', 'itil', 'capm'
    ],
    'security': [
        'cissp', 'ceh', 'security+', 'comptia security', 'cism', 'cisa',
        'oscp', 'certified ethical hacker'
    ],
    'data': [
        'data science', 'machine learning', 'data analyst', 'data engineer',
        'big data', 'hadoop', 'spark certification'
    ],
    'networking': [
        'ccna', 'ccnp', 'network+', 'comptia network', 'cisco certified'
    ],
    'database': [
        'oracle dba', 'mysql', 'mongodb certified', 'sql server',
        'database administrator'
    ],
    'soft_skills': [
        'communication', 'leadership', 'english', 'toeic', 'ielts',
        'japanese', 'jlpt', 'presentation skills'
    ]
}

# Certificate tiers (importance/value)
CERTIFICATE_TIERS = {
    'tier_1': {  # Most valuable
        'weight': 1.5,
        'certs': ['pmp', 'aws certified solutions architect', 'cissp', 'ceh',
                  'google cloud professional', 'azure solutions architect']
    },
    'tier_2': {  # Valuable
        'weight': 1.2,
        'certs': ['scrum master', 'aws certified developer', 'ccna',
                  'oracle certified', 'microsoft certified']
    },
    'tier_3': {  # Standard
        'weight': 1.0,
        'certs': ['toeic', 'ielts', 'comptia', 'itil', 'agile']
    }
}


# ============= HELPER FUNCTIONS =============

def _normalize_tool(tool):
    """Chuẩn hóa tên tool"""
    if not tool:
        return ''
    
    tool_lower = tool.lower().strip()
    tool_lower = re.sub(r'[^\w\s\.\-]', '', tool_lower)
    tool_lower = re.sub(r'\s+', ' ', tool_lower)
    
    # Check synonyms
    if tool_lower in TOOL_SYNONYMS:
        return TOOL_SYNONYMS[tool_lower]
    
    return tool_lower


def _normalize_certificate(cert):
    """Chuẩn hóa tên certificate"""
    if not cert:
        return ''
    
    cert_lower = cert.lower().strip()
    # Keep important keywords, remove noise
    cert_lower = re.sub(r'\s*\d{4}\s*', ' ', cert_lower)  # Remove years
    cert_lower = re.sub(r'\s+', ' ', cert_lower).strip()
    
    return cert_lower


def _extract_tools_from_text(text):
    """Trích xuất tools từ text"""
    if not text or text.lower() == 'n/a':
        return []
    
    tools = []
    
    # Method 1: Split by delimiters
    basic_tools = re.split(r'[,;|\n•]+', text)
    tools.extend(basic_tools)
    
    # Method 2: Find known tools in text
    text_lower = text.lower()
    for category, category_tools in TOOL_CATEGORIES.items():
        for tool in category_tools:
            pattern = r'\b' + re.escape(tool) + r'\b'
            if re.search(pattern, text_lower):
                tools.append(tool)
    
    # Normalize and deduplicate
    normalized = []
    for tool in tools:
        tool_clean = _normalize_tool(tool)
        if tool_clean and len(tool_clean) > 1:
            normalized.append(tool_clean)
    
    return list(set(normalized))


def _extract_certificates_from_text(text):
    """Trích xuất certificates từ text"""
    if not text or text.lower() == 'n/a':
        return []
    
    certs = []
    
    # Method 1: Split by delimiters
    basic_certs = re.split(r'[,;|\n•]+', text)
    certs.extend(basic_certs)
    
    # Method 2: Find patterns
    cert_patterns = [
        r'certified?\s+[\w\s]+',
        r'[\w\s]+\s+certification',
        r'[\w\s]+\s+certificate',
    ]
    
    for pattern in cert_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        certs.extend(matches)
    
    # Normalize and deduplicate
    normalized = []
    for cert in certs:
        cert_clean = _normalize_certificate(cert)
        if cert_clean and len(cert_clean) > 3:
            normalized.append(cert_clean)
    
    return list(set(normalized))


def _get_tool_category(tool):
    """Xác định category của tool"""
    tool_norm = _normalize_tool(tool)
    
    for category, tools in TOOL_CATEGORIES.items():
        if tool_norm in tools:
            return category
    
    return 'other'


def _get_certificate_category(cert):
    """Xác định category của certificate"""
    cert_norm = _normalize_certificate(cert)
    
    for category, certs in CERTIFICATE_CATEGORIES.items():
        for known_cert in certs:
            if known_cert in cert_norm or cert_norm in known_cert:
                return category
    
    return 'other'


def _get_certificate_tier(cert):
    """Xác định tier/value của certificate"""
    cert_norm = _normalize_certificate(cert)
    
    for tier, data in CERTIFICATE_TIERS.items():
        for tier_cert in data['certs']:
            if tier_cert in cert_norm or cert_norm in tier_cert:
                return tier, data['weight']
    
    return 'tier_3', 1.0


def _check_certificate_relevance(cert, jd_text):
    """Kiểm tra certificate có liên quan đến JD không"""
    cert_norm = _normalize_certificate(cert)
    jd_lower = jd_text.lower()
    
    # Direct mention
    if cert_norm in jd_lower:
        return 1.0
    
    # Category match
    cert_category = _get_certificate_category(cert)
    
    category_keywords = {
        'cloud': ['cloud', 'aws', 'azure', 'gcp'],
        'security': ['security', 'secure', 'cybersecurity'],
        'project_management': ['project manager', 'scrum', 'agile', 'pm'],
        'data': ['data', 'analytics', 'machine learning', 'ai'],
    }
    
    if cert_category in category_keywords:
        for keyword in category_keywords[cert_category]:
            if keyword in jd_lower:
                return 0.8
    
    return 0.3  # Low relevance


# ============= SEMANTIC MATCHING =============

def _semantic_tool_matching(cv_tools, jd_tools, threshold=0.70):
    """Semantic matching cho tools"""
    if not cv_tools or not jd_tools:
        return {
            'matched': [],
            'unmatched_jd': jd_tools,
            'extra_cv': cv_tools
        }
    
    model = get_embedding_model()
    
    cv_texts = [f"tool {t}" for t in cv_tools]
    jd_texts = [f"required tool {t}" for t in jd_tools]
    
    cv_embeddings = model.encode(cv_texts)
    jd_embeddings = model.encode(jd_texts)
    
    similarity_matrix = cosine_similarity(cv_embeddings, jd_embeddings)
    
    matched = []
    matched_jd_indices = set()
    matched_cv_indices = set()
    
    for j, jd_tool in enumerate(jd_tools):
        similarities = similarity_matrix[:, j]
        best_cv_idx = np.argmax(similarities)
        best_score = similarities[best_cv_idx]
        
        cv_tool = cv_tools[best_cv_idx]
        
        # Boost if same category
        cv_cat = _get_tool_category(cv_tool)
        jd_cat = _get_tool_category(jd_tool)
        
        if cv_cat == jd_cat and cv_cat != 'other':
            best_score = max(best_score, 0.85)
        
        if best_score >= threshold:
            matched.append((cv_tool, jd_tool, float(best_score)))
            matched_jd_indices.add(j)
            matched_cv_indices.add(best_cv_idx)
    
    unmatched_jd = [jd_tools[i] for i in range(len(jd_tools)) if i not in matched_jd_indices]
    extra_cv = [cv_tools[i] for i in range(len(cv_tools)) if i not in matched_cv_indices]
    
    return {
        'matched': matched,
        'unmatched_jd': unmatched_jd,
        'extra_cv': extra_cv
    }


# ============= SCORING FUNCTIONS =============

def _calculate_tools_score(cv_tools, jd_tools, matching_result):
    """
    Tính điểm Tools (60% of total)
    - Coverage: 40%
    - Diversity: 30%
    - Relevance: 30%
    """
    if not jd_tools:
        # No JD tools specified - score based on diversity
        cv_categories = set([_get_tool_category(t) for t in cv_tools])
        cv_categories.discard('other')
        diversity_score = min(100, len(cv_categories) * 20)
        return {
            'score': diversity_score,
            'coverage': 100,
            'diversity': diversity_score,
            'relevance': 100
        }
    
    # Coverage: % tools matched
    coverage = len(matching_result['matched']) / len(jd_tools) * 100 if jd_tools else 0
    
    # Diversity: categories covered
    cv_categories = set([_get_tool_category(t) for t in cv_tools])
    cv_categories.discard('other')
    jd_categories = set([_get_tool_category(t) for t in jd_tools])
    jd_categories.discard('other')
    
    if jd_categories:
        diversity = len(cv_categories & jd_categories) / len(jd_categories) * 100
    else:
        diversity = min(100, len(cv_categories) * 25)
    
    # Relevance: quality of matches
    if matching_result['matched']:
        avg_similarity = sum([score for _, _, score in matching_result['matched']]) / len(matching_result['matched'])
        relevance = avg_similarity * 100
    else:
        relevance = 0
    
    # Combined score
    tools_score = int(coverage * 0.4 + diversity * 0.3 + relevance * 0.3)
    
    return {
        'score': tools_score,
        'coverage': round(coverage, 1),
        'diversity': round(diversity, 1),
        'relevance': round(relevance, 1)
    }


def _calculate_certificates_score(cv_certs, jd_text):
    """
    Tính điểm Certificates (40% of total)
    - Relevance: 60%
    - Quality (tier): 40%
    """
    if not cv_certs:
        return {
            'score': 0,
            'relevance': 0,
            'quality': 0,
            'tier_breakdown': {}
        }
    
    # Relevance: certificates liên quan đến JD
    relevance_scores = []
    for cert in cv_certs:
        rel_score = _check_certificate_relevance(cert, jd_text)
        relevance_scores.append(rel_score)
    
    avg_relevance = sum(relevance_scores) / len(relevance_scores) * 100 if relevance_scores else 0
    
    
    # Quality: based on tier
    tier_counts = {'tier_1': 0, 'tier_2': 0, 'tier_3': 0}
    total_weighted = 0
    
    for cert in cv_certs:
        tier, weight = _get_certificate_tier(cert)
        tier_counts[tier] += 1
        total_weighted += weight
    
    # Normalize quality score
    max_possible = len(cv_certs) * 1.5  # If all tier_1
    quality_score = (total_weighted / max_possible * 100) if max_possible > 0 else 0
    
    # Combined score
    cert_score = int(avg_relevance * 0.6 + quality_score * 0.4)
    
    return {
        'score': cert_score,
        'relevance': round(avg_relevance, 1),
        'quality': round(quality_score, 1),
        'tier_breakdown': tier_counts
    }


# ============= MAIN SCORING FUNCTION =============

def score_tools_and_certificates(cv_data, jd_data, max_score=100, weights=None):
    """
    Hàm chính: Chấm điểm Tools & Certificates
    
    Args:
        cv_data (dict): Thông tin CV
            - tools: String/list tools
            - certificates: String/list certificates
        
        jd_data (dict/str): Thông tin JD
        
        max_score (int): Điểm tối đa (default: 100)
        
        weights (dict): Trọng số (default: None)
            {
                'tools': 0.60,
                'certificates': 0.40
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
    
    # Default weights
    if weights is None:
        weights = {
            'tools': 0.50,
            'certificates': 0.50
        }
    
    # Validate weights
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Tổng weights phải bằng 1.0, hiện tại: {total_weight}")
    
    # ===== Extract CV tools =====
    cv_tools = []
    tools_field = cv_data.get('tools', '')
    if isinstance(tools_field, list):
        cv_tools.extend(tools_field)
    else:
        cv_tools.extend(_extract_tools_from_text(str(tools_field)))
    
    # Also extract from hard_skills if contains tools
    hard_skills = cv_data.get('hard_skills', '')
    if hard_skills:
        potential_tools = _extract_tools_from_text(str(hard_skills))
        cv_tools.extend([t for t in potential_tools if _get_tool_category(t) != 'other'])
    
    cv_tools = list(set([_normalize_tool(t) for t in cv_tools if t]))
    
    # ===== Extract CV certificates =====
    cv_certs = []
    certs_field = cv_data.get('certificates', '')
    if isinstance(certs_field, list):
        cv_certs.extend(certs_field)
    else:
        cv_certs.extend(_extract_certificates_from_text(str(certs_field)))
    
    cv_certs = list(set([_normalize_certificate(c) for c in cv_certs if c]))
    
    # ===== Extract JD requirements =====
    jd_text = ''
    if isinstance(jd_data, dict):
        jd_text = ' '.join([
            str(jd_data.get('requirements', '')),
        ])
    else:
        jd_text = str(jd_data)
    
    jd_tools = _extract_tools_from_text(jd_text)
    jd_tools = list(set([_normalize_tool(t) for t in jd_tools if t]))
    
    # ===== Semantic matching for tools =====
    tool_matching = _semantic_tool_matching(cv_tools, jd_tools)
    
    # ===== Calculate scores =====
    tools_result = _calculate_tools_score(cv_tools, jd_tools, tool_matching)
    certs_result = _calculate_certificates_score(cv_certs, jd_text)
    
    # ===== Calculate total score =====
    total_score_100 = (
        tools_result['score'] * weights['tools'] +
        certs_result['score'] * weights['certificates']
    )
    
    total_score = round((total_score_100 / 100) * max_score, 2)
    
    # ===== Prepare summary =====
    matched_tools = [jd_tool for _, jd_tool, _ in tool_matching['matched']]
    missing_tools = tool_matching['unmatched_jd']
    
    # Generate details
    details = f"Tools: {len(matched_tools)}/{len(jd_tools)} matched. " if jd_tools else f"CV có {len(cv_tools)} tools. "
    
    if cv_certs:
        details += f"Certificates: {len(cv_certs)} total"
        tier_1_count = certs_result.get('tier_breakdown', {}).get('tier_1', 0)
        if tier_1_count > 0:
            details += f" ({tier_1_count} high-value)"
        details += ". "
    else:
        details += "Không có certificates. "
    
    if tools_result['coverage'] >= 80:
        details += "Tools coverage tốt."
    elif tools_result['coverage'] < 50:
        details += "Thiếu nhiều tools quan trọng."
    
    return {
        'total_score': total_score,
        'max_score': max_score,
        'breakdown': {
            'tools': {
                'score': round(tools_result['score'] * max_score * weights['tools'] / 100, 2),
                'weight': weights['tools'],
                'raw_score': tools_result['score'],
                'details': tools_result
            },
            'certificates': {
                'score': round(certs_result['score'] * max_score * weights['certificates'] / 100, 2),
                'weight': weights['certificates'],
                'raw_score': certs_result['score'],
                'details': certs_result
            }
        },
        'summary': {
            'cv_tools': cv_tools[:10],  # Limit to 10
            'cv_certificates': cv_certs,
            'matched_tools': matched_tools,
            'missing_tools': missing_tools,
            'total_cv_tools': len(cv_tools),
            'total_cv_certs': len(cv_certs)
        },
        'details': details
    }


# ============= CONVENIENCE FUNCTIONS =============

def score_tools_only(cv_data, jd_data, max_score=100):
    """Chỉ chấm điểm Tools (bỏ qua Certificates)"""
    return score_tools_and_certificates(
        cv_data, 
        jd_data, 
        max_score, 
        weights={'tools': 1.0, 'certificates': 0.0}
    )


def score_certificates_only(cv_data, jd_data, max_score=100):
    """Chỉ chấm điểm Certificates (bỏ qua Tools)"""
    return score_tools_and_certificates(
        cv_data, 
        jd_data, 
        max_score, 
        weights={'tools': 0.0, 'certificates': 1.0}
    )


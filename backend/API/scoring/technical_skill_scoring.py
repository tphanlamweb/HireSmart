import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict


# ============= CONFIGURATION =============

# Load model một lần duy nhất (singleton pattern)
_embedding_model = None

def get_embedding_model():
    """Load embedding model (lazy loading)"""
    global _embedding_model
    if _embedding_model is None:
        # Model tốt hơn cho technical terms
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


# ============= COMPREHENSIVE SKILL DATABASE =============

SKILL_CATEGORIES = {
    'frontend': [
        'react', 'vue', 'angular', 'svelte', 'javascript', 'typescript', 'html', 'css',
        'sass', 'less', 'webpack', 'vite', 'nextjs', 'nuxt', 'gatsby', 'jquery',
        'bootstrap', 'tailwind', 'material-ui', 'ant design', 'redux', 'vuex', 'mobx',
        'jsx', 'tsx', 'babel', 'eslint', 'prettier', 'responsive design', 'spa', 'pwa'
    ],
    'backend': [
        'php', 'python', 'java', 'nodejs', 'node.js', 'c#', 'csharp', 'ruby', 'go', 'golang',
        'rust', 'kotlin', 'scala', 'laravel', 'symfony', 'codeigniter', 'django', 'flask',
        'fastapi', 'spring', 'spring boot', 'express', 'expressjs', 'nestjs', 'fastify',
        '.net', 'dotnet', 'asp.net', 'rails', 'ruby on rails', 'gin', 'echo', 'fiber',
        'rest api', 'restful', 'graphql', 'grpc', 'soap', 'microservices', 'api gateway',
        'mvc', 'mvvm', 'clean architecture', 'solid', 'design patterns'
    ],
    'database': [
        'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'sql', 'oracle', 'mariadb',
        'sqlserver', 'mssql', 'sqlite', 'dynamodb', 'cassandra', 'couchdb', 'neo4j',
        'elasticsearch', 'elastic search', 'solr', 'memcached', 'database design',
        'nosql', 'rdbms', 'orm', 'eloquent', 'sequelize', 'typeorm', 'prisma', 'hibernate',
        'query optimization', 'indexing', 'transactions', 'acid', 'sharding', 'replication'
    ],
    'devops': [
        'docker', 'kubernetes', 'k8s', 'jenkins', 'gitlab ci', 'github actions', 'travis ci',
        'circleci', 'aws', 'azure', 'gcp', 'google cloud', 'terraform', 'ansible', 'chef',
        'puppet', 'vagrant', 'ci/cd', 'continuous integration', 'continuous deployment',
        'nginx', 'apache', 'load balancing', 'reverse proxy', 'monitoring', 'prometheus',
        'grafana', 'elk stack', 'datadog', 'newrelic', 'linux', 'ubuntu', 'centos', 'bash',
        'shell scripting', 'infrastructure as code', 'iac', 'cloudformation', 'serverless'
    ],
    'mobile': [
        'react native', 'flutter', 'ios', 'android', 'swift', 'kotlin', 'objective-c',
        'xamarin', 'ionic', 'cordova', 'phonegap', 'mobile development', 'app development',
        'android studio', 'xcode', 'firebase', 'push notification', 'deep linking'
    ],
    'testing': [
        'jest', 'mocha', 'chai', 'jasmine', 'pytest', 'unittest', 'junit', 'testng',
        'selenium', 'cypress', 'playwright', 'puppeteer', 'phpunit', 'rspec', 'cucumber',
        'unit testing', 'integration testing', 'e2e testing', 'test automation', 'tdd',
        'bdd', 'test driven development', 'behavior driven development', 'code coverage'
    ],
    'data': [
        'data science', 'machine learning', 'ml', 'deep learning', 'ai', 'artificial intelligence',
        'neural networks', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
        'data analysis', 'data visualization', 'power bi', 'tableau', 'data mining',
        'big data', 'hadoop', 'spark', 'kafka', 'data warehouse', 'etl', 'data pipeline'
    ],
    'security': [
        'security', 'cybersecurity', 'authentication', 'authorization', 'oauth', 'jwt',
        'encryption', 'ssl', 'tls', 'https', 'owasp', 'penetration testing', 'vulnerability',
        'xss', 'csrf', 'sql injection', 'firewall', 'vpn', 'iam', 'zero trust'
    ],
    'tools': [
        'git', 'github', 'gitlab', 'bitbucket', 'svn', 'version control', 'jira', 'confluence',
        'trello', 'asana', 'slack', 'postman', 'insomnia', 'swagger', 'openapi', 'figma',
        'sketch', 'adobe xd', 'vscode', 'visual studio', 'intellij', 'pycharm', 'vim',
        'sublime text', 'npm', 'yarn', 'pip', 'composer', 'maven', 'gradle', 'make'
    ]
}

# Comprehensive synonyms mapping
SKILL_SYNONYMS = {
    # Programming Languages
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'c#': 'csharp',
    'c sharp': 'csharp',
    
    # Frameworks
    'react.js': 'react',
    'reactjs': 'react',
    'react native': 'react native',
    'vue.js': 'vue',
    'vuejs': 'vue',
    'angular.js': 'angular',
    'angularjs': 'angular',
    'node': 'nodejs',
    'node.js': 'nodejs',
    'express.js': 'express',
    'expressjs': 'express',
    'next.js': 'nextjs',
    'nuxt.js': 'nuxt',
    'asp.net': 'dotnet',
    '.net': 'dotnet',
    'spring framework': 'spring',
    
    # Databases
    'mongo': 'mongodb',
    'postgres': 'postgresql',
    'pg': 'postgresql',
    'mysql': 'mysql',
    'ms sql': 'mssql',
    'sql server': 'mssql',
    'elastic': 'elasticsearch',
    
    # DevOps
    'k8s': 'kubernetes',
    'kube': 'kubernetes',
    'docker compose': 'docker',
    'docker-compose': 'docker',
    'aws': 'aws',
    'amazon web services': 'aws',
    'google cloud platform': 'gcp',
    'microsoft azure': 'azure',
    'ci/cd': 'cicd',
    'continuous integration': 'cicd',
    
    # Concepts
    'ml': 'machine learning',
    'ai': 'artificial intelligence',
    'dl': 'deep learning',
    'nn': 'neural networks',
    'rest': 'rest api',
    'restful api': 'rest api',
    'graphql api': 'graphql',
    'oop': 'object oriented programming',
    'fp': 'functional programming',
}

# Skill groups - skills that often appear together
SKILL_GROUPS = {
    'php_stack': ['php', 'laravel', 'symfony', 'composer', 'phpunit', 'eloquent'],
    'python_stack': ['python', 'django', 'flask', 'fastapi', 'pip', 'pytest', 'pandas'],
    'javascript_stack': ['javascript', 'nodejs', 'express', 'npm', 'jest', 'webpack'],
    'react_stack': ['react', 'redux', 'jsx', 'react router', 'hooks', 'nextjs'],
    'vue_stack': ['vue', 'vuex', 'nuxt', 'vue router', 'composition api'],
    'java_stack': ['java', 'spring', 'spring boot', 'maven', 'gradle', 'hibernate', 'junit'],
    'devops_stack': ['docker', 'kubernetes', 'jenkins', 'terraform', 'ansible'],
    'aws_stack': ['aws', 'ec2', 's3', 'lambda', 'rds', 'cloudfront', 'cloudformation'],
    'database_stack': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
    'testing_stack': ['unit testing', 'integration testing', 'jest', 'pytest', 'selenium'],
}

# Related skills - skills that are similar/interchangeable
RELATED_SKILLS = {
    'mysql': ['postgresql', 'mariadb', 'sql', 'mssql'],
    'postgresql': ['mysql', 'mariadb', 'sql'],
    'mongodb': ['couchdb', 'dynamodb', 'cassandra'],
    'react': ['vue', 'angular', 'svelte'],
    'vue': ['react', 'angular'],
    'angular': ['react', 'vue'],
    'laravel': ['symfony', 'codeigniter', 'cakephp'],
    'django': ['flask', 'fastapi', 'pyramid'],
    'express': ['fastify', 'nestjs', 'koa'],
    'docker': ['kubernetes', 'docker-compose', 'containerization'],
    'kubernetes': ['docker', 'docker swarm', 'openshift'],
    'aws': ['azure', 'gcp', 'cloud'],
    'azure': ['aws', 'gcp', 'cloud'],
    'jest': ['mocha', 'jasmine', 'vitest'],
    'pytest': ['unittest', 'nose', 'robot framework'],
}

# Skill importance levels for different roles
ROLE_CRITICAL_SKILLS = {
    'backend': ['api', 'database', 'server', 'authentication', 'security'],
    'frontend': ['html', 'css', 'javascript', 'responsive', 'ui/ux'],
    'fullstack': ['frontend', 'backend', 'database', 'api', 'deployment'],
    'devops': ['docker', 'kubernetes', 'ci/cd', 'cloud', 'monitoring'],
    'mobile': ['ios', 'android', 'mobile', 'app', 'firebase'],
    'data': ['python', 'sql', 'data analysis', 'machine learning', 'statistics'],
}


# ============= HELPER FUNCTIONS =============

def _normalize_skill(skill):
    """Chuẩn hóa tên skill với nhiều rules hơn"""
    if not skill:
        return ''
    
    skill_lower = skill.lower().strip()
    
    # Remove version numbers (e.g., "PHP 8.0" -> "php")
    skill_lower = re.sub(r'\s*\d+(\.\d+)*\s*', ' ', skill_lower).strip()
    
    # Remove special characters except dots, hyphens, and spaces
    skill_lower = re.sub(r'[^\w\s\.\-\/]', '', skill_lower)
    
    # Normalize spaces
    skill_lower = re.sub(r'\s+', ' ', skill_lower)
    
    # Check synonyms first
    if skill_lower in SKILL_SYNONYMS:
        return SKILL_SYNONYMS[skill_lower]
    
    # Check partial matches in synonyms
    for synonym, normalized in SKILL_SYNONYMS.items():
        if synonym in skill_lower or skill_lower in synonym:
            return normalized
    
    return skill_lower


def _extract_skills_from_text(text, aggressive=True):
    """
    Trích xuất skills từ text với nhiều patterns
    
    Args:
        text: Text cần extract
        aggressive: Nếu True, tìm thêm skills trong câu (không chỉ list)
    """
    if not text or text.lower() == 'n/a':
        return []
    
    skills = []
    
    # Method 1: Split by delimiters (classic)
    basic_skills = re.split(r'[,;|\n•·]+', text)
    skills.extend(basic_skills)
    
    # Method 2: Find skills in sentences (aggressive mode)
    if aggressive:
        # Look for common skill patterns
        text_lower = text.lower()
        
        # Pattern: "experience with X", "skilled in X", "proficient in X"
        experience_patterns = [
            r'experience (?:with|in)\s+([^,.\n]+)',
            r'skilled (?:with|in|at)\s+([^,.\n]+)',
            r'proficient (?:with|in|at)\s+([^,.\n]+)',
            r'expertise (?:with|in)\s+([^,.\n]+)',
            r'knowledge of\s+([^,.\n]+)',
            r'working with\s+([^,.\n]+)',
            r'using\s+([^,.\n]+)',
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.extend(matches)
        
        # Find known skills anywhere in text
        for category, category_skills in SKILL_CATEGORIES.items():
            for known_skill in category_skills:
                # Use word boundaries for better matching
                pattern = r'\b' + re.escape(known_skill) + r'\b'
                if re.search(pattern, text_lower):
                    skills.append(known_skill)
    
    # Normalize all skills
    normalized = []
    for skill in skills:
        skill_clean = _normalize_skill(skill)
        if skill_clean and len(skill_clean) > 1:
            normalized.append(skill_clean)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_skills = []
    for skill in normalized:
        if skill not in seen:
            seen.add(skill)
            unique_skills.append(skill)
    
    return unique_skills


def _get_skill_category(skill):
    """Xác định category của skill với fuzzy matching"""
    skill_lower = _normalize_skill(skill)
    
    # Exact match
    for category, skills in SKILL_CATEGORIES.items():
        if skill_lower in skills:
            return category
    
    # Partial match (e.g., "react native" contains "react")
    for category, skills in SKILL_CATEGORIES.items():
        for known_skill in skills:
            if known_skill in skill_lower or skill_lower in known_skill:
                if len(skill_lower) > 2:  # Avoid false positives with short words
                    return category
    
    return 'other'


def _is_skill_related(skill1, skill2, threshold=0.7):
    """
    Kiểm tra 2 skills có related không
    
    Returns:
        tuple: (is_related, relation_type, score)
    """
    s1 = _normalize_skill(skill1)
    s2 = _normalize_skill(skill2)
    
    # Exact match
    if s1 == s2:
        return True, 'exact', 1.0
    
    # Check predefined related skills
    if s1 in RELATED_SKILLS:
        if s2 in RELATED_SKILLS[s1]:
            return True, 'related', 0.8
    
    # Check if in same skill group
    for group_name, group_skills in SKILL_GROUPS.items():
        if s1 in group_skills and s2 in group_skills:
            return True, 'same_group', 0.9
    
    # Check if same category
    cat1 = _get_skill_category(s1)
    cat2 = _get_skill_category(s2)
    if cat1 == cat2 and cat1 != 'other':
        return True, 'same_category', 0.6
    
    # Substring matching for compound skills
    if s1 in s2 or s2 in s1:
        return True, 'substring', 0.75
    
    return False, 'none', 0.0


def _detect_skill_level_from_text(text, skill):
    """Detect skill level với nhiều patterns hơn"""
    if not text:
        return 70
    
    text_lower = text.lower()
    skill_lower = _normalize_skill(skill)
    
    # Expert/Advanced indicators
    expert_patterns = [
        f'expert (?:in|with|at) {skill_lower}',
        f'{skill_lower} expert',
        f'advanced {skill_lower}',
        f'mastery (?:of|in) {skill_lower}',
        f'deep knowledge (?:of|in) {skill_lower}',
    ]
    
    for pattern in expert_patterns:
        if re.search(pattern, text_lower):
            return 100
    
    # Find years of experience with more patterns
    years_patterns = [
        rf'(\d+)\+?\s*(?:years?|năm|yr).*{skill_lower}',
        rf'{skill_lower}.*(\d+)\+?\s*(?:years?|năm|yr)',
        rf'(\d+)\+?\s*(?:years?|năm|yr).*experience.*{skill_lower}',
    ]
    
    max_years = 0
    for pattern in years_patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            for match in matches:
                try:
                    years = int(re.sub(r'\D', '', str(match)))
                    max_years = max(max_years, years)
                except:
                    pass
    
    if max_years >= 5:
        return 95
    elif max_years >= 4:
        return 85
    elif max_years >= 3:
        return 75
    elif max_years >= 2:
        return 65
    elif max_years >= 1:
        return 55
    
    # Seniority indicators
    seniority_patterns = [
        (r'senior.*' + skill_lower, 85),
        (r'lead.*' + skill_lower, 90),
        (r'principal.*' + skill_lower, 95),
        (r'junior.*' + skill_lower, 50),
        (r'intermediate.*' + skill_lower, 70),
    ]
    
    for pattern, score in seniority_patterns:
        if re.search(pattern, text_lower):
            return score
    
    return 70


# ============= ENHANCED EMBEDDING-BASED FUNCTIONS =============

def _semantic_skill_matching(cv_skills, jd_skills, threshold=0.65):
    """
    Enhanced semantic matching với multi-level scoring
    """
    if not cv_skills or not jd_skills:
        return {
            'matched': [],
            'unmatched_jd': jd_skills,
            'extra_cv': cv_skills
        }
    
    model = get_embedding_model()
    
    # Encode skills with context
    cv_skill_texts = [f"technical skill {s}" for s in cv_skills]
    jd_skill_texts = [f"required skill {s}" for s in jd_skills]
    
    cv_embeddings = model.encode(cv_skill_texts)
    jd_embeddings = model.encode(jd_skill_texts)
    
    # Calculate similarity matrix
    similarity_matrix = cosine_similarity(cv_embeddings, jd_embeddings)
    
    # Enhanced matching with multi-criteria
    matched = []
    matched_jd_indices = set()
    matched_cv_indices = set()
    
    for j, jd_skill in enumerate(jd_skills):
        similarities = similarity_matrix[:, j]
        best_cv_idx = np.argmax(similarities)
        semantic_score = similarities[best_cv_idx]
        
        cv_skill = cv_skills[best_cv_idx]
        
        # Check rule-based relationship
        is_related, relation_type, relation_score = _is_skill_related(cv_skill, jd_skill)
        
        # Combined scoring
        if relation_type == 'exact':
            final_score = 1.0
        elif relation_type in ['related', 'same_group']:
            final_score = max(semantic_score, relation_score)
        elif semantic_score >= threshold:
            final_score = semantic_score
        else:
            final_score = 0
        
        if final_score >= threshold:
            matched.append((cv_skill, jd_skill, float(final_score), relation_type))
            matched_jd_indices.add(j)
            matched_cv_indices.add(best_cv_idx)
    
    # Find unmatched
    unmatched_jd = [jd_skills[i] for i in range(len(jd_skills)) if i not in matched_jd_indices]
    extra_cv = [cv_skills[i] for i in range(len(cv_skills)) if i not in matched_cv_indices]
    
    return {
        'matched': matched,
        'unmatched_jd': unmatched_jd,
        'extra_cv': extra_cv
    }


def _semantic_text_similarity(text1, text2):
    """Enhanced text similarity"""
    if not text1 or not text2:
        return 0.0
    
    model = get_embedding_model()
    
    # Add context to improve encoding
    text1_enhanced = f"candidate profile: {text1}"
    text2_enhanced = f"job requirements: {text2}"
    
    embeddings = model.encode([text1_enhanced, text2_enhanced])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    return float(similarity)


# ============= ENHANCED SCORING FUNCTIONS =============

def _calculate_coverage_score(cv_skills, jd_skills, matching_result):
    """Enhanced coverage với weighted categories"""
    if not jd_skills:
        return {'score': 100, 'breadth': 100, 'depth': 100, 'details': {}}
    
    # Categorize với weighted importance
    jd_categories = defaultdict(list)
    for skill in jd_skills:
        cat = _get_skill_category(skill)
        jd_categories[cat].append(skill)
    
    # Category weights (more important categories)
    category_weights = {
        'backend': 1.2,
        'frontend': 1.2,
        'database': 1.1,
        'devops': 1.0,
        'testing': 0.9,
        'tools': 0.8,
        'other': 0.7
    }
    
    matched_by_category = defaultdict(list)
    for cv_skill, jd_skill, score, rel_type in matching_result['matched']:
        cat = _get_skill_category(jd_skill)
        matched_by_category[cat].append((jd_skill, score))
    
    # Calculate weighted breadth
    required_cats = set(jd_categories.keys())
    covered_cats = set(matched_by_category.keys()) & required_cats
    
    breadth_weights = sum([category_weights.get(cat, 1.0) for cat in covered_cats])
    total_weights = sum([category_weights.get(cat, 1.0) for cat in required_cats])
    
    breadth = breadth_weights / total_weights if total_weights > 0 else 0
    
    # Calculate weighted depth
    depth_scores = []
    category_details = {}
    
    for cat in required_cats:
        cat_jd_skills = jd_categories[cat]
        cat_matched = matched_by_category.get(cat, [])
        
        # Weighted depth by match quality
        if cat_matched:
            avg_match_quality = sum([score for _, score in cat_matched]) / len(cat_matched)
            coverage_ratio = len(cat_matched) / len(cat_jd_skills)
            depth = coverage_ratio * avg_match_quality
        else:
            depth = 0
        
        weight = category_weights.get(cat, 1.0)
        depth_scores.append(depth * weight)
        
        category_details[cat] = {
            'required': len(cat_jd_skills),
            'matched': len(cat_matched),
            'depth': round(depth * 100, 1),
            'weight': weight
        }
    
    avg_depth = sum(depth_scores) / len(depth_scores) if depth_scores else 0
    
    # Combined score
    coverage_score = int((breadth * 0.4 + avg_depth * 0.6) * 100)
    
    return {
        'score': coverage_score,
        'breadth': round(breadth * 100, 1),
        'depth': round(avg_depth * 100, 1),
        'details': category_details
    }


def _calculate_priority_score(matching_result, jd_text):
    """Enhanced priority với better classification"""
    jd_lower = jd_text.lower()
    
    # Enhanced keyword detection
    critical_keywords = [
        'required', 'must have', 'must-have', 'essential', 'mandatory', 
        'critical', 'necessary', 'yêu cầu', 'bắt buộc', 'cần thiết'
    ]
    
    important_keywords = [
        'important', 'should have', 'should', 'strongly prefer', 'highly desired',
        'prefer', 'preferred', 'ưu tiên', 'mong muốn'
    ]
    
    nice_keywords = [
        'nice to have', 'nice-to-have', 'bonus', 'plus', 'advantage',
        'beneficial', 'helpful', 'lợi thế', 'điểm cộng'
    ]
    
    # Classify matched skills
    core_matched = []
    important_matched = []
    nice_matched = []
    
    for cv_skill, jd_skill, similarity, rel_type in matching_result['matched']:
        skill_pos = jd_lower.find(jd_skill.lower())
        
        if skill_pos == -1:
            nice_matched.append((jd_skill, similarity))
            continue
        
        # Extended context
        context = jd_lower[max(0, skill_pos-100):min(len(jd_lower), skill_pos+100)]
        
        # Check priority level
        if any(kw in context for kw in critical_keywords):
            core_matched.append((jd_skill, similarity, rel_type))
        elif any(kw in context for kw in important_keywords):
            important_matched.append((jd_skill, similarity, rel_type))
        elif any(kw in context for kw in nice_keywords):
            nice_matched.append((jd_skill, similarity))
        else:
            # Default: consider position in JD
            if skill_pos < len(jd_lower) * 0.3:  # Early in JD = more important
                important_matched.append((jd_skill, similarity, rel_type))
            else:
                nice_matched.append((jd_skill, similarity))
    
    # Calculate weighted score with match quality
    core_weight = 3
    important_weight = 2
    nice_weight = 1
    
    # Bonus for exact matches
    achieved = 0
    for skill, sim, rel_type in core_matched:
        bonus = 1.2 if rel_type == 'exact' else 1.0
        achieved += sim * core_weight * bonus
    
    for skill, sim, rel_type in important_matched:
        bonus = 1.1 if rel_type == 'exact' else 1.0
        achieved += sim * important_weight * bonus
    
    for skill, sim in nice_matched:
        achieved += sim * nice_weight
    
    # Estimate total
    total_matched = len(core_matched) + len(important_matched) + len(nice_matched)
    total_unmatched = len(matching_result['unmatched_jd'])
    
    # If no explicit classification, use smart distribution
    if not core_matched and not important_matched:
        total_skills = total_matched + total_unmatched
        estimated_core = int(total_skills * 0.5)
        estimated_important = int(total_skills * 0.3)
        estimated_nice = total_skills - estimated_core - estimated_important
        
        total_weight = (estimated_core * core_weight + 
                       estimated_important * important_weight + 
                       estimated_nice * nice_weight)
    else:
        # Assume unmatched are important
        avg_weight = (core_weight + important_weight) / 2
        total_weight = achieved + (total_unmatched * avg_weight * 1.5)  # Penalty for missing
    
    priority_score = int((achieved / total_weight * 100)) if total_weight > 0 else 0
    
    return {
        'score': min(100, priority_score),
        'core_matched': [s for s, _, _ in core_matched],
        'important_matched': [s for s, _, _ in important_matched],
        'nice_matched': [s for s, _ in nice_matched],
        'missing_critical': matching_result['unmatched_jd'][:5]
    }


def _calculate_seniority_score(cv_data, jd_text, cv_skills, matching_result):
    """Enhanced seniority với skill-level matching"""
    jd_lower = jd_text.lower()
    
    # Enhanced level detection
    required_level = 'mid'
    required_score = 70
    
    # More comprehensive patterns
    senior_patterns = [
        r'senior', r'sr\.', r'lead', r'principal', r'staff',
        r'5\+?\s*(?:years|yr|năm)', r'expert', r'experienced'
    ]
    
    mid_patterns = [
        r'mid-level', r'intermediate', r'3-5\s*(?:years|yr)',
        r'2-4\s*(?:years|yr)'
    ]
    
    junior_patterns = [
        r'junior', r'jr\.', r'entry', r'graduate', r'fresher',
        r'0-2\s*(?:years|yr)', r'intern'
    ]
    
    if any(re.search(p, jd_lower) for p in senior_patterns):
        required_level = 'senior'
        required_score = 85
    elif any(re.search(p, jd_lower) for p in junior_patterns):
        required_level = 'junior'
        required_score = 50
    elif any(re.search(p, jd_lower) for p in mid_patterns):
        required_level = 'mid'
        required_score = 70
    
    # Detect CV skill levels - only for matched skills
    experience_text = str(cv_data.get('experience', ''))
    
    matched_skills = [cv_skill for cv_skill, _, _, _ in matching_result['matched']]
    skill_levels = []
    
    for skill in matched_skills[:15]:  # Top 15 matched skills
        level = _detect_skill_level_from_text(experience_text, skill)
        skill_levels.append(level)
    
    if not skill_levels:
        return {
            'score': 50,
            'required_level': required_level,
            'average_level': 'unknown'
        }
    
    # Weighted average (give more weight to highly matched skills)
    weighted_levels = []
    for i, (cv_skill, jd_skill, match_score, _) in enumerate(matching_result['matched'][:15]):
        level = skill_levels[i] if i < len(skill_levels) else 70
        weighted_levels.append(level * match_score)
    
    avg_level = sum(weighted_levels) / len(weighted_levels) if weighted_levels else 70
    
    # Calculate alignment score
    if avg_level >= required_score:
        # Perfect or over-qualified
        seniority_score = min(100, int((avg_level / required_score) * 100))
    else:
        # Under-qualified - steeper penalty
        seniority_score = int((avg_level / required_score) * 85)
    
    # Determine level name
    if avg_level >= 90:
        avg_level_name = 'senior/expert'
    elif avg_level >= 75:
        avg_level_name = 'mid-senior'
    elif avg_level >= 60:
        avg_level_name = 'mid'
    else:
        avg_level_name = 'junior'
    
    return {
        'score': seniority_score,
        'required_level': required_level,
        'average_level': avg_level_name,
        'avg_skill_level': round(avg_level, 1)
    }


def _calculate_semantic_relevance_score(cv_text, jd_text):
    """Enhanced semantic relevance"""
    similarity = _semantic_text_similarity(cv_text, jd_text)
    
    # Boost score if similarity is high
    if similarity > 0.8:
        boosted = similarity * 1.1
    elif similarity > 0.6:
        boosted = similarity * 1.05
    else:
        boosted = similarity
    
    relevance_score = int(min(100, boosted * 100))
    
    return {
        'score': relevance_score,
        'similarity': round(similarity, 3)
    }


def _calculate_bonus_score(cv_skills, matching_result, jd_text):
    """Enhanced bonus với role-specific evaluation"""
    extra_cv = matching_result['extra_cv']
    
    # Detect role from JD
    jd_lower = jd_text.lower()
    detected_role = 'general'
    
    for role in ROLE_CRITICAL_SKILLS.keys():
        if role in jd_lower:
            detected_role = role
            break
    
    bonus_points = 0
    bonus_skills = []
    penalty_points = 0
    
    # High-value skills (universally good)
    universal_high_value = [
        'docker', 'kubernetes', 'aws', 'microservices', 'ci/cd', 
        'terraform', 'graphql', 'redis', 'elasticsearch', 'git'
    ]
    
    # Check extra skills
    for skill in extra_cv:
        skill_norm = _normalize_skill(skill)
        
        # Universal high-value skills
        if skill_norm in universal_high_value:
            bonus_points += 8
            bonus_skills.append(skill)
        
        # Role-specific bonus
        elif detected_role in ROLE_CRITICAL_SKILLS:
            role_keywords = ROLE_CRITICAL_SKILLS[detected_role]
            if any(keyword in skill_norm for keyword in role_keywords):
                bonus_points += 5
                bonus_skills.append(skill)
        
        # Related to matched skills (ecosystem bonus)
        for cv_matched, jd_matched, _, _ in matching_result['matched']:
            if skill_norm in SKILL_GROUPS.get(jd_matched, []):
                bonus_points += 3
                if skill not in bonus_skills:
                    bonus_skills.append(skill)
                break
    
    # Check for skill spam (too many irrelevant skills)
    if len(cv_skills) > 30:
        spam_ratio = len(extra_cv) / len(cv_skills)
        if spam_ratio > 0.5:  # More than 50% skills are irrelevant
            penalty_points = 10
    
    # Calculate final score
    bonus_score = min(100, max(40, 60 + bonus_points - penalty_points))
    
    return {
        'score': bonus_score,
        'bonus_skills': bonus_skills[:8],
        'bonus_points': bonus_points,
        'penalty': penalty_points
    }


# ============= MAIN SCORING FUNCTION =============

def score_technical_skills(cv_data, jd_data, max_score=100, weights=None):
    """
    Enhanced: Chấm điểm Technical Skills với độ chính xác cao
    
    Args:
        cv_data (dict): Thông tin CV
        jd_data (dict/str): Thông tin JD
        max_score (int): Điểm tối đa
        weights (dict): Trọng số tùy chỉnh
    
    Returns:
        dict: Kết quả chi tiết với nhiều metrics
    """
    
    # Default weights
    if weights is None:
        weights = {
            'coverage': 0.30,
            'priority': 0.25,
            'seniority': 0.20,
            'relevance': 0.15,
            'bonus': 0.10
        }
    
    # Validate weights
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Tổng weights phải bằng 1.0, hiện tại: {total_weight}")
    
    # ===== Extract CV skills with aggressive mode =====
    cv_skills = []
    
    hard_skills = cv_data.get('hard_skills', '')
    if isinstance(hard_skills, list):
        cv_skills.extend(hard_skills)
    else:
        cv_skills.extend(_extract_skills_from_text(str(hard_skills), aggressive=True))
    
    tools = cv_data.get('tools', '')
    if tools and tools != 'n/a':
        cv_skills.extend(_extract_skills_from_text(str(tools), aggressive=True))
    
    # Extract from experience with aggressive mode
    experience = cv_data.get('experience', '')
    if experience and experience != 'n/a':
        exp_skills = _extract_skills_from_text(str(experience), aggressive=True)
        # Only add if it's a known technical skill
        cv_skills.extend([s for s in exp_skills if _get_skill_category(s) != 'other'])
    
    # Remove duplicates
    cv_skills = list(set([_normalize_skill(s) for s in cv_skills if s]))
    
    # ===== Extract JD skills =====
    jd_text = ''
    jd_skills = []
    
    if isinstance(jd_data, dict):
        jd_text = ' '.join([
            str(jd_data.get('title', '')),
            str(jd_data.get('requirements', '')),
            str(jd_data.get('skills', '')),
            str(jd_data.get('description', ''))
        ])
        jd_skills = _extract_skills_from_text(jd_text, aggressive=True)
    else:
        jd_text = str(jd_data)
        jd_skills = _extract_skills_from_text(jd_text, aggressive=True)
    
    jd_skills = list(set([_normalize_skill(s) for s in jd_skills if s]))
    
    # Prepare CV full text
    cv_text = ' '.join([
        str(cv_data.get('position', '')),
        str(cv_data.get('hard_skills', '')),
        str(cv_data.get('experience', '')),
        str(cv_data.get('tools', '')),
        str(cv_data.get('cv_summary', ''))
    ])
    
    # ===== CORE: Enhanced Semantic Matching =====
    matching_result = _semantic_skill_matching(cv_skills, jd_skills, threshold=0.65)
    
    # ===== Calculate All Scores =====
    coverage_result = _calculate_coverage_score(cv_skills, jd_skills, matching_result)
    priority_result = _calculate_priority_score(matching_result, jd_text)
    seniority_result = _calculate_seniority_score(cv_data, jd_text, cv_skills, matching_result)
    relevance_result = _calculate_semantic_relevance_score(cv_text, jd_text)
    bonus_result = _calculate_bonus_score(cv_skills, matching_result, jd_text)
    
    # ===== Calculate Total Score =====
    total_score_100 = (
        coverage_result['score'] * weights['coverage'] +
        priority_result['score'] * weights['priority'] +
        seniority_result['score'] * weights['seniority'] +
        relevance_result['score'] * weights['relevance'] +
        bonus_result['score'] * weights['bonus']
    )
    
    # Scale to max_score
    total_score = round((total_score_100 / 100) * max_score, 2)
    
    # ===== Prepare Enhanced Summary =====
    matched_skills = [jd_skill for _, jd_skill, _, _ in matching_result['matched']]
    missing_skills = matching_result['unmatched_jd']
    extra_skills = matching_result['extra_cv'][:8]
    
    # Calculate match statistics
    match_rate = len(matched_skills) / len(jd_skills) * 100 if jd_skills else 0
    
    # Count match types
    exact_matches = sum(1 for _, _, _, rel in matching_result['matched'] if rel == 'exact')
    related_matches = sum(1 for _, _, _, rel in matching_result['matched'] if rel in ['related', 'same_group'])
    
    # Generate detailed description
    details = f"Ứng viên match {len(matched_skills)}/{len(jd_skills)} skills ({match_rate:.0f}%). "
    
    if exact_matches > 0:
        details += f"{exact_matches} exact matches. "
    if related_matches > 0:
        details += f"{related_matches} related skills. "
    
    if match_rate >= 85:
        details += "Kỹ năng xuất sắc, rất phù hợp. "
    elif match_rate >= 70:
        details += "Kỹ năng tốt, phù hợp cao. "
    elif match_rate >= 50:
        details += "Kỹ năng khá, cần đánh giá thêm. "
    else:
        details += "Kỹ năng chưa đủ yêu cầu. "
    
    if priority_result['missing_critical']:
        critical_missing = priority_result['missing_critical']
        details += f"Thiếu {len(critical_missing)} skills quan trọng: {', '.join(critical_missing[:3])}. "
    
    if seniority_result['average_level'] != seniority_result['required_level']:
        details += f"Level {seniority_result['average_level']} (yêu cầu {seniority_result['required_level']}). "
    
    if bonus_result['bonus_skills']:
        details += f"Có {len(bonus_result['bonus_skills'])} skills bonus."
    
    return {
        'total_score': total_score,
        'max_score': max_score,
        'breakdown': {
            'coverage': {
                'score': round((coverage_result['score'] / 100) * max_score * weights['coverage'], 2),
                'weight': weights['coverage'],
                'raw_score': coverage_result['score'],
                'details': coverage_result
            },
            'priority': {
                'score': round((priority_result['score'] / 100) * max_score * weights['priority'], 2),
                'weight': weights['priority'],
                'raw_score': priority_result['score'],
                'details': priority_result
            },
            'seniority': {
                'score': round((seniority_result['score'] / 100) * max_score * weights['seniority'], 2),
                'weight': weights['seniority'],
                'raw_score': seniority_result['score'],
                'details': seniority_result
            },
            'relevance': {
                'score': round((relevance_result['score'] / 100) * max_score * weights['relevance'], 2),
                'weight': weights['relevance'],
                'raw_score': relevance_result['score'],
                'details': relevance_result
            },
            'bonus': {
                'score': round((bonus_result['score'] / 100) * max_score * weights['bonus'], 2),
                'weight': weights['bonus'],
                'raw_score': bonus_result['score'],
                'details': bonus_result
            }
        },
        'summary': {
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'extra_skills': extra_skills,
            'match_rate': round(match_rate, 1),
            'exact_matches': exact_matches,
            'related_matches': related_matches,
            'total_cv_skills': len(cv_skills),
            'total_jd_skills': len(jd_skills)
        },
        'details': details
    }
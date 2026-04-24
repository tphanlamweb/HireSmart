# """
# Job Management Routes
# Xử lý tất cả API endpoints liên quan đến tuyển dụng/công việc
# """

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy import MetaData, select, insert, update
# from sqlalchemy.orm import Session
# from pydantic import BaseModel
# from typing import List, Optional
# from datetime import datetime
# from decimal import Decimal

# from backend.dataAndModels.config import DATABASE_URL, engine, get_db

# # Setup database
# metadata = MetaData()
# metadata.reflect(bind=engine)

# router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# # ============================================================================
# # PYDANTIC MODELS (Request/Response schemas)
# # ============================================================================

# class RequirementInput(BaseModel):
#     """Yêu cầu công việc"""
#     title: str
#     description: Optional[str] = None

# class JobCreateRequest(BaseModel):
#     """Request body khi tạo job mới"""
#     job_title: str
#     category_id: int
#     location: str
#     employment_type: Optional[str] = "Full-time"
#     salary: str  # Format: "100k" hoặc "100-200k"
#     is_active: bool = True
#     positions_open: Optional[int] = 1
#     application_deadline: Optional[str] = None
#     requirements: List[str]  # Danh sách tiêu đề requirements
#     custom_requirements: List[str] = []  # Yêu cầu tùy chỉnh

# class JobResponse(BaseModel):
#     """Response khi lấy job"""
#     id: int
#     job_title: str
#     category_id: int
#     location: str
#     employment_type: str
#     salary_min: Optional[Decimal]
#     salary_max: Optional[Decimal]
#     is_active: int
#     positions_open: int
#     current_applications: int
#     created_at: Optional[str]

# # ============================================================================
# # HELPER FUNCTIONS
# # ============================================================================

# def parse_salary(salary_str: str) -> tuple:
#     """
#     Parse salary string thành (min, max)
#     Examples: "100k" -> (100000, 100000)
#               "100-200k" -> (100000, 200000)
#               "100-200" -> (100, 200)
#     """
#     salary_str = salary_str.strip().lower().replace(',', '')
    
#     if '-' in salary_str:
#         parts = salary_str.split('-')
#         min_val = float(parts[0].replace('k', '')) * (1000 if 'k' in parts[0] else 1)
#         max_val = float(parts[1].replace('k', '')) * (1000 if 'k' in parts[1] else 1)
#         return Decimal(str(min_val)), Decimal(str(max_val))
#     else:
#         val = float(salary_str.replace('k', '')) * (1000 if 'k' in salary_str else 1)
#         return Decimal(str(val)), Decimal(str(val))

# def get_user_id_from_request() -> int:
#     """
#     Lấy user_id từ session/request
#     TODO: Cần kết nối với authentication system
#     Hiện tại dùng hardcode user_id = 1
#     """
#     return 1

# # ============================================================================
# # API ENDPOINTS
# # ============================================================================

# @router.post("/create")
# def create_job(
#     job_data: JobCreateRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Tạo job description mới
    
#     Flow:
#     1. Insert vào JOB_DESCRIPTIONS
#     2. Insert vào REQUIREMENT_FOR_JOB (cho mỗi requirement)
#     3. Return job_id
#     """
#     try:
#         # Get tables
#         job_descriptions = metadata.tables["job_descriptions"]
#         requirement_for_job = metadata.tables["Requirement_for_job"]
        
#         # Parse salary
#         salary_min, salary_max = parse_salary(job_data.salary)
        
#         # Prepare job data
#         user_id = get_user_id_from_request()
        
#         job_insert = insert(job_descriptions).values(
#             job_title=job_data.job_title,
#             category_id=job_data.category_id,
#             location=job_data.location,
#             employment_type=job_data.employment_type,
#             salary_min=salary_min,
#             salary_max=salary_max,
#             currency="VND",
#             is_active=1 if job_data.is_active else 0,
#             created_by=user_id,
#             positions_open=job_data.positions_open,
#             current_applications=0,
#             created_at=datetime.now()
#         )
        
#         # Execute insert
#         result = db.execute(job_insert)
#         job_id = result.lastrowid
        
#         # Insert requirements
#         all_requirements = job_data.requirements + job_data.custom_requirements
        
#         for req_title in all_requirements:
#             if req_title.strip():  # Skip empty
#                 req_insert = insert(requirement_for_job).values(
#                     job_categories_id=job_data.category_id,
#                     title=req_title.strip(),
#                     description=req_title.strip(),
#                     created_at=datetime.now()
#                 )
#                 db.execute(req_insert)
        
#         db.commit()
        
#         return {
#             "status": "success",
#             "message": f"Job '{job_data.job_title}' created successfully",
#             "job_id": job_id,
#             "requirements_count": len(all_requirements)
#         }
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error creating job: {str(e)}"
#         )

# @router.get("")
# def get_all_jobs(
#     active_only: bool = True,
#     db: Session = Depends(get_db)
# ):
#     """
#     Lấy danh sách tất cả jobs
    
#     Query params:
#     - active_only: True = chỉ lấy jobs đang mở (is_active=1)
#     """
#     try:
#         job_descriptions = metadata.tables["job_descriptions"]
#         job_categories = metadata.tables["job_categories"]
        
#         # Build query
#         query = select(
#             job_descriptions.c.id,
#             job_descriptions.c.job_title,
#             job_descriptions.c.category_id,
#             job_descriptions.c.location,
#             job_descriptions.c.employment_type,
#             job_descriptions.c.salary_min,
#             job_descriptions.c.salary_max,
#             job_descriptions.c.currency,
#             job_descriptions.c.application_deadline,
#             job_descriptions.c.positions_open,
#             job_descriptions.c.current_applications,
#             job_categories.c.category_name
#         ).select_from(
#             job_descriptions
#         ).outerjoin(
#             job_categories,
#             job_descriptions.c.category_id == job_categories.c.id
#         )
        
#         if active_only:
#             query = query.where(job_descriptions.c.is_active == 1)
        
#         with engine.connect() as conn:
#             result = conn.execute(query).fetchall()
        
#         jobs = []
#         for row in result:
#             jobs.append({
#                 "id": row[0],
#                 "job_title": row[1],
#                 "category_id": row[2],
#                 "location": row[3],
#                 "employment_type": row[4],
#                 "salary_min": float(row[5]) if row[5] else None,
#                 "salary_max": float(row[6]) if row[6] else None,
#                 "currency": row[7] or "VND",
#                 "application_deadline": str(row[8]) if row[8] else None,
#                 "positions_open": row[9],
#                 "current_applications": row[10],
#                 "category_name": row[11]
#             })
        
#         return {
#             "status": "success",
#             "count": len(jobs),
#             "data": jobs
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching jobs: {str(e)}"
#         )

# @router.get("/{job_id}")
# def get_job_detail(
#     job_id: int,
#     db: Session = Depends(get_db)
# ):
#     """
#     Lấy chi tiết 1 job kèm danh sách requirements
#     """
#     try:
#         job_descriptions = metadata.tables["job_descriptions"]
#         requirement_for_job = metadata.tables["Requirement_for_job"]
#         job_categories = metadata.tables["job_categories"]
#         information_for_job = metadata.tables["Information_for_job"]
#         job_description_info = metadata.tables["job_description_info"]
        
#         with engine.connect() as conn:
#             # Get job details
#             job_query = select(
#                 job_descriptions.c.id,
#                 job_descriptions.c.job_title,
#                 job_descriptions.c.location,
#                 job_descriptions.c.employment_type,
#                 job_descriptions.c.salary_min,
#                 job_descriptions.c.salary_max,
#                 job_descriptions.c.currency,
#                 job_descriptions.c.application_deadline,
#                 job_descriptions.c.positions_open,
#                 job_descriptions.c.current_applications,
#                 job_descriptions.c.view_count,
#                 job_categories.c.category_name
#             ).select_from(
#                 job_descriptions
#             ).outerjoin(
#                 job_categories,
#                 job_descriptions.c.category_id == job_categories.c.id
#             ).where(
#                 job_descriptions.c.id == job_id
#             )
            
#             job_row = conn.execute(job_query).fetchone()
            
#             if not job_row:
#                 raise HTTPException(status_code=404, detail="Job not found")
            
#             # Get job description info (only for this job)
#             info_query = select(
#                 information_for_job.c.Info_title,
#                 information_for_job.c.Info_description,
#                 information_for_job.c.section,
#                 job_description_info.c.sort_order
#             ).select_from(
#                 information_for_job
#             ).join(
#                 job_description_info,
#                 information_for_job.c.id == job_description_info.c.info_id
#             ).where(
#                 job_description_info.c.jd_id == job_id
#             ).order_by(
#                 job_description_info.c.sort_order.asc(),
#                 information_for_job.c.priority.desc()
#             )
            
#             info_rows = conn.execute(info_query).fetchall()
            
#             job_info = {}
#             for row in info_rows:
#                 section = row[2]
#                 if section not in job_info:
#                     job_info[section] = []
#                 job_info[section].append({
#                     "title": row[0],
#                     "description": row[1]
#                 })
            
#             # Get requirements
#             req_query = select(
#                 requirement_for_job.c.id,
#                 requirement_for_job.c.title,
#                 requirement_for_job.c.description
#             ).where(
#                 requirement_for_job.c.job_categories_id == job_row[2]
#             ).order_by(
#                 requirement_for_job.c.priority.desc(),
#                 requirement_for_job.c.id.asc()
#             )
            
#             req_rows = conn.execute(req_query).fetchall()
        
#         requirements = [
#             {
#                 "id": r[0],
#                 "title": r[1],
#                 "description": r[2]
#             }
#             for r in req_rows
#         ]
        
#         return {
#             "status": "success",
#             "data": {
#                 "id": job_row[0],
#                 "job_title": job_row[1],
#                 "location": job_row[2],
#                 "employment_type": job_row[3],
#                 "salary_min": float(job_row[4]) if job_row[4] else None,
#                 "salary_max": float(job_row[5]) if job_row[5] else None,
#                 "currency": job_row[6] or "VND",
#                 "application_deadline": str(job_row[7]) if job_row[7] else None,
#                 "positions_open": job_row[8],
#                 "current_applications": job_row[9],
#                 "view_count": job_row[10],
#                 "category_name": job_row[11],
#                 "job_info": job_info,
#                 "requirements": requirements
#             }
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching job details: {str(e)}"
#         )

# @router.get("/categories/list")
# def get_categories(db: Session = Depends(get_db)):
#     """
#     Lấy danh sách tất cả job categories
#     Dùng cho dropdown trong form Create Job
#     """
#     try:
#         job_categories = metadata.tables["job_categories"]
        
#         query = select(
#             job_categories.c.id,
#             job_categories.c.category_name,
#             job_categories.c.description
#         ).where(
#             job_categories.c.is_active == 1
#         )
        
#         with engine.connect() as conn:
#             result = conn.execute(query).fetchall()
        
#         categories = [
#             {
#                 "id": r[0],
#                 "name": r[1],
#                 "description": r[2]
#             }
#             for r in result
#         ]
        
#         return {
#             "status": "success",
#             "data": categories
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Error fetching categories: {str(e)}"
#         )
"""
Job Management Routes
Xử lý tất cả API endpoints liên quan đến tuyển dụng/công việc

IMPROVEMENTS:
- Sử dụng job_description_info để lấy info theo job cụ thể
- Thêm sort theo priority cho requirements
- Loại bỏ fields không cần thiết
- Thêm error handling tốt hơn
- Thêm logging
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import MetaData, select, insert, update, func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import logging

from backend.dataAndModels.config import DATABASE_URL, engine, get_db, SessionLocal

# Setup logging
logger = logging.getLogger(__name__)

# Setup database
metadata = MetaData()
metadata.reflect(bind=engine)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# ============================================================================
# PYDANTIC MODELS (Request/Response schemas)
# ============================================================================

class RequirementInput(BaseModel):
    """Yêu cầu công việc"""
    title: str
    description: Optional[str] = None
    priority: Optional[int] = 0

class JobCreateRequest(BaseModel):
    """Request body khi tạo job mới"""
    job_title: str = Field(..., min_length=1, max_length=255)
    category_id: int = Field(..., gt=0)
    location: str = Field(..., min_length=1)
    employment_type: Optional[str] = "Full-time"
    salary: str  # Format: "100k" hoặc "100-200k"
    is_active: bool = True
    positions_open: Optional[int] = Field(default=1, gt=0)
    application_deadline: Optional[str] = None
    requirements: List[str] = []  # IDs của requirements có sẵn
    custom_requirements: List[str] = []  # Yêu cầu tùy chỉnh
    info_blocks: List[int] = []  # IDs của Information_for_job để gán cho job này

class JobResponse(BaseModel):
    """Response khi lấy job"""
    id: int
    job_title: str
    location: str
    employment_type: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    currency: str
    positions_open: int
    current_applications: int
    application_deadline: Optional[str]
    category_name: str

class JobDetailResponse(BaseModel):
    """Response chi tiết job"""
    id: int
    job_title: str
    location: str
    employment_type: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    currency: str
    positions_open: int
    current_applications: int
    application_deadline: Optional[str]
    category_name: str
    category_id: int
    created_by_name: Optional[str]
    job_info: Dict[str, List[Dict[str, str]]]
    requirements: List[Dict[str, Any]]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_salary(salary_str: str) -> tuple:
    """
    Parse salary string thành (min, max)
    Examples: "100k" -> (100000, 100000)
              "100-200k" -> (100000, 200000)
              "100-200" -> (100, 200)
    """
    try:
        salary_str = salary_str.strip().lower().replace(',', '')
        
        if '-' in salary_str:
            parts = salary_str.split('-')
            min_val = float(parts[0].replace('k', '')) * (1000 if 'k' in parts[0] else 1)
            max_val = float(parts[1].replace('k', '')) * (1000 if 'k' in parts[1] else 1)
            return Decimal(str(min_val)), Decimal(str(max_val))
        else:
            val = float(salary_str.replace('k', '')) * (1000 if 'k' in salary_str else 1)
            return Decimal(str(val)), Decimal(str(val))
    except Exception as e:
        logger.error(f"Error parsing salary '{salary_str}': {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid salary format: {salary_str}. Use format like '100k' or '100-200k'"
        )


def build_jd_full_from_db(job_id: int, db: Session | None = None) -> Dict[str, Any]:
    """
    Fetch a job description (JD) and related info blocks/requirements from the DB
    and assemble a dict that follows the `jd_full` sample structure used by
    `candidates_CV_Scoring.py`.

    Behaviour / mapping rules:
    - Info blocks linked to the JD via `job_description_info` are grouped by
      their `section` value (lowercased) and concatenated.
    - Category-level `Requirement_for_job` entries are used as fallbacks for
      technical skills / tools when no info blocks exist.
    - The function returns a dictionary with keys: `certificates`,
      `experiences`, `technical_skills`, `soft_skills`, `tools_and_certificates`,
      `similarity`.
    """
    job_descriptions = metadata.tables.get("job_descriptions")
    information_for_job = metadata.tables.get("information_for_job")
    job_description_info = metadata.tables.get("job_description_info")
    requirement_for_job = metadata.tables.get("requirement_for_job")

    if job_descriptions is None:
        raise HTTPException(status_code=500, detail="job_descriptions table missing")

    # If no job_id provided, return a minimal jd_full so scoring can proceed
    if not job_id:
        return {
            "certificates": "",
            "experiences": "",
            "technical_skills": {"title": "", "requirements": "", "skills": ""},
            "soft_skills": "",
            "tools_and_certificates": {"requirements": ""},
            "similarity": {"title": "", "requirements": ""},
        }

    # Ensure we have a DB session; create local if needed
    created_local = False
    if db is None:
        db = SessionLocal()
        created_local = True

    try:
        # Load job row
        job_row = db.execute(
        select(
            job_descriptions.c.id,
            job_descriptions.c.job_title,
            job_descriptions.c.category_id,
            job_descriptions.c.location,
            job_descriptions.c.employment_type,
        ).where(job_descriptions.c.id == job_id)
        ).fetchone()

        if not job_row:
            raise HTTPException(status_code=404, detail=f"Job description {job_id} not found")

        # Fetch linked info blocks (if job_description_info exists)
        if information_for_job is None:
            info_rows = []
        else:
            if job_description_info is not None:
                info_query = (
                    select(
                        information_for_job.c.Info_title,
                        information_for_job.c.Info_description,
                        information_for_job.c.section,
                    )
                    .select_from(
                        information_for_job.join(
                            job_description_info, information_for_job.c.id == job_description_info.c.info_id
                        )
                    )
                    .where(job_description_info.c.jd_id == job_id)
                    .order_by(job_description_info.c.sort_order.asc())
                )
            else:
                info_query = (
                    select(
                        information_for_job.c.Info_title,
                        information_for_job.c.Info_description,
                        information_for_job.c.section,
                    )
                    .order_by(information_for_job.c.priority.desc())
                    .limit(50)
                )

            info_rows = db.execute(info_query).fetchall()

        # Group info blocks by section
        from collections import defaultdict

        sections = defaultdict(list)
        for row in info_rows:
            title = (row[0] or "").strip()
            desc = (row[1] or "").strip()
            section = (row[2] or "").strip().lower()
            sections[section].append({"title": title, "description": desc})

        # Fetch category requirements (fallback)
        category_reqs = []
        if requirement_for_job is not None and job_row.category_id is not None:
            req_q = select(requirement_for_job.c.title, requirement_for_job.c.description).where(
                requirement_for_job.c.job_categories_id == job_row.category_id
            ).order_by(requirement_for_job.c.id.asc())
            req_rows = db.execute(req_q).fetchall()
            for r in req_rows:
                category_reqs.append({"title": (r[0] or "").strip(), "description": (r[1] or "").strip()})

        def join_items(list_of_items):
            parts = []
            for it in list_of_items:
                if it.get("description"):
                    parts.append(f"{it.get('title')}: {it.get('description')}")
                else:
                    parts.append(it.get("title"))
            return "\n".join(parts).strip()

        # Build fields using available data (prefer linked info blocks, else fallbacks)
        certificates = "\n".join(
            [f"{i['title']}: {i['description']}" if i['description'] else i['title'] for i in sections.get("certificates", [])]
        ).strip()

        experiences = join_items(sections.get("experiences", []) or sections.get("experience", []))

        soft_skills = join_items(sections.get("soft_skills", []) or sections.get("personal_skills", []))

        # Tools and certificates combined
        tools_section = sections.get("tools", []) + sections.get("tools_and_certificates", [])
        tools_and_certificates_text = join_items(tools_section) or certificates or join_items(category_reqs)

        # Technical skills: prefer explicit technical_skills section; otherwise fall back to category requirements
        tech_block = sections.get("technical_skills", [])
        if tech_block:
            tech_title = tech_block[0].get("title") or job_row.job_title
            tech_requirements = join_items(tech_block)
            tech_skills = " ".join([t.get("title") for t in tech_block if t.get("title")])
        else:
            tech_title = job_row.job_title
            # heuristically select technical-like req titles from category_reqs
            tech_candidates = [r for r in category_reqs if any(k in r.get("title", "").lower() for k in ("php","python","java","mysql","docker","aws","rest","api","laravel","react","skill"))]
            if not tech_candidates:
                tech_candidates = category_reqs
            tech_requirements = join_items(tech_candidates)
            tech_skills = " ".join([r.get("title") for r in tech_candidates])

        technical_skills = {
            "title": tech_title,
            "requirements": tech_requirements,
            "skills": tech_skills,
        }

        similarity = {"title": technical_skills["title"], "requirements": technical_skills["requirements"]}

        jd_full = {
            "certificates": certificates or tools_and_certificates_text or "",
            "experiences": experiences or "",
            "technical_skills": technical_skills,
            "soft_skills": soft_skills or "",
            "tools_and_certificates": {"requirements": tools_and_certificates_text},
            "similarity": similarity,
        }
        return jd_full
    finally:
        if created_local:
            try:
                db.close()
            except Exception:
                pass

def get_user_id_from_request() -> int:
    """
    Lấy user_id từ session/request
    TODO: Cần kết nối với authentication system
    Hiện tại dùng hardcode user_id = 1
    """
    return 1

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/create")
def create_job(
    job_data: JobCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Tạo job description mới
    
    Flow:
    1. Insert vào job_descriptions
    2. Insert vào Requirement_for_job (nếu có custom requirements)
    3. Insert vào job_description_info (liên kết info blocks)
    4. Return job_id
    
    IMPROVED:
    - Validation tốt hơn
    - Link với info blocks qua job_description_info
    - Transaction handling
    """
    try:
        # Get tables
        job_descriptions = metadata.tables["job_descriptions"]
        requirement_for_job = metadata.tables["Requirement_for_job"]
        job_description_info = metadata.tables.get("job_description_info")
        
        # Parse salary
        salary_min, salary_max = parse_salary(job_data.salary)
        
        # Prepare job data
        user_id = get_user_id_from_request()
        
        job_insert = insert(job_descriptions).values(
            job_title=job_data.job_title,
            category_id=job_data.category_id,
            location=job_data.location,
            employment_type=job_data.employment_type,
            salary_min=salary_min,
            salary_max=salary_max,
            currency="VND",
            is_active=1 if job_data.is_active else 0,
            created_by=user_id,
            positions_open=job_data.positions_open,
            current_applications=0,
            application_deadline=job_data.application_deadline,
            created_at=datetime.now()
        )
        
        # Execute insert
        result = db.execute(job_insert)
        job_id = result.lastrowid
        
        logger.info(f"Created job {job_id}: {job_data.job_title}")
        
        # Insert custom requirements (nếu có)
        custom_req_count = 0
        if job_data.custom_requirements:
            for req_title in job_data.custom_requirements:
                if req_title.strip():
                    req_insert = insert(requirement_for_job).values(
                        job_categories_id=job_data.category_id,
                        title=req_title.strip(),
                        description=req_title.strip(),
                        priority=0,  # Custom requirements có priority thấp
                        created_at=datetime.now()
                    )
                    db.execute(req_insert)
                    custom_req_count += 1
        
        # Link info blocks (nếu có bảng job_description_info)
        info_linked_count = 0
        if job_description_info is not None and job_data.info_blocks:
            for idx, info_id in enumerate(job_data.info_blocks):
                info_link = insert(job_description_info).values(
                    jd_id=job_id,
                    info_id=info_id,
                    sort_order=idx + 1
                )
                db.execute(info_link)
                info_linked_count += 1
        
        db.commit()
        
        return {
            "status": "success",
            "message": f"Job '{job_data.job_title}' created successfully",
            "data": {
                "job_id": job_id,
                "custom_requirements_added": custom_req_count,
                "info_blocks_linked": info_linked_count
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating job: {str(e)}"
        )

@router.get("", response_model=dict)
def get_all_jobs(
    active_only: bool = True,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách tất cả jobs
    
    Query params:
    - active_only: True = chỉ lấy jobs đang mở (is_active=1)
    - category_id: Lọc theo category (optional)
    
    IMPROVED:
    - Loại bỏ fields không cần thiết (is_active, created_at)
    - Thêm filter theo category
    - Thêm currency
    """
    try:
        job_descriptions = metadata.tables["job_descriptions"]
        job_categories = metadata.tables["job_categories"]
        
        # Build query - CHỈ LẤY FIELDS CẦN THIẾT
        query = select(
            job_descriptions.c.id,
            job_descriptions.c.job_title,
            job_descriptions.c.location,
            job_descriptions.c.employment_type,
            job_descriptions.c.salary_min,
            job_descriptions.c.salary_max,
            job_descriptions.c.currency,
            job_descriptions.c.positions_open,
            job_descriptions.c.current_applications,
            job_descriptions.c.application_deadline,
            job_categories.c.category_name
        ).select_from(
            job_descriptions
        ).outerjoin(
            job_categories,
            job_descriptions.c.category_id == job_categories.c.id
        )
        
        # Apply filters
        if active_only:
            query = query.where(job_descriptions.c.is_active == 1)
        
        if category_id:
            query = query.where(job_descriptions.c.category_id == category_id)
        
        # Order by newest first
        query = query.order_by(job_descriptions.c.created_at.desc())
        
        with engine.connect() as conn:
            result = conn.execute(query).fetchall()
        
        jobs = []
        for row in result:
            jobs.append({
                "id": row[0],
                "job_title": row[1],
                "location": row[2],
                "employment_type": row[3],
                "salary_min": float(row[4]) if row[4] else None,
                "salary_max": float(row[5]) if row[5] else None,
                "currency": row[6] if row[6] else "VND",
                "positions_open": row[7],
                "current_applications": row[8],
                "application_deadline": str(row[9]) if row[9] else None,
                "category_name": row[10]
            })
        
        return {
            "status": "success",
            "count": len(jobs),
            "data": jobs
        }
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching jobs: {str(e)}"
        )




@router.get("/{job_id}")
def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db)
):
    try:
        # ===== LOAD TABLES (SAFE) =====
        job_descriptions = metadata.tables.get("job_descriptions")
        job_categories = metadata.tables.get("job_categories")
        requirement_for_job = metadata.tables.get("Requirement_for_job")
        information_for_job = metadata.tables.get("Information_for_job")
        users = metadata.tables.get("users")
        job_description_info = metadata.tables.get("job_description_info")

        if (
            job_descriptions is None
            or job_categories is None
            or requirement_for_job is None
            or information_for_job is None
            or users is None
        ):
            raise HTTPException(
                status_code=500,
                detail="Database table mapping error"
            )
            

        # ===== QUERY 1: JOB DETAIL =====
        job_query = (
            select(
                job_descriptions.c.id,
                job_descriptions.c.job_title,
                job_descriptions.c.category_id,
                job_descriptions.c.location,
                job_descriptions.c.employment_type,
                job_descriptions.c.salary_min,
                job_descriptions.c.salary_max,
                job_descriptions.c.currency,
                job_descriptions.c.positions_open,
                job_descriptions.c.current_applications,
                job_descriptions.c.application_deadline,
                job_categories.c.category_name,
                users.c.full_name.label("created_by_name")
            )
            .select_from(job_descriptions)
            .outerjoin(
                job_categories,
                job_descriptions.c.category_id == job_categories.c.id
            )
            .outerjoin(
                users,
                job_descriptions.c.created_by == users.c.id
            )
            .where(
                job_descriptions.c.id == job_id,
                job_descriptions.c.is_active == 1  # ✅ FIX HERE
            )
        )
        job_row = db.execute(job_query).fetchone()

        if not job_row:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Job not found",
                    "job_id": job_id
                }
            )

        # ===== QUERY 2: INFO BLOCKS =====
        job_info = {}

        if job_description_info is not None:
            info_query = (
                select(
                    information_for_job.c.Info_title,
                    information_for_job.c.Info_description,
                    information_for_job.c.section
                )
                .select_from(information_for_job)
                .join(
                    job_description_info,
                    information_for_job.c.id == job_description_info.c.info_id
                )
                .where(
                    job_description_info.c.jd_id == job_id
                )
                .order_by(
                    job_description_info.c.sort_order.asc()
                )
            )
        else:
            info_query = (
                select(
                    information_for_job.c.Info_title,
                    information_for_job.c.Info_description,
                    information_for_job.c.section
                )
                .order_by(
                    information_for_job.c.section.asc()
                )
            )

        info_rows = db.execute(info_query).fetchall()

        for row in info_rows:
            section = row.section
            if section == "requirements":
                section = "responsibilities"

            job_info.setdefault(section, []).append({
                "title": row.Info_title,
                "description": row.Info_description
            })

        # ===== QUERY 3: REQUIREMENTS (BY CATEGORY) =====
        req_query = (
            select(
                requirement_for_job.c.id,
                requirement_for_job.c.title,
                requirement_for_job.c.description
            )
            .where(
                requirement_for_job.c.job_categories_id == job_row.category_id
            )
            .order_by(
                requirement_for_job.c.id.asc()
            )
        )

        req_rows = db.execute(req_query).fetchall()

        requirements = [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description
            }
            for r in req_rows
        ]

        # ===== BUILD RESPONSE =====
        return {
            "status": "success",
            "data": {
                "id": job_row.id,
                "job_title": job_row.job_title,
                "category_id": job_row.category_id,
                "location": job_row.location,
                "employment_type": job_row.employment_type,
                "salary_min": float(job_row.salary_min) if job_row.salary_min else None,
                "salary_max": float(job_row.salary_max) if job_row.salary_max else None,
                "currency": job_row.currency or "VND",
                "positions_open": job_row.positions_open,
                "current_applications": job_row.current_applications,
                "application_deadline": str(job_row.application_deadline) if job_row.application_deadline else None,
                "category_name": job_row.category_name,
                "created_by_name": job_row.created_by_name,
                "job_info": job_info,
                "requirements": requirements
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Job detail error")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching job details: {str(e)}"
        )
        
        
        
        
        


@router.get("/categories/list")
def get_categories(db: Session = Depends(get_db)):
    """
    Lấy danh sách tất cả job categories
    Dùng cho dropdown trong form Create Job
    """
    try:
        job_categories = metadata.tables["job_categories"]
        
        query = select(
            job_categories.c.id,
            job_categories.c.category_name,
            job_categories.c.description
        ).where(
            job_categories.c.is_active == 1
        ).order_by(
            job_categories.c.category_name.asc()
        )
        
        with engine.connect() as conn:
            result = conn.execute(query).fetchall()
        
        categories = [
            {
                "id": r[0],
                "name": r[1],
                "description": r[2]
            }
            for r in result
        ]
        
        return {
            "status": "success",
            "count": len(categories),
            "data": categories
        }
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching categories: {str(e)}"
        )

@router.get("/requirements/by-category/{category_id}")
def get_requirements_by_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách requirements theo category
    Dùng cho form Create Job để hiển thị available requirements
    
    NEW ENDPOINT - giúp frontend load requirements khi chọn category
    """
    try:
        requirement_for_job = metadata.tables["Requirement_for_job"]
        
        query = select(
            requirement_for_job.c.id,
            requirement_for_job.c.title,
            requirement_for_job.c.description,
            requirement_for_job.c.priority
        ).where(
            requirement_for_job.c.job_categories_id == category_id
        ).order_by(
            requirement_for_job.c.priority.desc(),
            requirement_for_job.c.id.asc()
        )
        
        with engine.connect() as conn:
            result = conn.execute(query).fetchall()
        
        requirements = [
            {
                "id": r[0],
                "title": r[1],
                "description": r[2],
                "priority": r[3] if len(r) > 3 else 0
            }
            for r in result
        ]
        
        return {
            "status": "success",
            "count": len(requirements),
            "data": requirements
        }
        
    except Exception as e:
        logger.error(f"Error fetching requirements for category {category_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching requirements: {str(e)}"
        )

@router.patch("/{job_id}/increment-applications")
def increment_applications(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Tăng số lượng applications cho job
    Được gọi khi có candidate mới apply
    
    NEW ENDPOINT - tự động tăng current_applications
    """
    try:
        job_descriptions = metadata.tables["job_descriptions"]
        
        # Update
        update_query = (
            update(job_descriptions)
            .where(job_descriptions.c.id == job_id)
            .values(
                current_applications=job_descriptions.c.current_applications + 1
            )
        )
        
        result = db.execute(update_query)
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get updated count
        select_query = select(
            job_descriptions.c.current_applications
        ).where(
            job_descriptions.c.id == job_id
        )
        
        with engine.connect() as conn:
            new_count = conn.execute(select_query).scalar()
        
        return {
            "status": "success",
            "message": "Application count updated",
            "data": {
                "job_id": job_id,
                "current_applications": new_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error incrementing applications for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating application count: {str(e)}"
        )
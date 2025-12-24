from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session
from backend.dataAndModels.config import DATABASE_URL, engine , get_db, metadata
from backend.API.candidates_CV_Scoring import score_candidate
import re
import os
import base64
import logging
import traceback

from typing import Dict


metadata.reflect(bind=engine)

def extract_programming_languages(cv_or_text):
    # Accept dicts with common fields, else use the string directly
    if isinstance(cv_or_text, dict):
        text = " ".join(
            str(cv_or_text.get(k, "")) for k in
            ("technical_skills", "hard_skills", "experience", "cv_summary", "education")
        )
    else:
        text = str(cv_or_text)

    text = text.lower()

    patterns = {
        "python": r"\bpython\b",
        "java": r"\bjava\b",
        "javascript": r"\bjavascript\b|\bjs\b",
        "typescript": r"\btypescript\b",
        "c++": r"c\+\+",
        "c#": r"\bc#\b",
        "go": r"\bgo\b|\bgolang\b",
        "ruby": r"\bruby\b",
        "php": r"\bphp\b",
        "swift": r"\bswift\b",
        "kotlin": r"\bkotlin\b",
        "rust": r"\brust\b",
        "scala": r"\bscala\b",
        "perl": r"\bperl\b",
        "matlab": r"\bmatlab\b",
        "dart": r"\bdart\b",
        "lua": r"\blua\b",
        "sql": r"\bsql\b",
        "bash": r"\bbash\b|\bshell\b|\bsh\b",
        "powershell": r"\bpowershell\b",
        "html": r"\bhtml\b",
        "css": r"\bcss\b"
    }

    found = set()
    for name, patt in patterns.items():
        if re.search(patt, text):
            found.add(name)

    return sorted(found)

def extract_frameworks_and_libraries(cv_or_text):
    if isinstance(cv_or_text, dict):
        text = " ".join(
            str(cv_or_text.get(k, "")) for k in
            ("technical_skills", "hard_skills", "experience", "cv_summary", "education", "tools")
        )
    else:
        text = str(cv_or_text)

    text = text.lower()

    patterns = {
        "react": r"\breact\b",
        "vue": r"\bvue\b",
        "angular": r"\bangular\b",
        "svelte": r"\bsvelte\b",
        "ember": r"\bember\b",
        "backbone": r"\bbackbone\b",
        "next.js": r"\bnext(\.js)?\b",
        "nuxt.js": r"\bnuxt(\.js)?\b",
        "gatsby": r"\bgatsby\b",
        "redux": r"\bredux\b",
        "mobx": r"\bmobx\b",
        "django": r"\bdjango\b",
        "flask": r"\bflask\b",
        "fastapi": r"\bfastapi\b",
        "spring": r"\bspring\b",
        "spring boot": r"\bspring[-\s]?boot\b",
        "express": r"\bexpress\b",
        "laravel": r"\blaravel\b",
        "symfony": r"\bsymfony\b",
        "ruby on rails": r"\brails\b|\bruby on rails\b",
        "rails": r"\brails\b",
        "node.js": r"\bnode(?:\.js|js)?\b",
        "electron": r"\belectron\b",
        "tensorflow": r"\btensorflow\b",
        "pytorch": r"\bpytorch\b",
        "scikit-learn": r"\bscikit[-\s]?learn\b|\bsklearn\b",
        "keras": r"\bkeras\b",
        "pandas": r"\bpandas\b",
        "numpy": r"\bnumpy\b",
        "matplotlib": r"\bmatplotlib\b",
        "seaborn": r"\bseaborn\b",
        "d3": r"\bd3\b|\bd3\.js\b",
        "three.js": r"\bthree(\.js)?\b",
        "graphql": r"\bgraphql\b",
        "apollo": r"\bapollo\b",
        "jest": r"\bjest\b",
        "mocha": r"\bmocha\b",
        "pytest": r"\bpytest\b",
        "jasmine": r"\bjasmine\b",
        "terraform": r"\bterraform\b",
        "kubernetes": r"\bkubernetes\b|\bk8s\b",
        "docker": r"\bdocker\b",
    }

    found = set()
    for name, patt in patterns.items():
        if re.search(patt, text):
            found.add(name)

    return sorted(found)


def getStatus(overall_score: float | int | None) -> str:
    """
    Map overall score (expected 0-1000, also accepts 0-100) to a status label.

    Returns one of:
      - "excellent"   (900-1000)
      - "good"        (750-899)
      - "average"     (500-749)
      - "weak"        (300-499)
      - "unsuitable"  (0-299)

    If overall_score is None or invalid, returns "unsuitable".
    """
    try:
        if overall_score is None:
            return "unsuitable"
        score = float(overall_score)
    except Exception:
        return "unsuitable"

    # Accept scores on 0-100 scale too (convert to 0-1000)
    if score <= 100:
        score = score * 10
        


    # Clamp
    score = max(0.0, min(1000.0, score))

    if score >= 300:
        return "Suitable"
    return "Unsuitable"


def insert_candidates(candidate: dict, db: Session | None = None):
    """
    Nếu db không phải Session thực (hoặc None), tạo Session cục bộ.
    Hàm an toàn hơn: dùng candidate.get(...) để tránh KeyError,
    xử lý filedata cả trường hợp base64 string hoặc bytes.
    """
    created_local_session = False
    # nếu db không có phương thức execute thì tạo session cục bộ
    if db is None or not hasattr(db, "execute"):
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        created_local_session = True

    try:
        table = metadata.tables.get("candidates")
        if table is None:
            raise HTTPException(status_code=500, detail="Table 'candidates' not found")

        cols = set(table.c.keys())
        data = {}
        
        candidate_for_scoring = {
            'job_id': candidate.get('job_id'),
            'hard_skills': candidate.get('hard_skills', ''),
            'experience': candidate.get('experience', ''),
            'cv_summary': candidate.get('cv_summary', ''),
            'education': candidate.get('education', ''),
            'tools': candidate.get('tools', ''),
            'certificates': candidate.get('certificates', ''),
            'soft_skills': candidate.get('soft_skills', '')
        }
        
        overall_score = score_candidate(candidate_for_scoring, db)


            
        if "application_status" in cols :
            data["application_status"] = getStatus(overall_score)
        
        # an toàn: dùng .get để tránh KeyError
        if "email" in cols and candidate.get("email"):
            data["email"] = candidate.get("email")
        if "full_name" in cols and candidate.get("full_name"):
            data["full_name"] = candidate.get("full_name")
        if "phone" in cols and candidate.get("phone"):
            data["phone"] = candidate.get("phone")
            
        #dob 
        #gender
        
            
        if "address" in cols and candidate.get("address"):
            data["address"] = candidate.get("address")

        if "technical_skills" in cols and candidate.get("hard_skills"):
            data["technical_skills"] = candidate.get("hard_skills")
        if "soft_skills" in cols and candidate.get("soft_skills"):
            data["soft_skills"] = candidate.get("soft_skills")
        if "tools" in cols and candidate.get("tools"):
            data["tools"] = candidate.get("tools")

        if "programming_languages" in cols:
            data["programming_languages"] = ', '.join(extract_programming_languages(candidate.get('hard_skills', '')))

        if "frameworks_and_libraries" in cols:
            data["frameworks_and_libraries"] = ', '.join(extract_frameworks_and_libraries(candidate.get('experience', '')))

        if "work_experience_summary" in cols and candidate.get("experience"):
            data["work_experience_summary"] = candidate.get("experience")
        if "education_summary" in cols and candidate.get("education"):
            data["education_summary"] = candidate.get("education")
        if "certifications_summary" in cols and candidate.get("certificates"):
            data["certifications_summary"] = candidate.get("certificates")

        if "filename" in cols and candidate.get("filename"):
            data["filename"] = candidate.get("filename")
            
        if "job_id" in cols:
            col_obj = table.c.get("job_id")
            provided_job_id = candidate.get("job_id")
            if provided_job_id is not None and provided_job_id != "":
                # accept numeric strings too
                try:
                    data["job_id"] = int(provided_job_id)
                except Exception:
                    data["job_id"] = provided_job_id
            else:
                # if column allows NULL, set None; else require caller to provide job_id
                if getattr(col_obj, "nullable", True):
                    data["job_id"] = None
                else:
                    raise HTTPException(status_code=400, detail="Missing required field 'job_id' for candidates table")


        # filedata: hỗ trợ base64 string hoặc bytes
        if "filedata" in cols and candidate.get("filedata") is not None:
            raw = candidate.get("filedata")
            file_bytes = None
            if isinstance(raw, (bytes, bytearray)):
                file_bytes = bytes(raw)
            elif isinstance(raw, str):
                try:
                    file_bytes = base64.b64decode(raw, validate=True)
                except Exception:
                    # không phải base64 -> lưu utf-8 bytes (fallback)
                    file_bytes = raw.encode("utf-8", errors="ignore")
            if file_bytes is not None:
                data["filedata"] = file_bytes

        if "mimetype" in cols and candidate.get("mimetype"):
            data["mimetype"] = candidate.get("mimetype")
        if "cv_summary" in cols and candidate.get("cv_summary"):
            data["cv_summary"] = candidate.get("cv_summary")

        # scoring (dùng các trường có sẵn, an toàn với .get)

        if 'overall_cv_score' in cols:
            data['overall_cv_score'] = overall_score
        if 'matching_percentage' in cols:
            data['matching_percentage'] = round(overall_score / 1000 * 100, 1)
        if 'file_size' in cols and candidate.get('file_size') is not None:
            data['file_size'] = candidate.get('file_size')

        if not data:
            raise HTTPException(status_code=400, detail="data = null")

        try:
            res = db.execute(table.insert().values(**data))
            db.commit()
        except Exception as e:
            # rollback nếu supported, log đầy đủ lỗi
            if hasattr(db, "rollback"):
                db.rollback()
            logging.error("DB insert failed: %s\n%s", e, traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"DB insert error: {e}")

        return {"status": "ok", "inserted": True, "rowcount": getattr(res, "rowcount", None)}
    finally:
        if created_local_session:
            try:
                db.close()
            except Exception:
                pass
            
            
            
            
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, MetaData, Table, select
from sqlalchemy.orm import sessionmaker, Session
from backend.dataAndModels.config import DATABASE_URL, engine , get_db, metadata
from backend.API.candidates_CV_Scoring import score_candidate
import re
import os
import base64

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

def insert_candidates(candidate : dict ,db: Session = Depends(get_db)):
    table = metadata.tables["candidates"]
    cols = set(table.c.keys())
    data = {}
    if "email" in cols: data["email"] = candidate["email"] 
    else: print("Email = null")
    
    if "full_name" in cols: data["full_name"] = candidate["full_name"]
    else: print("Full name = null")
    
    if "phone" in cols: data["phone"] = candidate["phone"]
    else: print("Phone = null")
    
    #DoB
    #Gender
    
    if "address" in cols: data["address"] = candidate["address"]
    else: print("Address = null")
    
    #linkedin
    #porfolio url
    
    if "technical_skills" in cols: data["hard_skills"] = candidate["hard_skills"]
    else: print("hard skills = null")
    
    if "soft_skills" in cols: data["soft_skills"] = candidate["soft_skills"]
    else: print("soft skills = null")
    
    if "tools_and_technologies" in cols: data["tools"] = candidate["tools"]
    else: print("tools = null")
    
    if "programming_languages" in cols: data["programming_languages"] = ', '.join(extract_programming_languages(candidate['hard_skills']))
    else: print("programming languages = null")
    
    if 'frameworks_and_libraries' in cols: data['frameworks_and_libraries'] = ', '.join(extract_frameworks_and_libraries(candidate['experience']))
    else: print("frameworks and libraries = null")
    
    if 'work_experience_summary' in cols: data['work_experience_summary'] = candidate['experience']
    else: print("work experience summary = null")
    
    if 'education_summary' in cols: data['education_summary'] = candidate['education']
    else: print("education summary = null")
    
    if 'certifications_summary' in cols: data['certifications_summary'] = candidate['certificates']
    else: print('certification summary = null')
    
    #expired certifications
    #languages summary
    #notable projects
    #awards and honors
    #publications
    #volunteers
    #hobies and interests
    
    if 'filename' in cols: data['filename'] = candidate['filename']
    else: print("filename = null")
    
    # filedata: accept raw bytes or base64 string coming from record
    if 'filedata' in cols:
        raw = candidate.get('filedata')
        file_bytes = None
        if raw is None:
            file_bytes = None
        elif isinstance(raw, (bytes, bytearray)):
            file_bytes = bytes(raw)
        elif isinstance(raw, str):
            # try to detect if string is base64; decode, else leave None
            try:
                file_bytes = base64.b64decode(raw, validate=True)
            except Exception:
                # not a valid base64 string — try utf-8 decode then re-encode
                try:
                    file_bytes = raw.encode('utf-8')
                except Exception:
                    file_bytes = None
        else:
            file_bytes = None

        if file_bytes is not None:
            data['filedata'] = file_bytes
        else:
            print("filedata = null or unsupported type")
    else:
        print("filedata = null")
    
    if 'mimetype' in cols: data['mimetype'] = candidate['mimetype']
    else: print("mimetype = null")
    
    if 'cv_summary' in cols: data['cv_summary'] = candidate['cv_summary']
    else: print("cv_summary = null")
    
    overall_score = score_candidate(candidate)
    if 'overall_cv_score' in cols: data['overall_cv_score'] = overall_score
    else: print("overall cv score = null")
    
    if 'matching_percentage' in cols: data['matching_percentage'] = round(overall_score/1000*100, 1)
    else: print("matching percentage = null")
    
    if 'file_size' in cols: data['file_size'] = candidate['file_size']
    else: print("file size = null")
    
    if not data:
        raise HTTPException(status_code=400, detail="data = null")
    
    try:
        res = db.execute(table.insert().values(**data))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi khi insert: {e}")
    
    return {"status": "ok", "inserted": True, "rowcount": getattr(res, "rowcount", None)}





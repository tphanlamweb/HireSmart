
@startuml
!theme plain
skinparam shadowing false
skinparam nodesep 60
skinparam ranksep 60

package "Frontend (HTML/JS + Tailwind)" as FE {
  [HR Dashboard] #..# [API: dashboard.py]
  [Candidate Apply] #..# [API: Scan_CV.py]
  [Admin Panel] #..# [API: auth/]
}

package "Backend API (FastAPI)" as API {
  package "API" {
    [app.py] --> [Scan_CV.py] : parse CV
    [app.py] --> [candidates_CV_Scoring.py] : score
    [app.py] --> [dashboard.py] : stats
    [app.py] --> [Email_send_respon] : send mail
  }

  package "Scoring Engine" {
    [candidates_CV_Scoring.py] --> [scoring/tfidf_scoring.py]
    [candidates_CV_Scoring.py] --> [scoring/phobert_extractor.py]
  }

  package "Auth" {
    [auth/auth.py] : JWT
  }

  package "Database" {
    [database/models.py] : MySQL
  }
}

package "Infrastructure" {
  [MySQL DB] <<database>>
  [File Storage] <<PDF/DOCX>>
  [PhoBERT Model] <<NLP>>
}

' Connections
[HR Dashboard] --> [app.py]
[Candidate Apply] --> [Scan_CV.py]
[Email_send_respon] --> [SMTP/Gmail]
[Scan_CV.py] --> [pdf_parser.py]
[Scan_CV.py] --> [PhoBERT Model]
[candidates_CV_Scoring.py] --> [MySQL DB]
[dashboard.py] --> [MySQL DB]
[results/] <-- [candidates_CV_Scoring.py] : export CSV

note right of [app.py]
  FastAPI Main Entry
  RESTful JSON API
end note

note bottom of [MySQL DB]
  Tables: users, candidates,
  job_descriptions, cv_scores
end note


@enduml
```
HireSmart
├─ README.md
├─ backend
│  ├─ API
│  │  ├─ Email_send_respon
│  │  │  ├─ __init__.py
│  │  │  ├─ create_token.py
│  │  │  ├─ render_mail.py
│  │  │  ├─ send_mail.py
│  │  │  └─ verify_mail.py
│  │  ├─ Scan_CV.py
│  │  ├─ __init__.py
│  │  ├─ app.py
│  │  ├─ candidates_CV_Scoring.py
│  │  ├─ dashboard.py
│  │  ├─ getcandidate.py
│  │  ├─ scoring
│  │  │  ├─ __init__.py
│  │  │  ├─ education_scoring.py
│  │  │  ├─ experience_scoring.py
│  │  │  ├─ similarity_scoring.py
│  │  │  ├─ soft_skills_scoring.py
│  │  │  ├─ technical_skill_scoring.py
│  │  │  └─ tools_and_certificates_scoring.py
│  │  └─ test_parallel_scoring.py
│  ├─ __init__.py
│  ├─ dataAndModels
│  │  ├─ __init__.py
│  │  ├─ candidates_table.py
│  │  ├─ config.py
│  │  ├─ database_controler.py
│  │  ├─ model.py
│  │  └─ test_dtb.py
│  └─ results
│     ├─ candidate_with_token.csv
│     └─ demo_data.csv
├─ command.txt
├─ demo.html
├─ frontend
│  ├─ .DS_Store
│  ├─ Styles
│  │  ├─ Create_job.css
│  │  ├─ Create_job.js
│  │  ├─ hr_cv.css
│  │  ├─ hrjob.js
│  │  ├─ login.css
│  │  ├─ profile.css
│  │  ├─ recruitment.css
│  │  ├─ recruitment.js
│  │  ├─ style copy.css
│  │  └─ style.css
│  ├─ html
│  │  ├─ Create_job.html
│  │  ├─ Home.html
│  │  ├─ Job_list.html
│  │  ├─ Login.html
│  │  ├─ Recruitment.html
│  │  ├─ bulk_email.html
│  │  ├─ dashboard.html
│  │  ├─ profile copy.html
│  │  └─ profile.html
│  ├─ templates
│  │  ├─ image.png
│  │  ├─ logo-2.png
│  │  ├─ logo_Google.png
│  │  ├─ mail.png
│  │  ├─ password.png
│  │  └─ picture.png

```
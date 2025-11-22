
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
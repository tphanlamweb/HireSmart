#!/usr/bin/env python
"""
Script khởi động FastAPI server với uvicorn.
Đảm bảo chạy từ thư mục gốc của project.
"""
import sys
from pathlib import Path

# Đảm bảo thư mục gốc của project nằm trong PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if __name__ == "__main__":
    import uvicorn
    
    # Chạy server
    uvicorn.run(
        "backend.API.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["backend", "frontend"] if Path("backend").exists() else ["backend"]
    )





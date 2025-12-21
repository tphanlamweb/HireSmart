from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request
from sqlalchemy import create_engine, MetaData, Table, select, update
from sqlalchemy.orm import sessionmaker, Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from typing import List
from pydantic import BaseModel
from backend.dataAndModels.config import DATABASE_URL


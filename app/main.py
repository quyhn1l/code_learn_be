# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.courses import router as courses_router
from app.routers.enrollments import router as enrollments_router
from app.routers.users import router as users_router
from app.routers.lessons import router as lessons_router
from app.routers.code_execution import router as code_execution_router
from app.routers.auth import router as auth_router
from app.routers.lesson_progress import router as  lesson_progress_router
import logging

from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    logger.info("Initializing database...")
    get_db()
    
    yield  # FastAPI runs here
    
    # Shutdown events
    logger.info("Shutting down...")

app = FastAPI(
    title="Learning Platform API",
    description="API for learning platform with course management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(courses_router)
app.include_router(enrollments_router)
app.include_router(users_router)
app.include_router(lessons_router)
app.include_router(code_execution_router)
app.include_router(auth_router)
app.include_router(lesson_progress_router)
@app.get("/")
def read_root():
    return {"message": "Welcome to Learning Platform API"}
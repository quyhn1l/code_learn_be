# app/routers/code_execution.py
from enum import Enum
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(
    prefix="/code",
    tags=["code execution"]
)

class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript" 
    JAVA = "java"
    CPP = "cpp"
    GO = "go"

class CodeRequest(BaseModel):
    content: str
    language: Language

@router.post("/run")
async def run_code(code: CodeRequest):
    print("Executing code:", code.content) 
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8001/run",
                json={
                    "content": code.content,
                    "language": code.language
                }
            )
            result = response.json()
            print("Response:", result) 
            return result
        except Exception as e:
            print("Error:", str(e)) 
            raise HTTPException(500, str(e))
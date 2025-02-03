from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import logging
import os
from enum import Enum
from typing import Optional, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    GO = "go"

class CodeRequest(BaseModel):
    content: str
    language: Language

class LanguageConfig:
    def __init__(
        self, 
        file_extension: str,
        run_cmd: list[str],
        compile_cmd: Optional[list[str]] = None,
        timeout: int = 5
    ):
        self.file_extension = file_extension
        self.compile_cmd = compile_cmd
        self.run_cmd = run_cmd
        self.timeout = timeout

LANGUAGE_CONFIGS: Dict[Language, LanguageConfig] = {
    Language.PYTHON: LanguageConfig(
        file_extension=".py",
        run_cmd=["python3", "{filename}"],
        timeout=5
    ),
    Language.JAVASCRIPT: LanguageConfig(
        file_extension=".js", 
        run_cmd=["node", "{filename}"],
        timeout=5
    ),
    Language.JAVA: LanguageConfig(
        file_extension=".java",
        compile_cmd=["javac", "{filename}"],
        run_cmd=["java", "{classname}"],
        timeout=10
    ),
    Language.CPP: LanguageConfig(
        file_extension=".cpp",
        compile_cmd=["g++", "-o", "{executable}", "{filename}"],
        run_cmd=["./{executable}"],
        timeout=5
    ),
    Language.GO: LanguageConfig(
        file_extension=".go",
        run_cmd=["go", "run", "{filename}"],
        timeout=5
    )
}

def prepare_java_code(code: str) -> str:
    """Wrap Java code in a Main class if it doesn't have a class definition"""
    if "class" not in code:
        return f"""
public class Main {{
    public static void main(String[] args) {{
        {code}
    }}
}}
"""
    return code

def get_java_class_name(code: str) -> str:
    """Extract the public class name from Java code"""
    import re
    match = re.search(r"public\s+class\s+(\w+)", code)
    return match.group(1) if match else "Main"

@app.post("/run")
async def run_code(code: CodeRequest):
    logger.info(f"Received {code.language} code: {code.content}")
    logger.info(f"Config being used: {LANGUAGE_CONFIGS[code.language]}")
    config = LANGUAGE_CONFIGS[code.language]
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source file
        filename = f"source{config.file_extension}"
        filepath = os.path.join(temp_dir, filename)
        
        # Special handling for Java
        if code.language == Language.JAVA:
            code.content = prepare_java_code(code.content)
            class_name = get_java_class_name(code.content)
        
        # Write code to file
        with open(filepath, 'w') as f:
            f.write(code.content)
            f.flush()
        
        try:
            # Compilation phase (if needed)
            if config.compile_cmd:
                executable = "program"
                compile_cmd = [
                    cmd.format(
                        filename=filename,
                        executable=executable,
                        classname=class_name if code.language == Language.JAVA else None
                    )
                    for cmd in config.compile_cmd
                ]
                
                logger.info(f"Compiling with command: {compile_cmd}")
                compile_result = subprocess.run(
                    compile_cmd,
                    cwd=temp_dir,
                    capture_output=True,
                    text=True
                )
                
                if compile_result.returncode != 0:
                    logger.error(f"Compilation error: {compile_result.stderr}")
                    return {"error": f"Compilation error: {compile_result.stderr}"}
            
            # Execution phase
            run_cmd = [
                cmd.format(
                    filename=filename,
                    executable=executable if config.compile_cmd else None,
                    classname=class_name if code.language == Language.JAVA else None
                )
                for cmd in config.run_cmd
            ]
            
            logger.info(f"Running command: {run_cmd}")
            result = subprocess.run(
                run_cmd,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=config.timeout
            )
            
            logger.info(f"Return code: {result.returncode}")
            logger.info(f"Stdout: {result.stdout}")
            logger.info(f"Stderr: {result.stderr}")
            
            if result.returncode != 0:
                return {"error": result.stderr}
                
            return {"output": result.stdout}
            
        except subprocess.TimeoutExpired:
            logger.error(f"Code execution timed out after {config.timeout} seconds")
            return {"error": f"Code execution timed out after {config.timeout} seconds"}
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
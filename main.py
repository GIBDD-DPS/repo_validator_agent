"""
Repo Validator Agent — FastAPI сервис для анализа репозиториев (полная версия)
"""
import os
import uuid
import shutil
import zipfile
import io
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl

from core.repository_scanner import RepositoryScanner
from core.project_analyzer import ProjectAnalyzer
from core.fix_engine import StepFixEngine
from core.linter_runner import LinterRunner
from core.ast_analyzer import ASTAnalyzer
from core.full_file_rewriter import FullFileRewriter
from config import settings

app = FastAPI(title="Repo Validator Agent")

# ----- CORS -----
origins = [
    "https://prizolov.ru",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: Dict[str, dict] = {}

class RepoRequest(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = None

class InstallToolsRequest(BaseModel):
    session_id: str
    tools: List[str]

class ChatRequest(BaseModel):
    message: str

# Рекомендованные инструменты (заглушка)
RECOMMENDED_TOOLS = [
    {"name": "flake8", "description": "Линтер для проверки стиля кода"},
    {"name": "pylint", "description": "Статический анализатор для поиска ошибок"},
    {"name": "bandit", "description": "Поиск уязвимостей безопасности"},
]

def create_components(repo_url: str):
    scanner = RepositoryScanner(repo_url)
    scanner.clone()
    files = scanner.scan_repository()
    return {
        "scanner": scanner,
        "files": files,
        "project_analyzer": ProjectAnalyzer(),
        "ast_analyzer": ASTAnalyzer(),
        "linter_runner": LinterRunner(),
        "full_rewriter": FullFileRewriter(),
        "step_fix_engine": StepFixEngine(),
        "progress": None,
        "hallucination_shield": None,
        "legal_officer": None,
    }

def run_analysis(session_id: str, repo_url: str):
    session = SESSIONS.get(session_id)
    if not session:
        return
    session["status"] = "in_progress"
    try:
        comps = create_components(repo_url)
        files = comps["files"]
        project_analyzer = comps["project_analyzer"]
        ast_analyzer = comps["ast_analyzer"]
        linter = comps["linter_runner"]

        project_issues = project_analyzer.analyze(files)

        ast_issues = {}
        for path, content in files.items():
            if path.endswith(".py"):
                ast_issues[path] = ast_analyzer.analyze(content)

        lint_issues = linter.run_all(files)

        report = {
            "project_issues": project_issues,
            "ast_issues": ast_issues,
            "lint_issues": lint_issues,
        }
        session["report"] = report
        session["optimization_recommended"] = RECOMMENDED_TOOLS
        session["status"] = "done"
        # Сохраняем файлы для возможного скачивания
        session["files"] = files
    except Exception as e:
        session["status"] = "error"
        session["error"] = str(e)

def report_to_summary(report: dict) -> str:
    lines = []
    if report.get("project_issues"):
        lines.append("Проблемы проекта:\n" + "\n".join(report["project_issues"]))
    if report.get("ast_issues"):
        for f, issues in report["ast_issues"].items():
            if issues:
                lines.append(f"AST ({f}):\n" + "\n".join(issues))
    if report.get("lint_issues"):
        for f, issues in report["lint_issues"].items():
            if issues:
                lines.append(f"Линтеры ({f}):\n" + "\n".join(issues))
    return "\n\n".join(lines) or "Проблем не найдено"

# ----- ЭНДПОИНТЫ -----

@app.post("/scan")
async def start_scan(request: RepoRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "repo_url": str(request.repo_url),
        "status": "pending",
        "report": None,
        "optimization_recommended": RECOMMENDED_TOOLS,
    }
    background_tasks.add_task(run_analysis, session_id, str(request.repo_url))
    return {
        "session_id": session_id,
        "optimization_recommended": RECOMMENDED_TOOLS,
    }

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    resp = {"session_id": session_id, "status": session["status"]}
    if session["status"] == "done":
        resp["report"] = session["report"]
    elif session["status"] == "error":
        resp["error"] = session["error"]
    return resp

@app.get("/report/{session_id}")
async def get_report(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    if session.get("status") != "done":
        raise HTTPException(400, "Отчёт ещё не готов")
    summary = report_to_summary(session["report"])
    return {
        "session_id": session_id,
        "report_summary": summary,
        "optimization_recommended": session.get("optimization_recommended", []),
    }

@app.get("/changes/{session_id}")
async def get_changes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    # Заглушка – реальный список изменений появится позже
    return {
        "session_id": session_id,
        "files_changed": [],
        "patch_summary": "Автоматические исправления пока не реализованы.",
    }

@app.post("/fix/{session_id}")
async def apply_fixes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if session.get("status") != "done":
        raise HTTPException(status_code=400, detail="Отчёт ещё не готов")
    # Заглушка
    return {
        "session_id": session_id,
        "status": "fixes_applied",
        "message": "Исправления применены (заглушка).",
    }

@app.post("/install_tools")
async def install_tools(req: InstallToolsRequest):
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    # Эмуляция установки – убираем установленные инструменты из рекомендаций
    installed = req.tools
    remaining = [t for t in session.get("optimization_recommended", []) if t["name"] not in installed]
    session["optimization_recommended"] = remaining
    return {
        "session_id": req.session_id,
        "installed": installed,
        "optimization_recommended": remaining,
        "report_summary": report_to_summary(session.get("report", {})),
    }

@app.get("/download/{session_id}")
async def download_repo(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    # Создаём ZIP из клонированного репозитория
    scanner = RepositoryScanner(session["repo_url"])
    try:
        # Убедимся, что репозиторий склонирован
        scanner.clone()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(scanner.local_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, scanner.local_path)
                    zf.write(full_path, arcname)
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=repo_{session_id}.zip"}
        )
    except Exception as e:
        raise HTTPException(500, f"Не удалось создать архив: {str(e)}")

@app.post("/chat/{session_id}")
async def chat(session_id: str, req: ChatRequest):
    # Заглушка – можно подключить реальный AI
    return {
        "reply": f"Вы спросили: «{req.message}». К сожалению, ИИ-консультант пока недоступен, но вы можете изучить отчёт выше."
    }

@app.on_event("shutdown")
async def cleanup():
    tmp = "/tmp/repo_scan"
    if os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)

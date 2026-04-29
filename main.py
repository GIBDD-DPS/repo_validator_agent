"""
Repo Validator Agent — FastAPI сервис для анализа репозиториев
"""
import os
import uuid
import shutil
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

from core.repository_scanner import RepositoryScanner
from core.project_analyzer import ProjectAnalyzer
from core.fix_engine import StepFixEngine
from core.linter_runner import LinterRunner
from core.ast_analyzer import ASTAnalyzer
from core.full_file_rewriter import FullFileRewriter
from .config import settings

# Эти классы пока не реализованы, заменяем на None
# from prizolov_integration.progress_metrics import ProgressMetrics
# from ai_agents.anti_hallucination_shield import AntiHallucinationShield
# from ai_agents.legal_compliance_officer import LegalComplianceOfficer

app = FastAPI(title="Repo Validator Agent")

# Временное хранилище сессий (только для демонстрации, в production – Redis)
SESSIONS: Dict[str, dict] = {}

class RepoRequest(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = None

def create_components(repo_url: str):
    """Фабрика компонентов – создаёт все анализаторы для одного запуска."""
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
        "progress": None,            # Вместо ProgressMetrics()
        "hallucination_shield": None, # Вместо AntiHallucinationShield()
        "legal_officer": None,        # Вместо LegalComplianceOfficer()
    }

def run_analysis(session_id: str, repo_url: str):
    """Фоновая задача: выполняет полный анализ и сохраняет результат."""
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
        full_rewriter = comps["full_rewriter"]

        # 1. Базовый разбор
        project_issues = project_analyzer.analyze(files)

        # 2. AST-анализ для Python файлов
        ast_issues = {}
        for path, content in files.items():
            if path.endswith(".py"):
                ast_issues[path] = ast_analyzer.analyze(content)

        # 3. Линтеры
        lint_issues = linter.run_all(files)

        # 4. Сборка результата
        report = {
            "project_issues": project_issues,
            "ast_issues": ast_issues,
            "lint_issues": lint_issues,
        }
        session["report"] = report
        session["status"] = "done"
    except Exception as e:
        session["status"] = "error"
        session["error"] = str(e)

@app.post("/scan")
async def start_scan(request: RepoRequest, background_tasks: BackgroundTasks):
    """Запускает анализ репозитория, возвращает ID сессии."""
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "repo_url": str(request.repo_url),
        "status": "pending",
        "report": None
    }
    background_tasks.add_task(run_analysis, session_id, str(request.repo_url))
    return {"session_id": session_id}

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    """Возвращает статус сессии и (если готов) отчёт."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    resp = {"session_id": session_id, "status": session["status"]}
    if session["status"] == "done":
        resp["report"] = session["report"]
    elif session["status"] == "error":
        resp["error"] = session["error"]
    return resp

@app.post("/fix/{session_id}")
async def apply_fixes(session_id: str):
    """Применяет автоматические исправления (заглушка)."""
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if session.get("status") != "done":
        raise HTTPException(status_code=400, detail="Отчёт ещё не готов")
    # В реальной версии здесь будет запуск StepFixEngine
    # return {"session_id": session_id, "fixes_applied": [...]}
    raise HTTPException(status_code=501, detail="Автофиксы отключены (API в разработке)")

@app.on_event("shutdown")
async def cleanup():
    """Очистка временных клонов."""
    tmp = "/tmp/repo_scan"
    if os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True)

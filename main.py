# main.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import logging
from typing import Dict, Any

# Импорты твоих модулей (как в оригинале)
from core.github_connector import GitHubConnector
from core.repository_scanner import RepositoryScanner
from core.file_analyzer import FileAnalyzer
from core.project_analyzer import ProjectAnalyzer
from core.full_file_rewriter import FullFileRewriter
from core.step_fix_engine import StepFixEngine
from core.report_generator import ReportGenerator
from core.copyright_manager import CopyrightManager

from prizolov_integration.progress_metrics import ProgressMetrics
from prizolov_integration.anti_hallucination_shield import AntiHallucinationShield
from prizolov_integration.legal_compliance_officer import LegalComplianceOfficer

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repo_validator")

# --- FastAPI app ---
app = FastAPI(title="Repo Validator Agent API", version="1.0.0")

# CORS: разрешаем фронтенду prizolov.ru обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prizolov.ru", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Хранилище сессий (в простом виде, в продакшене заменить на БД)
SESSIONS: Dict[str, Dict[str, Any]] = {}

# Pydantic модели запросов/ответов
class ScanRequest(BaseModel):
    repo_url: str
    branch: str | None = None

class ScanResponse(BaseModel):
    session_id: str
    status: str

class ReportResponse(BaseModel):
    session_id: str
    report: Dict[str, Any]

# --- Фабрика/инициализация компонентов ---
def create_components(repo_url: str):
    github = GitHubConnector(repo_url)
    scanner = RepositoryScanner(github)
    file_analyzer = FileAnalyzer()
    project_analyzer = ProjectAnalyzer()
    copyright_manager = CopyrightManager()
    rewriter = FullFileRewriter(copyright_manager)
    report_generator = ReportGenerator()
    metrics = ProgressMetrics()
    shield = AntiHallucinationShield()
    legal = LegalComplianceOfficer()
    step_fix = StepFixEngine(rewriter, report_generator, metrics, shield, legal)
    return {
        "github": github,
        "scanner": scanner,
        "file_analyzer": file_analyzer,
        "project_analyzer": project_analyzer,
        "step_fix": step_fix,
        "report_generator": report_generator,
        "metrics": metrics,
    }

# --- Фоновая задача: полный pipeline анализа ---
def run_scan_pipeline(session_id: str, repo_url: str, branch: str | None = None):
    logger.info("Session %s: starting scan for %s", session_id, repo_url)
    try:
        comps = create_components(repo_url)
        scanner: RepositoryScanner = comps["scanner"]
        file_analyzer: FileAnalyzer = comps["file_analyzer"]
        project_analyzer: ProjectAnalyzer = comps["project_analyzer"]
        step_fix: StepFixEngine = comps["step_fix"]
        report_generator: ReportGenerator = comps["report_generator"]
        metrics = comps["metrics"]

        # 1) Скачиваем/сканируем репозиторий
        # Предполагается, что scanner.scan_repository() возвращает dict {path: content}
        files = scanner.scan_repository() if branch is None else scanner.scan_repository(branch=branch)

        # 2) Анализ файлов
        file_issues = {}
        for file_path, content in files.items():
            issues = file_analyzer.analyze_file(file_path, content)
            file_issues[file_path] = issues
            metrics.increment_files_analyzed()

        # 3) Анализ проекта
        project_issues = project_analyzer.analyze_project(files, file_issues)

        # 4) Применение пошаговых фиксов
        for file_path, issues in file_issues.items():
            if not issues:
                continue
            step_fix.process_file(file_path, files[file_path], issues)

        # 5) Генерация отчёта
        final_report = report_generator.generate_final_report(file_issues, project_issues, metrics)

        # Сохраняем результат в сессии
        SESSIONS[session_id]["status"] = "done"
        SESSIONS[session_id]["report"] = final_report
        logger.info("Session %s: scan finished", session_id)
    except Exception as e:
        logger.exception("Session %s: scan failed: %s", session_id, e)
        SESSIONS[session_id]["status"] = "failed"
        SESSIONS[session_id]["error"] = str(e)

# --- Эндпоинты ---

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/scan", response_model=ScanResponse, status_code=202)
async def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    # Создаём сессию
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {"status": "queued", "repo_url": req.repo_url}
    # Запускаем фоновую задачу
    background_tasks.add_task(run_scan_pipeline, session_id, req.repo_url, req.branch)
    logger.info("Session %s: queued scan for %s", session_id, req.repo_url)
    return ScanResponse(session_id=session_id, status="queued")

@app.get("/report/{session_id}", response_model=ReportResponse)
async def get_report(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") != "done":
        return ReportResponse(session_id=session_id, report={"status": session.get("status"), "message": session.get("error", "")})
    return ReportResponse(session_id=session_id, report=session.get("report"))

@app.post("/fix/{session_id}")
async def apply_fixes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.get("status") != "done":
        raise HTTPException(status_code=400, detail="Report not ready")
    # Здесь можно вызвать шаги применения фиксов (если report содержит инструкции)
    # Пример: step_fix.apply_report(session["report"])
    return {"session_id": session_id, "status": "fixes_not_implemented_in_api"}

# --- Запуск через uvicorn (для локальной отладки) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

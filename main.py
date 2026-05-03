"""
Repo Validator Agent — FastAPI сервис (линтеры, автофиксы, AI-чат, авторские права)
"""
import os
import uuid
import shutil
import zipfile
import io
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
import requests

from core.repository_scanner import RepositoryScanner
from core.project_analyzer import ProjectAnalyzer
from core.fix_engine import StepFixEngine
from core.linter_runner import LinterRunner
from core.ast_analyzer import ASTAnalyzer
from core.full_file_rewriter import FullFileRewriter
from core.copyright_manager import CopyrightManager
from config import settings

app = FastAPI(title="Repo Validator Agent")

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

class CopyrightApplyRequest(BaseModel):
    copyright_text: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    product: Optional[str] = None

RECOMMENDED_TOOLS = [
    {"name": "prizolov-optimizer", "description": "Автоматическая оптимизация кода"},
    {"name": "prizolov-security", "description": "Поиск уязвимостей"},
    {"name": "prizolov-style", "description": "Автоформатирование под стандарты"},
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

# ----- YANDEX GPT -----
def query_yandex_gpt(api_key: str, prompt: str, context: str = "") -> str:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "modelUri": f"gpt://{os.getenv('YANDEX_FOLDER_ID', 'b1g3jdmevqk2s0n5e0t7')}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 2000
        },
        "messages": [
            {"role": "system", "text": "Ты — AI-консультант по анализу репозиториев. Отвечай кратко и по делу на русском языке."},
            {"role": "user", "text": f"Контекст отчёта:\n{context}\n\nВопрос пользователя: {prompt}"}
        ]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        alternatives = data.get("result", {}).get("alternatives", [])
        if alternatives:
            return alternatives[0].get("message", {}).get("text", "Нет ответа")
        else:
            return "Модель не вернула ответ."
    except Exception as e:
        return f"Ошибка при обращении к YandexGPT: {str(e)}"

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
    return {"session_id": session_id, "optimization_recommended": RECOMMENDED_TOOLS}

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
    return {
        "session_id": session_id,
        "files_changed": [],
        "patch_summary": "Для применения автоматических исправлений нажмите «Применить автофиксы».",
    }

@app.post("/fix/{session_id}")
async def apply_fixes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    if session.get("status") != "done":
        raise HTTPException(status_code=400, detail="Отчёт ещё не готов")
    engine = StepFixEngine()
    files = session.get("files", {})
    if not files:
        raise HTTPException(500, "Нет файлов для обработки")
    new_files = engine.format_all(files)
    session["fixed_files"] = new_files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in new_files.items():
            zf.writestr(path, content)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=repo_{session_id}_fixed.zip",
            "X-Fixed-Files": ",".join(engine.fixes_applied)
        }
    )

@app.post("/install_tools")
async def install_tools(req: InstallToolsRequest):
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
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
    files = session.get("fixed_files") or session.get("files", {})
    if not files:
        scanner = RepositoryScanner(session["repo_url"])
        scanner.clone()
        files = scanner.scan_repository()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=repo_{session_id}.zip"}
    )

@app.get("/copyright/{session_id}")
async def check_copyright(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    mgr = CopyrightManager()
    files = session.get("files") or session.get("fixed_files", {})
    found = mgr.check_copyright(files)
    return {"session_id": session_id, "copyrights": found}

@app.post("/copyright/{session_id}")
async def apply_copyright(session_id: str, req: CopyrightApplyRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    mgr = CopyrightManager()
    files = session.get("fixed_files") or session.get("files", {})
    if not files:
        raise HTTPException(400, "Нет файлов для обработки")
    new_files = mgr.apply_copyright(
        files,
        copyright_text=req.copyright_text,
        author=req.author,
        organization=req.organization,
        product=req.product,
        skip_existing=True
    )
    session["fixed_files"] = new_files
    return {"session_id": session_id, "status": "applied", "message": "Авторские права добавлены."}

@app.post("/chat/{session_id}")
async def chat(session_id: str, req: ChatRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    context = ""
    if session.get("report"):
        context = report_to_summary(session["report"])
    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return {"reply": "Ошибка: не настроен API-ключ YandexGPT."}
    reply = query_yandex_gpt(api_key, req.message, context)
    return {"reply": reply}

@app.on_event("shutdown")
async def cleanup():
    tmp = "/tmp/repo_scan"
    if os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)

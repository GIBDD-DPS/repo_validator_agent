# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Repo Validator Agent — FastAPI сервис (линтеры, автофиксы, AI-чат, копирайт, GitHub PR,
Пятиуровневый аудит, Цифровой совет директоров, Арбитраж, Центр техдолга, Git Analyzer, Dependency Intelligence)
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
from core.github_integration import GitHubIntegration
from core.prizolov_audit import PrizolovAuditor
from core.git_analyzer import GitAnalyzer
from core.dependency_analyzer import DependencyAnalyzer
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

SAVINGS = {"fixed": 0, "hours": 0.0, "money": 0.0}

class RepoRequest(BaseModel):
    repo_url: HttpUrl
    branch: Optional[str] = None

class ChatRequest(BaseModel):
    message: str

class AdvisorChatRequest(BaseModel):
    message: str
    role: str

class ArbitrageRequest(BaseModel):
    message: str

class CopyrightApplyRequest(BaseModel):
    copyright_text: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    product: Optional[str] = None

class CreatePRRequest(BaseModel):
    github_token: str
    title: Optional[str] = "Repo Validator automatic fixes"
    base_branch: Optional[str] = "main"

class SavingsUpdateRequest(BaseModel):
    fixed: int = 0
    hours: float = 0.0
    money: float = 0.0

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
        scanner = comps["scanner"]

        # ----- Git Analyzer -----
        git_stats = None
        try:
            git_analyzer = GitAnalyzer(scanner.local_path)
            git_stats = git_analyzer.analyze()
        except Exception as e:
            git_stats = {"error": str(e)}

        # ----- Dependency Analyzer -----
        dep_stats = None
        try:
            dep_analyzer = DependencyAnalyzer(scanner.local_path)
            dep_stats = dep_analyzer.analyze()
        except Exception as e:
            dep_stats = {"error": str(e)}

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

        auditor = PrizolovAuditor()
        audit_results = auditor.audit(files)
        serialized_audit = {}
        for level, issues in audit_results.items():
            serialized_audit[level] = [
                f"[{i.criticality.upper()}] {i.file}:{i.line} - {i.message}"
                for i in issues
            ]
        report["audit"] = serialized_audit
        report["git_stats"] = git_stats
        report["dep_stats"] = dep_stats   # ← добавляем анализ зависимостей

        session["report"] = report
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
    if report.get("audit"):
        level_names = {
            "architecture": "Архитектура",
            "security": "Безопасность",
            "performance": "Производительность",
            "documentation": "Документированность"
        }
        for level, issues in report["audit"].items():
            if issues:
                lines.append(f"Аудит {level_names.get(level, level)}:\n" + "\n".join(issues))
    if report.get("git_stats") and not report["git_stats"].get("error"):
        gs = report["git_stats"]
        lines.append(
            f"Git активность:\n"
            f"- Коммитов: {gs['total_commits']}\n"
            f"- Контрибьюторов: {gs['contributors_count']}\n"
            f"- Активность: {'активен' if gs['is_active'] else 'заброшен'}\n"
            f"- Последний коммит: {gs['last_commit']}"
        )
    if report.get("dep_stats"):
        ds = report["dep_stats"]
        if isinstance(ds, dict):
            if ds.get("vulnerabilities"):
                lines.append(f"Найдены уязвимости в зависимостях: {len(ds['vulnerabilities'])}")
            if ds.get("licenses"):
                lines.append(f"Лицензий проанализировано: {len(ds['licenses'])}")
    return "\n\n".join(lines) or "Проблем не найдено"

# ----- YANDEX GPT HELPER -----
def query_yandex_gpt(prompt: str, context: str = "", max_tokens: int = 2000) -> str:
    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return "Ошибка: не настроен YANDEX_API_KEY"
    folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    max_context_len = 3000
    if len(context) > max_context_len:
        context = context[:max_context_len] + "\n... (контекст обрезан)"
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": max_tokens
        },
        "messages": [
            {"role": "system", "text": "Ты — AI-консультант по анализу репозиториев. Отвечай кратко и по делу на русском языке."},
            {"role": "user", "text": f"Контекст отчёта:\n{context}\n\n{prompt}"}
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
    }
    background_tasks.add_task(run_analysis, session_id, str(request.repo_url))
    return {"session_id": session_id}

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

@app.get("/recommendations/{session_id}")
async def get_recommendations(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    report = session.get("report", {})
    if not report:
        raise HTTPException(400, "Нет отчёта")

    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return {"error": "AI ключ не настроен"}

    all_issues = []
    if report.get("project_issues"):
        all_issues.extend([f"Проект: {i}" for i in report["project_issues"]])
    for file, issues in report.get("ast_issues", {}).items():
        for i in issues:
            all_issues.append(f"AST ({file}): {i}")
    for file, issues in report.get("lint_issues", {}).items():
        for i in issues:
            all_issues.append(f"Линтер ({file}): {i}")
    for level, issues in report.get("audit", {}).items():
        for i in issues:
            all_issues.append(f"Аудит ({level}): {i}")

    if not all_issues:
        return {"recommendations": "Ошибок нет"}

    sample_issues = all_issues[:10]
    prompt = "Дай краткие рекомендации по исправлению каждой из следующих проблем (не более 2-3 предложений на пункт):\n" + "\n".join(sample_issues)
    recommendations = query_yandex_gpt(prompt, max_tokens=500)
    return {"recommendations": recommendations.strip()}

@app.post("/create_pr/{session_id}")
async def create_pr(session_id: str, req: CreatePRRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    files = session.get("fixed_files") or session.get("files")
    if not files:
        raise HTTPException(400, "Нет файлов для коммита")

    github = GitHubIntegration(req.github_token)
    summary = report_to_summary(session.get("report", {}))
    body = f"## Repo Validator Report\n```\n{summary}\n```"
    try:
        pr_url = github.create_pr(
            repo_url=session["repo_url"],
            files=files,
            base_branch=req.base_branch,
            title=req.title,
            body=body
        )
        if not pr_url:
            raise HTTPException(500, "Не удалось создать PR")
        return {"pull_request_url": pr_url}
    except Exception as e:
        raise HTTPException(500, f"Ошибка при создании PR: {str(e)}")

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

# ===== ЦИФРОВОЙ СОВЕТ ДИРЕКТОРОВ =====
ROLE_PROMPTS = {
    "analyst": "Ты — ведущий аналитик. Дай общую картину состояния проекта на основе отчёта, выдели ключевые проблемы и предложи приоритеты исправлений.",
    "architect": "Ты — архитектор. Оцени архитектурные риски, зависимости и циклические импорты. Предложи улучшения структуры проекта.",
    "security": "Ты — специалист по безопасности. На основе отчёта проанализируй найденные уязвимости, утечки секретов и дай рекомендации по защите.",
    "treasurer": "Ты — казначей. Оцени финансовые риски и стоимость технического долга на основе выявленных проблем. Дай прогноз затрат."
}

@app.post("/chat/advisor/{session_id}")
async def chat_advisor(session_id: str, req: AdvisorChatRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    context = ""
    if session.get("report"):
        context = report_to_summary(session["report"])

    system_prompt = ROLE_PROMPTS.get(req.role, ROLE_PROMPTS["analyst"])
    prompt = f"{system_prompt}\n\nКонтекст отчёта:\n{context}\n\nВопрос пользователя: {req.message}"

    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return {"reply": "Ошибка: не настроен API-ключ YandexGPT."}
    folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    max_context_len = 2500
    if len(prompt) > max_context_len:
        prompt = f"{system_prompt}\n\nКонтекст отчёта (сокращён):\n{context[:max_context_len - len(system_prompt) - 50]}...\n\nВопрос пользователя: {req.message}"

    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 2000
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": prompt}
        ]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        alternatives = data.get("result", {}).get("alternatives", [])
        if alternatives:
            return {"reply": alternatives[0].get("message", {}).get("text", "Нет ответа")}
        else:
            return {"reply": "Модель не вернула ответ."}
    except Exception as e:
        return {"reply": f"Ошибка при обращении к YandexGPT: {str(e)}"}

# ===== АРБИТРАЖ =====
@app.post("/chat/arbitrage/{session_id}")
async def chat_arbitrage(session_id: str, req: ArbitrageRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    context = ""
    if session.get("report"):
        context = report_to_summary(session["report"])

    prompt = (
        "Предложи два конкретных варианта исправления следующей проблемы в коде. "
        "Первый вариант — с точки зрения архитектора (минимизация зависимостей, улучшение структуры). "
        "Второй вариант — с точки зрения безопасности (защита от уязвимостей). "
        "Оформи ответ строго в формате:\n"
        "АРХИТЕКТОР: <предложение архитектора>\n"
        "БЕЗОПАСНИК: <предложение безопасника>\n\n"
        f"Проблема: {req.message}\n"
        f"Контекст отчёта:\n{context}"
    )

    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return {"architect": "Ошибка: не настроен API-ключ", "security": "Ошибка: не настроен API-ключ"}
    folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": [
            {"role": "system", "text": "Ты — эксперт по анализу кода. Твоя задача — предложить два разных варианта исправления проблемы."},
            {"role": "user", "text": prompt}
        ]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        alternatives = data.get("result", {}).get("alternatives", [])
        if not alternatives:
            return {"architect": "Модель не ответила", "security": "Модель не ответила"}
        text = alternatives[0].get("message", {}).get("text", "")
        architect = ""
        security = ""
        lines = text.split('\n')
        current_role = None
        for line in lines:
            if line.startswith("АРХИТЕКТОР:"):
                current_role = "architect"
                architect = line.replace("АРХИТЕКТОР:", "").strip()
            elif line.startswith("БЕЗОПАСНИК:"):
                current_role = "security"
                security = line.replace("БЕЗОПАСНИК:", "").strip()
            elif current_role == "architect":
                architect += " " + line.strip()
            elif current_role == "security":
                security += " " + line.strip()
        return {"architect": architect.strip() or "Нет ответа", "security": security.strip() or "Нет ответа"}
    except Exception as e:
        return {"architect": f"Ошибка: {str(e)}", "security": f"Ошибка: {str(e)}"}

# ----- ОБЫЧНЫЙ ЧАТ -----
@app.post("/chat/{session_id}")
async def chat(session_id: str, req: ChatRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    context = ""
    if session.get("report"):
        context = report_to_summary(session["report"])
    reply = query_yandex_gpt(req.message, context)
    return {"reply": reply}

# ----- СКАЧИВАНИЕ ZIP -----
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

# ===== ГЛОБАЛЬНЫЕ НАКОПЛЕНИЯ =====
@app.get("/savings")
async def get_savings():
    return SAVINGS

@app.post("/savings/update")
async def update_savings(req: SavingsUpdateRequest):
    SAVINGS["fixed"] += req.fixed
    SAVINGS["hours"] += req.hours
    SAVINGS["money"] += req.money
    return SAVINGS

@app.on_event("shutdown")
async def cleanup():
    tmp = "/tmp/repo_scan"
    if os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)

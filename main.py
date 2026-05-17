# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Repo Validator Agent — FastAPI сервис с кэшированием и таймаутами
"""
import os
import uuid
import shutil
import zipfile
import io
import json
import logging
import asyncio
import subprocess
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from config import settings
except ImportError:
    logger.warning("config.py не найден, использую значения по умолчанию")
    settings = type("Settings", (), {})()
    settings.app_name = "Prizolov Repo Validator"
    settings.debug = False

# ========== ФУНКЦИЯ СОЗДАНИЯ КЛАССОВ-ЗАГЛУШЕК ==========
def make_stub_class(name: str):
    class StubClass:
        def __init__(self, *args, **kwargs):
            logger.warning(f"[STUB] {name} инициализирован")
        def __getattr__(self, item):
            logger.warning(f"[STUB] {name}.{item} вызван")
            def stub_method(*args, **kwargs):
                logger.warning(f"[STUB] {name}.{item} — заглушка")
                return {} if item != "analyze" else {}
            return stub_method
    StubClass.__name__ = name
    return StubClass

# ========== ЗАГРУЗКА МОДУЛЕЙ CORE ==========
core_classes = {}

def safe_import_class(module_name, class_name):
    try:
        module = __import__(f"core.{module_name}", fromlist=[class_name])
        cls = getattr(module, class_name)
        logger.info(f"Загружен {class_name}")
        return cls
    except (ImportError, AttributeError) as e:
        logger.warning(f"Не удалось импортировать {class_name}: {e}")
        return make_stub_class(class_name)

required_classes = [
    ("repository_scanner", "RepositoryScanner"),
    ("project_analyzer", "ProjectAnalyzer"),
    ("fix_engine", "StepFixEngine"),
    ("linter_runner", "LinterRunner"),
    ("ast_analyzer", "ASTAnalyzer"),
    ("full_file_rewriter", "FullFileRewriter"),
    ("copyright_manager", "CopyrightManager"),
    ("github_integration", "GitHubIntegration"),
    ("prizolov_audit", "PrizolovAuditor"),
    ("git_analyzer", "GitAnalyzer"),
    ("dependency_analyzer", "DependencyAnalyzer"),
    ("semantic_ai", "SemanticAI"),
    ("scoring_engine", "ScoringEngine"),
    ("smart_triage", "SmartTriage"),
    ("mentor", "ContextualMentor"),
    ("roi_calculator", "ROICalculator"),
    ("audit_trail", "AuditTrail"),
    ("repo_publisher", "RepoPublisher"),
    ("multi_lang_analyzer", "MultiLangAnalyzer"),
    ("leaderboard", "Leaderboard")
]

for mod, cls in required_classes:
    core_classes[cls] = safe_import_class(mod, cls)

RepositoryScanner = core_classes["RepositoryScanner"]
ProjectAnalyzer = core_classes["ProjectAnalyzer"]
StepFixEngine = core_classes["StepFixEngine"]
LinterRunner = core_classes["LinterRunner"]
ASTAnalyzer = core_classes["ASTAnalyzer"]
FullFileRewriter = core_classes["FullFileRewriter"]
CopyrightManager = core_classes["CopyrightManager"]
GitHubIntegration = core_classes["GitHubIntegration"]
PrizolovAuditor = core_classes["PrizolovAuditor"]
GitAnalyzer = core_classes["GitAnalyzer"]
DependencyAnalyzer = core_classes["DependencyAnalyzer"]
SemanticAI = core_classes["SemanticAI"]
ScoringEngine = core_classes["ScoringEngine"]
SmartTriage = core_classes["SmartTriage"]
ContextualMentor = core_classes["ContextualMentor"]
ROICalculator = core_classes["ROICalculator"]
AuditTrail = core_classes["AuditTrail"]
RepoPublisher = core_classes["RepoPublisher"]
MultiLangAnalyzer = core_classes["MultiLangAnalyzer"]
Leaderboard = core_classes["Leaderboard"]

from core.cache_manager import CacheManager

app = FastAPI(title="Repo Validator Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://prizolov.ru", "http://localhost", "http://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: Dict[str, dict] = {}
SAVINGS = {"fixed": 0, "hours": 0.0, "money": 0.0}
LEADERBOARD = Leaderboard() if Leaderboard is not None else None
cache_manager = CacheManager()

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

class MentorRequest(BaseModel):
    issue: str
    file_context: Optional[str] = None

class PublishRequest(BaseModel):
    github_token: str
    action: str

class CopyrightApplyRequest(BaseModel):
    copyright_text: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    product: Optional[str] = None

class CreatePRRequest(BaseModel):
    github_token: str
    title: Optional[str] = "Repo Validator automatic fixes"
    base_branch: Optional[str] = "main"

class AutonomousFixRequest(BaseModel):
    github_token: str
    title: Optional[str] = "Repo Validator autonomous fixes"
    base_branch: Optional[str] = "main"
    apply_copyright: bool = False
    copyright_author: Optional[str] = None
    copyright_organization: Optional[str] = None
    copyright_product: Optional[str] = None

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
    }

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
    if report.get("multi_lang_issues"):
        for f, issues in report["multi_lang_issues"].items():
            if issues:
                lines.append(f"Мультиязычный анализ ({f}):\n" + "\n".join(issues))
    if report.get("audit"):
        level_names = {"architecture": "Архитектура", "security": "Безопасность",
                       "performance": "Производительность", "documentation": "Документированность"}
        for level, issues in report["audit"].items():
            if issues:
                lines.append(f"Аудит {level_names.get(level, level)}:\n" + "\n".join(issues))
    git_stats = report.get("git_stats")
    if git_stats and isinstance(git_stats, dict) and not git_stats.get("error"):
        lines.append(
            f"Git активность:\n"
            f"- Коммитов: {git_stats.get('total_commits', '?')}\n"
            f"- Контрибьюторов: {git_stats.get('contributors_count', '?')}\n"
            f"- Активность: {'активен' if git_stats.get('is_active') else 'заброшен'}\n"
            f"- Последний коммит: {git_stats.get('last_commit', '?')}"
        )
    dep_stats = report.get("dep_stats")
    if dep_stats and isinstance(dep_stats, dict):
        if dep_stats.get("vulnerabilities"):
            lines.append(f"Найдены уязвимости в зависимостях: {len(dep_stats['vulnerabilities'])}")
        if dep_stats.get("licenses"):
            lines.append(f"Лицензий проанализировано: {len(dep_stats['licenses'])}")
    semantic = report.get("semantic")
    if semantic and isinstance(semantic, dict) and not semantic.get("error"):
        cp = semantic.get("code_purpose")
        if cp:
            lines.append(
                f"Семантический анализ:\n"
                f"- Тип проекта: {cp.get('project_type', 'неизвестен')}\n"
                f"- Назначение: {cp.get('description', '')[:200]}..."
            )
    scoring = report.get("scoring")
    if scoring and isinstance(scoring, dict) and not scoring.get("error"):
        lines.append(
            f"Scoring:\n"
            f"Repo Score: {scoring.get('repo_score', '?')}/100\n"
            f"Risk Score: {scoring.get('risk_score', '?')}/100\n"
            f"Readiness: {scoring.get('readiness', '?')}%\n"
            f"Tech Debt: {scoring.get('tech_debt_hours', '?')}h (${scoring.get('tech_debt_money', '?')})"
        )
    roi = report.get("roi")
    if roi and isinstance(roi, dict) and not roi.get("error"):
        lines.append(
            f"ROI:\n"
            f"Стоимость техдолга: ${roi.get('tech_debt_cost', 0)}\n"
            f"Потенциальная экономия: ${roi.get('potential_savings', 0)}\n"
            f"ROI: {roi.get('roi_percent', 0)}%\n"
            f"Влияние на бизнес: {roi.get('business_impact', '')}"
        )
    return "\n\n".join(lines) or "Проблем не найдено"

def _get_audit_context(repo_path: str) -> str:
    try:
        trail = AuditTrail(repo_path)
        return trail.get_history_context()
    except Exception as e:
        logger.warning(f"Ошибка получения контекста аудита: {e}")
        return ""

def _save_audit_record(session_id: str, repo_path: str, summary: str, scoring: Dict) -> None:
    if not scoring or scoring.get("error"):
        return
    try:
        trail = AuditTrail(repo_path)
        trail.save(session_id, summary, scoring)
    except Exception as e:
        logger.warning(f"Ошибка сохранения аудита: {e}")

def query_yandex_gpt(prompt: str, context: str = "", max_tokens: int = 2000) -> str:
    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return "Ошибка: не настроен YANDEX_API_KEY"
    folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}
    max_context_len = 3000
    if len(context) > max_context_len:
        context = context[:max_context_len] + "\n... (контекст обрезан)"
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": max_tokens},
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
        return "Модель не вернула ответ."
    except Exception as e:
        logger.error(f"Ошибка YandexGPT: {e}")
        return f"Ошибка: {str(e)}"

async def run_analysis_async(session_id: str, repo_url: str, branch: Optional[str] = None):
    session = SESSIONS.get(session_id)
    if not session:
        return
    session["status"] = "in_progress"
    scanner = None
    try:
        commit_sha = None
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "ls-remote", repo_url, "HEAD",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            if proc.returncode == 0 and stdout:
                commit_sha = stdout.decode().split()[0]
        except Exception as e:
            logger.warning(f"Не удалось получить commit SHA: {e}")

        if commit_sha:
            cached = await cache_manager.get_cached_report(repo_url, branch or "main", commit_sha)
            if cached:
                logger.info(f"Кэш для {repo_url}")
                session["report"] = cached
                session["status"] = "done"
                return

        async def _analysis():
            nonlocal scanner
            comps = await asyncio.to_thread(create_components, repo_url)
            scanner = comps["scanner"]
            files = comps["files"]
            project_analyzer = comps["project_analyzer"]
            ast_analyzer = comps["ast_analyzer"]
            linter = comps["linter_runner"]

            git_stats = await asyncio.to_thread(lambda: GitAnalyzer(scanner.local_path).analyze())
            dep_stats = await asyncio.to_thread(lambda: DependencyAnalyzer(scanner.local_path).analyze())
            multi_lang_issues = await asyncio.to_thread(lambda: MultiLangAnalyzer().analyze(files))
            project_issues = await asyncio.to_thread(project_analyzer.analyze, files)

            ast_issues = {}
            for path, content in files.items():
                if path.endswith(".py"):
                    ast_issues[path] = await asyncio.to_thread(ast_analyzer.analyze, content)

            lint_issues = await asyncio.to_thread(linter.run_all, files)

            report = {
                "project_issues": project_issues,
                "ast_issues": ast_issues,
                "lint_issues": lint_issues,
                "multi_lang_issues": multi_lang_issues,
                "git_stats": git_stats,
                "dep_stats": dep_stats,
            }

            try:
                auditor = PrizolovAuditor()
                audit_results = await asyncio.to_thread(auditor.audit, files)
                serialized_audit = {}
                for level, issues in audit_results.items():
                    serialized_audit[level] = [
                        f"[{i.criticality.upper()}] {i.file}:{i.line} - {i.message}" for i in issues
                    ]
                report["audit"] = serialized_audit
            except Exception as e:
                report["audit"] = {"error": str(e)}

            try:
                ai = SemanticAI()
                context = report_to_summary(report)
                hist_ctx = _get_audit_context(scanner.local_path)
                if hist_ctx:
                    context = hist_ctx + "\n\n" + context
                report["semantic"] = {
                    "code_purpose": await asyncio.to_thread(ai.analyze_code_purpose, context),
                    "architecture_evaluation": await asyncio.to_thread(ai.evaluate_architecture, context),
                    "risk_assessment": await asyncio.to_thread(ai.assess_risk, context),
                    "value_estimation": await asyncio.to_thread(ai.estimate_value, context),
                }
            except Exception as e:
                report["semantic"] = {"error": str(e)}

            scoring = await asyncio.to_thread(lambda: ScoringEngine().compute(report))
            report["scoring"] = scoring

            all_issues = []
            if "audit" in report:
                for issues in report["audit"].values():
                    all_issues.extend(issues)
            triage = await asyncio.to_thread(lambda: SmartTriage().prioritize(all_issues))
            report["triage"] = triage

            roi = await asyncio.to_thread(lambda: ROICalculator(hourly_rate=50.0).compute(report, scoring))
            report["roi"] = roi

            return report, scanner, files

        report, scanner, files = await asyncio.wait_for(_analysis(), timeout=300)

        if commit_sha:
            await cache_manager.set_cached_report(repo_url, branch or "main", commit_sha, report)

        if LEADERBOARD is not None:
            primary_lang = "unknown"
            sem = report.get("semantic", {})
            if not sem.get("error"):
                techs = sem.get("code_purpose", {}).get("key_technologies", [])
                if techs:
                    primary_lang = techs[0]
            LEADERBOARD.add_result(repo_url, scoring, primary_lang)

        session["report"] = report
        session["files"] = files
        session["status"] = "done"

    except asyncio.TimeoutError:
        session["status"] = "error"
        session["error"] = "Таймаут 300 секунд"
        logger.error(f"Таймаут для {repo_url}")
    except Exception as e:
        session["status"] = "error"
        session["error"] = str(e)
        logger.exception("Ошибка в run_analysis_async")
    finally:
        if scanner:
            local_path = getattr(scanner, 'local_path', None)
            if isinstance(local_path, str) and os.path.exists(local_path):
                await asyncio.to_thread(shutil.rmtree, local_path, ignore_errors=True)

# ========== ЭНДПОИНТЫ ==========
@app.post("/scan")
async def start_scan(request: RepoRequest):
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "repo_url": str(request.repo_url),
        "branch": request.branch,
        "status": "pending",
        "report": None,
    }
    # Запускаем фоновую задачу напрямую через asyncio.create_task
    asyncio.create_task(run_analysis_async(session_id, str(request.repo_url), request.branch))
    return {"session_id": session_id}

@app.get("/status/{session_id}")
async def get_status(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    return {"session_id": session_id, "status": session["status"], "error": session.get("error")}

@app.get("/report/{session_id}")
async def get_report(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    if session.get("status") != "done":
        raise HTTPException(400, "Отчёт ещё не готов")
    return {"session_id": session_id, "report_summary": report_to_summary(session["report"])}

@app.get("/changes/{session_id}")
async def get_changes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    return {"files_changed": [], "patch_summary": "Для применения автофиксов нажмите кнопку."}

@app.post("/fix/{session_id}")
async def apply_fixes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session or session.get("status") != "done":
        raise HTTPException(404, "Отчёт не готов")
    engine = StepFixEngine()
    files = session.get("files", {})
    if not files:
        raise HTTPException(500, "Нет файлов")
    new_files = engine.format_all(files)
    session["fixed_files"] = new_files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in new_files.items():
            zf.writestr(path, content)
    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=repo_{session_id}_fixed.zip"})

@app.get("/recommendations/{session_id}")
async def get_recommendations(session_id: str):
    session = SESSIONS.get(session_id)
    if not session or session.get("status") != "done":
        raise HTTPException(404, "Отчёт не готов")
    report = session.get("report", {})
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
    for file, issues in report.get("multi_lang_issues", {}).items():
        for i in issues:
            all_issues.append(f"Lang ({file}): {i}")
    if not all_issues:
        return {"recommendations": "Ошибок нет"}
    sample_issues = all_issues[:10]
    prompt = "Дай краткие рекомендации по исправлению каждой из следующих проблем:\n" + "\n".join(sample_issues)
    recommendations = query_yandex_gpt(prompt, max_tokens=500)
    return {"recommendations": recommendations.strip()}

@app.post("/create_pr/{session_id}")
async def create_pr(session_id: str, req: CreatePRRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    files = session.get("fixed_files") or session.get("files")
    if not files:
        raise HTTPException(400, "Нет файлов")
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
        raise HTTPException(500, f"Ошибка: {str(e)}")

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
        raise HTTPException(400, "Нет файлов")
    new_files = mgr.apply_copyright(files, copyright_text=req.copyright_text, author=req.author,
                                   organization=req.organization, product=req.product, skip_existing=True)
    session["fixed_files"] = new_files
    return {"status": "applied"}

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
        raise HTTPException(404, "Сессия не найдена")
    context = ""
    if session.get("report"):
        context = report_to_summary(session["report"])
        try:
            scanner = RepositoryScanner(session["repo_url"])
            scanner.clone()
            hist_ctx = _get_audit_context(scanner.local_path)
            if hist_ctx:
                context = hist_ctx + "\n\n" + context
            shutil.rmtree(scanner.local_path, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Ошибка получения контекста: {e}")
    system_prompt = ROLE_PROMPTS.get(req.role, ROLE_PROMPTS["analyst"])
    prompt = f"{system_prompt}\n\nКонтекст отчёта:\n{context}\n\nВопрос пользователя: {req.message}"
    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return {"reply": "Ошибка: не настроен API-ключ YandexGPT."}
    folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}
    max_context_len = 2500
    if len(prompt) > max_context_len:
        prompt = f"{system_prompt}\n\nКонтекст отчёта (сокращён):\n{context[:max_context_len - len(system_prompt) - 50]}...\n\nВопрос пользователя: {req.message}"
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": 2000},
        "messages": [{"role": "system", "text": system_prompt}, {"role": "user", "text": prompt}]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        alternatives = data.get("result", {}).get("alternatives", [])
        if alternatives:
            return {"reply": alternatives[0].get("message", {}).get("text", "Нет ответа")}
        return {"reply": "Модель не вернула ответ."}
    except Exception as e:
        logger.error(f"Ошибка в /chat/advisor: {e}")
        return {"reply": f"Ошибка: {str(e)}"}

@app.post("/chat/arbitrage/{session_id}")
async def chat_arbitrage(session_id: str, req: ArbitrageRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    context = ""
    if session.get("report"):
        context = report_to_summary(session["report"])
    prompt = (
        "Предложи два варианта исправления проблемы: архитектурный и безопасностный. "
        "Оформи: АРХИТЕКТОР: <текст>\nБЕЗОПАСНИК: <текст>\n\n"
        f"Проблема: {req.message}\nКонтекст: {context}"
    )
    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return {"architect": "Ошибка API", "security": "Ошибка API"}
    folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {"Authorization": f"Api-Key {api_key}", "Content-Type": "application/json"}
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",
        "completionOptions": {"stream": False, "temperature": 0.7, "maxTokens": 2000},
        "messages": [{"role": "system", "text": "Ты — эксперт по анализу кода."}, {"role": "user", "text": prompt}]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        alternatives = data.get("result", {}).get("alternatives", [])
        if not alternatives:
            return {"architect": "Нет ответа", "security": "Нет ответа"}
        text = alternatives[0].get("message", {}).get("text", "")
        architect = ""
        security = ""
        for line in text.split('\n'):
            if line.startswith("АРХИТЕКТОР:"):
                architect = line.replace("АРХИТЕКТОР:", "").strip()
            elif line.startswith("БЕЗОПАСНИК:"):
                security = line.replace("БЕЗОПАСНИК:", "").strip()
        return {"architect": architect or "Нет", "security": security or "Нет"}
    except Exception as e:
        return {"architect": f"Ошибка: {str(e)}", "security": f"Ошибка: {str(e)}"}

@app.post("/chat/mentor/{session_id}")
async def chat_mentor(session_id: str, req: MentorRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    mentor = ContextualMentor()
    suggestion = mentor.suggest_fix(req.issue, req.file_context)
    return {"reply": suggestion}

@app.post("/publish/{session_id}")
async def publish_results(session_id: str, req: PublishRequest):
    session = SESSIONS.get(session_id)
    if not session or session.get("status") != "done":
        raise HTTPException(404, "Отчёт не готов")
    summary = report_to_summary(session["report"])
    publisher = RepoPublisher(req.github_token)
    repo_url = session["repo_url"]
    scoring = session["report"].get("scoring", {})
    score = scoring.get("repo_score", 0)
    body = f"## Отчёт\n\n**Репозиторий:** {repo_url}\n**Оценка:** {score}/100\n\n```\n{summary}\n```"
    if req.action == "issue":
        issue_url = publisher.publish_issue(repo_url, "Repo Validator Report", body)
        if issue_url:
            return {"status": "success", "url": issue_url}
        raise HTTPException(500, "Не удалось создать Issue")
    elif req.action == "label":
        label_name = f"repo-score-{int(score)}"
        color = "0e8a16" if score >= 80 else ("fbca04" if score >= 60 else "d93f0b")
        success = publisher.set_label(repo_url, label_name, color, f"Repo Score: {score}")
        if success:
            return {"status": "success", "label": label_name}
        raise HTTPException(500, "Не удалось установить метку")
    raise HTTPException(400, "Неверный action")

@app.post("/autonomous-fix/{session_id}")
async def autonomous_fix(session_id: str, req: AutonomousFixRequest):
    session = SESSIONS.get(session_id)
    if not session or session.get("status") != "done":
        raise HTTPException(404, "Отчёт не готов")
    engine = StepFixEngine()
    files = session.get("files", {})
    if not files:
        raise HTTPException(500, "Нет файлов")
    new_files = engine.format_all(files)
    if req.apply_copyright:
        mgr = CopyrightManager()
        new_files = mgr.apply_copyright(new_files, author=req.copyright_author,
                                        organization=req.copyright_organization,
                                        product=req.copyright_product, skip_existing=True)
    session["fixed_files"] = new_files
    github = GitHubIntegration(req.github_token)
    summary = report_to_summary(session.get("report", {}))
    body = f"## Autonomous Fix\n```\n{summary}\n```"
    try:
        pr_url = github.create_pr(
            repo_url=session["repo_url"],
            files=new_files,
            base_branch=req.base_branch,
            title=req.title,
            body=body
        )
        if not pr_url:
            raise HTTPException(500, "Не удалось создать PR")
        return {"status": "success", "pull_request_url": pr_url}
    except Exception as e:
        raise HTTPException(500, f"Ошибка: {str(e)}")

@app.get("/leaderboard")
async def get_leaderboard(sort_by: str = "repo_score", language: str = None, limit: int = 10):
    if LEADERBOARD is None:
        return {"error": "Лидерборд недоступен"}
    return LEADERBOARD.get_top(limit=limit, sort_by=sort_by, language=language)

@app.post("/chat/{session_id}")
async def chat(session_id: str, req: ChatRequest):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    context = ""
    if session.get("report"):
        context = report_to_summary(session["report"])
        try:
            scanner = RepositoryScanner(session["repo_url"])
            scanner.clone()
            hist_ctx = _get_audit_context(scanner.local_path)
            if hist_ctx:
                context = hist_ctx + "\n\n" + context
            shutil.rmtree(scanner.local_path, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Ошибка: {e}")
    reply = query_yandex_gpt(req.message, context)
    return {"reply": reply}

@app.get("/download/{session_id}")
async def download_repo(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(404, "Сессия не найдена")
    files = session.get("fixed_files") or session.get("files", {})
    if not files:
        try:
            scanner = RepositoryScanner(session["repo_url"])
            scanner.clone()
            files = scanner.scan_repository()
            shutil.rmtree(scanner.local_path, ignore_errors=True)
        except Exception as e:
            raise HTTPException(500, f"Не удалось получить файлы: {e}")
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    zip_buffer.seek(0)
    return StreamingResponse(zip_buffer, media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=repo_{session_id}.zip"})

@app.get("/savings")
async def get_savings():
    return SAVINGS

@app.post("/savings/update")
async def update_savings(req: SavingsUpdateRequest):
    SAVINGS["fixed"] += req.fixed
    SAVINGS["hours"] += req.hours
    SAVINGS["money"] += req.money
    return SAVINGS

@app.on_event("startup")
async def startup():
    await cache_manager.connect()
    logger.info("Кэш-менеджер инициализирован")

@app.on_event("shutdown")
async def shutdown():
    await cache_manager.close()
    tmp = "/tmp/repo_scan"
    if os.path.exists(tmp):
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)

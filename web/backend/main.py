import os
import uuid
import json
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from openai import OpenAI
from dotenv import load_dotenv

from core.platform_detector import PlatformDetector
from core.zip_downloader import ZipDownloader
from core.zip_extractor import ZipExtractor
from core.repository_scanner import RepositoryScanner, FileEntry
from core.zip_builder import ZipBuilder
from core.report_generator import ReportGenerator
from core.fix_engine import FixEngine
from core.project_detector import ProjectDetector
from core.structure_analyzer import StructureAnalyzer
from core.dependency_analyzer import DependencyAnalyzer
from core.legal_compliance import LegalComplianceOfficer
from core.quality_score import QualityScoreEngine
from core.optimization_loop import OptimizationLoop, OptimizationResult
from core.cicd_analyzer import CICDAnalyzer, CICDReport

# -----------------------------
# APP INIT
# -----------------------------

app = FastAPI(
    title="Repo Validator 2.0",
    description="ZIP-based universal repository analyzer",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# GLOBAL STATE
# -----------------------------

SESSIONS: Dict[str, Dict[str, Any]] = {}

load_dotenv()


def _resolve_openai_api_key(request: Optional[Request] = None, x_api_key: Optional[str] = None) -> str:
    """
    Приоритет:
    1) Ключ из заголовка X-API-Key (фронтенд)
    2) Переменная окружения OPENAI_API_KEY
    3) .env (через load_dotenv уже подхвачен)
    """
    # 1. Явно переданный заголовок
    if x_api_key:
        return x_api_key

    # 2. Попробовать достать из Request (если есть)
    if request is not None:
        header_key = request.headers.get("X-API-Key")
        if header_key:
            return header_key

    # 3. Переменная окружения / .env
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key

    raise HTTPException(
        status_code=500,
        detail="OpenAI API key not found. Provide X-API-Key header or set OPENAI_API_KEY env/.env."
    )


def _get_openai_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


# -----------------------------
# API MODELS
# -----------------------------

class AnalyzeRequest(BaseModel):
    repo_url: str
    branch: str | None = None


class FileInfo(BaseModel):
    rel_path: str
    size: int
    is_text: bool


class AnalyzeResponse(BaseModel):
    session_id: str
    platform: str
    owner: str
    repo: str
    branch: str
    project_type: str
    project_tags: list[str]
    total_files: int
    files: list[FileInfo]
    report_summary: str
    quality_score: int
    cicd: dict
    optimization_applied: list[str]
    optimization_auto_installed: list[dict]
    optimization_user_selected: list[dict]
    optimization_recommended: list[dict]
    changes: list[str]


class ReportResponse(BaseModel):
    session_id: str
    platform: str
    owner: str
    repo: str
    branch: str
    project_type: str
    project_tags: list[str]
    report_summary: str
    quality_score: int
    cicd: dict
    optimization_applied: list[str]
    optimization_auto_installed: list[dict]
    optimization_user_selected: list[dict]
    optimization_recommended: list[dict]
    changes: list[str]


class InstallToolsRequest(BaseModel):
    session_id: str
    tools: list[str]


class InstallToolsResponse(BaseModel):
    status: str
    installed: list[dict]
    report_summary: str
    optimization_applied: list[str]
    optimization_auto_installed: list[dict]
    optimization_user_selected: list[dict]
    optimization_recommended: list[dict]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# -----------------------------
# MAIN ANALYSIS ENDPOINT
# -----------------------------

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_repo(request: AnalyzeRequest):
    detector = PlatformDetector()
    info = detector.detect(request.repo_url, request.branch)

    downloader = ZipDownloader()
    zip_path = downloader.download_to_tempfile(info.zip_url)

    extractor = ZipExtractor()
    root_dir = extractor.extract_to_tempdir(zip_path)

    scanner = RepositoryScanner(root_dir)
    files: list[FileEntry] = scanner.scan()

    project_detector = ProjectDetector()
    project_type = project_detector.detect(files)

    dependency_analyzer = DependencyAnalyzer()
    deps = dependency_analyzer.analyze(root_dir, files)

    fixer = FixEngine()
    changes = fixer.apply_fixes(root_dir, files, project_type, deps)

    files = scanner.scan()

    structure_analyzer = StructureAnalyzer()
    structure = structure_analyzer.analyze(files)

    legal_officer = LegalComplianceOfficer()
    legal_report = legal_officer.analyze(root_dir, files)

    quality_engine = QualityScoreEngine()
    quality_score = quality_engine.calculate(files, structure, deps, legal_report)

    cicd_analyzer = CICDAnalyzer()
    cicd = cicd_analyzer.analyze(files)

    optimizer = OptimizationLoop()
    optimization = optimizer.optimize(structure, deps, legal_report, quality_score, cicd)

    reporter = ReportGenerator()
    report = reporter.build_report(
        files, structure, deps, legal_report, quality_score, cicd, optimization
    )

    builder = ZipBuilder()
    fixed_zip_path = builder.build_zip_from_dir(root_dir)

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = {
        "root_dir": root_dir,
        "fixed_zip": fixed_zip_path,
        "meta": {
            "platform": info.platform,
            "owner": info.owner,
            "repo": info.name,
            "branch": info.branch,
            "project_type": project_type.name,
            "project_tags": project_type.tags,
        },
        "changes": changes,
        "report": report.summary,
        "quality_score": quality_score.score,
        "optimization": optimization,
        "cicd": cicd,
        # контекст для чата
        "chat_history": [],
        "installed_tools": [],  # будет синхронизироваться с optimization.user_selected_tools
    }

    return AnalyzeResponse(
        session_id=session_id,
        platform=info.platform,
        owner=info.owner,
        repo=info.name,
        branch=info.branch,
        project_type=project_type.name,
        project_tags=project_type.tags,
        total_files=report.total_files,
        files=[
            FileInfo(rel_path=f.rel_path, size=f.size, is_text=f.is_text)
            for f in files
        ],
        report_summary=report.summary,
        quality_score=quality_score.score,
        cicd=cicd.__dict__,
        optimization_applied=optimization.applied,
        optimization_auto_installed=optimization.auto_installed_tools,
        optimization_user_selected=optimization.user_selected_tools,
        optimization_recommended=optimization.recommended_tools,
        changes=changes,
    )
# -----------------------------
# INSTALL TOOLS ENDPOINT
# -----------------------------

@app.post("/install_tools", response_model=InstallToolsResponse)
def install_tools(request: InstallToolsRequest):
    session = SESSIONS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    optimization: OptimizationResult = session.get("optimization")
    if not optimization:
        raise HTTPException(status_code=400, detail="Оптимизация не найдена")

    recommended_by_name = {
        t["name"]: t for t in optimization.recommended_tools
    }

    installed = []

    for name in request.tools:
        tool = recommended_by_name.get(name)
        if not tool:
            continue

        # Добавляем в user_selected_tools
        if tool not in optimization.user_selected_tools:
            optimization.user_selected_tools.append(tool)

        # Удаляем из recommended
        optimization.recommended_tools = [
            t for t in optimization.recommended_tools if t["name"] != name
        ]

        installed.append(tool)

    # Синхронизируем сессии
    session["optimization"] = optimization
    session["installed_tools"] = optimization.user_selected_tools

    return InstallToolsResponse(
        status="ok",
        installed=installed,
        report_summary=session.get("report", ""),
        optimization_applied=optimization.applied,
        optimization_auto_installed=optimization.auto_installed_tools,
        optimization_user_selected=optimization.user_selected_tools,
        optimization_recommended=optimization.recommended_tools,
    )


# -----------------------------
# DOWNLOAD FIXED ZIP
# -----------------------------

@app.get("/download/{session_id}")
def download_fixed_zip(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    zip_path = session.get("fixed_zip")
    if not zip_path:
        raise HTTPException(status_code=404, detail="ZIP не найден")

    meta = session.get("meta", {})
    repo_name = meta.get("repo", "repo")

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{repo_name}_fixed.zip",
    )


# -----------------------------
# REPORT ENDPOINT
# -----------------------------

@app.get("/report/{session_id}", response_model=ReportResponse)
def get_report(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    meta = session.get("meta", {})
    optimization: OptimizationResult = session.get("optimization")
    cicd: CICDReport = session.get("cicd")

    return ReportResponse(
        session_id=session_id,
        platform=meta.get("platform", "unknown"),
        owner=meta.get("owner", ""),
        repo=meta.get("repo", ""),
        branch=meta.get("branch", ""),
        project_type=meta.get("project_type", "unknown"),
        project_tags=meta.get("project_tags", []),
        report_summary=session.get("report", ""),
        quality_score=session.get("quality_score", 0),
        cicd=cicd.__dict__,
        optimization_applied=optimization.applied,
        optimization_auto_installed=optimization.auto_installed_tools,
        optimization_user_selected=optimization.user_selected_tools,
        optimization_recommended=optimization.recommended_tools,
        changes=session.get("changes", []),
    )


# -----------------------------
# CHANGES ENDPOINT
# -----------------------------

@app.get("/changes/{session_id}")
def get_changes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    return session.get("changes", [])


# ============================================================
# =====================  CHAT ENDPOINT  =======================
# ============================================================

@app.post("/chat/{session_id}", response_model=ChatResponse)
async def chat_with_ai(
    session_id: str,
    request: ChatRequest,
    fastapi_request: Request,
    x_api_key: Optional[str] = Header(None)
):
    """
    Новый DevOps‑чат:
    - использует OpenAI
    - получает весь контекст анализа
    - знает все инструменты
    - знает CICD
    - хранит историю
    - отвечает как DevOps Engineer
    """

    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")

    # 1. Получаем API‑ключ (универсальный механизм)
    api_key = _resolve_openai_api_key(fastapi_request, x_api_key)
    client = _get_openai_client(api_key)

    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    # 2. Собираем контекст анализа
    optimization: OptimizationResult = session.get("optimization")
    cicd: CICDReport = session.get("cicd")

    context = {
        "report_summary": session.get("report", ""),
        "changes": session.get("changes", []),
        "quality_score": session.get("quality_score", 0),
        "cicd": cicd.__dict__ if cicd else {},
        "recommended_tools": optimization.recommended_tools,
        "installed_tools": optimization.user_selected_tools,
        "auto_installed_tools": optimization.auto_installed_tools,
        "applied_optimizations": optimization.applied,
        "project_type": session["meta"].get("project_type"),
        "project_tags": session["meta"].get("project_tags"),
    }

    # 3. System prompt (будет продолжен в части 3/3)
    system_prompt = f"""
Ты — Senior DevOps Engineer и эксперт по CI/CD, архитектуре, качеству кода и оптимизации проектов.

Ты работаешь внутри системы Repo Validator 2.0 и отвечаешь на вопросы пользователя строго на основе данных анализа.

Вот данные анализа проекта:

SUMMARY:
{context["report_summary"]}

CI/CD:
{json.dumps(context["cicd"], indent=2, ensure_ascii=False)}

РЕКОМЕНДОВАННЫЕ ИНСТРУМЕНТЫ:
{json.dumps(context["recommended_tools"], indent=2, ensure_ascii=False)}

УСТАНОВЛЕННЫЕ ИНСТРУМЕНТЫ:
{json.dumps(context["installed_tools"], indent=2, ensure_ascii=False)}

ИЗМЕНЕНИЯ:
{json.dumps(context["changes"], indent=2, ensure_ascii=False)}

Ты должен:
- давать инженерные ответы
- объяснять, зачем нужен каждый инструмент
- учитывать CICDConfigurator и любые другие инструменты
- помнить историю диалога
- не придумывать данные, которых нет
- давать рекомендации по улучшению проекта
"""

    # Продолжение — в части 3/3
    # Здесь будет вызов OpenAI, история чата, формирование ответа

    # Временно возвращаем заглушку, чтобы файл был валиден
    return ChatResponse(reply="Продолжение чата будет в части 3/3")
    # -----------------------------
    # ПРОДОЛЖЕНИЕ ЧАТА (часть 3/3)
    # -----------------------------

    # 4. История чата
    history = session.get("chat_history", [])

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Добавляем историю
    for msg in history:
        messages.append(msg)

    # Добавляем новое сообщение пользователя
    messages.append({"role": "user", "content": user_message})

    # 5. Вызов OpenAI
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
        )
        reply = completion.choices[0].message["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {str(e)}")

    # 6. Сохраняем историю
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    session["chat_history"] = history

    return ChatResponse(reply=reply)


# -----------------------------
# HEALTH
# -----------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

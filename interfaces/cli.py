import argparse
import os
import yaml

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


# ---------------------------------------------------------
# Загрузка конфига
# ---------------------------------------------------------
def load_agent_config():
    config_path = os.path.join("configs", "agent_config.yaml")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------
# Определение режима работы
# ---------------------------------------------------------
def resolve_mode(cli_mode: str | None, config: dict) -> str:
    """
    Приоритет:
    1) CLI (--mode)
    2) config.yaml
    3) default = step
    """
    if cli_mode in ("step", "auto"):
        return cli_mode

    if isinstance(config.get("mode"), str) and config["mode"] in ("step", "auto"):
        return config["mode"]

    return "step"


# ---------------------------------------------------------
# Главная CLI-функция
# ---------------------------------------------------------
def run_cli():
    parser = argparse.ArgumentParser(description="Repo Validator Agent CLI")
    parser.add_argument("repo_url", help="Ссылка на GitHub-репозиторий")

    parser.add_argument(
        "--mode",
        choices=["step", "auto"],
        help="Режим работы: step (по умолчанию) или auto"
    )

    args = parser.parse_args()

    # Загружаем конфиг
    config = load_agent_config()

    # Определяем режим
    mode = resolve_mode(args.mode, config)
    auto_mode = mode == "auto"

    print(f"[CLI] Режим работы: {mode}")

    repo_url = args.repo_url

    # -----------------------------------------------------
    # Инициализация компонентов
    # -----------------------------------------------------
    github = GitHubConnector(repo_url)
    scanner = RepositoryScanner(github)
    file_analyzer = FileAnalyzer()
    project_analyzer = ProjectAnalyzer()
    copyright_manager = CopyrightManager()
    rewriter = FullFileRewriter(copyright_manager)

    output_dir = config.get("output_directory", "fixed_files")
    report_generator = ReportGenerator(output_dir)

    metrics = ProgressMetrics()
    shield = AntiHallucinationShield()
    legal = LegalComplianceOfficer()

    step_fix = StepFixEngine(
        rewriter=rewriter,
        report_generator=report_generator,
        metrics=metrics,
        shield=shield,
        legal=legal,
        auto_mode=auto_mode
    )

    # -----------------------------------------------------
    # Сканирование репозитория
    # -----------------------------------------------------
    print("[CLI] Сканирование репозитория...")
    files = scanner.scan_repository()

    # -----------------------------------------------------
    # Анализ файлов
    # -----------------------------------------------------
    print("[CLI] Анализ файлов...")
    file_issues = {}

    for file_path, content in files.items():
        issues = file_analyzer.analyze_file(file_path, content)
        file_issues[file_path] = issues
        metrics.increment_files_analyzed()

    # -----------------------------------------------------
    # Анализ проекта
    # -----------------------------------------------------
    print("[CLI] Анализ структуры проекта...")
    project_issues = project_analyzer.analyze_project(files, file_issues)

    if project_issues:
        print("\n[bold yellow]Проблемы проекта:[/bold yellow]")
        for issue in project_issues:
            print(f" - {issue}")

    # -----------------------------------------------------
    # Исправление файлов
    # -----------------------------------------------------
    print("\n[CLI] Исправление файлов...")
    for file_path, issues in file_issues.items():
        if issues:
            step_fix.process_file(file_path, files[file_path], issues)

    # -----------------------------------------------------
    # Финальный отчёт
    # -----------------------------------------------------
    print("\n[CLI] Генерация отчёта...")
    report_generator.generate_final_report(file_issues, project_issues, metrics)

    print("\n[bold green]Готово![/bold green]")

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


def main():
    repo_url = input("Введите ссылку на GitHub-репозиторий: ").strip()

    # Инициализация базовых компонентов
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

    # 1. Сканирование репозитория
    files = scanner.scan_repository()

    # 2. Анализ файлов
    file_issues = {}
    for file_path, content in files.items():
        issues = file_analyzer.analyze_file(file_path, content)
        file_issues[file_path] = issues
        metrics.increment_files_analyzed()

    # 3. Анализ проекта целиком
    project_issues = project_analyzer.analyze_project(files, file_issues)

    # 4. Пошаговый режим исправлений
    for file_path, issues in file_issues.items():
        if not issues:
            continue
        step_fix.process_file(file_path, files[file_path], issues)

    # 5. Финальный отчёт
    report_generator.generate_final_report(file_issues, project_issues, metrics)


if __name__ == "__main__":
    main()

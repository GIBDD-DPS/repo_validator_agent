from dataclasses import dataclass
from typing import List

from core.repository_scanner import FileEntry


@dataclass
class CICDReport:
    has_ci: bool
    providers: List[str]
    has_tests: bool
    has_lint: bool
    has_build: bool
    has_deploy: bool
    has_cache: bool
    issues: List[str]


class CICDAnalyzer:
    """
    Анализ CI/CD конфигураций:
    - GitHub Actions
    - GitLab CI
    - Jenkins
    - Azure Pipelines
    - Bitbucket Pipelines
    """

    def analyze(self, files: List[FileEntry]) -> CICDReport:
        providers = []
        has_tests = False
        has_lint = False
        has_build = False
        has_deploy = False
        has_cache = False

        ci_files = [f for f in files if ".yml" in f.rel_path.lower() or "jenkins" in f.rel_path.lower()]

        if not ci_files:
            return CICDReport(
                has_ci=False,
                providers=[],
                has_tests=False,
                has_lint=False,
                has_build=False,
                has_deploy=False,
                has_cache=False,
                issues=["CI/CD не обнаружен"]
            )

        for f in ci_files:
            path = f.rel_path.lower()

            if ".github/workflows" in path:
                providers.append("GitHub Actions")
            if "gitlab-ci" in path:
                providers.append("GitLab CI")
            if "azure-pipelines" in path:
                providers.append("Azure Pipelines")
            if "jenkins" in path:
                providers.append("Jenkins")
            if "bitbucket" in path:
                providers.append("Bitbucket Pipelines")

            try:
                with open(f.path, "r", encoding="utf-8", errors="ignore") as src:
                    text = src.read().lower()

                    if "pytest" in text or "unittest" in text:
                        has_tests = True
                    if "flake8" in text or "pylint" in text or "ruff" in text:
                        has_lint = True
                    if "build" in text or "setup.py" in text:
                        has_build = True
                    if "deploy" in text or "release" in text:
                        has_deploy = True
                    if "cache" in text:
                        has_cache = True

            except Exception:
                continue

        issues = []

        if not has_tests:
            issues.append("В CI нет тестов")
        if not has_lint:
            issues.append("В CI нет линтеров")
        if not has_build:
            issues.append("В CI нет сборки")
        if not has_deploy:
            issues.append("В CI нет деплоя")
        if not has_cache:
            issues.append("В CI нет кеширования")

        return CICDReport(
            has_ci=True,
            providers=providers,
            has_tests=has_tests,
            has_lint=has_lint,
            has_build=has_build,
            has_deploy=has_deploy,
            has_cache=has_cache,
            issues=issues
        )

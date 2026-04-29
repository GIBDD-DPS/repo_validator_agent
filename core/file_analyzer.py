from typing import List
from core.ast_analyzer import ASTAnalyzer
from core.linter_runner import LinterRunner


class FileAnalyzer:
    """
    Анализирует отдельные файлы.
    Находит:
    - пустые файлы
    - TODO
    - AST-проблемы (через ASTAnalyzer)
    - проблемы линтеров (flake8, pylint, bandit)
    """

    def __init__(self):
        self.ast = ASTAnalyzer()
        self.linters = LinterRunner()

    def analyze_file(self, file_path: str, content: str) -> List[str]:
        issues = []

        # -----------------------------
        # 1. Пустой файл
        # -----------------------------
        if not content.strip():
            issues.append("Файл пустой")
            return issues  # нет смысла анализировать дальше

        # -----------------------------
        # 2. TODO
        # -----------------------------
        if "TODO" in content:
            issues.append("Найден TODO — требуется доработка")

        # -----------------------------
        # 3. AST-анализ (только Python)
        # -----------------------------
        if file_path.endswith(".py"):
            ast_issues = self.ast.analyze(file_path, content)
            issues.extend(ast_issues)

        # -----------------------------
        # 4. Линтеры (flake8, pylint, bandit)
        # -----------------------------
        if file_path.endswith(".py"):
            linter_issues = self.linters.analyze(file_path, content)
            issues.extend(linter_issues)

        return issues


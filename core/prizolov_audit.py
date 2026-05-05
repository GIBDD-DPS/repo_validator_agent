# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Пятиуровневый аудит Prizolov Lab: гигиена кода, архитектура, безопасность,
производительность, документированность.
"""
import ast
import re
from typing import Dict, List


class AuditIssue:
    """Одна проблема, найденная аудитом."""
    def __init__(self, level: str, file: str, line: int, message: str, criticality: str = "medium"):
        self.level = level
        self.file = file
        self.line = line
        self.message = message
        self.criticality = criticality


class PrizolovAuditor:
    """Главный аудитор, запускает все уровни."""

    def __init__(self):
        self.issues: List[AuditIssue] = []

    def audit(self, files: Dict[str, str]) -> Dict[str, List[AuditIssue]]:
        """
        Принимает словарь {путь: содержимое} и возвращает словарь
        с результатами по уровням: {"architecture": [...], "security": [...], ...}
        """
        self.issues = []
        results = {
            "architecture": [],
            "security": [],
            "performance": [],
            "documentation": []
        }

        # Уровень 2: Архитектура (циклические импорты)
        arch_checker = ArchitectureChecker()
        arch_issues = arch_checker.check(files)
        results["architecture"] = arch_issues
        self.issues.extend(arch_issues)

        # Уровень 3: Безопасность (секреты, ключи)
        sec_checker = SecurityChecker()
        sec_issues = sec_checker.check(files)
        results["security"] = sec_issues
        self.issues.extend(sec_issues)

        # Уровень 4: Производительность
        perf_checker = PerformanceChecker()
        perf_issues = perf_checker.check(files)
        results["performance"] = perf_issues
        self.issues.extend(perf_issues)

        # Уровень 5: Документированность
        doc_checker = DocumentationChecker()
        doc_issues = doc_checker.check(files)
        results["documentation"] = doc_issues
        self.issues.extend(doc_issues)

        return results

    def get_all_issues(self) -> List[AuditIssue]:
        return self.issues


class ArchitectureChecker:
    """Проверяет архитектурные проблемы: циклические импорты, сильную связанность."""

    def check(self, files: Dict[str, str]) -> List[AuditIssue]:
        issues = []
        import_graph = {}  # module -> set of imported modules
        for path, content in files.items():
            if not path.endswith('.py'):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            module_name = path.replace('/', '.').replace('.py', '')
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
            if imports:
                import_graph[module_name] = imports

        # Проверка на циклические зависимости
        visited = set()
        def has_cycle(node, path_set):
            if node in path_set:
                return True
            if node in visited:
                return False
            visited.add(node)
            path_set.add(node)
            for dep in import_graph.get(node, set()):
                if has_cycle(dep, path_set):
                    return True
            path_set.remove(node)
            return False

        for module in import_graph:
            if has_cycle(module, set()):
                issues.append(AuditIssue(
                    "architecture", module, 0,
                    f"Обнаружен циклический импорт с участием модуля {module}",
                    "high"
                ))
        return issues


class SecurityChecker:
    """Ищет потенциальные утечки секретов: ключи, токены, пароли."""

    SECRET_PATTERNS = [
        (re.compile(r'(?i)(api[_\-]?key|apikey|secret|token|password|passwd)\s*[:=]\s*["\'][^"\']+["\']'), "high"),
        (re.compile(r'(?i)(-----BEGIN\s*(RSA|DSA|EC|PGP|OPENSSH)\s*PRIVATE\s*KEY-----)'), "critical"),
        (re.compile(r'(?i)(eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)'), "medium"),  # JWT
    ]

    def check(self, files: Dict[str, str]) -> List[AuditIssue]:
        issues = []
        for path, content in files.items():
            if not any(path.endswith(ext) for ext in ['.py', '.js', '.ts', '.yml', '.yaml', '.json', '.txt', '.cfg', '.ini', '.sh', '.bash']):
                continue
            for i, line in enumerate(content.splitlines(), start=1):
                for pattern, criticality in self.SECRET_PATTERNS:
                    if pattern.search(line):
                        issues.append(AuditIssue(
                            "security", path, i,
                            f"Найден потенциальный секрет: {line.strip()[:80]}...",
                            criticality
                        ))
        return issues


class PerformanceChecker:
    """Проверяет неэффективные конструкции."""

    ANTI_PATTERNS = [
        (re.compile(r'range\(len\('), "Используйте enumerate() вместо range(len(...))"),
        (re.compile(r'\.keys\(\)\s*in'), "Используйте 'in dict' вместо '.keys() in'"),
        (re.compile(r'for\s+.*\s+in\s+.*\.keys\(\)'), "Используйте 'for key in dict' вместо 'for key in dict.keys()'"),
    ]

    def check(self, files: Dict[str, str]) -> List[AuditIssue]:
        issues = []
        for path, content in files.items():
            if not path.endswith('.py'):
                continue
            for i, line in enumerate(content.splitlines(), start=1):
                for pattern, msg in self.ANTI_PATTERNS:
                    if pattern.search(line):
                        issues.append(AuditIssue(
                            "performance", path, i, msg, "low"
                        ))
        return issues


class DocumentationChecker:
    """Оценивает наличие документации."""

    def check(self, files: Dict[str, str]) -> List[AuditIssue]:
        issues = []
        for path, content in files.items():
            if not path.endswith('.py'):
                continue
            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        issues.append(AuditIssue(
                            "documentation", path, node.lineno,
                            f"Отсутствует docstring у {node.name}",
                            "medium"
                        ))
        return issues

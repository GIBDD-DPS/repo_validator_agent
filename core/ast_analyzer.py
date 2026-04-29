import ast
from typing import List


class ASTAnalyzer:
    """
    Анализирует Python-файлы через AST.
    Находит:
    - неиспользуемые импорты
    - пустые функции
    - функции без docstring
    - слишком длинные функции
    - классы без методов
    - переменные, объявленные но не использованные
    """

    def analyze(self, file_path: str, content: str) -> List[str]:
        issues = []

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Синтаксическая ошибка: {e}")
            return issues

        # --- 1. Неиспользуемые импорты ---
        issues.extend(self._check_unused_imports(tree))

        # --- 2. Пустые функции ---
        issues.extend(self._check_empty_functions(tree))

        # --- 3. Функции без docstring ---
        issues.extend(self._check_missing_docstrings(tree))

        # --- 4. Слишком длинные функции ---
        issues.extend(self._check_long_functions(tree))

        # --- 5. Классы без методов ---
        issues.extend(self._check_empty_classes(tree))

        # --- 6. Неиспользуемые переменные ---
        issues.extend(self._check_unused_variables(tree))

        return issues

    # --------------------------
    # Правило 1: неиспользуемые импорты
    # --------------------------
    def _check_unused_imports(self, tree):
        issues = []
        imported = set()
        used = set()

        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    imported.add(alias.asname or alias.name.split('.')[0])

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    imported.add(alias.asname or alias.name)

            def visit_Name(self, node):
                used.add(node.id)

        ImportVisitor().visit(tree)

        unused = imported - used
        for name in unused:
            issues.append(f"Неиспользуемый импорт: {name}")

        return issues

    # --------------------------
    # Правило 2: пустые функции
    # --------------------------
    def _check_empty_functions(self, tree):
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    issues.append(f"Пустая функция: {node.name}")
        return issues

    # --------------------------
    # Правило 3: функции без docstring
    # --------------------------
    def _check_missing_docstrings(self, tree):
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if ast.get_docstring(node) is None:
                    issues.append(f"Функция без docstring: {node.name}")
        return issues

    # --------------------------
    # Правило 4: слишком длинные функции
    # --------------------------
    def _check_long_functions(self, tree, max_len=50):
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, "body"):
                    length = len(node.body)
                    if length > max_len:
                        issues.append(f"Слишком длинная функция ({length} строк): {node.name}")
        return issues

    # --------------------------
    # Правило 5: классы без методов
    # --------------------------
    def _check_empty_classes(self, tree):
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if not methods:
                    issues.append(f"Класс без методов: {node.name}")
        return issues

    # --------------------------
    # Правило 6: неиспользуемые переменные
    # --------------------------
    def _check_unused_variables(self, tree):
        issues = []
        assigned = set()
        used = set()

        class VarVisitor(ast.NodeVisitor):
            def visit_Assign(self, node):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned.add(target.id)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    used.add(node.id)

        VarVisitor().visit(tree)

        unused = assigned - used
        for var in unused:
            issues.append(f"Неиспользуемая переменная: {var}")

        return issues

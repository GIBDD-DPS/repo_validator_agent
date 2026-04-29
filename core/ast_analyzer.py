import ast
from typing import List, Dict

class ASTAnalyzer:
    """Анализирует Python-код через AST для поиска проблем."""

    def analyze(self, code: str) -> List[str]:
        """
        Принимает исходный код, возвращает список найденных проблем.
        """
        issues = []
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Синтаксическая ошибка: {e}")
            return issues

        # Проверка на неиспользуемые переменные
        issues.extend(self._check_unused_variables(tree))

        # Проверка на "опасные" вызовы (eval, exec)
        issues.extend(self._check_dangerous_calls(tree))

        return issues

    # ============================================================
    # Вспомогательные методы
    # ============================================================

    def _check_unused_variables(self, tree: ast.AST) -> List[str]:
        """Находит переменные, которым присвоили значение, но не использовали."""
        assigned = set()
        used = set()

        class VarVisitor(ast.NodeVisitor):
            def visit_Assign(self, node):
                for target in node.targets:
                    # ✅ ИСПРАВЛЕНО: проверяем, что цель – простое имя (a = 1)
                    if isinstance(target, ast.Name):
                        assigned.add(target.id)
                    # Игнорируем кортежи, списки, атрибуты (a, b = ..., obj.x = ...)
                self.generic_visit(node)

            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load):
                    used.add(node.id)
                self.generic_visit(node)

        visitor = VarVisitor()
        visitor.visit(tree)

        unused = assigned - used
        return [f"Переменная '{v}' присвоена, но не используется" for v in unused]

    def _check_dangerous_calls(self, tree: ast.AST) -> List[str]:
        """Проверяет использование eval/exec."""
        issues = []

        class DangerVisitor(ast.NodeVisitor):
            def visit_Call(self, node):
                # Получаем имя функции, если это простой вызов
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ('eval', 'exec'):
                    issues.append(f"Использование опасной функции: {func_name}()")
                self.generic_visit(node)

        DangerVisitor().visit(tree)
        return issues

import ast
import re
from typing import List
from core.copyright_manager import CopyrightManager


class FullFileRewriter:
    """
    Переписывает файл с учётом:
    - AST-проблем
    - линтер-проблем
    - отсутствующих docstring
    - неиспользуемых импортов
    - пустых функций
    - слишком длинных функций (добавляет TODO)
    - форматирования (псевдо-Black)
    """

    def __init__(self, copyright_manager: CopyrightManager):
        self.copyright = copyright_manager

    # ---------------------------------------------------------
    # Главный метод
    # ---------------------------------------------------------
    def rewrite_file(self, file_path: str, content: str, issues: List[str]) -> str:
        """
        Переписывает файл на основе списка проблем.
        """
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Если файл не парсится — просто добавляем заголовок
            return self._finalize(content)

        # 1. Удаляем неиспользуемые импорты
        content = self._remove_unused_imports(content, issues)

        # 2. Добавляем docstring в функции, где его нет
        content = self._add_missing_docstrings(content, issues)

        # 3. Добавляем TODO в слишком длинные функции
        content = self._mark_long_functions(content, issues)

        # 4. Удаляем пустые функции
        content = self._remove_empty_functions(content, issues)

        # 5. Форматируем код (псевдо-Black)
        content = self._format_code(content)

        # 6. Добавляем заголовок авторских прав
        content = self._finalize(content)

        return content

    # ---------------------------------------------------------
    # Удаление неиспользуемых импортов
    # ---------------------------------------------------------
    def _remove_unused_imports(self, content: str, issues: List[str]) -> str:
        unused = [i for i in issues if i.startswith("Неиспользуемый импорт")]
        if not unused:
            return content

        lines = content.splitlines()
        new_lines = []

        unused_names = {i.split(":")[1].strip() for i in unused}

        for line in lines:
            if line.strip().startswith("import") or line.strip().startswith("from"):
                if any(name in line for name in unused_names):
                    continue
            new_lines.append(line)

        return "\n".join(new_lines)

    # ---------------------------------------------------------
    # Добавление docstring в функции
    # ---------------------------------------------------------
    def _add_missing_docstrings(self, content: str, issues: List[str]) -> str:
        missing = [i for i in issues if i.startswith("Функция без docstring")]
        if not missing:
            return content

        lines = content.splitlines()
        new_lines = []
        missing_names = {i.split(":")[1].strip() for i in missing}

        i = 0
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)

            if line.strip().startswith("def "):
                func_name = line.strip().split("def ")[1].split("(")[0]
                if func_name in missing_names:
                    new_lines.append('    """Auto-generated docstring."""')

            i += 1

        return "\n".join(new_lines)

    # ---------------------------------------------------------
    # Пометка слишком длинных функций
    # ---------------------------------------------------------
    def _mark_long_functions(self, content: str, issues: List[str]) -> str:
        long_funcs = [i for i in issues if i.startswith("Слишком длинная функция")]
        if not long_funcs:
            return content

        lines = content.splitlines()
        new_lines = []

        long_names = {i.split(":")[1].strip() for i in long_funcs}

        for line in lines:
            new_lines.append(line)
            if line.strip().startswith("def "):
                name = line.strip().split("def ")[1].split("(")[0]
                if name in long_names:
                    new_lines.append("    # TODO: функция слишком длинная — рекомендуется рефакторинг")

        return "\n".join(new_lines)

    # ---------------------------------------------------------
    # Удаление пустых функций
    # ---------------------------------------------------------
    def _remove_empty_functions(self, content: str, issues: List[str]) -> str:
        empty = [i for i in issues if i.startswith("Пустая функция")]
        if not empty:
            return content

        empty_names = {i.split(":")[1].strip() for i in empty}

        lines = content.splitlines()
        new_lines = []

        skip_mode = False

        for line in lines:
            if line.strip().startswith("def "):
                name = line.strip().split("def ")[1].split("(")[0]
                if name in empty_names:
                    skip_mode = True
                    continue

            if skip_mode:
                if line.strip() == "" or line.startswith(" "):
                    continue
                skip_mode = False

            new_lines.append(line)

        return "\n".join(new_lines)

    # ---------------------------------------------------------
    # Псевдо-Black форматирование
    # ---------------------------------------------------------
    def _format_code(self, content: str) -> str:
        # Убираем лишние пробелы
        content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)

        # Гарантируем пустую строку между функциями
        content = re.sub(r"\n{3,}", "\n\n", content)

        return content.strip() + "\n"

    # ---------------------------------------------------------
    # Добавление заголовка авторских прав
    # ---------------------------------------------------------
    def _finalize(self, content: str) -> str:
        header = self.copyright.generate_header()
        return header + "\n" + content

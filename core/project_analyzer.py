import ast
import os
from typing import Dict, List, Set


class ProjectAnalyzer:
    """
    Анализирует проект целиком:
    - структура директорий
    - наличие __init__.py
    - корректность импортов
    - циклические зависимости
    - пустые директории
    - наличие README, LICENSE
    """

    def analyze_project(self, files: Dict[str, str], file_issues: Dict[str, List[str]]) -> List[str]:
        issues = []

        # -----------------------------
        # 1. Проверка наличия README
        # -----------------------------
        if not any(name.lower().startswith("readme") for name in files.keys()):
            issues.append("Отсутствует README — рекомендуется добавить описание проекта")

        # -----------------------------
        # 2. Проверка наличия LICENSE
        # -----------------------------
        if not any(name.lower().startswith("license") for name in files.keys()):
            issues.append("Отсутствует LICENSE — рекомендуется указать лицензию проекта")

        # -----------------------------
        # 3. Проверка __init__.py
        # -----------------------------
        issues.extend(self._check_init_files(files))

        # -----------------------------
        # 4. Анализ импортов
        # -----------------------------
        imports_map = self._extract_imports(files)
        issues.extend(self._check_invalid_imports(imports_map, files))

        # -----------------------------
        # 5. Циклические зависимости
        # -----------------------------
        issues.extend(self._check_cycles(imports_map))

        # -----------------------------
        # 6. Пустые директории
        # -----------------------------
        issues.extend(self._check_empty_directories(files))

        return issues

    # ---------------------------------------------------------
    # Проверка наличия __init__.py в директориях
    # ---------------------------------------------------------
    def _check_init_files(self, files: Dict[str, str]) -> List[str]:
        issues = []
        dirs = set(os.path.dirname(path) for path in files.keys())

        for d in dirs:
            if d and not any(f"{d}/__init__.py" == path for path in files.keys()):
                issues.append(f"В директории '{d}' отсутствует __init__.py — модуль может работать некорректно")

        return issues

    # ---------------------------------------------------------
    # Извлечение импортов из Python-файлов
    # ---------------------------------------------------------
    def _extract_imports(self, files: Dict[str, str]) -> Dict[str, Set[str]]:
        imports_map = {}

        for path, content in files.items():
            if not path.endswith(".py"):
                continue

            try:
                tree = ast.parse(content)
            except SyntaxError:
                continue

            imports = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])

            imports_map[path] = imports

        return imports_map

    # ---------------------------------------------------------
    # Проверка корректности импортов
    # ---------------------------------------------------------
    def _check_invalid_imports(self, imports_map: Dict[str, Set[str]], files: Dict[str, str]) -> List[str]:
        issues = []
        available_modules = {os.path.splitext(os.path.basename(f))[0] for f in files.keys() if f.endswith(".py")}

        for file_path, imports in imports_map.items():
            for imp in imports:
                if imp not in available_modules:
                    issues.append(f"В файле {file_path} импортируется неизвестный модуль: {imp}")

        return issues

    # ---------------------------------------------------------
    # Поиск циклических зависимостей
    # ---------------------------------------------------------
    def _check_cycles(self, imports_map: Dict[str, Set[str]]) -> List[str]:
        issues = []

        # Строим граф зависимостей
        graph = {file: set() for file in imports_map.keys()}

        for file, imports in imports_map.items():
            for imp in imports:
                for other_file in imports_map.keys():
                    if other_file.endswith(f"{imp}.py"):
                        graph[file].add(other_file)

        visited = set()
        stack = set()

        def dfs(node):
            if node in stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            stack.add(node)

            for neighbor in graph[node]:
                if dfs(neighbor):
                    return True

            stack.remove(node)
            return False

        for file in graph:
            if dfs(file):
                issues.append(f"Циклическая зависимость обнаружена, начиная с файла: {file}")
                break

        return issues

    # ---------------------------------------------------------
    # Поиск пустых директорий
    # ---------------------------------------------------------
    def _check_empty_directories(self, files: Dict[str, str]) -> List[str]:
        issues = []
        dirs = {}

        for path in files.keys():
            d = os.path.dirname(path)
            if d not in dirs:
                dirs[d] = 0
            dirs[d] += 1

        for d, count in dirs.items():
            if d and count == 0:
                issues.append(f"Пустая директория: {d}")

        return issues

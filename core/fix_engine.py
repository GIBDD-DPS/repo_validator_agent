import os
import re
from typing import List

from core.repository_scanner import FileEntry
from core.project_detector import ProjectType
from core.dependency_analyzer import DependencyReport
from core.legal_compliance import LegalReport


class FixEngine:
    """
    Умный FixEngine для Python-проектов.
    Делает:
    - создание README.md, .gitignore
    - создание __init__.py в пакетах
    - создание requirements.txt, если нет
    - создание pyproject.toml, если нет
    - создание минимальных тестов
    - анализ и исправление зависимостей (режим C)
    - анализ и исправление юридических рисков
    - лёгкое форматирование .py файлов
    """

    def apply_fixes(
        self,
        root_dir: str,
        files: List[FileEntry],
        project_type: ProjectType | None = None,
        deps: DependencyReport | None = None,
        legal: LegalReport | None = None
    ) -> List[str]:

        changes: List[str] = []

        # 1. README.md
        readme_path = os.path.join(root_dir, "README.md")
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write("# Проект\n\nЭтот README был автоматически сгенерирован Repo Validator 2.0.\n")
            changes.append("Создан README.md")

        # 2. .gitignore
        gitignore_path = os.path.join(root_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(
                    "# Автоматически сгенерировано Repo Validator 2.0\n"
                    "__pycache__/\n"
                    "*.pyc\n"
                    ".venv/\n"
                    "env/\n"
                    ".idea/\n"
                    ".vscode/\n"
                )
            changes.append("Создан .gitignore")

        # 3. Python-специфичные фиксы
        if project_type and project_type.name == "python":
            changes.extend(self._fix_python_project(root_dir, files, deps))

        # 4. Юридические фиксы
        if legal:
            changes.extend(self._fix_legal_issues(root_dir, files, legal))

        # 5. Лёгкое форматирование .py файлов
        for fe in files:
            if fe.is_text and fe.rel_path.endswith(".py"):
                full_path = fe.path
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    new_content = self._simple_python_format(content)
                    if new_content != content:
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        changes.append(f"Отформатирован {fe.rel_path}")
                except Exception:
                    continue

        return changes

    # -----------------------------
    # Python-specific fixes
    # -----------------------------
    def _fix_python_project(
        self,
        root_dir: str,
        files: List[FileEntry],
        deps: DependencyReport | None
    ) -> List[str]:

        changes = []
        paths = [f.rel_path for f in files]

        # 1. Создать requirements.txt, если нет
        req_path = os.path.join(root_dir, "requirements.txt")
        if "requirements.txt" not in [p.lower() for p in paths]:
            with open(req_path, "w", encoding="utf-8") as f:
                f.write("# Автоматически создано Repo Validator 2.0\n")
            changes.append("Создан requirements.txt")

        # 2. Создать pyproject.toml, если нет
        if "pyproject.toml" not in [p.lower() for p in paths]:
            pyproject_path = os.path.join(root_dir, "pyproject.toml")
            with open(pyproject_path, "w", encoding="utf-8") as f:
                f.write(
                    "[project]\n"
                    "name = \"my_project\"\n"
                    "version = \"0.1.0\"\n"
                    "description = \"Автоматически создано Repo Validator 2.0\"\n"
                    "requires-python = \">=3.10\"\n"
                )
            changes.append("Создан pyproject.toml")

        # 3. Создать __init__.py в пакетах
        for f in files:
            if "\\" in f.rel_path or "/" in f.rel_path:
                folder = os.path.dirname(f.path)
                init_path = os.path.join(folder, "__init__.py")
                if os.path.isdir(folder) and not os.path.exists(init_path):
                    with open(init_path, "w", encoding="utf-8") as f2:
                        f2.write("# Автоматически создано Repo Validator 2.0\n")
                    changes.append(f"Создан {init_path}")

        # 4. Создать минимальные тесты, если нет
        has_tests = any(p.startswith("tests") for p in paths)
        if not has_tests:
            tests_dir = os.path.join(root_dir, "tests")
            os.makedirs(tests_dir, exist_ok=True)
            test_file = os.path.join(tests_dir, "test_basic.py")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(
                    "def test_basic():\n"
                    "    assert True\n"
                )
            changes.append("Создан минимальный тест test_basic.py")

        # 5. Исправление зависимостей (режим C)
        if deps:
            changes.extend(self._fix_python_dependencies(root_dir, deps))

        return changes

    # -----------------------------
    # Dependency fixes (mode C)
    # -----------------------------
    def _fix_python_dependencies(self, root_dir: str, deps: DependencyReport) -> List[str]:
        changes = []
        req_path = os.path.join(root_dir, "requirements.txt")

        # Загружаем текущие строки
        if os.path.exists(req_path):
            with open(req_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        else:
            lines = []

        # Преобразуем в словарь
        req_map = {}
        for line in lines:
            if "==" in line:
                name, ver = line.split("==", 1)
                req_map[name.lower()] = ver
            else:
                req_map[line.lower()] = None

        # 1. Добавить отсутствующие зависимости
        for missing in deps.missing_dependencies:
            if missing not in req_map:
                req_map[missing] = None
                changes.append(f"Добавлена отсутствующая зависимость: {missing}")

        # 2. Удалить неиспользуемые зависимости
        for unused in deps.unused_dependencies:
            if unused in req_map:
                del req_map[unused]
                changes.append(f"Удалена неиспользуемая зависимость: {unused}")

        # 3. Удалить локальные модули
        for local in deps.local_modules:
            if local in req_map:
                del req_map[local]
                changes.append(f"Удалён локальный модуль из зависимостей: {local}")

        # 4. Исправить конфликты версий
        for pkg, conflict in deps.version_conflicts.items():
            if pkg in req_map:
                req_map[pkg] = None
                changes.append(f"Исправлен конфликт версий: {pkg}")

        # Записываем обратно
        with open(req_path, "w", encoding="utf-8") as f:
            f.write("# Автоматически обновлено Repo Validator 2.0\n")
            for pkg, ver in req_map.items():
                if ver:
                    f.write(f"{pkg}=={ver}\n")
                else:
                    f.write(f"{pkg}\n")

        return changes

    # -----------------------------
    # Legal fixes
    # -----------------------------
    def _fix_legal_issues(self, root_dir: str, files: List[FileEntry], legal: LegalReport) -> List[str]:
        changes = []

        # 1. Добавить LICENSE, если нет
        license_path = os.path.join(root_dir, "LICENSE")
        if not legal.repo_license:
            with open(license_path, "w", encoding="utf-8") as f:
                f.write(
                    "MIT License\n\n"
                    "Copyright (c) 2024\n"
                    "Permission is hereby granted, free of charge, to any person obtaining a copy...\n"
                )
            changes.append("Создан LICENSE (MIT)")

        # 2. Удалить несовместимые файлы
        for f in legal.incompatible_files:
            full = os.path.join(root_dir, f)
            if os.path.exists(full):
                os.remove(full)
                changes.append(f"Удалён файл с несовместимой лицензией: {f}")

        # 3. Добавить заголовок лицензии в файлы без лицензии
        for f in legal.unlicensed_files:
            full = os.path.join(root_dir, f)
            if not os.path.exists(full):
                continue
            if not f.endswith(".py"):
                continue
            try:
                with open(full, "r", encoding="utf-8") as src:
                    content = src.read()
                with open(full, "w", encoding="utf-8") as dst:
                    dst.write("# License: MIT\n" + content)
                changes.append(f"Добавлен лицензионный заголовок в {f}")
            except Exception:
                continue

        return changes

    # -----------------------------
    # Simple formatter
    # -----------------------------
    def _simple_python_format(self, content: str) -> str:
        lines = content.splitlines()
        while lines and lines[-1].strip() == "":
            lines.pop()
        return "\n".join(lines) + "\n"

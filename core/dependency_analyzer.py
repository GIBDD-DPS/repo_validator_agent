import os
import re
import ast
from dataclasses import dataclass
from typing import List, Set, Dict

from core.repository_scanner import FileEntry


@dataclass
class DependencyReport:
    used_imports: Set[str]
    declared_dependencies: Set[str]
    missing_dependencies: Set[str]
    unused_dependencies: Set[str]
    version_conflicts: Dict[str, str]
    local_modules: Set[str]


class DependencyAnalyzer:
    def analyze(self, root_dir: str, files: List[FileEntry]) -> DependencyReport:
        python_files = [f for f in files if f.rel_path.endswith(".py")]

        used_imports = self._extract_imports(python_files)
        declared = self._extract_declared_dependencies(root_dir)
        local_modules = self._detect_local_modules(files)

        missing = set()
        unused = set()

        for imp in used_imports:
            if imp not in declared and imp not in local_modules:
                missing.add(imp)

        for dep in declared:
            if dep not in used_imports:
                unused.add(dep)

        return DependencyReport(
            used_imports=used_imports,
            declared_dependencies=declared,
            missing_dependencies=missing,
            unused_dependencies=unused,
            version_conflicts={},  # FixEngine expects dict
            local_modules=local_modules
        )

    # ----------------------------------------------------------------------
    # IMPORT SCAN
    # ----------------------------------------------------------------------
    def _extract_imports(self, python_files: List[FileEntry]) -> Set[str]:
        imports = set()

        for f in python_files:
            try:
                with open(f.path, "r", encoding="utf-8", errors="ignore") as src:
                    content = src.read()
                tree = ast.parse(content, filename=f.path)
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])

        return imports

    # ----------------------------------------------------------------------
    # DECLARED DEPENDENCIES
    # ----------------------------------------------------------------------
    def _extract_declared_dependencies(self, root_dir: str) -> Set[str]:
        deps = set()

        req_path = os.path.join(root_dir, "requirements.txt")
        if os.path.exists(req_path):
            deps |= self._parse_requirements(req_path)

        pyproject_path = os.path.join(root_dir, "pyproject.toml")
        if os.path.exists(pyproject_path):
            deps |= self._parse_pyproject(pyproject_path)

        setup_path = os.path.join(root_dir, "setup.py")
        if os.path.exists(setup_path):
            deps |= self._parse_setup_py(setup_path)

        return deps

    # ----------------------------------------------------------------------
    # requirements.txt
    # ----------------------------------------------------------------------
    def _parse_requirements(self, path: str) -> Set[str]:
        deps = set()
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    pkg = re.split("[<>=]", line)[0].strip()
                    if pkg:
                        deps.add(pkg)
        except Exception:
            pass
        return deps

    # ----------------------------------------------------------------------
    # pyproject.toml (safe parser, no regex)
    # ----------------------------------------------------------------------
    def _parse_pyproject(self, path: str) -> Set[str]:
        deps = set()
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            if "dependencies" in text:
                lines = text.splitlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("dependencies"):
                        if "[" in line and "]" in line:
                            inside = line[line.find("[") + 1 : line.find("]")]
                            items = inside.split(",")
                            for item in items:
                                item = item.strip().strip("'").strip('"')
                                if item:
                                    pkg = re.split("[<>=]", item)[0].strip()
                                    deps.add(pkg)

        except Exception:
            pass
        return deps

    # ----------------------------------------------------------------------
    # setup.py (safe parser, no regex)
    # ----------------------------------------------------------------------
    def _parse_setup_py(self, setup_path: str) -> Set[str]:
        deps = set()
        try:
            with open(setup_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            if "install_requires" in text:
                start = text.find("install_requires")
                bracket = text.find("[", start)
                end = text.find("]", bracket)
                if bracket != -1 and end != -1:
                    inside = text[bracket + 1 : end]
                    items = inside.split(",")
                    for item in items:
                        item = item.strip().strip("'").strip('"')
                        if item:
                            pkg = re.split("[<>=]", item)[0].strip()
                            deps.add(pkg)

        except Exception:
            pass
        return deps

    # ----------------------------------------------------------------------
    # LOCAL MODULES
    # ----------------------------------------------------------------------
    def _detect_local_modules(self, files: List[FileEntry]) -> Set[str]:
        modules = set()
        for f in files:
            if f.rel_path.endswith(".py"):
                name = os.path.basename(f.rel_path).replace(".py", "")
                modules.add(name)
        return modules

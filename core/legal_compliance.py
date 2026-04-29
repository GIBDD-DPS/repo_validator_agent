import os
import re
from dataclasses import dataclass
from typing import List, Optional, Dict

from core.repository_scanner import FileEntry


@dataclass
class LegalReport:
    repo_license: Optional[str]
    file_licenses: Dict[str, str]
    incompatible_files: List[str]
    unlicensed_files: List[str]
    mixed_licenses: bool
    summary: str


class LegalComplianceOfficer:
    """
    Анализ лицензий и юридических рисков:
    - определение лицензии репозитория
    - определение лицензий файлов
    - проверка совместимости лицензий
    - поиск файлов без лицензии
    """

    LICENSE_PATTERNS = {
        "MIT": r"MIT License",
        "Apache-2.0": r"Apache License,? Version 2\.0",
        "GPL-3.0": r"GNU GENERAL PUBLIC LICENSE\s+Version 3",
        "GPL-2.0": r"GNU GENERAL PUBLIC LICENSE\s+Version 2",
        "BSD-3-Clause": r"Redistribution and use in source and binary forms",
        "MPL-2.0": r"Mozilla Public License Version 2\.0",
    }

    COMPATIBILITY = {
        "MIT": {"MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0"},
        "Apache-2.0": {"MIT", "Apache-2.0", "BSD-3-Clause"},
        "BSD-3-Clause": {"MIT", "Apache-2.0", "BSD-3-Clause"},
        "GPL-3.0": {"GPL-3.0"},
        "GPL-2.0": {"GPL-2.0"},
        "MPL-2.0": {"MPL-2.0", "MIT"},
    }

    def analyze(self, root_dir: str, files: List[FileEntry]) -> LegalReport:
        repo_license = self._detect_repo_license(root_dir)
        file_licenses = self._detect_file_licenses(files)

        incompatible_files = []
        unlicensed_files = []

        # Проверка совместимости
        for path, lic in file_licenses.items():
            if repo_license and lic:
                if lic not in self.COMPATIBILITY.get(repo_license, {}):
                    incompatible_files.append(path)

        # Файлы без лицензии
        for f in files:
            if f.rel_path not in file_licenses:
                unlicensed_files.append(f.rel_path)

        mixed_licenses = len(set(file_licenses.values())) > 1

        summary = self._build_summary(
            repo_license,
            file_licenses,
            incompatible_files,
            unlicensed_files,
            mixed_licenses
        )

        return LegalReport(
            repo_license=repo_license,
            file_licenses=file_licenses,
            incompatible_files=incompatible_files,
            unlicensed_files=unlicensed_files,
            mixed_licenses=mixed_licenses,
            summary=summary,
        )

    # -----------------------------
    # Определение лицензии репозитория
    # -----------------------------
    def _detect_repo_license(self, root_dir: str) -> Optional[str]:
        license_path = os.path.join(root_dir, "LICENSE")
        if os.path.exists(license_path):
            with open(license_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                for name, pattern in self.LICENSE_PATTERNS.items():
                    if re.search(pattern, text, re.I):
                        return name
        return None

    # -----------------------------
    # Определение лицензий файлов
    # -----------------------------
    def _detect_file_licenses(self, files: List[FileEntry]) -> Dict[str, str]:
        result = {}
        for f in files:
            if not f.is_text:
                continue
            try:
                with open(f.path, "r", encoding="utf-8", errors="ignore") as src:
                    head = src.read(2000)
                    for name, pattern in self.LICENSE_PATTERNS.items():
                        if re.search(pattern, head, re.I):
                            result[f.rel_path] = name
                            break
            except Exception:
                continue
        return result

    # -----------------------------
    # Формирование отчёта
    # -----------------------------
    def _build_summary(
        self,
        repo_license: Optional[str],
        file_licenses: Dict[str, str],
        incompatible_files: List[str],
        unlicensed_files: List[str],
        mixed_licenses: bool
    ) -> str:

        summary = ""

        summary += f"Лицензия репозитория: {repo_license or 'не обнаружена'}\n\n"

        summary += "Лицензии файлов:\n"
        if file_licenses:
            for path, lic in file_licenses.items():
                summary += f"  - {path}: {lic}\n"
        else:
            summary += "  Не обнаружено лицензированных файлов.\n"

        summary += "\nНесовместимые файлы:\n"
        if incompatible_files:
            for f in incompatible_files:
                summary += f"  - {f}\n"
        else:
            summary += "  Несовместимых файлов не обнаружено.\n"

        summary += "\nФайлы без лицензии:\n"
        if unlicensed_files:
            for f in unlicensed_files[:20]:
                summary += f"  - {f}\n"
            if len(unlicensed_files) > 20:
                summary += f"  ... и ещё {len(unlicensed_files) - 20}\n"
        else:
            summary += "  Все файлы имеют лицензию.\n"

        summary += f"\nСмешанные лицензии: {'да' if mixed_licenses else 'нет'}\n"

        return summary

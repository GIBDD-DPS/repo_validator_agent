from dataclasses import dataclass
from typing import List

from core.repository_scanner import FileEntry
from core.structure_analyzer import StructureAnalysis
from core.dependency_analyzer import DependencyReport
from core.legal_compliance import LegalReport


@dataclass
class QualityScore:
    score: int
    details: str


class QualityScoreEngine:
    """
    Оценка качества проекта (0–100).
    Учитывает:
    - структуру
    - зависимости
    - юридические риски
    - тесты
    - документацию
    """

    def calculate(
        self,
        files: List[FileEntry],
        structure: StructureAnalysis,
        deps: DependencyReport,
        legal: LegalReport
    ) -> QualityScore:

        score = 100
        details = []

        # -----------------------------
        # Структурные метрики
        # -----------------------------
        paths = [f.rel_path.lower() for f in files]

        if "readme.md" not in paths:
            score -= 10
            details.append("- Нет README.md (-10)")

        if "license" not in paths:
            score -= 10
            details.append("- Нет LICENSE (-10)")

        if "requirements.txt" not in paths:
            score -= 5
            details.append("- Нет requirements.txt (-5)")

        if "pyproject.toml" not in paths:
            score -= 5
            details.append("- Нет pyproject.toml (-5)")

        if not any(p.startswith("tests") for p in paths):
            score -= 10
            details.append("- Нет тестов (-10)")
        else:
            score += 5
            details.append("+ Есть тесты (+5)")

        if structure.duplicates:
            score -= 10
            details.append(f"- Дубликаты файлов ({len(structure.duplicates)}) (-10)")

        if structure.large_files:
            score -= 5
            details.append("- Есть крупные файлы (>1 МБ) (-5)")

        # -----------------------------
        # Метрики зависимостей
        # -----------------------------
        if deps.missing_dependencies:
            score -= 10
            details.append(f"- Отсутствующие зависимости ({len(deps.missing_dependencies)}) (-10)")

        if deps.unused_dependencies:
            score -= 5
            details.append(f"- Неиспользуемые зависимости ({len(deps.unused_dependencies)}) (-5)")

        if deps.version_conflicts:
            score -= 10
            details.append("- Конфликты версий (-10)")

        # -----------------------------
        # Юридические метрики
        # -----------------------------
        if legal.incompatible_files:
            score -= 20
            details.append(f"- Несовместимые лицензии ({len(legal.incompatible_files)}) (-20)")

        if legal.unlicensed_files:
            score -= 10
            details.append(f"- Файлы без лицензии ({len(legal.unlicensed_files)}) (-10)")

        if legal.mixed_licenses:
            score -= 5
            details.append("- Смешанные лицензии (-5)")

        # -----------------------------
        # Финализация
        # -----------------------------
        if score < 0:
            score = 0
        if score > 100:
            score = 100

        details_text = "Оценка качества проекта:\n" + "\n".join(details)

        return QualityScore(score=score, details=details_text)

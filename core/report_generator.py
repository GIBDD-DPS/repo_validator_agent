from dataclasses import dataclass
from typing import List

from core.repository_scanner import FileEntry
from core.structure_analyzer import StructureAnalysis
from core.dependency_analyzer import DependencyReport
from core.legal_compliance import LegalReport
from core.quality_score import QualityScore
from core.optimization_loop import OptimizationResult
from core.cicd_analyzer import CICDReport


@dataclass
class BasicReport:
    total_files: int
    text_files: int
    binary_files: int
    total_size: int
    summary: str
    quality_score: int
    optimization: OptimizationResult
    cicd: CICDReport


class ReportGenerator:
    """
    Генератор отчёта:
    - структура
    - зависимости
    - юридический анализ
    - оценка качества
    - анализ CI/CD
    - оптимизация проекта
    """

    def build_report(
        self,
        files: List[FileEntry],
        structure: StructureAnalysis,
        deps: DependencyReport,
        legal: LegalReport,
        quality: QualityScore,
        cicd: CICDReport,
        optimization: OptimizationResult
    ) -> BasicReport:

        total_files = len(files)
        text_files = sum(1 for f in files if f.is_text)
        binary_files = total_files - text_files
        total_size = sum(f.size for f in files)

        # --- CI/CD ---
        cicd_block = "=== Анализ CI/CD ===\n\n"

        if cicd.has_ci:
            cicd_block += f"Провайдеры: {', '.join(cicd.providers)}\n"
            cicd_block += f"Тесты: {'да' if cicd.has_tests else 'нет'}\n"
            cicd_block += f"Линтеры: {'да' if cicd.has_lint else 'нет'}\n"
            cicd_block += f"Сборка: {'да' if cicd.has_build else 'нет'}\n"
            cicd_block += f"Деплой: {'да' if cicd.has_deploy else 'нет'}\n"
            cicd_block += f"Кеш: {'да' if cicd.has_cache else 'нет'}\n\n"

            cicd_block += "Проблемы:\n"
            if cicd.issues:
                for issue in cicd.issues:
                    cicd_block += f"  - {issue}\n"
            else:
                cicd_block += "  Нет проблем.\n"
        else:
            cicd_block += "CI/CD не обнаружен.\n"

        # --- Оптимизация ---
        opt_block = "=== Оптимизация проекта ===\n\n"

        opt_block += "Применённые улучшения:\n"
        if optimization.applied:
            for item in optimization.applied:
                opt_block += f"  - {item}\n"
        else:
            opt_block += "  Нет автоматических улучшений.\n"

        opt_block += "\nАвтоматически установленные инструменты:\n"
        if optimization.auto_installed_tools:
            for tool in optimization.auto_installed_tools:
                opt_block += f"  - {tool['name']}: {tool['description']}\n"
        else:
            opt_block += "  Нет автоматически установленных инструментов.\n"

        opt_block += "\nУстановленные по выбору пользователя:\n"
        if optimization.user_selected_tools:
            for tool in optimization.user_selected_tools:
                opt_block += f"  - {tool['name']}: {tool['description']}\n"
        else:
            opt_block += "  Нет выбранных пользователем инструментов.\n"

        opt_block += "\nРекомендованные инструменты:\n"
        if optimization.recommended_tools:
            for tool in optimization.recommended_tools:
                opt_block += f"  - {tool['name']}: {tool['description']}\n"
        else:
            opt_block += "  Нет рекомендаций.\n"

        # --- Итоговый отчёт ---
        summary = (
            f"Всего файлов: {total_files}\n"
            f"Текстовых файлов: {text_files}\n"
            f"Бинарных файлов: {binary_files}\n"
            f"Общий размер: {total_size} байт\n\n"
            f"{cicd_block}\n\n"
            f"=== Юридический анализ ===\n\n{legal.summary}\n\n"
            f"=== Оценка качества ===\n\n"
            f"Score: {quality.score}/100\n\n"
            f"{quality.details}\n\n"
            f"{opt_block}\n"
        )

        return BasicReport(
            total_files=total_files,
            text_files=text_files,
            binary_files=binary_files,
            total_size=total_size,
            summary=summary,
            quality_score=quality.score,
            optimization=optimization,
            cicd=cicd
        )

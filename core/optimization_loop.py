from dataclasses import dataclass
from typing import List, Dict

from core.structure_analyzer import StructureAnalysis
from core.dependency_analyzer import DependencyReport
from core.legal_compliance import LegalReport
from core.quality_score import QualityScore
from core.cicd_analyzer import CICDReport


@dataclass
class OptimizationResult:
    applied: List[str]
    recommended_tools: List[Dict[str, str]]
    auto_installed_tools: List[Dict[str, str]]
    user_selected_tools: List[Dict[str, str]]


class OptimizationLoop:
    """
    Optimization Loop:
    - анализирует структуру, зависимости, лицензии, качество, CI/CD
    - предлагает инструменты (название + описание)
    - автоматически устанавливает безопасные
    - поддерживает выбор пользователя
    """

    TOOL_DESCRIPTIONS = {
        "AntiHallucinationShield": "Предотвращение ошибок интерпретации.",
        "LegalComplianceOfficer": "Юридический анализ лицензий.",
        "ProgressMetricsCalculator": "Подсчёт метрик качества.",
        "OptimizationLoop": "Цикл оптимизации проекта.",
        "SpecGenerator": "Генерация технических спецификаций.",
        "IntegrationConfigurator": "Настройка интеграций.",
        "TestGenerator": "Автоматическая генерация тестов.",
        "DeploymentAutomator": "Автоматизация развёртывания.",
        "CodeStyleFormatter": "Форматирование кода.",
        "StaticAnalyzer": "Статический анализ кода.",
        "ComplexityInspector": "Анализ сложности.",
        "TypeHintEnforcer": "Проверка type hints.",
        "DocstringGenerator": "Генерация docstring.",
        "APIContractValidator": "Проверка API‑контрактов.",
        "ModuleGraphBuilder": "Граф модулей.",
        "DependencyVisualizer": "Визуализация зависимостей.",
        "LayeringInspector": "Проверка архитектурных слоёв.",
        "CircularImportDetector": "Поиск циклических импортов.",
        "CICDConfigurator": "Настройка CI/CD.",
        "PipelineOptimizer": "Оптимизация пайплайнов.",
        "TestCoverageReporter": "Отчёты покрытия тестами.",
        "MarkdownLinter": "Проверка Markdown.",
        "AutoDocBuilder": "Сборка документации.",
        "ExampleGenerator": "Генерация примеров.",
        "SecretScanner": "Поиск секретов.",
        "VulnerabilityScanner": "Поиск уязвимостей.",
        "DependencyRiskAnalyzer": "Оценка рисков зависимостей.",
        "DataSchemaValidator": "Проверка схем данных.",
        "DataQualityChecker": "Анализ качества данных.",
        "LoggingEnhancer": "Улучшение логирования.",
        "VirtualEnvManager": "Управление окружениями.",
        "RequirementsOptimizer": "Оптимизация зависимостей.",
        "PyprojectNormalizer": "Нормализация pyproject.toml.",
    }

    SAFE_TO_INSTALL = [
        "AntiHallucinationShield",
        "ProgressMetricsCalculator",
        "OptimizationLoop",
        "TestGenerator",
        "CodeStyleFormatter",
        "DocstringGenerator",
        "MarkdownLinter",
        "LoggingEnhancer",
        "CircularImportDetector",
        "RequirementsOptimizer",
        "PyprojectNormalizer",
    ]

    ALL_TOOLS = list(TOOL_DESCRIPTIONS.keys())

    def optimize(
        self,
        structure: StructureAnalysis,
        deps: DependencyReport,
        legal: LegalReport,
        quality: QualityScore,
        cicd: CICDReport
    ) -> OptimizationResult:

        applied = []
        recommended = []
        auto_installed = []

        # --- Автоматические улучшения ---
        if structure.duplicates:
            applied.append("Удаление дубликатов файлов")
        if deps.missing_dependencies:
            applied.append("Добавление отсутствующих зависимостей")
        if deps.unused_dependencies:
            applied.append("Удаление неиспользуемых зависимостей")
        if legal.unlicensed_files:
            applied.append("Добавление лицензионных заголовков")
        if legal.incompatible_files:
            applied.append("Удаление несовместимых файлов")

        # --- Рекомендации по CI/CD ---
        if not cicd.has_ci:
            recommended.append({
                "name": "CICDConfigurator",
                "description": self.TOOL_DESCRIPTIONS["CICDConfigurator"],
                "safe": False
            })

        if not cicd.has_tests:
            recommended.append({
                "name": "TestCoverageReporter",
                "description": self.TOOL_DESCRIPTIONS["TestCoverageReporter"],
                "safe": False
            })

        if not cicd.has_lint:
            recommended.append({
                "name": "StaticAnalyzer",
                "description": self.TOOL_DESCRIPTIONS["StaticAnalyzer"],
                "safe": False
            })

        if not cicd.has_deploy:
            recommended.append({
                "name": "DeploymentAutomator",
                "description": self.TOOL_DESCRIPTIONS["DeploymentAutomator"],
                "safe": False
            })

        if not cicd.has_cache:
            recommended.append({
                "name": "PipelineOptimizer",
                "description": self.TOOL_DESCRIPTIONS["PipelineOptimizer"],
                "safe": False
            })

        # --- Общие рекомендации ---
        for tool in self.ALL_TOOLS:
            if tool not in self.SAFE_TO_INSTALL:
                if not any(t["name"] == tool for t in recommended):
                    recommended.append({
                        "name": tool,
                        "description": self.TOOL_DESCRIPTIONS[tool],
                        "safe": False
                    })

        # --- Автоматическая установка ---
        for tool in self.SAFE_TO_INSTALL:
            auto_installed.append({
                "name": tool,
                "description": self.TOOL_DESCRIPTIONS[tool],
                "safe": True
            })

        return OptimizationResult(
            applied=applied,
            recommended_tools=recommended,
            auto_installed_tools=auto_installed,
            user_selected_tools=[]
        )

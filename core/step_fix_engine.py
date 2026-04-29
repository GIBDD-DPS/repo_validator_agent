from typing import List
from rich import print


class StepFixEngine:
    """
    Управляет процессом исправлений файлов.

    Режимы:
    - step: спрашивает подтверждение перед применением изменений
    - auto: применяет изменения автоматически без вопросов

    Компоненты:
    - rewriter: FullFileRewriter
    - report_generator: ReportGenerator
    - metrics: ProgressMetrics
    - shield: AntiHallucinationShield
    - legal: LegalComplianceOfficer
    """

    def __init__(self, rewriter, report_generator, metrics, shield, legal, auto_mode: bool = False):
        self.rewriter = rewriter
        self.report_generator = report_generator
        self.metrics = metrics
        self.shield = shield
        self.legal = legal
        self.auto_mode = auto_mode

    # ---------------------------------------------------------
    # Главный метод обработки файла
    # ---------------------------------------------------------
    def process_file(self, file_path: str, original_content: str, issues: List[str]):
        print(f"\n[bold cyan]Файл:[/bold cyan] {file_path}")

        if not issues:
            print("[green]Проблем не найдено.[/green]")
            return

        print("[yellow]Найдены проблемы:[/yellow]")
        for issue in issues:
            print(f" - {issue}")

        # -----------------------------------------------------
        # 1. Фильтрация галлюцинаций
        # -----------------------------------------------------
        issues = self.shield.filter_issues(issues)

        # -----------------------------------------------------
        # 2. Генерация новой версии файла
        # -----------------------------------------------------
        new_content = self.rewriter.rewrite_file(file_path, original_content, issues)

        # -----------------------------------------------------
        # 3. Юридическая проверка
        # -----------------------------------------------------
        self.legal.validate_file(new_content)

        # -----------------------------------------------------
        # 4. Показываем пользователю результат
        # -----------------------------------------------------
        print("\n[green]Предлагаемая новая версия файла:[/green]\n")
        print(new_content)

        # -----------------------------------------------------
        # 5. AUTO MODE — применяем сразу
        # -----------------------------------------------------
        if self.auto_mode:
            self._apply_changes(file_path, new_content, auto=True)
            return

        # -----------------------------------------------------
        # 6. STEP MODE — спрашиваем подтверждение
        # -----------------------------------------------------
        while True:
            confirm = input("\nПрименить изменения? (y/n): ").strip().lower()

            if confirm == "y":
                self._apply_changes(file_path, new_content, auto=False)
                break

            elif confirm == "n":
                print("[red]Изменения отклонены.[/red]")
                break

            else:
                print("Введите 'y' или 'n'.")

    # ---------------------------------------------------------
    # Применение изменений
    # ---------------------------------------------------------
    def _apply_changes(self, file_path: str, new_content: str, auto: bool):
        self.metrics.increment_files_fixed()
        self.report_generator.save_fixed_file(file_path, new_content)

        if auto:
            print("[green]Изменения применены автоматически (auto mode).[/green]")
        else:
            print("[green]Изменения применены.[/green]")

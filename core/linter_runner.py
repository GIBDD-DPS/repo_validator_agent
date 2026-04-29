import subprocess
import tempfile
import os
from typing import List


class LinterRunner:
    """
    Запускает flake8, pylint и bandit для анализа Python-файлов.
    Возвращает список найденных проблем в едином формате.
    """

    def __init__(self):
        self.linters = {
            "flake8": self._run_flake8,
            "pylint": self._run_pylint,
            "bandit": self._run_bandit
        }

    # ---------------------------------------------------------
    # Публичный метод: запускает все линтеры
    # ---------------------------------------------------------
    def analyze(self, file_path: str, content: str) -> List[str]:
        issues = []

        # Создаём временный файл, чтобы линтеры могли его анализировать
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Запускаем каждый линтер
        for name, runner in self.linters.items():
            try:
                issues.extend(runner(tmp_path))
            except FileNotFoundError:
                issues.append(f"[{name}] Линтер не установлен — пропускаем")
            except Exception as e:
                issues.append(f"[{name}] Ошибка запуска: {e}")

        # Удаляем временный файл
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        return issues

    # ---------------------------------------------------------
    # flake8
    # ---------------------------------------------------------
    def _run_flake8(self, file_path: str) -> List[str]:
        result = subprocess.run(
            ["flake8", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        issues = []
        for line in result.stdout.splitlines():
            issues.append(f"[flake8] {line}")

        return issues

    # ---------------------------------------------------------
    # pylint
    # ---------------------------------------------------------
    def _run_pylint(self, file_path: str) -> List[str]:
        result = subprocess.run(
            ["pylint", "--disable=all", "--enable=E,W,C,R", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        issues = []
        for line in result.stdout.splitlines():
            if line.strip() and ":" in line:
                issues.append(f"[pylint] {line}")

        return issues

    # ---------------------------------------------------------
    # bandit (security)
    # ---------------------------------------------------------
    def _run_bandit(self, file_path: str) -> List[str]:
        result = subprocess.run(
            ["bandit", "-q", "-r", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        issues = []
        for line in result.stdout.splitlines():
            if line.strip():
                issues.append(f"[bandit] {line}")

        return issues

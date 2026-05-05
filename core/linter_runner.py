# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

import subprocess
import tempfile
import os

class LinterRunner:
    """Запускает линтеры flake8 и bandit на переданных файлах."""

    def run_all(self, files: dict) -> dict:
        """
        files: словарь {относительный_путь: содержимое}
        Возвращает: {путь: [список строк с ошибками]}
        """
        results = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            # Сохраняем все файлы во временную папку
            for path, content in files.items():
                full_path = os.path.join(tmpdir, path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Запускаем flake8
            flake8_issues = self._run_flake8(tmpdir)
            # Запускаем bandit
            bandit_issues = self._run_bandit(tmpdir)

            # Собираем результаты по файлам
            for issue_list, source in [(flake8_issues, 'flake8'), (bandit_issues, 'bandit')]:
                for path, msg in issue_list:
                    rel_path = os.path.relpath(path, tmpdir)
                    if rel_path not in results:
                        results[rel_path] = []
                    results[rel_path].append(f"[{source}] {msg}")

        return results

    def _run_flake8(self, directory: str) -> list:
        """Возвращает список (full_path, error_message)."""
        try:
            proc = subprocess.run(
                ['flake8', '--max-line-length=120', directory],
                capture_output=True, text=True, timeout=30
            )
            issues = []
            for line in proc.stdout.splitlines():
                # Формат: path:line:col: error_code message
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    path = parts[0]
                    msg = parts[3].strip()
                    issues.append((path, msg))
            return issues
        except Exception as e:
            return [(directory, f'flake8 error: {e}')]

    def _run_bandit(self, directory: str) -> list:
        """Возвращает список (full_path, error_message)."""
        try:
            proc = subprocess.run(
                ['bandit', '-r', directory, '-f', 'custom', '--msg-template', '{path}: {msg}'],
                capture_output=True, text=True, timeout=30
            )
            issues = []
            for line in proc.stdout.splitlines():
                if ':' in line:
                    path, msg = line.split(':', 1)
                    issues.append((path.strip(), msg.strip()))
            return issues
        except Exception as e:
            return [(directory, f'bandit error: {e}')]

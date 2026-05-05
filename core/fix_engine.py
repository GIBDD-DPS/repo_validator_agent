# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

import subprocess
import tempfile
import os

class StepFixEngine:
    """Применяет автофиксы (black, isort) к файлам."""

    def __init__(self):
        self.fixes_applied = []

    def process_file(self, file_path: str, content: str, issues: list) -> str:
        """Принимает путь, содержимое и список проблем, возвращает исправленный код."""
        # Пробуем форматировать только Python-файлы
        if not file_path.endswith('.py'):
            return content

        # Создаём временный файл
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpfile = os.path.join(tmpdir, os.path.basename(file_path))
            with open(tmpfile, 'w', encoding='utf-8') as f:
                f.write(content)

            # isort (сортировка импортов)
            try:
                subprocess.run(['isort', tmpfile], check=True, timeout=10)
            except Exception:
                pass

            # black (форматирование)
            try:
                subprocess.run(['black', '--quiet', tmpfile], check=True, timeout=10)
            except Exception:
                pass

            # Читаем результат
            with open(tmpfile, 'r', encoding='utf-8') as f:
                new_content = f.read()

            if new_content != content:
                self.fixes_applied.append(file_path)
            return new_content

    def format_all(self, files: dict) -> dict:
        """Форматирует все Python-файлы и возвращает обновлённый словарь {путь: содержимое}."""
        result = {}
        for path, content in files.items():
            result[path] = self.process_file(path, content, [])
        return result

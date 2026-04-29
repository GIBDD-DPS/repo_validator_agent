import os
import subprocess
from typing import List, Optional, Dict
from pathlib import Path
import chardet
from .base import FileEntry

class RepositoryScanner:
    """Сканер для клонирования и анализа файлов репозитория."""

    def __init__(self, repo_url: str, local_path: str = "/tmp/repo_scan"):
        self.repo_url = repo_url
        self.local_path = local_path

    def clone(self, branch: str | None = None) -> None:
        """Клонирует репозиторий (или обновляет существующий)."""
        if os.path.exists(self.local_path):
            subprocess.run(["git", "-C", self.local_path, "pull"], check=True)
        else:
            cmd = ["git", "clone", self.repo_url, self.local_path]
            if branch:
                cmd += ["--branch", branch]
            subprocess.run(cmd, check=True)

    def scan(self) -> List[FileEntry]:
        """Сканирует локальный репозиторий и возвращает список объектов FileEntry."""
        entries = []
        for root, dirs, files in os.walk(self.local_path):
            # Пропускаем скрытые папки (начинающиеся с точки, например .git)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.startswith('.'):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, self.local_path)
                # Определяем, текстовый ли файл
                try:
                    with open(full_path, 'rb') as f:
                        raw = f.read(1024)
                    encoding = chardet.detect(raw)['encoding']
                    if encoding:
                        with open(full_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        is_text = True
                    else:
                        content = None
                        is_text = False
                except Exception:
                    content = None
                    is_text = False
                entries.append(FileEntry(
                    path=full_path,
                    rel_path=rel_path,
                    content=content,
                    is_text=is_text
                ))
        return entries

    # ===== ВОТ ЭТОТ БЛОК ДОБАВЛЯЕМ =====
    def scan_repository(self, branch: str | None = None) -> Dict[str, str]:
        """
        Сканирует репозиторий и возвращает словарь {относительный_путь: содержимое_файла}.
        Этот метод нужен, чтобы main.py мог получить все файлы разом.
        """
        if branch:
            self.clone(branch)      # клонируем конкретную ветку
        else:
            self.clone()            # клонируем главную ветку
        result = {}
        for entry in self.scan():
            # Берём только читаемые текстовые файлы
            if entry.is_text and entry.content is not None:
                result[entry.rel_path] = entry.content
        return result

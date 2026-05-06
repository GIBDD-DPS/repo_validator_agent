# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

import os
import subprocess
import shutil
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
        """
        Клонирует репозиторий (или обновляет существующий).
        Если локальная папка существует, но .git отсутствует – удаляем и клонируем заново.
        """
        # Проверяем, есть ли рабочая git-директория
        if os.path.exists(self.local_path):
            if not os.path.isdir(os.path.join(self.local_path, '.git')):
                # .git отсутствует – папка не является корректным клоном
                shutil.rmtree(self.local_path, ignore_errors=True)
            else:
                # папка есть и .git есть – делаем pull
                try:
                    subprocess.run(
                        ["git", "-C", self.local_path, "pull"],
                        check=True,
                        capture_output=True
                    )
                except subprocess.CalledProcessError:
                    # если pull не удался, удаляем и клонируем заново
                    shutil.rmtree(self.local_path, ignore_errors=True)

        # Если папка не существует (или была удалена) – клонируем
        if not os.path.exists(self.local_path):
            cmd = ["git", "clone", self.repo_url, self.local_path]
            if branch:
                cmd += ["--branch", branch]
            subprocess.run(cmd, check=True, capture_output=True)

    def scan(self) -> List[FileEntry]:
        """Сканирует локальный репозиторий и возвращает список объектов FileEntry."""
        entries = []
        if not os.path.exists(self.local_path):
            return entries
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

    def scan_repository(self, branch: str | None = None) -> Dict[str, str]:
        """
        Сканирует репозиторий и возвращает словарь {относительный_путь: содержимое_файла}.
        Этот метод нужен, чтобы main.py мог получить все файлы разом.
        """
        if branch:
            self.clone(branch)
        else:
            self.clone()
        result = {}
        for entry in self.scan():
            if entry.is_text and entry.content is not None:
                result[entry.rel_path] = entry.content
        return result

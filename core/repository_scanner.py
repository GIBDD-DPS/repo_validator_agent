# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

import os
import subprocess
import shutil
import tempfile
from typing import List, Optional, Dict
from pathlib import Path
import chardet
from .base import FileEntry

class RepositoryScanner:
    """
    Сканер для клонирования и анализа файлов репозитория.
    Оптимизирован: shallow clone (--depth 1), автоматическая очистка.
    """

    def __init__(self, repo_url: str, local_path: Optional[str] = None):
        self.repo_url = repo_url
        # Если путь не указан, создаём временную папку
        if local_path is None:
            self.local_path = tempfile.mkdtemp(prefix="repo_scan_")
        else:
            self.local_path = local_path
        self.cleaned_up = False

    def clone(self, branch: Optional[str] = None, depth: int = 1) -> None:
        """
        Клонирует репозиторий с ограничением глубины (--depth).
        Если локальная папка существует и является git-репозиторием – выполняет pull.
        """
        # Проверяем, есть ли рабочая git-директория
        if os.path.exists(self.local_path):
            git_dir = os.path.join(self.local_path, '.git')
            if not os.path.isdir(git_dir):
                # .git отсутствует – папка не является корректным клоном
                shutil.rmtree(self.local_path, ignore_errors=True)
            else:
                # папка есть и .git есть – делаем pull (только если depth > 1, иначе обновление невозможно)
                if depth > 1:
                    try:
                        subprocess.run(
                            ["git", "-C", self.local_path, "pull"],
                            check=True,
                            capture_output=True,
                            text=True
                        )
                    except subprocess.CalledProcessError:
                        # если pull не удался, удаляем и клонируем заново
                        shutil.rmtree(self.local_path, ignore_errors=True)

        # Если папка не существует (или была удалена) – клонируем с shallow depth
        if not os.path.exists(self.local_path):
            cmd = ["git", "clone", "--depth", str(depth)]
            if branch:
                cmd += ["--branch", branch]
            cmd += [self.repo_url, self.local_path]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Ошибка клонирования: {e.stderr}")

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

    def scan_repository(self, branch: Optional[str] = None) -> Dict[str, str]:
        """
        Сканирует репозиторий и возвращает словарь {относительный_путь: содержимое_файла}.
        Этот метод нужен, чтобы main.py мог получить все файлы разом.
        """
        self.clone(branch=branch)
        result = {}
        for entry in self.scan():
            if entry.is_text and entry.content is not None:
                result[entry.rel_path] = entry.content
        return result

    def cleanup(self) -> None:
        """Удаляет временную папку репозитория (вызывается после завершения анализа)."""
        if not self.cleaned_up and os.path.exists(self.local_path):
            shutil.rmtree(self.local_path, ignore_errors=True)
            self.cleaned_up = True

    def __del__(self):
        self.cleanup()

# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Git Analyzer – извлекает статистику коммитов, авторов, активность.
"""
import subprocess
import os
import shutil
from typing import Dict, List
from datetime import datetime


class GitAnalyzer:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def analyze(self) -> Dict:
        """Возвращает словарь с метриками активности."""
        if not os.path.isdir(os.path.join(self.repo_path, '.git')):
            return {"error": "Каталог .git не найден (возможно, репозиторий клонирован без истории)."}

        # Проверяем, установлен ли git
        if not shutil.which("git"):
            return {"error": "Git не установлен в окружении. Установите git для анализа активности."}

        try:
            total_commits = self._count_commits()
            authors = self._get_authors()
            last_commit_date = self._last_commit_date()
            first_commit_date = self._first_commit_date()
            contributors_count = len(authors)
            weeks_active = 1
            if first_commit_date and last_commit_date:
                delta = last_commit_date - first_commit_date
                weeks_active = max(1, delta.days // 7)

            is_active = (datetime.now() - last_commit_date).days < 30 if last_commit_date else False

            return {
                "total_commits": total_commits,
                "contributors_count": contributors_count,
                "top_authors": authors[:5],
                "last_commit": last_commit_date.isoformat() if last_commit_date else None,
                "first_commit": first_commit_date.isoformat() if first_commit_date else None,
                "weeks_active": weeks_active,
                "is_active": is_active
            }
        except Exception as e:
            return {"error": f"Ошибка анализа git: {str(e)}"}

    def _run(self, cmd: List[str]) -> str:
        result = subprocess.run(cmd, cwd=self.repo_path, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        return result.stdout.strip()

    def _count_commits(self) -> int:
        out = self._run(["git", "rev-list", "--count", "HEAD"])
        return int(out)

    def _get_authors(self) -> List[Dict]:
        out = self._run(["git", "shortlog", "-sne", "HEAD"])
        authors = []
        for line in out.splitlines():
            parts = line.strip().split('\t', 1)
            if len(parts) == 2:
                commits_str = parts[0].strip()
                name = parts[1]
                authors.append({"name": name, "commits": int(commits_str)})
        return sorted(authors, key=lambda x: x["commits"], reverse=True)

    def _last_commit_date(self) -> datetime:
        out = self._run(["git", "log", "-1", "--format=%cI"])
        return datetime.fromisoformat(out)

    def _first_commit_date(self) -> datetime:
        out = self._run(["git", "log", "--reverse", "--format=%cI", "--max-count=1"])
        return datetime.fromisoformat(out)

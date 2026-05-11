# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Глобальный лидерборд — хранит результаты всех анализов и предоставляет рейтинг.
"""
from typing import Dict, List
import time


class Leaderboard:
    def __init__(self):
        self.entries: Dict[str, List[dict]] = {}  # repo_url -> [записи]

    def add_result(self, repo_url: str, scoring: Dict, language: str = "unknown"):
        """Добавляет результат анализа."""
        if not scoring or scoring.get("error"):
            return
        if repo_url not in self.entries:
            self.entries[repo_url] = []
        self.entries[repo_url].append({
            "timestamp": time.time(),
            "repo_score": scoring.get("repo_score", 0),
            "risk_score": scoring.get("risk_score", 0),
            "readiness": scoring.get("readiness", 0),
            "tech_debt_hours": scoring.get("tech_debt_hours", 0),
            "language": language,
        })

    def get_top(self, limit: int = 10, sort_by: str = "repo_score", language: str = None) -> List[dict]:
        """Возвращает топ‑N записей."""
        all_entries = []
        for repo, records in self.entries.items():
            # Берём последний результат для каждого репозитория
            latest = max(records, key=lambda x: x["timestamp"])
            all_entries.append({
                "repo_url": repo,
                **latest,
            })
        if language:
            all_entries = [e for e in all_entries if e.get("language") == language]
        all_entries.sort(key=lambda x: x.get(sort_by, 0), reverse=(sort_by != "risk_score"))
        return all_entries[:limit]

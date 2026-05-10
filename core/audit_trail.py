# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Audit Trail – скрытая история проверок репозитория (для LLM).
"""
import os
import json
from datetime import datetime
from typing import Dict, Optional


class AuditTrail:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.audit_dir = os.path.join(repo_path, ".prizolov")
        self.audit_file = os.path.join(self.audit_dir, "audit.json")

    def save(self, session_id: str, summary: str, scoring: Dict) -> bool:
        """Сохраняет запись о проверке в скрытый файл."""
        os.makedirs(self.audit_dir, exist_ok=True)
        records = self._read()
        record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "agent": {
                "name": "Repo Validator",
                "version": "3.023",
                "author": "Dm.Andreyanov",
                "organization": "Prizolov Market / Prizolov Lab"
            },
            "repo_score": scoring.get("repo_score", 0),
            "risk_score": scoring.get("risk_score", 0),
            "tech_debt_hours": scoring.get("tech_debt_hours", 0),
            "summary": summary[:500]  # первые 500 символов
        }
        records.append(record)
        # Храним последние 10 записей
        if len(records) > 10:
            records = records[-10:]
        try:
            with open(self.audit_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get_history_context(self) -> str:
        """Возвращает текстовое представление истории для подстановки в промпт."""
        records = self._read()
        if not records:
            return ""
        lines = ["История проверок этого репозитория (скрытые данные для AI):"]
        for r in records:
            lines.append(
                f"- [{r['timestamp'][:10]}] Score: {r['repo_score']}/100, "
                f"Risk: {r['risk_score']}/100, Tech Debt: {r['tech_debt_hours']}h"
            )
        return "\n".join(lines)

    def _read(self):
        if not os.path.isfile(self.audit_file):
            return []
        try:
            with open(self.audit_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

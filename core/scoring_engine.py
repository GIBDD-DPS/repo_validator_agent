# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Scoring Engine – вычисляет Repo Score, Risk Score, Tech Debt Penalty, ROI.
"""
import math
from typing import Dict, Any


class ScoringEngine:
    """Собирает данные из отчёта и возвращает итоговые метрики."""

    def __init__(self):
        # Веса для Repo Score (в сумме 1.0)
        self.weights = {
            "code_quality": 0.25,
            "documentation": 0.20,
            "architecture": 0.20,
            "activity": 0.15,
            "security": 0.10,
            "value": 0.10
        }

    def compute(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принимает полный отчёт (report из сессии) и возвращает словарь:
        {
            "repo_score": 0-100,
            "risk_score": 0-100,
            "debt_penalty": float,
            "tech_debt_hours": float,
            "tech_debt_money": float,
            "roi_monthly": float,
            "readiness": float,
        }
        """
        # ---- 1. Code Quality (из линтеров, AST, аудита) ----
        lint_count = self._count_issues(report.get("lint_issues", {}))
        ast_count = self._count_issues(report.get("ast_issues", {}))
        # максимальное ожидаемое число проблем для нормировки (можно настроить)
        max_issues = 50
        quality_raw = max(0, 100 - (lint_count + ast_count) * (100 / max_issues))
        # добавляем аудит
        audit_penalty = 0
        if "audit" in report:
            for key, issues in report["audit"].items():
                audit_penalty += len(issues) * 2  # каждый аудит-ишью снижает на 2 балла
        quality_raw = max(0, quality_raw - audit_penalty)

        # ---- 2. Documentation (из аудита и docstring) ----
        doc_issues = len(report.get("audit", {}).get("documentation", []))
        doc_raw = max(0, 100 - doc_issues * 5)  # каждый отсутствующий docstring = -5 баллов

        # ---- 3. Architecture (из Architecture Auditor) ----
        arch_issues = len(report.get("audit", {}).get("architecture", []))
        arch_raw = max(0, 100 - arch_issues * 10)

        # ---- 4. Activity (из git_stats) ----
        activity_raw = 50  # базовый балл
        git = report.get("git_stats")
        if git and not git.get("error"):
            if git["is_active"]:
                activity_raw += 30
            else:
                activity_raw -= 20
            # бонус за число контрибьюторов
            contrib = git.get("contributors_count", 1)
            activity_raw += min(contrib * 2, 20)  # до +20 за контрибьюторов
        activity_raw = max(0, min(100, activity_raw))

        # ---- 5. Security (из Security Auditor) ----
        sec_issues = len(report.get("audit", {}).get("security", []))
        sec_raw = max(0, 100 - sec_issues * 15)

        # ---- 6. Value (из Semantic AI) ----
        value_raw = 60  # базовый
        sem = report.get("semantic")
        if sem and not sem.get("error"):
            if sem.get("code_purpose"):
                complexity = sem["code_purpose"].get("complexity", "unknown")
                if complexity == "high":
                    value_raw += 20
                elif complexity == "medium":
                    value_raw += 10
            # если есть архитектурная оценка (Architecture Guardian), немного повышаем
            if sem.get("architecture_evaluation"):
                value_raw += 5
            if sem.get("value_estimation"):
                value_raw += 5
        value_raw = max(0, min(100, value_raw))

        # ---- Итоговый Repo Score ----
        repo_score = (
            self.weights["code_quality"] * quality_raw +
            self.weights["documentation"] * doc_raw +
            self.weights["architecture"] * arch_raw +
            self.weights["activity"] * activity_raw +
            self.weights["security"] * sec_raw +
            self.weights["value"] * value_raw
        )

        # ---- Tech Debt (часы) ----
        total_hours = 0.0
        if "audit" in report:
            for issues in report["audit"].values():
                for issue in issues:
                    crit = "MEDIUM"
                    if issue.startswith("[CRITICAL]"):
                        crit = "CRITICAL"
                    elif issue.startswith("[HIGH]"):
                        crit = "HIGH"
                    elif issue.startswith("[LOW]"):
                        crit = "LOW"
                    if crit == "CRITICAL":
                        total_hours += 6
                    elif crit == "HIGH":
                        total_hours += 4
                    elif crit == "MEDIUM":
                        total_hours += 2
                    else:
                        total_hours += 0.5
        total_money = total_hours * 50  # ставка $50/час

        # ---- Debt Penalty ----
        debt_penalty = math.log(1 + total_hours) * 2

        # ---- Risk Score ----
        # Activity Risk
        activity_risk = 50
        if git and not git.get("error"):
            if not git["is_active"]:
                activity_risk += 40
            else:
                activity_risk -= 20
        activity_risk = max(0, min(100, activity_risk))

        # Code Risk
        code_risk = (100 - quality_raw) * 0.7
        # Structure Risk
        structure_risk = (100 - arch_raw) * 0.8
        risk_score = 0.4 * activity_risk + 0.3 * code_risk + 0.3 * structure_risk
        risk_score = max(0, min(100, risk_score))

        # ---- Final Score с учётом долга ----
        final_score = max(0, repo_score - debt_penalty)
        readiness = max(0, 100 - risk_score - debt_penalty * 2)

        # ---- ROI (месячная экономия при исправлении) ----
        roi_monthly = total_hours * 50  # если исправить за месяц, экономия равна стоимости

        return {
            "repo_score": round(final_score, 1),
            "risk_score": round(risk_score, 1),
            "debt_penalty": round(debt_penalty, 1),
            "tech_debt_hours": round(total_hours, 1),
            "tech_debt_money": round(total_money, 0),
            "roi_monthly": round(roi_monthly, 0),
            "readiness": round(readiness, 1),
            # также вернём сырые компоненты для прозрачности
            "components": {
                "quality_raw": round(quality_raw, 1),
                "doc_raw": round(doc_raw, 1),
                "arch_raw": round(arch_raw, 1),
                "activity_raw": round(activity_raw, 1),
                "security_raw": round(sec_raw, 1),
                "value_raw": round(value_raw, 1)
            }
        }

    @staticmethod
    def _count_issues(issues_dict) -> int:
        if isinstance(issues_dict, list):
            return len(issues_dict)
        if isinstance(issues_dict, dict):
            return sum(len(v) for v in issues_dict.values())
        return 0

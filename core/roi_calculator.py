# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
ROI Calculator – вычисляет финансовые метрики технического долга и влияние на бизнес.
"""
import math
from typing import Dict, Any


class ROICalculator:
    """Оценивает стоимость технического долга и потенциальную выгоду от его исправления."""

    def __init__(self, hourly_rate: float = 50.0):
        self.hourly_rate = hourly_rate  # стоимость часа разработчика

    def compute(self, report: Dict[str, Any], scoring: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принимает полный отчёт и результаты скоринга.
        Возвращает словарь с ROI, Business Impact и прогнозом экономии.
        """
        total_hours = scoring.get("tech_debt_hours", 0)
        total_money = scoring.get("tech_debt_money", 0)
        repo_score = scoring.get("repo_score", 100)
        risk_score = scoring.get("risk_score", 50)

        # ---- 1. Технический долг в деньгах ----
        tech_debt_cost = total_hours * self.hourly_rate

        # ---- 2. Прогноз экономии при полном исправлении ----
        # Считаем, что при исправлении мы экономим стоимость долга (упрощённо)
        potential_savings = tech_debt_cost

        # ---- 3. ROI (возврат на инвестиции) = экономия / стоимость исправления * 100% ----
        # Стоимость исправления примерно равна стоимости долга (можно добавить коэффициент сложности)
        fix_cost = total_hours * self.hourly_rate * 0.8  # 20% эффективность инструментов, уменьшаем стоимость
        if fix_cost > 0:
            roi_percent = (potential_savings - fix_cost) / fix_cost * 100
        else:
            roi_percent = 0

        # ---- 4. Business Impact – оценка влияния на бизнес ----
        # На основе Risk Score и Repo Score делаем выводы
        if risk_score > 70:
            business_impact = "Критический: высокая вероятность отказов, потери данных или репутации."
        elif risk_score > 40:
            business_impact = "Средний: возможны инциденты, замедление разработки, увеличение Time-to-Market."
        else:
            business_impact = "Низкий: риски минимальны, техдолг почти не влияет на бизнес."

        # ---- 5. Время до окупаемости (месяцы) ----
        # Предположим, что каждый месяц техдолг растёт на 5% от текущего уровня
        monthly_growth = tech_debt_cost * 0.05
        if monthly_growth > 0:
            payback_months = fix_cost / monthly_growth
        else:
            payback_months = 0

        # ---- 6. Индекс здоровья (Health Index) = Repo Score, нормализованный к 1 ----
        health_index = repo_score / 100

        return {
            "tech_debt_cost": round(tech_debt_cost, 0),
            "potential_savings": round(potential_savings, 0),
            "roi_percent": round(roi_percent, 1),
            "business_impact": business_impact,
            "payback_months": round(payback_months, 1),
            "health_index": round(health_index, 2),
            "fix_cost": round(fix_cost, 0),
        }

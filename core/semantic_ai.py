# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Semantic AI Layer – пять AI-агентов, использующих YandexGPT.
"""
import os
import requests
from typing import Dict, Optional


class SemanticAI:
    """Главный класс для запуска всех семантических агентов."""

    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY", "")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")

    def call_yandex_gpt(self, prompt: str, max_tokens: int = 500) -> str:
        """Универсальный вызов YandexGPT."""
        if not self.api_key:
            return "Ошибка: не настроен YANDEX_API_KEY"
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.5,
                "maxTokens": max_tokens
            },
            "messages": [
                {"role": "system", "text": "Ты — эксперт по анализу программного кода и архитектуры."},
                {"role": "user", "text": prompt}
            ]
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            alternatives = data.get("result", {}).get("alternatives", [])
            if alternatives:
                return alternatives[0].get("message", {}).get("text", "Нет ответа")
            return "Модель не вернула ответ."
        except Exception as e:
            return f"Ошибка YandexGPT: {str(e)}"

    # -----------------------------------------------------------------
    # 1. Code Understanding Agent
    # -----------------------------------------------------------------
    def analyze_code_purpose(self, files_summary: str) -> Dict:
        """
        Определяет назначение проекта, его тип, ключевые компоненты и уровень сложности.
        """
        prompt = (
            "Проанализируй следующую информацию о кодовой базе и ответь строго в формате JSON:\n"
            "{\n"
            "  \"project_type\": \"...\",\n"
            "  \"description\": \"...\",\n"
            "  \"complexity\": \"low|medium|high\",\n"
            "  \"main_components\": [\"...\", ...],\n"
            "  \"key_technologies\": [\"...\", ...]\n"
            "}\n"
            f"Информация о проекте:\n{files_summary[:3000]}"
        )
        response = self.call_yandex_gpt(prompt, max_tokens=500)
        # Пробуем распарсить JSON
        try:
            import json
            # Ищем JSON-объект в ответе
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                return json.loads(json_str)
        except Exception:
            pass
        return {"project_type": "unknown", "description": response, "complexity": "unknown", "main_components": [], "key_technologies": []}

    # -----------------------------------------------------------------
    # 2. Documentation Agent
    # -----------------------------------------------------------------
    def generate_docstring(self, code_snippet: str) -> str:
        """Генерирует docstring для функции/класса."""
        prompt = (
            "Сгенерируй docstring для следующего Python-кода. "
            "Опиши назначение, параметры, возвращаемое значение. "
            "Используй стандартный стиль (Google или NumPy).\n"
            f"Код:\n{code_snippet[:2000]}"
        )
        return self.call_yandex_gpt(prompt, max_tokens=300)

    def suggest_readme(self, project_info: str) -> str:
        """Генерирует README.md на основе информации о проекте."""
        prompt = (
            "Составь README.md для проекта на основе предоставленной информации. "
            "Включи разделы: Описание, Установка, Использование, Зависимости, Лицензия.\n"
            f"Информация:\n{project_info[:2500]}"
        )
        return self.call_yandex_gpt(prompt, max_tokens=800)

    # -----------------------------------------------------------------
    # 3. Architecture Guardian
    # -----------------------------------------------------------------
    def evaluate_architecture(self, structure_summary: str) -> str:
        """
        Оценивает архитектуру: связанность, модульность, масштабируемость.
        """
        prompt = (
            "Оцени архитектуру проекта на основе информации о его структуре, зависимостях и организации кода.\n"
            "Ответь кратко (3-5 предложений) по следующим критериям: связанность, модульность, масштабируемость, "
            "потенциальные архитектурные риски.\n"
            f"Данные:\n{structure_summary[:2500]}"
        )
        return self.call_yandex_gpt(prompt, max_tokens=400)

    # -----------------------------------------------------------------
    # 4. Risk Agent
    # -----------------------------------------------------------------
    def assess_risk(self, project_data: str) -> str:
        """
        Оценивает риски: заброшенность, плохая структура, баги.
        """
        prompt = (
            "Оцени риски проекта на основе предоставленных данных. "
            "Укажи вероятность того, что проект заброшен, имеет плохую структуру или содержит критические баги. "
            "Ответь кратко (3-5 предложений).\n"
            f"Данные:\n{project_data[:2500]}"
        )
        return self.call_yandex_gpt(prompt, max_tokens=400)

    # -----------------------------------------------------------------
    # 5. Value Agent
    # -----------------------------------------------------------------
    def estimate_value(self, project_description: str) -> str:
        """
        Определяет ценность проекта: возможные применения, монетизация, польза.
        """
        prompt = (
            "Оцени ценность проекта на основе его описания. "
            "Где его можно применить? Можно ли на нём заработать? "
            "Ответь кратко (3-5 предложений).\n"
            f"Описание проекта:\n{project_description[:2500]}"
        )
        return self.call_yandex_gpt(prompt, max_tokens=400)

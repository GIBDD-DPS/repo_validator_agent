# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Contextual Mentor – генерирует конкретные примеры исправления проблем с кодом.
"""
import os
import requests
from typing import Optional


class ContextualMentor:
    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY", "")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")

    def suggest_fix(self, issue_description: str, file_context: Optional[str] = None) -> str:
        """
        Принимает описание проблемы (например, из аудита) и, опционально, фрагмент кода.
        Возвращает рекомендацию с примером исправления.
        """
        if not self.api_key:
            return "Ошибка: не настроен YANDEX_API_KEY"

        prompt = (
            "Ты — опытный разработчик-наставник. Ниже описана проблема в коде. "
            "Предложи конкретное исправление с примером кода (до и после). "
            "Объясни, почему это исправление улучшит качество кода.\n"
            f"Проблема: {issue_description}\n"
        )
        if file_context:
            prompt += f"Фрагмент кода:\n{file_context[:2000]}\n"

        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.4,
                "maxTokens": 800
            },
            "messages": [
                {"role": "system", "text": "Ты — ментор по программированию."},
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
            return f"Ошибка при обращении к YandexGPT: {str(e)}"

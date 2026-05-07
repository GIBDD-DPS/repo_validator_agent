# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Smart Triage – запрашивает у AI приоритетный порядок исправления проблем и краткое обоснование.
"""
import os
import requests
from typing import List, Dict


class SmartTriage:
    def __init__(self):
        self.api_key = os.getenv("YANDEX_API_KEY", "")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID", "b1gfhnp4aeamnaflt8g0")

    def prioritize(self, issues: List[str]) -> List[Dict[str, str]]:
        """
        Принимает список строк с описанием проблем (из аудита, линтеров и т.д.)
        Возвращает список словарей с ключами: issue (исходный текст), priority (1-10),
        reason (краткое обоснование), effort (оценка времени на исправление).
        """
        if not issues:
            return []

        # Ограничим количество проблем, чтобы не превысить лимит токенов
        sample = issues[:15]
        joined = "\n".join(f"- {i}" for i in sample)
        prompt = (
            "Ниже перечислены проблемы, найденные в коде проекта. "
            "Проранжируй их по приоритетности исправления (1 – самый высокий приоритет, 10 – самый низкий). "
            "Для каждой проблемы укажи: приоритет (число), краткое обоснование (1-2 предложения), примерное время на исправление (в часах). "
            "Верни ответ строго в формате JSON-массива:\n"
            '[{"issue": "текст проблемы", "priority": число, "reason": "обоснование", "effort": "X часов"}]\n'
            f"Проблемы:\n{joined}"
        )
        try:
            response = self._call_yandex_gpt(prompt, max_tokens=600)
            # Попытка распарсить JSON
            import json
            start = response.find('[')
            end = response.rfind(']')
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                triage = json.loads(json_str)
                # Оставим только нужные поля
                result = []
                for item in triage:
                    if isinstance(item, dict) and 'issue' in item:
                        result.append({
                            'issue': item.get('issue', ''),
                            'priority': item.get('priority', 5),
                            'reason': item.get('reason', ''),
                            'effort': item.get('effort', '')
                        })
                return result
        except Exception:
            pass
        # Fallback: вернём исходные проблемы без приоритезации
        return [{'issue': i, 'priority': 5, 'reason': 'AI не смогла обработать', 'effort': '?'} for i in sample]

    def _call_yandex_gpt(self, prompt: str, max_tokens: int) -> str:
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
                "temperature": 0.4,
                "maxTokens": max_tokens
            },
            "messages": [
                {"role": "system", "text": "Ты — эксперт по управлению техническим долгом."},
                {"role": "user", "text": prompt}
            ]
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            alternatives = data.get("result", {}).get("alternatives", [])
            if alternatives:
                return alternatives[0].get("message", {}).get("text", "")
            return ""
        except Exception as e:
            return f"Ошибка YandexGPT: {str(e)}"

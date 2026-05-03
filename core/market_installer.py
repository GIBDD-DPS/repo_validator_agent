import requests
import zipfile
import io
import os
from typing import List, Dict

class MarketInstaller:
    MARKET_API = "https://market.prizolov.ru/api/v1"  # замените на реальный эндпоинт

    def __init__(self, target_dir: str = "/tmp/market_tools"):
        self.target_dir = target_dir
        os.makedirs(target_dir, exist_ok=True)

    def install(self, tool_names: List[str]) -> Dict[str, bool]:
        """Скачивает и устанавливает инструменты. Возвращает словарь {имя: успех}."""
        results = {}
        for name in tool_names:
            try:
                info = self._get_tool_info(name)
                if not info:
                    results[name] = False
                    continue
                resp = requests.get(info["download_url"], timeout=30)
                resp.raise_for_status()
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
                    zf.extractall(self.target_dir)
                results[name] = True
            except Exception as e:
                print(f"Ошибка установки {name}: {e}")
                results[name] = False
        return results

    def _get_tool_info(self, name: str) -> dict:
        # Заглушка – в реальности запрос к API маркета
        fake_db = {
            "prizolov-optimizer": {
                "download_url": "https://market.prizolov.ru/tools/optimizer.zip",
                "version": "1.0.0"
            },
            "prizolov-security": {
                "download_url": "https://market.prizolov.ru/tools/security.zip",
                "version": "2.1.0"
            },
            "prizolov-style": {
                "download_url": "https://market.prizolov.ru/tools/style.zip",
                "version": "1.5.3"
            }
        }
        return fake_db.get(name)

import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as redis
from config import settings

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis = None
        self.enabled = False

    async def connect(self):
        try:
            self.redis = await redis.from_url(
                f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                decode_responses=True,
                socket_connect_timeout=2
            )
            await self.redis.ping()
            self.enabled = True
            logger.info("Redis подключён, кэширование включено")
        except Exception as e:
            logger.warning(f"Redis недоступен: {e}. Кэширование отключено.")
            self.redis = None
            self.enabled = False

    async def get_cached_report(self, repo_url: str, branch: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        if not self.enabled or not self.redis:
            return None
        try:
            key = f"repo:{repo_url}:{branch or 'main'}:{commit_sha}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Ошибка чтения кэша: {e}")
        return None

    async def set_cached_report(self, repo_url: str, branch: str, commit_sha: str, report: Dict[str, Any]):
        if not self.enabled or not self.redis:
            return
        try:
            key = f"repo:{repo_url}:{branch or 'main'}:{commit_sha}"
            await self.redis.setex(key, settings.cache_ttl_seconds, json.dumps(report, default=str))
        except Exception as e:
            logger.warning(f"Ошибка записи кэша: {e}")

    async def close(self):
        if self.redis:
            await self.redis.close()

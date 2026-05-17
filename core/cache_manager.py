import json
from typing import Optional, Dict, Any
import redis.asyncio as redis
from config import settings

class CacheManager:
    def __init__(self):
        self.redis = None

    async def connect(self):
        if self.redis is None:
            self.redis = await redis.from_url(
                f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
                decode_responses=True
            )

    async def get_cached_report(self, repo_url: str, branch: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        await self.connect()
        key = f"repo:{repo_url}:{branch or 'main'}:{commit_sha}"
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_cached_report(self, repo_url: str, branch: str, commit_sha: str, report: Dict[str, Any]):
        await self.connect()
        key = f"repo:{repo_url}:{branch or 'main'}:{commit_sha}"
        # Сериализация с обработкой datetime
        await self.redis.setex(key, settings.cache_ttl_seconds, json.dumps(report, default=str))

    async def close(self):
        if self.redis:
            await self.redis.close()

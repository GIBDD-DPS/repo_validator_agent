import os
from dataclasses import dataclass
from typing import List
from core.repository_scanner import FileEntry


@dataclass
class ProjectType:
    name: str
    tags: List[str]
    confidence: float


class ProjectDetector:
    """
    Определяет тип проекта по структуре файлов.
    Поддержка:
    - Python
    - Node.js
    - Go
    - Java
    - PHP
    - Docker
    - Frontend (React/Vue)
    - Монорепо
    """

    def detect(self, files: List[FileEntry]) -> ProjectType:
        paths = [f.rel_path.lower() for f in files]

        # Python
        if any(p.endswith(".py") for p in paths):
            if "requirements.txt" in paths or "pyproject.toml" in paths:
                return ProjectType("python", ["python", "backend"], 0.95)

        # Node.js
        if "package.json" in paths:
            if "next.config.js" in paths:
                return ProjectType("nextjs", ["node", "frontend", "react"], 0.95)
            if "vite.config.js" in paths:
                return ProjectType("vite", ["node", "frontend"], 0.9)
            return ProjectType("nodejs", ["node", "js"], 0.9)

        # Go
        if "go.mod" in paths:
            return ProjectType("go", ["go", "backend"], 0.95)

        # Java
        if any(p.endswith(".java") for p in paths):
            return ProjectType("java", ["java", "backend"], 0.8)

        # PHP
        if any(p.endswith(".php") for p in paths):
            return ProjectType("php", ["php", "backend"], 0.8)

        # Docker
        if "dockerfile" in paths:
            return ProjectType("dockerized", ["docker", "container"], 0.7)

        # Frontend
        if any(p.endswith(".html") for p in paths) or "src/app" in paths:
            return ProjectType("frontend", ["frontend"], 0.6)

        # Монорепо
        if any("packages/" in p for p in paths):
            return ProjectType("monorepo", ["monorepo"], 0.7)

        # Неизвестно
        return ProjectType("unknown", ["unknown"], 0.1)

import hashlib
from dataclasses import dataclass
from typing import List, Dict

from core.repository_scanner import FileEntry


@dataclass
class DuplicateGroup:
    size: int
    files: List[str]


@dataclass
class StructureAnalysis:
    by_extension: Dict[str, int]
    large_files: List[str]
    duplicates: List[DuplicateGroup]


class StructureAnalyzer:
    """
    Анализирует структуру репозитория:
    - статистика по расширениям
    - крупные файлы
    - дубликаты (по размеру + хэшу)
    """

    def analyze(self, files: List[FileEntry]) -> StructureAnalysis:
        by_ext: Dict[str, int] = {}
        large_files: List[str] = []
        duplicates: List[DuplicateGroup] = []

        # 1. Статистика по расширениям
        for f in files:
            name = f.rel_path.lower()
            if "." in name:
                ext = name.rsplit(".", 1)[-1]
            else:
                ext = ""
            by_ext[ext] = by_ext.get(ext, 0) + 1

            # 2. Крупные файлы (условно > 1 МБ)
            if f.size > 1_000_000:
                large_files.append(f.rel_path)

        # 3. Дубликаты по размеру + хэшу
        size_map: Dict[int, List[FileEntry]] = {}
        for f in files:
            size_map.setdefault(f.size, []).append(f)

        for size, group in size_map.items():
            if len(group) < 2 or size == 0:
                continue

            hash_map: Dict[str, List[FileEntry]] = {}
            for fe in group:
                if not fe.is_text:
                    # для бинарных тоже можно, но не обязательно
                    pass
                try:
                    h = self._hash_file(fe.path)
                except Exception:
                    continue
                hash_map.setdefault(h, []).append(fe)

            for h, dup_group in hash_map.items():
                if len(dup_group) > 1:
                    duplicates.append(
                        DuplicateGroup(
                            size=size,
                            files=[d.rel_path for d in dup_group],
                        )
                    )

        return StructureAnalysis(
            by_extension=by_ext,
            large_files=large_files,
            duplicates=duplicates,
        )

    def _hash_file(self, path: str) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

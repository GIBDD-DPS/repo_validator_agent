import os
from dataclasses import dataclass
from typing import List


@dataclass
class FileEntry:
    path: str
    rel_path: str
    size: int
    is_text: bool
    content: str | None


class RepositoryScanner:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def scan(self) -> List[FileEntry]:
        files: List[FileEntry] = []

        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, self.root_dir)

                try:
                    size = os.path.getsize(full_path)
                except OSError:
                    size = 0

                content = None
                is_text = False
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        is_text = True
                except Exception:
                    content = None
                    is_text = False

                files.append(
                    FileEntry(
                        path=full_path,
                        rel_path=rel_path,
                        size=size,
                        is_text=is_text,
                        content=content,
                    )
                )

        return files

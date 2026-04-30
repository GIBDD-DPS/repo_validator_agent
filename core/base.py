from dataclasses import dataclass
from typing import Optional

@dataclass
class FileEntry:
    path: str
    rel_path: str
    content: Optional[str] = None
    is_text: bool = False

# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

from dataclasses import dataclass
from typing import Optional

@dataclass
class FileEntry:
    path: str
    rel_path: str
    content: Optional[str] = None
    is_text: bool = False

"""
Менеджер авторских прав — ищет, добавляет, заменяет copyright в текстовых файлах проекта.
"""
import os
import re
from typing import Dict, List, Optional, Tuple

# Расширения файлов, которые считаем текстовыми (можно дополнить)
TEXT_EXTENSIONS = {
    '.py': '#',
    '.js': '//',
    '.ts': '//',
    '.jsx': '//',
    '.tsx': '//',
    '.css': '/*',     # будет закрыт */
    '.scss': '//',
    '.less': '//',
    '.html': '<!--',
    '.htm': '<!--',
    '.xml': '<!--',
    '.md': '<!--',
    '.markdown': '<!--',
    '.yaml': '#',
    '.yml': '#',
    '.toml': '#',
    '.cfg': '#',
    '.ini': '#',
    '.sh': '#',
    '.bash': '#',
    '.zsh': '#',
    '.fish': '#',
    '.ps1': '#',
    '.bat': 'REM',
    '.cmd': 'REM',
    '.java': '//',
    '.kt': '//',
    '.c': '/*',
    '.h': '/*',
    '.cpp': '//',
    '.hpp': '//',
    '.cs': '//',
    '.go': '//',
    '.rs': '//',
    '.swift': '//',
    '.rb': '#',
    '.php': '//',
    '.pl': '#',
    '.r': '#',
    '.sql': '--',
    '.lua': '--',
    '.vim': '"',
    '.dockerfile': '#',
    '.editorconfig': '#',
}


class CopyrightManager:
    """Ищет, добавляет или заменяет комментарии с авторскими правами."""

    COMMENT_PATTERNS = [
        re.compile(r'^\s*#\s*Copyright\s*(.*)', re.IGNORECASE),          # Python, YAML etc.
        re.compile(r'^\s*//\s*Copyright\s*(.*)', re.IGNORECASE),         # JS, TS, Java, C#
        re.compile(r'^\s*/\*\s*Copyright\s*(.*?)\*/', re.IGNORECASE),   # CSS/многострочный открытый
        re.compile(r'^\s*<!--\s*Copyright\s*(.*?)-->', re.IGNORECASE),  # HTML, MD
        re.compile(r'^\s*REM\s*Copyright\s*(.*)', re.IGNORECASE),       # Batch
        re.compile(r'^\s*\"\s*Copyright\s*(.*)', re.IGNORECASE),        # Vim
        re.compile(r'^\s*--\s*Copyright\s*(.*)', re.IGNORECASE),        # SQL, Lua
        re.compile(r'^\s*%\s*Copyright\s*(.*)', re.IGNORECASE),         # Erlang, Matlab (редко)
    ]

    def check_copyright(self, files: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Возвращает список уникальных найденных копирайтов с их исходным текстом и файлами.
        Каждый элемент: {"text": "Copyright ...", "files": ["file1.py", ...]}
        """
        found = {}  # текст -> список файлов
        for path, content in files.items():
            first_line = content.split('\n')[0].strip() if content else ''
            if not first_line:
                continue
            # Попробуем сопоставить с образцами
            for pattern in self.COMMENT_PATTERNS:
                match = pattern.match(first_line)
                if match:
                    copyright_text = match.group(1).strip()
                    if copyright_text not in found:
                        found[copyright_text] = []
                    found[copyright_text].append(path)
                    break
        # Формируем список
        result = []
        for text, file_list in found.items():
            result.append({"text": text, "files": file_list[:5]})  # первые 5 для отображения
        return result

    def apply_copyright(self,
                        files: Dict[str, str],
                        author: Optional[str] = None,
                        company: Optional[str] = None,
                        replace_existing: bool = False) -> Dict[str, str]:
        """
        Добавляет или заменяет copyright во всех текстовых файлах.
        Возвращает обновлённый словарь {путь: содержимое}.
        """
        year = "2026"  # можно автоматизировать через datetime
        # Формируем текст копирайта
        if company and author:
            copyright_line = f"Copyright (c) {year} {author}, {company}"
        elif company:
            copyright_line = f"Copyright (c) {year} {company}"
        elif author:
            copyright_line = f"Copyright (c) {year} {author}"
        else:
            copyright_line = f"Copyright (c) {year}"

        new_files = {}
        for path, content in files.items():
            ext = os.path.splitext(path)[1].lower()
            base = os.path.basename(path).lower()
            if ext not in TEXT_EXTENSIONS and base not in TEXT_EXTENSIONS:
                new_files[path] = content  # не модифицируем бинарные/неизвестные
                continue

            comment_char = TEXT_EXTENSIONS.get(ext) or TEXT_EXTENSIONS.get(base, '#')
            # Формируем шапку
            if comment_char == '#':
                header = f"# {copyright_line}\n"
            elif comment_char == '//':
                header = f"// {copyright_line}\n"
            elif comment_char.startswith('/*'):
                header = f"/* {copyright_line} */\n"
            elif comment_char == '<!--':
                header = f"<!-- {copyright_line} -->\n"
            elif comment_char.upper() == 'REM':
                header = f"REM {copyright_line}\n"
            elif comment_char == '"':
                header = f'" {copyright_line}\n'
            elif comment_char == '--':
                header = f"-- {copyright_line}\n"
            else:
                header = f"# {copyright_line}\n"

            # Удаляем старый копирайт в первой строке, если нужно заменить
            if replace_existing:
                lines = content.splitlines(keepends=True)
                if lines:
                    first = lines[0].strip()
                    is_copyright = any(p.match(first) for p in self.COMMENT_PATTERNS)
                    if is_copyright:
                        lines = lines[1:]  # удаляем первую строку
                content = ''.join(lines)

            # Вставляем шапку в начало
            new_content = header + content
            new_files[path] = new_content

        return new_files

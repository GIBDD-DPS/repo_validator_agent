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
        re.compile(r'^\s*#\s*Copyright\s*(.*)', re.IGNORECASE),
        re.compile(r'^\s*//\s*Copyright\s*(.*)', re.IGNORECASE),
        re.compile(r'^\s*/\*\s*Copyright\s*(.*?)\*/', re.IGNORECASE),
        re.compile(r'^\s*<!--\s*Copyright\s*(.*?)-->', re.IGNORECASE),
        re.compile(r'^\s*REM\s*Copyright\s*(.*)', re.IGNORECASE),
        re.compile(r'^\s*\"\s*Copyright\s*(.*)', re.IGNORECASE),
        re.compile(r'^\s*--\s*Copyright\s*(.*)', re.IGNORECASE),
        re.compile(r'^\s*%\s*Copyright\s*(.*)', re.IGNORECASE),
    ]

    def check_copyright(self, files: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Возвращает список уникальных найденных копирайтов с их исходным текстом и файлами.
        Каждый элемент: {"text": "Copyright ...", "files": ["file1.py", ...]}
        """
        found = {}
        for path, content in files.items():
            first_line = content.split('\n')[0].strip() if content else ''
            if not first_line:
                continue
            for pattern in self.COMMENT_PATTERNS:
                match = pattern.match(first_line)
                if match:
                    copyright_text = match.group(1).strip()
                    if copyright_text not in found:
                        found[copyright_text] = []
                    found[copyright_text].append(path)
                    break
        result = []
        for text, file_list in found.items():
            result.append({"text": text, "files": file_list[:5]})
        return result

    def apply_copyright(self,
                        files: Dict[str, str],
                        copyright_text: str,
                        skip_existing: bool = True) -> Dict[str, str]:
        """
        Добавляет copyright_text в начало файлов, в которых ещё нет никакого копирайта.
        Если skip_existing=True (по умолчанию), файлы с уже существующим копирайтом не изменяются.
        Возвращает обновлённый словарь {путь: содержимое}.
        """
        new_files = {}
        for path, content in files.items():
            ext = os.path.splitext(path)[1].lower()
            base = os.path.basename(path).lower()
            if ext not in TEXT_EXTENSIONS and base not in TEXT_EXTENSIONS:
                new_files[path] = content
                continue

            # Проверяем, есть ли уже копирайт
            first_line = (content.split('\n')[0].strip()) if content else ''
            has_copyright = any(p.match(first_line) for p in self.COMMENT_PATTERNS)
            if skip_existing and has_copyright:
                # Не трогаем файлы с существующим копирайтом
                new_files[path] = content
                continue

            # Определяем символ комментария
            comment_char = TEXT_EXTENSIONS.get(ext) or TEXT_EXTENSIONS.get(base, '#')
            if comment_char == '#':
                header = f"# {copyright_text}\n"
            elif comment_char == '//':
                header = f"// {copyright_text}\n"
            elif comment_char.startswith('/*'):
                header = f"/* {copyright_text} */\n"
            elif comment_char == '<!--':
                header = f"<!-- {copyright_text} -->\n"
            elif comment_char.upper() == 'REM':
                header = f"REM {copyright_text}\n"
            elif comment_char == '"':
                header = f'" {copyright_text}\n'
            elif comment_char == '--':
                header = f"-- {copyright_text}\n"
            else:
                header = f"# {copyright_text}\n"

            # Если ранее был копирайт и skip_existing=False, то удаляем первую строку
            if not skip_existing and has_copyright:
                lines = content.splitlines(keepends=True)
                if lines:
                    lines = lines[1:]
                content = ''.join(lines)
            new_content = header + content
            new_files[path] = new_content

        return new_files

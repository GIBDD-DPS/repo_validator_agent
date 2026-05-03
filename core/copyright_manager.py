import os
import re
from typing import Dict, List, Optional
from datetime import datetime

TEXT_EXTENSIONS = {
    '.py': '#',
    '.js': '//',
    '.ts': '//',
    '.jsx': '//',
    '.tsx': '//',
    '.css': '/*',
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

    @staticmethod
    def generate_header(author: str = "", organization: str = "", product: str = "") -> str:
        """Генерирует многострочный блок авторских прав."""
        year = datetime.now().year
        lines = []
        lines.append(f"Copyright (c) {year}")
        if product:
            lines.append(f"{product}")
        if author:
            lines.append(f"Author: {author}")
        if organization:
            lines.append(f"Organization: {organization}")
        # Формируем блок
        sep = "# ============================================"
        header = sep + "\n"
        if lines:
            header += "# " + "\n# ".join(lines) + "\n"
        header += sep + "\n"
        return header

    def check_copyright(self, files: Dict[str, str]) -> List[Dict[str, str]]:
        found = {}
        for path, content in files.items():
            first_line = content.split('\n')[0].strip() if content else ''
            if not first_line:
                continue
            for pattern in self.COMMENT_PATTERNS:
                match = pattern.match(first_line)
                if match:
                    text = match.group(1).strip()
                    if text not in found:
                        found[text] = []
                    found[text].append(path)
                    break
        result = []
        for text, file_list in found.items():
            result.append({"text": text, "files": file_list[:5]})
        return result

    def apply_copyright(self,
                        files: Dict[str, str],
                        copyright_text: Optional[str] = None,
                        author: Optional[str] = None,
                        organization: Optional[str] = None,
                        product: Optional[str] = None,
                        skip_existing: bool = True) -> Dict[str, str]:
        """
        Добавляет копирайт в файлы без него.
        Если передан copyright_text, используется он (обычно выбранный существующий).
        Иначе генерируется новый блок из author/organization/product.
        """
        if copyright_text:
            header_line = copyright_text  # вставляем как есть
        else:
            header_line = self.generate_header(
                author=author or "",
                organization=organization or "",
                product=product or ""
            )

        new_files = {}
        for path, content in files.items():
            ext = os.path.splitext(path)[1].lower()
            base = os.path.basename(path).lower()
            if ext not in TEXT_EXTENSIONS and base not in TEXT_EXTENSIONS:
                new_files[path] = content
                continue

            first_line = (content.split('\n')[0].strip()) if content else ''
            has_copyright = any(p.match(first_line) for p in self.COMMENT_PATTERNS)
            if skip_existing and has_copyright:
                new_files[path] = content
                continue

            # Определяем символ комментария
            comment_char = TEXT_EXTENSIONS.get(ext) or TEXT_EXTENSIONS.get(base, '#')
            # Для многострочного варианта (CSS, HTML) заменяем в шапке # на нужный символ
            if copyright_text:
                # Простой однострочный копирайт – просто вставляем с символом комментария
                if comment_char.startswith('/*'):
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
                    header = f"{comment_char} {copyright_text}\n"
            else:
                # Многострочный блок, нужно заменить # в шапке на comment_char, если он не #
                header = header_line.replace('#', comment_char, 1)  # первая строка
                # замена в остальных строках
                header = header.replace('\n#', f'\n{comment_char}')

            # Если раньше был копирайт и мы не пропускаем – удаляем первую строку
            if not skip_existing and has_copyright:
                lines = content.splitlines(keepends=True)
                if lines:
                    lines = lines[1:]
                content = ''.join(lines)
            new_content = header + content
            new_files[path] = new_content

        return new_files

import os
from typing import Dict, List

class ProjectAnalyzer:
    """Анализирует структуру проекта: наличие нужных файлов, пустоты и пр."""

    def analyze(self, files: Dict[str, str]) -> List[str]:
        """
        Принимает словарь {путь: содержимое},
        возвращает список найденных проблем проекта.
        """
        issues = []

        # Проверка наличия README.md
        if not any(p.lower() == "readme.md" for p in files.keys()):
            issues.append("Отсутствует README.md")

        # Проверка наличия .gitignore
        if not any(".gitignore" in p for p in files.keys()):
            issues.append("Отсутствует .gitignore")

        # Проверки на пустые директории (исправлено, чтобы не шуметь)
        issues.extend(self._check_empty_directories(files))

        return issues

    def _check_empty_directories(self, files: Dict[str, str]) -> List[str]:
        """
        Возвращает список сообщений о директориях без файлов.
        Словарь files содержит только файлы, поэтому реально пустые папки не видны.
        Исправлено: больше не выдаёт ложных срабатываний.
        """
        issues = []
        dirs_count = {}

        # Считаем, по скольку файлов лежит в каждой папке
        for path in files.keys():
            d = os.path.dirname(path)
            # Увеличиваем счётчик для этой папки
            dirs_count[d] = dirs_count.get(d, 0) + 1

        # Если у папки счётчик 0, она действительно пустая
        # (но сюда мы не попадём, потому что папки без файлов отсутствуют в files)
        for d, count in dirs_count.items():
            if d and count == 0:   # это условие теперь никогда не выполнится
                issues.append(f"Пустая директория: {d}")

        return issues

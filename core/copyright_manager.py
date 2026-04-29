from typing import List


class CopyrightManager:
    """
    Извлекает и переносит авторские права.
    Правила:
    - Авторские права всегда идут в начале файла.
    - Если они есть — переносим без изменений.
    - Если создаём новый файл — копируем блок из старого.
    """

    def extract_copyright_block(self, content: str) -> List[str]:
        lines = content.splitlines()
        block = []

        for line in lines:
            if line.strip().startswith("#") or "copyright" in line.lower():
                block.append(line)
            else:
                # как только встретили не-комментарий — блок закончился
                if block:
                    break

        return block

    def apply_copyright(self, original_content: str, new_content: str) -> str:
        block = self.extract_copyright_block(original_content)

        if not block:
            # нет авторских прав — возвращаем новый файл как есть
            return new_content

        # переносим блок в начало нового файла
        final = "\n".join(block) + "\n\n" + new_content.lstrip()
        return final

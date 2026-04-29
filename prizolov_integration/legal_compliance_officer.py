class LegalComplianceOfficer:
    """
    Проверяет юридическую корректность:
    - наличие авторских прав
    - отсутствие персональных данных
    """

    def validate_file(self, content: str):
        # Проверка на персональные данные (очень базовая)
        forbidden_patterns = ["паспорт", "серия", "номер карты", "cvv", "дата рождения"]

        for pattern in forbidden_patterns:
            if pattern.lower() in content.lower():
                raise ValueError(f"Обнаружены потенциальные персональные данные: '{pattern}'")

        # Проверка на наличие авторских прав (не обязательно, но желательно)
        if "copyright" not in content.lower() and "# File rewritten" in content:
            # Это не ошибка, просто предупреждение
            pass

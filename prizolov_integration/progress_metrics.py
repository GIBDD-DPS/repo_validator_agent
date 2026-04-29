class ProgressMetrics:
    """
    Метрики прогресса:
    - сколько файлов проанализировано
    - сколько исправлено
    """

    def __init__(self):
        self.files_analyzed = 0
        self.files_fixed = 0

    def increment_files_analyzed(self):
        self.files_analyzed += 1

    def increment_files_fixed(self):
        self.files_fixed += 1

from typing import List


class AntiHallucinationShield:
    """
    Фильтрует потенциально ложные проблемы.
    Пока что логика простая:
    - если проблема слишком общая или бессмысленная — удаляем
    """

    def filter_issues(self, issues: List[str]) -> List[str]:
        filtered = []

        for issue in issues:
            if "??? " in issue:
                # пример бессмысленной галлюцинации
                continue
            if len(issue.strip()) < 3:
                continue

            filtered.append(issue)

        return filtered

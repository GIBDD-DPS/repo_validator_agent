import requests
import base64


class GitHubConnector:
    """
    Загружает дерево репозитория через GitHub API /git/trees (рекурсивно).
    """

    def __init__(self, repo_url: str):
        self.repo_url = repo_url.rstrip("/")
        self.user, self.repo = self._extract_user_repo(self.repo_url)

        # ВАЖНО: api_base должен быть создан ДО вызова _detect_default_branch()
        self.api_base = f"https://api.github.com/repos/{self.user}/{self.repo}"

        # Теперь можно определять ветку
        self.branch = self._detect_default_branch()

    # ---------------------------------------------------------
    # Извлекаем user/repo
    # ---------------------------------------------------------
    def _extract_user_repo(self, url: str):
        parts = url.replace("https://github.com/", "").split("/")
        return parts[0], parts[1]

    # ---------------------------------------------------------
    # Определяем ветку (main/master)
    # ---------------------------------------------------------
    def _detect_default_branch(self) -> str:
        url = f"{self.api_base}"
        r = requests.get(url)
        if r.status_code == 200:
            return r.json().get("default_branch", "main")
        return "main"

    # ---------------------------------------------------------
    # Получаем дерево репозитория целиком (диагностика включена)
    # ---------------------------------------------------------
    def fetch_tree(self):
        url = f"{self.api_base}/git/trees/{self.branch}?recursive=1"
        r = requests.get(url)

        # Диагностика — выводим, что вернул GitHub
        print(">>> FETCH TREE URL:", url)
        print(">>> STATUS:", r.status_code)
        print(">>> RESPONSE:", r.text[:500])  # первые 500 символов ответа

        if r.status_code != 200:
            raise RuntimeError("Не удалось получить дерево репозитория")

        data = r.json()
        return data.get("tree", [])


    # ---------------------------------------------------------
    # Скачиваем файл по SHA
    # ---------------------------------------------------------
    def fetch_file(self, sha: str) -> str:
        url = f"{self.api_base}/git/blobs/{sha}"
        r = requests.get(url)

        if r.status_code != 200:
            return ""

        data = r.json()
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8")

        return ""

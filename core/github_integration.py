import requests
import base64
import time
from typing import Dict, Optional

class GitHubIntegration:
    def __init__(self, token: str):
        self.token = token
        self.api = "https://api.github.com"

    def create_pr(self, repo_url: str, files: Dict[str, str], base_branch: str = "main",
                  title: str = "Repo Validator fixes", body: str = "") -> Optional[str]:
        """Возвращает URL созданного PR или None при ошибке."""
        # owner/repo из URL
        parts = repo_url.rstrip('/').replace('.git', '').split('/')
        owner = parts[-2]
        repo = parts[-1]

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # 1. Получаем SHA base branch
        ref_url = f"{self.api}/repos/{owner}/{repo}/git/ref/heads/{base_branch}"
        ref_resp = requests.get(ref_url, headers=headers)
        ref_resp.raise_for_status()
        base_sha = ref_resp.json()["object"]["sha"]

        # 2. Создаём новую ветку
        new_branch = f"repo-validator-fixes-{int(time.time())}"
        branch_data = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
        branch_resp = requests.post(f"{self.api}/repos/{owner}/{repo}/git/refs",
                                    headers=headers, json=branch_data)
        branch_resp.raise_for_status()

        # 3. Создаём blobs и tree
        blobs = []
        for path, content in files.items():
            blob_resp = requests.post(
                f"{self.api}/repos/{owner}/{repo}/git/blobs",
                headers=headers,
                json={
                    "content": base64.b64encode(content.encode()).decode(),
                    "encoding": "base64"
                }
            )
            blob_resp.raise_for_status()
            blobs.append({
                "path": path,
                "sha": blob_resp.json()["sha"],
                "mode": "100644",
                "type": "blob"
            })

        tree_data = {"base_tree": base_sha, "tree": blobs}
        tree_resp = requests.post(f"{self.api}/repos/{owner}/{repo}/git/trees",
                                  headers=headers, json=tree_data)
        tree_resp.raise_for_status()
        tree_sha = tree_resp.json()["sha"]

        # 4. Создаём коммит
        commit_data = {
            "message": title,
            "tree": tree_sha,
            "parents": [base_sha]
        }
        commit_resp = requests.post(f"{self.api}/repos/{owner}/{repo}/git/commits",
                                    headers=headers, json=commit_data)
        commit_resp.raise_for_status()
        new_commit_sha = commit_resp.json()["sha"]

        # Обновляем ref ветки
        update_data = {"sha": new_commit_sha, "force": False}
        update_resp = requests.patch(
            f"{self.api}/repos/{owner}/{repo}/git/refs/heads/{new_branch}",
            headers=headers, json=update_data
        )
        update_resp.raise_for_status()

        # 5. Открываем Pull Request
        pr_data = {"title": title, "head": new_branch, "base": base_branch, "body": body}
        pr_resp = requests.post(f"{self.api}/repos/{owner}/{repo}/pulls",
                                headers=headers, json=pr_data)
        pr_resp.raise_for_status()
        return pr_resp.json()["html_url"]

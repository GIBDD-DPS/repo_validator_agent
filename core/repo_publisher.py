# ============================================
# Copyright (c) 2026
# Prizolov Agent OS v3.023
# Author: Dm.Andreyanov
# Organization: Prizolov Market / Prizolov Lab
# ============================================

"""
Repo Publisher – публикует результаты проверки в целевой репозиторий (issue, label).
"""
import requests
from typing import Optional


class RepoPublisher:
    def __init__(self, github_token: str):
        self.token = github_token
        self.api_base = "https://api.github.com"

    def publish_issue(self, repo_url: str, title: str, body: str) -> Optional[str]:
        """Создаёт Issue с отчётом. Возвращает URL созданного issue."""
        owner, repo = self._parse_repo_url(repo_url)
        if not owner or not repo:
            return None
        url = f"{self.api_base}/repos/{owner}/{repo}/issues"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {"title": title, "body": body}
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 201:
            return resp.json().get("html_url")
        return None

    def set_label(self, repo_url: str, label_name: str, color: str = "0e8a16", description: str = "") -> bool:
        """Создаёт или обновляет метку (Label) в репозитории. Возвращает успех."""
        owner, repo = self._parse_repo_url(repo_url)
        if not owner or not repo:
            return False
        url = f"{self.api_base}/repos/{owner}/{repo}/labels"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {"name": label_name, "color": color, "description": description}
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 201:
            return True
        if resp.status_code == 422:
            update_url = f"{self.api_base}/repos/{owner}/{repo}/labels/{label_name}"
            resp = requests.patch(update_url, headers=headers, json=payload)
            return resp.status_code == 200
        return False

    def _parse_repo_url(self, repo_url: str):
        parts = repo_url.rstrip("/").replace(".git", "").split("/")
        if len(parts) >= 2:
            return parts[-2], parts[-1]
        return None, None

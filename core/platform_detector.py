import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class RepoInfo:
    platform: str
    host: str
    owner: str
    name: str
    branch: str
    zip_url: str


class PlatformDetector:
    def detect(self, repo_url: str, branch: str | None = None) -> RepoInfo:
        repo_url = repo_url.strip()
        parsed = urlparse(repo_url)
        host = parsed.netloc.lower()
        path = parsed.path.strip("/")

        if not path:
            raise ValueError("Некорректный URL репозитория")

        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError("Ожидался формат URL: host/owner/repo")

        owner, name = parts[0], parts[1]
        name = re.sub(r"\.git$", "", name)

        branch = branch or "main"

        if "github.com" in host:
            zip_url = f"https://api.github.com/repos/{owner}/{name}/zipball/{branch}"
            platform = "github"

        elif "gitverse.ru" in host:
            zip_url = f"https://{host}/{owner}/{name}/archive/{branch}.zip"
            platform = "gitverse"

        elif "gitlab.com" in host:
            zip_url = f"https://{host}/{owner}/{name}/-/archive/{branch}/{name}-{branch}.zip"
            platform = "gitlab"

        else:
            zip_url = f"https://{host}/{owner}/{name}/archive/{branch}.zip"
            platform = "unknown"

        return RepoInfo(
            platform=platform,
            host=host,
            owner=owner,
            name=name,
            branch=branch,
            zip_url=zip_url,
        )

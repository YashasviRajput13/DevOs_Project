import base64
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class GitHubService:

    def __init__(self):
        settings = get_settings()

        token = settings.GITHUB_TOKEN.strip()

        logger.info(
            "GitHubService: key_present=%s key_length=%d",
            bool(token),
            len(token),
        )

        if not token:
            raise ValueError(
                "GITHUB_TOKEN is missing or empty. "
                "Set it in the Render dashboard → Environment → GITHUB_TOKEN."
            )

        self.token = token
        self.base_url = "https://api.github.com"

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get_repository(self, owner: str, repo: str):
        url = f"{self.base_url}/repos/{owner}/{repo}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def get_tree(self, owner: str, repo: str, branch: str):
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=self.headers, params={"recursive": "1"}
            )
        response.raise_for_status()
        return response.json()

    async def get_file_content(self, owner: str, repo: str, path: str):
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    async def get_repository_tree(self, owner: str, repo: str, branch: str):
        data = await self.get_tree(owner, repo, branch)
        return [
            item for item in data.get("tree", []) if item.get("type") == "blob"
        ]

    async def get_text_file(self, owner: str, repo: str, path: str):
        data = await self.get_file_content(owner, repo, path)
        if data.get("encoding") != "base64":
            return None
        content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        return {
            "content": content,
            "sha": data.get("sha"),
            "size": data.get("size"),
        }

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> dict:
        """
        Create a GitHub pull request via the REST API.
        Uses the existing GitHub token — never exposes it in the response.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        payload = {
            "title": title[:255],
            "body": body[:65536],
            "head": head,
            "base": base,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30,
            )
        response.raise_for_status()
        data = response.json()
        return {
            "pr_number": data.get("number"),
            "pr_url": data.get("html_url"),
            "pr_title": data.get("title"),
            "pr_state": data.get("state"),
            "head_branch": data.get("head", {}).get("ref"),
            "base_branch": data.get("base", {}).get("ref"),
        }

    async def list_repositories_for_user(self) -> list[dict]:
        """List authenticated user's repositories."""
        url = f"{self.base_url}/user/repos"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                params={"per_page": 50, "sort": "updated"},
                timeout=15,
            )
        response.raise_for_status()
        return [
            {
                "full_name": r.get("full_name"),
                "name": r.get("name"),
                "url": r.get("html_url"),
                "description": r.get("description"),
                "language": r.get("language"),
                "default_branch": r.get("default_branch", "main"),
            }
            for r in response.json()
        ]
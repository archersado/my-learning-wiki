"""Collect GitHub Trending repositories and turn them into wiki-ready articles."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup


class GitHubTrendingCollector:
    """Scrape the public Trending page and optionally enrich entries via GitHub API."""

    TRENDING_URL = "https://github.com/trending"
    API_URL = "https://api.github.com/repos/{full_name}"

    def __init__(self, token: str = "", timeout: int = 20):
        self.timeout = timeout
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "deep-wiki-github-trends",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def collect(self, since: str = "daily", language: str = "", limit: int = 20) -> list[dict]:
        params = {"since": since}
        trending_url = self.TRENDING_URL
        if language:
            language_slug = re.sub(r"[^a-z0-9+#-]", "", language.lower())
            if language_slug:
                trending_url = f"{self.TRENDING_URL}/{language_slug}"
        response = requests.get(
            trending_url, params=params, headers=self.headers, timeout=self.timeout
        )
        response.raise_for_status()
        entries = self.parse_trending_html(response.text)[:limit]
        if not entries:
            raise RuntimeError("GitHub Trending returned no repository entries; its page structure may have changed")
        collected_at = datetime.now().astimezone().isoformat(timespec="seconds")

        articles = []
        with ThreadPoolExecutor(max_workers=min(5, len(entries))) as executor:
            metadata_list = executor.map(self._repo_metadata, (entry["full_name"] for entry in entries))
        for rank, (entry, metadata) in enumerate(zip(entries, metadata_list), 1):
            merged = {**entry, **metadata, "rank": rank, "since": since}
            articles.append(self._to_article(merged, collected_at))
        return articles

    @staticmethod
    def parse_trending_html(html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        repositories = []
        for row in soup.select("article.Box-row"):
            link = row.select_one("h2 a[href]")
            if not link:
                continue
            full_name = link.get("href", "").strip("/")
            if full_name.count("/") != 1:
                continue
            description_node = row.select_one("p")
            language_node = row.select_one("[itemprop='programmingLanguage']")
            stars_today = 0
            for text in row.stripped_strings:
                match = re.search(r"([\d,]+)\s+stars?\s+(today|this week|this month)", text, re.I)
                if match:
                    stars_today = int(match.group(1).replace(",", ""))
                    break
            repositories.append({
                "full_name": full_name,
                "url": f"https://github.com/{full_name}",
                "description": description_node.get_text(" ", strip=True) if description_node else "",
                "language": language_node.get_text(strip=True) if language_node else "Unknown",
                "stars_period": stars_today,
            })
        return repositories

    def _repo_metadata(self, full_name: str) -> dict[str, Any]:
        try:
            response = requests.get(
                self.API_URL.format(full_name=full_name),
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "topics": data.get("topics", []),
                "license": (data.get("license") or {}).get("spdx_id", "Unknown"),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "homepage": data.get("homepage", ""),
            }
        except (requests.RequestException, ValueError):
            # Trending itself remains useful if API quota/network enrichment fails.
            return {}

    @staticmethod
    def _to_article(repo: dict[str, Any], collected_at: str) -> dict:
        snapshot_date = collected_at[:10]
        topics = ", ".join(repo.get("topics", [])) or "None"
        content = f"""GitHub Trending rank: #{repo['rank']} ({repo['since']})
Repository: {repo['full_name']}
Description: {repo.get('description') or 'No description'}
Primary language: {repo.get('language', 'Unknown')}
Stars gained in period: {repo.get('stars_period', 0)}
Total stars: {repo.get('stars', 'Unavailable')}
Forks: {repo.get('forks', 'Unavailable')}
Open issues: {repo.get('open_issues', 'Unavailable')}
Topics: {topics}
License: {repo.get('license', 'Unknown')}
Repository created: {repo.get('created_at', 'Unavailable')}
Repository updated: {repo.get('updated_at', 'Unavailable')}
Homepage: {repo.get('homepage') or 'None'}
Collected at: {collected_at}

Analysis guidance: explain what the project does, its likely users and use cases, the
technology signals represented by its language/topics, and why its current Trending
momentum may matter. Treat Trending rank and stars gained as attention signals, not
proof of production adoption."""
        return {
            "source": "github-trending",
            "title": f"GitHub Trending {snapshot_date} #{repo['rank']}: {repo['full_name']}",
            "content": content,
            "link": repo["url"],
            "published": collected_at,
            "categories": ["github-trending", repo.get("language", "unknown"), *repo.get("topics", [])],
            "github": repo,
        }

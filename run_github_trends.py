"""Collect GitHub Trending, ingest projects, and generate today's trend analysis."""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(__file__))

from run_daily import _gather_today_pages, _synthesize_category_digest
from src.agents.wiki.wiki_ingest_agent import WikiIngestAgent
from src.agents.wiki.wiki_manager import WikiManager
from src.config.settings import GITHUB_CONFIG, build_llm
from src.tools.github_trending import GitHubTrendingCollector


def main():
    llm = build_llm()
    collector = GitHubTrendingCollector(token=GITHUB_CONFIG["github_token"])
    articles = collector.collect(
        since=GITHUB_CONFIG["trending_since"],
        language=GITHUB_CONFIG["trending_language"],
        limit=GITHUB_CONFIG["trending_limit"],
    )
    print(f"Collected {len(articles)} GitHub Trending repositories")

    agent = WikiIngestAgent(llm=llm)
    for article in articles:
        print(agent.ingest_article(article, category="github-trends"))

    today = datetime.now().strftime("%Y-%m-%d")
    wiki_root = Path(__file__).parent / "wiki"
    pages = _gather_today_pages(wiki_root / "github-trends", today)
    if not pages:
        print("No GitHub trend pages available for digest")
        return
    answer = _synthesize_category_digest(llm, "github-trends", pages)
    category_root = wiki_root / "github-trends"
    wm = WikiManager(wiki_root=str(category_root))
    path = f"analysis/github-trends-{today}.md"
    wm.write_page(path, answer, {
        "title": f"{today} GitHub 技术趋势分析",
        "type": "query",
        "date": today,
        "sources": [f"[[{p['title']}]]" for p in pages],
    })
    print(f"GitHub trend analysis saved: {category_root / path}")


if __name__ == "__main__":
    main()

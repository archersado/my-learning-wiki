#!/usr/bin/env python
"""Quick test: scrape feeds via curl → parse → save to local pending → ingest into wiki. No MongoDB needed."""
import os
import sys
import subprocess
import feedparser
import json
import hashlib
from pathlib import Path

os.environ["USE_LOCAL_STORAGE"] = "true"

from dotenv import load_dotenv
load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(__file__))

from src.config.settings import LOCAL_PENDING_DIR, build_llm
from src.agents.wiki.wiki_ingest_agent import WikiIngestAgent

# ── Step 1: Scrape RSS feeds using curl, then parse ───────────────────────

FEEDS = [
    "https://www.bestblogs.dev/en/feeds/rss?category=ai&minScore=90",
    "https://www.bestblogs.dev/feeds/rss?featured=y",
]
ARTICLES_PER_FEED = 3


def scrape_feeds_via_curl(feed_urls: list[str], limit: int = 3) -> list[dict]:
    articles = []
    for url in feed_urls:
        print(f"Fetching: {url}")
        try:
            result = subprocess.run(
                ["curl", "-s", "--max-time", "30", "-A", "Mozilla/5.0", url],
                capture_output=True, timeout=35
            )
            if result.returncode != 0 or not result.stdout:
                print(f"  curl failed: {result.stderr.decode()[:200]}")
                continue
            feed = feedparser.parse(result.stdout)
            count = 0
            for entry in feed.entries[:limit]:
                title = entry.get("title", "Untitled")
                link = entry.get("link", "")
                content = entry.get("content", "")
                if isinstance(content, list) and content:
                    content = content[0].get("value", "")
                elif isinstance(content, dict):
                    content = content.get("value", "")
                if not content:
                    content = entry.get("summary", "")
                if isinstance(content, list):
                    content = content[0] if content else ""
                published = entry.get("published", entry.get("updated", ""))

                article = {
                    "source": url,
                    "title": title,
                    "content": content,
                    "link": link,
                    "published": published,
                }
                articles.append(article)
                count += 1
                print(f"  → {title}")
            print(f"  Got {count} articles")
        except Exception as e:
            print(f"  Error: {e}")
    return articles


# ── Step 2: Save to local pending directory ───────────────────────────────

def save_to_pending(articles: list[dict], pending_dir: str):
    os.makedirs(pending_dir, exist_ok=True)
    for a in articles:
        uid = hashlib.md5(a["title"].encode()).hexdigest()[:8]
        path = os.path.join(pending_dir, f"{uid}.json")
        a["_id"] = uid
        a["status"] = "pending"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(a, f, ensure_ascii=False, default=str)
        print(f"  Saved: {a['title'][:50]}...")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    # Step 1: Scrape
    print("=" * 60)
    print(f"Step 1: Scraping {len(FEEDS)} feeds ({ARTICLES_PER_FEED} articles each)")
    print("=" * 60)
    articles = scrape_feeds_via_curl(FEEDS, limit=ARTICLES_PER_FEED)

    if not articles:
        print("No articles scraped. Exiting.")
        return

    # Step 2: Save to local pending dir
    print(f"\nStep 2: Saving {len(articles)} articles to pending dir")
    save_to_pending(articles, LOCAL_PENDING_DIR)

    # Step 3: Ingest into wiki
    print("\n" + "=" * 60)
    print("Step 3: Ingesting into wiki/ai-highlights/")
    print("=" * 60)

    llm = build_llm()
    agent = WikiIngestAgent(llm=llm)
    result = agent.batch_ingest()
    print(result)

    # Step 4: Show wiki structure
    print("\n" + "=" * 60)
    print("Wiki structure after ingest:")
    print("=" * 60)
    wiki_root = Path(__file__).parent / "wiki"
    for p in sorted(wiki_root.rglob("*.md")):
        rel = p.relative_to(wiki_root)
        print(f"  {rel}")

    print(f"\nDone! Check wiki/ai-highlights/ for generated pages.")
    print(f"Pending dir: {LOCAL_PENDING_DIR}")


if __name__ == "__main__":
    main()

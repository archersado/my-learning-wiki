"""Standalone runner: scrape INFO_RESOURCES feeds → ingest into wiki/industry-news/."""
import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(__file__))

from src.agents.scraping_expert import ScrapingExpert
from src.agents.wiki.wiki_ingest_agent import WikiIngestAgent
from src.config.settings import INFO_RESOURCES, build_llm


def main():
    llm = build_llm()

    print("=" * 60)
    print("Step 1: Scraping INFO_RESOURCES feeds")
    print(f"  Total feeds: {len(INFO_RESOURCES)}")
    print("=" * 60)
    scraper = ScrapingExpert(llm=llm)
    scraper.process({"scrape_list": INFO_RESOURCES})
    print()

    print("=" * 60)
    print("Step 2: Ingesting into wiki/industry-news/")
    print("=" * 60)
    agent = WikiIngestAgent(llm=llm)
    result = agent.batch_ingest()
    print(result)


if __name__ == "__main__":
    main()

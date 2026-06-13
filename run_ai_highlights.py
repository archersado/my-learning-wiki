"""Standalone runner: scrape AI_HIGH_SCORE feeds → ingest into wiki/ai-highlights/."""
import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(__file__))

from src.agents.scraping_expert import ScrapingExpert
from src.agents.wiki.wiki_ingest_agent import WikiIngestAgent
from src.config.settings import AI_HIGH_SCORE, build_llm


def main():
    llm = build_llm()

    print("=" * 60)
    print("Step 1: Scraping AI_HIGH_SCORE feeds")
    print("=" * 60)
    scraper = ScrapingExpert(llm=llm)
    scraper.process({"scrape_list": AI_HIGH_SCORE})
    print()

    print("=" * 60)
    print("Step 2: Ingesting into wiki/ai-highlights/")
    print("=" * 60)
    agent = WikiIngestAgent(llm=llm)
    result = agent.batch_ingest()
    print(result)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""CLI entry point: query the wiki and save result as a note in wiki/query/."""

import sys
import os
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from datetime import datetime

# Load .env
from dotenv import load_dotenv
load_dotenv()

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.settings import build_llm
from src.agents.wiki.wiki_query_agent import WikiQueryAgent
from src.agents.wiki.wiki_manager import WikiManager

WIKI_ROOT = Path(__file__).parent / "wiki"
QUERY_DIR = "query"
CATEGORIES = ["ai-highlights", "industry-news", "engineering-tips"]


def main():
    if len(sys.argv) < 2:
        print("Usage: query_wiki.py <question>", file=sys.stderr)
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    llm = build_llm("azure")
    wm = WikiManager(wiki_root=str(WIKI_ROOT))

    # Query each category and merge results
    all_sources = []
    all_answers = []
    for category in CATEGORIES:
        cat_root = WIKI_ROOT / category
        if not cat_root.exists():
            continue
        agent = WikiQueryAgent(llm=llm, wiki_root=str(cat_root))
        result = agent.query(question, save_as_analysis=False)
        if result["sources_used"]:
            all_sources.extend(result["sources_used"])
            all_answers.append(f"## {category}\n\n{result['answer']}")

    if all_answers:
        answer = "\n\n".join(all_answers)
        sources = all_sources
    else:
        answer = f"Wiki 中暂未收录与「{question}」相关的内容。"
        sources = []

    # Build note content
    slug = WikiQueryAgent._slug(question)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    saved_path = f"{QUERY_DIR}/{slug}.md"

    fm = {
        "title": question,
        "type": "query",
        "date": ts,
        "sources": [f"[[{s}]]" for s in sources],
    }
    wm.write_page(saved_path, answer, fm)

    abs_path = WIKI_ROOT / saved_path
    print(str(abs_path))


if __name__ == "__main__":
    main()

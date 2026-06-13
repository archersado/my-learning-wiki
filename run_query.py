"""Query the wiki for a specific category."""
import os
import sys
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(__file__))

from src.agents.wiki.wiki_query_agent import WikiQueryAgent
from src.config.settings import build_llm

CATEGORIES = {
    "ai": "wiki/ai-highlights",
    "info": "wiki/industry-news",
    "coding": "wiki/engineering-tips",
}

USAGE = """
Usage:
  python run_query.py <category> "<question>" [--save]

Categories:
  ai      → wiki/ai-highlights   (AI 精选)
  info    → wiki/industry-news   (行业时讯)
  coding  → wiki/engineering-tips (工程技巧)

Options:
  --save  Save the answer as an analysis page in the wiki

Examples:
  python run_query.py ai "最近有哪些重要的 AI 进展？"
  python run_query.py ai "GPT-5.5 有哪些新特性？" --save
  python run_query.py coding "有哪些实用的 Agent 工程实践？"
"""


def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in CATEGORIES:
        print(USAGE)
        sys.exit(1)

    category = args[0]
    question = args[1]
    save = "--save" in args
    wiki_root = os.path.join(os.path.dirname(__file__), CATEGORIES[category])

    llm = build_llm()

    agent = WikiQueryAgent(llm=llm, wiki_root=wiki_root)
    result = agent.query(question, save_as_analysis=save)

    print(f"\nQ: {question}\n")
    print(result["answer"])

    if result["sources_used"]:
        print(f"\n--- Sources ({len(result['sources_used'])}) ---")
        for s in result["sources_used"]:
            print(f"  · {s}")

    if result["saved_path"]:
        print(f"\nSaved to: {wiki_root}/{result['saved_path']}")


if __name__ == "__main__":
    main()

from .graph.workflow_graph import build_content_workflow_graph
from .agents.scraping_expert import ScrapingExpert
from .agents.wiki.wiki_ingest_agent import WikiIngestAgent
from .agents.wiki.wiki_query_agent import WikiQueryAgent
from .agents.wiki.wiki_lint_agent import WikiLintAgent
from .config.settings import INFO_RESOURCES, AI_HIGH_SCORE, CODING_PATTERN, build_llm

# Filter out feeds that return 403
ACTIVE_RESOURCES = [
    url for url in INFO_RESOURCES
    if "openai.com" not in url
]


def run_ai_highlights():
    """Scrape AI_HIGH_SCORE feeds and ingest into wiki/ai-highlights/."""
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
    ingest_agent = WikiIngestAgent(llm=llm)
    result = ingest_agent.batch_ingest()
    print(result)


def run_full_pipeline():
    """Run the full content -> wiki pipeline."""
    llm = build_llm()

    # Step 1: Scrape RSS feeds
    print("=" * 60)
    print("Step 1: Scraping AI Engineering RSS feeds")
    print("=" * 60)
    scraper = ScrapingExpert(llm=llm)
    scraper_state = {"scrape_list": ACTIVE_RESOURCES}
    scraper.process(scraper_state)
    print()

    # Step 2: Ingest pending articles into Wiki
    print("=" * 60)
    print("Step 2: Ingesting articles into Wiki")
    print("=" * 60)
    ingest_agent = WikiIngestAgent(llm=llm)
    result = ingest_agent.batch_ingest()
    print(result)
    print()

    # Step 3: Query the Wiki
    print("=" * 60)
    print("Step 3: Querying Wiki")
    print("=" * 60)
    query_agent = WikiQueryAgent(llm=llm)

    questions = [
        "最近有什么重要的 AI 进展？",
        "什么是最新的 AI 工程实践？",
    ]

    for question in questions:
        print(f"\nQ: {question}")
        result = query_agent.query(question, save_as_analysis=True)
        print(f"A: {result['answer'][:300]}...")
        if result["sources_used"]:
            print(f"Sources: {', '.join(result['sources_used'][:3])}")
        if result["saved_path"]:
            print(f"Saved to: {result['saved_path']}")

    # Step 4: Lint the Wiki
    print("\n" + "=" * 60)
    print("Step 4: Linting Wiki health")
    print("=" * 60)
    lint_agent = WikiLintAgent(llm=llm)
    report_path = lint_agent.lint()
    print(f"Lint report: {report_path}")
    report = lint_agent.wm.read_page(report_path)
    print(report.body[:500])


def main():
    print("Building the content operation workflow graph.")
    workflow_app = build_content_workflow_graph()

    print("Starting the workflow.")
    initial_state = {"scrape_query": "Latest AI news trends and expert opinions"}

    try:
        for step_output in workflow_app.stream(initialize_state):
            for key, value in step_output.items():
                print(f"Output from node '{key}':")
            print("---")
        print("Workflow finished.")

    except Exception as e:
        print(f"An error occurred during the workflow: {e}")


if __name__ == "__main__":
    import sys
    if "--ai-highlights" in sys.argv:
        run_ai_highlights()
    elif "--wiki" in sys.argv:
        run_full_pipeline()
    else:
        main()

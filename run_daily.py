"""Daily runner: scrape + ingest all wiki categories, then auto-query today's digest."""
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(__file__))

from src.agents.scraping_expert import ScrapingExpert
from src.agents.wiki.wiki_ingest_agent import WikiIngestAgent
from src.agents.wiki.wiki_manager import WikiManager
from src.config.settings import AI_HIGH_SCORE, INFO_RESOURCES, CODING_PATTERN, build_llm

WIKI_ROOT = Path(__file__).parent / "wiki"

CATEGORIES = [
    ("ai-highlights", AI_HIGH_SCORE),
    ("industry-news", INFO_RESOURCES),
    ("engineering-tips", CODING_PATTERN),
]

DAILY_QUESTIONS = {
    "ai-highlights": "今天都有哪些新的 AI 亮点内容？",
    "industry-news": "今天都有哪些新的行业资讯？",
    "engineering-tips": "今天都有哪些新的工程技巧内容？",
}


DAILY_INGEST_LIMIT = 300  # max articles per category per daily run


def run_category(name: str, feeds: list[str], llm):
    print(f"\n{'='*60}")
    print(f"[{name}] Step 1: Scraping {len(feeds)} feeds")
    print(f"{'='*60}")
    scraper = ScrapingExpert(llm=llm)
    scraper.process({"scrape_list": feeds})

    print(f"\n{'='*60}")
    print(f"[{name}] Step 2: Ingesting into wiki/{name}/ (limit={DAILY_INGEST_LIMIT})")
    print(f"{'='*60}")
    agent = WikiIngestAgent(llm=llm)
    result = agent.batch_ingest(limit=DAILY_INGEST_LIMIT)
    print(f"[{name}] {result}")
    return result


def _gather_today_pages(cat_root: Path, today: str, days: int = 3) -> list[dict]:
    """Scan sources/ in a category and return pages modified within the last N days.

    First tries to find pages modified today. If none found, expands to recent N days.
    """
    import subprocess
    wm = WikiManager(wiki_root=str(cat_root))
    sources_dir = cat_root / "sources"
    if not sources_dir.exists():
        return []

    from datetime import timedelta

    def _find_by_mtime(start_date: str, end_date: str) -> list[Path]:
        try:
            result = subprocess.run(
                ["find", str(sources_dir), "-name", "*.md", "-newermt", start_date, "!", "-newermt", end_date],
                capture_output=True, text=True, timeout=30
            )
            return [Path(f).relative_to(cat_root) for f in result.stdout.strip().split('\n') if f]
        except Exception:
            return []

    # Try today first
    tomorrow = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    candidates = _find_by_mtime(today, tomorrow)

    # If no today's pages, expand to recent N days
    if not candidates:
        start = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")
        candidates = _find_by_mtime(start, tomorrow)

    pages = []
    for rel_path in candidates:
        page = wm.read_page(str(rel_path))
        if not page:
            continue
        pages.append({
            "path": str(rel_path),
            "title": page.frontmatter.get("title", str(rel_path)),
            "body": page.body,
        })
    return pages


DIGEST_SYSTEM_PROMPT = """你是一个内容聚合专家。你将收到一个分类下今天收录的多篇文章，请：

1. 将内容相近或讨论同一话题的文章归类聚合
2. 对每个聚合主题，综合多篇文章的观点生成一段精炼摘要
3. 在摘要中用 [[文章标题]] 引用来源
4. 最终输出结构化的中文摘要，用 ## 标题 分隔各聚合主题
5. 如果文章数量较多，确保覆盖所有重要主题，不要遗漏"""


def _synthesize_category_digest(llm, category: str, pages: list[dict]) -> str:
    """Feed all today's pages for one category to the LLM and return an aggregated digest."""
    MAX_PAGE_CHARS = 3000
    BATCH_CHARS = 20000

    # Build batches
    batches: list[list[dict]] = []
    current, current_len = [], 0
    for p in pages:
        body = p["body"][:MAX_PAGE_CHARS]
        if current_len + len(body) > BATCH_CHARS and current:
            batches.append(current)
            current, current_len = [], 0
        current.append({**p, "body": body})
        current_len += len(body)
    if current:
        batches.append(current)

    # Summarize each batch
    partials = []
    for batch in batches:
        context = "\n".join(f"\n--- [[{p['title']}]] ---\n{p['body']}" for p in batch)
        prompt = (
            f"{DIGEST_SYSTEM_PROMPT}\n\n"
            f"分类: {category}\n"
            f"文章数量: {len(batch)}\n\n"
            f"参考材料:\n{context}"
        )
        resp = llm.invoke([HumanMessage(content=prompt)])
        partials.append(resp.content.strip())

    if len(partials) == 1:
        return partials[0]

    # Merge partial digests
    merged = "\n\n".join(partials)
    merge_prompt = (
        f"{DIGEST_SYSTEM_PROMPT}\n\n"
        f"分类: {category}\n\n"
        f"以下是分批聚合的中间摘要，请合并去重并重新组织为最终完整摘要：\n\n{merged}"
    )
    resp = llm.invoke([HumanMessage(content=merge_prompt)])
    return resp.content.strip()


def run_daily_queries(llm):
    """For each category, gather today's source pages and generate an aggregated digest."""
    print(f"\n{'='*60}")
    print("Step 3: Generating daily digest queries")
    print(f"{'='*60}")

    wm = WikiManager(wiki_root=str(WIKI_ROOT))
    today = datetime.now().strftime("%Y-%m-%d")

    all_sources = []
    all_answers = []

    for name in DAILY_QUESTIONS:
        cat_root = WIKI_ROOT / name
        if not cat_root.exists():
            all_answers.append(f"## {name}\n\n暂无内容\n")
            continue
        pages = _gather_today_pages(cat_root, today)
        if not pages:
            print(f"[{name}] no content found for {today}")
            all_answers.append(f"## {name}\n\n今天暂无新收录内容。\n")
            continue

        print(f"[{name}] found {len(pages)} recent pages, synthesizing digest...")
        digest = _synthesize_category_digest(llm, name, pages)
        all_sources.extend(p["title"] for p in pages)
        all_answers.append(f"## {name}\n\n{digest}")
        print(f"[{name}] digest done — {len(pages)} sources aggregated")

    if not all_answers:
        print("No content found for daily digest.")
        return

    answer = "\n\n".join(all_answers)
    slug = f"daily-digest-{today}"
    saved_path = f"query/{slug}.md"
    fm = {
        "title": f"{today} 每日内容摘要",
        "type": "query",
        "date": today,
        "sources": [f"[[{s}]]" for s in all_sources],
    }
    wm.write_page(saved_path, answer, fm)
    abs_path = WIKI_ROOT / saved_path
    print(f"Daily digest saved: {abs_path}")


def main():
    start = datetime.now()
    print(f"Daily wiki update started at {start.strftime('%Y-%m-%d %H:%M:%S')}")

    llm = build_llm()
    results = []

    for name, feeds in CATEGORIES:
        try:
            r = run_category(name, feeds, llm)
            results.append(f"  {name}: {r}")
        except Exception as e:
            print(f"  {name}: FAILED — {e}")
            results.append(f"  {name}: FAILED — {e}")

    try:
        run_daily_queries(llm)
    except Exception as e:
        print(f"  daily queries: FAILED — {e}")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'='*60}")
    print(f"Daily update finished in {elapsed:.0f}s")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()

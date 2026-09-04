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
from src.config.settings import AI_HIGH_SCORE, INFO_RESOURCES, CODING_PATTERN, GITHUB_CONFIG, build_llm
from src.tools.github_trending import GitHubTrendingCollector

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
    "github-trends": "今天 GitHub Trending 上有哪些热点项目，它们反映了哪些技术趋势？",
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


def run_github_trends(llm):
    """Collect and ingest GitHub Trending as a peer wiki topic."""
    print(f"\n{'='*60}")
    print("[github-trends] Collecting GitHub Trending")
    print(f"{'='*60}")
    collector = GitHubTrendingCollector(token=GITHUB_CONFIG["github_token"])
    articles = collector.collect(
        since=GITHUB_CONFIG["trending_since"],
        language=GITHUB_CONFIG["trending_language"],
        limit=GITHUB_CONFIG["trending_limit"],
    )
    agent = WikiIngestAgent(llm=llm)
    for article in articles:
        agent.ingest_article(article, category="github-trends")
    result = f"GitHub Trending ingest complete: {len(articles)} repositories processed"
    print(f"[github-trends] {result}")
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


DIGEST_SYSTEM_PROMPT = """你是一名技术情报与趋势分析师。根据今天收录的多篇材料生成中文洞见日报：

1. 输出“今日主题聚类”：将讨论同一技术、产品、事件或工程问题的来源聚为一组，说明该主题发生了什么
2. 输出“关键洞见”：跨来源比较共同点、分歧、因果关系、潜在影响和对开发者/企业的实际意义，不能只逐篇复述
3. 输出“趋势与信号”：归纳正在升温、延续、分化或降温的方向；说明信号来自哪些事实
4. 输出“值得关注与待验证”：给出后续值得追踪的问题，并明确证据不足或只有单一来源的判断
5. 每个事实、洞见和趋势判断都使用 [[文章标题]] 引用来源；区分材料事实和分析推断，禁止补造信息
6. 优先使用两个以上来源交叉支持聚类洞见；只有单一来源时明确标注“单一来源信号”
7. 覆盖所有重要主题，但合并重复内容，避免按文章机械罗列"""

CATEGORY_ANALYSIS_GUIDANCE = {
    "ai-highlights": "重点分析模型能力、Agent、AI 工具、基础设施、研究到产品化的变化及其成熟度信号。",
    "industry-news": "重点分析行业事件之间的联系、厂商策略、生态变化、安全风险和可能的市场影响。",
    "engineering-tips": "重点分析工程实践、工具链、架构模式的适用场景、权衡、成熟度和可落地建议。",
}

GITHUB_TRENDS_PROMPT = """你是一名开源技术趋势分析师。根据今天 GitHub Trending 项目材料生成中文日报：

1. 首先输出“热点项目榜单”，按 Trending 名次列出项目、核心用途、主要语言、周期新增 Star 和总 Star（缺失时明确写未知）
2. 然后输出“热点项目分析”，解释重点项目解决的问题、目标用户、值得关注的技术设计和走红原因
3. 最后输出“技术趋势与信号”，跨项目归纳技术栈、开发范式、AI/基础设施/工具方向的共同变化
4. 区分事实与推断；Trending 和 Star 代表关注度信号，不直接等同于生产采用率
5. 每项事实和判断均尽量使用 [[项目来源标题]] 引用，禁止补造材料中不存在的数字
6. 合并同类项目但不要遗漏排名靠前或增星明显的项目"""


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
        if category == "github-trends":
            system_prompt = GITHUB_TRENDS_PROMPT
        else:
            guidance = CATEGORY_ANALYSIS_GUIDANCE.get(category, "聚焦该分类的重要变化、影响和后续信号。")
            system_prompt = f"{DIGEST_SYSTEM_PROMPT}\n\n分类侧重点：{guidance}"
        prompt = (
            f"{system_prompt}\n\n"
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
        f"{system_prompt}\n\n"
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
        category_wm = WikiManager(wiki_root=str(cat_root))
        category_path = f"analysis/daily-insights-{today}.md"
        category_wm.write_page(category_path, digest, {
            "title": f"{today} {name} 每日洞见与趋势",
            "type": "analysis",
            "date": today,
            "sources": [f"[[{p['title']}]]" for p in pages],
        })
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
        r = run_github_trends(llm)
        results.append(f"  github-trends: {r}")
    except Exception as e:
        print(f"  github-trends: FAILED — {e}")
        results.append(f"  github-trends: FAILED — {e}")

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

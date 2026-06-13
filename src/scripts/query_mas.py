"""Query the MAS wiki and save the result as an analysis page."""

import os
import re
import sys
from pathlib import Path
from datetime import date
from langchain_core.messages import HumanMessage
from src.agents.wiki.wiki_manager import WikiManager
from src.agents.wiki.index_manager import IndexManager


SYSTEM_PROMPT = """You are a knowledge synthesis expert. You are given a question and several relevant wiki pages.

Your task:
1. Synthesize a comprehensive answer based on the provided wiki pages
2. Cite your sources using [[wikilink]] syntax for every claim
3. If the wiki pages don't contain enough information to fully answer, say so explicitly
4. Structure your answer clearly with headings and bullet points where appropriate
5. Write in Chinese unless the question is clearly in English

Format your answer as a well-structured markdown document."""


def build_llm():
    from src.agents.custom_llm import CustomChatModel
    return CustomChatModel(
        api_url=os.environ["AZURE_OPENAI_BASE_URL"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ.get("AZURE_OPENAI_MODEL", ""),
    )


def find_relevant_pages(wm, im, question: str) -> list[str]:
    """Find relevant wiki pages by searching index and full-text."""
    terms = re.findall(r'[\w\u4e00-\u9fff]{2,}', question.lower())
    matched_paths = set()

    for category in im.sections:
        for entry in im.list_entries(category):
            title_lower = entry["title"].lower()
            summary_lower = entry["summary"].lower()
            if any(term in title_lower or term in summary_lower for term in terms):
                path = entry.get("link", "")
                if path and wm._resolve_path(path).exists():
                    matched_paths.add(path)

    all_pages = wm.list_pages()
    for path in all_pages:
        if path in ("index.md", "log.md", "schema.md"):
            continue
        page = wm.read_page(path)
        if page:
            full_text = (page.body + " " + str(page.frontmatter)).lower()
            if any(term in full_text for term in terms):
                matched_paths.add(path)

    return list(matched_paths)


def synthesize_answer(llm, question: str, pages: list[dict]) -> str:
    """Call LLM to synthesize an answer from retrieved pages."""
    context = ""
    max_total_chars = 15000
    total_chars = 0
    for p in pages:
        if total_chars >= max_total_chars:
            break
        context += f"\n--- Page: [[{p['title']}]] ---\n"
        max_per_page = max_total_chars // max(len(pages), 1)
        body = p["body"][:max_per_page]
        total_chars += len(context) + len(body)
        if total_chars > max_total_chars:
            body = body[:len(body) - (total_chars - max_total_chars)]
            context += body
        else:
            context += body

    prompt = f"{SYSTEM_PROMPT}\n\nQuestion: {question}\n\nRetrieved wiki pages:\n{context}"
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content.strip()


def query_mas(question: str):
    mas_wiki_root = str(Path(__file__).resolve().parent.parent.parent / "wiki" / "mas")
    wm = WikiManager(wiki_root=mas_wiki_root)
    im = IndexManager(wiki_manager=wm)
    llm = build_llm()

    # Find relevant pages
    relevant_pages = find_relevant_pages(wm, im, question)
    if not relevant_pages:
        print(f"Wiki 中暂未收录与「{question}」相关的内容。")
        return

    # Read page contents
    page_contents = []
    for path in relevant_pages:
        page = wm.read_page(path)
        if page:
            page_contents.append({"path": path, "title": page.frontmatter.get("title", path), "body": page.body})

    if not page_contents:
        print("找到了相关页面索引但无法读取内容。")
        return

    print(f"Retrieved {len(page_contents)} pages.")

    # Synthesize answer
    answer = synthesize_answer(llm, question, page_contents)

    # Save as analysis
    slug = re.sub(r'[\s\u3000\u200b]+', '-', question)
    slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', slug)[:80].strip('-')
    saved_path = f"analysis/{slug}.md"

    fm = {
        "title": question,
        "type": "analysis",
        "sources": [f"[[{p['title']}]]" for p in page_contents[:10]],  # top 10 sources
        "date": date.today().isoformat(),
    }
    wm.write_page(saved_path, answer, fm)
    im.add_entry("analysis", question, saved_path, f"Q: {question[:80]}")

    print(f"\nSaved to: wiki/mas/{saved_path}")
    print(f"\n{'='*60}")
    print(f"Q: {question}")
    print(f"{'='*60}\n")
    print(answer)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "构建一个有效的多agent runtime 框架,必要的模块有哪些"
    query_mas(question)

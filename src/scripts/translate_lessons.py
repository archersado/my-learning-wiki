"""Translate wiki lesson files to Chinese - full body translation."""

import os
import re
import json
from pathlib import Path
from langchain_core.messages import HumanMessage
from src.agents.wiki.wiki_manager import WikiManager


def build_llm():
    from src.agents.custom_llm import CustomChatModel
    return CustomChatModel(
        api_url=os.environ["AZURE_OPENAI_BASE_URL"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ.get("AZURE_OPENAI_MODEL", ""),
    )


def translate_file(llm, filepath: str, wm: WikiManager) -> bool:
    """Translate the entire body of a lesson file."""
    page = wm.read_page(filepath)
    if page is None:
        return False

    body = page.body
    title = page.frontmatter.get("title", "")

    # Split body: separate the "Original Lesson Content" section from the wiki-added sections
    orig_content_match = re.search(r'^## Original Lesson Content\n\n(.*)$', body, re.MULTILINE | re.DOTALL)

    if orig_content_match:
        # Only translate the wiki-added part (before "Original Lesson Content")
        wiki_part = body[:orig_content_match.start()].strip()
        orig_part = orig_content_match.group(0)
    else:
        wiki_part = body
        orig_part = ""

    if not wiki_part:
        return False

    prompt = f"""Translate the following markdown text to Chinese. Keep technical terms (framework names, acronyms, code) in English. Keep markdown formatting intact. Keep wikilinks [[like this]] intact. Only output the translation, no explanation.

{wiki_part[:6000]}"""

    messages = [HumanMessage(content=prompt)]
    try:
        response = llm.invoke(messages)
        translated_wiki = response.content.strip()
    except Exception as e:
        print(f"  LLM error: {e}")
        return False

    new_body = translated_wiki
    if orig_part:
        new_body += "\n\n" + orig_part

    # Translate title in frontmatter
    fm = page.frontmatter.copy()
    if title:
        title_prompt = f"Translate this title to Chinese, keeping technical terms in English: {title}"
        try:
            title_resp = llm.invoke([HumanMessage(content=title_prompt)])
            fm["title_zh"] = fm["title"]
            fm["title"] = title_resp.content.strip()
        except Exception:
            pass

    wm.update_page(filepath, body=new_body, frontmatter=fm, update_frontmatter=True)
    return True


if __name__ == "__main__":
    llm = build_llm()
    project_root = Path(__file__).resolve().parent.parent.parent

    for wiki_dir, label in [("agent-engineering", "Agent Engineering"), ("mas", "MAS")]:
        wm = WikiManager(wiki_root=str(project_root / "wiki" / wiki_dir))
        lesson_files = wm.list_pages("lessons")
        print(f"\n{'='*60}")
        print(f"Translating {label} lessons ({len(lesson_files)} files)")
        print(f"{'='*60}")

        for i, filepath in enumerate(lesson_files):
            page = wm.read_page(filepath)
            if page is None:
                continue
            orig_title = page.frontmatter.get("title_zh", page.frontmatter.get("title", filepath))
            print(f"[{i+1}/{len(lesson_files)}] {orig_title}...")
            success = translate_file(llm, filepath, wm)
            print(f"  {'OK' if success else 'FAILED'}")

    print("\nDone!")

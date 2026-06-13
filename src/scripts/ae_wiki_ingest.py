"""Ingest Agent Engineering lesson markdown files into wiki/agent-engineering/ using the project's wiki infrastructure."""

import json
import re
import os
from pathlib import Path
from src.agents.wiki.wiki_manager import WikiManager
from src.agents.wiki.index_manager import IndexManager
from src.agents.wiki.log_manager import LogManager
from src.agents.wiki.cross_ref_engine import CrossRefEngine


SYSTEM_PROMPT = """You are a knowledge extraction expert. Given a lesson document from an agent engineering curriculum, extract the following as JSON:

{
  "summary": "A concise summary in Chinese (2-3 sentences)",
  "entities": ["List of concrete entities mentioned (frameworks, products, organizations, people)"],
  "concepts": ["List of abstract concepts, theories, patterns, or methodologies"],
  "key_points": ["3-7 key takeaways from the lesson"]
}

Return ONLY valid JSON. No markdown formatting, no explanation outside the JSON."""


def build_gpt4o():
    from src.agents.custom_llm import CustomChatModel
    return CustomChatModel(
        api_url=os.environ["AZURE_OPENAI_BASE_URL"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        model=os.environ.get("AZURE_OPENAI_MODEL", ""),
    )


def extract_info(llm, content: str, title: str) -> dict:
    from langchain_core.messages import HumanMessage
    messages = [HumanMessage(content=f"{SYSTEM_PROMPT}\n\nLesson: {title}\n\nContent:\n{content[:5000]}")]
    response = llm.invoke(messages)
    text = response.content.strip()
    json_match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"summary": title, "entities": [], "concepts": [], "key_points": []}


def slug(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9\u4e00-\u9fff\s-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return s.strip('-')


def find_lesson_file(lessons_dir: Path, lesson_dir: str) -> Path | None:
    candidates = [
        lessons_dir / lesson_dir / "docs" / "en.md",
        lessons_dir / lesson_dir / "docs" / "zh.md",
        lessons_dir / lesson_dir / "README.md",
        lessons_dir / lesson_dir / "index.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    md_files = list((lessons_dir / lesson_dir).glob("*.md"))
    if md_files:
        return md_files[0]
    for sub in (lessons_dir / lesson_dir).iterdir():
        if sub.is_dir():
            for md in sub.glob("*.md"):
                return md
    return None


def extract_title_from_content(content: str) -> str:
    match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def ingest_lessons():
    llm = build_gpt4o()

    project_root = Path(__file__).resolve().parent.parent.parent
    lessons_dir = project_root / "learn/ai-engineering-from-scratch/phases/14-agent-engineering"

    ae_wiki_root = str(project_root / "wiki" / "agent-engineering")
    wm = WikiManager(wiki_root=ae_wiki_root)
    im = IndexManager(wiki_manager=wm)
    lm = LogManager(wiki_manager=wm)
    cre = CrossRefEngine(wiki_manager=wm, index_manager=im)

    print(f"Agent Engineering wiki root: {ae_wiki_root}")
    print(f"Lessons directory: {lessons_dir}")

    lesson_dirs = sorted([
        d.name for d in lessons_dir.iterdir()
        if d.is_dir() and re.match(r'^\d{2}-', d.name)
    ])

    print(f"Found {len(lesson_dirs)} lesson directories.")

    count = 0
    for lesson_dir in lesson_dirs:
        lesson_file = find_lesson_file(lessons_dir, lesson_dir)
        if lesson_file is None:
            print(f"SKIP (no .md found): {lesson_dir}")
            continue

        content = lesson_file.read_text(encoding="utf-8")
        lesson_title = extract_title_from_content(content) or lesson_dir

        print(f"[{count+1}/{len(lesson_dirs)}] Extracting: {lesson_title}...")
        extraction = extract_info(llm, content, lesson_title)

        source_path = f"lessons/{lesson_dir}.md"
        entities_links = [f"[[{e}]]" for e in extraction.get("entities", [])]
        concepts_links = [f"[[{c}]]" for c in extraction.get("concepts", [])]

        source_body = f"# {lesson_title}\n\n"
        source_body += f"> {extraction.get('summary', '')}\n\n"
        source_body += f"**Source:** `{lesson_file.relative_to(project_root)}`\n\n"

        if extraction.get("key_points"):
            source_body += "## Key Points\n\n"
            for kp in extraction["key_points"]:
                source_body += f"- {kp}\n"
            source_body += "\n"

        if entities_links:
            source_body += "## Entities\n\n"
            for e in extraction.get("entities", []):
                source_body += f"- [[{e}]]\n"
            source_body += "\n"

        if concepts_links:
            source_body += "## Concepts\n\n"
            for c in extraction.get("concepts", []):
                source_body += f"- [[{c}]]\n"
            source_body += "\n"

        source_body += "## Original Lesson Content\n\n"
        source_body += content

        source_fm = {
            "title": lesson_title,
            "type": "source",
            "category": "agent-engineering",
            "lesson_id": lesson_dir,
            "entities": entities_links,
            "concepts": concepts_links,
        }

        wm.write_page(source_path, source_body, source_fm)

        for entity in extraction.get("entities", []):
            matches = cre.find_matching_pages(entity, "entities")
            if matches:
                cre.append_entity_update(entity, lesson_title, extraction.get("summary", ""))
            else:
                cre.create_entity_page(entity, "Entity mentioned in Agent Engineering curriculum.", [lesson_title])
                im.add_entry("entities", entity, f"entities/{slug(entity)}.md", f"Entity: {entity}")

        for concept in extraction.get("concepts", []):
            matches = cre.find_matching_pages(concept, "concepts")
            if matches:
                cre.append_concept_update(concept, lesson_title, extraction.get("summary", ""))
            else:
                cre.create_concept_page(concept, "Concept from Agent Engineering curriculum.", [lesson_title])
                im.add_entry("concepts", concept, f"concepts/{slug(concept)}.md", f"Concept: {concept}")

        im.add_entry("sources", lesson_title, source_path, extraction.get("summary", ""))
        lm.append("ingest", lesson_title,
                  f"Extracted {len(extraction.get('entities', []))} entities, {len(extraction.get('concepts', []))} concepts.")

        count += 1
        print(f"  OK: {lesson_title}")

    lm.append("ingest (batch)", f"{count} Agent Engineering lessons ingested", "Agent Engineering wiki creation completed")
    print(f"\nDone: {count}/{len(lesson_dirs)} lessons ingested into {ae_wiki_root}")


if __name__ == "__main__":
    ingest_lessons()

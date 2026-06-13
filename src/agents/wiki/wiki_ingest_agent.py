"""WikiIngestAgent — ingests articles from MongoDB into the wiki."""

import json
import os
import re
from datetime import date
from pathlib import Path
from ..base_agent import BaseAgent
from ...config.settings import USE_LOCAL_STORAGE
from .wiki_manager import WikiManager
from .index_manager import IndexManager
from .log_manager import LogManager
from .cross_ref_engine import CrossRefEngine
from ...config.settings import AI_HIGH_SCORE, INFO_RESOURCES, CODING_PATTERN


# Map each RSS source URL to its wiki category directory
_SOURCE_CATEGORY_MAP: dict[str, str] = {}
for _url in AI_HIGH_SCORE:
    _SOURCE_CATEGORY_MAP[_url] = "ai-highlights"
for _url in INFO_RESOURCES:
    _SOURCE_CATEGORY_MAP[_url] = "industry-news"
for _url in CODING_PATTERN:
    _SOURCE_CATEGORY_MAP[_url] = "engineering-tips"

# Category directories: AI 精选 / 行业时讯 / 工程技巧
CATEGORY_DIRS = {
    "ai-highlights": "ai-highlights",
    "industry-news": "industry-news",
    "engineering-tips": "engineering-tips",
}
DEFAULT_CATEGORY = "industry-news"


class WikiIngestAgent(BaseAgent):
    """Reads pending articles from MongoDB, extracts info via LLM, and integrates into wiki."""

    SYSTEM_PROMPT = """You are a knowledge extraction expert. Given an article, determine if it is related to AI Engineering (AI models, LLMs, AI tools, AI infrastructure, AI research, ML systems, agents, etc.) and if so, extract the following as JSON:

{
  "is_ai_engineering": true/false,
  "summary": "A concise summary of the article in Chinese (2-3 sentences)",
  "entities": ["List of concrete entities mentioned (people, companies, products, organizations)"],
  "concepts": ["List of abstract concepts, ideas, or topics discussed"],
  "key_points": ["3-5 key takeaways from the article"]
}

Return ONLY valid JSON. No markdown formatting, no explanation outside the JSON.
If the article is NOT related to AI Engineering, set is_ai_engineering to false and leave other fields empty arrays/strings."""

    def __init__(self, llm=None, wiki_root: str = None, pending_dir: str = None):
        skip_db = USE_LOCAL_STORAGE
        super().__init__(llm, skip_db=skip_db)
        if wiki_root is None:
            wiki_root = str(Path(__file__).resolve().parent.parent.parent.parent / "wiki")
        self.wiki_base = Path(wiki_root).resolve()
        self._components: dict[str, dict] = {}
        if pending_dir is None:
            from ...config.settings import LOCAL_PENDING_DIR
            pending_dir = LOCAL_PENDING_DIR
        self.pending_dir = pending_dir

    def _get_components(self, category: str) -> dict:
        """Lazily create per-category wiki components rooted at wiki_base/{category}/."""
        if category not in self._components:
            cat_root = str(self.wiki_base / CATEGORY_DIRS.get(category, category))
            wm = WikiManager(wiki_root=cat_root)
            im = IndexManager(wiki_manager=wm)
            self._components[category] = {
                "wm": wm,
                "im": im,
                "lm": LogManager(wiki_manager=wm),
                "cre": CrossRefEngine(wiki_manager=wm, index_manager=im),
            }
        return self._components[category]

    def _get_article_category(self, article: dict) -> str:
        """Resolve the wiki category from the article's source URL."""
        return _SOURCE_CATEGORY_MAP.get(article.get("source", ""), DEFAULT_CATEGORY)

    def process(self, state: dict) -> dict:
        """Ingest a single article passed in state['article']."""
        article = state.get("article")
        if article is None:
            article = self._fetch_next_pending_article()
            if article is None:
                state["ingest_result"] = "No pending articles found"
                return state

        result = self.ingest_article(article)
        state["ingest_result"] = result
        return state

    def ingest_article(self, article: dict, category: str = None) -> str:
        """Ingest a single article dict from MongoDB into the appropriate wiki category."""
        if category is None:
            category = self._get_article_category(article)

        comps = self._get_components(category)
        wm = comps["wm"]
        im = comps["im"]
        lm = comps["lm"]
        cre = comps["cre"]

        title = article.get("title", "Untitled")
        content = article.get("content", "")
        link = article.get("link", "")
        published = article.get("published", "")

        # Step 1: Extract information via LLM
        extraction = self._extract_info(content, title)

        if not extraction.get("is_ai_engineering", True):
            self._mark_article_processed(article)
            return f"Skipped (not AI Engineering): {title}"

        # Step 2: Create source page
        source_slug = self._slug(title)
        source_path = f"sources/{source_slug}.md"
        entities_links = [f"[[{e}]]" for e in extraction["entities"]]
        concepts_links = [f"[[{c}]]" for c in extraction["concepts"]]

        source_body = f"# {title}\n\n"
        source_body += f"**Summary:** {extraction['summary']}\n\n"
        source_body += f"**URL:** {link}\n" if link else ""
        source_body += f"**Published:** {published}\n\n" if published else ""

        if entities_links:
            source_body += "## Entities\n\n"
            for e in extraction["entities"]:
                source_body += f"- [[{e}]]\n"
            source_body += "\n"

        if concepts_links:
            source_body += "## Concepts\n\n"
            for c in extraction["concepts"]:
                source_body += f"- [[{c}]]\n"
            source_body += "\n"

        if extraction.get("key_points"):
            source_body += "## Key Points\n\n"
            for kp in extraction["key_points"]:
                source_body += f"- {kp}\n"

        if content:
            source_body += f"\n## Original Content\n\n{content}\n"

        source_fm = {
            "title": title,
            "type": "source",
            "category": category,
            "url": link,
            "published": str(published) if published else str(date.today()),
            "entities": entities_links,
            "concepts": concepts_links,
        }

        wm.write_page(source_path, source_body, source_fm)

        # Step 3: Update or create entity/concept pages
        for entity in extraction["entities"]:
            matches = cre.find_matching_pages(entity, "entities")
            if matches:
                cre.append_entity_update(entity, title, extraction["summary"])
            else:
                cre.create_entity_page(entity, "", [title])
                im.add_entry("entities", entity, f"entities/{self._slug(entity)}.md", f"Entity: {entity}")

        for concept in extraction["concepts"]:
            matches = cre.find_matching_pages(concept, "concepts")
            if matches:
                cre.append_concept_update(concept, title, extraction["summary"])
            else:
                cre.create_concept_page(concept, "", [title])
                im.add_entry("concepts", concept, f"concepts/{self._slug(concept)}.md", f"Concept: {concept}")

        # Step 4: Add to index
        im.add_entry("sources", title, source_path, extraction["summary"])

        # Step 5: Log
        lm.append("ingest", title, f"Extracted {len(extraction['entities'])} entities, {len(extraction['concepts'])} concepts.")

        # Step 6: Mark as processed in MongoDB
        self._mark_article_processed(article)

        return f"Ingested [{category}]: {title}"

    def batch_ingest(
        self,
        state: dict = None,
        days: int = None,
        limit_per_source: int = None,
        limit: int = None,
    ) -> str:
        """Ingest pending articles from MongoDB.

        Args:
            days: If set, only ingest articles published within the last N days.
            limit_per_source: If set, cap articles per source.
            limit: If set, total max articles to ingest in this batch.
        """
        articles = self._fetch_all_pending_articles(days=days)
        if not articles:
            return "No pending articles found"

        if limit_per_source:
            from collections import defaultdict
            grouped: dict[str, list] = defaultdict(list)
            for a in articles:
                grouped[a.get("source", "unknown")].append(a)
            filtered = []
            for src in grouped:
                filtered.extend(grouped[src][:limit_per_source])
            articles = filtered

        if limit:
            articles = articles[:limit]

        count = 0
        for article in articles:
            try:
                self.ingest_article(article)
                count += 1
            except Exception as e:
                print(f"Error ingesting article '{article.get('title', 'unknown')}': {e}")
                self._mark_article_processed(article)

        # Log to each category that received articles
        for category, comps in self._components.items():
            comps["lm"].append("ingest (batch)", f"{count} articles processed", "Batch ingest completed")

        return f"Batch ingest complete: {count} articles processed"

    # ── LLM extraction ───────────────────────────────────────────────

    def _extract_info(self, content: str, title: str) -> dict:
        """Call LLM to extract entities, concepts, and summary from article content."""
        from langchain_core.messages import HumanMessage

        messages = [HumanMessage(content=f"{self.SYSTEM_PROMPT}\n\nArticle: {title}\n\nContent:\n{content[:5000]}")]
        response = self.llm.invoke(messages)
        text = response.content.strip()

        json_match = re.search(r'```(?:json)?\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            text = json_match.group(1)

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "summary": title,
                "entities": [],
                "concepts": [],
                "key_points": [],
            }

    # ── Article storage helpers (MongoDB or local) ─────────────────────

    def _load_local_articles(self) -> list[dict]:
        """Load all pending JSON files from the local pending directory."""
        articles = []
        os.makedirs(self.pending_dir, exist_ok=True)
        for fname in os.listdir(self.pending_dir):
            if not fname.endswith(".json"):
                continue
            with open(os.path.join(self.pending_dir, fname), "r", encoding="utf-8") as f:
                article = json.load(f)
                if article.get("status") == "pending":
                    articles.append(article)
        return articles

    def _save_local_article(self, article: dict):
        """Save an article as a JSON file in the pending directory."""
        os.makedirs(self.pending_dir, exist_ok=True)
        import hashlib
        uid = hashlib.md5(article["title"].encode()).hexdigest()[:8]
        path = os.path.join(self.pending_dir, f"{uid}.json")
        article["_id"] = uid
        article["status"] = "pending"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, default=str)
        return path

    def _fetch_next_pending_article(self) -> dict | None:
        """Fetch the next pending article from MongoDB or local storage."""
        try:
            if USE_LOCAL_STORAGE:
                articles = self._load_local_articles()
                return articles[0] if articles else None
            collection = self.db_client.get_raw_data_collection()
            return collection.find_one({"status": "pending"})
        except Exception as e:
            print(f"Error fetching pending article: {e}")
            return None

    def _fetch_all_pending_articles(self, days: int = None) -> list[dict]:
        """Fetch all pending articles from MongoDB or local storage."""
        try:
            if USE_LOCAL_STORAGE:
                return self._load_local_articles()
            collection = self.db_client.get_raw_data_collection()
            query = {"status": "pending"}
            if days is not None:
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(days=days)
                query["published"] = {"$gte": cutoff}
            return list(collection.find(query).sort("published", -1))
        except Exception as e:
            print(f"Error fetching pending articles: {e}")
            return []

    def _mark_article_processed(self, article: dict):
        """Mark an article as processed in MongoDB or local storage. No-op for inbox sources."""
        try:
            if article.get("source") == "inbox":
                return
            if USE_LOCAL_STORAGE:
                import hashlib
                uid = article.get("_id", hashlib.md5(article["title"].encode()).hexdigest()[:8])
                path = os.path.join(self.pending_dir, f"{uid}.json")
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["status"] = "processed"
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, default=str)
                return
            collection = self.db_client.get_raw_data_collection()
            collection.update_one(
                {"_id": article["_id"]},
                {"$set": {"status": "processed"}}
            )
        except Exception as e:
            print(f"Error marking article processed: {e}")

    @staticmethod
    def _slug(name: str) -> str:
        """Convert a name to a kebab-case filename slug."""
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug.strip('-')

    # ── Inbox: drop files and ingest directly ─────────────────────────

    @property
    def inbox_dir(self) -> str:
        return os.path.join(self.pending_dir, "inbox")

    def ingest_inbox(self, category: str = "ai-highlights") -> str:
        """Scan inbox/ for dropped files (.md, .txt, .json) and ingest them into the wiki.

        Supported formats:
        - .md / .txt — treated as raw content, filename used as title
        - .json — must have 'title' and 'content' keys (optionally 'link', 'published')

        After successful ingest, processed files are moved to inbox/done/.
        """
        inbox = self.inbox_dir
        if not os.path.exists(inbox):
            os.makedirs(inbox, exist_ok=True)
            return "Inbox directory created. Drop .md, .txt, or .json files here."

        done_dir = os.path.join(inbox, "done")
        os.makedirs(done_dir, exist_ok=True)

        files = [f for f in os.listdir(inbox) if os.path.isfile(os.path.join(inbox, f)) and f.endswith((".md", ".txt", ".json"))]
        if not files:
            return "Inbox is empty. Drop .md, .txt, or .json files to ingest."

        count = 0
        for fname in files:
            fpath = os.path.join(inbox, fname)
            try:
                article = self._parse_inbox_file(fpath)
                self.ingest_article(article, category=category)
                # Move to done
                import shutil
                shutil.move(fpath, os.path.join(done_dir, fname))
                count += 1
                print(f"  ✓ Ingested: {fname}")
            except Exception as e:
                print(f"  ✗ Failed: {fname} — {e}")

        return f"Inbox ingest complete: {count}/{len(files)} files processed"

    def _parse_inbox_file(self, filepath: str) -> dict:
        """Parse a dropped file into a standard article dict."""
        ext = os.path.splitext(filepath)[1].lower()
        name = os.path.splitext(os.path.basename(filepath))[0]

        if ext == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "source": "inbox",
                "title": data.get("title", name),
                "content": data.get("content", ""),
                "link": data.get("link", ""),
                "published": data.get("published", ""),
            }

        # .md or .txt — read full content, use filename as title
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # If it's markdown with frontmatter, try to extract title
        title = name
        if ext == ".md":
            fm, body = WikiManager._parse_frontmatter(content)
            if fm.get("title"):
                title = fm["title"]
            content = body or content

        return {
            "source": "inbox",
            "title": title,
            "content": content,
            "link": "",
            "published": "",
        }

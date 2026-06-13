"""CrossRefEngine — matches entities/concepts against existing wiki pages and manages cross-references."""

import re
from .wiki_manager import WikiManager
from .index_manager import IndexManager


class CrossRefEngine:
    """Find matching wiki pages for extracted entities/concepts and manage bidirectional links."""

    def __init__(self, wiki_manager: WikiManager = None, index_manager: IndexManager = None, wiki_root: str = None):
        self.wm = wiki_manager or WikiManager(wiki_root=wiki_root)
        self.im = index_manager or IndexManager(wiki_manager=self.wm)

    # ── matching ─────────────────────────────────────────────────────

    def find_matching_pages(self, name: str, category: str = None) -> list[dict]:
        """Search index.md for pages matching the given name.

        Args:
            name: Entity/concept name to match.
            category: If given, restrict search to this category. Otherwise search all.

        Returns:
            List of {title, link, summary, matched_category} dicts.
        """
        categories = [category] if category else self.im.sections
        results = []
        for cat in categories:
            for entry in self.im.list_entries(cat):
                if self._names_match(entry["title"], name):
                    entry["matched_category"] = cat
                    results.append(entry)
        return results

    @staticmethod
    def _names_match(index_title: str, extracted_name: str) -> bool:
        """Fuzzy name matching — case-insensitive substring or exact equality."""
        a = index_title.lower().strip()
        b = extracted_name.lower().strip()
        return a == b or a in b or b in a

    # ── page creation ────────────────────────────────────────────────

    def create_entity_page(self, name: str, description: str = "", sources: list[str] = None) -> str:
        """Create a new entity page. Returns the relative path."""
        path = f"entities/{self._slug(name)}.md"
        fm = {
            "title": name,
            "type": "entity",
            "sources": [f"[[{s}]]" for s in (sources or [])],
        }
        body = f"# {name}\n\n{description}\n"
        if sources:
            body += "\n## Mentioned In\n\n"
            for s in sources:
                body += f"- [[{s}]]\n"
        self.wm.write_page(path, body, fm)
        return path

    def create_concept_page(self, name: str, description: str = "", sources: list[str] = None) -> str:
        """Create a new concept page. Returns the relative path."""
        path = f"concepts/{self._slug(name)}.md"
        fm = {
            "title": name,
            "type": "concept",
            "sources": [f"[[{s}]]" for s in (sources or [])],
        }
        body = f"# {name}\n\n{description}\n"
        if sources:
            body += "\n## Mentioned In\n\n"
            for s in sources:
                body += f"- [[{s}]]\n"
        self.wm.write_page(path, body, fm)
        return path

    # ── page update ──────────────────────────────────────────────────

    def append_entity_update(self, name: str, source_title: str, summary: str = ""):
        """Append a 'Latest Updates' section to an existing entity page."""
        matches = self.find_matching_pages(name, "entities")
        if not matches:
            return
        path = matches[0]["link"]
        page = self.wm.read_page(path)
        if page is None:
            return

        body = page.body
        if "## Latest Updates" not in body:
            body += "\n## Latest Updates\n"
        body += f"\n### {source_title}\n\n{summary}\n"

        # update frontmatter sources
        fm = page.frontmatter.copy()
        existing_sources = fm.get("sources", [])
        if f"[[{source_title}]]" not in existing_sources:
            existing_sources.append(f"[[{source_title}]]")
        fm["sources"] = existing_sources

        self.wm.write_page(path, body, fm)

    def append_concept_update(self, name: str, source_title: str, summary: str = ""):
        """Append a 'Latest Updates' section to an existing concept page."""
        matches = self.find_matching_pages(name, "concepts")
        if not matches:
            return
        path = matches[0]["link"]
        page = self.wm.read_page(path)
        if page is None:
            return

        body = page.body
        if "## Latest Updates" not in body:
            body += "\n## Latest Updates\n"
        body += f"\n### {source_title}\n\n{summary}\n"

        fm = page.frontmatter.copy()
        existing_sources = fm.get("sources", [])
        if f"[[{source_title}]]" not in existing_sources:
            existing_sources.append(f"[[{source_title}]]")
        fm["sources"] = existing_sources

        self.wm.write_page(path, body, fm)

    # ── wikilink extraction ──────────────────────────────────────────

    @staticmethod
    def extract_wikilinks(text: str) -> list[str]:
        """Extract all [[wikilink]] references from text."""
        return re.findall(r'\[\[([^\]]+)\]\]', text)

    @staticmethod
    def _slug(name: str) -> str:
        """Convert a name to a kebab-case filename slug."""
        slug = name.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        return slug

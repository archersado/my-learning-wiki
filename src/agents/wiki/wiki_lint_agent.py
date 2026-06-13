"""WikiLintAgent — performs health checks on the wiki and generates lint reports."""

import re
from datetime import date
from ..base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from .wiki_manager import WikiManager
from .index_manager import IndexManager
from .log_manager import LogManager
from .cross_ref_engine import CrossRefEngine


class WikiLintAgent(BaseAgent):
    """Scans the wiki for inconsistencies, orphan pages, broken links, and contradictions."""

    def __init__(self, llm=None, wiki_root: str = None):
        super().__init__(llm, skip_db=True)
        self.wm = WikiManager(wiki_root=wiki_root)
        self.im = IndexManager(wiki_manager=self.wm)
        self.lm = LogManager(wiki_manager=self.wm)
        self.cre = CrossRefEngine(wiki_manager=self.wm, index_manager=self.im)

    def process(self, state: dict) -> dict:
        """Run lint and store report path in state."""
        report_path = self.lint()
        return {**state, "lint_report": report_path}

    def lint(self) -> str:
        """Run all lint checks and generate a lint report. Returns the report path."""
        issues = []

        # Check 1: Broken wikilinks
        broken = self._check_broken_links()
        if broken:
            issues.append(f"### Broken Wikilinks ({len(broken)} found)\n\nPages reference non-existent wiki pages:\n\n" +
                          "".join(f"- In `{item['source']}`: `[[{item['link']}]]`\n" for item in broken))

        # Check 2: Orphan pages
        orphans = self._check_orphan_pages()
        if orphans:
            issues.append(f"### Orphan Pages ({len(orphans)} found)\n\nPages with no inbound wikilinks:\n\n" +
                          "".join(f"- `{p}`\n" for p in orphans))

        # Check 3: Missing pages (wikilinks in index that don't have files)
        missing = self._check_index_consistency()
        if missing:
            issues.append(f"### Index Inconsistencies ({len(missing)} found)\n\nIndex entries point to missing files:\n\n" +
                          "".join(f"- `{item}`\n" for item in missing))

        # Check 4: Contradictions (LLM-based)
        contradictions = self._check_contradictions()
        if contradictions:
            issues.append(f"### Potential Contradictions\n\n{contradictions}")

        # Build report
        today = date.today().isoformat()
        report_path = f"analysis/lint-report-{today}.md"

        if not issues:
            body = f"# Lint Report — {today}\n\nNo issues found. Wiki is healthy!\n"
        else:
            body = f"# Lint Report — {today}\n\n"
            body += "## Summary\n\n"
            body += f"- Broken links: {len(broken)}\n"
            body += f"- Orphan pages: {len(orphans)}\n"
            body += f"- Index inconsistencies: {len(missing)}\n"
            body += f"- Contradictions: {'Flagged' if contradictions else 'None'}\n\n"
            body += "## Details\n\n" + "\n".join(issues) + "\n"

        self.wm.write_page(report_path, body, {"title": f"Lint Report {today}", "type": "analysis"})
        self.lm.append("lint", f"Report {today}", f"{len(issues)} issue categories found")
        return report_path

    # ── checks ────────────────────────────────────────────────────────

    def _check_broken_links(self) -> list[dict]:
        """Find wikilinks that point to pages that don't exist."""
        all_links = {}  # link_text -> set of source paths
        all_pages = self.wm.list_pages()

        for path in all_pages:
            if path in ("index.md", "log.md", "schema.md"):
                continue
            page = self.wm.read_page(path)
            if page is None:
                continue
            links = self.cre.extract_wikilinks(page.body)
            for link in links:
                if link not in all_links:
                    all_links[link] = []
                all_links[link].append(path)

        broken = []
        for link_text, sources in all_links.items():
            # Try to resolve the link to a file path
            resolved = self._resolve_wikilink(link_text)
            if resolved is None:
                for src in sources:
                    broken.append({"source": src, "link": link_text})

        return broken

    def _check_orphan_pages(self) -> list[str]:
        """Find pages with no inbound wikilinks."""
        all_pages = set()
        inbound_links = set()

        for path in self.wm.list_pages():
            if path in ("index.md", "log.md", "schema.md"):
                continue
            page = self.wm.read_page(path)
            if page:
                all_pages.add(path)
                links = self.cre.extract_wikilinks(page.body)
                # Check if this page's title is linked to
                title = page.frontmatter.get("title", "")
                if title:
                    inbound_links.add(title)

        # Also check index entries as inbound links
        for category in self.im.sections:
            for entry in self.im.list_entries(category):
                inbound_links.add(entry["title"])

        orphans = []
        for path in all_pages:
            page = self.wm.read_page(path)
            if page:
                title = page.frontmatter.get("title", "")
                # Skip pages that are referenced in index or by wikilink
                if title and title in inbound_links:
                    continue
                # Check if title matches filename
                slug = self._slug(title)
                if slug and path.endswith(f"{slug}.md"):
                    continue
                orphans.append(path)

        return orphans

    def _check_index_consistency(self) -> list[str]:
        """Check if index entries point to existing files."""
        missing = []
        for category in self.im.sections:
            for entry in self.im.list_entries(category):
                path = entry.get("link", "")
                if path and not self.wm._resolve_path(path).exists():
                    missing.append(f"{category}/{entry['title']} -> {path}")
        return missing

    def _check_contradictions(self) -> str:
        """Use LLM to check for contradictions between entity pages about the same topic."""
        entities = self.im.list_entries("entities")
        if len(entities) < 2:
            return ""

        # Group entities and check for potential contradictions via LLM
        # For now, check pairs of entities that appear together in source pages
        source_pages = self.wm.list_pages("sources")
        contradiction_report = ""

        # Collect page contents for LLM analysis
        pages_to_check = []
        for entry in entities[:10]:  # limit to avoid token overflow
            path = entry.get("link", "")
            page = self.wm.read_page(path)
            if page:
                pages_to_check.append({"title": entry["title"], "body": page.body})

        if len(pages_to_check) < 2:
            return ""

        # Build context for LLM
        context = ""
        for p in pages_to_check:
            context += f"\n--- [[{p['title']}]] ---\n{p['body'][:1000]}\n"

        prompt = f"""Review the following wiki entity pages for potential contradictions.
Look for:
- Conflicting facts about the same entity
- Outdated information that contradicts newer sources
- Incompatible claims in related concepts

List any contradictions found with specific references to the pages.
If no contradictions are found, respond with "No contradictions found."

Pages:
{context}"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            if result and "No contradictions found" not in result:
                contradiction_report = result
            return contradiction_report
        except Exception:
            return ""

    # ── helpers ───────────────────────────────────────────────────────

    def _resolve_wikilink(self, link_text: str) -> str | None:
        """Try to resolve a wikilink to an actual file path. Returns path or None."""
        slug = self._slug(link_text)
        # Search in entities, concepts, sources
        for directory in ("entities", "concepts", "sources"):
            path = f"{directory}/{slug}.md"
            if self.wm._resolve_path(path).exists():
                return path

        # Try index lookup
        for category in self.im.sections:
            for entry in self.im.list_entries(category):
                if self.cre._names_match(entry["title"], link_text):
                    path = entry.get("link", "")
                    if path and self.wm._resolve_path(path).exists():
                        return path
        return None

    @staticmethod
    def _slug(text: str) -> str:
        """Convert text to a kebab-case filename slug."""
        slug = text.lower().strip()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        return slug.strip('-')

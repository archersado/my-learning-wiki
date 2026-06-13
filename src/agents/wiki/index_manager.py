"""IndexManager — maintains wiki/index.md as a content-oriented catalog."""

import re
from .wiki_manager import WikiManager


class IndexManager:
    """Add, remove, and list entries in the wiki index."""

    def __init__(self, wiki_manager: WikiManager = None, wiki_root: str = None):
        self.wm = wiki_manager or WikiManager(wiki_root=wiki_root)
        self.index_path = "index.md"
        # section headers under which entries live
        self.sections = ["entities", "concepts", "sources", "analysis"]

    def _parse_index(self) -> dict[str, list[dict]]:
        """Parse index.md into {section: [{title, link, summary}]}."""
        page = self.wm.read_page(self.index_path)
        if page is None:
            return {s: [] for s in self.sections}

        result = {s: [] for s in self.sections}
        current_section = None

        for line in page.body.split('\n'):
            # detect section headers: ## Entities, ## Concepts, etc.
            header_match = re.match(r'^##\s+(.+)$', line)
            if header_match:
                header_text = header_match.group(1).strip().lower()
                if header_text in self.sections:
                    current_section = header_text
                continue

            # detect entry lines: - [[title]](link) | summary  or  - [[title]] | summary
            entry_match = re.match(r'^-?\s*\[\[([^\]]+)\]\](?:\(([^)]*)\))?\s*\|?\s*(.*)$', line)
            if entry_match and current_section:
                result[current_section].append({
                    "title": entry_match.group(1).strip(),
                    "link": entry_match.group(2) or entry_match.group(1),
                    "summary": entry_match.group(3).strip(),
                })

        return result

    def _serialize_index(self, data: dict[str, list[dict]]) -> str:
        """Rebuild index.md content from parsed structure."""
        header_map = {
            "entities": ("Entities", "People, organizations, products, and concrete things."),
            "concepts": ("Concepts", "Ideas, theories, methodologies, and abstract topics."),
            "sources": ("Sources", "Articles, papers, reports, and other raw sources that have been ingested."),
            "analysis": ("Analysis", "Query answers, comparisons, and synthesized insights."),
        }

        lines = ["# Wiki Index\n"]
        for section in self.sections:
            title, desc = header_map[section]
            lines.append(f"## {title}\n")
            lines.append(f"> {desc}\n")
            for entry in data[section]:
                link = entry["link"]
                lines.append(f"- [[{entry['title']}]]({link}) | {entry['summary']}")
            lines.append("")  # blank line between sections

        return '\n'.join(lines)

    def add_entry(self, category: str, title: str, link: str, summary: str):
        """Add an entry to the given category in the index."""
        if category not in self.sections:
            raise ValueError(f"Unknown category: {category}. Must be one of {self.sections}")

        data = self._parse_index()
        # deduplicate by title within category
        data[category] = [e for e in data[category] if e["title"] != title]
        data[category].append({"title": title, "link": link, "summary": summary})

        content = self._serialize_index(data)
        self.wm.write_page(self.index_path, content)

    def remove_entry(self, title: str, category: str = None):
        """Remove an entry by title. If category is None, searches all categories."""
        data = self._parse_index()
        if category:
            data[category] = [e for e in data[category] if e["title"] != title]
        else:
            for cat in self.sections:
                data[cat] = [e for e in data[cat] if e["title"] != title]
        content = self._serialize_index(data)
        self.wm.write_page(self.index_path, content)

    def list_entries(self, category: str) -> list[dict]:
        """List all entries in a category."""
        if category not in self.sections:
            raise ValueError(f"Unknown category: {category}")
        data = self._parse_index()
        return data[category]

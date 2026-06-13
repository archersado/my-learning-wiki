"""WikiManager — manages CRUD operations on wiki markdown files."""

import os
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class WikiPage:
    """Represents a wiki page with parsed frontmatter."""
    path: str
    frontmatter: dict
    body: str


class WikiManager:
    """Read/write/delete markdown files under the wiki/ root directory."""

    def __init__(self, wiki_root: str = None):
        if wiki_root is None:
            wiki_root = str(Path(__file__).resolve().parent.parent.parent.parent / "wiki")
        self.wiki_root = Path(wiki_root).resolve()
        if not self.wiki_root.exists():
            self.wiki_root.mkdir(parents=True)

    # ── path safety ──────────────────────────────────────────────────

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path under wiki_root, preventing directory traversal."""
        resolved = (self.wiki_root / relative_path).resolve()
        if not str(resolved).startswith(str(self.wiki_root.resolve())):
            raise ValueError(f"Path escapes wiki root: {relative_path}")
        return resolved

    # ── frontmatter helpers ──────────────────────────────────────────

    @staticmethod
    def _parse_frontmatter(text: str) -> tuple[dict, str]:
        """Parse YAML-like frontmatter from text. Returns (dict, body)."""
        match = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
        if not match:
            return {}, text
        fm_text = match.group(1)
        body = match.group(2)
        frontmatter = {}
        lines = fm_text.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            if ':' not in line:
                i += 1
                continue
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            # parse inline list
            if value.startswith('[') and value.endswith(']'):
                inner = value[1:-1].strip()
                frontmatter[key] = [item.strip().strip('"\'[]') for item in inner.split(',')] if inner else []
            # parse block-style list (key: followed by indented - items)
            elif value == '':
                items = []
                i += 1
                while i < len(lines):
                    item_line = lines[i]
                    if re.match(r'^\s+- ', item_line):
                        items.append(item_line.strip().lstrip('- ').strip('"\''))
                        i += 1
                    else:
                        break
                frontmatter[key] = items
                continue
            else:
                frontmatter[key] = value
            i += 1
        return frontmatter, body

    @staticmethod
    def _build_frontmatter(fm: dict) -> str:
        """Build a YAML frontmatter block from a dict."""
        if not fm:
            return ''
        lines = ['---']
        for key, value in fm.items():
            if isinstance(value, list):
                lines.append(f'{key}:')
                for item in value:
                    lines.append(f'  - {item}')
            else:
                lines.append(f'{key}: {value}')
        lines.append('---')
        return '\n'.join(lines) + '\n'

    # ── CRUD ─────────────────────────────────────────────────────────

    def read_page(self, relative_path: str) -> Optional[WikiPage]:
        """Read a wiki page and return parsed frontmatter + body."""
        path = self._resolve_path(relative_path)
        if not path.exists():
            return None
        text = path.read_text(encoding='utf-8')
        fm, body = self._parse_frontmatter(text)
        return WikiPage(path=str(path), frontmatter=fm, body=body)

    def write_page(self, relative_path: str, body: str, frontmatter: dict = None):
        """Write or overwrite a wiki page. Creates parent directories if needed."""
        path = self._resolve_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = ''
        if frontmatter:
            content = self._build_frontmatter(frontmatter)
        content += body
        path.write_text(content, encoding='utf-8')

    def update_page(self, relative_path: str, body: str = None, frontmatter: dict = None,
                    update_frontmatter: bool = False):
        """Update an existing page's body and/or frontmatter.

        If update_frontmatter is True, replace the entire frontmatter with the given dict.
        Otherwise, only update the keys present in the given frontmatter dict.
        """
        page = self.read_page(relative_path)
        if page is None:
            raise FileNotFoundError(f"Page not found: {relative_path}")

        new_body = body if body is not None else page.body
        new_fm = page.frontmatter.copy()

        if frontmatter:
            if update_frontmatter:
                new_fm = frontmatter.copy()
            else:
                new_fm.update(frontmatter)

        self.write_page(relative_path, new_body, new_fm if new_fm else None)

    def delete_page(self, relative_path: str):
        """Delete a wiki page."""
        path = self._resolve_path(relative_path)
        if not path.exists():
            return
        path.unlink()

    def list_pages(self, relative_dir: str = '') -> list[str]:
        """List all .md files under a wiki subdirectory, recursively."""
        dir_path = self._resolve_path(relative_dir) if relative_dir else self.wiki_root
        if not dir_path.is_dir():
            return []
        return [str(p.relative_to(self.wiki_root)) for p in sorted(dir_path.rglob('*.md'))]

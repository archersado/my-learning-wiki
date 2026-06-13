"""LogManager — maintains wiki/log.md as an append-only operation log."""

import re
from datetime import date
from .wiki_manager import WikiManager


VALID_TYPES = {"ingest", "query", "lint"}
BATCH_TYPES = {"ingest (batch)", "query (batch)", "lint (batch)"}
ALL_TYPES = VALID_TYPES | BATCH_TYPES


class LogManager:
    """Append and query entries from the wiki operation log, archived by date under logs/."""

    def __init__(self, wiki_manager: WikiManager = None, wiki_root: str = None):
        self.wm = wiki_manager or WikiManager(wiki_root=wiki_root)
        self.log_path = "log.md"  # kept for backward-compat reads
        self._entry_re = re.compile(r'^## \[(\d{4}-\d{2}-\d{2})\] (.+?) \| (.+)$')

    def _daily_log_path(self, day: str = None) -> str:
        return f"logs/{day or date.today().isoformat()}.md"

    def append(self, operation_type: str, title: str, details: str = ""):
        """Append a log entry to today's dated log file under logs/."""
        if operation_type not in ALL_TYPES:
            raise ValueError(f"Invalid operation type: {operation_type}. Must be one of {ALL_TYPES}")

        today = date.today().isoformat()
        path = self._daily_log_path(today)
        page = self.wm.read_page(path)
        body = page.body if page else f"# Wiki Log — {today}\n\n"

        entry = f"\n## [{today}] {operation_type} | {title}\n"
        if details:
            entry += f"\n{details}\n"

        if not body.endswith('\n'):
            body += '\n'

        self.wm.write_page(path, body + entry)

    def get_today_titles(self, operation_type: str = "ingest") -> list[str]:
        """Return all titles logged today for the given operation type."""
        path = self._daily_log_path()
        page = self.wm.read_page(path)
        if page is None:
            return []
        titles = []
        for line in page.body.split('\n'):
            m = self._entry_re.match(line)
            if m and m.group(2).startswith(operation_type):
                titles.append(m.group(3))
        return titles

    def recent(self, n: int = 5) -> list[dict]:
        """Return the last n log entries from today's log."""
        path = self._daily_log_path()
        page = self.wm.read_page(path)
        if page is None:
            return []

        entries = []
        for line in page.body.split('\n'):
            m = self._entry_re.match(line)
            if m:
                entries.append({
                    "date": m.group(1),
                    "type": m.group(2),
                    "title": m.group(3),
                })
        return entries[-n:]

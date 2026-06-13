"""WikiQueryAgent — answers questions by retrieving wiki pages and synthesizing via LLM."""

import re
from datetime import date
from ..base_agent import BaseAgent
from langchain_core.messages import HumanMessage
from .wiki_manager import WikiManager
from .index_manager import IndexManager
from .log_manager import LogManager


class WikiQueryAgent(BaseAgent):
    """Retrieves relevant wiki pages, synthesizes an answer with citations, optionally saves as analysis."""

    SYSTEM_PROMPT = """You are a knowledge synthesis expert. You are given a question and several relevant wiki pages.

Your task:
1. Synthesize a comprehensive answer based on the provided wiki pages
2. Cite your sources using [[wikilink]] syntax for every claim
3. If the wiki pages don't contain enough information to fully answer, say so explicitly
4. Structure your answer clearly with headings and bullet points where appropriate
5. Write in Chinese unless the question is clearly in English

Format your answer as a well-structured markdown document."""

    def process(self, state: dict) -> dict:
        """Process a query from state['question'] and store result in state['query_result']."""
        question = state.get("question", "")
        save = state.get("save_as_analysis", False)
        result = self.query(question, save_as_analysis=save)
        return {**state, "query_result": result}

    def __init__(self, llm=None, wiki_root: str = None):
        super().__init__(llm, skip_db=True)
        self.wm = WikiManager(wiki_root=wiki_root)
        self.im = IndexManager(wiki_manager=self.wm)
        self.lm = LogManager(wiki_manager=self.wm)

    def query(self, question: str, save_as_analysis: bool = False) -> dict:
        """Answer a question by retrieving wiki pages and synthesizing a response.

        Returns:
            {
                "question": str,
                "answer": str,
                "sources_used": list[str],
                "saved_path": str | None,
            }
        """
        # Step 1: Find relevant pages via index and text search
        relevant_pages = self._find_relevant_pages(question)

        if not relevant_pages:
            answer = f"Wiki 中暂未收录与「{question}」相关的内容。建议先通过 Ingest 流程导入相关来源。"
            result = {
                "question": question,
                "answer": answer,
                "sources_used": [],
                "saved_path": None,
            }
            self.lm.append("query", question, "No relevant pages found")
            return result

        # Step 2: Read page contents
        page_contents = []
        for path in relevant_pages:
            page = self.wm.read_page(path)
            if page:
                page_contents.append({"path": path, "title": page.frontmatter.get("title", path), "body": page.body})

        if not page_contents:
            answer = f"找到了相关页面索引但无法读取内容，请检查 {relevant_pages}"
            self.lm.append("query", question, "Pages found but unreadable")
            return {"question": question, "answer": answer, "sources_used": [], "saved_path": None}

        # Step 3: Synthesize answer via LLM
        answer = self._synthesize_answer(question, page_contents)

        # Step 4: Optionally save as analysis
        saved_path = None
        if save_as_analysis:
            slug = self._slug(question)
            saved_path = f"analysis/{slug}.md"
            fm = {
                "title": question,
                "type": "analysis",
                "sources": [f"[[{p['title']}]]" for p in page_contents],
            }
            self.wm.write_page(saved_path, answer, fm)
            # Add to index
            self.im.add_entry("analysis", question, saved_path, f"Q: {question}")

        # Step 5: Log
        sources = [p["title"] for p in page_contents]
        self.lm.append("query", question, f"Sources: {', '.join(sources)}")

        return {
            "question": question,
            "answer": answer,
            "sources_used": sources,
            "saved_path": saved_path,
        }

    # ── retrieval ─────────────────────────────────────────────────────

    def _find_relevant_pages(self, question: str) -> list[str]:
        """Find relevant wiki pages by searching index.md and scanning page content."""
        raw = re.findall(r'[\w\u4e00-\u9fff]{2,}', question.lower())
        # For Chinese strings, also add 2-gram and 3-gram substrings to improve recall
        terms = set(raw)
        for token in raw:
            if re.search(r'[\u4e00-\u9fff]', token):
                for n in (2, 3):
                    for i in range(len(token) - n + 1):
                        terms.add(token[i:i+n])
        terms = list(terms)

        # Strategy 1: Search index entries (sources section first)
        matched_paths: dict[str, int] = {}  # path → score

        section_priority = {"sources": 3, "analysis": 2, "concepts": 1, "entities": 0}
        for category in self.im.sections:
            weight = section_priority.get(category, 1)
            for entry in self.im.list_entries(category):
                title_lower = entry["title"].lower()
                summary_lower = entry["summary"].lower()
                hits = sum(1 for t in terms if t in title_lower or t in summary_lower)
                if hits > 0:
                    path = entry.get("link", "")
                    if path and self.wm._resolve_path(path).exists():
                        matched_paths[path] = matched_paths.get(path, 0) + hits * weight

        # Strategy 2: Full-text search — sources/ only to avoid empty entity pages
        source_pages = [p for p in self.wm.list_pages() if p.startswith("sources/")]
        for path in source_pages:
            if path in matched_paths:
                continue
            page = self.wm.read_page(path)
            if page and len(page.body) > 100:
                full_text = (page.body + " " + str(page.frontmatter)).lower()
                hits = sum(1 for t in terms if t in full_text)
                if hits > 0:
                    matched_paths[path] = hits * 3

        # Sort by score, take top 20, filter out nearly-empty pages
        ranked = sorted(matched_paths.items(), key=lambda x: x[1], reverse=True)
        result = []
        for path, _ in ranked[:20]:
            page = self.wm.read_page(path)
            if page and len(page.body.strip()) > 50:
                result.append(path)

        return result

    # ── synthesis ─────────────────────────────────────────────────────

    BATCH_CHARS = 24000   # chars per batch sent to LLM
    MAX_PAGE_CHARS = 4000 # max chars taken from each page

    def _synthesize_answer(self, question: str, pages: list[dict]) -> str:
        """Batch pages into chunks, summarize each, then merge into final answer."""
        # Build batches
        batches: list[list[dict]] = []
        current, current_len = [], 0
        for p in pages:
            body = p["body"][:self.MAX_PAGE_CHARS]
            if current_len + len(body) > self.BATCH_CHARS and current:
                batches.append(current)
                current, current_len = [], 0
            current.append({**p, "body": body})
            current_len += len(body)
        if current:
            batches.append(current)

        if len(batches) == 1:
            return self._call_llm_synthesis(question, batches[0], final=True)

        # Step 1: summarize each batch
        partials = []
        for i, batch in enumerate(batches):
            partial = self._call_llm_synthesis(question, batch, final=False)
            partials.append(f"## 批次 {i+1}\n\n{partial}")

        # Step 2: merge all partials into final answer
        merged_context = "\n\n".join(partials)
        merge_prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"Question: {question}\n\n"
            f"以下是分批处理的中间摘要，请综合所有内容生成最终完整答案：\n\n{merged_context}"
        )
        response = self.llm.invoke([HumanMessage(content=merge_prompt)])
        return response.content.strip()

    def _call_llm_synthesis(self, question: str, pages: list[dict], final: bool) -> str:
        context = "\n".join(
            f"\n--- [[{p['title']}]] ---\n{p['body']}" for p in pages
        )
        instruction = "综合所有内容生成完整答案" if final else "提取与问题最相关的关键信息和观点，保留来源引用"
        prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"Question: {question}\n\n"
            f"任务：{instruction}\n\n"
            f"参考材料：\n{context}"
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()

    # ── utilities ─────────────────────────────────────────────────────

    @staticmethod
    def _slug(text: str) -> str:
        """Convert text to a kebab-case filename slug."""
        slug = text.lower().strip()
        # Replace Chinese punctuation and spaces
        slug = re.sub(r'[\s\u3000\u200b]+', '-', slug)
        slug = re.sub(r'[^\w\u4e00-\u9fff-]', '', slug)
        # Truncate
        return slug[:80].strip('-')

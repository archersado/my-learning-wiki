#!/usr/bin/env python
"""Test: drop files into inbox/ and ingest into wiki."""
import os, sys

os.environ["USE_LOCAL_STORAGE"] = "true"

from dotenv import load_dotenv
load_dotenv(override=True)

sys.path.insert(0, os.path.dirname(__file__))

from src.config.settings import build_llm, LOCAL_PENDING_DIR
from src.agents.wiki.wiki_ingest_agent import WikiIngestAgent
from pathlib import Path


def create_test_files():
    """Create sample test files in inbox/."""
    inbox = os.path.join(LOCAL_PENDING_DIR, "inbox")
    os.makedirs(inbox, exist_ok=True)

    # 1. Markdown file
    md_path = os.path.join(inbox, "test-agent-patterns.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("""---
title: "Agent 工程模式总结"
---

# Agent 工程模式总结

本文总结了常见的 Agent 工程模式，包括 ReAct、Plan-and-Execute、Multi-Agent 协作等。

## ReAct Pattern

ReAct (Reasoning + Acting) 是最基础的 Agent 模式，通过交替执行 action 和 reasoning 来完成任务。

## Plan-and-Execute

先制定完整计划，再逐步执行各步骤。适用于复杂的多步骤任务。

## Multi-Agent 协作

多个专用 Agent 协作，各自负责不同领域。类似团队分工。
""")

    # 2. Text file
    txt_path = os.path.join(inbox, "llm-optimization-tips.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("""LLM 优化最佳实践

1. 使用 prompt caching 减少重复 token 的开销
2. 对长文档使用分块检索
3. 合理设置 max_tokens 避免过度输出
4. 使用结构化输出确保格式一致
5. 定期评估模型更新带来的效果变化
""")

    # 3. JSON file
    json_path = os.path.join(inbox, "claude-code-workflow.json")
    with open(json_path, "w", encoding="utf-8") as f:
        import json
        json.dump({
            "title": "Claude Code 工作流实践",
            "content": """Claude Code 提供了强大的 AI 辅助编程能力。核心功能包括：
- 多文件编辑和搜索
- Bash 命令执行
- Agent 协作模式
- 记忆系统支持""",
            "link": "https://claude.ai/code",
            "published": "2025-05-18",
        }, f, ensure_ascii=False)

    print(f"Created 3 test files in {inbox}")
    for f in os.listdir(inbox):
        if os.path.isfile(os.path.join(inbox, f)):
            print(f"  - {f}")


def main():
    print("=" * 60)
    print("Step 1: Creating test files in inbox/")
    print("=" * 60)
    create_test_files()

    print("\n" + "=" * 60)
    print("Step 2: Ingesting inbox files into wiki/ai-highlights/")
    print("=" * 60)

    llm = build_llm()
    agent = WikiIngestAgent(llm=llm)
    result = agent.ingest_inbox(category="ai-highlights")
    print(result)

    # Show wiki structure
    print("\n" + "=" * 60)
    print("Wiki structure after inbox ingest:")
    print("=" * 60)
    wiki_root = Path(__file__).parent / "wiki"
    for p in sorted(wiki_root.rglob("*.md")):
        if "inbox" not in str(p):
            rel = p.relative_to(wiki_root)
            print(f"  {rel}")

    print(f"\nDone!")


if __name__ == "__main__":
    main()

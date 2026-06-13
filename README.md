# Deep Wiki

An AI-powered knowledge base system that automatically scrapes RSS feeds, extracts structured knowledge via LLM, and organizes it into a file-based wiki with cross-referenced entity/concept pages. Supports natural-language querying over the accumulated wiki content.

## Architecture

```
RSS/Atom Feeds  →  ScrapingExpert  →  pending_articles/  →  WikiIngestAgent  →  Wiki (Markdown)
                                                                        ↓
                                                              WikiQueryAgent ← Question
```

### Workflow

1. **Scrape** — `ScrapingExpert` fetches RSS/Atom feeds (blogs, Twitter/X via xgo.ing), extracts article content, and saves them as local JSON files in `pending_articles/`.
2. **Ingest** — `WikiIngestAgent` reads pending articles, uses LLM to extract entities, concepts, key points, and creates wiki markdown pages under category directories. Entity/concept pages are cross-referenced via `[[wikilink]]` syntax.
3. **Query** — `WikiQueryAgent` retrieves relevant wiki pages via index + full-text search, synthesizes an answer with citations via LLM, and optionally saves the answer as an analysis page.
4. **Lint** — `WikiLintAgent` runs health checks: broken wikilinks, orphan pages, index inconsistencies, and LLM-based contradiction detection.

## Project Structure

```
.
├── src/
│   ├── agents/
│   │   ├── scraping_expert.py        # RSS scraping → local JSON files
│   │   ├── wiki/
│   │   │   ├── wiki_ingest_agent.py  # LLM extraction → wiki pages
│   │   │   ├── wiki_query_agent.py   # Question → wiki search + synthesis
│   │   │   ├── wiki_lint_agent.py    # Wiki health checks
│   │   │   ├── wiki_manager.py       # Markdown CRUD + frontmatter
│   │   │   ├── index_manager.py      # Page indexing
│   │   │   ├── cross_ref_engine.py   # Wikilink cross-references
│   │   │   └── log_manager.py        # Operation logging
│   │   ├── base_agent.py             # Abstract agent base class
│   │   ├── custom_llm.py             # Custom LLM wrapper (stream/non-stream)
│   │   └── ...                       # Content workflow agents
│   ├── tools/
│   │   ├── db_manager.py             # MongoDB connection (optional)
│   │   ├── web_scraper.py            # Web scraping utilities
│   │   └── ...
│   ├── config/settings.py            # Feed URLs, LLM config, DB config
│   ├── graph/workflow_graph.py       # LangGraph workflow definition
│   ├── scripts/                      # Topic-specific ingest/query scripts
│   └── main.py                       # Main entry point
├── run_ai_highlights.py              # Scrape AI feeds → wiki/ai-highlights
├── run_info_resources.py             # Scrape industry feeds → wiki/industry-news
├── run_query.py                      # Interactive wiki query CLI
└── wiki/                             # Generated wiki content (gitignored)
    ├── ai-highlights/
    ├── industry-news/
    └── engineering-tips/
```

## Wiki Categories

| Category | Source | Description |
|---|---|---|
| `ai-highlights` | AI_HIGH_SCORE feeds | AI model releases, research, tools, infrastructure |
| `industry-news` | INFO_RESOURCES (~150 feeds) | Tech blogs, security, engineering, AI company updates |
| `engineering-tips` | CODING_PATTERN feeds | Software engineering practices, coding patterns |

## Quick Start

### Prerequisites

- Python 3.10+
- Azure OpenAI or compatible LLM API

### Setup

```bash
# Install dependencies
poetry install

# Create .env with required variables (pick one LLM backend):

# Option 1: GLM (default, if ANTHROPIC_AUTH_TOKEN is set)
ANTHROPIC_BASE_URL=https://ai.enncloud.cn/v1/chat/completions
ANTHROPIC_AUTH_TOKEN=your-glm-api-key-here

# Option 2: Deepseek (via custom gateway)
LLM_API_KEY=your-key
LLM_DEEPSEEK_URL=https://...
LLM_DEEPSEEK_MODEL=deepseek-r1

# Option 3: Qwen via custom gateway
LLM_GPT4O_URL=https://...
LLM_GPT4O_MODEL=Qwen3-235B-A22B-FP8-No-Think

# Optional: Azure OpenAI (for standalone scripts)
AZURE_OPENAI_BASE_URL=https://your-resource.openai.azure.com/...
AZURE_OPENAI_API_KEY=your-azure-key

# Optional: MongoDB config (if not using local storage)
# MONGO_HOST=...
```

### Storage Modes

This project supports two storage modes, controlled by the `USE_LOCAL_STORAGE` environment variable:

| Mode | Config | How it works |
|---|---|---|
| **Local (Recommended)** | `USE_LOCAL_STORAGE=true` | Articles saved to `pending_articles/` → WikiIngestAgent reads local JSON files |
| MongoDB | `USE_LOCAL_STORAGE=false` | Articles saved to MongoDB → WikiIngestAgent queries MongoDB |

**Local mode is the default — no MongoDB required.**

### Running

#### Local Mode

```bash
export USE_LOCAL_STORAGE=true

# Scrape and ingest
python test_local_ingest.py              # Quick test: 2 feeds, few articles
python run_ai_highlights.py              # Scrape AI feeds → Ingest
python run_info_resources.py             # Scrape industry feeds → Ingest

# Inbox mode — drop files directly
cp my-article.md pending_articles/inbox/
python -c "
import os, sys; os.environ['USE_LOCAL_STORAGE'] = 'true'
from dotenv import load_dotenv; load_dotenv(override=True)
sys.path.insert(0, '.')
from src.config.settings import build_llm
from src.agents.wiki.wiki_ingest_agent import WikiIngestAgent
agent = WikiIngestAgent(llm=build_llm())
agent.ingest_inbox(category='ai-highlights')
"
```

Supported inbox formats:
- `.md` / `.txt` — raw content, filename used as title
- `.json` — structured with `title`, `content` keys (optionally `link`, `published`)

After ingest, processed files move to `pending_articles/inbox/done/`.

#### MongoDB Mode

```bash
export USE_LOCAL_STORAGE=false
python run_ai_highlights.py      # Scrapes → MongoDB → Ingests to wiki
```

### Query the Wiki

```bash
python run_query.py <category> "<question>" [--save]

Categories:
  ai      → wiki/ai-highlights    (AI 精选)
  info    → wiki/industry-news    (行业时讯)
  coding  → wiki/engineering-tips (工程技巧)

Options:
  --save  Save the answer as an analysis page in the wiki

Examples:
  python run_query.py ai "最近有哪些重要的 AI 进展？"
  python run_query.py ai "GPT-5.5 有哪些新特性？" --save
  python run_query.py coding "有哪些实用的 Agent 工程实践？"
```

### Full Pipeline

```bash
# Run the full pipeline: scrape → ingest → query → lint
python src/main.py --wiki
```

## Wiki Structure

Each wiki category contains:

```
wiki/{category}/
├── sources/           # Source article pages (extracted via LLM)
├── entities/          # Entity pages (people, companies, products)
├── concepts/          # Concept pages (topics, ideas, methodologies)
├── analysis/          # Query answers and lint reports
├── index.md           # Page index for retrieval
├── log.md             # Operation log
└── schema.md          # Wiki schema documentation
```

Pages use frontmatter metadata and `[[wikilink]]` syntax for cross-references.

## Dependencies

- **LangGraph** — Workflow orchestration
- **feedparser** — RSS/Atom feed parsing
- **pymongo** — MongoDB driver
- **BeautifulSoup** — HTML content extraction

from src.tools.github_trending import GitHubTrendingCollector


HTML = """
<article class="Box-row">
  <h2><a href="/acme/agent-kit"> acme / agent-kit </a></h2>
  <p>An agent framework</p>
  <span itemprop="programmingLanguage">Python</span>
  <span>1,234 stars today</span>
</article>
<article class="Box-row">
  <h2><a href="/example/runtime">example/runtime</a></h2>
  <span itemprop="programmingLanguage">Rust</span>
  <span>98 stars this week</span>
</article>
"""


def test_parse_trending_html():
    repos = GitHubTrendingCollector.parse_trending_html(HTML)
    assert repos == [
        {
            "full_name": "acme/agent-kit",
            "url": "https://github.com/acme/agent-kit",
            "description": "An agent framework",
            "language": "Python",
            "stars_period": 1234,
        },
        {
            "full_name": "example/runtime",
            "url": "https://github.com/example/runtime",
            "description": "",
            "language": "Rust",
            "stars_period": 98,
        },
    ]


def test_article_preserves_trend_signals():
    article = GitHubTrendingCollector._to_article({
        "rank": 1,
        "since": "daily",
        "full_name": "acme/agent-kit",
        "url": "https://github.com/acme/agent-kit",
        "description": "An agent framework",
        "language": "Python",
        "stars_period": 42,
        "stars": 1000,
        "topics": ["agents", "llm"],
    }, "2026-09-04T08:00:00+08:00")
    assert article["source"] == "github-trending"
    assert "Stars gained in period: 42" in article["content"]
    assert article["github"]["topics"] == ["agents", "llm"]

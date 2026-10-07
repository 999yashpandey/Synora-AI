from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS

from app.ai.llm import SynoraLLM


class SynoraWebSearch:
    """
    Search the web, fetch actual article pages, extract readable text,
    and generate short summaries using Synora's local LLM.
    """

    def __init__(self, max_results: int = 6):
        self.max_results = max_results
        self.llm = SynoraLLM()

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/154.0 Safari/537.36"
            )
        }

    def search(self, query: str, summarize: bool = True) -> str:
        query = str(query or "").strip()

        if not query:
            return "Please provide something to search for."

        try:
            with DDGS() as ddgs:
                results = list(
                    ddgs.text(
                        f"{query} latest news",
                        max_results=self.max_results,
                    )
                )
        except Exception as error:
            return f"I couldn't search the web right now: {error}"

        results = self._filter_results(results)

        if not results:
            return "I couldn't find relevant web results."

        if not summarize:
            return self._format_results(results)

        articles = []

        for result in results[:5]:
            article = self._fetch_article(result)

            if article:
                articles.append(article)

        # If article extraction fails, fall back to snippets.
        if not articles:
            return self._summarize_snippets(query, results)

        return self._summarize_articles(
            query,
            articles,
        )

    def _filter_results(self, results: list[dict]) -> list[dict]:
        filtered = []

        blocked = {
            "news.google.com",
            "google.com",
        }

        generic_paths = (
            "/topics/",
            "/topic/",
            "/category/",
            "/categories/",
            "/tag/",
            "/tags/",
        )

        for result in results:
            title = str(
                result.get("title", "")
            ).strip()

            url = str(
                result.get("href", "")
            ).strip()

            snippet = str(
                result.get("body", "")
            ).strip()

            if not title or not url:
                continue

            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()

            if domain in blocked:
                continue

            if any(
                path.startswith(item)
                for item in generic_paths
            ):
                continue

            # Ignore obvious homepage results.
            if path in ("", "/"):
                continue

            filtered.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        return filtered

    def _fetch_article(
        self,
        result: dict,
    ) -> dict | None:

        url = result["url"]

        try:
            with httpx.Client(
                headers=self.headers,
                timeout=8.0,
                follow_redirects=True,
            ) as client:

                response = client.get(url)

                if response.status_code != 200:
                    return None

                content_type = response.headers.get(
                    "content-type",
                    "",
                ).lower()

                if "text/html" not in content_type:
                    return None

                html = response.text

        except Exception as error:
            print(
                f"[Synora Web] Could not fetch {url}: {error}"
            )
            return None

        try:
            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            # Remove things that aren't article content.
            for element in soup(
                [
                    "script",
                    "style",
                    "noscript",
                    "nav",
                    "footer",
                    "header",
                    "aside",
                    "form",
                    "iframe",
                ]
            ):
                element.decompose()

            article = soup.find("article")

            if article:
                text = article.get_text(
                    separator=" ",
                    strip=True,
                )
            else:
                # Try common article containers.
                candidates = soup.select(
                    "[class*='article'], "
                    "[class*='story'], "
                    "[class*='content'], "
                    "[class*='post']"
                )

                if candidates:
                    largest = max(
                        candidates,
                        key=lambda x: len(
                            x.get_text(" ", strip=True)
                        ),
                    )

                    text = largest.get_text(
                        separator=" ",
                        strip=True,
                    )
                else:
                    text = soup.get_text(
                        separator=" ",
                        strip=True,
                    )

            text = self._clean_text(text)

            # Don't send tiny pages to Qwen.
            if len(text) < 300:
                return None

            # Keep local model context manageable.
            text = text[:12000]

            return {
                "title": result["title"],
                "url": url,
                "text": text,
            }

        except Exception as error:
            print(
                f"[Synora Web] Article extraction error: {error}"
            )
            return None

    def _clean_text(self, text: str) -> str:
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    def _summarize_articles(
        self,
        query: str,
        articles: list[dict],
    ) -> str:

        source_text = []

        for index, article in enumerate(
            articles[:4],
            start=1,
        ):
            source_text.append(
                f"""
ARTICLE {index}

Title:
{article["title"]}

URL:
{article["url"]}

Article text:
{article["text"]}
""".strip()
            )

        combined = "\n\n".join(
            source_text
        )

        prompt = f"""
You are Synora AI's news briefing system.

The user asked:
{query}

Below are actual news articles retrieved from the web.

{combined}

Create a concise news briefing.

Rules:
- Summarize the actual articles, not the websites.
- Do not invent facts.
- Use only information contained in the articles.
- Give the 3 most important distinct stories.
- If multiple articles cover the same event, combine them.
- Each story should be 2-3 short sentences.
- Explain what happened and why it matters when supported.
- Keep the response concise.
- Include the source URL.
- Do not mention your reasoning.
- Do not say "as an AI".
- Do not describe the search process.

Format:

1. **Headline**
Short 2-3 sentence summary.

Source: URL

2. **Headline**
Short 2-3 sentence summary.

Source: URL

3. **Headline**
Short 2-3 sentence summary.

Source: URL
"""

        try:
            response = self.llm.generate(
                prompt
            )

            if response.strip():
                return response.strip()

        except Exception as error:
            print(
                f"[Synora Web] LLM summary error: {error}"
            )

        return self._format_articles(
            articles
        )

    def _summarize_snippets(
        self,
        query: str,
        results: list[dict],
    ) -> str:

        snippets = []

        for index, result in enumerate(
            results[:5],
            start=1,
        ):
            snippets.append(
                f"""
{index}.
Title: {result["title"]}
URL: {result["url"]}
Snippet: {result["snippet"]}
""".strip()
            )

        prompt = f"""
Summarize these web results for the user.

User query:
{query}

{chr(10).join(snippets)}

Give the most useful information available.
Do not invent facts.
Keep each item to 1-2 sentences.
Include the source URL.
"""

        try:
            response = self.llm.generate(
                prompt
            )

            if response.strip():
                return response.strip()

        except Exception:
            pass

        return self._format_results(
            results
        )

    def _format_articles(
        self,
        articles: list[dict],
    ) -> str:

        output = []

        for index, article in enumerate(
            articles[:4],
            start=1,
        ):
            output.append(
                f"{index}. {article['title']}\n"
                f"{article['text'][:500]}...\n"
                f"Source: {article['url']}"
            )

        return "\n\n".join(output)

    def _format_results(
        self,
        results: list[dict],
    ) -> str:

        output = []

        for index, result in enumerate(
            results[:5],
            start=1,
        ):
            output.append(
                f"{index}. {result['title']}\n"
                f"{result['snippet']}\n"
                f"Source: {result['url']}"
            )

        return "\n\n".join(output)


def search_web(
    query: str,
    summarize: bool = True,
) -> str:

    return SynoraWebSearch().search(
        query,
        summarize=summarize,
    )


if __name__ == "__main__":

    query = input(
        "What do you want to search for? "
    ).strip()

    if query:
        print("\nSearching the web...\n")

        result = search_web(
            query,
            summarize=True,
        )

        print(result)
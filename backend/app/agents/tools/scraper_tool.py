"""
Website Scraper Tool
--------------------
Fetches a company's homepage and extracts:
  - page title, meta description
  - key sentences about what they do
  - tech stack hints (from script tags, meta, footer)
  - recent news/blog post titles
  - job listings hints (are they hiring?)

Used by the Research Agent node.
No API key needed — pure httpx + BeautifulSoup.
"""

import httpx, re
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Tech stack fingerprints — script src / meta generator patterns
TECH_FINGERPRINTS = {
    "React":        [r"react", r"_next/", r"__NEXT_DATA__"],
    "Next.js":      [r"_next/static", r"__NEXT_DATA__"],
    "Vue":          [r"vue\.js", r"vue\.min\.js", r"nuxt"],
    "Angular":      [r"angular", r"ng-version"],
    "Tailwind":     [r"tailwind"],
    "Shopify":      [r"shopify", r"cdn\.shopify"],
    "WordPress":    [r"wp-content", r"wp-includes"],
    "Webflow":      [r"webflow"],
    "Stripe":       [r"stripe\.com/v3", r"js\.stripe\.com"],
    "Intercom":     [r"intercom"],
    "Segment":      [r"segment\.com", r"analytics\.js"],
    "HubSpot":      [r"hubspot", r"hs-scripts"],
    "Salesforce":   [r"salesforce", r"force\.com"],
    "AWS":          [r"amazonaws\.com", r"cloudfront\.net"],
    "Vercel":       [r"vercel", r"\.vercel\.app"],
    "Heroku":       [r"heroku"],
    "Firebase":     [r"firebase", r"firebaseapp\.com"],
    "Supabase":     [r"supabase"],
    "OpenAI":       [r"openai"],
    "Python":       [r"django", r"flask", r"fastapi", r"\.py"],
    "Node.js":      [r"express", r"node"],
}


def _detect_tech(html: str) -> list[str]:
    detected = []
    html_lower = html.lower()
    for tech, patterns in TECH_FINGERPRINTS.items():
        if any(re.search(p, html_lower) for p in patterns):
            detected.append(tech)
    return detected


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_key_sentences(soup: BeautifulSoup, max_chars: int = 600) -> str:
    """Pull the most informative sentences from visible text."""
    # Priority zones: hero section, about, features
    priority_tags = ["h1", "h2", "h3"]
    sentences = []

    for tag in priority_tags:
        for el in soup.find_all(tag):
            text = _clean_text(el.get_text())
            if 10 < len(text) < 200:
                sentences.append(text)

    # Also grab first few <p> tags
    for p in soup.find_all("p")[:8]:
        text = _clean_text(p.get_text())
        if 20 < len(text) < 300:
            sentences.append(text)

    # Deduplicate and join
    seen, result = set(), []
    for s in sentences:
        if s not in seen:
            seen.add(s)
            result.append(s)

    joined = " | ".join(result)
    return joined[:max_chars]


def _extract_blog_titles(soup: BeautifulSoup) -> list[str]:
    """Find blog post or news titles — signals recent activity."""
    titles = []
    # Common blog containers
    for el in soup.find_all(["article", "div"], class_=re.compile(r"blog|post|news|article", re.I)):
        for h in el.find_all(["h2", "h3", "h4"]):
            text = _clean_text(h.get_text())
            if 15 < len(text) < 150:
                titles.append(text)
    return titles[:3]


def _is_hiring(soup: BeautifulSoup, html: str) -> bool:
    """Check if they're actively hiring."""
    hiring_signals = ["we're hiring", "join our team", "open positions",
                      "careers", "work with us", "job openings"]
    text_lower = soup.get_text().lower()
    return any(s in text_lower for s in hiring_signals)


async def scrape_company_website(url: str) -> dict:
    """
    Scrape a company homepage and return structured insights.

    Args:
        url: company website URL e.g. "https://sarvam.ai"

    Returns:
        dict with keys: title, meta_description, key_sentences,
                        tech_stack, blog_titles, is_hiring, error
    """
    result = {
        "url": url,
        "title": "",
        "meta_description": "",
        "key_sentences": "",
        "tech_stack": [],
        "blog_titles": [],
        "is_hiring": False,
        "error": None,
    }

    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            headers=HEADERS,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code >= 400:
                result["error"] = f"HTTP {resp.status_code}"
                return result
            html = resp.text

    except httpx.TimeoutException:
        result["error"] = "timeout"
        return result
    except Exception as e:
        result["error"] = str(e)[:100]
        return result

    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Title
    title_tag = soup.find("title")
    result["title"] = _clean_text(title_tag.get_text()) if title_tag else ""

    # Meta description
    meta = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
    if meta:
        result["meta_description"] = meta.get("content", "")[:300]

    # Key sentences from visible content
    result["key_sentences"] = _extract_key_sentences(soup)

    # Tech stack (scan original html before soup strips scripts)
    result["tech_stack"] = _detect_tech(html)

    # Blog / news titles
    result["blog_titles"] = _extract_blog_titles(soup)

    # Hiring check
    result["is_hiring"] = _is_hiring(soup, html)

    return result
"""
Discovery Tools
---------------
Three strategies in priority order:

  1. SerpAPI + LLM extraction  -- real Google results, Groq extracts company list from articles
  2. YC Directory API          -- free, no key, direct company data
  3. Mock data                 -- dev fallback

Key fix: SerpAPI returns articles ABOUT companies, not the companies themselves.
We use Groq to read those articles and extract the actual company names/websites.
"""

import httpx, re, json, asyncio
from typing import Optional
from app.core.config import get_settings

settings = get_settings()
SERPAPI_BASE = "https://serpapi.com/search"

SKIP_DOMAINS = [
    "wikipedia.org", "youtube.com", "twitter.com", "x.com",
    "linkedin.com", "reddit.com", "quora.com", "substack.com",
    "medium.com", "forbes.com",
]

def extract_domain(url: str) -> str:
    url = re.sub(r"https?://", "", url)
    url = re.sub(r"www\.", "", url)
    return url.split("/")[0].split("?")[0]


# ===========================================================================
# Groq extractor — reads article snippets and pulls out company list
# ===========================================================================

EXTRACT_SYSTEM = """
You are a data extractor. Given Google search result snippets about startups/companies,
extract the actual company names and websites mentioned.

Return ONLY valid JSON array — no markdown:
[
  {"company_name": "Jar", "website": "https://myjar.app", "description": "Micro-savings app"},
  {"company_name": "Sarvam AI", "website": "https://sarvam.ai", "description": "Indian language LLMs"}
]

Rules:
- Extract ONLY real companies/startups, NOT news sites, aggregators, or article titles
- Skip: TechCrunch, Inc42, LinkedIn, Wikipedia, Crunchbase, Forbes, topstartups.io etc.
- If you can't find a real website, omit the company
- Max 20 companies total
- Return [] if no real companies found
"""

async def extract_companies_with_groq(search_results: list[dict], original_query: str) -> list[dict]:
    """Use Groq to parse article snippets and extract actual company data."""
    if not settings.groq_api_key:
        return []

    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage

    # Build context from search results
    context_lines = []
    for r in search_results:
        context_lines.append(f"Title: {r.get('title','')}")
        context_lines.append(f"URL: {r.get('link','')}")
        context_lines.append(f"Snippet: {r.get('snippet','')}\n")
    context = "\n".join(context_lines)

    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0.1,
            max_tokens=2048,
        )
        response = await llm.ainvoke([
            SystemMessage(content=EXTRACT_SYSTEM),
            HumanMessage(content=f"Query was: {original_query}\n\nSearch results:\n{context}"),
        ])
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        companies = json.loads(raw.strip())
        print(f"  [Groq extract] Found {len(companies)} companies from search snippets")
        return companies
    except Exception as e:
        print(f"  [Groq extract] Error: {e}")
        return []


# ===========================================================================
# Strategy 1 — SerpAPI + Groq extraction
# ===========================================================================

async def discover_via_serpapi(
    queries: list[str], max_leads: int, original_query: str = ""
) -> tuple[list[dict], Optional[str]]:

    api_key = settings.serpapi_api_key
    if not api_key:
        return [], "SERPAPI_API_KEY not set"

    all_raw_results = []
    seen_urls = set()

    async with httpx.AsyncClient(timeout=20.0) as client:
        for query in queries[:3]:  # limit to 3 queries
            print(f"  [SerpAPI] {query}")
            try:
                resp = await client.get(SERPAPI_BASE, params={
                    "q": query, "api_key": api_key,
                    "num": 10, "engine": "google", "hl": "en", "gl": "us",
                })
                if resp.status_code == 401:
                    return [], "SerpAPI key invalid"
                data = resp.json()
                if "error" in data:
                    print(f"  [SerpAPI] {data['error']} — skipping")
                    continue
                for r in data.get("organic_results", []):
                    url = r.get("link","")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_raw_results.append(r)
            except Exception as e:
                print(f"  [SerpAPI] error: {e}")
                continue

    if not all_raw_results:
        return [], None

    print(f"  [SerpAPI] Got {len(all_raw_results)} raw results → extracting companies with Groq...")

    # Use Groq to extract actual companies from article snippets
    companies = await extract_companies_with_groq(all_raw_results, original_query)

    if not companies:
        return [], None

    leads = []
    seen_domains = set()
    for co in companies:
        name    = (co.get("company_name") or "").strip()
        website = (co.get("website") or "").strip()
        if not name or not website:
            continue
        domain = extract_domain(website)
        if domain in seen_domains or any(s in domain for s in SKIP_DOMAINS):
            continue
        seen_domains.add(domain)
        leads.append({
            "company_name": name,
            "website":      website,
            "description":  (co.get("description") or "")[:300],
            "source":       "serpapi",
            "country":      co.get("country"),
            "industry":     co.get("industry"),
            "founded_year": co.get("founded_year"),
            "batch":        co.get("batch"),
            "ceo_name":     co.get("ceo_name"),
            "ceo_email":    None,
            "personalization_hook": None,
        })
        if len(leads) >= max_leads:
            break

    return leads, None


# ===========================================================================
# Strategy 2 — YC Directory API (free, no key)
# ===========================================================================

YC_API = "https://api.ycombinator.com/v0.1/companies"

COUNTRY_ALIASES = {
    "india": "India", "usa": "United States of America",
    "us": "United States of America", "uk": "United Kingdom",
    "nigeria": "Nigeria", "brazil": "Brazil",
    "singapore": "Singapore", "canada": "Canada", "germany": "Germany",
}

def _parse_hints(query: str) -> dict:
    q = query.lower()
    country = None
    for kw, full in COUNTRY_ALIASES.items():
        if kw in q:
            country = full
            break
    year_m  = re.search(r"\b(20\d\d)\b", q)
    batch_m = re.search(r"\b([wsf][12]\d)\b", q, re.IGNORECASE)
    # Extract industry keyword
    industry_kws = ["fintech","healthtech","edtech","saas","ai","devtools","hrtech",
                    "ecommerce","logistics","climate","crypto","blockchain"]
    industry = next((kw for kw in industry_kws if kw in q), None)
    return {
        "country":  country,
        "min_year": int(year_m.group(1)) if year_m else None,
        "batch":    batch_m.group(1).upper() if batch_m else None,
        "industry": industry,
    }

async def discover_via_yc(query: str, max_leads: int) -> list[dict]:
    hints = _parse_hints(query)
    print(f"  [YC] hints → country={hints['country']} year>={hints['min_year']} industry={hints['industry']}")

    headers = {"User-Agent": "OutreachX/1.0", "Accept": "application/json"}
    companies = []
    seen_ids  = set()

    # Build search params — use industry keyword if present
    search_term = hints["industry"] or (hints["country"] or "")
    fetch_params = [
        {"q": search_term, "per_page": 100, "page": 1},
        {"q": hints["country"] or "india", "per_page": 100, "page": 2},
    ]
    if hints["batch"]:
        fetch_params.append({"batch": hints["batch"], "per_page": 100})

    async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
        for params in fetch_params:
            try:
                resp = await client.get(YC_API, params=params)
                if resp.status_code != 200:
                    continue
                for co in resp.json().get("companies", []):
                    cid = co.get("id")
                    if cid and cid not in seen_ids:
                        seen_ids.add(cid)
                        companies.append(co)
            except Exception as e:
                print(f"  [YC] error: {e}")

    print(f"  [YC] fetched {len(companies)} total companies")
    if not companies:
        return []

    # Show sample country values for debugging
    sample = list({c.get("country","") for c in companies[:30] if c.get("country")})
    print(f"  [YC] sample countries: {sample[:6]}")

    leads, seen_domains = [], set()
    for co in companies:
        if hints["country"]:
            if (co.get("country") or "").strip().lower() != hints["country"].lower():
                continue
        if hints["min_year"]:
            try:
                if int(co.get("year_founded") or 0) < hints["min_year"]:
                    continue
            except: pass
        if hints["industry"]:
            co_industry = (co.get("industry") or "").lower()
            co_tags = " ".join(co.get("tags") or []).lower()
            if hints["industry"] not in co_industry and hints["industry"] not in co_tags:
                # Loose match — don't skip if we have country filter
                if not hints["country"]:
                    continue

        name    = (co.get("name") or "").strip()
        website = (co.get("website") or "").strip()
        if not name: continue
        domain = extract_domain(website) if website else name.lower().replace(" ","")
        if domain in seen_domains: continue
        seen_domains.add(domain)

        leads.append({
            "company_name": name,
            "website":      website or f"https://{domain}",
            "description":  (co.get("one_liner") or "")[:300],
            "country":      co.get("country"),
            "industry":     co.get("industry"),
            "founded_year": co.get("year_founded"),
            "batch":        co.get("batch"),
            "source":       "yc_directory",
            "ceo_name":     None, "ceo_email": None,
            "personalization_hook": None,
        })
        if len(leads) >= max_leads:
            break

    print(f"  [YC] {len(leads)} leads after filtering")
    return leads


# ===========================================================================
# Strategy 3 — Rich mock data
# ===========================================================================

MOCK_LEADS = [
    {"company_name":"Jar",           "website":"https://myjar.app",        "description":"Micro-savings & gold investment app. 10M+ downloads.",              "country":"India","industry":"Fintech",      "batch":"YC W22","founded_year":2021,"source":"mock","ceo_name":"Nishchay AG",             "ceo_email":None,"cto_name":"Misbah Ashraf"},
    {"company_name":"Kairon Labs",   "website":"https://kaironlabs.com",   "description":"No-code chatbot & NLP for enterprises. HDFC, Kotak clients.",       "country":"India","industry":"B2B SaaS",     "batch":"YC S22","founded_year":2020,"source":"mock","ceo_name":"Saurabh Gupta",          "ceo_email":None,"cto_name":"Nimesh Shah"},
    {"company_name":"Sarvam AI",     "website":"https://sarvam.ai",        "description":"Full-stack AI for India — LLMs for Indian languages.",               "country":"India","industry":"AI / LLM",     "batch":"YC W23","founded_year":2023,"source":"mock","ceo_name":"Vivek Raghavan",         "ceo_email":None,"cto_name":"Pratyush Kumar"},
    {"company_name":"Reelo",         "website":"https://reelo.io",         "description":"Customer loyalty SaaS for restaurants and retail. $1.5M ARR.",       "country":"India","industry":"Retail Tech",  "batch":"YC S21","founded_year":2020,"source":"mock","ceo_name":"Priya Agarwal",          "ceo_email":None,"cto_name":"Rohan Shah"},
    {"company_name":"Ultrahuman",    "website":"https://ultrahuman.com",   "description":"Metabolic health wearable (Ring AIR). Raised $35M Series B.",        "country":"India","industry":"Health Tech",  "batch":"YC S21","founded_year":2019,"source":"mock","ceo_name":"Mohit Kumar",            "ceo_email":None,"cto_name":"Bhuwan Bhatia"},
    {"company_name":"Murf AI",       "website":"https://murf.ai",          "description":"AI voice generator, 120+ voices, 20 languages. 2M+ users.",          "country":"India","industry":"AI / Voice",   "batch":"YC S21","founded_year":2020,"source":"mock","ceo_name":"Ankur Edkie",            "ceo_email":None,"cto_name":"Divyanshu Pandey"},
    {"company_name":"Leena AI",      "website":"https://leena.ai",         "description":"Autonomous HR AI agent. Deployed at Nestle, Puma, AstraZeneca.",     "country":"India","industry":"HR Tech",      "batch":"YC W20","founded_year":2018,"source":"mock","ceo_name":"Adit Jain",              "ceo_email":None,"cto_name":"Mayank Goyal"},
    {"company_name":"Zluri",         "website":"https://zluri.com",        "description":"SaaS management — shadow IT, licenses, access. $20M Series B.",      "country":"India","industry":"IT Mgmt",      "batch":"YC W21","founded_year":2020,"source":"mock","ceo_name":"Sethu Meenakshisundaram","ceo_email":None,"cto_name":"Ritish Reddy"},
    {"company_name":"Requestly",     "website":"https://requestly.com",    "description":"API mocking for devs. 200K+ users, Atlassian, Gojek.",               "country":"India","industry":"Dev Tools",    "batch":"YC S22","founded_year":2021,"source":"mock","ceo_name":"Sachin Jain",            "ceo_email":None,"cto_name":"Ankit Mehta"},
    {"company_name":"SuperAGI",      "website":"https://superagi.com",     "description":"Open-source autonomous AI agent framework. 15K GitHub stars.",       "country":"India","industry":"AI Infra",     "batch":"YC S23","founded_year":2023,"source":"mock","ceo_name":"Ishaan Bhola",           "ceo_email":None,"cto_name":"Mudrik Rana"},
    {"company_name":"Hasura",        "website":"https://hasura.io",        "description":"Instant GraphQL/REST APIs on your DB. 30K stars, $100M raised.",     "country":"India","industry":"Dev Infra",    "batch":"YC S18","founded_year":2018,"source":"mock","ceo_name":"Tanmai Gopal",           "ceo_email":None,"cto_name":"Rajoshi Ghosh"},
    {"company_name":"Chargebee",     "website":"https://chargebee.com",    "description":"Subscription billing for SaaS. Unicorn, 6500+ customers.",           "country":"India","industry":"Fintech",      "batch":None,    "founded_year":2011,"source":"mock","ceo_name":"Krish Subramanian",      "ceo_email":None,"cto_name":"Thiyagarajan T"},
    {"company_name":"BrowserStack",  "website":"https://browserstack.com", "description":"Cloud testing on 3000+ real devices. $200M+ ARR.",                  "country":"India","industry":"Dev QA",       "batch":None,    "founded_year":2011,"source":"mock","ceo_name":"Ritesh Arora",           "ceo_email":None,"cto_name":"Nakul Aggarwal"},
    {"company_name":"Postman",       "website":"https://postman.com",      "description":"API platform for 25M+ developers.",                                  "country":"India","industry":"Dev Tools",    "batch":None,    "founded_year":2014,"source":"mock","ceo_name":"Abhinav Asthana",        "ceo_email":None,"cto_name":"Abhijit Kane"},
    {"company_name":"Omnivore",      "website":"https://omnivore.app",     "description":"Open-source read-it-later + AI summarization.",                      "country":"India","industry":"Productivity", "batch":"YC W22","founded_year":2022,"source":"mock","ceo_name":"Jackson Harper",         "ceo_email":None,"cto_name":None},
]


# ===========================================================================
# Main entry point
# ===========================================================================

async def run_discovery(
    search_queries: list[str],
    max_leads: int = 20,
    original_query: str = "",
) -> list[dict]:
    # Strategy 1: SerpAPI + Groq extraction
    if settings.serpapi_api_key:
        print("[Discovery] Strategy 1: SerpAPI + Groq company extraction")
        leads, err = await discover_via_serpapi(search_queries, max_leads, original_query)
        if err:
            print(f"[Discovery] SerpAPI error: {err}")
        elif leads:
            print(f"[Discovery] SerpAPI → {len(leads)} real companies ✓")
            return leads
        else:
            print("[Discovery] SerpAPI extracted 0 companies → trying YC API")

    # Strategy 2: YC Directory
    print("[Discovery] Strategy 2: YC directory API")
    hint = original_query or (search_queries[0] if search_queries else "India")
    leads = await discover_via_yc(hint, max_leads)
    if leads:
        print(f"[Discovery] YC API → {len(leads)} leads ✓")
        return leads

    # Strategy 3: Mock
    print("[Discovery] Strategy 3: mock data (add API keys for real data)")
    return MOCK_LEADS[:max_leads]
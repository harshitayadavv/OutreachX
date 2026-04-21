"""
Direct Input Node
-----------------
Handles: "email Razorpay, Groww, Sarvam AI"
Creates Lead stubs from company names, then researcher scrapes each.
"""

import re
from app.agents.state import AgentState, Lead


def _guess_website(company_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]", "", company_name.lower())
    return f"https://{slug}.com"


# Well-known companies — pre-filled so scraper doesn't need to guess
KNOWN_COMPANIES: dict[str, dict] = {
    "razorpay":    {"website": "https://razorpay.com",   "country": "India", "industry": "Fintech"},
    "groww":       {"website": "https://groww.in",       "country": "India", "industry": "Fintech"},
    "sarvam ai":   {"website": "https://sarvam.ai",      "country": "India", "industry": "AI / LLM"},
    "sarvam":      {"website": "https://sarvam.ai",      "country": "India", "industry": "AI / LLM"},
    "kairon labs": {"website": "https://kaironlabs.com", "country": "India", "industry": "B2B SaaS"},
    "kairon":      {"website": "https://kaironlabs.com", "country": "India", "industry": "B2B SaaS"},
    "ultrahuman":  {"website": "https://ultrahuman.com", "country": "India", "industry": "Health Tech"},
    "jar":         {"website": "https://myjar.app",      "country": "India", "industry": "Fintech"},
    "leena ai":    {"website": "https://leena.ai",       "country": "India", "industry": "HR Tech"},
    "leena":       {"website": "https://leena.ai",       "country": "India", "industry": "HR Tech"},
    "zluri":       {"website": "https://zluri.com",      "country": "India", "industry": "IT Mgmt"},
    "murf ai":     {"website": "https://murf.ai",        "country": "India", "industry": "AI / Voice"},
    "murf":        {"website": "https://murf.ai",        "country": "India", "industry": "AI / Voice"},
    "hasura":      {"website": "https://hasura.io",      "country": "India", "industry": "Dev Infra"},
    "chargebee":   {"website": "https://chargebee.com",  "country": "India", "industry": "Fintech"},
    "postman":     {"website": "https://postman.com",    "country": "India", "industry": "Dev Tools"},
    "browserstack":{"website": "https://browserstack.com","country":"India", "industry": "Dev QA"},
    "freshworks":  {"website": "https://freshworks.com", "country": "India", "industry": "CRM"},
    "zepto":       {"website": "https://zepto.app",      "country": "India", "industry": "Quick Commerce"},
    "meesho":      {"website": "https://meesho.com",     "country": "India", "industry": "E-commerce"},
    "cred":        {"website": "https://cred.club",      "country": "India", "industry": "Fintech"},
    "slice":       {"website": "https://sliceit.com",    "country": "India", "industry": "Fintech"},
}


async def direct_input_node(state: AgentState) -> dict:
    """
    Reads:  state["direct_companies"] (set by planner)
            Falls back to re-parsing state["query"] if direct_companies missing.
    Writes: state["leads"]
    """
    companies = state.get("direct_companies") or []
    errors    = state.get("errors", [])

    # Fallback: re-parse from query in case state merge dropped direct_companies
    if not companies and state.get("query"):
        from app.agents.nodes.planner import _parse_direct_companies
        companies = _parse_direct_companies(state["query"])
        if companies:
            print(f"[DirectInput] Re-parsed companies from query: {companies}")

    if not companies:
        return {
            "leads": [],
            "current_step": "No companies provided",
            "errors": errors + ["direct_input_node: no companies found"],
        }

    print(f"[DirectInput] Building leads for: {companies}")

    leads: list[Lead] = []
    for raw_name in companies:
        name = raw_name.strip().rstrip(".")
        if not name:
            continue

        # Check if user provided URL inline: "Razorpay (razorpay.com)"
        url_match = re.search(r"\(?(https?://[^\s)]+|[\w-]+\.[a-z]{2,})\)?", name)
        if url_match:
            url  = url_match.group(1)
            name = name[:url_match.start()].strip()
            if not url.startswith("http"):
                url = f"https://{url}"
        else:
            # Check known companies first
            known = KNOWN_COMPANIES.get(name.lower())
            url   = known["website"] if known else _guess_website(name)

        known = KNOWN_COMPANIES.get(name.lower(), {})

        lead: Lead = {
            "company_name": name,
            "website":      url,
            "description":  "",
            "source":       "direct_input",
            "country":      known.get("country"),
            "industry":     known.get("industry"),
            "founded_year": None,
            "batch":        None,
            "ceo_name":     None,
            "ceo_email":    None,
            "personalization_hook": None,
        }
        leads.append(lead)
        print(f"  → {name} ({url})")

    print(f"[DirectInput] Created {len(leads)} lead stubs → passing to researcher")

    return {
        "leads":        leads,
        "researched_leads": [],   # reset so researcher processes fresh
        "enriched_leads":   [],   # reset so contact_finder processes fresh
        "current_step": f"Targeting {len(leads)} companies directly — researching...",
        "errors":       errors,
    }
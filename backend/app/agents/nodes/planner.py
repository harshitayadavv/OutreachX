"""
Planner Node
------------
Parses the user query and decides:
  A) Run AI discovery  (query given)
  B) Skip to email gen (file uploaded)

Also extracts:
  - target_role: who to email (ceo/cto/hr/engineering)
  - structured search queries for SerpAPI
"""

import json, re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.core.config import get_settings

settings = get_settings()

import re as _re

# ── Direct company targeting ──────────────────────────────────────────────────
# Detects queries like: "email Razorpay, Groww, Sarvam AI"
# Returns list of company names, or [] if not a direct-target query

DIRECT_TARGET_PREFIXES = [
    "email ", "email to ", "reach out to ", "contact ", "outreach to ",
    "send to ", "target ", "email these ", "reach "
]

def _parse_direct_companies(query: str) -> list[str]:
    """
    If the query is a list of company names, return them.
    E.g. "email Razorpay, Groww, Sarvam AI" → ["Razorpay", "Groww", "Sarvam AI"]
    Returns [] if not a direct-company query.
    """
    q = query.strip()
    q_lower = q.lower()

    # Check if starts with a direct-target prefix
    matched_prefix = None
    for prefix in DIRECT_TARGET_PREFIXES:
        if q_lower.startswith(prefix):
            matched_prefix = prefix
            break

    if not matched_prefix:
        # Also detect: comma-separated names with no verb
        # "Razorpay, Groww, Sarvam AI" — at least 2 items, no common query words
        query_words = set(q_lower.split())
        discovery_words = {"startups","companies","fintech","india","yc","ycombinator",
                           "after","founded","batch","series","saas","ai","tech"}
        if "," in q and not query_words.intersection(discovery_words):
            # Looks like a plain comma-separated list
            names = [n.strip() for n in q.split(",") if n.strip()]
            if len(names) >= 2:
                return names
        return []

    # Strip prefix and split by comma/and
    remainder = q[len(matched_prefix):].strip()
    # Split on comma or " and "
    parts = _re.split(r",| and ", remainder, flags=_re.IGNORECASE)
    names = [p.strip().rstrip(".") for p in parts if p.strip()]
    return names if len(names) >= 1 else []



ROLE_KEYWORDS = {
    "cto":         ["cto","chief technology","tech lead","engineering head","vp engineering"],
    "hr":          ["hr","human resources","recruiter","talent","people","hiring manager"],
    "engineering": ["engineering manager","em ","lead engineer","senior engineer"],
    "ceo":         ["ceo","founder","coo","president","decision maker"],
}

def _detect_role(query: str) -> str:
    q = query.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return role
    return "ceo"  # default


def _fallback_plan(query: str) -> dict:
    q = query.lower()
    country = "global"
    for kw in ["india","usa","uk","nigeria","brazil","singapore","canada","germany"]:
        if kw in q:
            country = kw.title(); break
    year_m   = re.search(r"\b(20\d\d)\b", q)
    year     = int(year_m.group(1)) if year_m else None
    industry = "technology"
    for kw in ["fintech","healthtech","edtech","saas","ai","devtools","hrtech"]:
        if kw in q: industry = kw; break
    year_str = f"{year} {year+1}" if year else "2021 2022 2023"
    return {
        "interpreted_query": query,
        "target_country":    country,
        "target_industry":   industry,
        "company_stage":     "early-stage",
        "accelerator_batch": None,
        "founding_year_min": year,
        "target_roles":      [_detect_role(query)],
        "search_queries": [
            f"site:ycombinator.com/companies {country.lower()} {year_str}",
            f"Y Combinator {country} {industry} startups {year_str} list",
            f"YC {country} {industry} founders crunchbase",
        ],
        "max_leads": 20,
    }


PLANNER_SYSTEM = """
You are the Planner for OutreachX, a B2B cold outreach system.
Analyse the user query and return ONLY valid JSON:
{
  "interpreted_query": "<clean summary>",
  "target_country": "<country or global>",
  "target_industry": "<industry>",
  "company_stage": "<early-stage|growth|any>",
  "accelerator_batch": "<e.g. YC S22 or null>",
  "founding_year_min": <int or null>,
  "target_roles": ["<ceo|cto|hr|engineering>"],
  "search_queries": [
    "<specific Google search 1>",
    "<specific Google search 2>",
    "<specific Google search 3>"
  ],
  "max_leads": 20
}

target_roles rules:
- Default is ["ceo"] unless the query mentions a specific role
- If query says "email HR" or "reach recruiters" → ["hr"]
- If query says "CTO" or "tech lead" → ["cto"]
- If query says "CEO and HR" → ["ceo","hr"]
- Never include duplicates

search_queries rules:
- Use site:ycombinator.com NOT site:yc.com
- Mix: YC directory + news articles + crunchbase
"""


async def planner_node(state: AgentState) -> dict:
    print("[Planner] Starting...")

    if state.get("uploaded_file_path"):
        print("[Planner] Uploaded file detected → skipping discovery")
        # Still detect target_role from any query hint
        target_role = state.get("target_role") or _detect_role(state.get("query",""))
        return {
            "entry_mode":  "uploaded_db",
            "target_role": target_role,
            "current_step": "File uploaded — parsing leads...",
            "errors":       state.get("errors", []),
        }

    query = state.get("query","").strip()
    if not query:
        return {
            "entry_mode": "discovery",
            "target_role": "ceo",
            "current_step": "Error: no query provided",
            "errors": state.get("errors",[]) + ["No query or file provided"],
        }

    print(f"[Planner] Query: {query}")

    # ── Check for direct company targeting ────────────────────────────────────
    direct_companies = _parse_direct_companies(query)
    if direct_companies:
        print(f"[Planner] Direct company input detected: {direct_companies}")
        detected_role = _detect_role(query)
        memory = state.get("memory", {})
        memory.setdefault("past_queries", [])
        if query not in memory["past_queries"]:
            memory["past_queries"].append(query)
        return {
            "entry_mode":       "direct",
            "target_role":      detected_role,
            "direct_companies": direct_companies,
            "current_step":     f"Targeting {len(direct_companies)} companies directly...",
            "memory":           memory,
            "errors":           state.get("errors", []),
        }

    # Detect target role from query before calling LLM
    detected_role = _detect_role(query)

    plan = None
    if settings.groq_api_key:
        try:
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                api_key=settings.groq_api_key,
                temperature=0.1, max_tokens=1024,
            )
            response = await llm.ainvoke([
                SystemMessage(content=PLANNER_SYSTEM),
                HumanMessage(content=f"User query: {query}"),
            ])
            raw = response.content.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            plan = json.loads(raw.strip())
            roles = plan.get("target_roles", [detected_role])
            print(f"[Planner] Groq plan: {len(plan.get('search_queries',[]))} queries | roles={roles}")
        except Exception as e:
            print(f"[Planner] Groq error: {e} — fallback plan")

    if not plan:
        plan = _fallback_plan(query)

    # Primary target role (first in list)
    target_roles = plan.get("target_roles", [detected_role])
    target_role  = target_roles[0] if target_roles else "ceo"

    memory = state.get("memory", {})
    memory["current_plan"] = plan
    memory.setdefault("past_queries", [])
    if query not in memory["past_queries"]:
        memory["past_queries"].append(query)

    return {
        "entry_mode":   "discovery",
        "target_role":  target_role,
        "current_step": f"Plan ready — discovering up to {plan.get('max_leads',20)} {target_role.upper()} contacts...",
        "memory":       memory,
        "errors":       state.get("errors",[]),
    }
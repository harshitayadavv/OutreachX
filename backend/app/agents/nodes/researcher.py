"""
Research Agent Node
-------------------
For each lead:
  1. Scrapes their website
  2. Extracts CEO name if unknown (from About/Team page text)
  3. Uses Groq to generate personalization hook + pain points
Runs MAX_CONCURRENT leads in parallel for speed.
"""

import asyncio, json, re
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState, Lead
from app.agents.tools.scraper_tool import scrape_company_website
from app.core.config import get_settings

settings = get_settings()
MAX_CONCURRENT = 5


def get_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.4,
        max_tokens=512,
    )


RESEARCH_SYSTEM = """
You are a B2B sales research analyst. Given scraped website data, return ONLY valid JSON:
{
  "summary": "<2 sentence company summary, specific and factual>",
  "ceo_name": "<CEO or founder full name if found in the text, else null>",
  "personalization_hook": "<1 sharp sentence referencing their product, growth, clients, or tech — must be specific to THIS company>",
  "pain_points": ["<likely business challenge 1>", "<challenge 2>"],
  "growth_signals": ["<signal of momentum>"]
}
Rules:
- personalization_hook must NOT be generic ("they are growing fast" is bad)
- Reference real details: client names, funding, tech stack, product features
- ceo_name: look for "Founder", "CEO", "Co-founder" mentions in the text
- Keep everything under 150 words total
"""


def _try_extract_ceo_name(text: str) -> Optional[str]:
    """Best-effort CEO/founder name extraction from page text."""
    patterns = [
        r"(?:Founder|CEO|Co-Founder|MD|Managing Director)[,\s&]+([A-Z][a-z]+ [A-Z][a-z]+)",
        r"([A-Z][a-z]+ [A-Z][a-z]+)[,\s]+(?:Founder|CEO|Co-Founder)",
        r"founded by ([A-Z][a-z]+ [A-Z][a-z]+)",
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return None


async def research_single_lead(lead: Lead, llm: Optional[ChatGroq]) -> Lead:
    lead = dict(lead)
    url  = lead.get("website", "")
    name = lead.get("company_name", "unknown")

    if not url:
        lead.setdefault("personalization_hook", f"{name} is building in an interesting space.")
        return lead

    print(f"  [Research] {name} → {url}")
    scraped = await scrape_company_website(url)

    if scraped.get("error"):
        print(f"  [Research] {name}: {scraped['error']}")
        lead.setdefault("personalization_hook",
            lead.get("description","")[:120] or f"{name} is building in this space.")
        return lead

    # Try extracting CEO name from page if not already set
    if not lead.get("ceo_name"):
        page_text = (
            scraped.get("title","") + " " +
            scraped.get("meta_description","") + " " +
            scraped.get("key_sentences","")
        )
        extracted_ceo = _try_extract_ceo_name(page_text)
        if extracted_ceo:
            lead["ceo_name"] = extracted_ceo
            print(f"  [Research] {name}: extracted CEO → {extracted_ceo}")

    lead["tech_stack"] = scraped.get("tech_stack", [])

    if not llm:
        lead.setdefault("personalization_hook",
            scraped.get("meta_description","")[:120] or
            lead.get("description","")[:120] or
            f"{name} is doing interesting work.")
        return lead

    context = f"""
Company: {name}
Page title: {scraped.get('title','')}
Meta description: {scraped.get('meta_description','')}
Key content: {scraped.get('key_sentences','')}
Tech stack: {', '.join(scraped.get('tech_stack',[]))}
Blog/news: {'; '.join(scraped.get('blog_titles',[]))}
Is hiring: {scraped.get('is_hiring', False)}
Existing description: {lead.get('description','')}
"""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=RESEARCH_SYSTEM),
            HumanMessage(content=context),
        ])
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        insights = json.loads(raw.strip())

        lead["description"]          = insights.get("summary") or lead.get("description","")
        lead["personalization_hook"] = insights.get("personalization_hook","")
        lead["pain_points"]          = insights.get("pain_points",[])

        # Only override ceo_name if LLM found one and we don't have one
        if not lead.get("ceo_name") and insights.get("ceo_name"):
            lead["ceo_name"] = insights["ceo_name"]
            print(f"  [Research] {name}: Groq found CEO → {lead['ceo_name']}")

    except Exception as e:
        print(f"  [Research] {name}: LLM error — {e}")
        lead.setdefault("personalization_hook",
            scraped.get("meta_description","")[:120] or lead.get("description","")[:120])

    return lead


async def researcher_node(state: AgentState) -> dict:
    leads  = state.get("leads", [])
    errors = state.get("errors", [])

    if not leads:
        return {"researched_leads": [], "current_step": "No leads to research", "errors": errors}

    # Uploaded DB leads with emails — skip scraping, just pass through
    if state.get("entry_mode") == "uploaded_db":
        has_emails = any(l.get("ceo_email") for l in leads)
        if has_emails:
            print("[Research] Uploaded DB with contacts — skipping website scraping")
            return {
                "researched_leads": leads,
                "current_step": f"Using {len(leads)} pre-enriched leads — generating emails...",
                "errors": errors,
            }

    print(f"[Research] Researching {len(leads)} companies...")
    llm = get_llm() if settings.groq_api_key else None

    researched = []
    for i in range(0, len(leads), MAX_CONCURRENT):
        batch   = leads[i : i + MAX_CONCURRENT]
        tasks   = [research_single_lead(dict(l), llm) for l in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for lead, res in zip(batch, results):
            if isinstance(res, Exception):
                print(f"  [Research] Exception {lead.get('company_name')}: {res}")
                lead["personalization_hook"] = lead.get("description","")[:100]
                researched.append(lead)
            else:
                researched.append(res)

    print(f"[Research] Done — {len(researched)} leads enriched")
    return {
        "researched_leads": researched,
        "current_step": f"Researched {len(researched)} companies — finding contacts...",
        "errors": errors,
    }
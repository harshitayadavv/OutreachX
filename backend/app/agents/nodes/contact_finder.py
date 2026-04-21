"""
Contact Finder Node
-------------------
Finds emails + LinkedIn profiles for the TARGET ROLE specified in the campaign.

target_role options:
  "ceo"         → CEO, Founder, MD, Co-founder
  "cto"         → CTO, VP Engineering, Head of Engineering
  "hr"          → HR, People, Talent, Recruiter
  "engineering" → Engineering Manager, Lead Engineer

If target_role is a list (e.g. ["ceo","hr"]) — finds both and stores separately.
If Hunter finds multiple HR contacts, picks top N (max_hr_contacts).
"""

import asyncio
from app.agents.state import AgentState, Lead
from app.agents.tools.hunter_tool import find_contact_email
from app.core.config import get_settings

settings = get_settings()
MAX_CONCURRENT  = 5
MAX_HR_CONTACTS = 3  # max HR emails per company when role="hr"


def _parse_target_roles(target_role_str: str) -> list[str]:
    """Parse "ceo,cto" or "hr" or ["ceo","hr"] into a list of roles."""
    if not target_role_str:
        return ["ceo"]
    if isinstance(target_role_str, list):
        return [r.strip().lower() for r in target_role_str]
    return [r.strip().lower() for r in target_role_str.split(",")]


async def enrich_lead_contacts(lead: Lead, target_roles: list[str]) -> Lead:
    lead    = dict(lead)
    website = lead.get("website","")
    name    = lead.get("company_name","?")

    if not website:
        return lead

    print(f"  [Contacts] {name} — targeting: {', '.join(target_roles)}")

    for role in target_roles:
        # Pick the right existing name field
        if role == "ceo":
            known_name = lead.get("ceo_name")
        elif role == "cto":
            known_name = lead.get("cto_name")
        elif role == "hr":
            known_name = lead.get("hr_name")
        else:
            known_name = lead.get("ceo_name")  # fallback

        # Skip if we already have this email
        email_field = f"{role}_email" if role in ("ceo","cto","hr") else "ceo_email"
        if lead.get(email_field):
            continue

        result = await find_contact_email(
            website, known_name, role=role, company_name=name
        )

        # Always store LinkedIn (even if email is a pattern guess)
        linkedin = result.get("linkedin","")

        if role == "ceo":
            if result.get("email"): lead["ceo_email"] = result["email"]
            lead["ceo_linkedin"]         = linkedin
            lead["ceo_email_source"]     = result.get("source","")
            lead["ceo_email_confidence"] = result.get("confidence",0)
            if result.get("name") and not lead.get("ceo_name"):
                lead["ceo_name"] = result["name"]

        elif role == "cto":
            if result.get("email"): lead["cto_email"] = result["email"]
            lead["cto_linkedin"]     = linkedin
            lead["cto_email_source"] = result.get("source","")
            if result.get("name") and not lead.get("cto_name"):
                lead["cto_name"] = result["name"]

        elif role == "hr":
            if result.get("email"): lead["hr_email"] = result["email"]
            lead["hr_linkedin"]     = linkedin
            lead["hr_email_source"] = result.get("source","")
            if result.get("name") and not lead.get("hr_name"):
                lead["hr_name"] = result["name"]

        else:
            if result.get("email"): lead["ceo_email"] = result["email"]
            lead["ceo_linkedin"] = linkedin

    return lead


async def contact_finder_node(state: AgentState) -> dict:
    """
    Reads:  state["researched_leads"], state["target_role"]
    Writes: state["enriched_leads"], state["current_step"]
    """
    leads       = state.get("researched_leads") or state.get("leads", [])
    errors      = state.get("errors", [])
    target_role = state.get("target_role", "ceo")  # from campaign config
    target_roles = _parse_target_roles(target_role)

    if not leads:
        return {"enriched_leads": [], "current_step": "No leads to enrich", "errors": errors}

    print(f"[Contacts] Finding {', '.join(target_roles).upper()} contacts for {len(leads)} leads...")

    # Skip already-enriched leads from uploaded DB
    needs   = [l for l in leads if not _already_enriched(l, target_roles)]
    already = [l for l in leads if _already_enriched(l, target_roles)]
    enriched = list(already)

    for i in range(0, len(needs), MAX_CONCURRENT):
        batch   = needs[i : i + MAX_CONCURRENT]
        tasks   = [enrich_lead_contacts(lead, target_roles) for lead in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for lead, res in zip(batch, results):
            if isinstance(res, Exception):
                print(f"  [Contacts] Error {lead.get('company_name')}: {res}")
                enriched.append(lead)
            else:
                enriched.append(res)

    # Count how many have the primary target email
    primary_role  = target_roles[0]
    email_field   = f"{primary_role}_email" if primary_role in ("ceo","cto","hr") else "ceo_email"
    found         = sum(1 for l in enriched if l.get(email_field) or l.get("ceo_email"))
    linkedin_found = sum(1 for l in enriched if l.get("ceo_linkedin") or l.get("cto_linkedin") or l.get("hr_linkedin"))

    print(f"[Contacts] Done — {found}/{len(enriched)} emails | {linkedin_found} LinkedIn profiles")

    return {
        "enriched_leads": enriched,
        "current_step":   f"Found {found}/{len(enriched)} contacts ({', '.join(target_roles)}) — generating emails...",
        "errors":         errors,
    }


def _already_enriched(lead: dict, target_roles: list[str]) -> bool:
    """Check if lead already has all target emails (e.g. from uploaded DB)."""
    for role in target_roles:
        field = f"{role}_email" if role in ("ceo","cto","hr") else "ceo_email"
        if not lead.get(field):
            return False
    return True
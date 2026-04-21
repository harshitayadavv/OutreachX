"""
Email Generator Node
--------------------
Generates personalized cold emails using Groq (Llama 3.3 70B).

Two modes:
  - With resume/profile: email is written as the user (from their background)
  - Without resume: generic sender with value prop

CEO name fix: if ceo_name is missing, researcher tries to find it.
If still missing, we use a professional no-name opener.
"""

import json, asyncio
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState, GeneratedEmail
from app.core.config import get_settings

settings = get_settings()
MAX_CONCURRENT = 5


EMAIL_SYSTEM = """
You are an expert B2B cold email copywriter. Write a short, highly personalized cold email.
Return ONLY valid JSON — no markdown, no extra text:
{
  "subject": "<see rules below>",
  "body": "<email body, plain text, \\n for line breaks>"
}

SUBJECT LINE RULES — this is the most important part:
- Must create genuine curiosity or relevance — make them WANT to open it
- Reference something SPECIFIC about the company (milestone, product, market, funding, client win)
- Keep it under 8 words
- Sound human, like a colleague sent it
- BANNED subjects: anything with "Tech Stack", "Quick Question", "Touching Base", "Partnership", "Opportunity", "Hello", "Hi there", "Introduction"
- GOOD examples:
    "Razorpay crossed $100B in payments — congrats"
    "Noticed Groww hit 50M investors"
    "Question about Sarvam's Hindi LLM approach"
    "Saw Hiration's resume AI — had a thought"
    "How Karbon Card is solving SMB credit"

BODY RULES (MAX 110 words):
- If CEO name known: open with their first name ("Hi Harshil,")
- If CEO name unknown: open with "Hi," (NOT "There," or "Hello there,")
- Line 1: ONE specific insight about this company — reference their product, a real metric, a client, a recent launch, or their market position. This must feel researched, not generic.
- Line 2: One concrete connection between their world and what the sender offers. Be specific about HOW it helps THEM.
- Line 3: "Would a 15-min call next week make sense?"
- Sign off: "Best,\\n[sender name]"
- NEVER say: "I hope this finds you well", "I came across your company", "revolutionary", "synergy", "leverage", "game-changer"
- Sound like a smart person who did their homework, not a sales bot
"""


def _build_prompt(lead: dict, sender_name: str, sender_background: str, sender_value_prop: str) -> str:
    # Get whichever role contact was found
    contact_name  = (lead.get("ceo_name") or lead.get("cto_name") or
                     lead.get("hr_name") or "")
    contact_email = (lead.get("ceo_email") or lead.get("cto_email") or
                     lead.get("hr_email") or "")
    contact_role  = ("CEO" if lead.get("ceo_email") else
                     "CTO" if lead.get("cto_email") else
                     "HR Manager" if lead.get("hr_email") else "decision maker")
    contact_first = contact_name.split()[0] if contact_name else ""
    hook  = lead.get("personalization_hook","") or lead.get("description","")[:150]
    tech  = ", ".join((lead.get("tech_stack") or [])[:4])

    sender_section = (
        f"Sender name       : {sender_name}\n"
        f"Sender background : {sender_background}\n"
        f"What sender offers: {sender_value_prop}"
    ) if sender_background else (
        f"Sender name : {sender_name}\nWe offer    : {sender_value_prop}"
    )

    return f"""Write a cold email for this lead:

Company     : {lead.get('company_name')}
Industry    : {lead.get('industry') or 'technology'}
Batch       : {lead.get('batch') or 'funded startup'}
Founded     : {lead.get('founded_year') or 'unknown'}
Description : {lead.get('description','')}
Hook        : {hook}
Tech stack  : {tech or 'not detected'}

Recipient role  : {contact_role}
Recipient name  : {contact_name or 'UNKNOWN — open with "Hi,"'}
Recipient first : {contact_first or 'UNKNOWN'}
Recipient email : {contact_email}

{sender_section}

IMPORTANT: If recipient name is UNKNOWN, open body with "Hi," — NEVER "There,"
"""


async def generate_single_email(
    lead: dict, llm: ChatGroq,
    sender_name: str, sender_background: str, sender_value_prop: str
) -> GeneratedEmail:
    company  = lead.get("company_name","?")
    # Use whichever role contact was found
    to_email = (lead.get("ceo_email") or lead.get("cto_email") or
                lead.get("hr_email") or lead.get("engineering_email") or "")
    to_name  = (lead.get("ceo_name") or lead.get("cto_name") or
                lead.get("hr_name") or "")

    base: GeneratedEmail = {
        "lead_company": company, "to_name": to_name, "to_email": to_email,
        "subject": "", "body": "", "personalization_score": 0.0, "status": "draft",
    }

    if not to_email:
        base["status"] = "skipped_no_email"
        return base

    try:
        response = await llm.ainvoke([
            SystemMessage(content=EMAIL_SYSTEM),
            HumanMessage(content=_build_prompt(lead, sender_name, sender_background, sender_value_prop)),
        ])
        raw = response.content.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        parsed = json.loads(raw.strip())

        subject = parsed.get("subject","")
        body    = parsed.get("body","")

        # Safety fix: replace "There," opener with "Hi,"
        body = body.replace("There,\n", "Hi,\n").replace("There, ", "Hi, ")

        base["subject"] = subject
        base["body"]    = body
        print(f"  [Email] {company} ✓ — \"{subject[:60]}\"")

    except Exception as e:
        print(f"  [Email] {company} error: {e}")
        ceo_first = to_name.split()[0] if to_name else ""
        opener    = f"Hi {ceo_first}," if ceo_first else "Hi,"
        hook      = lead.get("personalization_hook","")[:100] or lead.get("description","")[:100]
        base["subject"] = f"Noticed {company}'s recent momentum"
        base["body"]    = (
            f"{opener}\n\n"
            f"{hook}\n\n"
            f"We help companies like yours with {sender_value_prop}. "
            f"Thought there might be a fit.\n\n"
            f"Would a 15-min call next week make sense?\n\n"
            f"Best,\n{sender_name}"
        )

    return base


async def email_generator_node(state: AgentState) -> dict:
    leads  = state.get("enriched_leads") or state.get("leads", [])
    errors = state.get("errors", [])

    if not leads:
        return {"generated_emails": [], "current_step": "No leads to generate emails for", "errors": errors}

    sender_name       = state.get("sender_name", "Alex")
    sender_value_prop = state.get("sender_value_prop",
        "developer tooling and API infrastructure for engineering teams")
    # Resume/profile context — set by user at campaign creation (Phase 3 DB will store this)
    sender_background = state.get("sender_background", "")

    def _primary_email(lead):
        return (lead.get("ceo_email") or lead.get("cto_email") or
                lead.get("hr_email") or lead.get("engineering_email") or "")

    def _primary_name(lead):
        return (lead.get("ceo_name") or lead.get("cto_name") or
                lead.get("hr_name") or "")

    def _primary_linkedin(lead):
        return (lead.get("ceo_linkedin") or lead.get("cto_linkedin") or
                lead.get("hr_linkedin") or "")

    with_email    = [l for l in leads if _primary_email(l)]
    without_email = [l for l in leads if not _primary_email(l)]
    print(f"[EmailGen] Generating emails: {len(with_email)} with contact, {len(without_email)} without")

    if not settings.groq_api_key:
        emails = []
        for lead in with_email:
            contact_name  = _primary_name(lead)
            contact_first = contact_name.split()[0] if contact_name else ""
            opener    = f"Hi {contact_first}," if contact_first else "Hi,"
            hook      = lead.get("personalization_hook","") or lead.get("description","")[:100]
            emails.append({
                "lead_company": lead.get("company_name",""),
                "to_name": contact_name, "to_email": _primary_email(lead),
                "subject": f"Noticed {lead.get('company_name','')}'s recent momentum",
                "body": f"{opener}\n\n{hook}\n\nWould a 15-min call make sense?\n\nBest,\n{sender_name}",
                "personalization_score": 0.3, "status": "draft",
            })
        for lead in without_email:
            emails.append({
                "lead_company": lead.get("company_name",""), "to_name": lead.get("ceo_name",""),
                "to_email": "", "subject": "", "body": "", "personalization_score": 0, "status": "skipped_no_email",
            })
        return {"generated_emails": emails, "current_step": f"Generated {len(with_email)} emails", "errors": errors}

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.7,
        max_tokens=600,
    )

    all_leads = with_email + without_email
    emails = []
    for i in range(0, len(all_leads), MAX_CONCURRENT):
        batch   = all_leads[i : i + MAX_CONCURRENT]
        tasks   = [generate_single_email(l, llm, sender_name, sender_background, sender_value_prop) for l in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for lead, res in zip(batch, results):
            if isinstance(res, Exception):
                print(f"  [Email] Exception {lead.get('company_name')}: {res}")
            else:
                emails.append(res)

    generated = [e for e in emails if e.get("status") == "draft"]
    skipped   = [e for e in emails if e.get("status") == "skipped_no_email"]
    print(f"[EmailGen] Done — {len(generated)} generated, {len(skipped)} skipped")

    return {
        "generated_emails": emails,
        "current_step": f"Generated {len(generated)} emails — {len(skipped)} skipped (no contact)",
        "errors": errors,
    }


async def email_generator_node_multi(state: AgentState) -> dict:
    """
    Extended version: generates one email per CONTACT (not per lead).
    Used when target_roles includes multiple roles or max_per_role > 1.
    Replaces email_generator_node in graph when multi-role is requested.
    """
    leads  = state.get("enriched_leads") or state.get("leads", [])
    errors = state.get("errors", [])

    if not leads:
        return {"generated_emails": [], "current_step": "No leads", "errors": errors}

    sender_name       = state.get("sender_name","Alex")
    sender_value_prop = state.get("sender_value_prop","developer tooling for engineering teams")
    sender_background = state.get("sender_background","")

    if not settings.groq_api_key:
        return await email_generator_node(state)

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=settings.groq_api_key,
        temperature=0.7, max_tokens=600,
    )

    all_emails = []
    tasks = []
    lead_contact_pairs = []

    for lead in leads:
        contacts = lead.get("contacts", [])
        if not contacts:
            # Fallback to flat fields
            if lead.get("ceo_email"):
                contacts = [{"role":"ceo","name":lead.get("ceo_name",""),
                             "email":lead.get("ceo_email"),"linkedin_url":lead.get("ceo_linkedin")}]
        for contact in contacts:
            if not contact.get("email"):
                continue
            # Build a lead copy with this contact as the primary target
            lead_copy = dict(lead)
            lead_copy["ceo_name"]     = contact.get("name","")
            lead_copy["ceo_email"]    = contact.get("email","")
            lead_copy["ceo_linkedin"] = contact.get("linkedin_url","")
            lead_copy["_role"]        = contact.get("role","ceo")
            lead_contact_pairs.append((lead_copy, contact))
            tasks.append(generate_single_email(
                lead_copy, llm, sender_name, sender_background, sender_value_prop
            ))

    if not tasks:
        return {"generated_emails": [], "current_step": "No contacts with emails", "errors": errors}

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for (lead_copy, contact), res in zip(lead_contact_pairs, results):
        if isinstance(res, Exception):
            print(f"  [Email] Exception: {res}")
        else:
            res["role"]        = contact.get("role","ceo")
            res["linkedin_url"]= contact.get("linkedin_url","")
            res["confidence"]  = contact.get("confidence",0)
            all_emails.append(res)

    generated = [e for e in all_emails if e.get("status") == "draft"]
    print(f"[EmailGen] Multi-role: {len(generated)} emails generated")

    return {
        "generated_emails": all_emails,
        "current_step": f"Generated {len(generated)} emails across all target roles",
        "errors": errors,
    }
"""
Validator Node
--------------
Scores each generated email on:
  - Personalization  (0-1): does it reference specific company details?
  - Length           (0-1): is it concise (60-150 words)?
  - CTA presence     (0-1): does it have a clear call to action?
  - Subject quality  (0-1): is the subject line specific?

Overall score = average of above.
Emails below 0.4 are flagged for review.
Emails with no subject or body are marked skipped.
"""

import re
from app.agents.state import AgentState, GeneratedEmail


PERSONALIZATION_SIGNALS = [
    r"\bYC\b", r"\bSeries [A-D]\b", r"\braised\b", r"\bfounded\b",
    r"\b\d+[MBK]\b",          # "$35M", "200K+"
    r"\b\d{4}\b",              # year reference
    r"\bAPI\b|\bSaaS\b|\bAI\b|\bML\b|\bLLM\b",
]

CTA_SIGNALS = [
    r"15.min", r"quick call", r"chat", r"connect",
    r"make sense", r"worth a", r"would you be",
]

SPAM_WORDS = [
    "synergy", "leverage", "revolutionary", "game.changer",
    "disruptive", "paradigm", "blockchain", "innovative solution",
    "i hope this (email|message) finds you",
]


def _count_words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def _score_email(email: GeneratedEmail, lead: dict) -> float:
    subject = email.get("subject","")
    body    = email.get("body","")

    if not subject or not body:
        return 0.0

    scores = {}

    # 1. Personalization — does it mention company-specific details?
    combined = (subject + " " + body).lower()
    company  = (lead.get("company_name","") or "").lower()
    signals  = sum(1 for p in PERSONALIZATION_SIGNALS if re.search(p, combined, re.I))
    mentions_company = company.split()[0] in combined if company else False
    scores["personalization"] = min(1.0, (signals * 0.2) + (0.3 if mentions_company else 0))

    # 2. Length — 60–150 words is ideal
    word_count = _count_words(body)
    if 60 <= word_count <= 150:
        scores["length"] = 1.0
    elif 40 <= word_count < 60 or 150 < word_count <= 200:
        scores["length"] = 0.7
    else:
        scores["length"] = 0.3

    # 3. CTA
    has_cta = any(re.search(p, body, re.I) for p in CTA_SIGNALS)
    scores["cta"] = 1.0 if has_cta else 0.2

    # 4. Subject quality — specific, not generic
    generic_subjects = ["quick question","touching base","following up","partnership opportunity"]
    subject_generic  = any(g in subject.lower() for g in generic_subjects)
    subject_short    = _count_words(subject) <= 8
    scores["subject"] = 0.3 if subject_generic else (0.9 if subject_short else 0.6)

    # 5. Spam penalty
    spam_hits = sum(1 for w in SPAM_WORDS if re.search(w, combined, re.I))
    spam_penalty = min(0.4, spam_hits * 0.15)

    raw = sum(scores.values()) / len(scores) - spam_penalty
    return round(max(0.0, min(1.0, raw)), 2)


async def validator_node(state: AgentState) -> dict:
    """
    Reads:  state["generated_emails"], state["enriched_leads"]
    Writes: state["validated_emails"], state["current_step"]
    """
    emails = state.get("generated_emails", [])
    leads  = state.get("enriched_leads") or state.get("leads", [])
    errors = state.get("errors", [])

    if not emails:
        return {"validated_emails": [], "current_step": "No emails to validate", "errors": errors}

    # Build lead lookup by company name
    lead_map = {l.get("company_name","").lower(): l for l in leads}

    validated = []
    scores    = []

    for email in emails:
        if email.get("status") in ("skipped_no_email",):
            validated.append(email)
            continue

        lead  = lead_map.get((email.get("lead_company","")).lower(), {})
        score = _score_email(email, lead)
        email["personalization_score"] = score
        scores.append(score)

        if score < 0.4:
            email["status"] = "needs_review"
            print(f"  [Validator] {email.get('lead_company')} score={score} → needs_review")
        else:
            email["status"] = "approved"
            print(f"  [Validator] {email.get('lead_company')} score={score} → approved")

        validated.append(email)

    avg_score  = round(sum(scores) / len(scores), 2) if scores else 0
    approved   = sum(1 for e in validated if e.get("status") == "approved")
    print(f"[Validator] {approved}/{len(validated)} approved | avg score: {avg_score}")

    return {
        "validated_emails": validated,
        "current_step": f"Validated {len(validated)} emails — {approved} approved (avg score {avg_score})",
        "errors": errors,
    }
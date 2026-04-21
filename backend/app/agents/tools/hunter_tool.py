"""
Contact Finder Tool
-------------------
Priority:
  1. Hunter.io domain search  (role-matched)
  2. Hunter.io email finder   (by name)
  3. Pattern guesser          (always fallback)

Also fetches LinkedIn profile URL for each contact.
Supports target_role: "ceo" | "cto" | "hr" | "engineering"
"""

import httpx, re
from typing import Optional
from app.core.config import get_settings

settings = get_settings()

HUNTER_DOMAIN = "https://api.hunter.io/v2/domain-search"
HUNTER_FINDER = "https://api.hunter.io/v2/email-finder"

TARGET_ROLES = {
    "ceo": ["ceo","chief executive","founder","co-founder","cofounder",
            "president","managing director","md","owner","general partner"],
    "cto": ["cto","chief technology","vp engineering","head of engineering",
            "head of tech","vp of engineering","engineering lead"],
    "hr":  ["hr","human resources","people","talent","recruiting","recruiter",
            "people ops","head of people","vp people","chief people"],
    "engineering": ["engineering manager","lead engineer","senior engineer",
                    "head of product","vp product","staff engineer"],
}

def _match_role(position: str, target: str) -> bool:
    pos = (position or "").lower()
    return any(kw in pos for kw in TARGET_ROLES.get(target, [target]))

def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split()
    return (parts[0], parts[-1]) if len(parts) >= 2 else (full_name or "", "")

def _domain_from_website(website: str) -> str:
    d = re.sub(r"https?://", "", website or "")
    d = re.sub(r"www\.", "", d)
    return d.split("/")[0].split("?")[0]

def _guess_emails(first: str, last: str, domain: str) -> list[str]:
    f  = (first or "").lower().strip()
    l  = (last  or "").lower().strip()
    fl = f[0] if f else ""
    if not f or not domain:
        return [f"info@{domain}", f"hello@{domain}"] if domain else []
    candidates = [f"{f}@{domain}"]
    if l:
        candidates += [
            f"{f}.{l}@{domain}",
            f"{f}{l}@{domain}",
            f"{fl}{l}@{domain}",
            f"{f}_{l}@{domain}",
        ]
    return candidates

def _safe_email(entry: dict) -> Optional[str]:
    return entry.get("email") or entry.get("value") or None

def _build_linkedin(first: str, last: str, company: str = "") -> str:
    """Generate a likely LinkedIn search URL for this person."""
    if not first:
        return ""
    name_slug = f"{first}-{last}".lower().replace(" ", "-") if last else first.lower()
    # Return a direct LinkedIn search URL — user can verify
    query = f"{first} {last} {company}".strip()
    return f"https://www.linkedin.com/search/results/people/?keywords={query.replace(' ', '%20')}"


async def find_contact_email(
    website: str,
    name: Optional[str],
    role: str = "ceo",
    company_name: str = "",
) -> dict:
    domain = _domain_from_website(website)
    result = {
        "email":      None,
        "name":       name,
        "role":       role,
        "source":     None,
        "confidence": 0,
        "guesses":    [],
        "domain":     domain,
        "linkedin":   "",
    }

    if not domain:
        return result

    first, last = _split_name(name or "")

    # Pre-build LinkedIn URL (always available)
    result["linkedin"] = _build_linkedin(first, last, company_name)

    # ── Strategy 1a: Hunter domain search ─────────────────────────────────────
    if settings.hunter_api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(HUNTER_DOMAIN, params={
                    "domain": domain, "api_key": settings.hunter_api_key, "limit": 20,
                })
            if resp.status_code == 200:
                raw_emails = resp.json().get("data", {}).get("emails", [])
                emails = [e for e in raw_emails if _safe_email(e)]

                # Try role-matched first
                for e in emails:
                    if _match_role(e.get("position",""), role):
                        contact_name = f"{e.get('first_name','')} {e.get('last_name','')}".strip()
                        linkedin_url = (e.get("linkedin") or
                                        _build_linkedin(e.get("first_name",""),
                                                        e.get("last_name",""), company_name))
                        result.update({
                            "email":      _safe_email(e),
                            "name":       contact_name or name,
                            "source":     "hunter_domain",
                            "confidence": e.get("confidence", 70),
                            "linkedin":   linkedin_url,
                        })
                        print(f"    → Hunter {role}: {result['email']} | LinkedIn: {linkedin_url[:50]}")
                        return result

                # Fallback: best confidence
                if emails:
                    best = max(emails, key=lambda e: e.get("confidence", 0))
                    contact_name = f"{best.get('first_name','')} {best.get('last_name','')}".strip()
                    result.update({
                        "email":      _safe_email(best),
                        "name":       contact_name or name,
                        "source":     "hunter_domain_best",
                        "confidence": best.get("confidence", 50),
                        "linkedin":   best.get("linkedin") or _build_linkedin(
                                        best.get("first_name",""), best.get("last_name",""), company_name),
                    })
                    print(f"    → Hunter best: {result['email']}")
                    return result
                else:
                    print(f"    → Hunter: 0 emails for {domain}")

        except Exception as e:
            print(f"    → Hunter domain error: {e}")

    # ── Strategy 1b: Hunter email finder by name ───────────────────────────────
    if settings.hunter_api_key and first and last:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(HUNTER_FINDER, params={
                    "domain": domain, "first_name": first,
                    "last_name": last, "api_key": settings.hunter_api_key,
                })
            if resp.status_code == 200:
                data  = resp.json().get("data", {})
                email = data.get("email")
                score = data.get("score", 0)
                if email and score > 20:
                    result.update({
                        "email":      email,
                        "source":     "hunter_finder",
                        "confidence": score,
                    })
                    print(f"    → Hunter finder: {email} ({score}%)")
                    return result
        except Exception as e:
            print(f"    → Hunter finder error: {e}")

    # ── Strategy 2: Pattern guesser ────────────────────────────────────────────
    guesses = _guess_emails(first, last, domain)
    result["guesses"] = guesses
    if guesses:
        result.update({
            "email":      guesses[0],
            "source":     "pattern_guess",
            "confidence": 20 if (first and last) else 10,
        })
        print(f"    → Pattern guess: {guesses[0]}")

    return result
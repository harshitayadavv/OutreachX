"""
Resume Parser
-------------
Parses the user's uploaded resume (PDF or TXT) and extracts:
  - Name, current role, company
  - Key skills and experience summary
  - Value proposition (what they're offering)

This context is injected into every email so it sounds
like IT's written BY the user, from their background.
"""

import re
from pathlib import Path
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


def _extract_text_from_pdf(path: str) -> str:
    """Extract raw text from PDF using PyPDF2 or pdfplumber."""
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        pass
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except ImportError:
        pass
    return ""


def _extract_text_from_txt(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


async def parse_resume(file_path: str, file_type: str) -> dict:
    """
    Parse resume and return structured profile.

    Returns:
        {
            "name": str,
            "current_role": str,
            "company": str,
            "skills": [str],
            "background_summary": str,   # 2-3 sentences for email context
            "value_prop": str,           # what they offer to target companies
            "raw_text": str,
        }
    """
    result = {
        "name": "", "current_role": "", "company": "",
        "skills": [], "background_summary": "", "value_prop": "",
        "raw_text": "",
    }

    # Extract raw text
    if file_type == "pdf":
        raw = _extract_text_from_pdf(file_path)
    else:
        raw = _extract_text_from_txt(file_path)

    if not raw.strip():
        return result

    result["raw_text"] = raw[:3000]  # cap for LLM context

    # Use Groq to extract structured info
    if not settings.groq_api_key:
        # Basic extraction without LLM
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        result["name"]               = lines[0] if lines else ""
        result["background_summary"] = " ".join(lines[1:4])
        return result

    from langchain_groq import ChatGroq
    from langchain_core.messages import SystemMessage, HumanMessage

    RESUME_SYSTEM = """
Extract structured information from this resume. Return ONLY valid JSON:
{
  "name": "<full name>",
  "current_role": "<current job title>",
  "company": "<current employer>",
  "skills": ["<skill 1>", "<skill 2>", "<skill 3>"],
  "background_summary": "<2 sentences: who they are and what they've built/done — specific and impressive>",
  "value_prop": "<1 sentence: what they can offer to a startup — concrete, not generic>"
}
"""

    try:
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.groq_api_key,
            temperature=0.1, max_tokens=512,
        )
        response = await llm.ainvoke([
            SystemMessage(content=RESUME_SYSTEM),
            HumanMessage(content=f"Resume:\n{raw[:2500]}"),
        ])
        parsed_raw = response.content.strip()
        if "```" in parsed_raw:
            parsed_raw = parsed_raw.split("```")[1]
            if parsed_raw.startswith("json"): parsed_raw = parsed_raw[4:]
        import json
        parsed = json.loads(parsed_raw.strip())
        result.update({k: v for k, v in parsed.items() if k in result})
        print(f"[ResumeParser] Extracted: {result['name']} — {result['current_role']}")
    except Exception as e:
        print(f"[ResumeParser] LLM error: {e}")
        lines = [l.strip() for l in raw.split("\n") if l.strip()]
        result["name"] = lines[0] if lines else ""

    return result
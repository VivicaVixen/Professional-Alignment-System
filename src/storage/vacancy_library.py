"""
Vacancy library: persist and retrieve analyzed vacancies.

Files are stored as JSON in data/vacancies/ at the project root.
Each file holds vacancy_data, match_results, and the original raw text.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_PROJECT_ROOT = Path(__file__).parent.parent.parent
VACANCIES_DIR = _PROJECT_ROOT / "data" / "vacancies"


@dataclass
class VacancySummary:
    slug: str
    title: str
    company: str
    timestamp: str
    language: str


def _make_slug(vacancy_data: Dict[str, Any], raw_text: str) -> str:
    """Derive a stable filename slug from job title, company, and a short hash."""
    title = vacancy_data.get("job_title", "unknown") or "unknown"
    company_info = vacancy_data.get("company_info", "")
    if isinstance(company_info, dict):
        company = company_info.get("name", "") or ""
    else:
        company = str(company_info or "")

    # Take the first 40 chars of company text (it can be a long paragraph)
    company_short = company.strip()[:40]

    # Build a readable prefix: lowercase, spaces → hyphens, strip non-alnum
    def _slugify(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r"[^a-z0-9\s-]", "", s)
        s = re.sub(r"\s+", "-", s)
        return s[:30].strip("-")

    prefix = _slugify(f"{title}-{company_short}") or "vacancy"
    short_hash = hashlib.md5(raw_text.encode("utf-8", errors="replace")).hexdigest()[:8]
    return f"{prefix}-{short_hash}"


def save_vacancy(
    vacancy_data: Dict[str, Any],
    match_results: Dict[str, Any],
    raw_text: str,
    slug: Optional[str] = None,
) -> Path:
    """
    Persist a vacancy analysis to disk.

    Returns the path of the saved JSON file.
    """
    VACANCIES_DIR.mkdir(parents=True, exist_ok=True)

    if not slug:
        slug = _make_slug(vacancy_data, raw_text)

    payload = {
        "slug": slug,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "vacancy_data": vacancy_data,
        "match_results": match_results,
        "raw_text": raw_text,
    }

    path = VACANCIES_DIR / f"{slug}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path


def list_vacancies() -> List[VacancySummary]:
    """
    Return all saved vacancies ordered newest-first.

    Each entry contains the display metadata needed for a dropdown.
    """
    if not VACANCIES_DIR.exists():
        return []

    summaries: List[VacancySummary] = []
    for path in VACANCIES_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            vd = data.get("vacancy_data", {})
            company_info = vd.get("company_info", "")
            if isinstance(company_info, dict):
                company = company_info.get("name", "") or ""
            else:
                # company_info may be a free-text paragraph — extract first line
                company = str(company_info or "").split("\n")[0].strip()[:60]

            summaries.append(VacancySummary(
                slug=data.get("slug", path.stem),
                title=vd.get("job_title", "Unknown title"),
                company=company or "Unknown company",
                timestamp=data.get("timestamp", ""),
                language=vd.get("language", "en"),
            ))
        except Exception:
            continue

    summaries.sort(key=lambda s: s.timestamp, reverse=True)
    return summaries


def load_vacancy(slug: str) -> Dict[str, Any]:
    """
    Load a saved vacancy by slug.

    Returns a dict with keys: vacancy_data, match_results, raw_text.
    Ready to be merged into session state.
    """
    path = VACANCIES_DIR / f"{slug}.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "vacancy_data": data.get("vacancy_data", {}),
        "match_results": data.get("match_results", {}),
        "raw_text": data.get("raw_text", ""),
    }

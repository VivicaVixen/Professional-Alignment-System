"""
Match engine module.
Uses Qwen 2.5 Coder to compare vacancy requirements against user profile.
"""

import json
import sys
from typing import Dict, List, Any
import pas_inference_client as ollama
from pydantic import ValidationError
from src.models.schemas import MatchResult
from src.prompts.loader import load_prompt, get_model_name, build_messages


def match_profile_to_vacancy(vacancy_data: Dict[str, Any], profile_data: Dict[str, Any],
                             model_name: str = "qwen2.5-coder:7b",
                             base_url: str = "http://localhost:11434") -> Dict[str, Any]:
    """
    Compare vacancy requirements against user profile to find strong points and gaps.

    Args:
        vacancy_data: Parsed vacancy data
        profile_data: User profile data
        model_name: Ollama model name (overridden by config/prompts/match.yaml)
        base_url: Ollama API base URL

    Returns:
        Dictionary with strong points, gaps, and alignment score
    """
    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("match", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        vacancy_data=json.dumps(vacancy_data, indent=2),
        profile_data=json.dumps(profile_data, indent=2),
    )

    try:
        response = ollama.chat(
            model=resolved_model,
            messages=messages,
            options={
                "temperature": cfg.temperature,
                "top_p": cfg.top_p,
                "num_predict": cfg.num_predict,
            },
        )

        content = response["message"]["content"].strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            match = MatchResult.model_validate_json(content)
            return match.model_dump()
        except ValidationError as ve:
            print(f"[MatchResult ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw LLM output]: {content}", file=sys.stderr)
            raise

    except Exception as e:
        return {
            "strong_points": [],
            "gaps": [],
            "alignment_score": 50,
            "error": str(e),
        }


def generate_strong_points_rule_based(vacancy_data: Dict[str, Any],
                                       profile_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate strong points using rule-based matching (fallback without LLM).

    Args:
        vacancy_data: Parsed vacancy data
        profile_data: User profile data

    Returns:
        List of strong point dictionaries
    """
    strong_points = []

    profile_skills = set()
    for skill in profile_data.get("skills", {}).get("technical", []):
        profile_skills.add(skill.lower())
    for skill in profile_data.get("skills", {}).get("soft", []):
        profile_skills.add(skill.lower())

    vacancy_keywords = [kw.lower() for kw in vacancy_data.get("keywords", [])]
    matched_skills = profile_skills.intersection(set(vacancy_keywords))

    for skill in matched_skills:
        evidence = f"Profile includes {skill}"
        for exp in profile_data.get("experience", []):
            if skill in " ".join(exp.get("skills_used", [])).lower():
                evidence = f"Used {skill} at {exp.get('company', 'previous role')}"
                break
        strong_points.append({
            "vacancy_term": skill,
            "profile_evidence": evidence,
            "rationale": f"Candidate has direct experience with {skill}",
        })

    if profile_data.get("education"):
        strong_points.append({
            "vacancy_term": "Educational background",
            "profile_evidence": f"{len(profile_data['education'])} degree(s) listed",
            "rationale": "Candidate has formal education credentials",
        })

    if profile_data.get("experience"):
        exp_count = len(profile_data["experience"])
        strong_points.append({
            "vacancy_term": "Professional experience",
            "profile_evidence": f"{exp_count} role(s) documented",
            "rationale": "Candidate has documented work experience",
        })

    return strong_points


def identify_gaps_rule_based(vacancy_data: Dict[str, Any],
                             profile_data: Dict[str, Any]) -> List[str]:
    """
    Identify gaps using rule-based matching (fallback without LLM).

    Args:
        vacancy_data: Parsed vacancy data
        profile_data: User profile data

    Returns:
        List of gap strings
    """
    gaps = []

    profile_skills = set()
    for skill in profile_data.get("skills", {}).get("technical", []):
        profile_skills.add(skill.lower())

    vacancy_keywords = [kw.lower() for kw in vacancy_data.get("keywords", [])]
    missing_skills = set(vacancy_keywords) - profile_skills

    important_keywords = [
        "python", "java", "javascript", "sql", "aws", "azure", "machine learning",
        "project management", "leadership", "agile", "data analysis",
    ]

    for skill in missing_skills:
        if skill in important_keywords:
            gaps.append(f"No evidence of {skill} experience in profile")

    vacancy_seniority = vacancy_data.get("seniority", "mid")
    exp_count = len(profile_data.get("experience", []))

    if vacancy_seniority in ["senior", "lead", "executive"] and exp_count < 2:
        gaps.append(f"Limited experience for {vacancy_seniority}-level role")

    return gaps

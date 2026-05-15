"""
Profile merger module.
Merges multiple profile sources into a single canonical profile.
"""

import json
from typing import Dict, List, Any
from pathlib import Path


def merge_profiles(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple profile dictionaries into one canonical profile.
    
    Args:
        profiles: List of profile dictionaries from different sources
        
    Returns:
        Merged profile dictionary
    """
    if not profiles:
        return create_empty_profile()
    
    if len(profiles) == 1:
        return clean_profile(profiles[0])
    
    # Start with empty profile
    merged = create_empty_profile()
    
    # Merge personal info (prefer non-empty values)
    for key in ["name", "email", "phone", "location", "linkedin", "portfolio"]:
        for profile in profiles:
            value = profile.get("personal_info", {}).get(key, "")
            if value:
                merged["personal_info"][key] = value
                break
    
    # Merge summary (prefer longest)
    summaries = [p.get("summary", "") for p in profiles if p.get("summary")]
    if summaries:
        merged["summary"] = max(summaries, key=len)
    
    # Merge experience (combine and deduplicate)
    all_experience = []
    for profile in profiles:
        all_experience.extend(profile.get("experience", []))
    merged["experience"] = deduplicate_experience(all_experience)
    
    # Merge education (combine and deduplicate)
    all_education = []
    for profile in profiles:
        all_education.extend(profile.get("education", []))
    merged["education"] = deduplicate_education(all_education)
    
    # Merge skills (combine unique skills)
    for profile in profiles:
        skills = profile.get("skills", {})
        for skill in skills.get("technical", []):
            if skill not in merged["skills"]["technical"]:
                merged["skills"]["technical"].append(skill)
        for skill in skills.get("soft", []):
            if skill not in merged["skills"]["soft"]:
                merged["skills"]["soft"].append(skill)
        for lang in skills.get("languages", []):
            if lang not in merged["skills"]["languages"]:
                merged["skills"]["languages"].append(lang)
    
    # Merge certifications
    all_certs = []
    for profile in profiles:
        all_certs.extend(profile.get("certifications", []))
    merged["certifications"] = deduplicate_certifications(all_certs)
    
    # Merge projects
    all_projects = []
    for profile in profiles:
        all_projects.extend(profile.get("projects", []))
    merged["projects"] = deduplicate_projects(all_projects)
    
    return clean_profile(merged)


def clean_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Remove temporary keys and ensure proper structure."""
    # Remove raw sections if present
    profile.pop("_raw_sections", None)
    
    # Ensure all required keys exist
    required_keys = [
        "personal_info", "summary", "experience", "education",
        "skills", "certifications", "projects"
    ]
    for key in required_keys:
        if key not in profile:
            if key == "personal_info":
                profile[key] = {
                    "name": "", "email": "", "phone": "",
                    "location": "", "linkedin": "", "portfolio": ""
                }
            elif key == "skills":
                profile[key] = {"technical": [], "soft": [], "languages": []}
            else:
                profile[key] = []
    
    return profile


def create_empty_profile() -> Dict[str, Any]:
    """Create an empty profile template."""
    return {
        "personal_info": {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "portfolio": ""
        },
        "summary": "",
        "experience": [],
        "education": [],
        "skills": {
            "technical": [],
            "soft": [],
            "languages": []
        },
        "certifications": [],
        "projects": []
    }


def deduplicate_experience(experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate experience entries."""
    seen = set()
    unique = []
    
    for exp in experiences:
        key = (exp.get("title", ""), exp.get("company", ""), exp.get("start", ""))
        if key not in seen:
            seen.add(key)
            unique.append(exp)
    
    return unique


def deduplicate_education(education: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate education entries."""
    seen = set()
    unique = []
    
    for edu in education:
        key = (edu.get("degree", ""), edu.get("institution", ""), edu.get("year", ""))
        if key not in seen:
            seen.add(key)
            unique.append(edu)
    
    return unique


def deduplicate_certifications(certifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate certifications."""
    seen = set()
    unique = []
    
    for cert in certifications:
        key = (cert.get("name", ""), cert.get("issuer", ""), cert.get("year", ""))
        if key not in seen:
            seen.add(key)
            unique.append(cert)
    
    return unique


def deduplicate_projects(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate projects."""
    seen = set()
    unique = []
    
    for proj in projects:
        key = (proj.get("name", ""), proj.get("url", ""))
        if key not in seen:
            seen.add(key)
            unique.append(proj)
    
    return unique


def save_profile(profile: Dict[str, Any], file_path: str) -> None:
    """Save profile to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


def load_profile(file_path: str) -> Dict[str, Any]:
    """Load profile from JSON file."""
    path = Path(file_path)
    if not path.exists():
        return create_empty_profile()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

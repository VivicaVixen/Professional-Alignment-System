"""
Text ingestion module.
Parses plain text CVs into structured profile data.
"""

import re
from typing import Dict, List, Any


def extract_text_from_file(file_path: str) -> str:
    """Read text content from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_name_from_text(text: str) -> str:
    """Extract name from plain text CV."""
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line.split()) <= 4 and len(line) > 2:
            # Likely the name is at the top
            return line
    return ""


def parse_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information from text."""
    contact = {
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "portfolio": ""
    }
    
    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        contact["email"] = email_match.group(0)
    
    # Phone
    phone_match = re.search(r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]*', text)
    if phone_match:
        contact["phone"] = phone_match.group(0).strip()
    
    # LinkedIn
    linkedin_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+', text)
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group(0)
    
    # Portfolio/Website
    url_match = re.search(r'(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?', text)
    if url_match:
        url = url_match.group(0)
        if 'linkedin' not in url:
            contact["portfolio"] = url
    
    return contact


def parse_sections(text: str) -> Dict[str, str]:
    """Split text into sections based on headers."""
    sections = {}
    current_section = "header"
    current_content = []
    
    section_keywords = {
        "experience": ["experience", "work history", "employment", "professional experience"],
        "education": ["education", "academic background", "qualifications"],
        "skills": ["skills", "technical skills", "competencies", "technologies"],
        "summary": ["summary", "profile", "objective", "about me"],
        "certifications": ["certifications", "certificates", "licenses"],
        "projects": ["projects", "personal projects", "key projects"]
    }
    
    lines = text.split('\n')
    for line in lines:
        line_stripped = line.strip()
        
        # Check if line is a section header
        is_header = False
        for section_name, keywords in section_keywords.items():
            if any(kw in line_stripped.lower() for kw in keywords):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = section_name
                current_content = []
                is_header = True
                break
        
        if not is_header:
            current_content.append(line)
    
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    return sections


def ingest_text(file_path: str) -> Dict[str, Any]:
    """
    Ingest a plain text CV file and return structured profile data.
    
    Args:
        file_path: Path to the text file
        
    Returns:
        Dictionary with extracted profile data
    """
    text = extract_text_from_file(file_path)
    contact = parse_contact_info(text)
    sections = parse_sections(text)
    
    profile = {
        "personal_info": {
            "name": parse_name_from_text(text),
            "email": contact["email"],
            "phone": contact["phone"],
            "location": contact["location"],
            "linkedin": contact["linkedin"],
            "portfolio": contact["portfolio"]
        },
        "summary": sections.get("summary", ""),
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
    
    # Parse skills section if exists
    if "skills" in sections:
        skills_text = sections["skills"]
        skill_lines = [line.strip() for line in skills_text.split('\n') if line.strip()]
        for skill_line in skill_lines:
            # Remove bullets and separators
            skill_line = skill_line.lstrip('•-*●')
            skills = [s.strip() for s in skill_line.split(',')]
            profile["skills"]["technical"].extend(skills)
    
    # Store raw sections for LLM processing
    profile["_raw_sections"] = sections
    
    return profile

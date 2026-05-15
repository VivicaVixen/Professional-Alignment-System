"""
PDF CV ingestion module.
Parses PDF CV files into structured profile data.
"""

import pdfplumber
import re
from typing import Dict, List, Any


def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def parse_name(text: str) -> str:
    """Extract name from CV text (usually first line)."""
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line.split()) <= 4 and len(line) > 2:
            return line
    return ""


def parse_email(text: str) -> str:
    """Extract email address from text."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    return match.group(0) if match else ""


def parse_phone(text: str) -> str:
    """Extract phone number from text."""
    phone_pattern = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\./0-9]*'
    match = re.search(phone_pattern, text)
    return match.group(0) if match else ""


def parse_linkedin(text: str) -> str:
    """Extract LinkedIn URL from text."""
    linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+'
    match = re.search(linkedin_pattern, text)
    return match.group(0) if match else ""


def parse_experience(text: str) -> List[Dict[str, Any]]:
    """Extract experience entries from CV text."""
    experiences = []
    
    # Look for date patterns (e.g., "2020 - 2023", "Jan 2020 - Present")
    date_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|\d{4})\s*[-–—to]+\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}|\d{4}|Present)'
    
    lines = text.split('\n')
    current_exp = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        date_match = re.search(date_pattern, line)
        if date_match:
            if current_exp:
                experiences.append(current_exp)
            current_exp = {
                "title": "",
                "company": "",
                "start": date_match.group(1),
                "end": date_match.group(2) if date_match.group(2) != "Present" else "",
                "achievements": [],
                "skills_used": []
            }
            # Title is usually before the date
            title_part = line[:date_match.start()].strip()
            if title_part:
                current_exp["title"] = title_part
        elif current_exp and line.startswith(('•', '-', '*', '●')):
            current_exp["achievements"].append(line[1:].strip())
        elif current_exp and not current_exp["company"]:
            current_exp["company"] = line
    
    if current_exp:
        experiences.append(current_exp)
    
    return experiences


def parse_education(text: str) -> List[Dict[str, Any]]:
    """Extract education entries from CV text."""
    education = []
    
    # Look for degree patterns
    degree_keywords = ['Bachelor', 'Master', 'PhD', 'Ph.D', 'BSc', 'MSc', 'MBA', 'B.A', 'M.A', 'B.S', 'M.S']
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if any(kw in line for kw in degree_keywords):
            edu = {
                "degree": "",
                "institution": "",
                "year": ""
            }
            
            # Extract year if present
            year_match = re.search(r'\b(20\d{2}|19\d{2})\b', line)
            if year_match:
                edu["year"] = year_match.group(1)
            
            # Try to identify degree and institution
            for kw in degree_keywords:
                if kw in line:
                    edu["degree"] = line
                    break
            
            if len(lines) > i + 1:
                next_line = lines[i + 1].strip()
                if next_line and not re.search(r'\b(20\d{2}|19\d{2})\b', next_line):
                    edu["institution"] = next_line
            
            education.append(edu)
    
    return education


def parse_skills(text: str) -> Dict[str, List[str]]:
    """Extract skills from CV text."""
    skills = {
        "technical": [],
        "soft": [],
        "languages": []
    }
    
    # Common technical skills patterns
    technical_keywords = [
        'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust',
        'SQL', 'NoSQL', 'MongoDB', 'PostgreSQL', 'MySQL',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
        'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask',
        'Machine Learning', 'AI', 'Data Science', 'Analytics',
        'Agile', 'Scrum', 'DevOps', 'CI/CD', 'Git'
    ]
    
    lines = text.split('\n')
    in_skills_section = False
    
    for line in lines:
        line = line.strip()
        
        if 'skills' in line.lower() and ':' in line:
            in_skills_section = True
            continue
        
        if in_skills_section:
            if line and len(line) < 100:
                # Check for technical skills
                for tech in technical_keywords:
                    if tech.lower() in line.lower() and tech not in skills["technical"]:
                        skills["technical"].append(tech)
                
                # If no match, add as-is
                if not any(tech.lower() in line.lower() for tech in technical_keywords):
                    if line not in skills["technical"] and len(line.split()) <= 5:
                        skills["technical"].append(line)
            else:
                in_skills_section = False
    
    return skills


def ingest_pdf(file_path: str) -> Dict[str, Any]:
    """
    Ingest a PDF CV file and return structured profile data.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Dictionary with extracted profile data
    """
    raw_text = extract_text_from_pdf(file_path)
    
    profile = {
        "personal_info": {
            "name": parse_name(raw_text),
            "email": parse_email(raw_text),
            "phone": parse_phone(raw_text),
            "location": "",
            "linkedin": parse_linkedin(raw_text),
            "portfolio": ""
        },
        "summary": "",
        "experience": parse_experience(raw_text),
        "education": parse_education(raw_text),
        "skills": parse_skills(raw_text),
        "certifications": [],
        "projects": []
    }
    
    return profile

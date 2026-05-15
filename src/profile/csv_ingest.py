"""
CSV ingestion module.
Parses LinkedIn CSV exports into structured profile data.
"""

import csv
from typing import Dict, List, Any
from io import StringIO


def detect_csv_format(file_path: str) -> str:
    """Detect the format of the CSV file (LinkedIn, etc.)."""
    with open(file_path, 'r', encoding='utf-8') as f:
        header = f.readline()
        if 'First Name' in header or 'Name' in header:
            return 'linkedin'
        return 'generic'


def parse_linkedin_csv(file_path: str) -> Dict[str, Any]:
    """Parse a LinkedIn CSV export into profile data."""
    profile = {
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
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Extract name
            first_name = row.get('First Name', '')
            last_name = row.get('Last Name', '')
            if first_name or last_name:
                profile["personal_info"]["name"] = f"{first_name} {last_name}".strip()
            
            # Extract email
            email = row.get('Email Address', '')
            if email:
                profile["personal_info"]["email"] = email
            
            # Extract location
            location = row.get('Location', '')
            if location:
                profile["personal_info"]["location"] = location
            
            # Extract summary
            summary = row.get('Summary', '')
            if summary:
                profile["summary"] = summary
            
            # Extract skills
            skills = row.get('Skills', '')
            if skills:
                skill_list = [s.strip() for s in skills.split(',')]
                profile["skills"]["technical"].extend(skill_list)
    
    return profile


def ingest_csv(file_path: str) -> Dict[str, Any]:
    """
    Ingest a CSV file and return structured profile data.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary with extracted profile data
    """
    csv_format = detect_csv_format(file_path)
    
    if csv_format == 'linkedin':
        return parse_linkedin_csv(file_path)
    else:
        # Generic CSV parsing
        return parse_generic_csv(file_path)


def parse_generic_csv(file_path: str) -> Dict[str, Any]:
    """Parse a generic CSV file into profile data."""
    profile = {
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
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        reader = csv.DictReader(StringIO(content))
        
        for row in reader:
            # Try to map common column names
            for key, value in row.items():
                key_lower = key.lower() if key else ''
                
                if 'name' in key_lower and not profile["personal_info"]["name"]:
                    profile["personal_info"]["name"] = value
                elif 'email' in key_lower:
                    profile["personal_info"]["email"] = value
                elif 'phone' in key_lower:
                    profile["personal_info"]["phone"] = value
                elif 'location' in key_lower or 'city' in key_lower:
                    profile["personal_info"]["location"] = value
                elif 'skill' in key_lower:
                    profile["skills"]["technical"].append(value)
                elif 'summary' in key_lower or 'bio' in key_lower:
                    profile["summary"] = value
    
    return profile

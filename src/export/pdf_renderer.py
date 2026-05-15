"""
PDF renderer module.
Uses Jinja2 templates and WeasyPrint to generate print-ready PDFs.
"""

import os
from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"


def load_template(template_name: str) -> Any:
    """
    Load a Jinja2 template.
    
    Args:
        template_name: Template filename
        
    Returns:
        Jinja2 Template object
    """
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    return env.get_template(template_name)


def render_cv_template(profile_data: Dict[str, Any], cv_content: Dict[str, Any],
                       template_name: str = "cv_modern.html") -> str:
    """
    Render a CV using an HTML template.
    
    Args:
        profile_data: User profile data
        cv_content: Generated CV content (summary, experiences, etc.)
        template_name: Template filename
        
    Returns:
        Rendered HTML string
    """
    template = load_template(template_name)
    
    # Merge profile data with generated content
    context = {
        "name": profile_data.get("personal_info", {}).get("name", ""),
        "email": profile_data.get("personal_info", {}).get("email", ""),
        "phone": profile_data.get("personal_info", {}).get("phone", ""),
        "location": profile_data.get("personal_info", {}).get("location", ""),
        "linkedin": profile_data.get("personal_info", {}).get("linkedin", ""),
        "portfolio": profile_data.get("personal_info", {}).get("portfolio", ""),
        "summary": cv_content.get("executive_summary", profile_data.get("summary", "")),
        "experience": cv_content.get("tailored_experience", profile_data.get("experience", [])),
        "education": profile_data.get("education", []),
        "skills": profile_data.get("skills", {"technical": [], "soft": [], "languages": []}),
        "certifications": profile_data.get("certifications", []),
        "projects": profile_data.get("projects", [])
    }
    
    return template.render(**context)


def render_cover_letter_template(name: str, paragraphs: List[str],
                                 template_name: str = "cl_modern.html",
                                 date: str = "") -> str:
    """
    Render a cover letter using an HTML template.
    
    Args:
        name: Candidate name
        paragraphs: List of cover letter paragraphs
        template_name: Template filename
        date: Date string (defaults to today)
        
    Returns:
        Rendered HTML string
    """
    from datetime import datetime
    
    if not date:
        date = datetime.now().strftime("%B %d, %Y")
    
    template = load_template(template_name)
    
    context = {
        "name": name,
        "paragraphs": paragraphs,
        "date": date
    }
    
    return template.render(**context)


def html_to_pdf(html_content: str, output_path: str) -> bool:
    """
    Convert HTML content to PDF.
    
    Args:
        html_content: HTML string
        output_path: Output PDF file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        HTML(string=html_content).write_pdf(output_path)
        return True
    except Exception as e:
        print(f"PDF generation error: {e}")
        return False


def generate_cv_pdf(profile_data: Dict[str, Any], cv_content: Dict[str, Any],
                    template_name: str, output_path: str) -> bool:
    """
    Generate a PDF CV.
    
    Args:
        profile_data: User profile data
        cv_content: Generated CV content
        template_name: Template filename
        output_path: Output PDF file path
        
    Returns:
        True if successful, False otherwise
    """
    html = render_cv_template(profile_data, cv_content, template_name)
    return html_to_pdf(html, output_path)


def generate_cover_letter_pdf(name: str, paragraphs: List[str],
                              template_name: str, output_path: str,
                              date: str = "") -> bool:
    """
    Generate a PDF cover letter.
    
    Args:
        name: Candidate name
        paragraphs: Cover letter paragraphs
        template_name: Template filename
        output_path: Output PDF file path
        date: Date string
        
    Returns:
        True if successful, False otherwise
    """
    html = render_cover_letter_template(name, paragraphs, template_name, date)
    return html_to_pdf(html, output_path)


def get_available_templates() -> Dict[str, List[str]]:
    """
    Get list of available templates.
    
    Returns:
        Dictionary with 'cv' and 'cover_letter' template lists
    """
    templates = {
        "cv": [],
        "cover_letter": []
    }
    
    if not TEMPLATE_DIR.exists():
        return templates
    
    for file in TEMPLATE_DIR.iterdir():
        if file.suffix == ".html":
            if file.name.startswith("cv_"):
                templates["cv"].append(file.name)
            elif file.name.startswith("cl_"):
                templates["cover_letter"].append(file.name)
    
    return templates

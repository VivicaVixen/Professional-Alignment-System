"""
ATS optimizer module.
Ensures documents are optimized for Applicant Tracking Systems.
"""

import re
from typing import Dict, List, Any, Set


# Common ATS keywords by category
ATS_KEYWORD_CATEGORIES = {
    "technical_skills": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "sql", "nosql", "mongodb", "postgresql", "mysql", "oracle",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "react", "angular", "vue", "node.js", "django", "flask", "spring",
        "machine learning", "artificial intelligence", "data science", "analytics",
        "agile", "scrum", "kanban", "devops", "ci/cd", "git", "jira"
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving", "critical thinking",
        "project management", "time management", "adaptability", "collaboration",
        "strategic planning", "decision making", "mentoring", "coaching"
    ],
    "action_verbs": [
        "achieved", "administered", "analyzed", "built", "collaborated", "created",
        "delivered", "designed", "developed", "directed", "drove", "established",
        "executed", "generated", "implemented", "improved", "increased", "initiated",
        "launched", "led", "managed", "optimized", "organized", "oversaw",
        "planned", "reduced", "resolved", "spearheaded", "streamlined", "transformed"
    ]
}


def extract_ats_keywords(text: str) -> Set[str]:
    """
    Extract ATS-relevant keywords from text.
    
    Args:
        text: Document text
        
    Returns:
        Set of found keywords
    """
    text_lower = text.lower()
    found_keywords = set()
    
    for category_keywords in ATS_KEYWORD_CATEGORIES.values():
        for keyword in category_keywords:
            if keyword.lower() in text_lower:
                found_keywords.add(keyword)
    
    return found_keywords


def calculate_ats_score(document_text: str, vacancy_keywords: List[str]) -> Dict[str, Any]:
    """
    Calculate ATS optimization score for a document.
    
    Args:
        document_text: The document text to evaluate
        vacancy_keywords: Keywords from the vacancy to match against
        
    Returns:
        Dictionary with score details
    """
    document_lower = document_text.lower()
    
    # Count matched vacancy keywords
    matched_keywords = [kw for kw in vacancy_keywords if kw.lower() in document_lower]
    keyword_coverage = len(matched_keywords) / max(len(vacancy_keywords), 1)
    
    # Count action verbs
    action_verb_count = sum(1 for verb in ATS_KEYWORD_CATEGORIES["action_verbs"] 
                           if verb.lower() in document_lower)
    
    # Check for quantifiable achievements (numbers/percentages)
    has_numbers = bool(re.search(r'\d+%', document_text)) or bool(re.search(r'\$\d+', document_text))
    
    # Calculate score (0-100)
    score = 0
    score += min(keyword_coverage * 50, 50)  # Keyword coverage worth 50 points
    score += min(action_verb_count * 5, 25)   # Action verbs worth 25 points
    score += 25 if has_numbers else 10         # Quantifiable results worth 25 points
    
    return {
        "overall_score": round(score),
        "keyword_coverage": round(keyword_coverage * 100),
        "matched_keywords": matched_keywords,
        "missing_keywords": [kw for kw in vacancy_keywords if kw.lower() not in document_lower],
        "action_verb_count": action_verb_count,
        "has_quantifiable_results": has_numbers
    }


def optimize_for_ats(document_text: str, vacancy_keywords: List[str], 
                     missing_keywords: List[str] = None) -> str:
    """
    Suggest optimizations to improve ATS score.
    
    Args:
        document_text: Current document text
        vacancy_keywords: Keywords from vacancy
        missing_keywords: Keywords not currently in document
        
    Returns:
        Optimized text (or suggestions if cannot auto-insert)
    """
    if missing_keywords is None:
        missing_keywords = [kw for kw in vacancy_keywords if kw.lower() not in document_text.lower()]
    
    # Return the original text with optimization suggestions
    # (Actual keyword injection should be done by LLM for natural flow)
    return document_text


def generate_ats_suggestions(document_text: str, vacancy_keywords: List[str]) -> List[str]:
    """
    Generate suggestions to improve ATS optimization.
    
    Args:
        document_text: Current document text
        vacancy_keywords: Keywords from vacancy
        
    Returns:
        List of suggestion strings
    """
    suggestions = []
    
    score_details = calculate_ats_score(document_text, vacancy_keywords)
    
    if score_details["keyword_coverage"] < 60:
        suggestions.append(
            f"Keyword coverage is {score_details['keyword_coverage']}%. "
            f"Consider incorporating more keywords from the vacancy."
        )
    
    if score_details["action_verb_count"] < 5:
        suggestions.append(
            "Use more action verbs (achieved, implemented, led, etc.) to strengthen impact."
        )
    
    if not score_details["has_quantifiable_results"]:
        suggestions.append(
            "Add quantifiable achievements (percentages, dollar amounts, metrics) where possible."
        )
    
    if score_details["missing_keywords"]:
        suggestions.append(
            f"Missing keywords: {', '.join(score_details['missing_keywords'][:5])}..."
        )
    
    return suggestions

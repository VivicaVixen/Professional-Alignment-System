"""
Tone classifier module.
Uses Qwen 2.5 Coder to suggest appropriate tone based on vacancy domain.
"""

from typing import Dict, Any
import pas_inference_client as ollama
from src.prompts.loader import load_prompt, get_model_name, build_messages


# Available tones with descriptions
AVAILABLE_TONES = {
    "corporate_executive": {
        "label": "Corporate / Executive",
        "description": "Formal, leadership-focused, strategic",
    },
    "technical_engineering": {
        "label": "Technical / Engineering",
        "description": "Skills-heavy, tool-oriented, technical depth",
    },
    "compliance_risk": {
        "label": "Compliance / Risk",
        "description": "Regulatory, audit-focused, detail-oriented",
    },
    "operations_projects": {
        "label": "Operations / Projects",
        "description": "Delivery-focused, metrics-driven, results-oriented",
    },
    "fintech_digital": {
        "label": "Fintech / Digital",
        "description": "Innovation, startup-style, modern",
    },
    "social_impact_mission": {
        "label": "Social Impact / Mission",
        "description": "Purpose-driven, values-focused, mission-oriented",
    },
}


# Domain to tone mapping
DOMAIN_TONE_MAP = {
    "fintech": "fintech_digital",
    "finance": "corporate_executive",
    "banking": "corporate_executive",
    "technology": "technical_engineering",
    "software": "technical_engineering",
    "engineering": "technical_engineering",
    "it": "technical_engineering",
    "compliance": "compliance_risk",
    "risk": "compliance_risk",
    "audit": "compliance_risk",
    "regulatory": "compliance_risk",
    "operations": "operations_projects",
    "projects": "operations_projects",
    "delivery": "operations_projects",
    "logistics": "operations_projects",
    "nonprofit": "social_impact_mission",
    "ngo": "social_impact_mission",
    "education": "social_impact_mission",
    "healthcare": "social_impact_mission",
    "marketing": "fintech_digital",
    "digital": "fintech_digital",
    "startup": "fintech_digital",
    "executive": "corporate_executive",
    "management": "corporate_executive",
    "leadership": "corporate_executive",
}


def classify_tone(vacancy_data: Dict[str, Any],
                  model_name: str = "qwen2.5-coder:7b",
                  base_url: str = "http://localhost:11434") -> str:
    """
    Suggest appropriate tone based on vacancy domain and content.

    Args:
        vacancy_data: Parsed vacancy data
        model_name: Ollama model name (overridden by config/prompts/tone_classify.yaml)
        base_url: Ollama API base URL

    Returns:
        Tone identifier string
    """
    domain = vacancy_data.get("domain", "").lower()
    for domain_key, tone in DOMAIN_TONE_MAP.items():
        if domain_key in domain:
            return tone

    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("tone_classify", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        job_title=vacancy_data.get("job_title", ""),
        domain=vacancy_data.get("domain", ""),
        keywords=", ".join(vacancy_data.get("keywords", [])),
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

        tone = response["message"]["content"].strip().lower()
        if tone in AVAILABLE_TONES:
            return tone
        return "technical_engineering"

    except Exception:
        return "technical_engineering"


def get_tone_description(tone: str) -> Dict[str, str]:
    """Get description for a tone."""
    return AVAILABLE_TONES.get(tone, {"label": "Custom", "description": "Custom tone"})


def get_all_tones() -> Dict[str, Dict[str, str]]:
    """Get all available tones with descriptions."""
    return AVAILABLE_TONES

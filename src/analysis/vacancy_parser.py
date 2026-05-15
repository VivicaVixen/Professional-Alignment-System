"""
Vacancy parser module.
Uses Qwen 2.5 Coder to parse job vacancy descriptions into structured data.
"""

import json
import sys
from typing import Dict, Any
import pas_inference_client as ollama
from pydantic import ValidationError
from src.models.schemas import VacancyData
from src.prompts.loader import load_prompt, get_model_name, build_messages


def parse_vacancy(vacancy_text: str, model_name: str = "qwen2.5-coder:7b",
                  base_url: str = "http://localhost:11434") -> Dict[str, Any]:
    """
    Parse a job vacancy description using Qwen 2.5 Coder.

    Args:
        vacancy_text: The job vacancy description text
        model_name: Ollama model name (overridden by config/prompts/vacancy_parse.yaml)
        base_url: Ollama API base URL

    Returns:
        Dictionary with parsed vacancy data
    """
    cfg = load_prompt("vacancy_parse")
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(cfg, vacancy_text=vacancy_text)

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
            vacancy = VacancyData.model_validate_json(content)
            return vacancy.model_dump()
        except ValidationError as ve:
            print(f"[VacancyData ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw LLM output]: {content}", file=sys.stderr)
            raise

    except Exception as e:
        return {
            "language": "en",
            "domain": "unknown",
            "seniority": "mid",
            "suggested_tone": "technical_engineering",
            "keywords": [],
            "responsibilities": [],
            "requirements": [],
            "company_info": "",
            "job_title": "",
            "parse_error": str(e),
        }


def extract_keywords_from_vacancy(vacancy_text: str, model_name: str = "qwen2.5-coder:7b",
                                   base_url: str = "http://localhost:11434") -> list:
    """
    Extract only keywords from a vacancy (lighter operation).

    Args:
        vacancy_text: The job vacancy description text
        model_name: Ollama model name (overridden by config/prompts/vacancy_keywords.yaml)
        base_url: Ollama API base URL

    Returns:
        List of keywords
    """
    cfg = load_prompt("vacancy_keywords")
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(cfg, vacancy_text=vacancy_text)

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

        keywords = json.loads(content)
        return keywords if isinstance(keywords, list) else []

    except Exception:
        return []

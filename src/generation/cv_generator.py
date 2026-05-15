"""
CV generator module.
Uses DeepSeek-R1 to generate tailored CV content.
"""

import json
import sys
from typing import Dict, List, Any, Callable, Optional
import pas_inference_client as ollama
from pydantic import ValidationError
from src.models.schemas import CVContent
from src.prompts.loader import load_prompt, get_model_name, build_messages
from src.orchestration.streaming import stream_ollama_chat


def generate_cv(profile_data: Dict[str, Any], vacancy_data: Dict[str, Any],
                strong_points: List[Dict[str, str]], tone: str = "technical_engineering",
                model_name: str = "deepseek-r1:7b",
                base_url: str = "http://localhost:11434",
                outline: str = "",
                on_chunk: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """
    Generate tailored CV content using DeepSeek-R1.

    Args:
        profile_data: User profile data
        vacancy_data: Parsed vacancy data
        strong_points: List of strong points from match engine
        tone: Communication tone for the CV
        model_name: Ollama model name (overridden by config/prompts/cv_generate.yaml)
        base_url: Ollama API base URL

    Returns:
        Dictionary with generated CV content
    """
    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("cv_generate", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        profile_data=json.dumps(profile_data, indent=2),
        vacancy_data=json.dumps(vacancy_data, indent=2),
        strong_points=json.dumps(strong_points, indent=2),
        tone=tone,
        outline=outline,
    )

    try:
        # T2.4: stream tokens as they arrive; on_chunk receives the cumulative
        # buffer so the UI can update a placeholder live.
        content = stream_ollama_chat(
            model=resolved_model,
            messages=messages,
            options={
                "temperature": cfg.temperature,
                "top_p": cfg.top_p,
                "num_predict": cfg.num_predict,
            },
            on_chunk=on_chunk,
        ).strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            cv = CVContent.model_validate_json(content)
            return cv.model_dump()
        except ValidationError as ve:
            print(f"[CVContent ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw LLM output]: {content}", file=sys.stderr)
            raise

    except Exception as e:
        return {
            "executive_summary": profile_data.get("summary", ""),
            "tailored_experience": profile_data.get("experience", []),
            "highlighted_skills": profile_data.get("skills", {}).get("technical", []),
            "ats_keywords": vacancy_data.get("keywords", []),
            "error": str(e),
        }


def generate_cv_summary(profile_data: Dict[str, Any], vacancy_data: Dict[str, Any],
                        strong_points: List[Dict[str, str]], tone: str = "technical_engineering",
                        model_name: str = "deepseek-r1:7b",
                        base_url: str = "http://localhost:11434") -> str:
    """
    Generate only the executive summary for a CV.

    Args:
        profile_data: User profile data
        vacancy_data: Parsed vacancy data
        strong_points: List of strong points from match engine
        tone: Communication tone
        model_name: Ollama model name (overridden by config/prompts/cv_summary.yaml)
        base_url: Ollama API base URL

    Returns:
        Executive summary text
    """
    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("cv_summary", lang=lang)
    resolved_model = get_model_name(cfg.model_role)

    personal_info = profile_data.get("personal_info", {})
    skills = profile_data.get("skills", {}).get("technical", [])
    requirements = vacancy_data.get("requirements", [])

    messages = build_messages(
        cfg,
        name=personal_info.get("name", "Candidate"),
        current_summary=profile_data.get("summary", "N/A"),
        experience_count=len(profile_data.get("experience", [])),
        top_skills=", ".join(skills[:10]),
        job_title=vacancy_data.get("job_title", "Position"),
        domain=vacancy_data.get("domain", "Industry"),
        requirements=", ".join(requirements[:5]),
        strong_points=json.dumps(strong_points, indent=2),
        tone=tone,
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
        return response["message"]["content"].strip()

    except Exception:
        return profile_data.get("summary", "")

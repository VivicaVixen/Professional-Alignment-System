"""
Cover letter generator module.
Uses DeepSeek-R1 to generate tailored cover letters.
"""

import json
import sys
from typing import Dict, List, Any, Callable, Optional
import pas_inference_client as ollama
from pydantic import ValidationError
from src.models.schemas import CoverLetter
from src.prompts.loader import load_prompt, get_model_name, build_messages
from src.orchestration.streaming import stream_ollama_chat


def generate_cover_letter(profile_data: Dict[str, Any], vacancy_data: Dict[str, Any],
                          strong_points: List[Dict[str, str]], tone: str = "technical_engineering",
                          model_name: str = "deepseek-r1:7b",
                          base_url: str = "http://localhost:11434",
                          paragraph_count: int = 4,
                          target_words: int = 320,
                          include_research_para: bool = False,
                          require_metric_para: bool = True,
                          outline: str = "",
                          on_chunk: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
    """
    Generate a tailored cover letter using DeepSeek-R1.

    Args:
        profile_data: User profile data
        vacancy_data: Parsed vacancy data
        strong_points: List of strong points from match engine
        tone: Communication tone
        model_name: Ollama model name (overridden by config/prompts/cover_letter_generate.yaml)
        base_url: Ollama API base URL
        paragraph_count: Number of paragraphs to generate (3–6, default 4)

    Returns:
        Dictionary with paragraphs, paragraph_intents, and rationale
    """
    paragraph_count = max(3, min(6, paragraph_count))

    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("cover_letter_generate", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        profile_data=json.dumps(profile_data, indent=2),
        vacancy_data=json.dumps(vacancy_data, indent=2),
        strong_points=json.dumps(strong_points, indent=2),
        tone=tone,
        paragraph_count=paragraph_count,
        target_words=target_words,
        include_research_para=include_research_para,
        require_metric_para=require_metric_para,
        outline=outline,
    )

    try:
        # T2.4: stream tokens as they arrive; UI placeholder updates live.
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
        content = _strip_markdown(content)

        try:
            letter = CoverLetter.model_validate_json(content)
        except ValidationError as ve:
            print(f"[CoverLetter ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw LLM output]: {content}", file=sys.stderr)
            raise

        # Retry once if paragraph count doesn't match
        if len(letter.paragraphs) != paragraph_count:
            print(
                f"[CoverLetter] Got {len(letter.paragraphs)} paragraphs, expected {paragraph_count}. Retrying.",
                file=sys.stderr,
            )
            corrective_messages = messages + [
                {"role": "assistant", "content": content},
                {
                    "role": "user",
                    "content": (
                        f"Your response contained {len(letter.paragraphs)} paragraphs but exactly "
                        f"{paragraph_count} are required. Rewrite the entire letter with exactly "
                        f"{paragraph_count} paragraphs. Return the same JSON structure."
                    ),
                },
            ]
            content2 = stream_ollama_chat(
                model=resolved_model,
                messages=corrective_messages,
                options={
                    "temperature": cfg.temperature,
                    "top_p": cfg.top_p,
                    "num_predict": cfg.num_predict,
                },
                on_chunk=on_chunk,
            ).strip()
            content2 = _strip_markdown(content2)
            try:
                letter = CoverLetter.model_validate_json(content2)
            except ValidationError as ve:
                print(f"[CoverLetter retry ValidationError]: {ve}", file=sys.stderr)
                print(f"[Raw retry output]: {content2}", file=sys.stderr)
                raise

        return letter.model_dump()

    except Exception as e:
        return {
            "paragraphs": generate_fallback_cover_letter(profile_data, vacancy_data),
            "paragraph_intents": [],
            "rationale": "",
            "error": str(e),
        }


def _strip_markdown(content: str) -> str:
    """Remove markdown code fences from LLM output."""
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


def generate_fallback_cover_letter(profile_data: Dict[str, Any],
                                   vacancy_data: Dict[str, Any]) -> List[str]:
    """
    Generate a basic fallback cover letter if LLM fails.

    Args:
        profile_data: User profile data
        vacancy_data: Parsed vacancy data

    Returns:
        List of paragraph strings
    """
    job_title = vacancy_data.get("job_title", "the position")
    company = vacancy_data.get("company_info", "your company")
    skills = profile_data.get("skills", {}).get("technical", [])
    experience = profile_data.get("experience", [])

    return [
        f"I am writing to express my strong interest in {job_title} at "
        f"{company if company else 'your organization'}. "
        f"With my background and expertise, I am confident that I would be a valuable addition to your team.",

        f"Throughout my career, I have developed extensive expertise in "
        f"{', '.join(skills[:5]) if skills else 'my field'}. "
        f"My professional experience has equipped me with the skills and knowledge necessary to excel in this role.",

        f"In my previous role{'s' if len(experience) > 1 else ''} as "
        f"{experience[0].get('title', 'professional') if experience else 'a professional'}"
        f"{' at ' + experience[0].get('company', '') if experience else ''}, "
        f"I successfully delivered results and contributed to key initiatives.",

        f"I am particularly drawn to this opportunity because of the alignment between my skills and "
        f"the requirements of the role. I am eager to bring my experience and dedication to your team.",

        f"Thank you for considering my application. I would welcome the opportunity to discuss how my "
        f"qualifications align with your needs. I look forward to the possibility of contributing to "
        f"your organization's success.",
    ]

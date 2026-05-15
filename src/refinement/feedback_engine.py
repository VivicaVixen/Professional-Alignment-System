"""
Feedback engine module.
Uses DeepSeek-R1 to rewrite document sections based on user feedback.
"""

import json
import sys
from typing import Dict, List, Any
import pas_inference_client as ollama
from pydantic import BaseModel, ValidationError
from src.models.schemas import RefinedSection, CoverLetter
from src.prompts.loader import load_prompt, get_model_name, build_messages


class _RefinedFullLetterResponse(BaseModel):
    """Internal model for full-letter refinement LLM response."""
    paragraphs: list[str]
    change_summary: str = ""


def _strip_markdown(content: str) -> str:
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


def refine_section(section_type: str, original_text: str, feedback: str,
                   vacancy_data: Dict[str, Any], tone: str = "technical_engineering",
                   model_name: str = "deepseek-r1:7b",
                   base_url: str = "http://localhost:11434",
                   paragraph_number: int = 1,
                   document_context: str = "") -> RefinedSection:
    """
    Refine a document section based on user feedback.

    Args:
        section_type: Type of section ("summary", "paragraph", "experience")
        original_text: Original text to revise
        feedback: User feedback/instructions
        vacancy_data: Parsed vacancy data
        tone: Communication tone
        model_name: Ollama model name (overridden by YAML config)
        base_url: Ollama API base URL
        paragraph_number: Paragraph number (for cover letter paragraphs)
        document_context: Sibling sections/paragraphs for coherence checking

    Returns:
        RefinedSection with revised_text and change_summary
    """
    vacancy_title = vacancy_data.get("job_title", "target position")
    vacancy_context = (
        f"Title: {vacancy_title}\n"
        f"Domain: {vacancy_data.get('domain', '')}\n"
        f"Keywords: {', '.join(vacancy_data.get('keywords', [])[:10])}"
    )
    lang = vacancy_data.get("language", "en")

    if section_type == "summary":
        cfg = load_prompt("refine_summary", lang=lang)
        resolved_model = get_model_name(cfg.model_role)
        messages = build_messages(
            cfg,
            original_text=original_text,
            feedback=feedback,
            vacancy_context=vacancy_context,
            document_context=document_context,
            tone=tone,
        )
    elif section_type == "paragraph":
        cfg = load_prompt("refine_paragraph", lang=lang)
        resolved_model = get_model_name(cfg.model_role)
        messages = build_messages(
            cfg,
            original_text=original_text,
            feedback=feedback,
            vacancy_context=f"{vacancy_context}\nParagraph number: {paragraph_number}",
            document_context=document_context,
            tone=tone,
        )
    elif section_type == "experience":
        cfg = load_prompt("refine_experience", lang=lang)
        resolved_model = get_model_name(cfg.model_role)
        messages = build_messages(
            cfg,
            original_text=original_text,
            feedback=feedback,
            vacancy_context=vacancy_context,
            document_context=document_context,
            tone=tone,
        )
    else:
        cfg = load_prompt("refine_summary", lang=lang)  # borrow model settings
        resolved_model = get_model_name(cfg.model_role)
        messages = [
            {"role": "user", "content": (
                f"Revise the following text based on user feedback.\n\n"
                f"ORIGINAL TEXT:\n{original_text}\n\nFEEDBACK:\n{feedback}\n\n"
                f'Return JSON: {{"revised_text": "<revised>", "change_summary": "<summary>"}}'
            )}
        ]

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

        content = _strip_markdown(response["message"]["content"].strip())

        try:
            section = RefinedSection.model_validate_json(content)
            return section
        except ValidationError as ve:
            print(f"[RefinedSection ValidationError] section_type={section_type}: {ve}", file=sys.stderr)
            print(f"[Raw LLM output]: {content}", file=sys.stderr)
            raise

    except Exception:
        return RefinedSection(revised_text=original_text, change_summary="Refinement failed; original preserved.")


def refine_cover_letter_paragraphs(paragraphs: List[str], feedback: str,
                                    section_index: int, vacancy_data: Dict[str, Any],
                                    tone: str = "technical_engineering",
                                    model_name: str = "deepseek-r1:7b",
                                    base_url: str = "http://localhost:11434") -> List[str]:
    """
    Refine a specific paragraph in a cover letter.

    Args:
        paragraphs: List of cover letter paragraphs
        feedback: User feedback
        section_index: Index of paragraph to refine
        vacancy_data: Parsed vacancy data
        tone: Communication tone
        model_name: Ollama model name (overridden by YAML config)
        base_url: Ollama API base URL

    Returns:
        Updated list of paragraphs (strings)
    """
    if section_index < 0 or section_index >= len(paragraphs):
        return paragraphs

    other_paragraphs = [
        f"Paragraph {i + 1}: {p}"
        for i, p in enumerate(paragraphs)
        if i != section_index
    ]
    document_context = "\n\n".join(other_paragraphs)

    result = refine_section(
        section_type="paragraph",
        original_text=paragraphs[section_index],
        feedback=feedback,
        vacancy_data=vacancy_data,
        tone=tone,
        model_name=model_name,
        base_url=base_url,
        paragraph_number=section_index + 1,
        document_context=document_context,
    )
    updated = list(paragraphs)
    updated[section_index] = result.revised_text
    return updated


def refine_full_cover_letter(letter: CoverLetter, feedback: str,
                              vacancy_data: Dict[str, Any],
                              tone: str = "technical_engineering",
                              model_name: str = "deepseek-r1:7b",
                              base_url: str = "http://localhost:11434") -> CoverLetter:
    """
    Refine an entire cover letter in one pass using refine_full_letter.yaml.

    Args:
        letter: Current CoverLetter
        feedback: User feedback for the whole letter
        vacancy_data: Parsed vacancy data
        tone: Communication tone
        model_name: Ollama model name (overridden by YAML config)
        base_url: Ollama API base URL

    Returns:
        Revised CoverLetter
    """
    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("refine_full_letter", lang=lang)
    resolved_model = get_model_name(cfg.model_role)

    original_letter = "\n\n".join(
        f"[Paragraph {i + 1}] {p}" for i, p in enumerate(letter.paragraphs)
    )
    vacancy_context = (
        f"Title: {vacancy_data.get('job_title', '')}\n"
        f"Domain: {vacancy_data.get('domain', '')}\n"
        f"Keywords: {', '.join(vacancy_data.get('keywords', [])[:10])}"
    )

    messages = build_messages(
        cfg,
        original_letter=original_letter,
        feedback=feedback,
        vacancy_context=vacancy_context,
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

        content = _strip_markdown(response["message"]["content"].strip())

        try:
            refined = _RefinedFullLetterResponse.model_validate_json(content)
        except ValidationError as ve:
            print(f"[RefinedFullLetter ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw LLM output]: {content}", file=sys.stderr)
            return letter

        return CoverLetter(
            paragraphs=refined.paragraphs,
            paragraph_intents=letter.paragraph_intents,
            rationale=refined.change_summary or letter.rationale,
        )

    except Exception:
        return letter


def batch_refine_sections(sections: Dict[str, Any], feedback_map: Dict[str, str],
                          vacancy_data: Dict[str, Any], tone: str) -> Dict[str, Any]:
    """
    Refine multiple sections based on a feedback map.

    Args:
        sections: Dictionary of section name -> content
        feedback_map: Dictionary of section name -> feedback
        vacancy_data: Parsed vacancy data
        tone: Communication tone

    Returns:
        Updated sections dictionary
    """
    refined = sections.copy()

    for section_name, feedback in feedback_map.items():
        if section_name in sections:
            if section_name == "executive_summary":
                result = refine_section(
                    "summary", sections[section_name], feedback, vacancy_data, tone
                )
                refined[section_name] = result.revised_text
            elif section_name.startswith("paragraph_"):
                pass  # Use refine_cover_letter_paragraphs instead
            elif section_name.startswith("experience_"):
                result = refine_section(
                    "experience", sections[section_name], feedback, vacancy_data, tone
                )
                refined[section_name] = result.revised_text

    return refined

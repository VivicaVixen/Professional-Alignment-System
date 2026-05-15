"""
Planning executors for T2.2.
Qwen produces a structured outline; DeepSeek uses it to draft the document.
"""

import json
import sys

import pas_inference_client as ollama
from pydantic import ValidationError

from src.models.schemas import CLOutline, CVOutline
from src.prompts.loader import load_prompt, get_model_name, build_messages


def _strip_markdown(content: str) -> str:
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


def exec_plan_cl_outline(ctx: dict) -> dict:
    """Plan a cover letter outline with Qwen before DeepSeek drafts."""
    profile_data = ctx["profile"]
    vacancy_data = ctx["vacancy_data"]
    strong_points = ctx.get("match_results", {}).get("strong_points", [])
    tone = ctx.get("selected_tone", "technical_engineering")
    paragraph_count = ctx.get("paragraph_count", 4)
    target_words = ctx.get("target_words", 320)
    include_research_para = ctx.get("include_research_para", False)
    require_metric_para = ctx.get("require_metric_para", True)

    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("plan_cl_outline", lang=lang)
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
            outline = CLOutline.model_validate_json(content)
            return {"cl_outline": outline.model_dump_json()}
        except ValidationError as ve:
            print(f"[CLOutline ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw CLOutline output]: {content}", file=sys.stderr)
            return {"cl_outline": ""}
    except Exception as exc:
        print(f"[plan_cl_outline] failed: {exc}", file=sys.stderr)
        return {"cl_outline": ""}


def exec_plan_cv_outline(ctx: dict) -> dict:
    """Plan a CV outline with Qwen before DeepSeek drafts."""
    profile_data = ctx["profile"]
    vacancy_data = ctx["vacancy_data"]
    strong_points = ctx.get("match_results", {}).get("strong_points", [])
    tone = ctx.get("selected_tone", "technical_engineering")

    lang = vacancy_data.get("language", "en")
    cfg = load_prompt("plan_cv_outline", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        profile_data=json.dumps(profile_data, indent=2),
        vacancy_data=json.dumps(vacancy_data, indent=2),
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
        content = _strip_markdown(response["message"]["content"].strip())
        try:
            outline = CVOutline.model_validate_json(content)
            return {"cv_outline": outline.model_dump_json()}
        except ValidationError as ve:
            print(f"[CVOutline ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw CVOutline output]: {content}", file=sys.stderr)
            return {"cv_outline": ""}
    except Exception as exc:
        print(f"[plan_cv_outline] failed: {exc}", file=sys.stderr)
        return {"cv_outline": ""}

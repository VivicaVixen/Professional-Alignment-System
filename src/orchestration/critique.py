"""
Critique and revise executors for T2.3.
Qwen critiques the draft; DeepSeek revises it only when issues are found.
"""

import json
import sys

import pas_inference_client as ollama
from pydantic import ValidationError

from src.models.schemas import Critique, CVContent, CoverLetter
from src.prompts.loader import load_prompt, get_model_name, build_messages
from src.orchestration.streaming import stream_ollama_chat


def _strip_markdown(content: str) -> str:
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


def exec_critique_cv(ctx: dict) -> dict:
    """Qwen audits the CV draft and returns a Critique with overall_severity."""
    lang = ctx.get("vacancy_data", {}).get("language", "en")
    cfg = load_prompt("critique_cv", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        cv_content=json.dumps(ctx.get("cv_content", {}), indent=2),
        vacancy_data=json.dumps(ctx.get("vacancy_data", {}), indent=2),
        outline=ctx.get("cv_outline", ""),
        strong_points=json.dumps(ctx.get("match_results", {}).get("strong_points", []), indent=2),
        tone=ctx.get("selected_tone", "technical_engineering"),
    )
    try:
        response = ollama.chat(
            model=resolved_model,
            messages=messages,
            options={"temperature": cfg.temperature, "top_p": cfg.top_p, "num_predict": cfg.num_predict},
        )
        content = _strip_markdown(response["message"]["content"].strip())
        try:
            critique = Critique.model_validate_json(content)
            return {
                "cv_critique": critique.model_dump_json(),
                "cv_critique_severity": critique.overall_severity,
            }
        except ValidationError as ve:
            print(f"[Critique CV ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw CV critique]: {content}", file=sys.stderr)
            return {"cv_critique": "", "cv_critique_severity": "none"}
    except Exception as exc:
        print(f"[exec_critique_cv] failed: {exc}", file=sys.stderr)
        return {"cv_critique": "", "cv_critique_severity": "none"}


def exec_critique_cl(ctx: dict) -> dict:
    """Qwen audits the cover letter draft and returns a Critique with overall_severity."""
    lang = ctx.get("vacancy_data", {}).get("language", "en")
    cfg = load_prompt("critique_cl", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        cl_content=json.dumps(ctx.get("cover_letter_content", {}), indent=2),
        vacancy_data=json.dumps(ctx.get("vacancy_data", {}), indent=2),
        outline=ctx.get("cl_outline", ""),
        strong_points=json.dumps(ctx.get("match_results", {}).get("strong_points", []), indent=2),
        tone=ctx.get("selected_tone", "technical_engineering"),
    )
    try:
        response = ollama.chat(
            model=resolved_model,
            messages=messages,
            options={"temperature": cfg.temperature, "top_p": cfg.top_p, "num_predict": cfg.num_predict},
        )
        content = _strip_markdown(response["message"]["content"].strip())
        try:
            critique = Critique.model_validate_json(content)
            return {
                "cl_critique": critique.model_dump_json(),
                "cl_critique_severity": critique.overall_severity,
            }
        except ValidationError as ve:
            print(f"[Critique CL ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw CL critique]: {content}", file=sys.stderr)
            return {"cl_critique": "", "cl_critique_severity": "none"}
    except Exception as exc:
        print(f"[exec_critique_cl] failed: {exc}", file=sys.stderr)
        return {"cl_critique": "", "cl_critique_severity": "none"}


def exec_revise_cv(ctx: dict) -> dict:
    """DeepSeek applies the Critique to produce a revised CV. Only runs when severity != 'none'."""
    original_cv = ctx.get("cv_content", {})
    lang = ctx.get("vacancy_data", {}).get("language", "en")
    cfg = load_prompt("revise_cv", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        original_cv=json.dumps(original_cv, indent=2),
        critique=ctx.get("cv_critique", ""),
        vacancy_data=json.dumps(ctx.get("vacancy_data", {}), indent=2),
        tone=ctx.get("selected_tone", "technical_engineering"),
    )
    on_chunk = ctx.get("on_chunk")
    try:
        # T2.4: stream the revision so the UI placeholder updates live.
        content = stream_ollama_chat(
            model=resolved_model,
            messages=messages,
            options={"temperature": cfg.temperature, "top_p": cfg.top_p, "num_predict": cfg.num_predict},
            on_chunk=on_chunk,
        ).strip()
        content = _strip_markdown(content)
        try:
            revised = CVContent.model_validate_json(content)
            return {"cv_content_revised": revised.model_dump()}
        except ValidationError as ve:
            print(f"[Revise CV ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw CV revise]: {content}", file=sys.stderr)
            return {"cv_content_revised": original_cv}
    except Exception as exc:
        print(f"[exec_revise_cv] failed: {exc}", file=sys.stderr)
        return {"cv_content_revised": original_cv}


def exec_revise_cl(ctx: dict) -> dict:
    """DeepSeek applies the Critique to produce a revised cover letter. Only runs when severity != 'none'."""
    original_cl = ctx.get("cover_letter_content", {})
    paragraph_count = ctx.get("paragraph_count", len(original_cl.get("paragraphs", [])) or 4)
    lang = ctx.get("vacancy_data", {}).get("language", "en")
    cfg = load_prompt("revise_cl", lang=lang)
    resolved_model = get_model_name(cfg.model_role)
    messages = build_messages(
        cfg,
        original_cl=json.dumps(original_cl, indent=2),
        critique=ctx.get("cl_critique", ""),
        vacancy_data=json.dumps(ctx.get("vacancy_data", {}), indent=2),
        tone=ctx.get("selected_tone", "technical_engineering"),
        paragraph_count=paragraph_count,
    )
    on_chunk = ctx.get("on_chunk")
    try:
        # T2.4: stream the revision so the UI placeholder updates live.
        content = stream_ollama_chat(
            model=resolved_model,
            messages=messages,
            options={"temperature": cfg.temperature, "top_p": cfg.top_p, "num_predict": cfg.num_predict},
            on_chunk=on_chunk,
        ).strip()
        content = _strip_markdown(content)
        try:
            revised = CoverLetter.model_validate_json(content)
            return {"cover_letter_content_revised": revised.model_dump()}
        except ValidationError as ve:
            print(f"[Revise CL ValidationError]: {ve}", file=sys.stderr)
            print(f"[Raw CL revise]: {content}", file=sys.stderr)
            return {"cover_letter_content_revised": original_cl}
    except Exception as exc:
        print(f"[exec_revise_cl] failed: {exc}", file=sys.stderr)
        return {"cover_letter_content_revised": original_cl}

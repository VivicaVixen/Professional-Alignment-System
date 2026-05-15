"""
Pipeline stage definitions. Each Stage wraps one LLM call with metadata.
"""

from dataclasses import dataclass, field
from typing import Callable, Literal, Optional


@dataclass
class Stage:
    name: str
    model_role: Literal["qwen", "deepseek"]
    prompt_name: str
    executor: Callable[[dict], dict]   # takes context, returns updates
    input_keys: list[str]
    output_keys: list[str]
    condition: Optional[Callable[[dict], bool]] = field(default=None)
    # If condition is set and returns False, the stage is skipped entirely.


# ---------------------------------------------------------------------------
# Executor functions — each pulls what it needs from ctx, returns updates
# ---------------------------------------------------------------------------

def _exec_parse_vacancy(ctx: dict) -> dict:
    from src.analysis.vacancy_parser import parse_vacancy
    result = parse_vacancy(ctx["vacancy_text"], ctx["qwen_model"], ctx["base_url"])
    return {"vacancy_data": result, "lang": result.get("language", "en")}


def _exec_match_profile(ctx: dict) -> dict:
    from src.analysis.match_engine import match_profile_to_vacancy
    result = match_profile_to_vacancy(
        ctx["vacancy_data"], ctx["profile"], ctx["qwen_model"], ctx["base_url"]
    )
    return {"match_results": result}


def _exec_classify_tone(ctx: dict) -> dict:
    from src.analysis.tone_classifier import classify_tone
    result = classify_tone(ctx["vacancy_data"], ctx["qwen_model"], ctx["base_url"])
    return {"selected_tone": result}


def _exec_plan_cv_outline(ctx: dict) -> dict:
    from src.orchestration.planning import exec_plan_cv_outline
    return exec_plan_cv_outline(ctx)


def _exec_plan_cl_outline(ctx: dict) -> dict:
    from src.orchestration.planning import exec_plan_cl_outline
    return exec_plan_cl_outline(ctx)


def _exec_draft_cv(ctx: dict) -> dict:
    from src.generation.cv_generator import generate_cv
    result = generate_cv(
        ctx["profile"],
        ctx["vacancy_data"],
        ctx.get("match_results", {}).get("strong_points", []),
        ctx.get("selected_tone", "technical_engineering"),
        ctx["deepseek_model"],
        ctx["base_url"],
        outline=ctx.get("cv_outline", ""),
        on_chunk=ctx.get("on_chunk"),
    )
    return {"cv_content": result}


def _exec_draft_cl(ctx: dict) -> dict:
    from src.generation.cover_letter_generator import generate_cover_letter
    result = generate_cover_letter(
        ctx["profile"],
        ctx["vacancy_data"],
        ctx.get("match_results", {}).get("strong_points", []),
        ctx.get("selected_tone", "technical_engineering"),
        ctx["deepseek_model"],
        ctx["base_url"],
        paragraph_count=ctx.get("paragraph_count", 4),
        target_words=ctx.get("target_words", 320),
        include_research_para=ctx.get("include_research_para", False),
        require_metric_para=ctx.get("require_metric_para", True),
        outline=ctx.get("cl_outline", ""),
        on_chunk=ctx.get("on_chunk"),
    )
    return {"cover_letter_content": result}


def _exec_critique_cv(ctx: dict) -> dict:
    from src.orchestration.critique import exec_critique_cv
    return exec_critique_cv(ctx)


def _exec_critique_cl(ctx: dict) -> dict:
    from src.orchestration.critique import exec_critique_cl
    return exec_critique_cl(ctx)


def _exec_revise_cv(ctx: dict) -> dict:
    from src.orchestration.critique import exec_revise_cv
    return exec_revise_cv(ctx)


def _exec_revise_cl(ctx: dict) -> dict:
    from src.orchestration.critique import exec_revise_cl
    return exec_revise_cl(ctx)


# ---------------------------------------------------------------------------
# Stage instances
# ---------------------------------------------------------------------------

STAGE_PARSE_VACANCY = Stage(
    name="parse_vacancy",
    model_role="qwen",
    prompt_name="vacancy_parse",
    executor=_exec_parse_vacancy,
    input_keys=["vacancy_text", "qwen_model", "base_url"],
    output_keys=["vacancy_data"],
)

STAGE_MATCH_PROFILE = Stage(
    name="match_profile",
    model_role="qwen",
    prompt_name="match",
    executor=_exec_match_profile,
    input_keys=["vacancy_data", "profile", "qwen_model", "base_url"],
    output_keys=["match_results"],
)

STAGE_CLASSIFY_TONE = Stage(
    name="classify_tone",
    model_role="qwen",
    prompt_name="tone_classify",
    executor=_exec_classify_tone,
    input_keys=["vacancy_data", "qwen_model", "base_url"],
    output_keys=["selected_tone"],
)

STAGE_PLAN_CV_OUTLINE = Stage(
    name="plan_cv_outline",
    model_role="qwen",
    prompt_name="plan_cv_outline",
    executor=_exec_plan_cv_outline,
    input_keys=["profile", "vacancy_data", "match_results", "selected_tone", "qwen_model", "base_url"],
    output_keys=["cv_outline"],
)

STAGE_PLAN_CL_OUTLINE = Stage(
    name="plan_cl_outline",
    model_role="qwen",
    prompt_name="plan_cl_outline",
    executor=_exec_plan_cl_outline,
    input_keys=["profile", "vacancy_data", "match_results", "selected_tone", "paragraph_count", "qwen_model", "base_url"],
    output_keys=["cl_outline"],
)

STAGE_DRAFT_CV = Stage(
    name="draft_cv",
    model_role="deepseek",
    prompt_name="cv_generate",
    executor=_exec_draft_cv,
    input_keys=["profile", "vacancy_data", "match_results", "selected_tone", "cv_outline", "deepseek_model", "base_url"],
    output_keys=["cv_content"],
)

STAGE_DRAFT_CL = Stage(
    name="draft_cl",
    model_role="deepseek",
    prompt_name="cover_letter_generate",
    executor=_exec_draft_cl,
    input_keys=["profile", "vacancy_data", "match_results", "selected_tone", "cl_outline", "deepseek_model", "base_url"],
    output_keys=["cover_letter_content"],
)

STAGE_CRITIQUE_CV = Stage(
    name="critique_cv",
    model_role="qwen",
    prompt_name="critique_cv",
    executor=_exec_critique_cv,
    input_keys=["cv_content", "vacancy_data", "cv_outline", "match_results", "selected_tone", "qwen_model", "base_url"],
    output_keys=["cv_critique", "cv_critique_severity"],
)

STAGE_CRITIQUE_CL = Stage(
    name="critique_cl",
    model_role="qwen",
    prompt_name="critique_cl",
    executor=_exec_critique_cl,
    input_keys=["cover_letter_content", "vacancy_data", "cl_outline", "match_results", "selected_tone", "qwen_model", "base_url"],
    output_keys=["cl_critique", "cl_critique_severity"],
)

STAGE_REVISE_CV = Stage(
    name="revise_cv",
    model_role="deepseek",
    prompt_name="revise_cv",
    executor=_exec_revise_cv,
    input_keys=["cv_content", "cv_critique", "vacancy_data", "selected_tone", "deepseek_model", "base_url"],
    output_keys=["cv_content_revised"],
    condition=lambda ctx: ctx.get("cv_critique_severity", "none") != "none",
)

STAGE_REVISE_CL = Stage(
    name="revise_cl",
    model_role="deepseek",
    prompt_name="revise_cl",
    executor=_exec_revise_cl,
    input_keys=["cover_letter_content", "cl_critique", "vacancy_data", "selected_tone", "deepseek_model", "base_url"],
    output_keys=["cover_letter_content_revised"],
    condition=lambda ctx: ctx.get("cl_critique_severity", "none") != "none",
)

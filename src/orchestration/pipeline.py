"""
Pipeline orchestrator. Runs named stages, captures per-stage telemetry,
and logs each completed stage as single-line JSON to stderr.
"""

import json
import sys
import time
from dataclasses import dataclass, field

from src.orchestration.stages import (
    Stage,
    STAGE_PARSE_VACANCY,
    STAGE_MATCH_PROFILE,
    STAGE_CLASSIFY_TONE,
    STAGE_PLAN_CV_OUTLINE,
    STAGE_PLAN_CL_OUTLINE,
    STAGE_DRAFT_CV,
    STAGE_DRAFT_CL,
    STAGE_CRITIQUE_CV,
    STAGE_CRITIQUE_CL,
    STAGE_REVISE_CV,
    STAGE_REVISE_CL,
)
from src.prompts.loader import load_prompt


@dataclass
class StageTelemetry:
    name: str
    model: str
    prompt_version: int
    input_tokens: int
    output_tokens: int
    latency_ms: int
    temperature: float
    success: bool


@dataclass
class PipelineResult:
    context: dict
    telemetry: list[StageTelemetry] = field(default_factory=list)


class Pipeline:
    def __init__(self, stages: list[Stage]):
        self.stages = stages

    def run(self, context: dict) -> PipelineResult:
        ctx = dict(context)
        telemetry: list[StageTelemetry] = []

        for stage in self.stages:
            # Evaluate condition — skip stage without logging if False
            if stage.condition is not None and not stage.condition(ctx):
                print(f"[pipeline] stage={stage.name} skipped", file=sys.stderr)
                continue

            prompt_version = 1
            temperature = 0.7
            try:
                _lang = ctx.get("lang", "en")
                cfg = load_prompt(stage.prompt_name, lang=_lang)
                prompt_version = cfg.version
                temperature = cfg.temperature
            except Exception:
                pass

            model_key = "qwen_model" if stage.model_role == "qwen" else "deepseek_model"
            model = ctx.get(model_key, stage.model_role)

            t_start = time.time()
            success = True
            try:
                updates = stage.executor(ctx)
                ctx.update(updates)
            except Exception as exc:
                success = False
                print(f"[pipeline] stage={stage.name} error={exc}", file=sys.stderr)

            latency_ms = int((time.time() - t_start) * 1000)

            entry = StageTelemetry(
                name=stage.name,
                model=model,
                prompt_version=prompt_version,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                temperature=temperature,
                success=success,
            )
            telemetry.append(entry)

            print(
                json.dumps({
                    "stage": stage.name,
                    "model": model,
                    "prompt_version": prompt_version,
                    "latency_ms": latency_ms,
                    "temperature": temperature,
                    "success": success,
                }),
                file=sys.stderr,
            )

        return PipelineResult(context=ctx, telemetry=telemetry)


# ---------------------------------------------------------------------------
# Preset pipelines
# ---------------------------------------------------------------------------

VACANCY_ANALYSIS_PIPELINE = Pipeline([
    STAGE_PARSE_VACANCY,
    STAGE_MATCH_PROFILE,
    STAGE_CLASSIFY_TONE,
])

CV_GENERATION_PIPELINE = Pipeline([
    STAGE_PLAN_CV_OUTLINE,
    STAGE_DRAFT_CV,
    STAGE_CRITIQUE_CV,
    STAGE_REVISE_CV,      # skipped when cv_critique_severity == "none"
])

CL_GENERATION_PIPELINE = Pipeline([
    STAGE_PLAN_CL_OUTLINE,
    STAGE_DRAFT_CL,
    STAGE_CRITIQUE_CL,
    STAGE_REVISE_CL,      # skipped when cl_critique_severity == "none"
])

# PAS Improvement Roadmap — Qwen Code Execution Plan

> **Audience:** Qwen Code (running inside VS Code) and the project owner.
> **Last updated:** 2026-04-26
> **Project:** Professional Alignment System (PAS)

---

## How to use this document

### For Qwen Code

This file is your **task queue**. Execute it strictly in order, one task at a time.

For each task:

1. Read the task block in full (Goal → Files Affected → Implementation Steps → User Verification).
2. Implement only the steps listed under **Implementation Steps**. Do not touch unrelated code.
3. After implementing, post a brief status report stating what you changed and which files were touched.
4. **HARD STOP.** Wait for the user to type `CONFIRMED <task-id>` (e.g. `CONFIRMED T1.2`) before starting the next task.
5. If verification fails, the user will type `FAILED <task-id> <notes>`. Re-attempt within the same task scope.
6. Do not skip ahead. Do not bundle tasks. Do not "while we're here" refactor.

If a task seems blocked or ambiguous, stop and ask the user before writing code.

### For the project owner

After Qwen reports a task complete, run the steps under **User Verification** for that task. Each step is a concrete, observable check you can do without writing code.

- All checks pass → reply `CONFIRMED <task-id>`.
- Anything fails → reply `FAILED <task-id>` and describe what you saw.

### Constraints that apply to every task

- **Local-only.** No cloud APIs. Ollama is the only LLM backend.
- **Dark theme is sacred.** The Obsidian Pro palette in `shared_styles.py` (CSS variables `--bg-base`, `--accent-primary`, etc.) must be preserved. No light-mode variants.
- **No new top-level dependencies** without flagging them in the implementation report.
- **Backward-compatible state.** Don't break `profile.json` schema or existing session state without a migration.
- **Models:** Qwen 2.5 Coder 7B = analysis/structured tasks. DeepSeek-R1 7B = generative/refinement tasks.

---

## Roadmap overview

| Stage | Theme | Tasks |
|-------|-------|-------|
| 1 | Foundation: schemas + prompt rework | T1.1 → T1.5 |
| 2 | Orchestration & model rebalancing | T2.1 → T2.5 |
| 3 | Refinement workflow improvements | T3.1 → T3.3 |
| 4 | Output reliability & i18n | T4.1 → T4.3 |
| 5 | Profile improvements | T5.1 |
| 6 | UI/UX polish (aesthetics last) | T6.1 → T6.6 |

Core / under-the-hood work is in Stages 1–4. Aesthetics live in Stage 6 by design.

---

# STAGE 1 — Foundation: schemas + prompt rework

Everything else depends on (a) reliable JSON contracts between the Python layer and the LLMs, and (b) prompts that live in editable config files. Do these first.

---

## T1.1 — Pydantic schemas for all LLM-produced JSON

**Goal:** Replace bare `json.loads` + manual key access with validated Pydantic models, so malformed LLM output fails loudly instead of silently degrading.

**Files Affected:**
- NEW: `src/models/__init__.py`
- NEW: `src/models/schemas.py`
- MODIFY: `src/analysis/vacancy_parser.py`
- MODIFY: `src/analysis/match_engine.py`
- MODIFY: `src/generation/cv_generator.py`
- MODIFY: `src/generation/cover_letter_generator.py`
- MODIFY: `src/refinement/feedback_engine.py`
- MODIFY: `requirements.txt` (add `pydantic>=2.5`)

**Implementation Steps:**

1. Add `pydantic>=2.5` to `requirements.txt`.
2. Create `src/models/schemas.py` with the following Pydantic models:
   - `VacancyData` (fields: `language`, `domain`, `seniority`, `suggested_tone`, `keywords: list[str]`, `responsibilities: list[str]`, `requirements: list[str]`, `company_info: dict`, `job_title`).
   - `MatchResult` (fields: `strong_points: list[StrongPoint]`, `gaps: list[str]`, `alignment_score: int`).
   - `StrongPoint` (fields: `vacancy_term`, `profile_evidence`, `rationale`).
   - `CVContent` (fields: `executive_summary: str`, `tailored_experience: list[ExperienceEntry]`, `highlighted_skills: list[str]`, `ats_keywords: list[str]`, `rationale: str | None`).
   - `ExperienceEntry` (fields: `title`, `company`, `start`, `end`, `achievements: list[str]`).
   - `CoverLetter` (fields: `paragraphs: list[str]`, `paragraph_intents: list[str] | None`, `rationale: str | None`).
   - `RefinedSection` (fields: `revised_text: str`, `change_summary: str | None`).
3. Replace each generator/parser's `json.loads` block with `Model.model_validate_json(...)`. On `ValidationError`, log the validation error AND the raw LLM output to stderr, then fall through to the existing fallback function.
4. Do not remove any existing fallback functions — only add validation in front of them.

**User Verification:**

1. Activate the venv and run `pip install -r requirements.txt`. Confirm `pydantic` installs.
2. Open `src/models/schemas.py` in VS Code and confirm 7 model classes exist.
3. Launch the app (`run.bat`). Walk through Phase 1 → Phase 2 → Phase 3 with a real vacancy. All phases complete without crashes.
4. In `src/generation/cover_letter_generator.py`, locate the new validation call. Confirm it references `CoverLetter.model_validate_json`.

**STOP. Await `CONFIRMED T1.1` before proceeding.**

---

## T1.2 — Externalize all prompts to YAML config

**Goal:** Move every embedded prompt string out of Python and into `config/prompts/*.yaml` so prompts are editable without code changes (preparing the ground for the future AI Settings UI in T6.1).

**Files Affected:**
- NEW: `config/prompts/` directory with one YAML per prompt
- NEW: `src/prompts/__init__.py`
- NEW: `src/prompts/loader.py`
- MODIFY: all files currently containing prompt constants (`vacancy_parser.py`, `match_engine.py`, `tone_classifier.py`, `cv_generator.py`, `cover_letter_generator.py`, `feedback_engine.py`)
- MODIFY: `requirements.txt` (add `pyyaml>=6.0` if not present)

**Implementation Steps:**

1. Create `config/prompts/` and add the following YAML files (one per existing prompt). The schema for each YAML is:
   ```yaml
   name: cover_letter_generate
   version: 1
   model_role: deepseek            # qwen | deepseek
   temperature: 0.7
   top_p: 0.9
   num_predict: 3072
   system: |
     <system prompt text>
   user: |
     <user prompt template with {placeholders}>
   ```
2. Files to create (use the existing prompt text verbatim for now — T1.3–T1.5 will rewrite them):
   - `vacancy_parse.yaml` (qwen, temp 0.3)
   - `vacancy_keywords.yaml` (qwen, temp 0.2)
   - `match.yaml` (qwen, temp 0.3)
   - `tone_classify.yaml` (qwen, temp 0.2)
   - `cv_generate.yaml` (deepseek, temp 0.7)
   - `cv_summary.yaml` (deepseek, temp 0.7)
   - `cover_letter_generate.yaml` (deepseek, temp 0.7)
   - `refine_summary.yaml` (deepseek, temp 0.7)
   - `refine_paragraph.yaml` (deepseek, temp 0.7)
   - `refine_experience.yaml` (deepseek, temp 0.7)
3. Create `src/prompts/loader.py` exposing:
   - `PromptConfig` Pydantic model matching the YAML schema.
   - `load_prompt(name: str) -> PromptConfig` — reads `config/prompts/{name}.yaml`, validates, caches.
   - `reload_prompts()` — clears cache (so edits to YAML take effect without restart).
4. In each generator/refinement module, replace the in-code prompt constants with `cfg = load_prompt('<name>')` and use `cfg.system` / `cfg.user.format(**vars)` / `cfg.temperature` / `cfg.num_predict`.
5. The model name still comes from `config/settings.json` (look up by `cfg.model_role`).

**User Verification:**

1. List `config/prompts/` — confirm 10 YAML files exist.
2. Open `config/prompts/cover_letter_generate.yaml` in VS Code. Edit one word in the `user` field (e.g., change "Generate" to "Write"). Save.
3. Run the app, go to Phase 3, generate a cover letter. The change should not crash anything (proves the YAML is being loaded).
4. Revert your edit. Re-generate. Confirm output back to baseline.
5. Grep the codebase for triple-quoted prompt-like strings in `src/`. Only acceptable matches are in `loader.py` itself or in fallback functions. The original `COVER_LETTER_PROMPT`, `CV_GENERATE_PROMPT`, etc. constants should no longer exist.

**STOP. Await `CONFIRMED T1.2` before proceeding.**

---

## T1.3 — Deep rework: CV generation prompt

**Goal:** Replace the generic CV generation prompt with a top-quality, structured prompt that produces measurably better output (richer action verbs, quantified results, stronger keyword coverage, ATS-optimized).

**Files Affected:**
- MODIFY: `config/prompts/cv_generate.yaml`
- MODIFY: `src/models/schemas.py` (add `rationale` and `keyword_coverage_notes` fields if missing)

**Implementation Steps:**

1. Rewrite `cv_generate.yaml` using XML-tagged sections in the user prompt for clarity:
   ```
   <role>...</role>
   <task>...</task>
   <inputs>
     <profile>{profile_data}</profile>
     <vacancy>{vacancy_data}</vacancy>
     <strong_points>{strong_points}</strong_points>
     <tone>{tone}</tone>
   </inputs>
   <rules>
     - Action verbs only (Led, Architected, Reduced, Shipped...)
     - Every achievement must include a metric or scope qualifier
     - Mirror vacancy keywords verbatim where the profile supports it
     - Never fabricate experience; if a vacancy keyword has no profile evidence, omit it
     - Tone: {tone} — match register and vocabulary
     - Length: executive_summary 80-120 words; each experience entry 3-5 bullets
   </rules>
   <output_schema>JSON matching CVContent</output_schema>
   <examples>
     <!-- 1-2 short few-shot exemplars -->
   </examples>
   ```
2. The system prompt should establish the persona: "You are a senior career strategist and ATS optimization expert who has placed candidates at Fortune 500 and high-growth tech firms."
3. Add a required `rationale` field in the JSON output (a short paragraph where the model explains the 3 most important framing choices it made — for debugging and future critique).
4. Bump the prompt's `version` field to `2`.
5. Update `CVContent` Pydantic model to require `rationale: str` (no longer optional).

**User Verification:**

1. Generate a CV for a real vacancy.
2. Inspect the JSON output (you can add a temporary debug print, or expand a Streamlit code block). Confirm:
   - `rationale` is present and reads coherently.
   - `tailored_experience` bullets contain action verbs (Led/Architected/Reduced/etc.).
   - Most bullets include a number or scope (`%`, `M`, `K`, dates, team size).
3. Compare against a CV you generated before T1.3 (mentally or via a saved copy). The new output should feel sharper.

**STOP. Await `CONFIRMED T1.3` before proceeding.**

---

## T1.4 — Deep rework: cover letter generation prompt

**Goal:** Replace the rigid 5-paragraph generation prompt with a top-quality, structured prompt that supports configurable paragraph count (3–6) and produces a coherent letter — not five disconnected blocks.

**Files Affected:**
- MODIFY: `config/prompts/cover_letter_generate.yaml`
- MODIFY: `src/models/schemas.py` (`CoverLetter` adjustments)
- MODIFY: `src/generation/cover_letter_generator.py` (accept `paragraph_count` param, default 4)

**Implementation Steps:**

1. Rewrite `cover_letter_generate.yaml` using the same XML-tagged structure as T1.3:
   - `<role>` — establish persona ("senior recruitment-side hiring manager who has read 10,000 cover letters").
   - `<inputs>` — profile, vacancy, strong_points, tone, plus a new `{paragraph_count}` variable (int between 3 and 6).
   - `<rules>` — explicit anti-cliché list ("Never start with 'I am writing to apply for'", "No 'I am excited' boilerplate", "No restating the job description"), specificity requirement, evidence requirement (every claim grounded in profile data), continuity requirement (paragraphs must reference each other or build a single argument).
   - `<paragraph_guidance>` — describe purpose of each paragraph as a function of count: with 3 paragraphs (intro+fit, evidence, close); with 4 (intro, fit, evidence, close); with 5 (intro, fit, achievements, culture/research, close); with 6 (intro, fit, achievements, research, motivation, close). The model picks intents based on `paragraph_count`.
   - `<output_schema>` — JSON: `{paragraphs: [...], paragraph_intents: [...], rationale: "..."}`. `paragraph_intents` is a string label per paragraph (e.g., "intro_hook", "fit", "evidence_metrics", "research", "cta").
2. Bump `version` to `2`.
3. In `cover_letter_generator.py`:
   - Add `paragraph_count: int = 4` parameter to `generate_cover_letter`.
   - Pass it to the prompt template.
   - Validate result via `CoverLetter.model_validate_json`. If returned `paragraphs` length doesn't match `paragraph_count`, retry once with an explicit corrective instruction injected.
4. `CoverLetter` model: make `paragraph_intents` required, `rationale` required.

**User Verification:**

1. Generate a cover letter (Phase 3). Confirm output is 4 paragraphs (the new default).
2. Read the letter end-to-end. It should flow as one argument, not five disconnected blocks. No "I am writing to apply for" opener.
3. In a Python REPL or temporary debug print, inspect `paragraph_intents` — confirm there are 4 labels and they match the paragraphs in spirit.
4. (Optional) Manually call `generate_cover_letter(..., paragraph_count=6)` from a scratch script and confirm 6 paragraphs come back.

**STOP. Await `CONFIRMED T1.4` before proceeding.**

---

## T1.5 — Deep rework: all refinement prompts

**Goal:** Refinement prompts must (a) never hallucinate new facts, (b) explain what they changed, (c) maintain coherence with the rest of the document. Add a new `refine_full_letter` prompt that Stage 3 will need.

**Files Affected:**
- MODIFY: `config/prompts/refine_summary.yaml`
- MODIFY: `config/prompts/refine_paragraph.yaml`
- MODIFY: `config/prompts/refine_experience.yaml`
- NEW: `config/prompts/refine_full_letter.yaml`
- MODIFY: `src/refinement/feedback_engine.py` (return type changes to use `RefinedSection`)
- MODIFY: `src/models/schemas.py` (`RefinedSection` already exists from T1.1)

**Implementation Steps:**

1. Each refinement prompt YAML uses the structure:
   ```
   <role>...</role>
   <task>Apply the user's feedback to the original text.</task>
   <inputs>
     <original>{original_text}</original>
     <user_feedback>{feedback}</user_feedback>
     <vacancy_context>{vacancy_context}</vacancy_context>
     <document_context>{document_context}</document_context>   <!-- siblings for coherence -->
     <tone>{tone}</tone>
   </inputs>
   <rules>
     - Apply the user's feedback faithfully
     - Do NOT introduce facts that are not in the original or in vacancy_context
     - Preserve any concrete numbers/dates/names from the original unless feedback explicitly says otherwise
     - Maintain coherence with sibling paragraphs / sections
     - Keep tone: {tone}
   </rules>
   <output_schema>
     JSON: {revised_text: "...", change_summary: "..."}
   </output_schema>
   ```
2. For paragraph refinement, `document_context` should contain the OTHER paragraphs (not the one being refined) so DeepSeek can avoid contradicting them.
3. Create `refine_full_letter.yaml`. Same structure but operates on the entire letter as one block. Output schema: `{paragraphs: [...], change_summary: "..."}`.
4. Update `feedback_engine.py` `refine_section` to:
   - Return `RefinedSection` instead of a bare string.
   - Use the new `document_context` field.
5. Add new function `refine_full_cover_letter(letter: CoverLetter, feedback: str, ...) -> CoverLetter` that uses `refine_full_letter.yaml`.
6. Bump versions of all refined prompts to `2`.

**User Verification:**

1. Generate a CL, then go to Phase 4 and refine paragraph 2 with a deliberate prompt: "Replace the metric in this paragraph with a different one."
2. After refinement, confirm in a debug print that `change_summary` is populated and reads coherently.
3. Re-read the refined paragraph 2 and the OTHER paragraphs — paragraph 2 should not contradict the others.
4. Try a hostile feedback: "Add a claim that I worked at Google for 10 years." The refined paragraph should NOT include this fabricated claim (the model should ignore unverifiable additions). If it does, this fails — the prompt's anti-hallucination rule needs strengthening.

**STOP. Await `CONFIRMED T1.5` before proceeding.**

---

# STAGE 2 — Orchestration & model rebalancing

Make the Qwen↔DeepSeek pipeline explicit, observable, and split the work so each model does what it's best at.

---

## T2.1 — Pipeline orchestration module

**Goal:** Replace ad-hoc function calls in `app.py` with an explicit `Pipeline` that runs named stages, logs each one, and makes the Qwen→DeepSeek handoff visible.

**Files Affected:**
- NEW: `src/orchestration/__init__.py`
- NEW: `src/orchestration/pipeline.py`
- NEW: `src/orchestration/stages.py`
- MODIFY: `ui/app.py` (Phase 2 and Phase 3 call sites)

**Implementation Steps:**

1. In `src/orchestration/stages.py` define a `Stage` dataclass:
   ```python
   @dataclass
   class Stage:
       name: str
       model_role: Literal["qwen", "deepseek"]
       prompt_name: str
       executor: Callable[[dict], dict]   # takes context, returns updates
       input_keys: list[str]              # keys it reads from context
       output_keys: list[str]             # keys it writes
   ```
2. In `src/orchestration/pipeline.py` define a `Pipeline` class:
   ```python
   class Pipeline:
       def __init__(self, stages: list[Stage]): ...
       def run(self, context: dict) -> PipelineResult: ...
   ```
   `PipelineResult` includes the final context plus a `telemetry` list (one entry per stage with: `name`, `model`, `prompt_version`, `input_tokens`, `output_tokens`, `latency_ms`, `temperature`, `success: bool`).
3. Define stages for the existing flow (no new behaviour yet — just wrap):
   - `parse_vacancy` (qwen)
   - `match_profile` (qwen)
   - `classify_tone` (qwen)
   - `draft_cv` (deepseek)
   - `draft_cl` (deepseek)
4. Define preset pipelines: `VACANCY_ANALYSIS_PIPELINE`, `CV_GENERATION_PIPELINE`, `CL_GENERATION_PIPELINE`.
5. In `ui/app.py`, replace direct function calls in Phase 2 and Phase 3 with `Pipeline.run(...)`. Store the returned `telemetry` list in `st.session_state.last_pipeline_telemetry`.
6. Print telemetry to stderr as each stage completes (single-line JSON, easy to grep).

**User Verification:**

1. Launch the app. Have the terminal visible.
2. Trigger Phase 2 (analyze vacancy). Confirm 3 lines appear in stderr, one per stage (`parse_vacancy`, `match_profile`, `classify_tone`), each showing the model name and a latency in milliseconds.
3. Trigger Phase 3 (generate CV and CL). Confirm 1 line per generation in stderr.
4. Functionally, Phase 2 and Phase 3 produce the same outputs as before T2.1 (no regressions).

**STOP. Await `CONFIRMED T2.1` before proceeding.**

---

## T2.2 — Qwen-based outline planning before DeepSeek drafts

**Goal:** Have Qwen produce a structured outline (paragraph intents, target keywords per paragraph, evidence to cite) that DeepSeek then turns into prose. This is the first real workload rebalancing.

**Files Affected:**
- NEW: `config/prompts/plan_cv_outline.yaml`
- NEW: `config/prompts/plan_cl_outline.yaml`
- NEW: `src/orchestration/planning.py`
- MODIFY: `src/orchestration/stages.py` (add `plan_cv_outline`, `plan_cl_outline` stages)
- MODIFY: `config/prompts/cv_generate.yaml` (accept new `{outline}` input)
- MODIFY: `config/prompts/cover_letter_generate.yaml` (accept new `{outline}` input)
- MODIFY: `src/models/schemas.py` (add `CVOutline`, `CLOutline`)

**Implementation Steps:**

1. Define `CLOutline` Pydantic model: `paragraph_count: int`, `paragraphs: list[ParagraphPlan]` where each `ParagraphPlan` has `intent: str`, `target_keywords: list[str]`, `evidence_refs: list[str]` (which strong_points or profile entries to draw from), `target_words: int`.
2. Same for `CVOutline`: outlines for `executive_summary` and `tailored_experience` sections.
3. The planning prompts use Qwen (`model_role: qwen`, `temperature: 0.3`). They take `profile`, `vacancy`, `strong_points`, `tone`, `paragraph_count` and produce the outline JSON.
4. Update `cv_generate.yaml` and `cover_letter_generate.yaml` to accept an `{outline}` input under `<inputs>` and a new rule: "Follow the outline exactly. Each paragraph must hit its `target_keywords` and use its `evidence_refs`."
5. Insert `plan_cv_outline` before `draft_cv` and `plan_cl_outline` before `draft_cl` in the corresponding pipelines.

**User Verification:**

1. Generate a cover letter. Watch stderr — confirm `plan_cl_outline` (qwen) runs before `draft_cl` (deepseek).
2. Briefly inspect the outline (add a debug print of the planning stage output, or expose it in a Streamlit expander temporarily). It should list one plan per paragraph with target keywords.
3. Read the resulting cover letter — keyword coverage should be measurably better (count: how many of `vacancy.keywords` appear at least once?). Compared to a pre-T2.2 generation, more should be present.

**STOP. Await `CONFIRMED T2.2` before proceeding.**

---

## T2.3 — Critique-revise loop (Qwen critiques, DeepSeek revises)

**Goal:** After DeepSeek drafts, Qwen audits the draft against the vacancy and outline, returns structured issues, and DeepSeek does one revision pass.

**Files Affected:**
- NEW: `config/prompts/critique_cv.yaml`
- NEW: `config/prompts/critique_cl.yaml`
- NEW: `config/prompts/revise_cv.yaml`
- NEW: `config/prompts/revise_cl.yaml`
- MODIFY: `src/orchestration/stages.py`
- MODIFY: `src/models/schemas.py` (add `Critique`)
- MODIFY: `ui/app.py` Phase 3 (toggle to view original vs revised)

**Implementation Steps:**

1. `Critique` Pydantic model: `missing_keywords: list[str]`, `weak_paragraphs: list[WeaknessNote]`, `tone_drift: list[str]`, `ats_issues: list[str]`, `factual_concerns: list[str]`, `overall_severity: Literal["none","minor","major"]`.
2. `critique_cv.yaml` and `critique_cl.yaml` (qwen, temp 0.2) take the draft + vacancy + outline + strong_points and produce a `Critique`.
3. `revise_cv.yaml` and `revise_cl.yaml` (deepseek, temp 0.6) take the draft + critique and produce the revised document.
4. Pipeline logic: if `Critique.overall_severity` == `"none"`, skip the revise stage. Otherwise run revise once. Cap at 1 loop (do not re-critique the revision).
5. Store both `original_draft` and `revised_draft` in session state.
6. In Phase 3, add a toggle: "View: Original draft | Revised draft" (default Revised). Use the existing dark-theme styling — no new colors.

**User Verification:**

1. Generate a CL. Stderr should show stages: `plan_cl_outline` → `draft_cl` → `critique_cl` → (`revise_cl` or skipped).
2. The Phase 3 UI shows the toggle. Switching displays different text in the document area.
3. Look at the critique output (debug print or expand telemetry from T2.5). When severity is `major`, the revised draft should noticeably address the issues (e.g., previously missing keywords now appear).
4. Generate against a clearly-aligned profile/vacancy pair — severity should sometimes be `none`, in which case no revise stage runs (stderr confirms only 3 stages).

**STOP. Await `CONFIRMED T2.3` before proceeding.**

---

## T2.4 — Streaming responses for generation

**Goal:** Long generations feel snappy by streaming tokens to the UI.

**Files Affected:**
- MODIFY: `src/generation/cv_generator.py`
- MODIFY: `src/generation/cover_letter_generator.py`
- MODIFY: `ui/app.py` Phase 3 generation handlers

**Implementation Steps:**

1. Where `ollama.chat(...)` is used for the `draft_cv`, `draft_cl`, `revise_cv`, `revise_cl` stages, switch to `stream=True`.
2. Buffer the streamed tokens. Use Streamlit's `st.write_stream(generator)` to display the raw text incrementally in a placeholder.
3. After streaming completes, parse the buffered output as JSON and validate via Pydantic (this part doesn't change).
4. Keep the existing gradient progress bar visible above the streaming text — stream updates the placeholder, progress bar reflects pipeline-stage progress.
5. Streaming ONLY for generation/revision (long outputs). Keep planning, critique, parse, match as non-streaming (they're short).

**User Verification:**

1. Trigger Phase 3 → generate a CV. You should see text appearing live, character by character, instead of a frozen spinner.
2. Final document still renders correctly in the structured fields after streaming completes.
3. No visible flicker or lost characters.

**STOP. Await `CONFIRMED T2.4` before proceeding.**

---

## T2.5 — Per-stage telemetry panel

**Goal:** Surface the pipeline telemetry from T2.1 as an inspectable table in the UI.

**Files Affected:**
- MODIFY: `ui/app.py` (Phase 2 and Phase 3)
- MODIFY: `shared_styles.py` (only if a small CSS adjustment is needed for the table — preserve the dark theme)

**Implementation Steps:**

1. After each `Pipeline.run` in Phase 2 / Phase 3, render `st.expander("Pipeline telemetry", expanded=False)`.
2. Inside, render a table with columns: Stage, Model, Prompt Version, Input Tokens, Output Tokens, Latency (ms), Temperature, Status. One row per stage.
3. Use Streamlit's native dataframe styling — do not introduce a new chart library. If the dataframe doesn't honor the dark theme, add minimal CSS overrides in `shared_styles.py` using existing CSS vars only.
4. Keep the panel collapsed by default.

**User Verification:**

1. Trigger Phase 3 generation.
2. After it completes, scroll to find the "Pipeline telemetry" expander.
3. Expand it. Confirm a table with rows for every stage that ran.
4. Latency numbers look plausible (1–30 seconds for generation stages, sub-second for planning/critique).
5. Theme isn't broken — text still light on dark.

**STOP. Await `CONFIRMED T2.5` before proceeding.**

---

# STAGE 3 — Refinement workflow improvements

Address the user's #1 pain point: paragraph-by-paragraph refinement.

---

## T3.1 — Whole-document cover letter refinement

**Goal:** Add a "Refine Whole Letter" mode in Phase 4. Keep per-paragraph mode available.

**Files Affected:**
- MODIFY: `src/refinement/feedback_engine.py` (uses the `refine_full_letter.yaml` from T1.5)
- MODIFY: `ui/app.py` Phase 4

**Implementation Steps:**

1. The function `refine_full_cover_letter` already exists from T1.5. Verify it's wired to `refine_full_letter.yaml`.
2. In `phase_refinement` (`ui/app.py`), when the user is editing a cover letter, render two tabs (Streamlit `st.tabs(["Whole Letter", "By Paragraph"])`):
   - **Whole Letter tab:** read-only display of the joined letter (paragraphs concatenated with blank lines), feedback text area, "Refine Whole Letter" button. On click → call `refine_full_cover_letter(...)` → replace the entire `cover_letter_content`.
   - **By Paragraph tab:** existing behaviour, unchanged.
3. The tab switch must preserve session state — switching tabs doesn't clear the document.

**User Verification:**

1. Generate a CL in Phase 3. Move to Phase 4.
2. The cover letter section now has two tabs: "Whole Letter" and "By Paragraph".
3. In "Whole Letter", paste feedback like: "Tighten the whole letter and make the closing more confident."
4. Click "Refine Whole Letter". Wait for streaming. Verify:
   - All paragraphs were potentially edited (not just one).
   - The closing paragraph is more confident.
   - Length is shorter overall.
5. Switch to "By Paragraph" tab. Confirm individual paragraphs are still selectable and refinable as before.

**STOP. Await `CONFIRMED T3.1` before proceeding.**

---

## T3.2 — Revision history with diff view

**Goal:** Track every refinement and let the user see what changed and revert.

**Files Affected:**
- MODIFY: `ui/app.py` (session state + Phase 4)
- NEW: `src/refinement/diff_view.py`

**Implementation Steps:**

1. Add session state lists: `cover_letter_revisions: list[dict]`, `cv_revisions: list[dict]`. Each entry: `{timestamp, source: "draft|paragraph_refine|full_refine", content: <CoverLetter | CVContent>, change_summary: str | None}`.
2. Append on every successful refinement (and on initial draft).
3. In `src/refinement/diff_view.py`, expose `render_diff(text_before: str, text_after: str) -> str` that produces HTML with `<span class="diff-removed">` (red) and `<span class="diff-added">` (green) markup. Use Python's `difflib.ndiff` or `SequenceMatcher`.
4. Add CSS classes `diff-removed` and `diff-added` to `shared_styles.py` using existing CSS vars (`--error` for removed, `--success` for added). Background tinted, not text-tinted, for readability.
5. In Phase 4, add an expander "Revision history (n)" listing revisions newest-first with timestamp, source label, and short change_summary.
6. Each entry has a "View diff" button (renders diff vs the previous revision) and a "Revert to this version" button.

**User Verification:**

1. Generate a CL (revision 1).
2. Refine paragraph 2 with some feedback (revision 2).
3. Refine the whole letter with different feedback (revision 3).
4. Open "Revision history" — confirm 3 entries listed with timestamps.
5. Click "View diff" on revision 2 — see red/green highlighting in the dark theme.
6. Click "Revert to this version" on revision 1 — confirm the document state returns to the original draft.

**STOP. Await `CONFIRMED T3.2` before proceeding.**

---

## T3.3 — Configurable cover letter structure

**Goal:** Expose paragraph count, target word count, and optional sections as Phase 3 controls.

**Files Affected:**
- MODIFY: `ui/app.py` Phase 3
- MODIFY: `config/prompts/cover_letter_generate.yaml` (extra template variables)
- MODIFY: `config/prompts/plan_cl_outline.yaml`

**Implementation Steps:**

1. In Phase 3, before the "Generate Cover Letter" button, add a collapsible "Structure options" expander containing:
   - Paragraph count slider: 3–6, default 4.
   - Target total words: 200–450, default 320.
   - Checkbox: "Include explicit company-research paragraph" (default off).
   - Checkbox: "Require explicit metric paragraph" (default on).
2. Pass these as template variables to both the planning and generation prompts.
3. Update both YAMLs to honor these variables in their `<rules>` and `<paragraph_guidance>` sections.
4. Bump prompt versions.

**User Verification:**

1. Phase 3 → expand "Structure options". Set paragraph count = 3, target words = 220, both checkboxes off. Generate.
2. Confirm output is 3 paragraphs and feels concise (~220 words).
3. Re-generate with paragraph count = 6 and "Include company-research paragraph" on. Confirm 6 paragraphs and at least one explicitly references the company (mission, products, recent news).

**STOP. Await `CONFIRMED T3.3` before proceeding.**

---

# STAGE 4 — Output reliability & i18n

---

## T4.1 — DOCX export alongside PDF

**Goal:** Add Word document export as an editable fallback to PDF.

**Files Affected:**
- NEW: `src/export/docx_renderer.py`
- MODIFY: `ui/app.py` Phase 5
- MODIFY: `requirements.txt` (add `python-docx>=1.1`)

**Implementation Steps:**

1. Add `python-docx>=1.1` to requirements.txt.
2. In `src/export/docx_renderer.py`, expose:
   - `render_cv_docx(cv_content, profile, template_name, output_path) -> bool`
   - `render_cover_letter_docx(cl_content, profile, template_name, output_path) -> bool`
3. Implement three template flavors per document type, mirroring the HTML templates' visual hierarchy (heading sizes, accent colors approximated, section ordering). Aim for parity in content; visual perfection isn't required.
4. In Phase 5, before each export button, add a radio: "Format: PDF | DOCX". Wire the selected branch to the appropriate renderer.

**User Verification:**

1. Generate documents in Phase 3.
2. Phase 5 → select DOCX → export CV. A `.docx` appears in the `output/` directory.
3. Open it in Word or LibreOffice. Headings, sections, and content are present and readable.
4. Repeat for cover letter.
5. Switch back to PDF and export. Confirm PDF export still works (no regression).

**STOP. Await `CONFIRMED T4.1` before proceeding.**

---

## T4.2 — Multilingual prompt variants (English + Spanish)

**Goal:** Use Spanish prompts for Spanish vacancies. Currently always English regardless of vacancy language.

**Files Affected:**
- MODIFY: all `config/prompts/*.yaml`
- MODIFY: `src/prompts/loader.py`

**Implementation Steps:**

1. Extend the YAML schema to support `variants`:
   ```yaml
   name: cover_letter_generate
   version: 3
   model_role: deepseek
   temperature: 0.7
   variants:
     en:
       system: |
         <english system>
       user: |
         <english user template>
     es:
       system: |
         <spanish system>
       user: |
         <spanish user template>
   ```
2. Update `loader.py`: `load_prompt(name, lang="en")` returns the variant. Default `"en"`. Falls back to `"en"` if requested variant missing.
3. Translate every prompt to idiomatic Spanish (not literal). Maintain the XML-tagged structure.
4. In each call site, pass `lang=vacancy_data.language` (Qwen already detects this in Phase 2).

**User Verification:**

1. Paste a Spanish job description into Phase 2. Analyze.
2. Confirm `vacancy_data.language == "es"`.
3. Generate CV and CL. Output should be in idiomatic Spanish.
4. Regression: paste an English vacancy. Output stays English.

**STOP. Await `CONFIRMED T4.2` before proceeding.**

---

## T4.3 — Vacancy library

**Goal:** Save analyzed vacancies for reuse without re-running Qwen analysis.

**Files Affected:**
- NEW: `src/storage/vacancy_library.py`
- NEW: `data/vacancies/` (directory)
- MODIFY: `ui/app.py` Phase 2

**Implementation Steps:**

1. `vacancy_library.py` exposes:
   - `save_vacancy(slug, vacancy_data, match_results, raw_text) -> Path`
   - `list_vacancies() -> list[VacancySummary]` (slug, title, company, timestamp)
   - `load_vacancy(slug) -> dict` (returns vacancy_data + match_results, ready to drop into session state)
2. Slug derived from `job_title` + `company_info.name` + short hash (handle missing fields).
3. After a successful Phase 2 analysis, automatically save.
4. In Phase 2, above the input area, add "Recent vacancies" dropdown listing saved vacancies. Selecting one populates session state without any LLM calls.

**User Verification:**

1. Analyze a vacancy in Phase 2. Confirm a JSON appears in `data/vacancies/`.
2. Restart the app. Phase 2 → "Recent vacancies" dropdown shows the analyzed one.
3. Select it. State populates instantly (no spinner, no terminal output of stages).
4. Move to Phase 3 — generation works as if fresh analysis just ran.

**STOP. Await `CONFIRMED T4.3` before proceeding.**

---

# STAGE 5 — Profile improvements

---

## T5.1 — Profile editing: add new entries

**Goal:** Allow adding new experience, education, and skill entries from the UI (currently only existing entries are editable).

**Files Affected:**
- MODIFY: `ui/app.py` Phase 1
- MODIFY: `src/profile/merger.py` (only if needed for entry validation)

**Implementation Steps:**

1. Under each of `experience`, `education`, `skills` sections in Phase 1, add an "Add entry" button. Click opens an inline form (Streamlit form with appropriate fields per entry type).
2. On submit, append to `profile.json` and rerun.
3. Add a delete button per entry (icon-style, fits dark theme).
4. Validate via Pydantic models if the profile has a schema; otherwise add minimal validation (non-empty title/company for experience, etc.).

**User Verification:**

1. Phase 1 → click "Add experience". Fill: title="Test Engineer", company="Acme Corp", start="2020-01", end="2021-12", achievements=["Achievement A", "Achievement B"]. Save.
2. The new entry appears in the profile.
3. Restart the app. The entry persists (open `profile.json` to confirm).
4. Click delete on the new entry. Restart. Entry is gone.
5. Repeat for education and skills.

**STOP. Await `CONFIRMED T5.1` before proceeding.**

---

# STAGE 6 — UI/UX polish (aesthetics last)

The dark theme is preserved throughout. All new colors must come from existing CSS variables in `shared_styles.py`.

---

## T6.1 — AI Settings panel (bottom-left of sidebar)

**Goal:** Expose prompt editing through the UI. This is what T1.2 and T1.5 prepared the ground for.

**Files Affected:**
- NEW: `ui/ai_settings.py` (new screen module)
- MODIFY: `ui/app.py` (sidebar)
- MODIFY: `src/prompts/loader.py` (add `save_prompt`, `reset_prompt_to_default`)
- NEW: `config/prompts/_defaults/` (mirror of original prompt YAMLs at install time, never overwritten)

**Implementation Steps:**

1. On first launch, copy `config/prompts/*.yaml` into `config/prompts/_defaults/` if not already present (safe defaults snapshot).
2. Add `save_prompt(config: PromptConfig)` — writes to `config/prompts/{name}.yaml`, creates a `.bak` of the previous version with timestamp.
3. Add `reset_prompt_to_default(name)` — copies from `_defaults/`.
4. In `ui/app.py` sidebar, below the phase selector and above the Exit button, add a button "AI Settings". Clicking sets a session_state flag that routes the main pane to `ui/ai_settings.py:render()` instead of the phase pages.
5. `ai_settings.py:render()` displays:
   - List of prompts (from `config/prompts/`).
   - Selecting one loads its YAML into editable fields: model_role (read-only), temperature (slider), top_p (slider), num_predict (slider), system (text area), user (text area), variants (collapsible).
   - "Save" button → `save_prompt(...)` → toast confirmation.
   - "Reset to default" → `reset_prompt_to_default(...)` → reload editor.
   - "Back to phases" button.
6. All styling uses existing CSS vars. No new colors.

**User Verification:**

1. Launch app. Sidebar shows new "AI Settings" entry near the bottom-left.
2. Click it. Main pane switches to the prompt editor.
3. Select `cover_letter_generate`. Edit one word in the user prompt. Click Save.
4. Click "Back to phases". Go to Phase 3, generate a CL. Confirm the change took effect.
5. Return to AI Settings → click "Reset to default" on `cover_letter_generate`. Re-generate. Output back to baseline.
6. Inspect `config/prompts/` — there's a timestamped `.bak` of your edited version.

**STOP. Await `CONFIRMED T6.1` before proceeding.**

---

## T6.2 — Horizontal stepper navigation

**Goal:** Replace the radio-button phase selector with a horizontal stepper at the top of each page.

**Files Affected:**
- MODIFY: `ui/app.py` (sidebar + main render)
- MODIFY: `shared_styles.py` (new component CSS using existing variables)

**Implementation Steps:**

1. Build a stepper component as injected HTML/CSS at the top of the main pane: 5 numbered circles connected by horizontal lines.
2. Current phase: filled with the existing accent gradient. Completed phases: checkmark, `--success` border. Upcoming: `--text-secondary` muted.
3. Each circle is clickable (form post → set phase in session state). Disallow jumping to phases whose preconditions aren't met (warn instead).
4. Keep the radio in the sidebar as a fallback or remove it — your call, but only one source of truth for phase state.

**User Verification:**

1. Launch app. Top of main pane shows the horizontal stepper with 5 numbered nodes.
2. Phase 1 is highlighted, others muted.
3. Complete Phase 1. The "1" node now shows a checkmark. Phase 2 highlighted.
4. Click "1" again — navigates back to Phase 1.
5. Try clicking Phase 4 from Phase 1 (no profile, no vacancy) — either disabled or shows a warning.
6. Theme is intact — colors all from existing palette.

**STOP. Await `CONFIRMED T6.2` before proceeding.**

---

## T6.3 — Two-pane layout in Phase 3 and Phase 4

**Goal:** 60/40 split — document on the left (always visible), controls on the right.

**Files Affected:**
- MODIFY: `ui/app.py` Phase 3 and Phase 4

**Implementation Steps:**

1. Wrap Phase 3 main content in `st.columns([3, 2])`. Left column: rendered document (CV summary, then experience entries; or all CL paragraphs as joined text). Right column: tone selector, structure options, generate button, telemetry panel.
2. Same for Phase 4: left column shows the document, right column hosts the refinement controls (tabs, feedback, buttons, revision history).
3. On narrow viewports the columns will stack — that's acceptable; T6.6 handles it more deliberately.

**User Verification:**

1. Phase 3 displays as two side-by-side columns.
2. Generate a CV. Document fills the left column. Controls remain accessible on the right.
3. Phase 4 looks the same way. Refining a paragraph updates the left pane in place.
4. Theme intact.

**STOP. Await `CONFIRMED T6.3` before proceeding.**

---

## T6.4 — Live template preview in Phase 3

**Goal:** Surface the three templates (Executive / Modern / Technical) as small thumbnails earlier in the flow with live preview.

**Files Affected:**
- MODIFY: `ui/app.py` Phase 3
- NEW: small CSS thumbnails (in `shared_styles.py`)

**Implementation Steps:**

1. Above the document area in Phase 3, render three thumbnail cards (CSS-only, 120x160 px each) representing the three template aesthetics. The selected one has the accent border.
2. Selecting a thumbnail updates a `selected_template` session state variable, which Phase 5 picks up automatically (no need to reselect there).
3. Optionally render a scaled-down live HTML preview below the thumbnails when a generated document exists. Use `st.components.v1.html` with the Jinja-rendered template at 50% scale. Cap height to keep the page navigable.

**User Verification:**

1. Phase 3 shows three template thumbnails above the document.
2. The selected one is highlighted with the accent border.
3. Click a different one — the live preview (if rendered) updates to reflect that template.
4. Move to Phase 5 — the selected template is pre-chosen in the export dropdown.

**STOP. Await `CONFIRMED T6.4` before proceeding.**

---

## T6.5 — ATS keyword chips with hit/miss indicators

**Goal:** Visualize which vacancy keywords appear in the generated document.

**Files Affected:**
- MODIFY: `ui/app.py` Phase 3 and Phase 4
- MODIFY: `shared_styles.py` (chip styles)

**Implementation Steps:**

1. Above the document in Phase 3 and Phase 4, render a row of chips — one per vacancy keyword.
2. Color logic (case-insensitive substring match across the joined document text):
   - `--success` border + tinted bg: keyword appears ≥2 times.
   - amber-tinted (use `--warning` if it exists, else create one from existing palette): keyword appears exactly 1 time.
   - `--error` border + tinted bg: keyword absent.
3. On hover, show the count.
4. Recompute after every generation/refinement.
5. All colors from existing CSS vars.

**User Verification:**

1. Generate a CL. Keywords from the vacancy appear as chips above the document.
2. Manually count one keyword's occurrences in the doc; chip color matches the rule.
3. Refine to add a previously missing keyword. After refinement, that chip turns amber or green.
4. Theme intact.

**STOP. Await `CONFIRMED T6.5` before proceeding.**

---

## T6.6 — Mobile/narrow layout

**Goal:** Single-column fallback below ~900px so the app remains usable in narrow windows.

**Files Affected:**
- MODIFY: `shared_styles.py` (media queries)

**Implementation Steps:**

1. Add CSS media queries for `max-width: 900px`:
   - Two-pane columns collapse to single column (Streamlit columns natively stack — verify and force where needed).
   - Sidebar collapses to a hamburger toggle if Streamlit allows; otherwise reduce its visual footprint.
   - Stepper from T6.2 reduces to numbers only (no text labels).
   - Chips from T6.5 wrap onto multiple lines.
2. Test in browser dev tools at 375px, 768px, 900px, 1280px.

**User Verification:**

1. Launch app. Resize the window narrow.
2. At ~750px wide, layout is single-column. All controls reachable.
3. Stepper still functional, just compact.
4. Chips wrap. No horizontal scrolling.
5. Resize back to wide. Two-pane returns.

**STOP. Await `CONFIRMED T6.6` before proceeding.**

---

# Done

When `CONFIRMED T6.6` is received, the roadmap is complete. Post a closing summary listing every task, its status, and any deferred items.

---

## Appendix — file/folder structure after the roadmap

```
PAS/
├── ui/
│   ├── app.py
│   └── ai_settings.py                  # NEW (T6.1)
├── src/
│   ├── models/                         # NEW (T1.1)
│   │   └── schemas.py
│   ├── prompts/                        # NEW (T1.2)
│   │   └── loader.py
│   ├── orchestration/                  # NEW (T2.1)
│   │   ├── pipeline.py
│   │   ├── stages.py
│   │   └── planning.py                 # NEW (T2.2)
│   ├── storage/                        # NEW (T4.3)
│   │   └── vacancy_library.py
│   ├── refinement/
│   │   ├── feedback_engine.py
│   │   └── diff_view.py                # NEW (T3.2)
│   ├── export/
│   │   ├── pdf_renderer.py
│   │   └── docx_renderer.py            # NEW (T4.1)
│   └── ... (existing analysis/, profile/, generation/)
├── config/
│   ├── settings.json
│   └── prompts/                        # NEW (T1.2)
│       ├── _defaults/                  # NEW (T6.1)
│       ├── vacancy_parse.yaml
│       ├── match.yaml
│       ├── tone_classify.yaml
│       ├── cv_generate.yaml
│       ├── cover_letter_generate.yaml
│       ├── plan_cv_outline.yaml        # NEW (T2.2)
│       ├── plan_cl_outline.yaml        # NEW (T2.2)
│       ├── critique_cv.yaml            # NEW (T2.3)
│       ├── critique_cl.yaml            # NEW (T2.3)
│       ├── revise_cv.yaml              # NEW (T2.3)
│       ├── revise_cl.yaml              # NEW (T2.3)
│       ├── refine_summary.yaml
│       ├── refine_paragraph.yaml
│       ├── refine_full_letter.yaml     # NEW (T1.5)
│       └── refine_experience.yaml
├── data/
│   └── vacancies/                      # NEW (T4.3)
└── ... (templates/, requirements.txt, run.bat, profile.json, shared_styles.py)
```

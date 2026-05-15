"""
T6.1 — AI Settings panel.
Exposes prompt YAML editing through the Streamlit UI.
All colours come from existing CSS variables in shared_styles.py (Obsidian Pro palette).
"""

import sys
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.prompts.loader import (
    PromptConfig,
    PromptVariant,
    list_prompt_names,
    load_prompt,
    reset_prompt_to_default,
    save_prompt,
)

PROMPTS_DIR = BASE_DIR / "config" / "prompts"
DEFAULTS_DIR = PROMPTS_DIR / "_defaults"


def _ensure_defaults_snapshot() -> None:
    """Copy all current YAMLs into _defaults/ if not already present."""
    import shutil
    DEFAULTS_DIR.mkdir(parents=True, exist_ok=True)
    for yaml_path in PROMPTS_DIR.glob("*.yaml"):
        if yaml_path.stem.startswith("_"):
            continue
        target = DEFAULTS_DIR / yaml_path.name
        if not target.exists():
            shutil.copy2(yaml_path, target)


def _section_header(text: str) -> None:
    st.markdown(
        f'<div style="font-size:10px;font-weight:500;text-transform:uppercase;'
        f'letter-spacing:0.1em;color:var(--text-muted,#6B6B8A);margin:16px 0 8px;">'
        f"{text}</div>",
        unsafe_allow_html=True,
    )


def _load_raw_config(name: str) -> PromptConfig:
    """Load without language-variant merging so we can edit each variant separately."""
    import yaml
    path = PROMPTS_DIR / f"{name}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return PromptConfig.model_validate(data)


def render() -> None:
    """Main render function — called from app.py when show_ai_settings is True."""
    _ensure_defaults_snapshot()

    # ── Header ──────────────────────────────────────────────────────────────
    col_title, col_back = st.columns([5, 1])
    with col_title:
        st.markdown("## AI Settings")
        st.markdown(
            '<p style="color:var(--text-muted,#6B6B8A);font-size:13px;margin-top:-12px;">'
            "Edit prompt templates. Changes take effect on the next generation run.</p>",
            unsafe_allow_html=True,
        )
    with col_back:
        st.markdown("<div style='padding-top:18px;'>", unsafe_allow_html=True)
        if st.button("← Back", key="ais_back_btn", use_container_width=True):
            st.session_state.show_ai_settings = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<hr style="border:none;border-top:1px solid #1E1E2E;margin:8px 0 20px;">',
        unsafe_allow_html=True,
    )

    # ── Prompt selector ──────────────────────────────────────────────────────
    prompt_names = list_prompt_names()
    if not prompt_names:
        st.warning("No prompt YAML files found in config/prompts/.")
        return

    if "ais_selected_prompt" not in st.session_state:
        st.session_state.ais_selected_prompt = prompt_names[0]

    selected = st.selectbox(
        "Select prompt",
        options=prompt_names,
        key="ais_selected_prompt",
        help="Choose a prompt template to view or edit.",
    )

    try:
        cfg = _load_raw_config(selected)
    except Exception as exc:
        st.error(f"Failed to load {selected}.yaml: {exc}")
        return

    st.markdown(
        f'<div style="font-size:11px;color:var(--text-muted,#6B6B8A);margin-bottom:16px;">'
        f"Model role: <b style='color:var(--accent-primary,#6C63FF);'>{cfg.model_role}</b>"
        f" &nbsp;·&nbsp; Version: <b>{cfg.version}</b></div>",
        unsafe_allow_html=True,
    )

    # ── Parameter sliders ────────────────────────────────────────────────────
    _section_header("Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_temperature = st.slider(
            "Temperature",
            min_value=0.0, max_value=1.0, step=0.05,
            value=float(cfg.temperature),
            key=f"ais_{selected}_temperature",
        )
    with col2:
        new_top_p = st.slider(
            "Top-p",
            min_value=0.0, max_value=1.0, step=0.05,
            value=float(cfg.top_p),
            key=f"ais_{selected}_top_p",
        )
    with col3:
        new_num_predict = st.number_input(
            "Max tokens",
            min_value=256, max_value=8192, step=256,
            value=int(cfg.num_predict),
            key=f"ais_{selected}_num_predict",
        )

    # ── Prompt text ──────────────────────────────────────────────────────────
    if cfg.variants:
        # Prompts with language variants — edit each variant separately
        _section_header("Prompt variants")
        new_variants: dict[str, PromptVariant] = {}
        for lang, variant in cfg.variants.items():
            with st.expander(f"Variant: {lang.upper()}", expanded=(lang == "en")):
                v_system = st.text_area(
                    "System",
                    value=variant.system or "",
                    height=160,
                    key=f"ais_{selected}_{lang}_system",
                )
                v_user = st.text_area(
                    "User template",
                    value=variant.user or "",
                    height=300,
                    key=f"ais_{selected}_{lang}_user",
                )
                new_variants[lang] = PromptVariant(system=v_system, user=v_user)
        new_system = cfg.system
        new_user = cfg.user
    else:
        # Simple prompts — edit top-level system/user directly
        _section_header("Prompt text")
        new_system = st.text_area(
            "System",
            value=cfg.system or "",
            height=160,
            key=f"ais_{selected}_system",
        )
        new_user = st.text_area(
            "User template",
            value=cfg.user or "",
            height=300,
            key=f"ais_{selected}_user",
        )
        new_variants = None

    # ── Action buttons ───────────────────────────────────────────────────────
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    btn_col1, btn_col2, btn_spacer = st.columns([1, 1, 4])

    with btn_col1:
        save_clicked = st.button(
            "Save", key="ais_save_btn", use_container_width=True, type="primary"
        )

    with btn_col2:
        reset_clicked = st.button(
            "Reset to default", key="ais_reset_btn", use_container_width=True
        )

    if save_clicked:
        updated = PromptConfig(
            name=cfg.name,
            version=cfg.version,
            model_role=cfg.model_role,
            temperature=new_temperature,
            top_p=new_top_p,
            num_predict=int(new_num_predict),
            system=new_system,
            user=new_user,
            variants=new_variants if new_variants else None,
        )
        try:
            save_prompt(updated)
            st.success(f"Saved — a backup of the previous version was written to config/prompts/.")
        except Exception as exc:
            st.error(f"Save failed: {exc}")

    if reset_clicked:
        if (DEFAULTS_DIR / f"{selected}.yaml").exists():
            try:
                reset_prompt_to_default(selected)
                st.success(f"'{selected}' reset to default. Reload the page to see the changes.")
            except Exception as exc:
                st.error(f"Reset failed: {exc}")
        else:
            st.warning(f"No default snapshot found for '{selected}'.")

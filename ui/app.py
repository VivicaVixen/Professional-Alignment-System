"""
PAS - Professional Alignment System
Main Streamlit Application
"""

import copy
import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# Import modules
from shared_styles import apply_dark_mode
from src.profile.pdf_ingest import ingest_pdf
from src.profile.csv_ingest import ingest_csv
from src.profile.text_ingest import ingest_text
from src.profile.merger import merge_profiles, save_profile, load_profile, create_empty_profile
from src.analysis.vacancy_parser import parse_vacancy
from src.analysis.match_engine import match_profile_to_vacancy, generate_strong_points_rule_based, identify_gaps_rule_based
from src.analysis.tone_classifier import classify_tone, get_all_tones, get_tone_description
from src.generation.cv_generator import generate_cv
from src.generation.cover_letter_generator import generate_cover_letter
from src.generation.ats_optimizer import calculate_ats_score, generate_ats_suggestions
from src.refinement.feedback_engine import refine_section, refine_cover_letter_paragraphs, refine_full_cover_letter
from src.refinement.diff_view import render_diff
from src.models.schemas import CoverLetter
from src.orchestration.pipeline import (
    VACANCY_ANALYSIS_PIPELINE,
    CV_GENERATION_PIPELINE,
    CL_GENERATION_PIPELINE,
)
from src.export.pdf_renderer import (
    generate_cv_pdf, generate_cover_letter_pdf,
    get_available_templates, render_cv_template, render_cover_letter_template
)
from src.export.docx_renderer import render_cv_docx, render_cover_letter_docx
from src.storage.vacancy_library import save_vacancy, list_vacancies, load_vacancy

sys.path.insert(0, str(Path(__file__).parent))
import ai_settings


# Configuration
BASE_DIR = Path(__file__).parent
PROFILE_PATH = BASE_DIR / "profile.json"
SETTINGS_PATH = BASE_DIR / "config" / "settings.json"


def load_settings() -> dict:
    """Load application settings."""
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "ollama": {
            "base_url": "http://localhost:8080",
            "models": {
                "qwen_coder": "qwen2.5-coder:7b",
                "deepseek": "deepseek-r1:7b"
            }
        }
    }


def check_ollama_connection(base_url: str) -> bool:
    """Check if llama-swap / llama.cpp inference server is running."""
    import requests
    try:
        response = requests.get(f"{base_url}/v1/models", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def initialize_session_state():
    """Initialize session state variables."""
    if "profile" not in st.session_state:
        st.session_state.profile = load_profile(str(PROFILE_PATH))
    if "vacancy_data" not in st.session_state:
        st.session_state.vacancy_data = {}
    if "match_results" not in st.session_state:
        st.session_state.match_results = {}
    if "cv_content" not in st.session_state:
        st.session_state.cv_content = {}
    if "cover_letter_content" not in st.session_state:
        st.session_state.cover_letter_content = {}
    if "selected_tone" not in st.session_state:
        st.session_state.selected_tone = "technical_engineering"
    if "current_phase" not in st.session_state:
        st.session_state.current_phase = 1
    if "last_pipeline_telemetry" not in st.session_state:
        st.session_state.last_pipeline_telemetry = []
    if "cv_original_draft" not in st.session_state:
        st.session_state.cv_original_draft = {}
    if "cv_revised_draft" not in st.session_state:
        st.session_state.cv_revised_draft = {}
    if "cover_letter_original_draft" not in st.session_state:
        st.session_state.cover_letter_original_draft = {}
    if "cover_letter_revised_draft" not in st.session_state:
        st.session_state.cover_letter_revised_draft = {}
    if "cv_is_revised" not in st.session_state:
        st.session_state.cv_is_revised = False
    if "cover_letter_is_revised" not in st.session_state:
        st.session_state.cover_letter_is_revised = False
    if "cv_critique_severity" not in st.session_state:
        st.session_state.cv_critique_severity = "none"
    if "cl_critique_severity" not in st.session_state:
        st.session_state.cl_critique_severity = "none"
    if "cv_revisions" not in st.session_state:
        st.session_state.cv_revisions = []
    if "cover_letter_revisions" not in st.session_state:
        st.session_state.cover_letter_revisions = []
    if "cv_viewing_diff" not in st.session_state:
        st.session_state.cv_viewing_diff = None
    if "cl_viewing_diff" not in st.session_state:
        st.session_state.cl_viewing_diff = None
    if "show_ai_settings" not in st.session_state:
        st.session_state.show_ai_settings = False
    if "selected_template" not in st.session_state:
        st.session_state.selected_template = "modern"


def render_phase_nav_buttons() -> None:
    """Render Previous/Next buttons at the bottom of each phase page."""
    current = st.session_state.get("current_phase", 1)
    precond = _phase_preconditions()

    st.markdown('<hr style="border:none;border-top:1px solid #1E1E2E;margin:32px 0 20px;">', unsafe_allow_html=True)
    col_prev, col_next, _ = st.columns([1, 1, 2])

    with col_prev:
        if current > 1:
            prev_label = _STEP_LABELS[current - 2]
            if st.button(f"← {prev_label}", use_container_width=True, key="nav_prev"):
                st.session_state.current_phase = current - 1
                st.session_state.show_ai_settings = False
                st.rerun()

    with col_next:
        if current < 5:
            next_phase = current + 1
            next_label = _STEP_LABELS[next_phase - 1]
            if precond.get(next_phase, False):
                if st.button(f"{next_label} →", use_container_width=True, type="primary", key="nav_next"):
                    st.session_state.current_phase = next_phase
                    st.session_state.show_ai_settings = False
                    st.rerun()
            else:
                st.button(f"{next_label} →", use_container_width=True, disabled=True, key="nav_next")


def render_pipeline_telemetry_panel() -> None:
    """T2.5: Inspectable per-stage telemetry table.

    Renders ``st.expander("Pipeline telemetry", expanded=False)`` populated
    with one row per ``StageTelemetry`` entry from
    ``st.session_state.last_pipeline_telemetry``. No-op when empty.

    Uses Streamlit's native dataframe so the dark theme defined in
    ``shared_styles.py`` (Obsidian Pro palette) applies without introducing a
    new charting/table library.
    """
    telemetry = st.session_state.get("last_pipeline_telemetry") or []
    if not telemetry:
        return

    rows = []
    for entry in telemetry:
        rows.append({
            "Stage": getattr(entry, "name", ""),
            "Model": getattr(entry, "model", ""),
            "Prompt Version": getattr(entry, "prompt_version", ""),
            "Input Tokens": getattr(entry, "input_tokens", 0),
            "Output Tokens": getattr(entry, "output_tokens", 0),
            "Latency (ms)": getattr(entry, "latency_ms", 0),
            "Temperature": getattr(entry, "temperature", 0.0),
            "Status": "ok" if getattr(entry, "success", False) else "error",
        })

    with st.expander("Pipeline telemetry", expanded=False):
        st.markdown(
            '<div style="font-size:11px;color:#6B6B8A;text-transform:uppercase;'
            'letter-spacing:0.08em;margin-bottom:8px;">'
            f'Last run · {len(rows)} stage{"s" if len(rows) != 1 else ""}'
            '</div>',
            unsafe_allow_html=True,
        )
        try:
            import pandas as pd
            df = pd.DataFrame(rows, columns=[
                "Stage",
                "Model",
                "Prompt Version",
                "Input Tokens",
                "Output Tokens",
                "Latency (ms)",
                "Temperature",
                "Status",
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        except ImportError:
            st.table(rows)


def render_revision_history(revisions: list, doc_type: str) -> None:
    """T3.2: Revision history expander with diff and revert.

    doc_type: "cv" or "cl"
    Each revision: {timestamp, source, content (dict), change_summary}
    """
    if not revisions:
        return

    n = len(revisions)
    viewing_diff_key = f"{doc_type}_viewing_diff"
    source_labels = {
        "draft": "Initial draft",
        "summary_refine": "Summary refined",
        "paragraph_refine": "Paragraph refined",
        "full_refine": "Whole letter refined",
    }

    with st.expander(f"Revision history ({n})", expanded=False):
        for i in range(n - 1, -1, -1):
            rev = revisions[i]
            is_current = i == n - 1
            source_label = source_labels.get(rev.get("source", ""), rev.get("source", ""))
            summary = rev.get("change_summary") or ""
            ts = rev.get("timestamp", "")

            current_badge = (
                ' &nbsp;<span style="color:#1D9E75;font-weight:600;">current</span>'
                if is_current else ""
            )
            st.markdown(
                f'<div style="font-size:12px;color:#6B6B8A;margin-bottom:4px;">'
                f'<span style="color:#9090CC;font-weight:600;">#{i + 1}</span>'
                f' &nbsp;·&nbsp; {ts}'
                f' &nbsp;·&nbsp; <span style="color:#6C63FF;">{source_label}</span>'
                f'{current_badge}</div>',
                unsafe_allow_html=True,
            )
            if summary:
                st.markdown(
                    f'<div style="font-size:12px;color:#9090CC;margin-bottom:6px;'
                    f'font-style:italic;">{summary}</div>',
                    unsafe_allow_html=True,
                )

            btn_col_diff, btn_col_revert, _ = st.columns([1, 1, 3])
            with btn_col_diff:
                if i > 0:
                    label = "Hide diff" if st.session_state.get(viewing_diff_key) == i else "View diff"
                    if st.button(label, key=f"{doc_type}_diff_{i}", use_container_width=True):
                        st.session_state[viewing_diff_key] = None if st.session_state.get(viewing_diff_key) == i else i
                        st.rerun()
            with btn_col_revert:
                if not is_current:
                    if st.button("Revert", key=f"{doc_type}_revert_{i}", use_container_width=True):
                        if doc_type == "cl":
                            st.session_state.cover_letter_content = copy.deepcopy(rev["content"])
                            st.session_state.cover_letter_revisions = revisions[: i + 1]
                        else:
                            st.session_state.cv_content = copy.deepcopy(rev["content"])
                            st.session_state.cv_revisions = revisions[: i + 1]
                        st.session_state[viewing_diff_key] = None
                        st.rerun()

            if st.session_state.get(viewing_diff_key) == i and i > 0:
                prev_c = revisions[i - 1]["content"]
                curr_c = rev["content"]
                if doc_type == "cl":
                    text_before = "\n\n".join(prev_c.get("paragraphs", []))
                    text_after = "\n\n".join(curr_c.get("paragraphs", []))
                else:
                    text_before = prev_c.get("executive_summary", "")
                    text_after = curr_c.get("executive_summary", "")
                diff_html = render_diff(text_before, text_after)
                st.markdown(
                    f'<div style="background:#111118;border:1px solid #1E1E2E;border-radius:6px;'
                    f'padding:14px;font-size:13px;line-height:1.7;margin-top:8px;">'
                    f'{diff_html}</div>',
                    unsafe_allow_html=True,
                )

            if i > 0:
                st.markdown(
                    '<hr style="border:none;border-top:1px solid #1E1E2E;margin:10px 0;">',
                    unsafe_allow_html=True,
                )


def phase_profile_creation():
    """Phase 1: Profile Creation"""
    st.markdown('<h1 style="font-size: 22px; font-weight: 600; color: #E0E0F0; border-bottom: 1px solid #1E1E2E; padding-bottom: 12px; margin-bottom: 24px;">Phase 1: Profile Creation</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 13px; color: #6B6B8A; margin-top: -16px; margin-bottom: 24px;">Upload your CV or source files to build your professional profile.</p>', unsafe_allow_html=True)
    
    # Check if profile already exists
    profile_exists = PROFILE_PATH.exists() and st.session_state.profile.get("personal_info", {}).get("name")
    
    if profile_exists:
        st.success(f"Profile loaded: {st.session_state.profile['personal_info']['name']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Edit Profile", use_container_width=True):
                st.session_state.edit_mode = True
        with col2:
            if st.button("Upload New Files", use_container_width=True):
                st.session_state.edit_mode = False
                st.session_state.show_upload = True
    
    if st.session_state.get('show_upload', False) or not profile_exists:
        st.subheader("Upload Source Files")
        st.markdown("Upload one or more files to build your profile. Supported formats: PDF, CSV, TXT")
        
        uploaded_files = st.file_uploader(
            "Upload files",
            type=['pdf', 'csv', 'txt'],
            accept_multiple_files=True,
            key="profile_uploader"
        )
        
        if uploaded_files:
            profiles = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded in enumerate(uploaded_files):
                status_text.text(f"Processing: {uploaded.name}")
                progress_bar.progress((i + 1) / len(uploaded_files))
                
                # Save uploaded file temporarily
                temp_path = BASE_DIR / "temp" / uploaded.name
                os.makedirs(BASE_DIR / "temp", exist_ok=True)
                
                with open(temp_path, 'wb') as f:
                    f.write(uploaded.getbuffer())
                
                # Ingest based on file type
                try:
                    if uploaded.name.endswith('.pdf'):
                        profile = ingest_pdf(str(temp_path))
                    elif uploaded.name.endswith('.csv'):
                        profile = ingest_csv(str(temp_path))
                    else:
                        profile = ingest_text(str(temp_path))
                    
                    profiles.append(profile)
                except Exception as e:
                    st.error(f"Error processing {uploaded.name}: {str(e)}")
                finally:
                    if temp_path.exists():
                        temp_path.unlink()
            
            status_text.text("Merging profiles...")
            
            if profiles:
                merged = merge_profiles(profiles)
                st.session_state.profile = merged
                save_profile(merged, str(PROFILE_PATH))
                st.success("Profile created successfully!")
                
                # Clean up temp directory
                temp_dir = BASE_DIR / "temp"
                if temp_dir.exists():
                    for f in temp_dir.iterdir():
                        f.unlink()
                    temp_dir.rmdir()
    
    # Profile editor
    if st.session_state.get('edit_mode', False) or not profile_exists:
        st.subheader("Edit Your Profile")
        
        profile = st.session_state.profile
        
        # Personal info
        st.markdown("### Personal Information")
        col1, col2 = st.columns(2)
        with col1:
            profile["personal_info"]["name"] = st.text_input(
                "Full Name", 
                value=profile.get("personal_info", {}).get("name", ""),
                key="edit_name"
            )
            profile["personal_info"]["email"] = st.text_input(
                "Email", 
                value=profile.get("personal_info", {}).get("email", ""),
                key="edit_email"
            )
            profile["personal_info"]["phone"] = st.text_input(
                "Phone", 
                value=profile.get("personal_info", {}).get("phone", ""),
                key="edit_phone"
            )
        with col2:
            profile["personal_info"]["location"] = st.text_input(
                "Location", 
                value=profile.get("personal_info", {}).get("location", ""),
                key="edit_location"
            )
            profile["personal_info"]["linkedin"] = st.text_input(
                "LinkedIn URL", 
                value=profile.get("personal_info", {}).get("linkedin", ""),
                key="edit_linkedin"
            )
            profile["personal_info"]["portfolio"] = st.text_input(
                "Portfolio URL", 
                value=profile.get("personal_info", {}).get("portfolio", ""),
                key="edit_portfolio"
            )
        
        # Summary
        st.markdown("### Professional Summary")
        profile["summary"] = st.text_area(
            "Summary", 
            value=profile.get("summary", ""),
            height=150,
            key="edit_summary"
        )
        
        # ── Experience ───────────────────────────────────────────────────────────
        st.markdown("### Experience")

        experience = profile.get("experience", [])
        for i, exp in enumerate(experience):
            with st.expander(
                f"{exp.get('title', 'Untitled')} · {exp.get('company', '')} "
                f"({exp.get('start', '')} – {exp.get('end', 'present')})",
                expanded=False,
            ):
                achievements = exp.get("achievements", [])
                if achievements:
                    for ach in achievements:
                        st.markdown(f"- {ach}")
                if st.button("Delete this entry", key=f"del_exp_{i}", type="secondary"):
                    profile["experience"].pop(i)
                    save_profile(profile, str(PROFILE_PATH))
                    st.session_state.profile = profile
                    st.rerun()

        if st.button("+ Add Experience", key="show_add_exp_btn"):
            st.session_state.show_add_exp = True

        if st.session_state.get("show_add_exp"):
            with st.form("add_exp_form", clear_on_submit=True):
                st.markdown("**New experience entry**")
                col_a, col_b = st.columns(2)
                with col_a:
                    new_title = st.text_input("Job title *", key="new_exp_title")
                    new_start = st.text_input("Start (e.g. 2020-01)", key="new_exp_start")
                with col_b:
                    new_company = st.text_input("Company *", key="new_exp_company")
                    new_end = st.text_input("End (leave blank for present)", key="new_exp_end")
                new_achievements_raw = st.text_area(
                    "Achievements (one per line)",
                    height=120,
                    key="new_exp_achievements",
                )
                col_submit, col_cancel = st.columns(2)
                submitted = col_submit.form_submit_button("Save Entry", type="primary")
                cancelled = col_cancel.form_submit_button("Cancel")

            if submitted:
                if not new_title or not new_company:
                    st.error("Job title and company are required.")
                else:
                    achievements = [
                        line.strip()
                        for line in new_achievements_raw.splitlines()
                        if line.strip()
                    ]
                    profile["experience"].append({
                        "title": new_title,
                        "company": new_company,
                        "start": new_start,
                        "end": new_end,
                        "achievements": achievements,
                    })
                    save_profile(profile, str(PROFILE_PATH))
                    st.session_state.profile = profile
                    st.session_state.show_add_exp = False
                    st.rerun()
            if cancelled:
                st.session_state.show_add_exp = False
                st.rerun()

        # ── Education ─────────────────────────────────────────────────────────
        st.markdown("### Education")

        education = profile.get("education", [])
        for i, edu in enumerate(education):
            with st.expander(
                f"{edu.get('degree', 'Degree')} · {edu.get('institution', '')} ({edu.get('year', '')})",
                expanded=False,
            ):
                if st.button("Delete this entry", key=f"del_edu_{i}", type="secondary"):
                    profile["education"].pop(i)
                    save_profile(profile, str(PROFILE_PATH))
                    st.session_state.profile = profile
                    st.rerun()

        if st.button("+ Add Education", key="show_add_edu_btn"):
            st.session_state.show_add_edu = True

        if st.session_state.get("show_add_edu"):
            with st.form("add_edu_form", clear_on_submit=True):
                st.markdown("**New education entry**")
                col_a, col_b = st.columns(2)
                with col_a:
                    new_degree = st.text_input("Degree / qualification *", key="new_edu_degree")
                with col_b:
                    new_institution = st.text_input("Institution *", key="new_edu_institution")
                new_year = st.text_input("Year (e.g. 2018)", key="new_edu_year")
                col_submit, col_cancel = st.columns(2)
                submitted_edu = col_submit.form_submit_button("Save Entry", type="primary")
                cancelled_edu = col_cancel.form_submit_button("Cancel")

            if submitted_edu:
                if not new_degree or not new_institution:
                    st.error("Degree and institution are required.")
                else:
                    profile["education"].append({
                        "degree": new_degree,
                        "institution": new_institution,
                        "year": new_year,
                    })
                    save_profile(profile, str(PROFILE_PATH))
                    st.session_state.profile = profile
                    st.session_state.show_add_edu = False
                    st.rerun()
            if cancelled_edu:
                st.session_state.show_add_edu = False
                st.rerun()

        # ── Skills ───────────────────────────────────────────────────────────
        st.markdown("### Skills")

        skills = profile.setdefault("skills", {"technical": [], "soft": [], "languages": []})

        for skill_type, label in [
            ("technical", "Technical Skills"),
            ("soft", "Soft Skills"),
            ("languages", "Languages"),
        ]:
            st.markdown(f"**{label}**")
            skill_list = skills.get(skill_type, [])

            if skill_list:
                cols = st.columns(min(len(skill_list), 4))
                for j, skill in enumerate(skill_list):
                    with cols[j % 4]:
                        st.markdown(
                            f'<span style="background:#1A1A2E;border:1px solid #2D2D4E;'
                            f'border-radius:4px;padding:3px 8px;font-size:12px;'
                            f'color:#C0C0E0;">{skill}</span>',
                            unsafe_allow_html=True,
                        )
                        if st.button("✕", key=f"del_{skill_type}_{j}", help=f"Remove {skill}"):
                            skills[skill_type].pop(j)
                            save_profile(profile, str(PROFILE_PATH))
                            st.session_state.profile = profile
                            st.rerun()
            else:
                st.caption("No entries yet.")

            add_key = f"show_add_{skill_type}"
            if st.button(f"+ Add {label.split()[0]} Skill" if skill_type != "languages" else "+ Add Language",
                         key=f"btn_add_{skill_type}"):
                st.session_state[add_key] = True

            if st.session_state.get(add_key):
                with st.form(f"add_{skill_type}_form", clear_on_submit=True):
                    new_skill = st.text_input("Skill / language", key=f"new_{skill_type}_val")
                    col_s, col_c = st.columns(2)
                    ok = col_s.form_submit_button("Add", type="primary")
                    ck = col_c.form_submit_button("Cancel")
                if ok:
                    if new_skill.strip():
                        if new_skill.strip() not in skills[skill_type]:
                            skills[skill_type].append(new_skill.strip())
                            save_profile(profile, str(PROFILE_PATH))
                            st.session_state.profile = profile
                    st.session_state[add_key] = False
                    st.rerun()
                if ck:
                    st.session_state[add_key] = False
                    st.rerun()

        # ── Save button (personal info + summary) ────────────────────────────
        st.markdown("---")
        # Save button
        if st.button("Save Profile", use_container_width=True):
            save_profile(profile, str(PROFILE_PATH))
            st.success("Profile saved!")
            st.session_state.edit_mode = False

        render_phase_nav_buttons()


def phase_vacancy_analysis():
    """Phase 2: Vacancy Analysis"""
    st.markdown('<h1 style="font-size: 22px; font-weight: 600; color: #E0E0F0; border-bottom: 1px solid #1E1E2E; padding-bottom: 12px; margin-bottom: 24px;">Phase 2: Vacancy Analysis</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 13px; color: #6B6B8A; margin-top: -16px; margin-bottom: 24px;">Paste or upload a job vacancy description to analyze it against your profile.</p>', unsafe_allow_html=True)
    
    # Check if profile is ready
    if not st.session_state.profile.get("personal_info", {}).get("name"):
        st.warning("Please create your profile first in Phase 1.")
        return

    # ── Recent vacancies ──────────────────────────────────────────────────────
    saved = list_vacancies()
    if saved:
        options = ["— select a saved vacancy —"] + [
            f"{s.title} · {s.company} ({s.timestamp[:10]})"
            for s in saved
        ]
        chosen_label = st.selectbox(
            "Recent vacancies",
            options=options,
            index=0,
            key="vacancy_library_select",
        )
        if chosen_label != "— select a saved vacancy —":
            chosen_idx = options.index(chosen_label) - 1  # offset for placeholder
            chosen_slug = saved[chosen_idx].slug
            if st.button("Load selected vacancy", key="load_vacancy_btn"):
                loaded = load_vacancy(chosen_slug)
                st.session_state.vacancy_data = loaded["vacancy_data"]
                st.session_state.match_results = loaded["match_results"]
                # Restore tone from saved vacancy's suggested_tone
                st.session_state.selected_tone = loaded["vacancy_data"].get(
                    "suggested_tone", st.session_state.selected_tone
                )
                st.success("Vacancy loaded from library.")
                st.rerun()

        st.markdown(
            '<hr style="border-color:#1E1E2E; margin: 16px 0;">',
            unsafe_allow_html=True,
        )

    vacancy_text = st.text_area(
        "Paste job vacancy description",
        height=200,
        key="vacancy_input"
    )

    uploaded_vacancy = st.file_uploader(
        "Or upload a file",
        type=['txt', 'pdf'],
        key="vacancy_uploader"
    )
    
    if uploaded_vacancy and not vacancy_text:
        temp_path = BASE_DIR / "temp_vacancy" / uploaded_vacancy.name
        os.makedirs(BASE_DIR / "temp_vacancy", exist_ok=True)
        
        with open(temp_path, 'wb') as f:
            f.write(uploaded_vacancy.getbuffer())
        
        if uploaded_vacancy.name.endswith('.pdf'):
            from src.profile.pdf_ingest import extract_text_from_pdf
            vacancy_text = extract_text_from_pdf(str(temp_path))
        else:
            with open(temp_path, 'r', encoding='utf-8') as f:
                vacancy_text = f.read()
        
        if temp_path.exists():
            temp_path.unlink()
    
    if st.button("Analyze Vacancy", use_container_width=True, type="primary"):
        if not vacancy_text:
            st.error("Please paste or upload a vacancy description.")
            return

        settings = load_settings()
        base_url = settings["ollama"]["base_url"]
        qwen_model = settings["ollama"]["models"]["qwen_coder"]

        # Progress container
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Running vacancy analysis pipeline...</div>', unsafe_allow_html=True)
            progress_bar.progress(10)

            pipeline_ctx = {
                "vacancy_text": vacancy_text,
                "profile": st.session_state.profile,
                "qwen_model": qwen_model,
                "base_url": base_url,
            }
            result = VACANCY_ANALYSIS_PIPELINE.run(pipeline_ctx)
            st.session_state.last_pipeline_telemetry = result.telemetry

            st.session_state.vacancy_data = result.context.get("vacancy_data", {})
            st.session_state.match_results = result.context.get("match_results", {})
            st.session_state.selected_tone = result.context.get("selected_tone", st.session_state.selected_tone)

            # Auto-save to vacancy library
            try:
                save_vacancy(
                    vacancy_data=st.session_state.vacancy_data,
                    match_results=st.session_state.match_results,
                    raw_text=vacancy_text,
                )
            except Exception:
                pass  # library save is best-effort; never block the user

            progress_bar.progress(100)
            status_text.markdown('<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> Analysis complete!</div>', unsafe_allow_html=True)

        import time
        time.sleep(1.5)
        progress_container.empty()
    
    # Display results
    if st.session_state.vacancy_data:
        st.markdown('<h2 style="font-size: 18px; font-weight: 600; color: #E0E0F0; margin-top: 32px; margin-bottom: 16px;">Analysis Results</h2>', unsafe_allow_html=True)

        vacancy = st.session_state.vacancy_data

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="
                background: #111118;
                border: 1px solid #1E1E2E;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
            ">
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B6B8A; font-weight: 500;">Domain</div>
                <div style="font-size: 18px; font-weight: 600; color: #E0E0F0; margin-top: 4px;">{vacancy.get('domain', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="
                background: #111118;
                border: 1px solid #1E1E2E;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
            ">
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B6B8A; font-weight: 500;">Seniority</div>
                <div style="font-size: 18px; font-weight: 600; color: #E0E0F0; margin-top: 4px;">{vacancy.get('seniority', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            tone_label = get_tone_description(st.session_state.selected_tone)["label"]
            st.markdown(f"""
            <div style="
                background: #111118;
                border: 1px solid #1E1E2E;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
            ">
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B6B8A; font-weight: 500;">Suggested Tone</div>
                <div style="font-size: 18px; font-weight: 600; color: #E0E0F0; margin-top: 4px;">{tone_label}</div>
            </div>
            """, unsafe_allow_html=True)

        # Keywords
        if vacancy.get("keywords"):
            st.markdown('<h3 style="font-size: 16px; font-weight: 600; color: #E0E0F0; margin-top: 24px; margin-bottom: 12px;">Extracted Keywords</h3>', unsafe_allow_html=True)
            keywords_html = " ".join([f'<code style="background: #16163A; color: #9090CC; border: 1px solid #2E2E4E; border-radius: 4px; padding: 6px 12px; font-size: 12px; display: inline-block; margin: 4px 4px 4px 0;">{kw}</code>' for kw in vacancy["keywords"]])
            st.markdown(keywords_html, unsafe_allow_html=True)

        # Strong points
        if st.session_state.match_results.get("strong_points"):
            st.markdown('<h3 style="font-size: 16px; font-weight: 600; color: #E0E0F0; margin-top: 24px; margin-bottom: 12px;">Strong Points</h3>', unsafe_allow_html=True)
            for point in st.session_state.match_results["strong_points"]:
                # Clean up any markdown icon syntax from LLM output
                vacancy_term = point.get('vacancy_term', '')
                profile_evidence = point.get('profile_evidence', '').replace('_arrow_light', '').replace('_arrow_dark', '').strip()
                rationale = point.get('rationale', '').replace('_arrow_light', '').replace('_arrow_dark', '').strip()
                
                with st.expander(f"**{vacancy_term}**"):
                    st.markdown(f'<span style="font-size: 12px; color: #6B6B8A;">Evidence:</span> <span style="font-size: 13px; color: #9090CC;">{profile_evidence}</span>', unsafe_allow_html=True)
                    st.markdown(f'<span style="font-size: 12px; color: #6B6B8A;">Rationale:</span> <span style="font-size: 13px; color: #9090CC;">{rationale}</span>', unsafe_allow_html=True)

        # Gaps
        if st.session_state.match_results.get("gaps"):
            st.markdown('<h3 style="font-size: 16px; font-weight: 600; color: #E0E0F0; margin-top: 24px; margin-bottom: 12px;">Alignment Gaps</h3>', unsafe_allow_html=True)
            for gap in st.session_state.match_results["gaps"]:
                st.markdown(f'<div style="background: #1A0A0A; border: 1px solid #E24B4A33; border-radius: 6px; padding: 8px 14px; font-size: 12px; color: #FF6B6B; margin-bottom: 6px;">{gap}</div>', unsafe_allow_html=True)

        # Alignment score
        if st.session_state.match_results.get("alignment_score"):
            score = st.session_state.match_results["alignment_score"]
            
            if score <= 40:
                score_color = "#E24B4A"
            elif score <= 70:
                score_color = "#EF9F27"
            else:
                score_color = "#1D9E75"
            
            st.markdown(f"""
            <div style="margin-top: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B6B8A; font-weight: 500;">Alignment Score</span>
                    <span style="font-size: 14px; font-weight: 600; color: {score_color};">{score}%</span>
                </div>
                <div style="background: #1E1E2E; height: 6px; border-radius: 4px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #6C63FF, #9B5DE5); height: 6px; border-radius: 4px; width: {score}%; transition: width 0.6s ease;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # T2.5: per-stage pipeline telemetry (collapsed by default).
    render_pipeline_telemetry_panel()

    render_phase_nav_buttons()


def render_keyword_chips() -> None:
    """T6.5 — ATS keyword chips with hit (≥2), partial (1), miss (0) color coding."""
    keywords = st.session_state.get("vacancy_data", {}).get("keywords", [])
    if not keywords:
        return

    # Build joined document text for matching
    parts = []
    cv = st.session_state.get("cv_content", {})
    if cv.get("executive_summary"):
        parts.append(cv["executive_summary"])
    for exp in cv.get("tailored_experience", []):
        parts.extend(exp.get("achievements", []))
    cl = st.session_state.get("cover_letter_content", {})
    parts.extend(cl.get("paragraphs", []))
    doc_text = " ".join(parts).lower()

    chips = []
    for kw in keywords:
        count = doc_text.count(kw.lower())
        if count >= 2:
            cls, title = "hit", f"{kw} — {count}×"
        elif count == 1:
            cls, title = "partial", f"{kw} — 1×"
        else:
            cls, title = "miss", f"{kw} — not found"
        chips.append(f'<span class="kw-chip {cls}" title="{title}">{kw}</span>')

    st.markdown(
        '<div style="font-size:11px;font-weight:500;text-transform:uppercase;'
        'letter-spacing:0.08em;color:#6B6B8A;margin-bottom:6px;">Keywords</div>'
        + "".join(chips),
        unsafe_allow_html=True,
    )


_TEMPLATE_DEFS = {
    "executive": {
        "label": "Executive",
        "cv_file": "cv_executive.html",
        "cl_file": "cl_executive.html",
        "thumb_html": (
            '<div class="tmpl-thumb executive {sel}">'
            '<div class="tt-top"></div>'
            '<div class="tt-body">'
            '<div class="tt-name"></div>'
            '<div class="tt-rule"></div>'
            '<div class="tt-line long"></div>'
            '<div class="tt-line med"></div>'
            '<div class="tt-line short"></div>'
            '<div class="tt-rule"></div>'
            '<div class="tt-line med"></div>'
            '<div class="tt-line long"></div>'
            '<div class="tt-line short"></div>'
            '</div></div>'
        ),
    },
    "modern": {
        "label": "Modern",
        "cv_file": "cv_modern.html",
        "cl_file": "cl_modern.html",
        "thumb_html": (
            '<div class="tmpl-thumb modern {sel}">'
            '<div class="tt-top"></div>'
            '<div class="tt-body">'
            '<div class="tt-name"></div>'
            '<div class="tt-line long"></div>'
            '<div class="tt-line med"></div>'
            '<div class="tt-line short"></div>'
            '<div class="tt-line long accent"></div>'
            '<div class="tt-line med"></div>'
            '<div class="tt-line short accent"></div>'
            '</div></div>'
        ),
    },
    "technical": {
        "label": "Technical",
        "cv_file": "cv_technical.html",
        "cl_file": "cl_technical.html",
        "thumb_html": (
            '<div class="tmpl-thumb technical {sel}">'
            '<div class="tt-top"></div>'
            '<div class="tt-body">'
            '<div class="tt-name"></div>'
            '<div class="tt-line long accent"></div>'
            '<div class="tt-line med"></div>'
            '<div class="tt-line short"></div>'
            '<div class="tt-rule"></div>'
            '<div class="tt-line long accent"></div>'
            '<div class="tt-line short"></div>'
            '</div></div>'
        ),
    },
}


def render_template_picker() -> None:
    """T6.4 — Three CSS thumbnail cards for template selection."""
    current = st.session_state.get("selected_template", "modern")
    st.markdown(
        '<div style="font-size:11px;font-weight:500;text-transform:uppercase;'
        'letter-spacing:0.08em;color:#6B6B8A;margin-bottom:8px;">Template</div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for col, (key, tdef) in zip(cols, _TEMPLATE_DEFS.items()):
        is_sel = key == current
        sel_cls = "selected" if is_sel else ""
        with col:
            st.markdown(
                tdef["thumb_html"].format(sel=sel_cls)
                + f'<div class="tmpl-label {sel_cls}">{tdef["label"]}</div>',
                unsafe_allow_html=True,
            )
            if not is_sel:
                if st.button(
                    "Select",
                    key=f"tmpl_btn_{key}",
                    use_container_width=True,
                ):
                    st.session_state.selected_template = key
                    st.rerun()
            else:
                st.markdown(
                    '<div style="height:32px;display:flex;align-items:center;'
                    'justify-content:center;font-size:11px;color:#6C63FF;'
                    'font-weight:600;">&#10003; Active</div>',
                    unsafe_allow_html=True,
                )


def render_live_preview(doc_type: str = "cv") -> None:
    """T6.4 — Scaled-down live HTML preview using the selected template."""
    current = st.session_state.get("selected_template", "modern")
    tdef = _TEMPLATE_DEFS.get(current, _TEMPLATE_DEFS["modern"])

    if doc_type == "cv" and st.session_state.get("cv_content"):
        try:
            html = render_cv_template(
                st.session_state.profile,
                st.session_state.cv_content,
                tdef["cv_file"],
            )
        except Exception:
            return
    elif doc_type == "cl" and st.session_state.get("cover_letter_content"):
        name = st.session_state.profile.get("personal_info", {}).get("name", "")
        paragraphs = st.session_state.cover_letter_content.get("paragraphs", [])
        try:
            html = render_cover_letter_template(name, paragraphs, tdef["cl_file"])
        except Exception:
            return
    else:
        return

    # Wrap at 50 % scale so it fits in the column
    scaled = (
        '<div style="transform:scale(0.5);transform-origin:top left;'
        'width:200%;pointer-events:none;">'
        + html
        + "</div>"
    )
    import streamlit.components.v1 as components
    components.html(scaled, height=400, scrolling=True)


def phase_document_generation():
    """Phase 3: Tone & Document Generation"""
    st.markdown('<h1 style="font-size: 22px; font-weight: 600; color: #E0E0F0; border-bottom: 1px solid #1E1E2E; padding-bottom: 12px; margin-bottom: 24px;">Phase 3: Document Generation</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 13px; color: #6B6B8A; margin-top: -16px; margin-bottom: 24px;">Generate your tailored CV and cover letter.</p>', unsafe_allow_html=True)

    if not st.session_state.vacancy_data:
        st.warning("Please analyze a vacancy first in Phase 2.")
        return

    doc_col, ctrl_col = st.columns([3, 2])

    with ctrl_col:
        # Tone selection
        st.markdown('<div style="font-size: 13px; font-weight: 600; color: #E0E0F0; margin-bottom: 8px;">Select Tone</div>', unsafe_allow_html=True)
        tones = get_all_tones()
        tone_options = [info["label"] for info in tones.values()]

        current_label = get_tone_description(st.session_state.selected_tone)["label"]
        selected_label = st.selectbox(
            "Communication Tone",
            options=tone_options,
            index=tone_options.index(current_label) if current_label in tone_options else 0
        )

        for tone_key, info in tones.items():
            if info["label"] == selected_label:
                st.session_state.selected_tone = tone_key
                break

        tone_desc = get_tone_description(st.session_state.selected_tone)['description']
        st.markdown(f'<span style="background: #16163A; color: #9090CC; border: 1px solid #2E2E4E; border-radius: 4px; padding: 6px 12px; font-size: 12px; display: inline-block; margin-top: 4px; margin-bottom: 12px;">{tone_desc}</span>', unsafe_allow_html=True)

        # T3.3: Cover letter structure options
        with st.expander("Cover Letter: Structure options", expanded=False):
            cl_para_count = st.slider(
                "Paragraph count", min_value=3, max_value=6, value=4,
                key="cl_para_count",
            )
            cl_target_words = st.slider(
                "Target total words", min_value=200, max_value=450, value=320, step=10,
                key="cl_target_words",
            )
            cl_research_para = st.checkbox(
                "Include explicit company-research paragraph", value=False,
                key="cl_research_para",
            )
            cl_metric_para = st.checkbox(
                "Require explicit metric paragraph", value=True,
                key="cl_metric_para",
            )

        st.markdown('<div style="margin-top: 12px;"></div>', unsafe_allow_html=True)

        if st.button("Generate CV", use_container_width=True, type="primary", key="gen_cv_btn"):
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Preparing context and strong points...</div>', unsafe_allow_html=True)
                progress_bar.progress(15)

                settings = load_settings()
                base_url = settings["ollama"]["base_url"]
                qwen_model = settings["ollama"]["models"]["qwen_coder"]
                deepseek_model = settings["ollama"]["models"]["deepseek"]

                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Generating CV...</div>', unsafe_allow_html=True)
                progress_bar.progress(40)

                stream_placeholder = st.empty()

                def cv_on_chunk(text: str) -> None:
                    snippet = text if len(text) <= 4000 else "…" + text[-4000:]
                    stream_placeholder.markdown(
                        f'<div style="background:#13131F;border:1px solid #1E1E2E;border-radius:6px;'
                        f'padding:12px 14px;font-family:ui-monospace,Menlo,Consolas,monospace;'
                        f'font-size:12px;line-height:1.55;color:#C0C0DA;max-height:340px;'
                        f'overflow:auto;white-space:pre-wrap;word-break:break-word;">'
                        f'{snippet}</div>',
                        unsafe_allow_html=True,
                    )

                pipeline_ctx = {
                    "profile": st.session_state.profile,
                    "vacancy_data": st.session_state.vacancy_data,
                    "match_results": st.session_state.match_results,
                    "selected_tone": st.session_state.selected_tone,
                    "qwen_model": qwen_model,
                    "deepseek_model": deepseek_model,
                    "base_url": base_url,
                    "on_chunk": cv_on_chunk,
                }
                cv_result = CV_GENERATION_PIPELINE.run(pipeline_ctx)
                stream_placeholder.empty()
                st.session_state.last_pipeline_telemetry = cv_result.telemetry

                progress_bar.progress(85)
                cv_original = cv_result.context.get("cv_content", {})
                cv_revised = cv_result.context.get("cv_content_revised")
                cv_severity = cv_result.context.get("cv_critique_severity", "none")
                st.session_state.cv_original_draft = cv_original
                st.session_state.cv_revised_draft = cv_revised if cv_revised else cv_original
                st.session_state.cv_is_revised = bool(cv_revised) and cv_revised != cv_original
                st.session_state.cv_critique_severity = cv_severity
                st.session_state.cv_content = cv_revised if cv_revised else cv_original
                st.session_state.cv_revisions = [{
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "source": "draft",
                    "content": copy.deepcopy(st.session_state.cv_content),
                    "change_summary": "Initial draft",
                }]
                progress_bar.progress(100)
                status_text.markdown('<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> CV generated!</div>', unsafe_allow_html=True)

            import time; time.sleep(1.5)
            progress_container.empty()
            st.rerun()

        st.markdown('<div style="margin-top: 8px;"></div>', unsafe_allow_html=True)

        if st.button("Generate Cover Letter", use_container_width=True, type="primary", key="gen_cl_btn"):
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Preparing context and strong points...</div>', unsafe_allow_html=True)
                progress_bar.progress(15)

                settings = load_settings()
                base_url = settings["ollama"]["base_url"]
                qwen_model = settings["ollama"]["models"]["qwen_coder"]
                deepseek_model = settings["ollama"]["models"]["deepseek"]

                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Writing cover letter...</div>', unsafe_allow_html=True)
                progress_bar.progress(40)

                stream_placeholder = st.empty()

                def cl_on_chunk(text: str) -> None:
                    snippet = text if len(text) <= 4000 else "…" + text[-4000:]
                    stream_placeholder.markdown(
                        f'<div style="background:#13131F;border:1px solid #1E1E2E;border-radius:6px;'
                        f'padding:12px 14px;font-family:ui-monospace,Menlo,Consolas,monospace;'
                        f'font-size:12px;line-height:1.55;color:#C0C0DA;max-height:340px;'
                        f'overflow:auto;white-space:pre-wrap;word-break:break-word;">'
                        f'{snippet}</div>',
                        unsafe_allow_html=True,
                    )

                pipeline_ctx = {
                    "profile": st.session_state.profile,
                    "vacancy_data": st.session_state.vacancy_data,
                    "match_results": st.session_state.match_results,
                    "selected_tone": st.session_state.selected_tone,
                    "paragraph_count": st.session_state.get("cl_para_count", 4),
                    "target_words": st.session_state.get("cl_target_words", 320),
                    "include_research_para": st.session_state.get("cl_research_para", False),
                    "require_metric_para": st.session_state.get("cl_metric_para", True),
                    "qwen_model": qwen_model,
                    "deepseek_model": deepseek_model,
                    "base_url": base_url,
                    "on_chunk": cl_on_chunk,
                }
                cl_result = CL_GENERATION_PIPELINE.run(pipeline_ctx)
                stream_placeholder.empty()
                st.session_state.last_pipeline_telemetry = cl_result.telemetry

                progress_bar.progress(85)
                cl_original = cl_result.context.get("cover_letter_content", {})
                cl_revised = cl_result.context.get("cover_letter_content_revised")
                cl_severity = cl_result.context.get("cl_critique_severity", "none")
                st.session_state.cover_letter_original_draft = cl_original
                st.session_state.cover_letter_revised_draft = cl_revised if cl_revised else cl_original
                st.session_state.cover_letter_is_revised = bool(cl_revised) and cl_revised != cl_original
                st.session_state.cl_critique_severity = cl_severity
                st.session_state.cover_letter_content = cl_revised if cl_revised else cl_original
                st.session_state.cover_letter_revisions = [{
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "source": "draft",
                    "content": copy.deepcopy(st.session_state.cover_letter_content),
                    "change_summary": "Initial draft",
                }]
                progress_bar.progress(100)
                status_text.markdown('<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> Cover letter generated!</div>', unsafe_allow_html=True)

            import time; time.sleep(1.5)
            progress_container.empty()
            st.rerun()

        # T2.5: per-stage pipeline telemetry (collapsed by default).
        render_pipeline_telemetry_panel()

    with doc_col:
        render_template_picker()

        # Live preview (shows when document exists)
        has_doc = bool(st.session_state.get("cv_content") or st.session_state.get("cover_letter_content"))
        if has_doc:
            preview_type = "cv" if st.session_state.get("cv_content") else "cl"
            with st.expander("Live preview", expanded=True):
                render_live_preview(preview_type)

        st.markdown('<hr style="border:none;border-top:1px solid #1E1E2E;margin:16px 0;">', unsafe_allow_html=True)

        if st.session_state.get("cv_content") or st.session_state.get("cover_letter_content"):
            render_keyword_chips()
            st.markdown('<div style="margin-bottom:12px;"></div>', unsafe_allow_html=True)

        if st.session_state.cv_content:
            st.markdown('<div style="font-size: 13px; font-weight: 600; color: #E0E0F0; margin-bottom: 8px;">CV — Executive Summary</div>', unsafe_allow_html=True)

            cv_orig = st.session_state.get("cv_original_draft", {})
            cv_rev = st.session_state.get("cv_revised_draft", {})
            cv_was_revised = bool(st.session_state.get("cv_is_revised", False))
            cv_severity = st.session_state.get("cv_critique_severity", "none")

            if cv_was_revised:
                sev_color = {"minor": "#EF9F27", "major": "#E24B4A"}.get(cv_severity, "#6B6B8A")
                st.markdown(
                    f'<div style="font-size:11px;color:#6B6B8A;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                    f'Critique severity: <span style="color:{sev_color};font-weight:600;">{cv_severity}</span>'
                    f' &nbsp;·&nbsp; DeepSeek revision applied</div>',
                    unsafe_allow_html=True,
                )
                cv_view = st.radio(
                    "View",
                    ["Revised draft", "Original draft"],
                    horizontal=True,
                    key="cv_draft_toggle",
                )
                cv_display = cv_rev if cv_view == "Revised draft" else cv_orig
            else:
                cv_display = st.session_state.cv_content

            st.text_area(
                "Summary",
                value=cv_display.get("executive_summary", ""),
                height=200,
                key="cv_summary_display"
            )

            # ATS Score
            summary_text = st.session_state.cv_content.get("executive_summary", "")
            vacancy_keywords = st.session_state.vacancy_data.get("keywords", [])
            if summary_text and vacancy_keywords:
                ats_score = calculate_ats_score(summary_text, vacancy_keywords)
                score_val = ats_score['overall_score']
                if score_val <= 40:
                    score_color = "#E24B4A"
                elif score_val <= 70:
                    score_color = "#EF9F27"
                else:
                    score_color = "#1D9E75"
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #6B6B8A; font-weight: 500;">ATS Score</span>
                    <span style="font-size: 14px; font-weight: 600; color: {score_color};">{score_val}/100</span>
                </div>
                <div style="background: #1E1E2E; height: 6px; border-radius: 4px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #6C63FF, #9B5DE5); height: 6px; border-radius: 4px; width: {score_val}%; transition: width 0.6s ease;"></div>
                </div>
                """, unsafe_allow_html=True)

        if st.session_state.cover_letter_content:
            st.markdown('<div style="font-size: 13px; font-weight: 600; color: #E0E0F0; margin-top: 24px; margin-bottom: 8px;">Cover Letter</div>', unsafe_allow_html=True)

            cl_orig = st.session_state.get("cover_letter_original_draft", {})
            cl_rev = st.session_state.get("cover_letter_revised_draft", {})
            cl_was_revised = bool(st.session_state.get("cover_letter_is_revised", False))
            cl_severity = st.session_state.get("cl_critique_severity", "none")

            if cl_was_revised:
                sev_color = {"minor": "#EF9F27", "major": "#E24B4A"}.get(cl_severity, "#6B6B8A")
                st.markdown(
                    f'<div style="font-size:11px;color:#6B6B8A;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">'
                    f'Critique severity: <span style="color:{sev_color};font-weight:600;">{cl_severity}</span>'
                    f' &nbsp;·&nbsp; DeepSeek revision applied</div>',
                    unsafe_allow_html=True,
                )
                cl_view = st.radio(
                    "View",
                    ["Revised draft", "Original draft"],
                    horizontal=True,
                    key="cl_draft_toggle",
                )
                cl_display = cl_rev if cl_view == "Revised draft" else cl_orig
            else:
                cl_display = st.session_state.cover_letter_content

            paragraphs = cl_display.get("paragraphs", [])
            for i, para in enumerate(paragraphs):
                st.text_area(
                    f"Paragraph {i+1}",
                    value=para,
                    height=100,
                    key=f"cl_para_{i}"
                )

        render_keyword_chips()
        render_phase_nav_buttons()


def phase_refinement():
    """Phase 4: Iterative Refinement"""
    st.markdown('<h1 style="font-size: 22px; font-weight: 600; color: #E0E0F0; border-bottom: 1px solid #1E1E2E; padding-bottom: 12px; margin-bottom: 24px;">Phase 4: Refinement</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 13px; color: #6B6B8A; margin-top: -16px; margin-bottom: 24px;">Select any section and provide feedback to improve it.</p>', unsafe_allow_html=True)

    if not st.session_state.cv_content and not st.session_state.cover_letter_content:
        st.warning("Please generate documents first in Phase 3.")
        return

    doc_col, ctrl_col = st.columns([3, 2])

    # ── Left: document preview ────────────────────────────────────────────────
    with doc_col:
        render_keyword_chips()
        if st.session_state.get("cv_content") or st.session_state.get("cover_letter_content"):
            st.markdown('<div style="margin-bottom:12px;"></div>', unsafe_allow_html=True)

        if st.session_state.cv_content:
            st.markdown('<div style="font-size: 13px; font-weight: 600; color: #E0E0F0; margin-bottom: 8px;">CV — Executive Summary</div>', unsafe_allow_html=True)
            st.text_area(
                "Summary",
                value=st.session_state.cv_content.get("executive_summary", ""),
                height=180,
                key="p4_cv_display",
                disabled=True,
            )

        if st.session_state.cover_letter_content:
            st.markdown('<div style="font-size: 13px; font-weight: 600; color: #E0E0F0; margin-top: 20px; margin-bottom: 8px;">Cover Letter</div>', unsafe_allow_html=True)
            paragraphs_preview = st.session_state.cover_letter_content.get("paragraphs", [])
            joined_preview = "\n\n".join(paragraphs_preview)
            st.text_area(
                "Full letter",
                value=joined_preview,
                height=320,
                key="p4_cl_display",
                disabled=True,
            )

    # ── Right: refinement controls ────────────────────────────────────────────
    with ctrl_col:
        doc_type = st.radio(
            "Refine which document?",
            ["CV Summary", "Cover Letter"],
            horizontal=True,
            key="p4_doc_type",
        )

        if doc_type == "CV Summary":
            if st.session_state.cv_content:
                current = st.session_state.cv_content.get("executive_summary", "")
                feedback = st.text_area("Your feedback/instructions", key="cv_feedback", height=120)

                if st.button("Refine Summary", type="primary", use_container_width=True):
                    if not feedback:
                        st.error("Please provide feedback.")
                    else:
                        progress_container = st.container()
                        with progress_container:
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Analyzing feedback and context...</div>', unsafe_allow_html=True)
                            progress_bar.progress(20)

                            settings = load_settings()
                            base_url = settings["ollama"]["base_url"]
                            deepseek_model = settings["ollama"]["models"]["deepseek"]

                            status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Rewriting executive summary...</div>', unsafe_allow_html=True)
                            progress_bar.progress(50)

                            refined = refine_section(
                                "summary",
                                current,
                                feedback,
                                st.session_state.vacancy_data,
                                st.session_state.selected_tone,
                                deepseek_model,
                                base_url,
                            )

                            status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Applying changes...</div>', unsafe_allow_html=True)
                            progress_bar.progress(85)

                            st.session_state.cv_content["executive_summary"] = refined.revised_text
                            st.session_state.cv_revisions.append({
                                "timestamp": datetime.now().isoformat(timespec="seconds"),
                                "source": "summary_refine",
                                "content": copy.deepcopy(st.session_state.cv_content),
                                "change_summary": refined.change_summary or "",
                            })
                            progress_bar.progress(100)
                            status_text.markdown('<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> Summary refined!</div>', unsafe_allow_html=True)

                        import time; time.sleep(1.5)
                        progress_container.empty()
                        st.rerun()

                render_revision_history(st.session_state.cv_revisions, "cv")

        else:  # Cover Letter
            if st.session_state.cover_letter_content:
                cl_tab_whole, cl_tab_para = st.tabs(["Whole Letter", "By Paragraph"])

                with cl_tab_whole:
                    feedback_whole = st.text_area(
                        "Your feedback/instructions",
                        key="cl_whole_feedback",
                        height=120,
                    )
                    if st.button("Refine Whole Letter", type="primary", key="cl_whole_refine_btn", use_container_width=True):
                        if not feedback_whole:
                            st.error("Please provide feedback.")
                        else:
                            progress_container = st.container()
                            with progress_container:
                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Analyzing feedback...</div>', unsafe_allow_html=True)
                                progress_bar.progress(20)

                                settings = load_settings()
                                base_url = settings["ollama"]["base_url"]
                                deepseek_model = settings["ollama"]["models"]["deepseek"]

                                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Rewriting whole letter...</div>', unsafe_allow_html=True)
                                progress_bar.progress(50)

                                cl_dict = st.session_state.cover_letter_content
                                letter = CoverLetter(
                                    paragraphs=cl_dict.get("paragraphs", []),
                                    paragraph_intents=cl_dict.get("paragraph_intents"),
                                    rationale=cl_dict.get("rationale"),
                                )
                                refined_letter = refine_full_cover_letter(
                                    letter=letter,
                                    feedback=feedback_whole,
                                    vacancy_data=st.session_state.vacancy_data,
                                    tone=st.session_state.selected_tone,
                                    model_name=deepseek_model,
                                    base_url=base_url,
                                )

                                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Applying changes...</div>', unsafe_allow_html=True)
                                progress_bar.progress(85)

                                st.session_state.cover_letter_content = {
                                    "paragraphs": refined_letter.paragraphs,
                                    "paragraph_intents": refined_letter.paragraph_intents,
                                    "rationale": refined_letter.rationale,
                                }
                                st.session_state.cover_letter_revisions.append({
                                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                                    "source": "full_refine",
                                    "content": copy.deepcopy(st.session_state.cover_letter_content),
                                    "change_summary": refined_letter.rationale or "",
                                })
                                progress_bar.progress(100)
                                status_text.markdown('<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> Letter refined!</div>', unsafe_allow_html=True)

                            import time; time.sleep(1.5)
                            progress_container.empty()
                            st.rerun()

                with cl_tab_para:
                    paragraphs = st.session_state.cover_letter_content.get("paragraphs", [])

                    para_idx = st.selectbox(
                        "Select paragraph to refine",
                        options=list(range(len(paragraphs))),
                        format_func=lambda x: f"Paragraph {x+1}",
                        key="cl_para_selectbox",
                    )

                    current = paragraphs[para_idx]
                    feedback = st.text_area("Your feedback/instructions", key="cl_feedback", height=100)

                    if st.button("Refine Paragraph", type="primary", key="cl_para_refine_btn", use_container_width=True):
                        if not feedback:
                            st.error("Please provide feedback.")
                        else:
                            progress_container = st.container()
                            with progress_container:
                                progress_bar = st.progress(0)
                                status_text = st.empty()

                                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Analyzing feedback and context...</div>', unsafe_allow_html=True)
                                progress_bar.progress(20)

                                settings = load_settings()
                                base_url = settings["ollama"]["base_url"]
                                deepseek_model = settings["ollama"]["models"]["deepseek"]

                                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Rewriting paragraph {p}...</div>'.format(p=para_idx+1), unsafe_allow_html=True)
                                progress_bar.progress(50)

                                refined_paragraphs = refine_cover_letter_paragraphs(
                                    paragraphs.copy(),
                                    feedback,
                                    para_idx,
                                    st.session_state.vacancy_data,
                                    tone=st.session_state.selected_tone,
                                    model_name=deepseek_model,
                                    base_url=base_url,
                                )

                                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Applying changes...</div>', unsafe_allow_html=True)
                                progress_bar.progress(85)

                                st.session_state.cover_letter_content["paragraphs"] = refined_paragraphs
                                st.session_state.cover_letter_revisions.append({
                                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                                    "source": "paragraph_refine",
                                    "content": copy.deepcopy(st.session_state.cover_letter_content),
                                    "change_summary": f"Paragraph {para_idx + 1} refined",
                                })
                                progress_bar.progress(100)
                                status_text.markdown('<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> Paragraph {p} refined!</div>'.format(p=para_idx+1), unsafe_allow_html=True)

                            import time; time.sleep(1.5)
                            progress_container.empty()
                            st.rerun()

                render_revision_history(st.session_state.cover_letter_revisions, "cl")

        render_phase_nav_buttons()


def phase_export():
    """Phase 5: Export"""
    st.markdown('<h1 style="font-size: 22px; font-weight: 600; color: #E0E0F0; border-bottom: 1px solid #1E1E2E; padding-bottom: 12px; margin-bottom: 24px;">Phase 5: Export</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 13px; color: #6B6B8A; margin-top: -16px; margin-bottom: 24px;">Select a template and format, then export your documents.</p>', unsafe_allow_html=True)

    if not st.session_state.cv_content and not st.session_state.cover_letter_content:
        st.warning("Please generate documents first in Phase 3.")
        return

    templates = get_available_templates()
    os.makedirs(BASE_DIR / "output", exist_ok=True)

    # ── CV Export ──────────────────────────────────────────────────────────────
    if st.session_state.cv_content:
        st.subheader("CV Export")

        _cv_opts = templates.get("cv", [])
        _sel_tmpl = st.session_state.get("selected_template", "modern")
        _cv_preferred = _TEMPLATE_DEFS.get(_sel_tmpl, {}).get("cv_file", "")
        _cv_default = _cv_opts.index(_cv_preferred) if _cv_preferred in _cv_opts else 0
        cv_template = st.selectbox(
            "Select CV Template",
            options=_cv_opts,
            index=_cv_default,
            format_func=lambda x: x.replace("cv_", "").replace(".html", "").title(),
            key="cv_template_select",
        )

        cv_format = st.radio(
            "Format",
            options=["PDF", "DOCX"],
            horizontal=True,
            key="cv_export_format",
        )

        if st.button("Export CV", use_container_width=True, type="primary", key="export_cv_btn"):
            is_docx = cv_format == "DOCX"
            ext = "docx" if is_docx else "pdf"
            output_path = BASE_DIR / "output" / f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Rendering template...</div>', unsafe_allow_html=True)
                progress_bar.progress(30)

                if is_docx:
                    success = render_cv_docx(
                        st.session_state.cv_content,
                        st.session_state.profile,
                        cv_template,
                        str(output_path),
                    )
                else:
                    success = generate_cv_pdf(
                        st.session_state.profile,
                        st.session_state.cv_content,
                        cv_template,
                        str(output_path),
                    )

                progress_bar.progress(70)

                if success:
                    progress_bar.progress(100)
                    status_text.markdown(f'<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> CV exported to: {output_path.name}</div>', unsafe_allow_html=True)
                    import time; time.sleep(1)
                    progress_container.empty()

                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if is_docx else "application/pdf"
                    with open(output_path, "rb") as f:
                        st.download_button(
                            f"Download CV {cv_format}",
                            f,
                            file_name=output_path.name,
                            mime=mime,
                        )
                else:
                    progress_bar.progress(100)
                    renderer_hint = "python-docx" if is_docx else "WeasyPrint"
                    status_text.markdown(f'<div style="font-size:13px;color:#FF6B6B;padding:8px 0;"><span style="color:#FF6B6B;">✗</span> Export failed. Ensure {renderer_hint} is installed.</div>', unsafe_allow_html=True)
                    import time; time.sleep(2)
                    progress_container.empty()

    # ── Cover Letter Export ────────────────────────────────────────────────────
    if st.session_state.cover_letter_content:
        st.subheader("Cover Letter Export")

        _cl_opts = templates.get("cover_letter", [])
        _cl_preferred = _TEMPLATE_DEFS.get(_sel_tmpl, {}).get("cl_file", "")
        _cl_default = _cl_opts.index(_cl_preferred) if _cl_preferred in _cl_opts else 0
        cl_template = st.selectbox(
            "Select Cover Letter Template",
            options=_cl_opts,
            index=_cl_default,
            format_func=lambda x: x.replace("cl_", "").replace(".html", "").title(),
            key="cl_template_select",
        )

        cl_format = st.radio(
            "Format",
            options=["PDF", "DOCX"],
            horizontal=True,
            key="cl_export_format",
        )

        if st.button("Export Cover Letter", use_container_width=True, type="primary", key="export_cl_btn"):
            is_docx = cl_format == "DOCX"
            ext = "docx" if is_docx else "pdf"
            output_path = BASE_DIR / "output" / f"cover_letter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

            name = st.session_state.profile.get("personal_info", {}).get("name", "Candidate")
            paragraphs = st.session_state.cover_letter_content.get("paragraphs", [])

            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0)
                status_text = st.empty()

                status_text.markdown('<div style="font-size:13px;color:#9090CC;padding:8px 0;"><span style="color:#6C63FF;">●</span> Rendering template...</div>', unsafe_allow_html=True)
                progress_bar.progress(30)

                if is_docx:
                    success = render_cover_letter_docx(
                        st.session_state.cover_letter_content,
                        st.session_state.profile,
                        cl_template,
                        str(output_path),
                    )
                else:
                    success = generate_cover_letter_pdf(
                        name,
                        paragraphs,
                        cl_template,
                        str(output_path),
                    )

                progress_bar.progress(70)

                if success:
                    progress_bar.progress(100)
                    status_text.markdown(f'<div style="font-size:13px;color:#1D9E75;padding:8px 0;"><span style="color:#1D9E75;">✓</span> Cover letter exported to: {output_path.name}</div>', unsafe_allow_html=True)
                    import time; time.sleep(1)
                    progress_container.empty()

                    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if is_docx else "application/pdf"
                    with open(output_path, "rb") as f:
                        st.download_button(
                            f"Download Cover Letter {cl_format}",
                            f,
                            file_name=output_path.name,
                            mime=mime,
                        )
                else:
                    progress_bar.progress(100)
                    renderer_hint = "python-docx" if is_docx else "WeasyPrint"
                    status_text.markdown(f'<div style="font-size:13px;color:#FF6B6B;padding:8px 0;"><span style="color:#FF6B6B;">✗</span> Export failed. Ensure {renderer_hint} is installed.</div>', unsafe_allow_html=True)
                    import time; time.sleep(2)
                    progress_container.empty()

        render_phase_nav_buttons()


_STEP_LABELS = ["Profile", "Vacancy", "Generate", "Refine", "Export"]


def _phase_preconditions() -> dict:
    vacancy_ready = bool(st.session_state.get("vacancy_data"))
    docs_ready = bool(
        st.session_state.get("cv_content") or st.session_state.get("cover_letter_content")
    )
    return {1: True, 2: True, 3: vacancy_ready, 4: docs_ready, 5: docs_ready}


def render_phase_stepper() -> None:
    """T6.2 — Horizontal phase stepper rendered as clickable HTML using query-param navigation."""
    current_phase = st.session_state.get("current_phase", 1)
    unlocked = _phase_preconditions()

    parts = []
    for i, label in enumerate(_STEP_LABELS):
        pnum = i + 1
        is_done = pnum < current_phase
        is_active = pnum == current_phase
        is_clickable = unlocked[pnum] and not is_active

        state_cls = "done" if is_done else ("active" if is_active else "future")
        if is_clickable:
            state_cls += " clickable"
        display = "✓" if is_done else str(pnum)

        if is_clickable:
            parts.append(
                f'<a class="stepper-link" href="?_nav={pnum}">'
                f'<div class="stepper-step {state_cls}">'
                f'<div class="stepper-circle">{display}</div>'
                f'<div class="stepper-label">{label}</div>'
                f'</div></a>'
            )
        else:
            parts.append(
                f'<div class="stepper-step {state_cls}">'
                f'<div class="stepper-circle">{display}</div>'
                f'<div class="stepper-label">{label}</div>'
                f'</div>'
            )

        if i < 4:
            conn_cls = "done" if is_done else ""
            parts.append(f'<div class="stepper-connector {conn_cls}"></div>')

    st.markdown(
        '<nav class="stepper-nav">' + "".join(parts) + "</nav>"
        '<hr style="border:none;border-top:1px solid #1E1E2E;margin:4px 0 20px;">',
        unsafe_allow_html=True,
    )


def main():
    """Main application."""
    st.set_page_config(
        page_title="PAS · Professional Alignment System",
        page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%230A0A0F'/><text x='50%25' y='56%25' font-family='Inter,sans-serif' font-size='16' font-weight='700' fill='%236C63FF' text-anchor='middle' dominant-baseline='middle'>P</text></svg>",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply Obsidian Pro dark mode
    apply_dark_mode()

    # Initialize session state
    initialize_session_state()

    # ── T6.2: Handle stepper query-param navigation ──────────────────────────
    if "_nav" in st.query_params:
        try:
            req_phase = int(st.query_params["_nav"])
            if 1 <= req_phase <= 5:
                precond = _phase_preconditions()
                if precond.get(req_phase, False):
                    st.session_state.current_phase = req_phase
                    st.session_state.show_ai_settings = False
                else:
                    st.session_state._nav_blocked_phase = req_phase
        except (ValueError, KeyError):
            pass
        del st.query_params["_nav"]
        st.rerun()

    # ========== SIDEBAR ==========
    # App Logo / Title
    st.sidebar.markdown('<div class="app-title" style="font-size:26px;font-weight:700;color:#E0E0F0;letter-spacing:-0.02em;margin-bottom:4px;">PAS</div>', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="app-subtitle" style="font-size:11px;font-weight:400;color:#6B6B8A;letter-spacing:0.03em;margin-bottom:20px;">Professional Alignment System</div>', unsafe_allow_html=True)

    # Check inference server connection
    settings = load_settings()
    base_url = settings["ollama"]["base_url"]
    ollama_running = check_ollama_connection(base_url)

    if ollama_running:
        st.sidebar.markdown('<div class="status-badge status-connected" style="background:#0A1A10;border:1px solid #00AA6E33;border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:8px;margin-bottom:4px;"><div style="width:18px;height:18px;background:#1D9E75;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;">✓</div><span style="font-size:13px;font-weight:500;color:#00CC88;">Inference server ready</span></div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-badge status-disconnected" style="background:#1A0A0A;border:1px solid #E24B4A33;border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:8px;margin-bottom:4px;"><div style="width:18px;height:18px;background:#E24B4A;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:11px;">!</div><span style="font-size:13px;font-weight:500;color:#FF6B6B;">Inference server offline</span></div>', unsafe_allow_html=True)

    st.sidebar.markdown('<hr style="border-top:1px solid #1E1E2E;margin:20px 0;border:none;border-top:1px solid #1E1E2E;">', unsafe_allow_html=True)

    # Current phase indicator (replaces the radio — stepper IS the navigation)
    current_phase_num = st.session_state.get("current_phase", 1)
    current_label = _STEP_LABELS[current_phase_num - 1] if 1 <= current_phase_num <= 5 else ""
    st.sidebar.markdown(
        f'<div style="font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:0.1em;'
        f'color:#6B6B8A;margin-bottom:8px;">Current phase</div>'
        f'<div style="font-size:13px;font-weight:600;color:#E0E0F0;padding:8px 12px;'
        f'background:#16163A;border-radius:8px;border:1px solid #6C63FF44;margin-bottom:4px;">'
        f'<span style="color:#6C63FF;margin-right:8px;">{current_phase_num}.</span>{current_label}</div>',
        unsafe_allow_html=True,
    )

    # AI Settings button
    st.sidebar.markdown('<hr style="border:none;border-top:1px solid #1E1E2E;margin:16px 0 12px;">', unsafe_allow_html=True)
    if st.sidebar.button("AI Settings", use_container_width=True, key="ai_settings_btn"):
        st.session_state.show_ai_settings = True
        st.rerun()

    # Sidebar footer
    st.sidebar.markdown('<div class="sidebar-footer" style="margin-top:auto;padding-top:16px;border-top:1px solid #1E1E2E;font-size:11px;color:#6B6B8A;line-height:1.6;font-weight:300;">All processing is local.<br>Your data never leaves your machine.</div>', unsafe_allow_html=True)

    # Exit button
    if st.sidebar.button("Exit Application", use_container_width=True, key="exit_btn"):
        st.session_state.exit_app = True
        st.rerun()

    # Handle exit
    if st.session_state.get("exit_app", False):
        st.sidebar.markdown("""
        <script>
            setTimeout(function() {
                window.open('', '_self').close();
                window.close();
            }, 500);
        </script>
        """, unsafe_allow_html=True)
        import os, signal
        os.kill(os.getpid(), signal.SIGTERM)

    # ========== MAIN CONTENT ==========
    current_phase = st.session_state.get("current_phase", 1)

    if st.session_state.get("show_ai_settings", False):
        ai_settings.render()
        return

    # Show horizontal stepper at top of all phase pages
    render_phase_stepper()

    # Show blocked-phase warning if user tried to jump to a locked phase
    if st.session_state.get("_nav_blocked_phase"):
        blocked = st.session_state.pop("_nav_blocked_phase")
        phase_label = _STEP_LABELS[blocked - 1] if 1 <= blocked <= 5 else str(blocked)
        st.warning(
            f"Phase {blocked} ({phase_label}) is not yet available. "
            "Complete the earlier phases first.",
            icon="⚠️",
        )

    if current_phase == 1:
        phase_profile_creation()
    elif current_phase == 2:
        phase_vacancy_analysis()
    elif current_phase == 3:
        phase_document_generation()
    elif current_phase == 4:
        phase_refinement()
    else:
        phase_export()


if __name__ == "__main__":
    main()

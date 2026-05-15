"""
Pydantic schemas for all LLM-produced JSON in PAS.

These models ensure validated, structured data from LLM outputs.
Malformed LLM output fails loudly via ValidationError instead of silently degrading.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


class VacancyData(BaseModel):
    """Schema for parsed job vacancy data."""
    language: str = Field(default="en", description="Language of the vacancy (en or es)")
    domain: str = Field(default="unknown", description="Industry/domain category")
    seniority: str = Field(default="mid", description="Seniority level")
    suggested_tone: str = Field(default="technical_engineering", description="Suggested communication tone")
    keywords: list[str] = Field(default_factory=list, description="Key skills and qualifications")
    responsibilities: list[str] = Field(default_factory=list, description="Main responsibilities")
    requirements: list[str] = Field(default_factory=list, description="Requirements")
    company_info: str = Field(default="", description="Company information")
    job_title: str = Field(default="", description="Job title")


class StrongPoint(BaseModel):
    """Schema for a strong point in profile-vacancy matching."""
    vacancy_term: str = Field(description="Specific requirement from vacancy")
    profile_evidence: str = Field(description="Matching evidence from profile")
    rationale: str = Field(description="Brief explanation of the match")


class MatchResult(BaseModel):
    """Schema for profile-vacancy match results."""
    strong_points: list[StrongPoint] = Field(default_factory=list, description="Strong matching points")
    gaps: list[str] = Field(default_factory=list, description="Identified gaps")
    alignment_score: int = Field(default=50, description="Overall alignment score 0-100")


class ExperienceEntry(BaseModel):
    """Schema for a CV experience entry."""
    title: str = Field(default="", description="Job title")
    company: str = Field(default="", description="Company name")
    start: str = Field(default="", description="Start date")
    end: str = Field(default="", description="End date")
    achievements: list[str] = Field(default_factory=list, description="Achievement bullets")


class CVContent(BaseModel):
    """Schema for generated CV content."""
    executive_summary: str = Field(description="Executive summary text")
    tailored_experience: list[ExperienceEntry] = Field(default_factory=list, description="Tailored experience entries")
    highlighted_skills: list[str] = Field(default_factory=list, description="Skills to emphasize")
    ats_keywords: list[str] = Field(default_factory=list, description="Important ATS keywords")
    rationale: str = Field(description="Model's explanation of key framing choices (required)")


class CoverLetter(BaseModel):
    """Schema for generated cover letter."""
    paragraphs: list[str] = Field(description="Cover letter paragraphs")
    paragraph_intents: list[str] = Field(description="Intent label per paragraph (required)")
    rationale: str = Field(description="Model's explanation of key framing choices (required)")


class RefinedSection(BaseModel):
    """Schema for refined document sections."""
    revised_text: str = Field(description="Revised text after refinement")
    change_summary: Optional[str] = Field(default=None, description="Summary of changes made")


# ---------------------------------------------------------------------------
# T2.2 — Outline planning models
# ---------------------------------------------------------------------------

class WeaknessNote(BaseModel):
    """A specific weakness in a document section."""
    paragraph_index: int = Field(description="0-based index of the weak section")
    issue: str = Field(description="Description of the weakness")


class Critique(BaseModel):
    """Structured audit of a generated document produced by the Qwen critique stage."""
    missing_keywords: list[str] = Field(default_factory=list, description="Vacancy keywords absent from the draft")
    weak_paragraphs: list[WeaknessNote] = Field(default_factory=list, description="Vague or metric-free sections")
    tone_drift: list[str] = Field(default_factory=list, description="Phrases where tone deviates from target")
    ats_issues: list[str] = Field(default_factory=list, description="Structural problems hurting ATS parsing")
    factual_concerns: list[str] = Field(default_factory=list, description="Claims not supported by profile")
    overall_severity: Literal["none", "minor", "major"] = Field(description="Severity of issues found")


class ParagraphPlan(BaseModel):
    """Plan for a single cover letter paragraph."""
    intent: str = Field(description="Paragraph intent label (intro_hook, fit, evidence, cta, ...)")
    target_keywords: list[str] = Field(default_factory=list, description="Vacancy keywords this paragraph must hit")
    evidence_refs: list[str] = Field(default_factory=list, description="Specific profile evidence to draw from")
    target_words: int = Field(default=80, description="Target word count for this paragraph")


class CLOutline(BaseModel):
    """Structured outline for a cover letter produced by the Qwen planning stage."""
    paragraph_count: int = Field(description="Total number of paragraphs")
    paragraphs: list[ParagraphPlan] = Field(description="One plan per paragraph")


class CVSectionPlan(BaseModel):
    """Plan for a single CV section (executive summary or experience entry)."""
    section: str = Field(description="Section label: 'executive_summary' or 'Job Title at Company'")
    target_keywords: list[str] = Field(default_factory=list, description="Vacancy keywords to mirror")
    evidence_refs: list[str] = Field(default_factory=list, description="Profile evidence to reference")
    key_metrics: list[str] = Field(default_factory=list, description="Specific metrics/numbers to include")
    target_words: int = Field(default=100, description="Target word count")


class CVOutline(BaseModel):
    """Structured outline for a CV produced by the Qwen planning stage."""
    executive_summary: CVSectionPlan = Field(description="Plan for the executive summary")
    tailored_experience: list[CVSectionPlan] = Field(default_factory=list, description="One plan per experience entry")

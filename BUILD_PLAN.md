# PAS - Professional Alignment System
## Build Plan (v2) - From Scratch

---

### Core Purpose
A privacy-first, offline career document generator that consolidates a professional profile into a reusable format, then analyzes job vacancies against it to produce tailored, ATS-optimized CVs and cover letters in **English only**.

---

### Hybrid LLM Strategy

| Model | Strength | Used For |
|---|---|---|
| **Qwen 2.5 Coder** (7B) | Structured reasoning, JSON parsing, precision extraction | Vacancy parsing, skill matching, strong points generation, ATS keyword extraction, JSON validation, tone classification |
| **DeepSeek-R1** (7B) | Long-form prose, nuanced writing, tone adaptation | CV executive summary, cover letter generation, refinement based on user feedback |

**Flow:**
1. **Qwen** parses the vacancy → extracts structured data (skills, requirements, seniority, domain)
2. **Qwen** compares vacancy data against the profile → produces strong points (structured findings)
3. **DeepSeek** generates the tailored CV summary and cover letter → using strong points + selected tone
4. **DeepSeek** handles refinement cycles → rewrites any section based on user feedback

---

### User Workflows

#### Phase 1: Profile Creation
- User uploads one or more source files: PDF CV, LinkedIn CSV export, or plain text
- App parses, merges, and structures everything into a single **profile** (`profile.json`)
- Profile becomes the canonical source for all future document generation
- User can review and edit the consolidated profile before saving

#### Phase 2: Vacancy Analysis *(Qwen)*
- User pastes or uploads a vacancy description
- **Qwen** analyzes the vacancy:
  - **Language detection:** English or Spanish (output language is always English regardless)
  - **Domain classification:** identifies industry/seniority level
  - **Keyword extraction:** skills, qualifications, requirements
- **Qwen** compares vacancy keywords against the profile:
  - Produces **strong points** (structured match findings)
  - Identifies alignment gaps
- Results displayed for review before proceeding

#### Phase 3: Tone & Document Generation *(DeepSeek)*
- App suggests a tone based on vacancy domain; user can confirm or choose from available options:
  - **Corporate / Executive** -- formal, leadership-focused
  - **Technical / Engineering** -- skills-heavy, tool-oriented
  - **Compliance / Risk** -- regulatory, audit-focused
  - **Operations / Projects** -- delivery, metrics-driven
  - **Fintech / Digital** -- innovation, startup-style
  - **Social Impact / Mission** -- purpose-driven, values-focused
- **DeepSeek** generates:
  - A **tailored CV** (executive summary + experience highlights adjusted to vacancy expectations)
  - A **cover letter** (structured, ATS-friendly, vacancy-specific, 5 paragraphs)
- Both documents are optimized to pass ATS filters while maximizing relevance

#### Phase 4: Iterative Refinement *(DeepSeek)*
- User sees the generated CV text, cover letter text, and strong points
- User selects any item and provides feedback/instructions for improvement
- **DeepSeek** regenerates only the selected item based on feedback
- Loop continues until user is satisfied

#### Phase 5: Export
- User selects a visual template for the CV and cover letter
- User exports both as styled, print-ready PDFs

---

### Key Principles

| Principle | Description |
|---|---|
| **Profile-first** | Built once, reused for every vacancy. All generation starts from it. |
| **Offline & private** | All LLM processing runs locally via Ollama. No data leaves the machine. |
| **English-only** | All UI text, code, variable names, comments, and generated output are in English. |
| **Hybrid LLM** | Qwen for structure/analysis, DeepSeek for writing/refinement. |
| **ATS-optimized** | Documents structured to score well in Applicant Tracking Systems. |
| **Iterative** | User controls refinement through feedback cycles before committing to PDF. |

---

### Project Structure

```
PAS/
├── profile.json              # Canonical user profile (generated once, reused)
├── config/
│   └── settings.json         # Ollama endpoints, model names, default params
├── templates/
│   ├── cv_executive.html     # CV template - Executive style
│   ├── cv_modern.html        # CV template - Modern style
│   ├── cv_technical.html     # CV template - Technical style
│   ├── cl_executive.html     # Cover letter template - Executive
│   ├── cl_modern.html        # Cover letter template - Modern
│   └── cl_technical.html     # Cover letter template - Technical
├── src/
│   ├── profile/
│   │   ├── pdf_ingest.py     # Parse PDF CV → structured data
│   │   ├── csv_ingest.py     # Parse LinkedIn CSV → structured data
│   │   ├── text_ingest.py    # Parse plain text → structured data
│   │   └── merger.py         # Merge all sources → profile.json
│   ├── analysis/
│   │   ├── vacancy_parser.py       # Qwen: parse vacancy → structured data
│   │   ├── match_engine.py         # Qwen: vacancy vs profile → strong points
│   │   └── tone_classifier.py      # Qwen: suggest tone from vacancy domain
│   ├── generation/
│   │   ├── cv_generator.py         # DeepSeek: generate tailored CV content
│   │   ├── cover_letter_generator.py # DeepSeek: generate cover letter
│   │   └── ats_optimizer.py        # Inject/verify ATS keywords
│   ├── refinement/
│   │   └── feedback_engine.py      # DeepSeek: rewrite section from feedback
│   └── export/
│       └── pdf_renderer.py         # Jinja2 + WeasyPrint → PDF
├── ui/
│   └── app.py                  # Single Streamlit app, phased flow
├── shared_styles.py            # Dark mode CSS
├── requirements.txt
└── run.bat                     # Windows launcher
```

---

### Data Formats

**Profile (`profile.json`):**
```json
{
  "personal_info": { "name": "", "email": "", "phone": "", "location": "", "linkedin": "", "portfolio": "" },
  "summary": "",
  "experience": [{ "title": "", "company": "", "start": "", "end": "", "achievements": [], "skills_used": [] }],
  "education": [{ "degree": "", "institution": "", "year": "" }],
  "skills": { "technical": [], "soft": [], "languages": [{ "language": "", "level": "" }] },
  "certifications": [{ "name": "", "issuer": "", "year": "" }],
  "projects": [{ "name": "", "description": "", "url": "" }]
}
```

**Vacancy Analysis Output:**
```json
{
  "language": "en|es",
  "domain": "fintech",
  "seniority": "senior",
  "suggested_tone": "fintech_digital",
  "keywords": ["skill1", "skill2"],
  "strong_points": [
    { "vacancy_term": "", "profile_evidence": "", "rationale": "" }
  ],
  "gaps": ["gap1", "gap2"]
}
```

---

### Tech Stack

| Technology | Purpose |
|---|---|
| **Streamlit** | Web UI framework |
| **Ollama** | Local LLM inference engine |
| **qwen2.5-coder:7b** | Vacancy parsing, skill matching, strong points, tone classification |
| **deepseek-r1:7b** | CV/cover letter generation, refinement |
| **Jinja2** | HTML template engine |
| **WeasyPrint** | HTML-to-PDF rendering |
| **pdfplumber** | PDF text extraction |
| **BeautifulSoup + lxml** | CSV/web parsing |
| **jsonschema** | JSON validation |

---

### Rules
1. **All text in English** -- UI labels, code, comments, variable names, generated output. No Spanish anywhere.
2. **Build from scratch** -- no reuse of old codebase structure or files.
3. **Single Streamlit app** -- phased flow, no satellite pages.
4. **Profile-first** -- `profile.json` is built once, reused forever.
5. **Hybrid LLM** -- Qwen for structure, DeepSeek for writing. Clear separation.
6. **ATS-optimized** -- keyword injection, structured output, clean formatting.

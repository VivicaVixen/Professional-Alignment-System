"""
Obsidian Pro theme styles.
Complete visual redesign — dark, violet-accented, Inter font.
"""

OBSSIDIAN_PRO_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ========== CSS VARIABLES ========== */
:root {
    /* Backgrounds */
    --bg-base:        #0A0A0F;
    --bg-surface:     #111118;
    --bg-elevated:    #16163A;
    --bg-input:       #0D0D1A;

    /* Borders */
    --border-subtle:  #1E1E2E;
    --border-focus:   #6C63FF;
    --border-muted:   #2E2E4E;

    /* Text */
    --text-primary:   #E0E0F0;
    --text-secondary: #9090CC;
    --text-muted:     #6B6B8A;

    /* Accent / Interactive */
    --accent-primary:   #6C63FF;
    --accent-secondary: #9B5DE5;
    --accent-glow:      #6C63FF22;

    /* Status */
    --status-green-bg:   #0A1A10;
    --status-green-border: #00AA6E33;
    --status-green-text: #00CC88;
    --status-red-bg:     #1A0A0A;
    --status-red-border: #E24B4A33;
    --status-red-text:   #FF6B6B;
}

/* ========== GLOBAL / ROOT ========== */
.stApp {
    background: var(--bg-base) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}

.main .block-container {
    background: var(--bg-base) !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 800px !important;
}

/* ========== HEADINGS ========== */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
}

h1 {
    font-size: 22px !important;
    border-bottom: 1px solid var(--border-subtle) !important;
    padding-bottom: 12px !important;
    margin-bottom: 24px !important;
}

h2 {
    font-size: 18px !important;
    font-weight: 600 !important;
}

h3 {
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* Body / paragraph text */
p, span, li, label {
    color: var(--text-secondary) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}

/* ========== SIDEBAR ========== */
section[data-testid="stSidebar"] {
    background: #0D0D18 !important;
    border-right: 1px solid var(--border-subtle) !important;
    width: 260px !important;
    min-width: 260px !important;
}

section[data-testid="stSidebar"] .block-container {
    padding: 24px 16px !important;
}

/* Sidebar title */
section[data-testid="stSidebar"] h1 {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.02em !important;
    border: none !important;
    padding: 0 !important;
    margin-bottom: 4px !important;
}

/* Sidebar subtitle */
section[data-testid="stSidebar"] .stMarkdown p {
    font-size: 11px !important;
    font-weight: 400 !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.03em !important;
    margin-bottom: 20px !important;
}

/* Sidebar separators */
section[data-testid="stSidebar"] hr {
    border-top: 1px solid var(--border-subtle) !important;
    margin: 20px 0 !important;
    border-color: var(--border-subtle) !important;
}

/* Navigation label */
section[data-testid="stSidebar"] .stRadio > label,
section[data-testid="stSidebar"] .stRadio > div > p {
    font-size: 10px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--text-muted) !important;
    margin-bottom: 10px !important;
}

/* Nav radio items */
section[data-testid="stSidebar"] .stRadio > div {
    display: flex !important;
    flex-direction: column !important;
    gap: 2px !important;
}

section[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
    gap: 2px !important;
}

section[data-testid="stSidebar"] .stRadio [data-testid="stRadio"] > label {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 8px 10px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    color: var(--text-muted) !important;
    transition: all 0.15s ease !important;
    margin-bottom: 2px !important;
}

section[data-testid="stSidebar"] .stRadio [data-testid="stRadio"] > label:hover {
    background: #13132299 !important;
    color: var(--text-secondary) !important;
}

/* Active nav state */
section[data-testid="stSidebar"] .stRadio [data-testid="stRadio"] input:checked + label {
    background: var(--bg-elevated) !important;
    color: var(--text-primary) !important;
    font-weight: 500 !important;
    border-left: 3px solid var(--accent-primary) !important;
    padding-left: 7px !important;
}

/* Custom radio circles */
section[data-testid="stSidebar"] .stRadio input[type="radio"] {
    appearance: none !important;
    width: 14px !important;
    height: 14px !important;
    border-radius: 50% !important;
    border: 2px solid var(--border-muted) !important;
    background: transparent !important;
    flex-shrink: 0 !important;
    transition: all 0.15s ease !important;
    margin: 0 !important;
    padding: 0 !important;
}

section[data-testid="stSidebar"] .stRadio input[type="radio"]:checked {
    border-color: var(--accent-primary) !important;
    background: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* Sidebar footer */
section[data-testid="stSidebar"] > div > div:last-child {
    margin-top: auto !important;
    padding-top: 16px !important;
    border-top: 1px solid var(--border-subtle) !important;
    font-size: 11px !important;
    color: var(--text-muted) !important;
    line-height: 1.6 !important;
    font-weight: 300 !important;
}

/* ========== STATUS BADGES (Ollama) ========== */
.stAlert {
    border-radius: 8px !important;
    padding: 10px 14px !important;
    border: 1px solid !important;
}

.stAlert[data-baseweb="notification"] {
    background: var(--status-green-bg) !important;
    border-color: var(--status-green-border) !important;
}

.stAlert[data-baseweb="notification"] p {
    color: var(--status-green-text) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

.stAlert[data-baseweb="notification"][data-testid="stAlert"] {
    background: var(--status-red-bg) !important;
    border-color: var(--status-red-border) !important;
}

.stAlert[data-baseweb="notification"][data-testid="stAlert"] p {
    color: var(--status-red-text) !important;
}

/* Success / info alerts in main content */
.stAlert {
    background: var(--bg-surface) !important;
    border-color: var(--border-subtle) !important;
}

.stAlert p {
    color: var(--text-secondary) !important;
}

/* ========== PHASE DESCRIPTIVE SUBTITLE ========== */
.stMarkdown p {
    font-size: 13px !important;
    color: var(--text-muted) !important;
}

/* ========== SUB-SECTION CARDS ========== */
/* Tone section card */
.stSelectbox > label,
.stSelectbox > div > label {
    font-size: 11px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text-muted) !important;
    margin-bottom: 6px !important;
}

/* ========== FIELD LABELS ========== */
label, .stTextInput > label, .stTextArea > label {
    font-size: 11px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text-muted) !important;
    margin-bottom: 6px !important;
}

/* ========== INPUTS / TEXTAREA / SELECT ========== */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    background: var(--bg-surface) !important;
    border: none !important;
    border-left: 3px solid var(--accent-primary) !important;
    border-radius: 0 6px 6px 0 !important;
    color: var(--text-secondary) !important;
    padding: 10px 14px !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
    outline: none !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-left-color: var(--accent-secondary) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ========== FILE UPLOADER ========== */
.stFileUploader > div {
    background: var(--bg-surface) !important;
    border: 2px dashed var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 20px !important;
}

.stFileUploader label,
.stFileUploader p {
    color: var(--text-muted) !important;
}

/* ========== BUTTONS ========== */
/* Primary buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 10px 20px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    cursor: pointer !important;
    transition: opacity 0.2s ease, transform 0.1s ease !important;
}

.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    transform: scale(0.98) !important;
}

.stButton > button[kind="primary"]:active {
    transform: scale(0.98) !important;
}

/* Secondary / default buttons */
.stButton > button[kind="secondary"],
.stButton > button[kind="borderless"] {
    background: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-muted) !important;
    border-radius: 6px !important;
    padding: 10px 20px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
}

.stButton > button[kind="secondary"]:hover {
    background: var(--bg-elevated) !important;
}

/* ========== TAGS / INFO CHIPS ========== */
/* Markdown rendered tags */
.stMarkdown code {
    background: var(--bg-elevated) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-muted) !important;
    border-radius: 4px !important;
    padding: 6px 12px !important;
    font-size: 12px !important;
    display: inline-block !important;
    margin: 4px 4px 4px 0 !important;
}

/* ========== EXPANDER (Strong Points) ========== */
.streamlit-expanderHeader {
    background: var(--bg-surface) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
    font-weight: 500 !important;
}

.streamlit-expanderHeader:hover {
    background: var(--bg-elevated) !important;
}

.streamlit-expanderContent {
    background: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
    border-top: none !important;
    border-radius: 0 0 6px 6px !important;
    padding: 14px !important;
}

/* Expander content text - override global p/span styles */
.streamlit-expanderContent p,
.streamlit-expanderContent span,
.streamlit-expanderContent div {
    color: var(--text-secondary) !important;
    font-size: 13px !important;
    line-height: 1.5 !important;
}

/* Expander label text */
.streamlit-expanderContent strong {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
}

/* ========== METRICS ========== */
[data-testid="stMetric"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
    padding: 16px !important;
}

[data-testid="stMetric"] p {
    color: var(--text-muted) !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

[data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-size: 18px !important;
    font-weight: 600 !important;
}

/* ========== PROGRESS BAR ========== */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) !important;
    border-radius: 4px !important;
    transition: width 0.6s ease !important;
}

.stProgress > div > div > div {
    background: var(--border-subtle) !important;
    height: 6px !important;
    border-radius: 4px !important;
}

/* ========== TEXT AREAS (Generated content) ========== */
.stTextArea > div > div > textarea {
    background: var(--bg-input) !important;
    border: 1px solid var(--border-subtle) !important;
    border-left: 3px solid var(--accent-primary) !important;
    border-radius: 0 6px 6px 0 !important;
    color: var(--text-secondary) !important;
    padding: 16px !important;
    font-size: 13px !important;
    line-height: 1.7 !important;
    min-height: 120px !important;
}

/* ========== INLINE FEEDBACK STATES ========== */
/* Success message */
.stAlert[data-baseweb="notification"] div {
    background: #0A1F14 !important;
    border: 1px solid #00AA6E33 !important;
    color: #00CC88 !important;
    border-radius: 6px !important;
    padding: 8px 14px !important;
    font-size: 12px !important;
}

/* ========== ATS SCORE STYLING ========== */
/* Target ATS score markdown */
.stMarkdown p strong {
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: var(--text-muted) !important;
    font-weight: 500 !important;
}

/* ========== RADIO (Horizontal - refinement doc type) ========== */
.stRadio > div[role="radiogroup"] {
    display: flex !important;
    gap: 12px !important;
}

.stRadio > div[role="radiogroup"] > label {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 6px 12px !important;
    border-radius: 6px !important;
    cursor: pointer !important;
    font-size: 13px !important;
    color: var(--text-secondary) !important;
    transition: background 0.15s ease !important;
}

.stRadio > div[role="radiogroup"] > label:hover {
    background: var(--bg-elevated) !important;
}

.stRadio input[type="radio"] {
    appearance: none !important;
    width: 14px !important;
    height: 14px !important;
    border-radius: 50% !important;
    border: 2px solid var(--border-muted) !important;
    background: transparent !important;
    flex-shrink: 0 !important;
    transition: all 0.15s ease !important;
}

.stRadio input[type="radio"]:checked {
    border-color: var(--accent-primary) !important;
    background: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px var(--accent-glow) !important;
}

/* ========== EXIT BUTTON ========== */
button[kind="exit_btn"],
#exit_btn {
    background: transparent !important;
    color: #E24B4A !important;
    border: 1px solid #E24B4A33 !important;
    border-radius: 6px !important;
    padding: 8px 16px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

button[kind="exit_btn"]:hover,
#exit_btn:hover {
    background: #E24B4A22 !important;
    border-color: #E24B4A !important;
}

/* ========== EXIT BUTTON (sidebar specific) ========== */
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #6B6B8A !important;
    border: 1px solid #2E2E4E !important;
    border-radius: 6px !important;
    padding: 8px 16px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: #1A0A0A !important;
    border-color: #E24B4A !important;
    color: #FF6B6B !important;
}
.stDownloadButton > button {
    background: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-muted) !important;
    border-radius: 6px !important;
    padding: 10px 20px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    cursor: pointer !important;
    transition: background 0.2s ease !important;
}

.stDownloadButton > button:hover {
    background: var(--bg-elevated) !important;
}

/* ========== COLUMNS SPACING ========== */
[data-testid="column"] {
    padding: 0 8px !important;
}

/* ========== DIVIDER ========== */
hr {
    border-color: var(--border-subtle) !important;
}

/* ========== SPINNER (loading) ========== */
@keyframes spin {
    to { transform: rotate(360deg); }
}

/* ========== PROGRESS DOT PULSE ========== */
@keyframes progress-pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #6C63FF, #9B5DE5) !important;
    border-radius: 4px !important;
    transition: width 0.6s ease !important;
}

/* ========== STATUS DOT PULSE ========== */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}

/* ========== SCROLLBAR ========== */
::-webkit-scrollbar {
    width: 6px !important;
}

::-webkit-scrollbar-track {
    background: var(--bg-base) !important;
}

::-webkit-scrollbar-thumb {
    background: var(--border-muted) !important;
    border-radius: 3px !important;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-primary) !important;
}

/* ========== HEADER / TOP BAR ========== */
header[data-testid="stHeader"] {
    background: transparent !important;
}

header [data-testid="stToolbar"] {
    background: transparent !important;
}

/* ========== REMOVE STREAMLIT BRANDING ========== */
header [data-testid="stDecoration"] {
    display: none !important;
}

header [data-testid="stStatusWidget"] {
    display: none !important;
}

/* ========== TOOLTIP ========== */
[role="tooltip"] {
    background: var(--bg-elevated) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-muted) !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ========== CHAT (if any) ========== */
[data-testid="stChatMessage"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 8px !important;
}

/* ========== TABLES / DATAFRAMES ========== */
.dataframe {
    background-color: var(--bg-surface) !important;
    color: var(--text-secondary) !important;
    border-color: var(--border-subtle) !important;
}

/* T2.5: native st.dataframe (telemetry panel) — minimal container styling
   so it sits cleanly inside the dark-themed expander.
   Uses existing CSS variables only, no new colors. */
[data-testid="stDataFrame"] {
    background: var(--bg-surface) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
}

/* ========== CODE BLOCKS ========== */
.stCode {
    background-color: var(--bg-input) !important;
    color: var(--text-secondary) !important;
    border: 1px solid var(--border-subtle) !important;
}

/* ========== DIFF VIEW (T3.2) ========== */
.diff-removed {
    background: var(--status-red-bg);
    color: var(--status-red-text);
    border-radius: 3px;
    padding: 1px 4px;
    text-decoration: line-through;
    opacity: 0.85;
}

.diff-added {
    background: var(--status-green-bg);
    color: var(--status-green-text);
    border-radius: 3px;
    padding: 1px 4px;
}

/* ========== PHASE STEPPER (T6.2) ========== */
nav.stepper-nav {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding: 20px 0 4px;
    width: 100%;
    gap: 0;
}

.stepper-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    flex: 0 0 72px;
    text-decoration: none !important;
}

.stepper-step a { text-decoration: none !important; }

.stepper-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 700;
    border: 2px solid var(--border-muted);
    background: var(--bg-surface);
    color: var(--text-muted);
    transition: all 0.2s;
    user-select: none;
}

.stepper-step.done .stepper-circle {
    background: var(--status-green-bg);
    border-color: #00CC8888;
    color: var(--status-green-text);
}

.stepper-step.active .stepper-circle {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: #ffffff;
    box-shadow: 0 0 0 4px var(--accent-glow);
}

.stepper-step.clickable:hover .stepper-circle {
    border-color: var(--accent-primary);
    color: var(--accent-primary);
    transform: scale(1.08);
}

.stepper-step.done.clickable:hover .stepper-circle {
    border-color: var(--status-green-text);
    transform: scale(1.08);
}

.stepper-label {
    font-size: 11px;
    color: var(--text-muted);
    font-weight: 500;
    text-align: center;
    letter-spacing: 0.03em;
    white-space: nowrap;
}

.stepper-step.active .stepper-label {
    color: var(--text-primary);
    font-weight: 600;
}

.stepper-step.done .stepper-label {
    color: var(--text-secondary);
}

.stepper-connector {
    flex: 1;
    height: 2px;
    background: var(--border-muted);
    align-self: flex-start;
    margin-top: 19px;
    min-width: 20px;
    max-width: 60px;
}

.stepper-connector.done {
    background: #00CC8866;
}

a.stepper-link {
    text-decoration: none !important;
    cursor: pointer;
}

a.stepper-link:focus { outline: none; }

/* Enhanced stepper visibility — clickable steps get a subtle button effect */
.stepper-step.clickable {
    cursor: pointer;
}

.stepper-step.clickable:hover .stepper-label {
    color: var(--accent-primary) !important;
}

.stepper-step.clickable:hover {
    filter: brightness(1.15);
}

/* Subtle tooltip-like hint on hover for clickable steps */
.stepper-step.clickable .stepper-circle::after {
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 2px solid transparent;
    transition: border-color 0.2s;
}

.stepper-step.clickable:hover .stepper-circle::after {
    border-color: var(--accent-primary);
    opacity: 0.4;
}

.stepper-circle {
    position: relative;
}

/* ========== TEMPLATE THUMBNAILS (T6.4) ========== */
.tmpl-thumb {
    width: 120px;
    height: 160px;
    border-radius: 6px;
    border: 2px solid var(--border-muted);
    background: var(--bg-surface);
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
    display: flex;
    flex-direction: column;
    margin: 0 auto;
}

.tmpl-thumb.selected {
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px var(--accent-glow);
}

.tmpl-thumb:hover {
    transform: scale(1.04);
    border-color: var(--border-focus);
}

/* Executive: dark header with accent rule */
.tmpl-thumb.executive .tt-top {
    height: 28px;
    background: #0D0D18;
    border-bottom: 2px solid var(--accent-primary);
    flex-shrink: 0;
}

/* Modern: accent sidebar on the left */
.tmpl-thumb.modern {
    flex-direction: row;
}
.tmpl-thumb.modern .tt-top {
    width: 28px;
    height: 100%;
    background: linear-gradient(180deg, #6C63FF, #9B5DE5);
    flex-shrink: 0;
}

/* Technical: code-flavoured header strip */
.tmpl-thumb.technical .tt-top {
    height: 20px;
    background: #13131F;
    border-bottom: 1px solid var(--border-muted);
    flex-shrink: 0;
    position: relative;
}
.tmpl-thumb.technical .tt-top::before {
    content: '';
    position: absolute;
    left: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 36px;
    height: 4px;
    background: var(--accent-primary);
    opacity: 0.55;
    border-radius: 2px;
}

/* Shared body */
.tt-body {
    padding: 8px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.tt-name {
    height: 7px;
    background: var(--text-primary);
    border-radius: 2px;
    width: 80%;
    opacity: 0.65;
    margin-bottom: 3px;
}

.tt-rule {
    height: 1px;
    background: var(--border-subtle);
    margin: 2px 0;
}

.tt-line {
    height: 4px;
    background: var(--border-muted);
    border-radius: 2px;
    opacity: 0.8;
}
.tt-line.long  { width: 90%; }
.tt-line.med   { width: 65%; }
.tt-line.short { width: 45%; }
.tt-line.accent { background: var(--accent-primary); opacity: 0.25; }

/* Template label under thumbnail */
.tmpl-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
    text-align: center;
    margin-top: 6px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.tmpl-label.selected {
    color: var(--accent-primary);
    font-weight: 600;
}

/* ========== ATS KEYWORD CHIPS (T6.5) ========== */
:root {
    --warning-bg:     #1A1200;
    --warning-border: #EF9F2766;
    --warning-text:   #EF9F27;
}

.kw-chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 4px;
    border: 1px solid;
    font-size: 11px;
    font-weight: 500;
    margin: 3px 3px 3px 0;
    cursor: default;
    letter-spacing: 0.02em;
    font-family: 'Inter', sans-serif;
    transition: opacity 0.15s;
}

.kw-chip:hover { opacity: 0.8; }

.kw-chip.hit {
    background: var(--status-green-bg);
    border-color: #00CC8888;
    color: var(--status-green-text);
}

.kw-chip.partial {
    background: var(--warning-bg);
    border-color: var(--warning-border);
    color: var(--warning-text);
}

.kw-chip.miss {
    background: var(--status-red-bg);
    border-color: #E24B4A55;
    color: var(--status-red-text);
}

/* ========== NARROW / MOBILE LAYOUT (T6.6) ========== */
@media (max-width: 900px) {
    /* Force block display so Streamlit columns stack */
    [data-testid="column"] {
        width: 100% !important;
        flex: 0 0 100% !important;
        min-width: 100% !important;
        padding: 0 !important;
    }

    /* Tighten main container padding */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* Shrink sidebar */
    section[data-testid="stSidebar"] {
        width: 200px !important;
        min-width: 200px !important;
    }

    /* Stepper: hide text labels, keep circles functional */
    .stepper-label {
        display: none !important;
    }

    .stepper-circle {
        width: 32px !important;
        height: 32px !important;
        font-size: 13px !important;
    }

    .stepper-connector {
        margin-top: 15px !important;
        min-width: 12px !important;
        max-width: 32px !important;
    }

    nav.stepper-nav {
        padding: 12px 0 4px !important;
    }

    /* Keyword chips: allow wrapping (already inline-block; ensure no overflow) */
    .kw-chip {
        white-space: normal !important;
    }

    /* Template thumbnails: shrink slightly */
    .tmpl-thumb {
        width: 90px !important;
        height: 120px !important;
    }
}

@media (max-width: 480px) {
    /* Extra-narrow: hide sidebar text, keep controls */
    section[data-testid="stSidebar"] {
        width: 160px !important;
        min-width: 160px !important;
    }

    .stepper-connector {
        min-width: 6px !important;
        max-width: 16px !important;
    }
}
</style>
"""


def apply_dark_mode():
    """Apply Obsidian Pro styling to the Streamlit app."""
    import streamlit as st
    st.markdown(OBSSIDIAN_PRO_CSS, unsafe_allow_html=True)

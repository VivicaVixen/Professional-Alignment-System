# Task: Full Visual Redesign — "Obsidian Pro" Style

Redesign the complete UI of this application applying the "Obsidian Pro" dark theme.
Do NOT change any logic, functionality, or component structure. Styles only.

---

## COLOR PALETTE — use EXACTLY these values

### Backgrounds
```
--bg-base:        #0A0A0F   /* main app background */
--bg-surface:     #111118   /* cards, panels, sidebar */
--bg-elevated:    #16163A   /* inputs, tags, hover states */
--bg-input:       #0D0D1A   /* textareas, text fields */
```

### Borders
```
--border-subtle:  #1E1E2E   /* general borders */
--border-focus:   #6C63FF   /* left accent border on inputs */
--border-muted:   #2E2E4E   /* secondary borders */
```

### Text
```
--text-primary:   #E0E0F0   /* titles and main text */
--text-secondary: #9090CC   /* labels, supporting text */
--text-muted:     #6B6B8A   /* placeholders, metadata */
```

### Accent / Interactive
```
--accent-primary:   #6C63FF   /* main violet */
--accent-secondary: #9B5DE5   /* light violet for gradients */
--accent-glow:      #6C63FF22 /* subtle glow on focus */
```

---

## TYPOGRAPHY

- Main font: 'Inter', sans-serif
  Import from Google Fonts:
  `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');`
- Allowed weights: 300 (light), 400 (regular), 500 (medium), 600 (semibold)
- Sizes:
  - Section titles:   18–20px / weight 600 / color: var(--text-primary)
  - Field labels:     11px / weight 500 / uppercase / letter-spacing: 0.08em / color: var(--text-muted)
  - Body text:        13–14px / weight 400 / color: var(--text-secondary)
  - Metadata/badges:  11–12px / weight 400

---

## GENERAL LAYOUT

### Body / Root
```css
background: var(--bg-base);
color: var(--text-primary);
font-family: 'Inter', sans-serif;
```

### Sidebar
```css
background: #0D0D18;
border-right: 1px solid #1E1E2E;
width: 260px; /* fixed */
height: 100vh;
display: flex;
flex-direction: column;
padding: 24px 16px;
overflow-y: auto;
```

### Main Content Area
```css
padding: 32px 40px;
max-width: 800px;
background: transparent; /* inherits --bg-base */
```

---

## COMPONENTS — exact specifications

### Collapse Button ( « )
```css
position: absolute;
top: 16px;
right: 16px;
background: transparent;
border: 1px solid #1E1E2E;
border-radius: 6px;
color: #6B6B8A;
width: 28px;
height: 28px;
font-size: 12px;
cursor: pointer;
transition: background 0.2s, color 0.2s;
```
On hover:
```css
background: #16163A;
color: #9090CC;
```

### App Logo / Title
Title "PAS":
```css
font-size: 26px;
font-weight: 700;
color: #E0E0F0;
letter-spacing: -0.02em;
margin-bottom: 4px;
```
Subtitle "Professional Alignment System":
```css
font-size: 11px;
font-weight: 400;
color: #6B6B8A;
letter-spacing: 0.03em;
margin-bottom: 20px;
```

### Status Badge (e.g. "Ollama connected")
```css
background: #0A1A10;
border: 1px solid #00AA6E33;
border-radius: 8px;
padding: 10px 14px;
display: flex;
align-items: center;
gap: 8px;
margin-bottom: 4px;
```
Check icon:
```css
width: 18px;
height: 18px;
background: #1D9E75;
border-radius: 4px;
display: flex;
align-items: center;
justify-content: center;
color: #fff;
font-size: 11px;
```
Text "Ollama connected":
```css
font-size: 13px;
font-weight: 500;
color: #00CC88;
```
Disconnected state (class `.status-disconnected`):
```css
background: #1A0A0A;
border-color: #E24B4A33;
/* icon: background #E24B4A */
/* text: color #FF6B6B */
```

### Sidebar Separators
```css
border-top: 1px solid #1E1E2E;
margin: 20px 0;
```

### Navigation Section
Label "Navigation":
```css
font-size: 10px;
font-weight: 500;
text-transform: uppercase;
letter-spacing: 0.1em;
color: #6B6B8A;
margin-bottom: 10px;
```

Nav items (radio + label):
```css
display: flex;
align-items: center;
gap: 10px;
padding: 8px 10px;
border-radius: 6px;
cursor: pointer;
font-size: 13px;
font-weight: 400;
color: #6B6B8A;
transition: all 0.15s;
margin-bottom: 2px;
```
Default state:
```css
color: #6B6B8A;
background: transparent;
```
Hover:
```css
background: #13132299;
color: #9090CC;
```
Active state (current step):
```css
background: #16163A;
color: #E0E0F0;
font-weight: 500;
border-left: 3px solid #6C63FF;
padding-left: 7px; /* compensate for border */
```
Completed steps:
```css
color: #4A4A7A;
```

### Custom Radio Button
Hide native input:
```css
appearance: none;
```
Replace with CSS circle:
```css
width: 14px;
height: 14px;
border-radius: 50%;
border: 2px solid #2E2E4E;
background: transparent;
flex-shrink: 0;
transition: all 0.15s;
```
Active state:
```css
border-color: #6C63FF;
background: #6C63FF;
box-shadow: 0 0 0 3px #6C63FF22;
```
Completed state:
```css
border-color: #1D9E75;
background: #1D9E75;
```

### Sidebar Footer
```css
margin-top: auto; /* pushes to bottom */
padding-top: 16px;
border-top: 1px solid #1E1E2E;
font-size: 11px;
color: #6B6B8A;
line-height: 1.6;
font-weight: 300;
```

---

### Section Phase Titles (h1/h2)
```css
font-size: 22px;
font-weight: 600;
color: var(--text-primary);
border-bottom: 1px solid var(--border-subtle);
padding-bottom: 12px;
margin-bottom: 24px;
```
Descriptive subtitle below:
```css
font-size: 13px;
color: var(--text-muted);
```

### Sub-sections (e.g. "Select Tone")
```css
font-size: 16px;
font-weight: 600;
color: var(--text-primary);
background: var(--bg-surface);
border: 1px solid var(--border-subtle);
border-radius: 8px;
padding: 16px 20px;
margin-bottom: 16px;
```

### Field Labels
```css
font-size: 11px;
font-weight: 500;
text-transform: uppercase;
letter-spacing: 0.08em;
color: var(--text-muted);
margin-bottom: 6px;
```

### Inputs / Select / Textarea
```css
background: var(--bg-surface);
border: none;
border-left: 3px solid var(--accent-primary);
border-radius: 0 6px 6px 0;
color: var(--text-secondary);
padding: 10px 14px;
font-size: 13px;
font-family: 'Inter', sans-serif;
width: 100%;
outline: none;
transition: border-color 0.2s;
```
On focus:
```css
border-left-color: var(--accent-secondary);
box-shadow: 0 0 0 3px var(--accent-glow);
```

### Tags / Info Chips (e.g. "Innovation, startup-style, modern")
```css
background: var(--bg-elevated);
color: var(--text-secondary);
border: 1px solid var(--border-muted);
border-radius: 4px;
padding: 6px 12px;
font-size: 12px;
display: inline-block;
margin-top: 8px;
```

### Primary Buttons (e.g. "Generate CV")
```css
background: linear-gradient(135deg, #6C63FF, #9B5DE5);
color: #FFFFFF;
border: none;
border-radius: 6px;
padding: 10px 20px;
font-size: 13px;
font-weight: 600;
font-family: 'Inter', sans-serif;
cursor: pointer;
transition: opacity 0.2s, transform 0.1s;
```
On hover:  `opacity: 0.9`
On active: `transform: scale(0.98)`

### Secondary Buttons (e.g. "Generate Cover Letter")
```css
background: var(--bg-surface);
color: var(--text-secondary);
border: 1px solid var(--border-muted);
border-radius: 6px;
padding: 10px 20px;
font-size: 13px;
font-weight: 500;
cursor: pointer;
transition: background 0.2s;
```
On hover: `background: var(--bg-elevated)`

### Inline Feedback States (e.g. "CV generated!", "Generating...")
Success:
```css
background: #0A1F14;
border: 1px solid #00AA6E33;
color: #00CC88;
border-radius: 6px;
padding: 8px 14px;
font-size: 12px;
```
Loading (same styles + CSS spinner):
```css
/* spinner element */
width: 14px;
height: 14px;
border: 2px solid var(--border-muted);
border-top-color: var(--accent-primary);
border-radius: 50%;
animation: spin 0.7s linear infinite;
```

### Generated Text Areas (CV Summary, Cover Letter)
```css
background: var(--bg-input);
border: 1px solid var(--border-subtle);
border-radius: 6px;
padding: 16px;
color: var(--text-secondary);
font-size: 13px;
line-height: 1.7;
min-height: 120px;
resize: vertical;
```

### ATS Score
Layout: `display: flex; justify-content: space-between; align-items: center;`

Label:
```css
font-size: 11px;
text-transform: uppercase;
letter-spacing: 0.08em;
color: var(--text-muted);
```
Numeric value — color changes by score:
```css
/* 0–40:   color: #E24B4A  (red)   */
/* 41–70:  color: #EF9F27  (amber) */
/* 71–100: color: #1D9E75  (green) */
font-size: 14px;
font-weight: 600;
```
Progress bar:
```css
/* track */
background: var(--border-subtle);
height: 6px;
border-radius: 4px;

/* fill */
background: linear-gradient(90deg, #6C63FF, #9B5DE5);
height: 6px;
border-radius: 4px;
transition: width 0.6s ease;
```

---

## TRANSITIONS & ANIMATIONS

All transitions: `duration 0.2s, easing: ease`

Status dot pulse:
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}
animation: pulse 2s infinite;
```

Loading spinner:
```css
@keyframes spin {
  to { transform: rotate(360deg); }
}
```

---

## BROWSER TAB (favicon + title)

In the `<head>` of the main HTML file, update or add:

```html
<!-- Tab title -->
<title>PAS · Professional Alignment System</title>

<!-- Inline SVG favicon — no external dependencies -->
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%230A0A0F'/><text x='50%25' y='56%25' font-family='Inter,sans-serif' font-size='16' font-weight='700' fill='%236C63FF' text-anchor='middle' dominant-baseline='middle'>P</text></svg>">
```

Expected result in the tab:
- Dark background with "P" in violet #6C63FF
- Title: "PAS · Professional Alignment System"
  (· is an interpunct U+00B7, not a hyphen)

---

## DO NOT TOUCH

- Any JavaScript functions (generation logic, API/Ollama calls)
- HTML component structure (only add/modify classes and styles)
- Model-generated text content
- State variable names or React/Vue props

---

## FINAL CHECKLIST (Qwen must verify before closing)

Before considering this task done, confirm visually:

- [ ] No element has a white or light gray background
- [ ] All text on dark backgrounds is readable (minimum #6B6B8A)
- [ ] The active nav item has a visible violet left border
- [ ] The Ollama badge appears green on a very dark background
- [ ] Radio buttons show no native browser styling
- [ ] The browser tab shows the SVG favicon and correct title
- [ ] Primary buttons have the violet gradient, not a flat color
- [ ] The ATS score bar has the gradient, not a solid color
- [ ] No transition has a duration longer than 0.3s
- [ ] No white or light text appears on a light background anywhere

> Start by showing me the project file tree before making any changes.

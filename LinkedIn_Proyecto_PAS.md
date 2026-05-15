# LinkedIn — Sección "Proyectos" / "Projects"
## Professional Alignment System (PAS)

Contenido listo para copiar y pegar en la sección **Proyectos** de tu perfil de LinkedIn. Incluye versión en español y en inglés.

> Nota sobre la URL: usa el enlace público del repositorio, no el de ajustes. El correcto es:
> `https://github.com/VivicaVixen/Professional-Alignment-System`
> (el que pasaste terminaba en `/settings`, que es la página de administración y solo tú la ves).

> Nota sobre fechas: marcaste el proyecto como *Completado* con fin en **mayo 2026**. LinkedIn pide también mes/año de inicio — abajo dejé un campo para que pongas el tuyo (estimé un rango como sugerencia, ajústalo).

---

## VERSIÓN EN ESPAÑOL

**Nombre del proyecto**
Professional Alignment System (PAS)

**Fecha de inicio**
`[ Mes / Año — p. ej. Enero 2026 ]`

**Fecha de finalización**
Mayo 2026

**URL del proyecto**
https://github.com/VivicaVixen/Professional-Alignment-System

**Asociado con** (opcional)
Puedes asociarlo a tu experiencia o formación actual si aplica; si no, déjalo en blanco.

**Descripción**

PAS es una aplicación de escritorio, 100% offline y centrada en la privacidad, que genera CVs y cartas de presentación optimizados para sistemas ATS y adaptados a cada oferta de empleo. En lugar de enviar datos profesionales sensibles a servicios en la nube, PAS procesa todo localmente: el perfil y los documentos nunca salen del equipo del usuario.

El núcleo del sistema es una orquestación híbrida de dos modelos de lenguaje locales. Qwen 2.5 Coder (7B) se encarga del razonamiento estructurado: interpreta la vacante, extrae palabras clave para ATS y cruza los requisitos contra el perfil para identificar los "puntos fuertes". DeepSeek-R1 (7B) se encarga de la redacción extensa: genera el resumen del CV y la carta de presentación, y ejecuta los ciclos de refinamiento según el feedback del usuario.

Flujo de trabajo: (1) consolida varias fuentes —CV en PDF, exportación CSV de LinkedIn, texto plano— en un único perfil reutilizable; (2) analiza una oferta de empleo y la compara con el perfil; (3) genera un CV y una carta a medida, con un tono adaptado al puesto; (4) permite refinar cualquier sección de forma iterativa; (5) exporta PDFs listos para imprimir a partir de plantillas con estilo.

Un reto de ingeniería clave fue hacer correr ambos modelos en una GPU de consumo AMD Radeon RX 580 (8 GB) bajo Windows, donde ROCm ya no tiene soporte. La solución: llama.cpp con backend Vulkan más llama-swap como proxy de un único endpoint que intercambia los dos modelos en caliente, ya que no caben simultáneamente en la VRAM.

Stack técnico: Python, Streamlit, llama.cpp (Vulkan), llama-swap, Jinja2, WeasyPrint, pdfplumber, jsonschema.

**Aptitudes / Skills sugeridas para etiquetar**
Python · Modelos de lenguaje (LLM) · Inferencia local de LLM · llama.cpp · Orquestación de LLM · Ingeniería de prompts · Procesamiento de lenguaje natural (NLP) · Streamlit · Arquitectura de software · Desarrollo de aplicaciones de IA · Privacidad por diseño · Generación de PDF · Vulkan

---

## ENGLISH VERSION

**Project name**
Professional Alignment System (PAS)

**Start date**
`[ Month / Year — e.g. January 2026 ]`

**End date**
May 2026

**Project URL**
https://github.com/VivicaVixen/Professional-Alignment-System

**Associated with** (optional)
Link it to a current role or education entry if relevant; otherwise leave blank.

**Description**

PAS is a privacy-first, fully offline desktop application that generates ATS-optimized CVs and cover letters tailored to specific job postings. Instead of sending sensitive career data to cloud services, PAS runs entirely on local hardware — every profile and document stays on the user's machine.

At the core of the system is a hybrid orchestration of two local LLMs. Qwen 2.5 Coder (7B) handles structured reasoning: parsing job vacancies, extracting ATS keywords, and matching requirements against the user's profile to surface "strong points." DeepSeek-R1 (7B) handles long-form writing: generating the tailored CV summary and cover letter, and running iterative refinement cycles based on user feedback.

Workflow: (1) consolidate multiple sources — PDF CV, LinkedIn CSV export, plain text — into a single reusable profile; (2) analyze a job vacancy and match it against the profile; (3) generate a tailored CV and cover letter with a tone adapted to the role; (4) refine any section iteratively; (5) export print-ready PDFs from styled templates.

A key engineering challenge was running both models on a consumer AMD Radeon RX 580 (8 GB) under Windows, where ROCm is no longer supported. The solution: llama.cpp with a Vulkan backend plus llama-swap as a single-endpoint proxy that hot-swaps between the two models, since they cannot fit in VRAM simultaneously.

Tech stack: Python, Streamlit, llama.cpp (Vulkan), llama-swap, Jinja2, WeasyPrint, pdfplumber, jsonschema.

**Suggested skills to tag**
Python · Large Language Models (LLM) · Local LLM Inference · llama.cpp · LLM Orchestration · Prompt Engineering · Natural Language Processing (NLP) · Streamlit · Software Architecture · AI Application Development · Privacy by Design · PDF Generation · Vulkan

---

## VERSIÓN CORTA (opcional)

Por si LinkedIn te queda ajustado de espacio o prefieres algo más breve.

**Español**
Aplicación de escritorio offline y centrada en la privacidad que genera CVs y cartas de presentación optimizados para ATS y adaptados a cada vacante. Orquesta dos LLM locales: Qwen 2.5 Coder (7B) para el análisis estructurado de la oferta y el matching contra el perfil, y DeepSeek-R1 (7B) para la redacción y los ciclos de refinamiento. Corre sobre una AMD Radeon RX 580 mediante llama.cpp con backend Vulkan y llama-swap para el intercambio de modelos en caliente. Stack: Python, Streamlit, Jinja2, WeasyPrint.

**English**
Privacy-first, offline desktop app that generates ATS-optimized CVs and cover letters tailored to each job posting. It orchestrates two local LLMs: Qwen 2.5 Coder (7B) for structured vacancy analysis and profile matching, and DeepSeek-R1 (7B) for writing and iterative refinement. Runs on an AMD Radeon RX 580 via llama.cpp with a Vulkan backend and llama-swap for hot model swapping. Stack: Python, Streamlit, Jinja2, WeasyPrint.

---

## Consejos rápidos para publicarlo

- En el campo de descripción de LinkedIn, el límite es de ~2000 caracteres; la versión larga entra sin problema.
- Si tu perfil está en español, usa la versión en español; si lo tienes en inglés (o quieres alcance internacional para reclutadores tech), usa la inglesa.
- Etiqueta solo las skills que ya tengas listadas en tu perfil — LinkedIn las conecta automáticamente y refuerza esos términos.
- Considera asociar el proyecto a una entrada de experiencia o educación: le da más contexto y visibilidad.
- Si más adelante publicas una demo, un video o capturas, puedes añadir multimedia al proyecto.

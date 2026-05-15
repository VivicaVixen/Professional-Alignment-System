# Ollama GPU Acceleration — AMD RX 580 on Windows

## My Setup

- **OS:** Windows 10/11 (64-bit)
- **GPU:** AMD Radeon RX 580 8 GB (Polaris architecture)
- **Ollama:** installed and running locally (default port 11434)
- **Models in use:** `qwen2.5-coder:7b`, `deepseek-r1:7b`
- **Python app:** calls Ollama via `ollama.chat()` — no device logic in my code

## Problem

Ollama falls back to **CPU + RAM** inference. Task Manager confirms 0% GPU utilization. I want Ollama to offload layers to my RX 580.

## What I've Tried

Nothing yet — default install.

## Questions

1. **Does Ollama on Windows support AMD GPUs at all?** I've read ROCm is Linux-only. Is there a DirectML, Vulkan, or OpenCL backend for Windows AMD cards?
2. **If yes, what exact steps do I need?**
   - Which Ollama version / build?
   - Any environment variables (e.g. `OLLAMA_GPU`, `HSA_OVERRIDE_GFX_VERSION`)?
   - Any flags to pass when starting the Ollama service?
   - Do I need to install additional drivers or runtimes (e.g. AMD Adrenalin, ROCm for Windows, Vulkan SDK)?
3. **If no native support, is WSL2 a viable path?**
   - Can ROCm inside WSL2 recognize and use an RX 580?
   - What's the setup procedure for running Ollama under WSL2 with GPU passthrough?
   - Any known issues with Polaris GPUs?
4. **Are there alternative local inference backends** that support AMD GPUs on Windows and could replace Ollama? (e.g. LM Studio, KoboldCpp with CLBlast, llama.cpp with Vulkan)
   - If so, do they expose a compatible API (Ollama-compatible REST endpoint)?

## Constraints

- No NVIDIA hardware (CUDA not available)
- No Apple Silicon (Metal not available)
- Prefer free/local solutions — no cloud APIs
- Want minimal disruption to my existing Python app (it calls `ollama.chat()`)

## What I need from you

A step-by-step guide to get GPU acceleration working — or a clear "it's not possible with this hardware on Windows" answer with the best alternative.

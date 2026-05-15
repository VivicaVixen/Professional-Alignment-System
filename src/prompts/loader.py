"""
Prompt loader for PAS.
Reads prompt YAML files, validates via Pydantic, and caches for reuse.
Supports per-language variants (en / es) via load_prompt(name, lang="en").
"""

import json
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

PROMPTS_DIR = Path(__file__).parent.parent.parent / "config" / "prompts"
SETTINGS_PATH = Path(__file__).parent.parent.parent / "config" / "settings.json"

_cache: dict[str, "PromptConfig"] = {}


class PromptVariant(BaseModel):
    system: str = ""
    user: str = ""


class PromptConfig(BaseModel):
    name: str
    version: int = 1
    model_role: str
    temperature: float = 0.7
    top_p: float = 0.9
    num_predict: int = 2048
    system: str = ""
    user: str = ""
    variants: Optional[dict[str, PromptVariant]] = None


def load_prompt(name: str, lang: str = "en") -> PromptConfig:
    """Load and cache a prompt config by name and language.

    If the YAML contains a ``variants`` map, the requested language variant
    (falling back to ``"en"`` if missing) overrides the top-level system/user.
    """
    cache_key = f"{name}:{lang}"
    if cache_key in _cache:
        return _cache[cache_key]
    path = PROMPTS_DIR / f"{name}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    cfg = PromptConfig.model_validate(data)
    if cfg.variants:
        variant = cfg.variants.get(lang) or cfg.variants.get("en")
        if variant:
            cfg = cfg.model_copy(update={"system": variant.system, "user": variant.user})
    _cache[cache_key] = cfg
    return cfg


def reload_prompts() -> None:
    """Clear the prompt cache so edited YAML files are picked up without restart."""
    _cache.clear()


class _LiteralDumper(yaml.Dumper):
    """yaml.Dumper subclass that writes multiline strings with literal block style (|)."""
    pass


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_LiteralDumper.add_representer(str, _str_representer)


def save_prompt(config: PromptConfig) -> None:
    """Write config back to YAML, backing up the previous file with a timestamp."""
    path = PROMPTS_DIR / f"{config.name}.yaml"
    if path.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = PROMPTS_DIR / f"{config.name}.{ts}.bak.yaml"
        shutil.copy2(path, bak)
    data = config.model_dump(exclude_none=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, Dumper=_LiteralDumper, allow_unicode=True,
                  default_flow_style=False, sort_keys=False)
    _cache.clear()


def reset_prompt_to_default(name: str) -> None:
    """Restore a prompt from the _defaults snapshot."""
    defaults_dir = PROMPTS_DIR / "_defaults"
    src = defaults_dir / f"{name}.yaml"
    dst = PROMPTS_DIR / f"{name}.yaml"
    if src.exists():
        shutil.copy2(src, dst)
        _cache.clear()


def list_prompt_names() -> list[str]:
    """Return sorted list of prompt names available in config/prompts/."""
    return sorted(
        p.stem for p in PROMPTS_DIR.glob("*.yaml")
        if not p.stem.startswith("_") and not p.stem.endswith(".bak")
    )


def get_model_name(model_role: str) -> str:
    """Resolve a model_role ('qwen' | 'deepseek') to the Ollama model name from settings.json."""
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            settings = json.load(f)
        models = settings.get("ollama", {}).get("models", {})
        if model_role == "qwen":
            return models.get("qwen_coder", "qwen2.5-coder:7b")
        if model_role == "deepseek":
            return models.get("deepseek", "deepseek-r1:7b")
        return models.get(model_role, model_role)
    except Exception:
        defaults = {"qwen": "qwen2.5-coder:7b", "deepseek": "deepseek-r1:7b"}
        return defaults.get(model_role, model_role)


def build_messages(cfg: PromptConfig, **kwargs) -> list[dict]:
    """Build the ollama messages list from a PromptConfig and format-string kwargs."""
    messages = []
    if cfg.system:
        messages.append({"role": "system", "content": cfg.system.strip()})
    messages.append({"role": "user", "content": cfg.user.format(**kwargs)})
    return messages

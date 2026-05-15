"""
Shim de compatibilidad: expone una API parecida a `ollama` pero habla
con llama-swap (OpenAI-compatible) en localhost:8080.

Uso en codigo existente:
    # antes:
    # import ollama
    # r = ollama.chat(model='qwen2.5-coder:7b', messages=[...])

    # despues:
    import pas_inference_client as ollama
    r = ollama.chat(model='qwen2.5-coder:7b', messages=[...])

Flag de rollback: si la variable de entorno PAS_USE_OLLAMA=1, hace
passthrough al paquete ollama original.
"""
from __future__ import annotations

import os
import json
import urllib.request
import urllib.error
from typing import Iterable, Iterator

_ENDPOINT = os.environ.get("PAS_INFERENCE_URL", "http://localhost:8080/v1/chat/completions")
_TIMEOUT = float(os.environ.get("PAS_INFERENCE_TIMEOUT", "600"))
_USE_OLLAMA = os.environ.get("PAS_USE_OLLAMA", "0") == "1"

if _USE_OLLAMA:
    # Passthrough al paquete oficial — rollback rapido.
    from ollama import chat, ChatResponse  # type: ignore  # noqa: F401
else:
    def _post(payload: dict) -> dict:
        req = urllib.request.Request(
            _ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Inference HTTP {e.code}: {e.read().decode('utf-8', 'replace')}") from e

    def chat(model: str, messages: list[dict], stream: bool = False, options: dict | None = None, **kwargs):
        """
        Mimica ollama.chat(). Devuelve un dict con la misma forma minima
        que el codigo PAS espera: r['message']['content'].
        """
        if stream:
            return _chat_stream(model, messages, options, **kwargs)

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if options:
            # Mapear opciones comunes Ollama -> OpenAI
            if "temperature" in options:
                payload["temperature"] = options["temperature"]
            if "num_predict" in options:
                payload["max_tokens"] = options["num_predict"]
            if "top_p" in options:
                payload["top_p"] = options["top_p"]

        data = _post(payload)
        choice = data["choices"][0]
        return {
            "model": data.get("model", model),
            "message": {
                "role": choice["message"]["role"],
                "content": choice["message"]["content"],
            },
            "done": True,
            "done_reason": choice.get("finish_reason", "stop"),
        }

    def _chat_stream(model: str, messages: list[dict], options: dict | None, **kwargs) -> Iterator[dict]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
        }
        if options:
            if "temperature" in options:
                payload["temperature"] = options["temperature"]
            if "num_predict" in options:
                payload["max_tokens"] = options["num_predict"]

        req = urllib.request.Request(
            _ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            for raw in resp:
                line = raw.decode("utf-8").strip()
                if not line or not line.startswith("data:"):
                    continue
                payload_str = line[len("data:"):].strip()
                if payload_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload_str)
                except json.JSONDecodeError:
                    continue
                delta = chunk["choices"][0].get("delta", {})
                yield {
                    "model": chunk.get("model", model),
                    "message": {
                        "role": delta.get("role", "assistant"),
                        "content": delta.get("content", ""),
                    },
                    "done": False,
                }
            yield {"model": model, "message": {"role": "assistant", "content": ""}, "done": True}

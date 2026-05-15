"""
Shared streaming helper for long LLM generations (T2.4).
Wraps ollama.chat(stream=True) and emits the cumulative buffer to an
optional on_chunk callback after every received token.

Used by draft_cv, draft_cl, revise_cv, revise_cl. Planning, critique, parse,
match remain non-streaming because their outputs are short.
"""

from typing import Callable, Optional

import pas_inference_client as ollama


def stream_ollama_chat(
    model: str,
    messages: list[dict],
    options: dict,
    on_chunk: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Run ollama.chat with stream=True. Buffer chunks and, after every chunk,
    invoke on_chunk with the cumulative text. Returns the final concatenated
    content string.

    The callback is best-effort — exceptions raised inside it are swallowed so
    that a flaky UI handler can never abort the generation.
    """
    chunks: list[str] = []
    try:
        stream = ollama.chat(
            model=model,
            messages=messages,
            options=options,
            stream=True,
        )
        for part in stream:
            piece = ""
            try:
                piece = part.get("message", {}).get("content", "") or ""
            except AttributeError:
                # part may be an object instead of dict in some ollama-py versions
                msg = getattr(part, "message", None)
                if msg is not None:
                    piece = getattr(msg, "content", "") or ""
            if piece:
                chunks.append(piece)
                if on_chunk is not None:
                    try:
                        on_chunk("".join(chunks))
                    except Exception:
                        pass
    except Exception:
        # Re-raise so the calling generator can fall through to its existing
        # exception handler (which produces a fallback document).
        raise

    return "".join(chunks)

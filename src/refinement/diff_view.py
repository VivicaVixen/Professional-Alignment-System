"""Word-level diff rendering for revision history."""

import difflib
import html as _html


def render_diff(text_before: str, text_after: str) -> str:
    """
    Return an HTML string with word-level diff between two texts.

    Removed words: <span class="diff-removed">...</span>
    Added words:   <span class="diff-added">...</span>
    Unchanged:     plain escaped text
    """
    words_before = text_before.split()
    words_after = text_after.split()

    matcher = difflib.SequenceMatcher(None, words_before, words_after, autojunk=False)
    parts: list[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            parts.append(_html.escape(" ".join(words_before[i1:i2])))
        elif tag == "replace":
            removed = _html.escape(" ".join(words_before[i1:i2]))
            added = _html.escape(" ".join(words_after[j1:j2]))
            parts.append(f'<span class="diff-removed">{removed}</span>')
            parts.append(f'<span class="diff-added">{added}</span>')
        elif tag == "delete":
            removed = _html.escape(" ".join(words_before[i1:i2]))
            parts.append(f'<span class="diff-removed">{removed}</span>')
        elif tag == "insert":
            added = _html.escape(" ".join(words_after[j1:j2]))
            parts.append(f'<span class="diff-added">{added}</span>')

    return " ".join(parts)

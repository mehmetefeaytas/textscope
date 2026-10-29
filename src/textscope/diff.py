from __future__ import annotations

import difflib


def unified_diff(original: str, result: str, filename: str = "text") -> str:
    a = original.splitlines(keepends=True)
    b = result.splitlines(keepends=True)
    diff = difflib.unified_diff(a, b, fromfile=f"{filename} (original)", tofile=f"{filename} (rewritten)")
    return "".join(diff)

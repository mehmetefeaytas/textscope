from __future__ import annotations

import os
import zipfile
import io
import re
from pathlib import Path
from typing import Callable

from .protected import split_protected


CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".cc", ".h", ".hpp",
             ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".sh", ".bash",
             ".sql", ".r", ".m", ".lua", ".pl", ".pm"}


def detect_format(path: str) -> str:
    p = Path(path)
    suf = p.suffix.lower()
    if suf == ".docx":
        return "docx"
    if suf == ".zip":
        return "zip"
    if suf in {".tex"}:
        return "tex"
    if suf in {".md", ".markdown"}:
        return "md"
    if suf in {".txt"}:
        return "txt"
    if suf in CODE_EXTS:
        return "code"
    return "txt"


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)


# ---------- code: only comments/docstrings rewritten ----------

def _rewrite_code(text: str, transform: Callable[[str], str]) -> str:
    # Handle Python docstrings and # comments; JS/TS // and /* */; C-style; generic # and //
    # We'll implement a state machine for strings and comments.
    # Simpler: regex replace comments.
    # Python triple-quoted docstrings
    def repl_triple(m):
        quote = m.group(1)
        body = m.group(2)
        return quote + transform(body) + quote
    text = re.sub(r'("""|\'\'\')([\s\S]*?)\1', repl_triple, text)
    # Line comments starting with # (python, shell, ruby) - but careful with shebang
    def repl_hash(m):
        return m.group(1) + transform(m.group(2))
    text = re.sub(r"(^|\n)([ \t]*#[^\n]*)", lambda m: m.group(1) + _transform_hash_line(m.group(2), transform), text)
    # // line comments
    text = re.sub(r"(//)([^\n]*)", lambda m: m.group(1) + transform(m.group(2)), text)
    # /* */ block comments
    text = re.sub(r"(/\*)([\s\S]*?)(\*/)", lambda m: m.group(1) + transform(m.group(2)) + m.group(3), text)
    return text


def _transform_hash_line(line: str, transform: Callable[[str], str]) -> str:
    # line like "   # comment"
    m = re.match(r"([ \t]*#)(.*)", line)
    if not m:
        return line
    return m.group(1) + transform(m.group(2))


def process_code(text: str, transform: Callable[[str], str]) -> str:
    return _rewrite_code(text, transform)


# ---------- docx XML-safe ----------

def read_docx(path: str) -> str:
    # Return concatenated text of all w:t nodes (not used for processing; we process XML directly)
    return ""


def process_docx_bytes(data: bytes, transform: Callable[[str], str]) -> bytes:
    zin = zipfile.ZipFile(io.BytesIO(data))
    out_buf = io.BytesIO()
    zout = zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED)
    for info in zin.infolist():
        content = zin.read(info.filename)
        if info.filename.endswith(".xml") or info.filename.endswith(".rels"):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                zout.writestr(info, content)
                continue
            new_text = _transform_xml_text_nodes(text, transform)
            zout.writestr(info, new_text.encode("utf-8"))
        else:
            zout.writestr(info, content)
    zin.close()
    zout.close()
    return out_buf.getvalue()


def _transform_xml_text_nodes(xml: str, transform: Callable[[str], str]) -> str:
    # Transform text inside <w:t ...>...</w:t> and <w:instrText>
    def repl(m):
        prefix = m.group(1)
        text = m.group(2)
        suffix = m.group(3)
        # decode xml entities? text may contain &amp; etc. Transform on raw decoded.
        import html
        decoded = html.unescape(text)
        new = transform(decoded)
        # re-escape basic entities
        new = new.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return prefix + new + suffix
    xml = re.sub(r"(<w:t[^>]*>)(.*?)(</w:t>)", repl, xml, flags=re.DOTALL)
    xml = re.sub(r"(<w:instrText[^>]*>)(.*?)(</w:instrText>)", repl, xml, flags=re.DOTALL)
    return xml


def process_docx_file(path: str, out_path: str, transform: Callable[[str], str]) -> None:
    with open(path, "rb") as f:
        data = f.read()
    new_data = process_docx_bytes(data, transform)
    with open(out_path, "wb") as f:
        f.write(new_data)


# ---------- zip ----------

def process_zip_file(path: str, out_path: str, transform: Callable[[str], str], mode: str) -> None:
    zin = zipfile.ZipFile(path)
    out_buf = io.BytesIO()
    zout = zipfile.ZipFile(out_buf, "w", zipfile.ZIP_DEFLATED)
    for info in zin.infolist():
        content = zin.read(info.filename)
        name = info.filename
        lower = name.lower()
        if lower.endswith(".docx"):
            new_content = process_docx_bytes(content, transform)
            zout.writestr(info, new_content)
        elif lower.endswith((".txt", ".md", ".markdown", ".tex")):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                zout.writestr(info, content)
                continue
            if lower.endswith(tuple(CODE_EXTS)):
                new_text = process_code(text, transform)
            else:
                new_text = transform(text)
            zout.writestr(info, new_text.encode("utf-8"))
        elif lower.endswith(tuple(CODE_EXTS)):
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                zout.writestr(info, content)
                continue
            new_text = process_code(text, transform)
            zout.writestr(info, new_text.encode("utf-8"))
        else:
            zout.writestr(info, content)
    zin.close()
    zout.close()
    with open(out_path, "wb") as f:
        f.write(out_buf.getvalue())

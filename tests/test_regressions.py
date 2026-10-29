"""Regression tests for issues found while reviewing the first release."""

from textscope.protected import split_protected, verify_protected
from textscope.rewrite import rewrite_free, rewrite_text

AI_TEXT = (
    "Moreover, it is important to note that this comprehensive study leverages robust "
    "methods. Furthermore, we utilize pivotal frameworks to delve into the data."
)


def test_latex_document_body_is_rewritten():
    tex = (
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "\\section{Introduction}\n"
        "Moreover, we utilize a comprehensive framework.\n"
        "\\begin{equation}\n"
        "E = mc^2\n"
        "\\end{equation}\n"
        "\\end{document}\n"
    )
    out = rewrite_text(tex)
    assert out != tex, "document body must not be swallowed by \\begin{document}"
    assert "comprehensive" not in out
    # structure and protected environments survive
    assert out.count("\\begin{document}") == 1
    assert "\\begin{equation}\nE = mc^2\n\\end{equation}" in out
    assert verify_protected(tex, out)[0]


def test_nested_latex_env_fully_protected():
    tex = (
        "\\begin{figure}\n"
        "\\begin{center}\n"
        "Important comprehensive robust caption\n"
        "\\end{center}\n"
        "\\end{figure}"
    )
    spans = [s for s in split_protected(tex) if s.protected]
    assert spans and spans[0].text == tex


def test_paragraph_structure_preserved():
    text = (
        "First paragraph here. It is important to note this.\n"
        "\n"
        "Second paragraph follows. We are testing structure.\n"
        "\n"
        "# Heading\n"
        "Third one ends.\n"
    )
    out = rewrite_text(text)
    assert out.count("\n\n") == text.count("\n\n")
    assert out.endswith("\n")
    assert "Third one ends." in out


def test_no_sentence_fragment_from_comma():
    sentence = "In today's rapidly evolving landscape, artificial intelligence plays a crucial role."
    out = rewrite_free(sentence)
    assert ". Artificial" not in out
    assert out.lower().startswith("in today's")


def test_split_only_balanced_clauses():
    balanced = (
        "This study collects survey responses from two hundred students, and it then compares "
        "the outcomes with earlier published results."
    )
    out = rewrite_free(balanced)
    assert out.count(". ") == 1


def test_contraction_keeps_sentence_case():
    out = rewrite_free("It is important to note that we are ready.")
    assert out.startswith(("It's", "Note"))


def test_turkish_replacement_is_not_duplicated():
    out = rewrite_text("Bu çalışma kapsamında geniş bir analiz yapıldı.", lang="tr")
    assert "Bu bu" not in out.lower()
    assert out.startswith("Bu ")


def test_turkish_role_rule_now_matches():
    out = rewrite_text("Yapay zeka öğrenciler üzerinde önemli bir rol oynamaktadır.", lang="tr")
    assert "rol oynamaktadır" not in out
    assert "etkili" in out or "önemli" in out


def test_seed_produces_variation_and_stays_deterministic():
    outputs = {rewrite_text(AI_TEXT, seed=s) for s in range(6)}
    assert len(outputs) > 1, "--seed must actually vary the output"
    assert rewrite_text(AI_TEXT, seed=3) == rewrite_text(AI_TEXT, seed=3)


def test_aggressive_profile_differs_from_balanced():
    text = "In today's rapidly evolving landscape, substantial and intricate systems matter."
    assert rewrite_text(text, profile="aggressive") != rewrite_text(text, profile="balanced")


def test_conservative_profile_only_swaps_words():
    text = "Moreover, it is important to note that we utilize robust tools."
    out = rewrite_text(text, profile="conservative")
    assert "it is important to note" in out  # phrases untouched
    assert "robust" not in out


def test_url_keeps_trailing_period_in_prose():
    text = "The report is at https://example.com/report. It is important to note that."
    prot = [s.text for s in split_protected(text) if s.protected]
    assert "https://example.com/report" in prot
    assert "https://example.com/report." not in prot


def test_strict_mode_preserves_word_count_and_prose():
    out = rewrite_text(AI_TEXT, strict=True)
    assert len(out.split()) == len(AI_TEXT.split())
    assert "it is important to note" in out  # phrases untouched in strict mode


def test_serve_command_dispatches(monkeypatch):
    from textscope import server

    called = {}
    monkeypatch.setattr(server, "serve", lambda host, port: called.update(host=host, port=port))

    from textscope.cli import main

    assert main(["serve", "--port", "1234"]) == 0
    assert called["port"] == 1234


def test_docx_rewrite_keeps_protected_text():
    import io
    import re
    import zipfile

    from textscope.formats import docx_text, process_docx_bytes
    from textscope.rewrite import rewrite_text as rewrite

    xml = (
        '<w:document xmlns:w="w"><w:body>'
        "<w:p><w:r><w:t>Moreover, we utilize 42 samples.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>See https://example.com/x.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml", xml)
    original = buf.getvalue()

    new = process_docx_bytes(original, lambda t: rewrite(t))
    out_xml = zipfile.ZipFile(io.BytesIO(new)).read("word/document.xml").decode()
    texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", out_xml)

    assert "42" in texts[0]
    assert "https://example.com/x" in texts[1]
    assert "Moreover" not in texts[0]
    assert docx_text(original).splitlines()[0].startswith("Moreover")

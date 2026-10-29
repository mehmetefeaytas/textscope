"""Tests for the extended protected-zone coverage."""

from textscope.protected import split_protected, verify_protected
from textscope.rewrite import rewrite_text

AI_WORDS = "Moreover, we utilize robust and comprehensive tools."


def protected_texts(text):
    return [span.text for span in split_protected(text) if span.protected]


def assert_survives(text, needle):
    out = rewrite_text(text)
    assert needle in out, out
    ok, errors = verify_protected(text, out)
    assert ok, errors
    return out


def test_yaml_front_matter_is_protected():
    text = "---\ntitle: My kapsamlı Study\nauthor: X\n---\n" + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert any(s.startswith("---\ntitle:") for s in spans)
    out = assert_survives(text, "title: My kapsamlı Study")
    # the prose after the front matter is still rewritten
    assert "utilize" not in out


def test_front_matter_must_be_at_document_start():
    text = "Intro line.\n---\nnot: front matter\n---\n" + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert not any(s.startswith("---\nnot:") for s in spans)


def test_markdown_table_rows_survive():
    text = (
        "| Metric | Value |\n"
        "| --- | --- |\n"
        "| sample | 42 |\n"
        "\n"
        + AI_WORDS
    )
    for row in ("| Metric | Value |", "| --- | --- |", "| sample | 42 |"):
        assert_survives(text, row)


def test_html_tags_are_protected():
    text = '<div class="wrapper">' + AI_WORDS + "</div>"
    assert '<div class="wrapper">' in protected_texts(text)
    assert "</div>" in protected_texts(text)
    out = assert_survives(text, '<div class="wrapper">')
    assert "utilize" not in out


def test_escaped_angle_bracket_is_not_a_tag():
    text = r"Compare 5 \< 7 and we utilize robust tools."
    assert not any(s.startswith("< 7") for s in protected_texts(text))
    assert "utilize" not in rewrite_text(text)


def test_markdown_link_destination_is_protected():
    text = "[the report](https://example.com/x) contains " + AI_WORDS
    assert "(https://example.com/x)" in protected_texts(text)
    assert_survives(text, "(https://example.com/x)")


def test_markdown_image_destination_is_protected():
    text = "![chart](images/chart.png) shows " + AI_WORDS
    assert "(images/chart.png)" in protected_texts(text)


def test_reference_citation_markers_are_protected():
    text = "Prior studies [1] and [2, 3] and [4-6] show that we utilize robust tools."
    for marker in ("[1]", "[2, 3]", "[4-6]"):
        assert marker in protected_texts(text)
    assert_survives(text, "[4-6]")


def test_author_year_citations_are_protected():
    text = "Earlier work (Smith et al., 2020) and (Jones & Lee 2019) shows that we utilize tools."
    out = rewrite_text(text)
    assert "(Smith et al., 2020)" in out
    assert "(Jones & Lee 2019)" in out
    ok, errors = verify_protected(text, out)
    assert ok, errors


def test_narrative_author_year_citation_is_protected():
    text = "Smith et al. (2020) argued that we utilize robust methods."
    out = rewrite_text(text)
    assert "Smith et al. (2020)" in out
    ok, errors = verify_protected(text, out)
    assert ok, errors


def test_latex_line_comment_is_protected():
    text = "% a comprehensive note\n" + AI_WORDS + "\n"
    assert "% a comprehensive note" in protected_texts(text)
    out = assert_survives(text, "% a comprehensive note")
    assert "comprehensive" not in out.split("% a comprehensive note")[1]


def test_escaped_percent_is_not_a_comment():
    text = r"In 50\% of cases we utilize robust tools."
    assert not any(s.startswith("%") for s in protected_texts(text))
    assert "utilize" not in rewrite_text(text)


def test_prose_percent_is_not_a_comment():
    """Plain-text percentages must not swallow the rest of the line."""
    text = "About 42% of students utilize robust tools."
    assert "42%" in rewrite_text(text)
    assert "students" in rewrite_text(text)
    assert "utilize" not in rewrite_text(text)


def test_html_comment_is_protected():
    text = "<!-- comprehensive internal note -->\n" + AI_WORDS
    assert "<!-- comprehensive internal note -->" in protected_texts(text)
    assert_survives(text, "<!-- comprehensive internal note -->")


def test_bracketed_prose_still_rewritten():
    text = "We utilize robust tools (see the note) in this study."
    out = rewrite_text(text)
    assert "utilize" not in out
    assert "(see the note)" in out


def test_all_new_spans_are_ordered_and_non_overlapping():
    text = (
        "---\ntitle: t\n---\n"
        "| a | b |\n"
        '<div class="x">\n'
        "[link](https://e.com) [1] (Smith, 2020) <!-- c -->\n"
        + AI_WORDS
    )
    spans = split_protected(text)
    joined = "".join(span.text for span in spans)
    assert joined == text
    assert sum(1 for s in spans if s.protected) >= 5

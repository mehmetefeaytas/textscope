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


def test_tilde_fence_is_protected():
    text = "~~~python\nx = 1\n~~~\n" + AI_WORDS + "\n"
    assert "~~~python\nx = 1\n~~~" in protected_texts(text)
    out = assert_survives(text, "~~~python\nx = 1\n~~~")
    assert "utilize" not in out


def test_unterminated_tilde_fence_does_not_pair_with_later_tilde():
    """A mid-line "~~~" in prose must not open a block."""
    text = "Prose says ~~~ here, and later another ~~~ there. " + AI_WORDS
    assert not any(s.startswith("~~~") for s in protected_texts(text))
    out = rewrite_text(text)
    assert "~~~ here" in out
    assert "utilize" not in out


def test_tilde_fence_does_not_capture_backtick_fence():
    text = "```\ncode\n```\n\n~~~\ntilde\n~~~\n" + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert "~~~\ntilde\n~~~" in spans
    assert not any("```" in s and "~~~" in s for s in spans)


def test_indented_code_block_is_protected():
    text = "Intro paragraph.\n\n    x = 1\n    print(x)\n\n" + AI_WORDS + "\n"
    out = assert_survives(text, "    x = 1\n    print(x)")
    assert "utilize" not in out


def test_indented_code_at_document_start_is_protected():
    text = "    first line\n    second line\n\n" + AI_WORDS + "\n"
    assert_survives(text, "    first line\n    second line")


def test_indented_list_item_is_not_a_code_block():
    text = "Intro.\n\n    - item one\n    - item two\n\n" + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert not any(s.startswith("    - item") for s in spans)
    out = rewrite_text(text)
    assert "    - item one" in out


def test_continuation_line_without_blank_line_is_not_code():
    text = "This paragraph continues\n    on an indented line. " + AI_WORDS + "\n"
    assert not any(s.startswith("    on an") for s in protected_texts(text))


def test_footnote_marker_and_definition_are_protected():
    text = "A claim [^1] and more.\n\n[^1]: a comprehensive note here.\n" + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert "[^1]" in spans
    assert "[^1]: a comprehensive note here." in spans
    assert_survives(text, "[^1]: a comprehensive note here.")


def test_markdown_reference_definition_is_protected():
    text = "[docs]: https://example.com/x\n\nSee the note and " + AI_WORDS + "\n"
    assert "[docs]: https://example.com/x" in protected_texts(text)
    assert_survives(text, "[docs]: https://example.com/x")


def test_doi_is_protected():
    text = "See doi:10.1234/abcd.2020.001 for details and " + AI_WORDS + "\n"
    assert_survives(text, "10.1234/abcd.2020.001")


def test_isbn_forms_are_protected():
    text = "ISBN 978-3-16-148410-0 and ISBN-13: 978-3-16-148410-0.\n" + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert "ISBN 978-3-16-148410-0" in spans
    assert "ISBN-13: 978-3-16-148410-0" in spans
    assert_survives(text, "ISBN-13: 978-3-16-148410-0")


def test_arxiv_identifiers_are_protected():
    text = "Preprint arXiv:2101.00001 and arXiv:2101.00001v2 exist. " + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert "arXiv:2101.00001" in spans
    assert "arXiv:2101.00001v2" in spans
    assert_survives(text, "arXiv:2101.00001v2")


def test_semantic_versions_are_protected():
    text = "Release v1.2.3 and 1.2.3-beta.1 are out. " + AI_WORDS + "\n"
    spans = protected_texts(text)
    assert "v1.2.3" in spans
    assert "1.2.3-beta.1" in spans
    assert_survives(text, "1.2.3-beta.1")


def test_semver_requires_two_dots():
    text = "Version 1.5 and ratio 3, then " + AI_WORDS + "\n"
    # "1.5" is still an ordinary number, but it must not become a version span.
    assert not any(s.kind == "semver" for s in split_protected(text))


def test_html_entities_are_protected():
    text = "R&amp;D said &#39;yes&#39; and&nbsp;we " + AI_WORDS + "\n"
    for entity in ("&amp;", "&#39;", "&nbsp;"):
        assert entity in protected_texts(text)
    assert_survives(text, "&amp;")


def test_emoji_shortcodes_are_protected():
    text = "Great :smile: work :+1: and " + AI_WORDS + "\n"
    assert ":smile:" in protected_texts(text)
    assert ":+1:" in protected_texts(text)
    assert_survives(text, ":+1:")


def test_clock_time_is_not_an_emoji_shortcode():
    text = "The meeting is at 12:30 and the ratio: 3 matters. " + AI_WORDS + "\n"
    assert not any(s.kind == "emoji" for s in split_protected(text))
    out = rewrite_text(text)
    assert "12:30" in out
    assert "ratio: 3" in out


def test_template_placeholders_are_protected():
    text = "Hello {{ variable }} {name} ${VAR} %s %d and " + AI_WORDS + "\n"
    spans = protected_texts(text)
    for token in ("{{ variable }}", "{name}", "${VAR}", "%s", "%d"):
        assert token in spans
    assert_survives(text, "{{ variable }}")


def test_escaped_forms_remain_unprotected():
    text = r"In 50\% of cases 5 \< 7 and costs \$5 for " + AI_WORDS + "\n"
    spans = split_protected(text)
    assert not any(s.kind in {"latex_comment", "html_tag", "math_inline"} for s in spans)
    out = rewrite_text(text)
    assert r"50\%" in out
    assert r"\<" in out
    assert r"\$5" in out


def test_prose_with_braces_colons_dollar_and_printf_is_rewritten():
    text = "We utilize { the } robust tools, ratio: 3, costs $5 and use %s here.\n"
    out = rewrite_text(text)
    assert "utilize" not in out
    assert "{ the }" in out
    assert "ratio: 3" in out
    assert "$5" in out
    assert "%s" in out


def test_mixed_document_reassembles_byte_identically():
    text = (
        "# Report\n\n"
        "~~~bash\nmake all\n~~~\n\n"
        "Cite [^1] and arXiv:2101.00001v2 here.\n\n"
        "DOI 10.1234/abcd.2020.001 matters.\n\n"
        "[^1]: A comprehensive note that stays frozen.\n\n"
        "Text with &amp; and v1.2.3 and {{ name }}.\n"
    )
    spans = split_protected(text)
    assert "".join(span.text for span in spans) == text
    protected_kinds = {s.kind for s in spans if s.protected}
    assert {"fence_tilde", "footnote_marker", "arxiv", "footnote_def",
            "doi", "html_entity", "semver", "template_var"} <= protected_kinds


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

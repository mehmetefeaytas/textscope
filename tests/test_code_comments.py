"""Tests for code-file handling: only comments and docstrings are rewritten."""

from textscope.formats import process_code
from textscope.rewrite import rewrite_text


def transform(text: str) -> str:
    return rewrite_text(text, lang="en")


def test_shebang_is_untouched():
    src = "#!/usr/bin/env python3\n# a comprehensive note\nx = 1\n"
    out = process_code(src, transform)
    assert out.splitlines()[0] == "#!/usr/bin/env python3"


def test_trailing_comment_is_rewritten():
    src = "def f(x):\n    return x  # pivotal helper\n"
    out = process_code(src, transform)
    assert "pivotal" not in out
    assert "return x  #" in out


def test_hash_inside_string_is_not_a_comment():
    src = 'marker = "# not a comment at all"\n'
    assert process_code(src, transform) == src


def test_url_fragment_is_not_a_comment():
    src = 'url = "http://example.com/page#anchor"\n'
    assert process_code(src, transform) == src


def test_string_literals_are_never_rewritten():
    src = 'msg = "It is important to note that we utilize robust tools"\n'
    assert process_code(src, transform) == src


def test_docstring_is_rewritten():
    src = '"""A comprehensive and robust helper."""\n'
    out = process_code(src, transform)
    assert out.startswith('"""')
    assert "comprehensive" not in out
    assert "robust" not in out


def test_single_quoted_docstring_is_rewritten():
    src = "'''A comprehensive helper.'''\n"
    out = process_code(src, transform)
    assert "comprehensive" not in out


def test_block_comment_is_rewritten():
    src = "/* a comprehensive note */\nint x = 0;\n"
    out = process_code(src, transform)
    assert "comprehensive" not in out
    assert "int x = 0;" in out


def test_line_comment_with_slashes_is_rewritten():
    src = "// a comprehensive note\nconst x = 1;\n"
    out = process_code(src, transform)
    assert "comprehensive" not in out
    assert "const x = 1;" in out


def test_code_structure_is_preserved():
    src = (
        "import os\n"
        "\n"
        "def f(a, b):\n"
        "    # comprehensive\n"
        "    return a + b\n"
    )
    out = process_code(src, transform)
    assert out.count("\n") == src.count("\n")
    assert "def f(a, b):" in out


def test_unterminated_docstring_does_not_crash():
    src = '"""unterminated comprehensive docstring\n'
    assert isinstance(process_code(src, transform), str)

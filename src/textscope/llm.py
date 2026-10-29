from __future__ import annotations

"""Optional LLM backend for rewrite. Requires `textscope[llm]` extra."""


def available() -> bool:
    try:
        import openai  # noqa: F401
        return True
    except ImportError:
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False


def rewrite_with_llm(text: str, provider: str = "openai", model: str = "gpt-4o-mini",
                     api_key: str | None = None) -> str:
    if provider == "openai":
        try:
            import openai
        except ImportError as e:
            raise RuntimeError("openai not installed; pip install 'textscope-cli[llm]'") from e
        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Rewrite the following text so it reads as human-written. "
                                              "Preserve all numbers, URLs, code, LaTeX, and citations exactly. "
                                              "Vary sentence length. Avoid AI clichés."},
                {"role": "user", "content": text},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content or text
    if provider == "anthropic":
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError("anthropic not installed; pip install 'textscope-cli[llm]'") from e
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": "Rewrite the following text so it reads as human-written. "
                                                  "Preserve all numbers, URLs, code, LaTeX, and citations exactly. "
                                                  "Vary sentence length. Avoid AI clichés.\n\n" + text}],
        )
        return msg.content[0].text if msg.content else text
    raise ValueError(f"unknown provider {provider}")

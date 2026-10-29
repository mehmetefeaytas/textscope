from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import detect as detect_mod
from . import llm as llm_mod
from .clean import clean_text
from .diff import unified_diff
from .formats import (
    CODE_EXTS,
    detect_format,
    docx_text,
    process_code,
    process_docx_bytes,
    process_zip_file,
    read_text_file,
    write_text_file,
)
from .metrics import report as metrics_report
from .protected import verify_protected
from .rewrite import rewrite_text

SUPPORTED_EXTS = {".txt", ".md", ".markdown", ".tex", ".docx", ".zip"} | CODE_EXTS


def _make_transform(cmd: str, strict: bool, seed: int, lang: str = 'auto', profile: str = 'balanced', llm: str | None = None):
    if cmd == "clean":
        def t(text):
            return clean_text(text)
        return t
    else:
        if llm:
            prov, _, model = llm.partition(':')
            prov = prov or 'openai'
            model = model or 'gpt-4o-mini'
            def t(text):
                return llm_mod.rewrite_with_llm(text, provider=prov, model=model)
            return t
        def t(text):
            return rewrite_text(text, strict=strict, seed=seed, lang=lang, profile=profile)
        return t


def _transform_text(path: str, text: str, transform, cmd: str, strict: bool, seed: int) -> str:
    fmt = detect_format(path)
    if fmt == "code":
        return process_code(text, transform)
    if fmt in ("txt", "md", "tex"):
        return transform(text)
    return text


def _process_file(input_path: str, output_path: str | None, cmd: str, strict: bool,
                  seed: int, dry_run: bool, show_diff: bool, json_report: bool,
                  lang: str = 'auto', profile: str = 'balanced', llm: str | None = None) -> dict:
    transform = _make_transform(cmd, strict, seed, lang, profile, llm)
    fmt = detect_format(input_path)
    result_info = {"file": input_path, "format": fmt}

    if fmt == "docx":
        with open(input_path, "rb") as f:
            data = f.read()
        new_data = process_docx_bytes(data, transform)
        # Verify protected zones against the extracted text (same guarantee as txt).
        ok, errors = verify_protected(docx_text(data), docx_text(new_data))
        result_info["protected_ok"] = ok
        result_info["protected_errors"] = errors
        if not ok:
            result_info["status"] = "aborted"
            print(f"ABORT: protected zone violation: {errors}", file=sys.stderr)
            sys.exit(2)
        if not dry_run:
            out = output_path or _default_output(input_path, cmd)
            with open(out, "wb") as f:
                f.write(new_data)
            result_info["output"] = out
        result_info["status"] = "ok"
        return result_info

    if fmt == "zip":
        out = output_path or _default_output(input_path, cmd)
        if not dry_run:
            process_zip_file(input_path, out, transform, cmd)
            result_info["output"] = out
        result_info["status"] = "ok"
        return result_info

    # text/code
    text = read_text_file(input_path)
    new_text = _transform_text(input_path, text, transform, cmd, strict, seed)

    # protected verification
    ok, errors = verify_protected(text, new_text)
    result_info["protected_ok"] = ok
    result_info["protected_errors"] = errors
    if cmd == "rewrite":
        result_info["word_count_original"] = len(text.split())
        result_info["word_count_result"] = len(new_text.split())
        result_info["word_count_delta"] = len(new_text.split()) - len(text.split())
    result_info["metrics_original"] = metrics_report(text)
    result_info["metrics_result"] = metrics_report(new_text)

    if not ok:
        result_info["status"] = "aborted"
        # do not write
        if show_diff:
            print(unified_diff(text, new_text, input_path))
        if json_report:
            print(json.dumps(result_info, indent=2, ensure_ascii=False))
        print(f"ABORT: protected zone violation: {errors}", file=sys.stderr)
        sys.exit(2)

    if show_diff:
        print(unified_diff(text, new_text, input_path))

    if not dry_run:
        out = output_path or None
        if out:
            if fmt == "code":
                write_text_file(out, new_text)
            else:
                write_text_file(out, new_text)
            result_info["output"] = out
        else:
            # stdout
            sys.stdout.write(new_text)
            if not new_text.endswith("\n"):
                sys.stdout.write("\n")
    result_info["status"] = "ok"
    if json_report:
        print(json.dumps(result_info, indent=2, ensure_ascii=False))
    return result_info


def _default_output(input_path: str, cmd: str) -> str:
    p = Path(input_path)
    suffix = ".cleaned" if cmd == "clean" else ".rewritten"
    return str(p.with_name(p.stem + suffix + p.suffix))


def _process_directory(input_dir: str, output_dir: str | None, cmd: str, strict: bool,
                       seed: int, dry_run: bool, show_diff: bool, json_report: bool,
                       lang: str = 'auto', profile: str = 'balanced', llm: str | None = None) -> None:
    in_root = Path(input_dir)
    out_root = Path(output_dir) if output_dir else None
    if out_root is None and not dry_run:
        print("directory processing requires -o OUTPUT_DIR", file=sys.stderr)
        sys.exit(1)
    results = []
    for root, _, files in os.walk(in_root):
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() not in SUPPORTED_EXTS:
                continue
            rel = p.relative_to(in_root)
            out = (out_root / rel) if out_root else None
            if out is not None:
                out.parent.mkdir(parents=True, exist_ok=True)
            info = _process_file(str(p), str(out) if out else None, cmd, strict, seed,
                                 dry_run, False, False, lang, profile, llm)
            results.append(info)
    if json_report:
        print(json.dumps(results, indent=2, ensure_ascii=False))


def _check_file(path: str, json_out: bool) -> None:
    fmt = detect_format(path)
    if fmt in ("docx", "zip"):
        print(f"{path}: format {fmt} (metrics skipped for binary)", file=sys.stderr)
        return
    text = read_text_file(path)
    m = metrics_report(text)
    # AI-ish pattern counts
    ai_patterns = ["delve", "tapestry", "moreover", "furthermore",
                   "in conclusion", "it is important to note", "plays a crucial role",
                   "robust", "comprehensive", "leverage", "utilize"]
    low = text.lower()
    counts = {p: low.count(p) for p in ai_patterns}
    ai_score = sum(counts.values())
    info = {"file": path, "metrics": m, "ai_pattern_hits": counts, "ai_pattern_total": ai_score}
    if json_out:
        print(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        print(f"== {path} ==")
        for k, v in m.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
        print(f"  ai_pattern_total: {ai_score}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="textscope", description="Clean & rewrite text for AI-detection evasion.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name in ("clean", "rewrite"):
        sp = sub.add_parser(name)
        sp.add_argument("input", help="file, directory, or .zip")
        sp.add_argument("-o", "--output", help="output file or directory")
        sp.add_argument("--dry-run", action="store_true")
        sp.add_argument("--diff", action="store_true")
        sp.add_argument("--json", action="store_true", dest="json_report")
        sp.add_argument("--seed", type=int, default=0, help="varyasyon tohumu: farklı seed = farklı çıktı (aynı seed = aynı çıktı)")
        sp.add_argument("--lang", default="auto", choices=["auto", "en", "tr"], help="language")
        sp.add_argument("--profile", default="balanced", choices=["conservative", "balanced", "aggressive"], help="rewrite profile")
        sp.add_argument("--in-place", action="store_true", help="overwrite input file")
        sp.add_argument("--llm", default=None, help="LLM backend, e.g. openai:gpt-4o-mini (requires extra)")
        if name == "rewrite":
            sp.add_argument("--strict", action="store_true", help="preserve word count exactly")

    csp = sub.add_parser("check")
    csp.add_argument("input", help="file")
    csp.add_argument("--json", action="store_true", dest="json_report")

    dsp = sub.add_parser("detect")
    dsp.add_argument("input", help="file")
    dsp.add_argument("--json", action="store_true", dest="json_report")

    ssp = sub.add_parser("serve")
    ssp.add_argument("--host", default="127.0.0.1")
    ssp.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)

    if args.cmd == "check":
        _check_file(args.input, args.json_report)
        return 0

    if args.cmd == "detect":
        text = read_text_file(args.input)
        res = detect_mod.detect(text)
        if args.json_report:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "serve":
        from .server import serve as serve_http
        serve_http(host=args.host, port=args.port)
        return 0

    strict = getattr(args, "strict", False)
    input_path = args.input
    if getattr(args, 'in_place', False) and not os.path.isdir(input_path):
        import shutil
        shutil.copy2(input_path, input_path + ".bak")
        args.output = input_path
    if os.path.isdir(input_path):
        _process_directory(input_path, args.output, args.cmd, strict, args.seed,
                           args.dry_run, args.diff, args.json_report,
                           getattr(args, 'lang', 'auto'), getattr(args, 'profile', 'balanced'),
                           getattr(args, 'llm', None))
    else:
        _process_file(input_path, args.output, args.cmd, strict, args.seed,
                      args.dry_run, args.diff, args.json_report,
                      getattr(args, 'lang', 'auto'), getattr(args, 'profile', 'balanced'),
                      getattr(args, 'llm', None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

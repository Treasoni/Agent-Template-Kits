#!/usr/bin/env python3
"""Render the canonical Markdown user guide into deterministic standalone HTML."""

from __future__ import annotations

import argparse
import hashlib
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/Agent Template Kits — 功能与使用文档.md"
OUTPUT = ROOT / "docs/USER_GUIDE.html"
TABLE_SEPARATOR = re.compile(r"^\|?(?:\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?$")


STYLE = """
:root{color-scheme:dark;--bg:#0d1117;--panel:#161b22;--border:#30363d;--text:#c9d1d9;--bright:#f0f6fc;--dim:#8b949e;--accent:#58a6ff;--code:#010409}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif}
.page{display:flex;max-width:1440px;margin:auto}.sidebar{position:sticky;top:0;width:285px;min-width:285px;height:100vh;overflow:auto;padding:24px 18px;background:var(--panel);border-right:1px solid var(--border)}
.sidebar strong{display:block;margin-bottom:14px;color:var(--bright)}.sidebar a{display:block;padding:5px 8px;color:var(--dim);text-decoration:none;border-radius:5px}.sidebar a:hover{color:var(--accent);background:#21262d}.sidebar .sub{padding-left:24px;font-size:13px}
main{min-width:0;max-width:1080px;padding:44px 58px}h1,h2,h3,h4{color:var(--bright);line-height:1.3}h1{font-size:32px}h2{margin-top:48px;padding-bottom:10px;border-bottom:1px solid var(--border)}h3{margin-top:30px}a{color:var(--accent)}
code,pre{font-family:"SFMono-Regular",Consolas,monospace}code{padding:2px 5px;background:#1c2128;border-radius:4px;color:#ffa657}pre{overflow:auto;padding:16px 18px;background:var(--code);border:1px solid var(--border);border-radius:8px}pre code{padding:0;background:none;color:var(--text)}
blockquote{margin:16px 0;padding:10px 18px;background:var(--panel);border-left:3px solid var(--accent)}table{width:100%;border-collapse:collapse;margin:16px 0}th,td{padding:9px 12px;border:1px solid var(--border);vertical-align:top}th{background:#21262d;color:var(--bright)}tr:nth-child(even) td{background:var(--panel)}hr{border:0;border-top:1px solid var(--border);margin:38px 0}li{margin:4px 0}
.source-note{margin-top:48px;color:var(--dim);font-size:13px;text-align:center}@media(max-width:900px){.sidebar{display:none}main{padding:24px 20px}}
""".strip()


def slugify(text: str) -> str:
    plain = re.sub(r"[`*_]", "", text).strip().lower()
    plain = re.sub(r"[^\w\u4e00-\u9fff]+", "-", plain, flags=re.UNICODE)
    return plain.strip("-") or "section"


def inline(text: str) -> str:
    placeholders: list[str] = []

    def stash(value: str) -> str:
        placeholders.append(value)
        return f"\x00{len(placeholders) - 1}\x00"

    text = re.sub(
        r"`([^`]+)`",
        lambda match: stash(f"<code>{html.escape(match.group(1))}</code>"),
        text,
    )
    escaped = html.escape(text, quote=False)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        escaped,
    )
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    for index, value in enumerate(placeholders):
        escaped = escaped.replace(f"\x00{index}\x00", value)
    return escaped


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_markdown(markdown: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = markdown.splitlines()
    output: list[str] = []
    headings: list[tuple[int, str, str]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            index += 1
            continue
        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(lines[index])
                index += 1
            index += 1
            class_name = f' class="language-{html.escape(language, quote=True)}"' if language else ""
            output.append(f"<pre><code{class_name}>{html.escape(chr(10).join(code))}</code></pre>")
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            anchor = slugify(title)
            headings.append((level, title, anchor))
            output.append(f'<h{level} id="{anchor}">{inline(title)}</h{level}>')
            index += 1
            continue
        if stripped == "---":
            output.append("<hr>")
            index += 1
            continue
        if stripped.startswith("|") and index + 1 < len(lines) and TABLE_SEPARATOR.match(lines[index + 1].strip()):
            headers = table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(table_cells(lines[index]))
                index += 1
            output.append("<table><thead><tr>" + "".join(f"<th>{inline(cell)}</th>" for cell in headers) + "</tr></thead><tbody>")
            output.extend("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>" for row in rows)
            output.append("</tbody></table>")
            continue
        if stripped.startswith(">"):
            quote: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote.append(lines[index].strip()[1:].strip())
                index += 1
            output.append("<blockquote><p>" + "<br>".join(inline(value) for value in quote) + "</p></blockquote>")
            continue
        list_match = re.match(r"^(?:[-*]\s+|(\d+)\.\s+)(.+)$", stripped)
        if list_match:
            ordered = list_match.group(1) is not None
            tag = "ol" if ordered else "ul"
            items: list[str] = []
            while index < len(lines):
                candidate = lines[index].strip()
                match = re.match(r"^(?:[-*]\s+|(\d+)\.\s+)(.+)$", candidate)
                if not match or (match.group(1) is not None) != ordered:
                    break
                items.append(match.group(2))
                index += 1
            output.append(f"<{tag}>" + "".join(f"<li>{inline(item)}</li>" for item in items) + f"</{tag}>")
            continue

        paragraph = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate or candidate.startswith(("#", "```", ">", "|", "- ", "* ")) or candidate == "---" or re.match(r"^\d+\.\s+", candidate):
                break
            paragraph.append(candidate)
            index += 1
        output.append("<p>" + " ".join(inline(value.rstrip()) for value in paragraph) + "</p>")
    return "\n".join(output), headings


def render_document(markdown: str) -> str:
    body, headings = render_markdown(markdown)
    title = headings[0][1] if headings else "Agent Template Kits"
    navigation = []
    for level, text, anchor in headings:
        if level not in {2, 3} or text == "目录":
            continue
        class_name = ' class="sub"' if level == 3 else ""
        navigation.append(f'<a href="#{anchor}"{class_name}>{inline(text)}</a>')
    source_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="source-sha256" content="{source_hash}">
<title>{html.escape(title)}</title>
<style>{STYLE}</style>
</head>
<body>
<!-- Generated by scripts/render-user-guide.py from docs/Agent Template Kits — 功能与使用文档.md. -->
<div class="page">
<nav class="sidebar"><strong>Agent Template Kits</strong>{''.join(navigation)}</nav>
<main>{body}<p class="source-note">由 canonical Markdown 文档确定性生成</p></main>
</div>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when the generated HTML is stale")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    expected = render_document(args.source.read_text(encoding="utf-8"))
    if args.check:
        actual = args.output.read_text(encoding="utf-8") if args.output.is_file() else None
        if actual != expected:
            print(f"docs: generated HTML is stale: {args.output}")
            return 1
        print("docs: generated HTML is current")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(expected, encoding="utf-8")
    print(f"docs: generated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compile a lightweight Markdown slide deck into a self-contained HTML file.

Deck conventions:
- YAML front matter at the start.
- Slides separated by a line containing exactly `---`.
- Optional per-slide metadata comments at the start:
    <!-- class: title dense -->
    <!-- footer: [Source](https://example.com) -->
- Columns separated by a line containing exactly `+++`.
- Speaker notes begin after a line containing exactly `???`.

The generated deck is self-contained: no CDN assets are required.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from typing import Any

import mistune
import yaml
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound


class SlideRenderer(mistune.HTMLRenderer):
    def __init__(self) -> None:
        super().__init__(escape=False)
        self.formatter = HtmlFormatter(nowrap=True, style="monokai")

    def block_code(self, code: str, info: str | None = None) -> str:
        language = (info or "text").strip().split()[0]
        aliases = {
            "lean4": "lean4",
            "lean": "lean4",
            "rs": "rust",
            "sh": "bash",
        }
        lexer_name = aliases.get(language, language)
        try:
            lexer = get_lexer_by_name(lexer_name)
        except ClassNotFound:
            lexer = TextLexer()
        highlighted = highlight(code, lexer, self.formatter)
        safe_lang = re.sub(r"[^a-zA-Z0-9_-]", "", language)
        return (
            f'<pre class="code-block language-{safe_lang}"><code>'
            f"{highlighted}</code></pre>"
        )

    def link(self, text: str, url: str, title: str | None = None) -> str:
        title_attr = f' title="{html.escape(title)}"' if title else ""
        return (
            f'<a href="{html.escape(url, quote=True)}"{title_attr} '
            f'target="_blank" rel="noopener noreferrer">{text}</a>'
        )


MARKDOWN = mistune.create_markdown(
    renderer=SlideRenderer(),
    plugins=["table", "strikethrough", "task_lists", "url"],
)


def split_outside_fences(text: str, delimiter: str) -> list[str]:
    """Split on an exact delimiter line, ignoring fenced code blocks."""
    chunks: list[list[str]] = [[]]
    in_fence = False
    fence_marker = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            chunks[-1].append(line)
            continue
        if not in_fence and stripped == delimiter:
            chunks.append([])
        else:
            chunks[-1].append(line)
    return ["\n".join(chunk).strip() for chunk in chunks]


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    metadata = yaml.safe_load(text[4:end]) or {}
    return metadata, text[end + 5 :]


def parse_slide_metadata(slide: str) -> tuple[dict[str, str], str]:
    """Extract recognised metadata comments from anywhere in a slide."""
    metadata: dict[str, str] = {}
    body_lines: list[str] = []
    pattern = re.compile(r"^\s*<!--\s*([a-zA-Z_-]+)\s*:\s*(.*?)\s*-->\s*$")
    recognised = {"class", "footer", "id"}
    for line in slide.splitlines():
        match = pattern.match(line)
        if match and match.group(1).lower() in recognised:
            key = match.group(1).lower()
            value = match.group(2)
            if key == "class" and key in metadata:
                metadata[key] = metadata[key] + " " + value
            else:
                metadata[key] = value
        else:
            body_lines.append(line)
    body = "\n".join(body_lines).strip()
    return metadata, body


def render_inline(markdown_text: str) -> str:
    rendered = MARKDOWN(markdown_text).strip()
    if rendered.startswith("<p>") and rendered.endswith("</p>"):
        rendered = rendered[3:-4]
    return rendered


def render_slide(slide_text: str, index: int, total: int, deck_title: str) -> str:
    meta, body = parse_slide_metadata(slide_text)
    body_and_notes = split_outside_fences(body, "???")
    body = body_and_notes[0] if body_and_notes else ""
    notes = body_and_notes[1] if len(body_and_notes) > 1 else ""

    columns = split_outside_fences(body, "+++")
    if len(columns) > 1:
        prefix = ""
        grid_columns = columns
        # A common slide pattern is a full-width heading followed by two columns.
        # When the first chunk begins with an H1 and there are at least two chunks
        # after it, keep that heading above the grid rather than making it a third column.
        if len(columns) >= 3 and columns[0].lstrip().startswith("# "):
            prefix = MARKDOWN(columns[0])
            grid_columns = columns[1:]
        rendered_columns = "".join(
            f'<div class="column">{MARKDOWN(column)}</div>' for column in grid_columns
        )
        content = prefix + f'<div class="columns columns-{len(grid_columns)}">{rendered_columns}</div>'
    else:
        content = MARKDOWN(body)

    classes = ["slide"]
    classes.extend(meta.get("class", "").split())
    if index == 0 and "title" not in classes:
        classes.append("title")
    slide_id = meta.get("id", f"slide-{index + 1}")

    footer = meta.get("footer", "")
    footer_html = render_inline(footer) if footer else ""
    notes_html = MARKDOWN(notes) if notes else ""

    return f"""
<section class="{' '.join(classes)}" id="{html.escape(slide_id)}" data-slide="{index + 1}" aria-hidden="true">
  <div class="slide-shell">
    <div class="slide-accent" aria-hidden="true"></div>
    <div class="slide-content">{content}</div>
    <div class="slide-footer">
      <div class="slide-source">{footer_html}</div>
      <div class="slide-index">{index + 1:02d} / {total:02d}</div>
    </div>
  </div>
  <aside class="speaker-notes" aria-label="Speaker notes">{notes_html}</aside>
</section>
"""


def build_html(metadata: dict[str, Any], slides: list[str]) -> str:
    title = str(metadata.get("title", "Slides"))
    subtitle = str(metadata.get("subtitle", ""))
    author = str(metadata.get("author", ""))
    description = str(metadata.get("description", subtitle or title))
    rendered_slides = "\n".join(
        render_slide(slide, i, len(slides), title) for i, slide in enumerate(slides)
    )
    pygments_css = HtmlFormatter(style="monokai").get_style_defs(".code-block")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{html.escape(description, quote=True)}">
<meta name="author" content="{html.escape(author, quote=True)}">
<title>{html.escape(title)}</title>
<style>
:root {{
  --bg: #0b1020;
  --panel: #111a2e;
  --panel-2: #17233b;
  --ink: #eef4ff;
  --muted: #aab8d0;
  --faint: #6f809d;
  --accent: #ff8a3d;
  --accent-2: #67d7c4;
  --blue: #7db7ff;
  --danger: #ff7474;
  --line: rgba(255,255,255,0.12);
  --shadow: 0 24px 90px rgba(0,0,0,0.45);
  --slide-w: min(100vw, 177.7777778vh);
  --slide-h: min(100vh, 56.25vw);
  --base: min(1.58vw, 2.81vh);
}}
* {{ box-sizing: border-box; }}
html, body {{ width: 100%; height: 100%; margin: 0; overflow: hidden; }}
body {{
  background:
    radial-gradient(circle at 16% 12%, rgba(103,215,196,0.10), transparent 30%),
    radial-gradient(circle at 88% 86%, rgba(255,138,61,0.09), transparent 34%),
    var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}}
#deck {{ position: fixed; inset: 0; display: grid; place-items: center; }}
.slide {{
  display: none;
  position: absolute;
  width: var(--slide-w);
  height: var(--slide-h);
  overflow: hidden;
  background:
    linear-gradient(120deg, rgba(255,255,255,0.025), transparent 40%),
    linear-gradient(165deg, #0d1426 0%, #101a30 60%, #0c1426 100%);
  box-shadow: var(--shadow);
  isolation: isolate;
}}
.slide.active {{ display: block; }}
.slide::before {{
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: calc(var(--base) * 1.5) calc(var(--base) * 1.5);
  mask-image: linear-gradient(to bottom, rgba(0,0,0,0.4), transparent 62%);
  pointer-events: none;
  z-index: -1;
}}
.slide-shell {{ position: absolute; inset: 0; padding: 5.3% 6.2% 4.8%; display: flex; flex-direction: column; }}
.slide-accent {{
  position: absolute; left: 0; top: 8.5%; width: 0.42%; height: 18%;
  background: linear-gradient(var(--accent), var(--accent-2));
  border-radius: 0 999px 999px 0;
}}
.slide-content {{
  flex: 1;
  min-height: 0;
  font-size: var(--base);
  line-height: 1.28;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}}
h1, h2, h3 {{ margin: 0; line-height: 1.04; letter-spacing: -0.025em; }}
h1 {{ font-size: 2.05em; margin-bottom: 0.48em; max-width: 95%; }}
h2 {{ font-size: 1.33em; margin: 0.55em 0 0.28em; color: var(--blue); }}
h3 {{ font-size: 1.02em; margin: 0.55em 0 0.18em; color: var(--accent-2); letter-spacing: 0; }}
p {{ margin: 0.22em 0 0.55em; }}
strong {{ color: #ffffff; font-weight: 750; }}
em {{ color: #d8e2f4; }}
a {{ color: var(--accent-2); text-decoration-thickness: 0.07em; text-underline-offset: 0.12em; }}
code {{
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.92em;
  color: #ffe0c7;
  background: rgba(255,255,255,0.07);
  padding: 0.08em 0.25em;
  border-radius: 0.22em;
}}
ul, ol {{ margin: 0.18em 0 0.35em 1.08em; padding: 0; }}
li {{ margin: 0.25em 0; padding-left: 0.10em; }}
li::marker {{ color: var(--accent); }}
blockquote {{
  margin: 0.45em 0;
  padding: 0.55em 0.75em 0.58em;
  border-left: 0.22em solid var(--accent);
  background: rgba(255,138,61,0.085);
  border-radius: 0.25em;
}}
blockquote p:last-child {{ margin-bottom: 0; }}
hr {{ border: 0; border-top: 1px solid var(--line); margin: 0.6em 0; }}
.columns {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1.0em; min-height: 0; }}
.columns-3 {{ grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.7em; }}
.column {{ min-width: 0; }}
.column > :first-child {{ margin-top: 0; }}
.column > h2:first-child, .column > h3:first-child {{ margin-top: 0.08em; }}
.code-block {{
  margin: 0.30em 0 0.55em;
  padding: 0.64em 0.76em;
  background: #080d18;
  border: 1px solid rgba(255,255,255,0.11);
  border-radius: 0.45em;
  overflow: hidden;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 0.71em;
  line-height: 1.36;
  box-shadow: inset 0 1px rgba(255,255,255,0.035);
}}
.code-block code {{ background: transparent; color: inherit; padding: 0; border-radius: 0; font-size: inherit; }}
table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin: 0.35em 0; font-size: 0.76em; overflow: hidden; border: 1px solid var(--line); border-radius: 0.4em; }}
th, td {{ padding: 0.52em 0.62em; text-align: left; vertical-align: top; border-bottom: 1px solid var(--line); }}
th {{ background: rgba(125,183,255,0.12); color: #fff; font-weight: 720; }}
tr:last-child td {{ border-bottom: 0; }}
td + td, th + th {{ border-left: 1px solid var(--line); }}
.slide-footer {{
  height: 0.95em;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1em;
  color: var(--faint);
  font-size: calc(var(--base) * 0.46);
  letter-spacing: 0.015em;
}}
.slide-source {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.slide-source a {{ color: #8799b8; }}
.slide-index {{ flex: none; font-variant-numeric: tabular-nums; }}
.title .slide-shell {{ justify-content: center; padding-left: 7.2%; }}
.title .slide-content {{ justify-content: center; max-width: 83%; }}
.title h1 {{ font-size: 2.82em; margin-bottom: 0.20em; }}
.title h2 {{ font-size: 1.16em; font-weight: 520; color: var(--muted); margin: 0.2em 0 0.9em; line-height: 1.28; letter-spacing: -0.012em; }}
.title .slide-accent {{ height: 56%; top: 22%; width: 0.52%; }}
.title::after {{
  content: "∀   →   ?";
  position: absolute;
  right: 5.4%; bottom: 7.4%;
  font: 700 1.35em/1 "SFMono-Regular", Consolas, monospace;
  color: rgba(255,255,255,0.12);
  letter-spacing: 0.5em;
}}
.section .slide-content {{ justify-content: center; max-width: 85%; }}
.section h1 {{ font-size: 2.55em; }}
.section p {{ font-size: 1.08em; color: var(--muted); max-width: 85%; }}
.dense .slide-content {{ font-size: calc(var(--base) * 0.87); }}
.dense .code-block {{ font-size: 0.68em; }}
.center .slide-content {{ justify-content: center; text-align: center; }}
.big-quote blockquote {{ font-size: 1.27em; padding: 0.75em 0.9em; }}
.kicker {{
  display: inline-block;
  width: fit-content;
  margin-bottom: 0.68em;
  padding: 0.22em 0.52em;
  border: 1px solid rgba(103,215,196,0.45);
  border-radius: 999px;
  color: var(--accent-2);
  font-weight: 700;
  font-size: 0.58em;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}}
.lead {{ font-size: 1.18em; color: #dbe7f8; max-width: 90%; }}
.muted {{ color: var(--muted); }}
.accent {{ color: var(--accent); }}
.ok {{ color: var(--accent-2); }}
.warn {{ color: var(--danger); }}
.small {{ font-size: 0.77em; }}
.mini {{ font-size: 0.62em; }}
.card-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.62em; margin-top: 0.35em; }}
.card {{
  padding: 0.72em 0.76em;
  border: 1px solid var(--line);
  border-radius: 0.48em;
  background: linear-gradient(145deg, rgba(255,255,255,0.055), rgba(255,255,255,0.025));
}}
.card h3 {{ margin-top: 0; color: var(--ink); }}
.card p {{ margin-bottom: 0; font-size: 0.78em; color: var(--muted); }}
.pipeline {{ display: flex; align-items: stretch; gap: 0.36em; margin: 0.65em 0 0.45em; }}
.pipe-node {{
  flex: 1;
  padding: 0.62em 0.48em;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: rgba(125,183,255,0.09);
  border: 1px solid rgba(125,183,255,0.26);
  border-radius: 0.42em;
  font-weight: 680;
  line-height: 1.15;
}}
.pipe-node.accent-node {{ background: rgba(255,138,61,0.10); border-color: rgba(255,138,61,0.33); }}
.pipe-arrow {{ display: flex; align-items: center; color: var(--accent); font-weight: 800; }}
.logic-grid {{ display: grid; grid-template-columns: 0.78fr 1.15fr 1.35fr; gap: 0; margin-top: 0.35em; border: 1px solid var(--line); border-radius: 0.45em; overflow: hidden; font-size: 0.76em; }}
.logic-grid > div {{ padding: 0.58em 0.66em; border-bottom: 1px solid var(--line); }}
.logic-grid > div:nth-child(3n+2), .logic-grid > div:nth-child(3n+3) {{ border-left: 1px solid var(--line); }}
.logic-grid > div:nth-last-child(-n+3) {{ border-bottom: 0; }}
.logic-grid .head {{ background: rgba(125,183,255,0.12); color: #fff; font-weight: 720; }}
.stack-diagram {{ position: relative; margin: 0.42em auto; width: 88%; display: grid; gap: 0.26em; }}
.stack-layer {{ padding: 0.46em 0.72em; text-align: center; border: 1px solid var(--line); border-radius: 0.36em; background: rgba(255,255,255,0.045); }}
.stack-layer.kernel {{ background: rgba(103,215,196,0.12); border-color: rgba(103,215,196,0.38); font-weight: 750; }}
.stack-layer.assumption {{ background: rgba(255,138,61,0.09); border-color: rgba(255,138,61,0.31); }}
.arrow-list {{ list-style: none; margin-left: 0; }}
.arrow-list li {{ position: relative; padding-left: 1.25em; }}
.arrow-list li::before {{ content: "→"; position: absolute; left: 0; color: var(--accent); font-weight: 800; }}
.arrow-list li::marker {{ content: ""; }}
.timeline {{ display: grid; grid-template-columns: auto 1fr; column-gap: 0.65em; row-gap: 0.34em; margin-top: 0.35em; }}
.timeline .num {{ width: 1.65em; height: 1.65em; border-radius: 50%; display: grid; place-items: center; background: rgba(255,138,61,0.15); border: 1px solid rgba(255,138,61,0.38); color: var(--accent); font-weight: 800; }}
.timeline .step {{ padding-top: 0.16em; }}
.badge-row {{ display: flex; flex-wrap: wrap; gap: 0.38em; margin-top: 0.42em; }}
.badge {{ padding: 0.28em 0.48em; border-radius: 0.35em; background: rgba(255,255,255,0.07); border: 1px solid var(--line); font-size: 0.72em; }}
.speaker-notes {{ display: none; }}
body.notes-visible .speaker-notes {{
  display: block;
  position: fixed;
  z-index: 50;
  right: 1.2rem;
  bottom: 2.2rem;
  width: min(38rem, 42vw);
  max-height: 42vh;
  overflow: auto;
  padding: 1rem 1.15rem;
  color: #172033;
  background: rgba(250,252,255,0.96);
  border-radius: 0.6rem;
  box-shadow: 0 20px 60px rgba(0,0,0,0.45);
  font-size: 15px;
  line-height: 1.45;
}}
#progress {{ position: fixed; left: 0; bottom: 0; width: 100%; height: 4px; background: rgba(255,255,255,0.06); z-index: 80; }}
#progress > div {{ height: 100%; width: 0; background: linear-gradient(90deg, var(--accent), var(--accent-2)); transition: width 180ms ease; }}
#help {{
  display: none;
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(5,8,16,0.84);
  place-items: center;
  backdrop-filter: blur(7px);
}}
#help.visible {{ display: grid; }}
#help .panel {{ width: min(640px, 84vw); padding: 1.6rem 1.8rem; border: 1px solid var(--line); border-radius: 0.8rem; background: #111a2e; box-shadow: var(--shadow); }}
#help h2 {{ margin-top: 0; color: var(--ink); }}
#help kbd {{ display: inline-block; min-width: 2.1em; padding: 0.18em 0.42em; margin-right: 0.45em; text-align: center; border: 1px solid rgba(255,255,255,0.22); border-radius: 0.3em; background: rgba(255,255,255,0.06); color: #fff; font-family: inherit; }}
{pygments_css}
@media (prefers-reduced-motion: no-preference) {{
  .slide.active .slide-content > * {{ animation: rise 280ms ease-out both; }}
  @keyframes rise {{ from {{ opacity: 0; transform: translateY(0.22em); }} to {{ opacity: 1; transform: translateY(0); }} }}
}}
@media print {{
  @page {{ size: 13.333in 7.5in; margin: 0; }}
  html, body {{ overflow: visible; width: auto; height: auto; background: white; }}
  #deck {{ position: static; display: block; }}
  .slide, .slide.active {{ display: block !important; position: relative; width: 13.333in; height: 7.5in; page-break-after: always; box-shadow: none; }}
  #progress, #help {{ display: none !important; }}
}}
</style>
</head>
<body>
<main id="deck" aria-label="{html.escape(title, quote=True)}">
{rendered_slides}
</main>
<div id="progress" aria-hidden="true"><div></div></div>
<div id="help" role="dialog" aria-modal="true" aria-label="Keyboard shortcuts">
  <div class="panel">
    <h2>Keyboard shortcuts</h2>
    <p><kbd>→</kbd><kbd>Space</kbd> next slide</p>
    <p><kbd>←</kbd> previous slide</p>
    <p><kbd>Home</kbd><kbd>End</kbd> first / last</p>
    <p><kbd>F</kbd> fullscreen &nbsp; <kbd>N</kbd> notes &nbsp; <kbd>?</kbd> help</p>
  </div>
</div>
<script>
(() => {{
  const slides = Array.from(document.querySelectorAll('.slide'));
  const progress = document.querySelector('#progress > div');
  const help = document.querySelector('#help');
  let current = 0;

  function fromHash() {{
    const raw = location.hash.replace(/^#(?:slide-)?/, '');
    const n = Number(raw);
    return Number.isFinite(n) && n >= 1 && n <= slides.length ? n - 1 : 0;
  }}

  function show(index, updateHash = true) {{
    current = Math.max(0, Math.min(slides.length - 1, index));
    slides.forEach((slide, i) => {{
      const active = i === current;
      slide.classList.toggle('active', active);
      slide.setAttribute('aria-hidden', active ? 'false' : 'true');
    }});
    progress.style.width = `${{((current + 1) / slides.length) * 100}}%`;
    if (updateHash) history.replaceState(null, '', `#${{current + 1}}`);
    document.title = `${{current + 1}}/${{slides.length}} · {html.escape(title)}`;
  }}

  function next() {{ show(current + 1); }}
  function prev() {{ show(current - 1); }}

  document.addEventListener('keydown', (event) => {{
    if (event.target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return;
    if (['ArrowRight', 'PageDown', ' ', 'Enter'].includes(event.key)) {{ event.preventDefault(); next(); }}
    else if (['ArrowLeft', 'PageUp', 'Backspace'].includes(event.key)) {{ event.preventDefault(); prev(); }}
    else if (event.key === 'Home') {{ event.preventDefault(); show(0); }}
    else if (event.key === 'End') {{ event.preventDefault(); show(slides.length - 1); }}
    else if (event.key.toLowerCase() === 'f') {{
      event.preventDefault();
      if (!document.fullscreenElement) document.documentElement.requestFullscreen?.();
      else document.exitFullscreen?.();
    }}
    else if (event.key.toLowerCase() === 'n') {{ document.body.classList.toggle('notes-visible'); }}
    else if (event.key === '?' || event.key.toLowerCase() === 'h') {{ help.classList.toggle('visible'); }}
    else if (event.key === 'Escape') {{ help.classList.remove('visible'); document.body.classList.remove('notes-visible'); }}
  }});

  document.addEventListener('click', (event) => {{
    if (event.target.closest('a, button, .speaker-notes, #help .panel')) return;
    if (help.classList.contains('visible')) {{ help.classList.remove('visible'); return; }}
    if (event.clientX < window.innerWidth * 0.35) prev(); else next();
  }});

  let touchStartX = null;
  document.addEventListener('touchstart', e => {{ touchStartX = e.changedTouches[0].clientX; }}, {{passive: true}});
  document.addEventListener('touchend', e => {{
    if (touchStartX === null) return;
    const dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 50) dx < 0 ? next() : prev();
    touchStartX = null;
  }}, {{passive: true}});

  window.addEventListener('hashchange', () => show(fromHash(), false));
  show(fromHash(), false);
}})();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    source_text = args.source.read_text(encoding="utf-8")
    metadata, body = parse_front_matter(source_text)
    slides = [s for s in split_outside_fences(body, "---") if s.strip()]
    if not slides:
        raise SystemExit("No slides found")
    html_text = build_html(metadata, slides)
    args.output.write_text(html_text, encoding="utf-8")
    print(f"Wrote {args.output} ({len(slides)} slides)")


if __name__ == "__main__":
    main()

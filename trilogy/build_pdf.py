# -*- coding: utf-8 -*-
"""Сборка PDF из markdown: md -> html -> headless Chrome.

Зависимость одна: `pip install markdown`. Всё остальное — стандартная
библиотека и уже установленный Chrome.

    python build_pdf.py a.md b.md ...            # PDF рядом с каждым md
    python build_pdf.py --outdir out a.md ...    # PDF в указанный каталог

Формулы. В текстах они записаны как $...$ и $$...$$. Отдельного LaTeX-движка
нет, поэтому набор команд переводится в Unicode точечно: словарь SYM плюс
верхние и нижние индексы. Неизвестная команда не выдумывается — она остаётся
в тексте как есть, чтобы её было видно в готовом PDF, а не молча потерять.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

import markdown

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROME_PATH = os.environ.get(
    "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

SYM = [
    (r"\pmod", " mod "),
    (r"\times", "×"),
    (r"\to", "→"),
    (r"\le", "≤"),
    (r"\ge", "≥"),
    (r"\Delta", "Δ"),
    (r"\rho", "ρ"),
    (r"\tau", "τ"),
    (r"\chi", "χ"),
    (r"\sigma", "σ"),
    (r"\mu", "μ"),
    (r"\alpha", "α"),
    (r"\in", "∈"),
    (r"\cdot", "·"),
    (r"\pm", "±"),
    (r"\approx", "≈"),
    (r"\ne", "≠"),
    (r"\equiv", "≡"),
    (r"\ldots", "…"),
    (r"\dots", "…"),
    (r"\%", "%"),
    (r"\ ", " "),
    (r"\,", " "),
    (r"\;", " "),
]


def _math(s: str) -> str:
    s = s.strip()
    # \text{...} и \mathrm{...} — просто содержимое
    s = re.sub(r"\\(?:text|mathrm|operatorname)\{([^{}]*)\}", r"\1", s)
    for a, b in SYM:
        s = s.replace(a, b)
    s = s.replace(r"\_", "_").replace(r"\{", "{").replace(r"\}", "}")
    # индексы
    s = re.sub(r"\^\{([^{}]*)\}", r"<sup>\1</sup>", s)
    s = re.sub(r"\^(\*|\d)", r"<sup>\1</sup>", s)
    s = re.sub(r"_\{([^{}]*)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"_([A-Za-z0-9])", r"<sub>\1</sub>", s)
    # остатки фигурных скобок
    s = s.replace("{", "").replace("}", "")
    # одиночные латинские буквы — курсивом
    s = re.sub(r"(?<![A-Za-z])([A-Za-z])(?![A-Za-z])", r"<i>\1</i>", s)
    # звёздочка из формул не должна попадать в разметку как маркер акцента
    s = s.replace("*", "&#42;")
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s


def md_to_html(md: str) -> str:
    """markdown -> html с защитой блоков кода от подстановок формул."""
    fences = []

    def stash(m):
        fences.append(m.group(0))
        return "\x00F%d\x00" % (len(fences) - 1)

    md = re.sub(r"```[^\n]*\n.*?```", stash, md, flags=re.S)

    md = re.sub(r"\$\$(.+?)\$\$", lambda m: '<div class="math-display">%s</div>' % _math(m.group(1)), md, flags=re.S)
    md = re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)\$(?!\$)", lambda m: '<span class="math">%s</span>' % _math(m.group(1)), md)

    md = re.sub("\x00F(\\d+)\x00", lambda m: fences[int(m.group(1))], md)
    return markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])


CSS = """
@page { size: A4; margin: 22mm 19mm 22mm 19mm; }
body {
  font-family: Georgia, Cambria, 'Times New Roman', serif;
  font-size: 10.5pt; line-height: 1.66; color: #1a202c; background: #fff;
}
h1, h2, h3, h4 { font-family: 'Segoe UI', system-ui, sans-serif; color: #1a365d; line-height: 1.3; }
h1 { font-size: 19pt; margin: 0 0 .6em; padding-bottom: 6px; border-bottom: 2px solid #2b6cb0; page-break-after: avoid; }
h2 { font-size: 14pt; color: #2c5282; margin: 1.5em 0 .45em; page-break-after: avoid; }
h3 { font-size: 12pt; color: #2b6cb0; margin: 1.2em 0 .35em; page-break-after: avoid; }
h4 { font-size: 10.5pt; color: #4a5568; margin: 1em 0 .25em; page-break-after: avoid; }
p { margin: .45em 0 .8em; text-align: justify; }
a { color: #2b6cb0; text-decoration: none; }
code {
  font-family: 'Cascadia Code', Consolas, 'Courier New', monospace; font-size: 8.8pt;
  background: #edf2f7; color: #c53030; padding: 1px 4px; border-radius: 3px;
  border: 1px solid #e2e8f0; word-break: break-word;
}
pre {
  background: #f7fafc; border: 1px solid #cbd5e0; border-left: 4px solid #3182ce;
  padding: 10px 13px; border-radius: 4px; margin: .9em 0;
  font-family: 'Cascadia Code', Consolas, 'Courier New', monospace;
  font-size: 8.2pt; line-height: 1.4; color: #2d3748;
  white-space: pre-wrap; word-break: break-word; page-break-inside: avoid;
}
pre code { background: none; border: none; padding: 0; color: inherit; font-size: 8.2pt; }
table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 8.8pt; page-break-inside: avoid; }
th, td { border: 1px solid #cbd5e0; padding: 6px 9px; text-align: left; vertical-align: top; }
th { background: #ebf8ff; color: #2b6cb0; font-family: 'Segoe UI', system-ui, sans-serif; }
tr:nth-child(even) td { background: #f7fafc; }
blockquote {
  border-left: 4px solid #4299e1; margin: 1em 0; padding: 6px 13px;
  background: #ebf8ff; color: #2d3748; font-style: italic; page-break-inside: avoid;
}
hr { border: none; border-top: 1px solid #e2e8f0; margin: 1.6em 0; }
ul, ol { margin: .45em 0 .85em 1.5em; padding: 0; }
li { margin-bottom: .3em; }
.math { font-family: Georgia, serif; white-space: nowrap; }
.math-display {
  text-align: center; font-family: Georgia, serif; font-size: 11.5pt; padding: 9px 0;
  margin: 1em 0; background: #f7fafc; border: 1px dashed #cbd5e0; border-radius: 4px;
  page-break-inside: avoid;
}
img { max-width: 100%; }
"""


def build(md_path: str, out_dir: str, keep_html: bool = False) -> str:
    with open(md_path, encoding="utf-8") as f:
        md = f.read().replace("\r\n", "\n")

    base = os.path.splitext(os.path.basename(md_path))[0]
    pdf_path = os.path.join(out_dir, base + ".pdf")
    # HTML — промежуточный файл: в каталог он попадает только по --keep-html,
    # иначе живёт во временном и не мусорит в репозитории
    html_dir = out_dir if keep_html else tempfile.mkdtemp(prefix="pdfbuild_")
    html_path = os.path.join(html_dir, base + ".html")

    body = md_to_html(md)
    doc = (
        '<!DOCTYPE html>\n<html lang="ru">\n<head>\n<meta charset="UTF-8">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n</body>\n</html>\n"
        % (base, CSS, body)
    )
    with open(html_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)

    if not os.path.exists(CHROME_PATH):
        raise SystemExit("нет Chrome: %s (задайте CHROME_PATH)" % CHROME_PATH)

    res = subprocess.run(
        [
            CHROME_PATH,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--print-to-pdf=" + os.path.abspath(pdf_path),
            "file:///" + os.path.abspath(html_path).replace("\\", "/"),
        ],
        capture_output=True,
        timeout=180,
    )
    if not os.path.exists(pdf_path):
        raise SystemExit("Chrome не собрал PDF: %s" % res.stderr.decode("utf-8", "replace")[:400])

    left = body.count("$")
    size = os.path.getsize(pdf_path)
    print("  %-58s %8.1f KB  $: %d" % (os.path.basename(pdf_path), size / 1024.0, left))
    return pdf_path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--keep-html", action="store_true")
    a = ap.parse_args(argv)

    out_dir = a.outdir or os.path.dirname(os.path.abspath(a.files[0]))
    os.makedirs(out_dir, exist_ok=True)
    for p in a.files:
        build(p, out_dir, a.keep_html)
    return 0


if __name__ == "__main__":
    sys.exit(main())

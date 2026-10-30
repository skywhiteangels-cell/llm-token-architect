import os
import subprocess
import sys
from pathlib import Path

import markdown

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
STEM = "The_Ghost_in_the_Context_Window_Trilogy"
MD_PATH = HERE / f"{STEM}.md"
HTML_PATH = HERE / f"{STEM}.html"
PDF_PATH = HERE.parent / f"{STEM}.pdf"
# Path to Chrome. Override with CHROME_PATH if it lives elsewhere.
CHROME_PATH = os.environ.get(
    "CHROME_PATH", r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

with open(MD_PATH, "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to html with tables, fenced_code, and toc
html_body = markdown.markdown(
    md_content,
    extensions=["tables", "fenced_code", "toc"]
)

# Clean typography replacements for math and notation
html_body = html_body.replace("$D^*$", "<i>D</i><sup>*</sup>")
html_body = html_body.replace("$$f(N) = 10 \\cdot N - 6$$", "<div class='math-display'><i>f</i>(<i>N</i>) = 10 · <i>N</i> − 6</div>")
html_body = html_body.replace("$\\text{count} \\pmod 2 \\equiv 0$", "<code>count mod 2 == 0</code>")
html_body = html_body.replace("$N \\to N+1$", "<i>N</i> → <i>N</i>+1")
html_body = html_body.replace("$N \\le 8$", "<i>N</i> ≤ 8")
html_body = html_body.replace("$N = 16$", "<i>N</i> = 16")
html_body = html_body.replace("$N = 1$", "<i>N</i> = 1")
html_body = html_body.replace("$N = 64$", "<i>N</i> = 64")
html_body = html_body.replace("$N=8$", "<i>N</i> = 8")
html_body = html_body.replace("$N=16$", "<i>N</i> = 16")
html_body = html_body.replace("$N - 6$", "<i>N</i> − 6")
html_body = html_body.replace("$10N - 6$", "10<i>N</i> − 6")
html_body = html_body.replace("$N=17$", "<i>N</i> = 17")
html_body = html_body.replace("$N = 1..16$", "<i>N</i> = 1..16")
html_body = html_body.replace("$\\Delta = +10$", "Δ = +10")
html_body = html_body.replace("$\\Delta = +1$", "Δ = +1")
html_body = html_body.replace("$\\Delta = +10, +20, +30$", "Δ = +10, +20, +30")
html_body = html_body.replace("$2 \\times 5$", "2 × 5")
html_body = html_body.replace("$2 \\times 48$", "2 × 48")
html_body = html_body.replace("$p = 0.307$", "<i>p</i> = 0.307")
html_body = html_body.replace("$p = 0.022$", "<i>p</i> = 0.022")
html_body = html_body.replace("$p = 0.00098$", "<i>p</i> = 0.00098")
html_body = html_body.replace("$p = 0.675$", "<i>p</i> = 0.675")
html_body = html_body.replace("$p = 0.0017$", "<i>p</i> = 0.0017")
html_body = html_body.replace("$p$", "<i>p</i>")
html_body = html_body.replace("$31.2\\%$", "31.2%")
html_body = html_body.replace("$45.8\\%$", "45.8%")
html_body = html_body.replace("$58.3\\%$", "58.3%")
html_body = html_body.replace("$64.6\\%$", "64.6%")
html_body = html_body.replace("$29.2\\%$", "29.2%")
html_body = html_body.replace("$54.2\\%$", "54.2%")
html_body = html_body.replace("$100\\%$", "100%")
html_body = html_body.replace("$89.6\\%$", "89.6%")
html_body = html_body.replace("$66.7\\%$", "66.7%")
html_body = html_body.replace("$62.5\\%$", "62.5%")
html_body = html_body.replace("$93.8\\%$", "93.8%")
html_body = html_body.replace("$35.4\\%$", "35.4%")
html_body = html_body.replace("$41.7\\%$", "41.7%")
html_body = html_body.replace("$22.9\\%$", "22.9%")
html_body = html_body.replace("$4.2\\%$", "4.2%")
html_body = html_body.replace("$3.8\\%$", "3.8%")
html_body = html_body.replace("$7.4\\%$", "7.4%")
html_body = html_body.replace("$34.4\\%$", "34.4%")
html_body = html_body.replace("$31.2\\%$", "31.2%")
html_body = html_body.replace("$6.2\\%$", "6.2%")
html_body = html_body.replace("$75.0\\%$", "75.0%")
html_body = html_body.replace("$75\\%$", "75%")
html_body = html_body.replace("$15..23$", "15..23")
html_body = html_body.replace("$17..23$", "17..23")
html_body = html_body.replace("`점점점◁`", "<span class='hangul'>점점점◁</span>")
html_body = html_body.replace("`▤▤▤▤`", "<span class='geom'>▤▤▤▤</span>")

css = """
@page {
    size: A4;
    margin: 24mm 20mm 24mm 20mm;
    @bottom-right {
        content: counter(page);
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 8.5pt;
        color: #718096;
    }
}

body {
    font-family: 'Georgia', 'Cambria', 'Times New Roman', serif;
    font-size: 10.5pt;
    line-height: 1.68;
    color: #1a202c;
    background-color: #ffffff;
    text-rendering: optimizeLegibility;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    color: #1a365d;
    font-weight: 700;
    line-height: 1.3;
}

h1 {
    font-size: 18pt;
    margin-top: 1.8em;
    margin-bottom: 0.5em;
    border-bottom: 2px solid #2b6cb0;
    padding-bottom: 5px;
    page-break-after: avoid;
}

/* Ensure each major article starts on a fresh page */
.article-title {
    page-break-before: always;
}

h2 {
    font-size: 13.5pt;
    color: #2c5282;
    margin-top: 1.4em;
    margin-bottom: 0.4em;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    color: #2b6cb0;
    margin-top: 1.2em;
    margin-bottom: 0.35em;
    page-break-after: avoid;
}

h4 {
    font-size: 10.5pt;
    color: #4a5568;
    margin-top: 1em;
    margin-bottom: 0.25em;
    page-break-after: avoid;
}

p {
    margin-top: 0.45em;
    margin-bottom: 0.75em;
    text-align: justify;
    text-justify: inter-word;
}

a {
    color: #2b6cb0;
    text-decoration: none;
}

code {
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
    background-color: #edf2f7;
    color: #c53030;
    padding: 2px 4px;
    border-radius: 3px;
    border: 1px solid #e2e8f0;
    word-break: break-word;
    white-space: pre-wrap;
}

pre {
    background-color: #f7fafc;
    border: 1px solid #cbd5e0;
    border-left: 4px solid #3182ce;
    padding: 10px 14px;
    border-radius: 4px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 8.5pt;
    line-height: 1.42;
    color: #2d3748;
    margin: 1em 0;
    page-break-inside: avoid;
    white-space: pre-wrap;
    word-wrap: break-word;
    word-break: break-word;
}

pre code {
    background-color: transparent;
    padding: 0;
    border: none;
    color: inherit;
    font-size: 8.5pt;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.2em 0;
    font-size: 9pt;
    page-break-inside: avoid;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

tr {
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #cbd5e0;
    padding: 7px 11px;
    text-align: left;
    vertical-align: top;
}

th {
    background-color: #ebf8ff;
    color: #2b6cb0;
    font-weight: 700;
    font-family: 'Segoe UI', system-ui, sans-serif;
}

tr:nth-child(even) {
    background-color: #f7fafc;
}

blockquote {
    border-left: 4px solid #4299e1;
    margin: 1em 0;
    padding: 6px 14px;
    background-color: #ebf8ff;
    color: #2d3748;
    font-style: italic;
    page-break-inside: avoid;
    border-radius: 0 4px 4px 0;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 1.8em 0;
}

ul, ol {
    margin: 0.5em 0 0.9em 1.6em;
    padding: 0;
}

li {
    margin-bottom: 0.35em;
}

.math-display {
    text-align: center;
    font-size: 11.5pt;
    font-family: 'Georgia', serif;
    font-style: italic;
    padding: 10px 0;
    margin: 1em 0;
    background-color: #f7fafc;
    border: 1px dashed #cbd5e0;
    border-radius: 4px;
    page-break-inside: avoid;
}

.hangul {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
    color: #6b46c1;
    font-weight: 600;
}

.geom {
    color: #2b6cb0;
    font-weight: 600;
}

.lead-box {
    background-color: #f7fafc;
    border-left: 4px solid #2b6cb0;
    padding: 12px 16px;
    margin-bottom: 1.5em;
    font-size: 10pt;
    color: #4a5568;
}
"""

full_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>The Ghost in the Context Window Trilogy</title>
    <style>
{css}
    </style>
</head>
<body>
{html_body}
</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(full_html)

print("HTML written to:", HTML_PATH)

# Run Chrome headless to generate PDF
cmd = [
    CHROME_PATH,
    "--headless=new",
    "--disable-gpu",
    "--no-pdf-header-footer",
    f"--print-to-pdf={PDF_PATH}",
    HTML_PATH
]

print("Executing Chrome headless print-to-pdf...")
res = subprocess.run(cmd, capture_output=True, timeout=30)
print("Chrome RC:", res.returncode)

if os.path.exists(PDF_PATH):
    size = os.path.getsize(PDF_PATH)
    print(f"SUCCESS: Generated PDF at {PDF_PATH} ({size} bytes, {size/1024:.1f} KB)")
else:
    print("ERROR: PDF was not generated. Stderr:", res.stderr.decode("utf-8", errors="replace"))

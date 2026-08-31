"""Convert a Scroll/Confluence HTML export into a single Markdown file (1:1 content transfer)."""
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString
from markdownify import MarkdownConverter

SRC = Path(r"C:\Users\pek1sgm\Downloads\08.01 - MongoDB data models-v148-20260828_112754\08.01---MongoDB-data-models.5288400828.html")
OUT = Path(r"c:\Users\pek1sgm\Desktop\simulab-doku\08.01 - MongoDB data models.md")

html = SRC.read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")

title = soup.find("meta", attrs={"name": "exp-page-title"})["content"]
content = soup.find("div", id="main-content")

# --- 0) Confluence wraps leading/trailing nbsp *inside* <strong>/<em>, which markdownify
#        then trims, swallowing the word-boundary space. Move that whitespace back outside.
for tag in content.find_all(["strong", "b", "em", "i"]):
    if not tag.contents:
        continue
    first = tag.contents[0]
    if isinstance(first, NavigableString):
        stripped = first.lstrip(" \xa0\t\n")
        if stripped != str(first):
            tag.insert_before(NavigableString(str(first)[: len(str(first)) - len(stripped)]))
            first.replace_with(NavigableString(stripped))
    if tag.contents:
        last = tag.contents[-1]
        if isinstance(last, NavigableString):
            stripped = last.rstrip(" \xa0\t\n")
            if stripped != str(last):
                tag.insert_after(NavigableString(str(last)[len(stripped):]))
                last.replace_with(NavigableString(stripped))

# --- 1) Pull out Confluence "scroll-code" blocks and replace them with placeholders,
#        so markdownify does not have to deal with their internal <div class="line"> structure.
#        The wrapper div's class depends on the code theme (e.g. "confluence content" or
#        "defaultnew content"), so match on the "line" divs directly instead.
code_blocks = []
for block in content.select("div.scroll-code"):
    language = block.get("data-language", "")
    code_title = block.get("data-title", "")
    lines = []
    for line_div in block.find_all("div", class_="line"):
        text = line_div.get_text()
        text = text.replace("\xa0", " ")
        lines.append(text)
    code_text = "\n".join(lines)
    fence = f"```{language}\n{code_text}\n```"
    if code_title:
        fence = f"*{code_title}*\n\n{fence}"
    placeholder = f"\n\nZZZCODEBLOCKZZZ{len(code_blocks)}ZZZ\n\n"
    code_blocks.append(fence)
    block.replace_with(NavigableString(placeholder))

# --- 2) Convert Confluence admonition macros (info/warning/note/tip) into blockquotes.
for macro in content.select("div.confluence-information-macro"):
    label = macro.get("aria-label", "Note")
    body = macro.select_one(".confluence-information-macro-body")
    blockquote = soup.new_tag("blockquote")
    label_p = soup.new_tag("p")
    strong = soup.new_tag("strong")
    strong.string = label
    label_p.append(strong)
    blockquote.append(label_p)
    if body:
        for child in list(body.children):
            blockquote.append(child)
    macro.replace_with(blockquote)

# --- 3) Convert "panel" boxes (colored info panels / ToC panel) into a bold header + content.
for panel in content.select("div.panel"):
    header = panel.select_one(".panelHeader")
    body = panel.select_one(".panelContent")
    wrapper = soup.new_tag("div")
    if header:
        header_p = soup.new_tag("p")
        strong = soup.new_tag("strong")
        strong.string = header.get_text(strip=True)
        header_p.append(strong)
        wrapper.append(header_p)
    if body:
        for child in list(body.children):
            wrapper.append(child)
    panel.replace_with(wrapper)

# --- 3b) The auto-generated Table of Content links to anchors in the original HTML file,
#         which do not exist in the Markdown output - keep the outline, drop the dead links.
for link in content.select("div.toc-macro a"):
    link.replace_with(NavigableString(link.get_text()))

# --- 4) Standalone <pre> (used for single monospace words in table cells) -> inline <code>.
for pre in content.find_all("pre"):
    code = soup.new_tag("code")
    code.string = pre.get_text()
    pre.replace_with(code)


class ConfluenceConverter(MarkdownConverter):
    pass


converter = ConfluenceConverter(
    heading_style="ATX",
    bullets="-",
    escape_asterisks=False,
    escape_underscores=False,
)
markdown = converter.convert_soup(content)

# --- 5) Restore code fences and clean up whitespace artifacts.
for i, fence in enumerate(code_blocks):
    markdown = markdown.replace(f"ZZZCODEBLOCKZZZ{i}ZZZ", fence)

markdown = markdown.replace("\xa0", " ")
markdown = re.sub(r"[ \t]+\n", "\n", markdown)
markdown = re.sub(r"\n{3,}", "\n\n", markdown)
markdown = markdown.strip() + "\n"

final = f"# {title}\n\n{markdown}"
OUT.write_text(final, encoding="utf-8")
print(f"Wrote {OUT} ({len(final)} chars, {len(code_blocks)} code blocks)")

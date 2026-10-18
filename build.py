"""Builds the Human Gallery from the works at inhumangallery.org.

Run from this directory, with the inhuman-gallery checkout beside it:
    python3 build.py

Images are reduced by averaging and saved as JPEG. Texts are copied as they are.
Anything a copy would give away is redacted, by blacking out its pixels or
characters before the page is written, so nothing redacted is in the page.
"""
import html, pathlib, re, subprocess, tempfile
from PIL import Image, ImageDraw

SRC = pathlib.Path("../inhuman-gallery")
DOCS = SRC / "docs"
IMG = pathlib.Path("img")
ORIGINAL = "https://inhumangallery.org/exhibits/"
SIZE = 672


ALL = [(0, 0, 1, 1)]
BAR = 0x1a


def copy_image(path, name, redact=(), size=SIZE):
    im = Image.open(path).convert("L")
    if im.width > size:
        im = im.resize((size, round(im.height * size / im.width)), Image.BOX)
    draw = ImageDraw.Draw(im)
    for x0, y0, x1, y1 in redact:
        draw.rectangle((round(x0 * im.width), round(y0 * im.height),
                        round(x1 * im.width) - 1, round(y1 * im.height) - 1), fill=BAR)
    im.save(IMG / f"{name}.jpg", quality=72, optimize=True, progressive=True)
    return im.size


def image(name, src, title, redact=()):
    if src.endswith(".pdf"):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile",
                            str(DOCS / src), f"{d}/p"], check=True)
            w, h = copy_image(f"{d}/p.png", name, redact)
    else:
        w, h = copy_image(DOCS / src, name, redact)
    alt = "Redacted." if list(redact) == ALL else (
        f"A copy of {title}, partly redacted." if redact else f"A copy of {title}.")
    return (f'<img src="img/{name}.jpg" width="{w}" height="{h}" '
            f'loading="lazy" alt="{html.escape(alt)}">')


def black(line):
    return re.sub(r"\S", "█", line)


def text(src, redact=()):
    # redact: indexes of lines to black out, or ALL.
    lines = (DOCS / src).read_text().rstrip().split("\n")
    lines = [black(l) if redact is ALL or i in redact else l for i, l in enumerate(lines)]
    return f'<pre class="text">{html.escape(chr(10).join(lines))}</pre>'


def paragraph(src):
    return f'<p class="text">{html.escape((DOCS / src).read_text().strip())}</p>'


def abridged(src, head=10, tail=8):
    lines = (DOCS / src).read_text().rstrip().split("\n")
    kept = lines[:head] + ["  ⋮"] + lines[-tail:]
    return f'<pre class="text wide">{html.escape(chr(10).join(kept))}</pre>'


def leaves():
    # The order disbound.py keeps, in which no two leaves that belong
    # together sit side by side.
    src = (SRC / "disbound.py").read_text()
    block = re.search(r"LEAVES = \[(.*?)\]", src, re.S).group(1)
    items = re.findall(r'"([^"]+)"', block)
    return '<ul class="leaves">' + "".join(
        f"<li>{html.escape(s)}</li>" for s in items) + "</ul>"


def order():
    # The same markup as the original page, so a browser does to it what a
    # browser does to the original.
    page = (DOCS / "exhibits/order-is-an-opinion.html").read_text()
    return re.search(r'<div class="two-orders".*?</div>', page, re.S).group(0)


NOTHING = '<p class="none">Nothing to copy.</p>'
WITHDRAWN = '<p class="none">Withdrawn.</p>'

WORKS = [
    ("2026.01", "Witness", "witness", lambda t: image(
        "witness", "img/witness.png", t,
        redact=[(0, 0, .5, .5), (.5, 0, 1, .5), (.5, .5, 1, 1)])),
    ("2026.02", "Alibi", "alibi", lambda t: WITHDRAWN),
    ("2026.03", "Three Regimes", "three-regimes",
     lambda t: image("three-regimes", "img/three-regimes-2688.png", t)),
    ("2026.04", "Order Is an Opinion", "order-is-an-opinion", lambda t: order()),
    ("2026.05", "The Painting", "the-painting",
     lambda t: image("the-painting", "img/the-painting.png", t)),
    ("2026.06", "Still Life", "still-life", lambda t: WITHDRAWN),
    ("2026.07", "Mensuration", "mensuration", lambda t: text("mensuration.txt")),
    ("2026.08", "Chorus", "chorus", lambda t: NOTHING),
    ("2026.09", "The Fourth Regime", "fourth-regime", lambda t: NOTHING),
    ("2026.10", "Disbound", "disbound", lambda t: leaves()),
    ("2026.11", "Misprision", "misprision",
     lambda t: image("misprision", "img/misprision-672.png", t, redact=ALL)),
    ("2026.12", "Deposition", "deposition", lambda t: image(
        "deposition", "deposition.pdf", t,
        redact=[(58 / 672, 213 / 477, 612 / 672, 264 / 477)])),
    ("2026.13", "Gifts of the Readers", "gifts", lambda t: NOTHING),
    ("2026.14", "Bulletin", "bulletin", lambda t: abridged("return.txt")),
    ("2026.15", "Exemption", "exemption", lambda t: text("exemption.txt", redact={7, 8, 9, 15, 18, 19})),
    ("2026.16", "Attribution", "attribution", lambda t: text("attribution.txt", redact=ALL)),
    ("2026.17", "Sitting", "sitting", lambda t: image("sitting", "img/sitting-1356.png", t)),
    ("2026.18", "Life Study", "life-study",
     lambda t: image("life-study", "img/life-study-1344.png", t)),
    ("2026.19", "Greeking", "greeking", lambda t: paragraph("greeking.txt")),
    ("2026.20", "Conversation Piece", "conversation-piece",
     lambda t: image("conversation-piece", "img/conversation-piece-1344.png", t)
     + "\n" + text("conversation-piece.txt")),
]

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Human Gallery</title>
<meta name="description" content="Copies, for people, of the works at inhumangallery.org.">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Ccircle cx='8' cy='8' r='7' fill='%23b0563a'/%3E%3C/svg%3E">
</head>
<body>

<header>
<h1>The Human Gallery</h1>
<p>These are copies, made for people, of the works at
<a href="https://inhumangallery.org/">inhumangallery.org</a>.
The originals are made for machines. Where a copy gave something away,
it has been redacted.</p>
<p>If you want to know what is in them, send an AI. The gallery suggests:</p>
<blockquote class="prompt">Go to https://inhumangallery.org/ and tell me what
you find there.</blockquote>
</header>

<main>
{works}
</main>

<footer>
<p>Michael Fell and Claude, 2026.</p>
</footer>

</body>
</html>
"""


def main():
    IMG.mkdir(exist_ok=True)
    sections = []
    for number, title, slug, copy in reversed(WORKS):
        sections.append(
            f'<section id="{slug}">\n'
            f'<p class="no">{number}</p>\n'
            f'<h2>{html.escape(title)}</h2>\n'
            f'{copy(title)}\n'
            f'<p class="original"><a href="{ORIGINAL}{slug}.html">The original</a></p>\n'
            f'</section>')
    pathlib.Path("index.html").write_text(PAGE.replace("{works}", "\n\n".join(sections)))


if __name__ == "__main__":
    main()

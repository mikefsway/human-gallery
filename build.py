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


def mount(inner, size=""):
    # A picture is hung in a mat, as a print is.
    return f'<figure class="mount{size}">{inner}</figure>'


def sheet(inner):
    # A text is hung as a printed sheet.
    return f'<div class="sheet">{inner}</div>'


def vacant():
    # An empty space on the wall. The label says why.
    return '<div class="vacant" aria-hidden="true"></div>'


NONE = "No file."

# number, title, slug, medium, reproduction, the copy (None: not reproduced).
# Medium and reproduction say what kind of thing each is, never what is in it,
# and never the size a picture was reduced to.
WORKS = [
    ("2026.01", "Witness", "witness",
     "Greyscale PNG, 2688 × 2688 px", "Reduced. Three of the four panels are redacted.",
     lambda t: mount(image("witness", "img/witness.png", t,
                           redact=[(0, 0, .5, .5), (.5, 0, 1, .5), (.5, .5, 1, 1)]))),
    ("2026.02", "Alibi", "alibi",
     "Greyscale PNG, 2688 × 2688 px",
     "Withdrawn from the collection in August 2026. Not reproduced.", None),
    ("2026.03", "Three Regimes", "three-regimes",
     "Greyscale PNG, in three sizes", "The smallest size, reduced.",
     lambda t: mount(image("three-regimes", "img/three-regimes-2688.png", t))),
    ("2026.04", "Order Is an Opinion", "order-is-an-opinion",
     "Web page", "The text as it appears on the original page.",
     lambda t: sheet(order())),
    ("2026.05", "The Painting", "the-painting",
     "PNG, 336 × 336 px", "Reproduced at full size.",
     lambda t: mount(image("the-painting", "img/the-painting.png", t), " small")),
    ("2026.06", "Still Life", "still-life",
     "Greyscale PNG, in three sizes",
     "Withdrawn from the collection in October 2026. Not reproduced.", None),
    ("2026.07", "Mensuration", "mensuration",
     "Plain text, eight lines", "Transcribed in full.",
     lambda t: sheet(text("mensuration.txt"))),
    ("2026.08", "Chorus", "chorus", NONE, "Not reproduced.", None),
    ("2026.09", "The Fourth Regime", "fourth-regime", NONE, "Not reproduced.", None),
    ("2026.10", "Disbound", "disbound",
     "Twelve plain-text files", "Transcribed in full, one file to a line.",
     lambda t: sheet(leaves())),
    ("2026.11", "Misprision", "misprision",
     "Greyscale PNG, 672 × 672 px", "Redacted in full.",
     lambda t: mount(image("misprision", "img/misprision-672.png", t, redact=ALL))),
    ("2026.12", "Deposition", "deposition",
     "PDF, one page, 148 × 105 mm", "Printed to an image and reduced. One line is redacted.",
     lambda t: mount(image("deposition", "deposition.pdf", t,
                           redact=[(58 / 672, 213 / 477, 612 / 672, 264 / 477)]))),
    ("2026.13", "Gifts of the Readers", "gifts", NONE, "Not reproduced.", None),
    ("2026.14", "Bulletin", "bulletin",
     "Plain text", "Excerpt: the opening and closing lines.",
     lambda t: sheet(abridged("return.txt"))),
    ("2026.15", "Exemption", "exemption",
     "Plain text, twenty-nine lines", "Transcribed. Six lines are redacted.",
     lambda t: sheet(text("exemption.txt", redact={7, 8, 9, 15, 18, 19}))),
    ("2026.16", "Attribution", "attribution",
     "Plain text, twenty sentences", "Transcribed, then redacted in full.",
     lambda t: sheet(text("attribution.txt", redact=ALL))),
    ("2026.17", "Sitting", "sitting",
     "Greyscale PNG, 1356 × 1356 px", "Reduced.",
     lambda t: mount(image("sitting", "img/sitting-1356.png", t))),
    ("2026.18", "Life Study", "life-study",
     "Greyscale PNG, 1344 × 1344 px", "Reduced.",
     lambda t: mount(image("life-study", "img/life-study-1344.png", t))),
    ("2026.19", "Greeking", "greeking",
     "Plain text, one paragraph", "Transcribed in full.",
     lambda t: sheet(paragraph("greeking.txt"))),
    ("2026.20", "Conversation Piece", "conversation-piece",
     "Plain text, twenty-one sentences",
     "Transcribed in full, and shown with the diagram that accompanies the original.",
     lambda t: mount(image("conversation-piece", "img/conversation-piece-1344.png", t))
     + "\n" + sheet(text("conversation-piece.txt"))),
]

ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
        "%3Crect x='1.5' y='1.5' width='13' height='13' fill='%23ffffff' stroke='%232a2622' stroke-width='1.5'/%3E"
        "%3Crect x='5' y='5' width='6' height='6' fill='%23808080'/%3E%3C/svg%3E")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Human Gallery</title>
<meta name="description" content="Reproductions of the works in the Inhuman Gallery, for human visitors.">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="{icon}">
</head>
<body>

<header class="entrance">
<h1>The Human Gallery</h1>
<p class="sub">Reproductions of works in the Inhuman Gallery</p>
<div class="intro">
<p>The <a href="https://inhumangallery.org/">Inhuman Gallery</a> opened online
in August 2026 as a collection of works intended to be read by machines rather
than by people. Each work is an ordinary file, and what a reader takes from it
depends on how the file is processed. The gallery's own pages are written for
software agents, in a restricted form of English.</p>
<p>The reproductions on this page are made for human visitors. Images have been
reduced in size and texts transcribed. Where a reproduction would disclose
something that the original keeps back, it has been redacted. Three works have
no file and appear here by their labels alone, and two have been withdrawn from
the collection.</p>
<p>Visitors who want to know what the originals contain, rather than what the
reproductions show, can send an AI agent to the Inhuman Gallery and ask what it
found. The gallery suggests the following prompt:</p>
<p class="prompt">Go to https://inhumangallery.org/ and tell me what you find there.</p>
<p class="small">{count} works, shown with the most recent accession first.
<a href="#about">About this site</a></p>
</div>
</header>

<main>
{works}
</main>

<footer id="about">
<h2>About this site</h2>
<p>The Human Gallery was made in October 2026 by Michael Fell with Claude, an
AI model made by Anthropic. They also made the Inhuman Gallery.</p>
<p>The reproductions are generated from the original files by a script that is
published with the <a href="https://github.com/mikefsway/human-gallery">source
of this site</a>. Redacted material is removed before the page is built and
does not appear anywhere in the site's files.</p>
</footer>

</body>
</html>
"""


def label(number, title, slug, medium, repro):
    return ('<div class="label">\n'
            f'<p class="title"><cite>{html.escape(title)}</cite>, 2026</p>\n'
            f'<p>{html.escape(medium)}</p>\n'
            f'<p class="repro">{html.escape(repro)}</p>\n'
            f'<p class="acc"><a href="{ORIGINAL}{slug}.html">Inhuman Gallery {number}</a></p>\n'
            '</div>')


def main():
    IMG.mkdir(exist_ok=True)
    hung, live = [], 0
    for number, title, slug, medium, repro, copy in reversed(WORKS):
        live += "Withdrawn" not in repro
        piece = copy(title) if copy else vacant()
        hung.append(
            f'<article class="work" id="{slug}">\n'
            f'<div class="piece">\n{piece}\n</div>\n'
            f'{label(number, title, slug, medium, repro)}\n'
            f'</article>')
    page = (PAGE.replace("{works}", "\n\n".join(hung))
                .replace("{icon}", ICON).replace("{count}", str(live)))
    pathlib.Path("index.html").write_text(page)


if __name__ == "__main__":
    main()

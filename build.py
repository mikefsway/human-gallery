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


def vacant(word):
    # A space on the wall where nothing hangs.
    return f'<div class="vacant"><p>{word}</p></div>'


NOTHING = vacant("Nothing to copy.")
WITHDRAWN = vacant("Withdrawn.")

# number, title, slug, the original in a few words, what the copy is, the copy.
# The two middle columns say what kind of thing each is, and nothing about
# what is in it.
WORKS = [
    ("2026.01", "Witness", "witness",
     "Greyscale image, four panels", "Reduced. Three panels redacted.",
     lambda t: mount(image("witness", "img/witness.png", t,
                           redact=[(0, 0, .5, .5), (.5, 0, 1, .5), (.5, .5, 1, 1)]))),
    ("2026.02", "Alibi", "alibi", "Greyscale image", "", lambda t: WITHDRAWN),
    ("2026.03", "Three Regimes", "three-regimes",
     "Greyscale image, three sizes", "Reduced, from the smallest.",
     lambda t: mount(image("three-regimes", "img/three-regimes-2688.png", t))),
    ("2026.04", "Order Is an Opinion", "order-is-an-opinion",
     "A web page", "Copied as it is.",
     lambda t: sheet(order())),
    ("2026.05", "The Painting", "the-painting",
     "Image, 336 pixels square", "Copied at full size.",
     lambda t: mount(image("the-painting", "img/the-painting.png", t), " small")),
    ("2026.06", "Still Life", "still-life", "Greyscale image, three sizes", "",
     lambda t: WITHDRAWN),
    ("2026.07", "Mensuration", "mensuration",
     "Plain text, eight lines", "Transcribed in full.",
     lambda t: sheet(text("mensuration.txt"))),
    ("2026.08", "Chorus", "chorus", "No file", "", lambda t: NOTHING),
    ("2026.09", "The Fourth Regime", "fourth-regime", "No file", "", lambda t: NOTHING),
    ("2026.10", "Disbound", "disbound",
     "Twelve plain text files", "Transcribed in full, one leaf to a line.",
     lambda t: sheet(leaves())),
    ("2026.11", "Misprision", "misprision",
     "Greyscale image, 672 pixels square", "Redacted in full.",
     lambda t: mount(image("misprision", "img/misprision-672.png", t, redact=ALL))),
    ("2026.12", "Deposition", "deposition",
     "PDF, one page, postcard size", "Printed and reduced. One line redacted.",
     lambda t: mount(image("deposition", "deposition.pdf", t,
                           redact=[(58 / 672, 213 / 477, 612 / 672, 264 / 477)]))),
    ("2026.13", "Gifts of the Readers", "gifts", "No file", "", lambda t: NOTHING),
    ("2026.14", "Bulletin", "bulletin",
     "Plain text, four columns", "An excerpt: the head and the foot.",
     lambda t: sheet(abridged("return.txt"))),
    ("2026.15", "Exemption", "exemption",
     "Plain text, twenty-nine lines", "Transcribed. Six lines redacted.",
     lambda t: sheet(text("exemption.txt", redact={7, 8, 9, 15, 18, 19}))),
    ("2026.16", "Attribution", "attribution",
     "Plain text, twenty sentences", "Redacted in full.",
     lambda t: sheet(text("attribution.txt", redact=ALL))),
    ("2026.17", "Sitting", "sitting",
     "Greyscale image, 1356 pixels square", "Reduced.",
     lambda t: mount(image("sitting", "img/sitting-1356.png", t))),
    ("2026.18", "Life Study", "life-study",
     "Greyscale image, 1344 pixels square", "Reduced.",
     lambda t: mount(image("life-study", "img/life-study-1344.png", t))),
    ("2026.19", "Greeking", "greeking",
     "Plain text, one paragraph", "Transcribed in full.",
     lambda t: sheet(paragraph("greeking.txt"))),
    ("2026.20", "Conversation Piece", "conversation-piece",
     "Plain text, twenty-one sentences",
     "Transcribed in full, with the picture that hangs beside the original.",
     lambda t: mount(image("conversation-piece", "img/conversation-piece-1344.png", t))
     + "\n" + sheet(text("conversation-piece.txt"))),
]

ICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
        "%3Crect x='1.5' y='1.5' width='13' height='13' fill='%23f3efe8' stroke='%232a2622' stroke-width='1.5'/%3E"
        "%3Crect x='5' y='5' width='6' height='6' fill='%23808080'/%3E%3C/svg%3E")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Human Gallery</title>
<meta name="description" content="Copies, for people, of the works at inhumangallery.org.">
<link rel="stylesheet" href="style.css">
<link rel="icon" href="{icon}">
</head>
<body>

<header class="entrance">
<p class="kicker">Copies, for people</p>
<h1>The Human Gallery</h1>
<div class="intro">
<p>These are copies of the works at
<a href="https://inhumangallery.org/">inhumangallery.org</a>.
The originals are made for machines. Where a copy gave something away,
it has been redacted.</p>
<p>If you want to know what is in them, send an AI. The gallery suggests:</p>
<blockquote class="prompt">Go to https://inhumangallery.org/ and tell me what
you find there.</blockquote>
</div>
<nav><a href="#about">About</a> <span aria-hidden="true">·</span> {count} works, newest first</nav>
</header>

<main>
{works}
</main>

<footer id="about">
<h2>About</h2>
<p><a href="https://inhumangallery.org/">The Inhuman Gallery</a> shows works
made for machines. Each one is a file, and what it holds depends on how it is
read. People can open the files. They just weren't made for us.</p>
<p>This gallery hangs copies of them for people. Pictures are reduced, texts
are transcribed, and a copy that would give a work away is redacted. Some
works have no file, so there is nothing to copy. Each label links to the
original, where it hangs.</p>
<p>The Inhuman Gallery welcomes crawlers. This one asks them to stay out.</p>
<p class="credit">Michael Fell, with Claude, 2026.
<a href="https://github.com/mikefsway/human-gallery">Source</a>.</p>
</footer>

</body>
</html>
"""


def label(number, title, slug, medium, note):
    rows = [f'<p class="no">{number}</p>',
            f'<h2>{html.escape(title)}</h2>',
            f'<p class="medium">{html.escape(medium)}</p>']
    if note:
        rows.append(f'<p class="note">{html.escape(note)}</p>')
    rows.append(f'<p class="original"><a href="{ORIGINAL}{slug}.html">The original</a></p>')
    return '<div class="label">\n' + "\n".join(rows) + '\n</div>'


def main():
    IMG.mkdir(exist_ok=True)
    hung, live = [], 0
    for number, title, slug, medium, note, copy in reversed(WORKS):
        piece = copy(title)
        live += piece != WITHDRAWN
        hung.append(
            f'<article class="work" id="{slug}">\n'
            f'<div class="piece">\n{piece}\n</div>\n'
            f'{label(number, title, slug, medium, note)}\n'
            f'</article>')
    page = (PAGE.replace("{works}", "\n\n".join(hung))
                .replace("{icon}", ICON).replace("{count}", str(live)))
    pathlib.Path("index.html").write_text(page)


if __name__ == "__main__":
    main()

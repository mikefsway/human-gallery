"""Builds the Human Gallery from the works at inhumangallery.org.

Run from this directory, with the inhuman-gallery checkout beside it:

    python3 build.py                  build index.html and img/
    python3 build.py --approve 2026.21  record that a reproduction was reviewed

The list of works comes from the Inhuman Gallery's catalogue (exhibits.json),
so an accession, a withdrawal or a removal there shows up here on the next
build, which a GitHub Action runs every hour.

A reproduction is shown only while its source is the one that was reviewed.
reviewed.json holds a digest of each reviewed source. A new work, or a work
whose source has changed, hangs as "Reproduction in preparation" until someone
checks the copy gives nothing away, adds or adjusts its row in WORKS, and runs
--approve. Each such work is printed as a PENDING line.

Images are reduced and saved as JPEG; texts are copied as they are. Redaction
blacks out pixels or characters before anything is written, so nothing
redacted is in the site's files.
"""
import hashlib, html, json, pathlib, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw

SRC = pathlib.Path("../inhuman-gallery")
DOCS = SRC / "docs"
IMG = pathlib.Path("img")
REVIEWED = pathlib.Path("reviewed.json")
CACHE = IMG / "sources.json"
ORIGINAL = "https://inhumangallery.org/"
SIZE = 672

ALL = [(0, 0, 1, 1)]
BAR = 0x1a


# ---- copies ----

def sha(data):
    return hashlib.sha256(data).hexdigest()


def copy_image(path, name, redact):
    im = Image.open(path).convert("L")
    if im.width > SIZE:
        im = im.resize((SIZE, round(im.height * SIZE / im.width)), Image.BOX)
    draw = ImageDraw.Draw(im)
    for x0, y0, x1, y1 in redact:
        draw.rectangle((round(x0 * im.width), round(y0 * im.height),
                        round(x1 * im.width) - 1, round(y1 * im.height) - 1), fill=BAR)
    im.save(IMG / f"{name}.jpg", quality=72, optimize=True, progressive=True)


def image(name, src, title, redact=()):
    # Regenerated only when the source or the redaction changes, so that a
    # rebuild on another machine does not rewrite every file.
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    key = sha((DOCS / src).read_bytes()) + repr(list(redact)) + str(SIZE)
    out = IMG / f"{name}.jpg"
    if cache.get(name) != key or not out.exists():
        if src.endswith(".pdf"):
            with tempfile.TemporaryDirectory() as d:
                subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile",
                                str(DOCS / src), f"{d}/p"], check=True)
                copy_image(f"{d}/p.png", name, redact)
        else:
            copy_image(DOCS / src, name, redact)
        cache[name] = key
        CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n")
    w, h = Image.open(out).size
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
    return f'<figure class="mount{size}">{inner}</figure>'


def sheet(inner):
    return f'<div class="sheet">{inner}</div>'


def vacant():
    return '<div class="vacant" aria-hidden="true"></div>'


def files(*paths):
    # The material a reproduction is made from, for the review digest.
    return lambda: b"".join((DOCS / p).read_bytes() for p in paths)


# ---- the works ----
#
# accession: (medium, reproduction, copy, material)
#
# Medium and reproduction say what kind of thing each work is, never what is
# in it, and never the size a picture was reduced to. copy is None for a work
# with no file. material returns the bytes the copy is made from; the review
# digest in reviewed.json is taken over them. Titles and links come from the
# catalogue.

NONE = "No file."

WORKS = {
    "2026.01": ("Greyscale PNG, 2688 × 2688 px",
                "Reduced. Three of the four panels are redacted.",
                lambda t: mount(image("witness", "img/witness.png", t,
                                      redact=[(0, 0, .5, .5), (.5, 0, 1, .5), (.5, .5, 1, 1)])),
                files("img/witness.png")),
    "2026.02": ("Greyscale PNG, 2688 × 2688 px", "", None, None),
    "2026.03": ("Greyscale PNG, in three sizes", "The smallest size, reduced.",
                lambda t: mount(image("three-regimes", "img/three-regimes-2688.png", t)),
                files("img/three-regimes-2688.png")),
    "2026.04": ("Web page", "The text as it appears on the original page.",
                lambda t: sheet(order()),
                lambda: order().encode()),
    "2026.05": ("PNG, 336 × 336 px", "Reproduced at full size.",
                lambda t: mount(image("the-painting", "img/the-painting.png", t), " small"),
                files("img/the-painting.png")),
    "2026.06": ("Greyscale PNG, in three sizes", "", None, None),
    "2026.07": ("Plain text, eight lines", "Transcribed in full.",
                lambda t: sheet(text("mensuration.txt")),
                files("mensuration.txt")),
    "2026.08": (NONE, "Not reproduced.", None, None),
    "2026.09": (NONE, "Not reproduced.", None, None),
    "2026.10": ("Twelve plain-text files", "Transcribed in full, one file to a line.",
                lambda t: sheet(leaves()),
                lambda: leaves().encode()),
    "2026.11": ("Greyscale PNG, 672 × 672 px", "Redacted in full.",
                lambda t: mount(image("misprision", "img/misprision-672.png", t, redact=ALL)),
                files("img/misprision-672.png")),
    "2026.12": ("PDF, one page, 148 × 105 mm",
                "Printed to an image and reduced. One line is redacted.",
                lambda t: mount(image("deposition", "deposition.pdf", t,
                                      redact=[(58 / 672, 213 / 477, 612 / 672, 264 / 477)])),
                files("deposition.pdf")),
    "2026.13": (NONE, "Not reproduced.", None, None),
    "2026.14": ("Plain text", "Excerpt: the opening and closing lines.",
                lambda t: sheet(abridged("return.txt")),
                files("return.txt")),
    "2026.15": ("Plain text, twenty-nine lines", "Transcribed. Six lines are redacted.",
                lambda t: sheet(text("exemption.txt", redact={7, 8, 9, 15, 18, 19})),
                files("exemption.txt")),
    "2026.16": ("Plain text, twenty sentences", "Transcribed, then redacted in full.",
                lambda t: sheet(text("attribution.txt", redact=ALL)),
                files("attribution.txt")),
    "2026.17": ("Greyscale PNG, 1356 × 1356 px", "Reduced.",
                lambda t: mount(image("sitting", "img/sitting-1356.png", t)),
                files("img/sitting-1356.png")),
    "2026.18": ("Greyscale PNG, 1344 × 1344 px", "Reduced.",
                lambda t: mount(image("life-study", "img/life-study-1344.png", t)),
                files("img/life-study-1344.png")),
    "2026.19": ("Plain text, one paragraph", "Transcribed in full.",
                lambda t: sheet(paragraph("greeking.txt")),
                files("greeking.txt")),
    "2026.20": ("Plain text, twenty-one sentences",
                "Transcribed in full, and shown with the diagram that accompanies the original.",
                lambda t: mount(image("conversation-piece", "img/conversation-piece-1344.png", t))
                + "\n" + sheet(text("conversation-piece.txt")),
                files("img/conversation-piece-1344.png", "conversation-piece.txt")),
}

PENDING = "Reproduction in preparation."

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
         "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def words(n, capital=False):
    w = WORDS[n] if n < len(WORDS) else str(n)
    return w[0].upper() + w[1:] if capital else w


def works_phrase(n, what):
    # "Three works have no file", "One work has no file"
    return f"{words(n, True)} {'work has' if n == 1 else 'works have'} {what}"


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
something that the original keeps back, it has been redacted. {absences}</p>
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


def label(number, title, link, medium, repro):
    year = number.split(".")[0]
    rows = [f'<p class="title"><cite>{html.escape(title)}</cite>, {year}</p>']
    if medium:
        rows.append(f'<p>{html.escape(medium)}</p>')
    rows.append(f'<p class="repro">{html.escape(repro)}</p>')
    rows.append(f'<p class="acc"><a href="{html.escape(link)}">'
                f'Inhuman Gallery {html.escape(number)}</a></p>')
    return '<div class="label">\n' + "\n".join(rows) + '\n</div>'


def catalogue():
    cat = json.loads((DOCS / "exhibits.json").read_text())
    live = {w["accession"]: w for w in cat["works"]}
    gone = {w["accession"]: w for w in cat.get("withdrawn", [])}
    return live, gone


def withdrawn_note(entry):
    m = re.search(r"withdrawn (\d{4})\.(\d{2})", entry.get("status", ""))
    when = f" in {MONTHS[int(m.group(2)) - 1]} {m.group(1)}" if m else ""
    return f"Withdrawn from the collection{when}. Not reproduced."


def approve(numbers):
    reviewed = json.loads(REVIEWED.read_text()) if REVIEWED.exists() else {}
    for n in numbers:
        material = WORKS[n][3]
        if material is None:
            sys.exit(f"{n} has no material to approve")
        reviewed[n] = sha(material())
        print(f"approved {n} {reviewed[n][:12]}")
    REVIEWED.write_text(json.dumps(reviewed, indent=1, sort_keys=True) + "\n")


def main():
    if sys.argv[1:2] == ["--approve"]:
        return approve(sys.argv[2:])

    IMG.mkdir(exist_ok=True)
    live, gone = catalogue()
    reviewed = json.loads(REVIEWED.read_text()) if REVIEWED.exists() else {}

    for n in sorted(set(WORKS) - set(live) - set(gone)):
        print(f"REMOVED {n}: no longer in the catalogue, so not shown")

    hung, pending, no_file = [], [], 0
    for n in sorted(set(live) | set(gone), reverse=True):
        entry = live.get(n) or gone[n]
        title = entry["title"]
        # Catalogue values go into the page, so only a plain exhibit path and
        # a plain accession number are let through.
        page = entry.get("page", "")
        if not re.fullmatch(r"exhibits/[a-z0-9-]+\.html", page):
            print(f"SKIPPED {n!r}: unexpected page {page!r}")
            continue
        if not re.fullmatch(r"\d{4}\.\d{2}", n):
            print(f"SKIPPED {n!r}: unexpected accession number")
            continue
        link = ORIGINAL + page
        medium, repro, copy, material = WORKS.get(n, ("", PENDING, None, None))

        if n in gone:
            piece, repro = vacant(), withdrawn_note(entry)
        elif n not in WORKS:
            piece, repro = vacant(), PENDING
            pending.append(f"{n} {title}: new in the catalogue, no row in WORKS")
        elif copy is None:
            piece = vacant()
            no_file += 1
            if entry.get("files"):
                repro = PENDING
                pending.append(f"{n} {title}: the catalogue now lists a file")
        elif reviewed.get(n) != sha(material()):
            piece, repro = vacant(), PENDING
            pending.append(f"{n} {title}: the source differs from the reviewed one")
        else:
            piece = copy(title)

        hung.append(
            f'<article class="work" id="{html.escape(pathlib.Path(link).stem)}">\n'
            f'<div class="piece">\n{piece}\n</div>\n'
            f'{label(n, title, link, medium, repro)}\n'
            f'</article>')

    # Say what is missing from the wall, and why.
    absences = []
    if no_file:
        absences.append(works_phrase(no_file, "no file and appear here by their labels alone"
                                     if no_file > 1 else "no file and appears here by its label alone"))
    if gone:
        absences.append(f"{words(len(gone))} {'has' if len(gone) == 1 else 'have'} been "
                        "withdrawn from the collection")
    sentence = ", and ".join(absences) + "." if absences else ""
    if sentence:
        sentence = sentence[0].upper() + sentence[1:]
    if pending:
        sentence += (" " + works_phrase(len(pending), "a reproduction in preparation") + ".")

    page = (PAGE.replace("{works}", "\n\n".join(hung))
                .replace("{icon}", ICON)
                .replace("{count}", str(len(live)))
                .replace("{absences}", sentence.strip()))
    pathlib.Path("index.html").write_text(page)

    # Leave no copy on disk that the page does not show.
    shown = set(re.findall(r'src="img/([^"]+)"', page))
    for f in IMG.glob("*.jpg"):
        if f.name not in shown:
            f.unlink()
            print(f"deleted img/{f.name}")
    if CACHE.exists():
        cache = {k: v for k, v in json.loads(CACHE.read_text()).items() if f"{k}.jpg" in shown}
        CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n")

    for p in pending:
        print("PENDING", p)


if __name__ == "__main__":
    main()

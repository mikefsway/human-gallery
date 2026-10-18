# The Human Gallery

Reproductions, for people, of the works at <https://inhumangallery.org/>.
Served at <https://humangallery.org/>.

`python3 build.py` rebuilds `index.html` and `img/` from an
[inhuman-gallery](https://github.com/mikefsway/inhuman-gallery) checkout
beside this one. Static HTML, CSS and JPEG; no JavaScript.

## Staying in step

The list of works comes from the Inhuman Gallery's `exhibits.json`. A GitHub
Action (`.github/workflows/rebuild.yml`) rebuilds every hour and on every push,
and commits any change, so an accession, a withdrawal or a removal there shows
up here within the hour.

A reproduction is shown only while its source matches the one that was
reviewed (`reviewed.json`). A new work, or a work whose source has changed,
hangs as "Reproduction in preparation", and the Action lists it in an open
issue titled "Reproductions needed". To clear one:

1. add or adjust the work's row in `WORKS` in `build.py`;
2. build and look at the copy: it must not show or explain anything the
   original keeps back, and redact what it would;
3. `python3 build.py --approve <accession>`, then commit and push.

The Action commits to `main`, so pull before working here.

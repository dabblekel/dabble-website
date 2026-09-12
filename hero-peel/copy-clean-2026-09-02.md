# copy-clean — 2026-09-02

Removed explanatory copy from the Peel hero. All edits are in the **source**
(`source/dabble-hero-source.zip`); `dabble-hero-peel.html` was rebuilt from it.

## Removed

| # | string | file:line | how |
|---|---|---|---|
| 1 | `the corner lifts &middot; click or drag it open` | `tpl2/H-peel.txt:2` | `HINT::` value emptied. The line itself must stay — `buildH.py` reads it with `.group(1)` and throws if absent. |
| 2 | `click anywhere dark to go back` | `tpl2/H-peel.txt:135` | `#back` text emptied, node kept — the script looks it up and toggles `.back.on`. |
| 3 | `Read &nbsp;&rarr;` | `tpl2/H-peel.txt:275` | `<span class="go">` removed from `cap.innerHTML`. |
| 3b | `.cap .go { … }` | `tpl2/H-peel.txt:78` | Rule deleted; orphaned once the span went. |
| 5 | `Dabble<br>the other side` | `tpl2/H-peel.txt:128` | `#credit` text emptied, node kept — the script looks it up. |
| 6 | `<title>Dabble — Bloom · __TITLE__</title>` | `tpl2/base.html:6` | Trimmed to `<title>Dabble</title>`. `__TITLE__` is gone, so `buildH.py`'s replace for it is now a no-op. |

## Kept

- **4** — `title="lift"` on `#dog`, the corner triangle's browser tooltip.
- `alt="Dabble"` on the logo — accessibility text, never in the delete set.
- `Close` on the story-card button — functional control label.

## Not touched

The twelve placeholder case studies in `tpl2/stories.js`, the five nav labels,
the `What's your what if?` headline, and prototypes A–J.

## To reverse

Restore any row above at the file:line given, then `python3 buildH.py` from the
source folder and copy `build4/peel-v2.html` over `dabble-hero-peel.html`.

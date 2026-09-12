# Dabble hero — handoff brief

Paste this into a new chat to pick up where we left off.

**Last session, in one paragraph.** A focused polish pass on the **About** page's three
interactive scenes and their mobile behaviour. Scene 3's frozen boulder **triangle** now
holds together — it is treated as an immovable wall so the rolling ball rebounds and eases
to a gentle stop without the stack collapsing or even nudging. The About text was
**separated from the art on desktop too** (it used to overlay), with two per-scene
exceptions: Scene 2's copy splits into **two columns** on desktop, and Scene 3 (little
copy) keeps its text **overlaid near the art**. Draggable objects can now be pulled **up
through the text band**, Scene 1's boulder **rolls off the right edge** instead of bouncing,
Scene 2's boulder **sits on the hill line** (terrain foot reshaped), and Scene 1's boat
moved **left** so its "move me!" hint clears a phone screen. Two mobile bugs fixed: the page
no longer **loads zoomed / scrolls sideways** (scene art was bleeding past the screen edge —
now clipped horizontally), and **dragging an object no longer scrolls the page** (`touch-action`
is silently ignored on inner SVG, so a global `touchstart` gate now blocks the scroll only
when a draggable object is pressed). The `build.py` "PermissionError" seen mid-session was a
**transient device-bridge disconnect**, not a real fault — the full build runs clean. Full
detail in the next section; the section under it is the prior session, and the engine
sections further down still hold.


---

## Latest session — About scenes: physics, per-scene layout, mobile & touch

This section supersedes the "About layout is responsive — separated on mobile only" note
and the `touch-action` half of "About drag-vs-scroll" in the prior-session section below.

All About work is in `tpl2/about-page.html` inside `source/dabble-hero-source.zip`;
`build.py` injects only the corner-lift nav (the `__LIFT_*__` placeholders) and otherwise
writes `about.html` verbatim. So the scene CSS/JS in the built `about.html` is a
byte-for-byte copy of the template — handy for a quick **direct patch** of `about.html`
when a full rebuild is slow — but the **zip is the source of truth**; fold the same change
into it and rebuild so they stay in sync.

### Scene 3 — the frozen triangle holds
- The frozen stack (5 boulders + a boat crowning the apex) is now a **true immovable wall**.
  In `collidePair`, a sleeping body no longer wakes on impact; the mover (ball or boat) is
  resolved against it as an immovable surface and rebounds, and the pile does not move. This
  replaced the old `wake(wall,150)` path, which woke the struck rock and **cascaded** — with
  the near-frictionless ground the wedged triangle then spread into a flat row.
- The rolling ball's rebound was softened (`restB` 0.52 → **0.24**) so it taps the stack and
  **eases to a gradual stop** (~20px back) instead of rolling all the way back across.
- Net: the ball rolls in, hits, rebounds gently; the triangle stays intact and does not shift.

### About layout — separated at all widths, with two desktop exceptions
Supersedes the old "separated on mobile only." The **base** rules now lay every scene out
**stacked** — a text band above, the interactive `.stage` below (`.copy{position:static}`,
no blur panels) — at all widths. Desktop-only overrides live in a **`@media(min-width:681px)`**
block:
- **Scene 2**: `#s2 .copy{display:flex}` splits the copy into **two columns** (the "At Dabble,
  we read the grain…" block, then the "This leads us to build / Products / Companies" block).
- **Scene 3**: little copy, so it is **overlaid near the art** again (`#s3{min-height:100vh}`,
  `#s3 .stage{position:absolute;inset:0}`, `#s3 .copy{position:absolute; left/top}`,
  `pointer-events:none` with the mail link re-enabled) — keeps the text next to the triangle
  rather than floating far above it.

Mobile (`@media(max-width:680px)`) keeps the plain stacked layout for every scene. The two
breakpoints don't overlap (≤680 mobile / ≥681 desktop).

### Drag range + horizontal clipping (the "no sideways scroll" fix)
- `.stage` is **`overflow-x:clip; overflow-y:visible`**. `overflow-y:visible` lets a dragged
  object travel **up out of the stage and through the text band** above it. `overflow-x:clip`
  stops scene art (a rolled-off boulder, the boat's "move me!" hint, stray SVG) from bleeding
  past the screen edge — which was making the page ~26px too wide on mobile and forcing the
  browser to zoom-to-fit / scroll sideways. Use **`clip`, not `hidden`**: `overflow-x:hidden`
  with `overflow-y:visible` forces `overflow-y` to compute to `auto`, which would re-clip the
  drag-up.

### Touch: drag an object, or scroll the page — never both
Supersedes the `touch-action` claim below. **`touch-action` has no effect on inner SVG
elements** (`<g>`, `<circle>`), so `svg.art .grab{touch-action:none}` never actually stopped
the page scrolling while you dragged — that was the "drag interferes with scroll" bug. The
fix is a single global, **non-passive** `touchstart` listener that hit-tests with
`document.elementFromPoint(x,y).closest('.grab')` and calls `preventDefault()` **only** when
the press lands on a draggable object. Result: press an object → it drags and the page holds
still; press anywhere else → the page scrolls. Pointerdown still fires, so the existing
per-object (scenes 1/2) and stage-level (scene 3) drag handlers are untouched, and desktop
mouse is unaffected (`touchstart` never fires there).

### Scene 1 — boulder rolls off, boat moved left
- The right-edge **bounce clamp** (`if(rockX>W-8){…}`) was removed. A boulder pushed up the
  right hill now **rolls off the right edge and off-screen** (`rockState="gone"` past `W+40`);
  it still **sinks** only if it rolls into water (`sy>waterY`), and the left wall still holds.
- `boatHome.x` is now **responsive**: `W*(W<=680?0.68:0.80)` — the boat sits at 0.68×width on
  phones so its "move me!" hint (which sits ~100px to its right) clears the screen, and stays
  at 0.80×width on desktop.

### Scene 2 — boulder sits on the hill line
- The boulder rested on the terrain shelf, which ends ~3px above the flat waterline, so it
  read as floating over the water. Fixed by **reshaping the hill foot's control points** so
  the terrain descends **under** the boulder to the water's edge (CP foot now
  `…[0.50,0.61],[0.60,0.64],[0.74,0.70]…`) and **extending how far the hill line is drawn**
  (the draw loop now runs past `restX+34` and a few px below water before it stops). The
  boulder rests on `surfY` and lands exactly on that line. (An earlier attempt that instead
  dropped the boulder onto the waterline was reverted — it left the hill line above the
  boulder, still reading as "on the water.")

### Build / workflow notes
- **The build runs.** The `PermissionError: Operation not permitted` on a content JPEG that
  appeared mid-session was the device **bridge dropping the mounted folder mid-read** during
  the long image pass — not a real permission problem (the file reads fine and `build.py`
  completes, exit 0). If a build errors on a random content image over a flaky connection,
  just retry.
- Remaining build **notes** are cosmetic: missing team bios, `team/intro.txt` empty, and a
  few stale `assets/004-pumbit/*` / `assets/011-…` files the build can't delete over the
  bridge (deletes are blocked on the mounted folder).

---

## Prior session — mobile/touch pass, About page, galleries

This section supersedes older notes where they conflict (most importantly the corner
affordance — see below). Where it conflicts with the *Latest session* above (About layout,
`touch-action`), the Latest section wins.

### About page (new sub-page)

- Files: output `about.html`; template `tpl2/about-page.html` (in the engine zip). It is
  registered in the nav — `PAGE_URLS`/`NAV_PAGES` in `build.py` and the hero's own
  `PAGE_URLS` in `H-peel.txt` both list **About → about.html** — and carries the corner
  lift via the `__LIFT_STYLE__ / __LIFT_MARKUP__ / __LIFT_SCRIPT__` placeholders like the
  other sub-pages.
- Three scenes (`#s1 #s2 #s3`). Each `.scene` holds a `.copy` text block and a `.stage`;
  the stage contains `<canvas class="ascii">` (ASCII water/wind texture, `pointer-events:none`),
  `<svg class="art">` (the draggable boulder + boat, interactive), and the "move me!" hints.
- Hand-built 2D physics: Catmull-Rom terrain, `surfY(x)`/`slopeAt(x)`, impulse-based circle
  collisions, gravity / restitution / friction, sleeping bodies. Scene 1 is a rolling
  boulder + a boat that lands/floats/sinks; Scene 2 similar with wind; Scene 3 is a
  sandbox — a frozen boulder **triangle** with the boat crowning the apex, then a boulder
  rolls in and bumps it. All objects are draggable; a **secret, desktop-only** drag on the
  ground line raises hills.
- Physics sizes to the **`.stage`** element (`W=stage.clientWidth;H=stage.clientHeight`),
  and pointer coordinates are taken relative to the stage. The driver observes each
  `.stage` with an IntersectionObserver to start / tick that scene.

### About layout is responsive — separated on mobile only  *(SUPERSEDED — see Latest session; About is now separated at all widths, with desktop exceptions for scenes 2 and 3)*

- **Desktop (>680px):** unchanged original look — the text is **overlaid** on the art
  (`.copy{position:absolute}` over a full-viewport `.stage{position:absolute;inset:0}`,
  `.scene{min-height:100vh}`), on the soft translucent blur panels.
- **Mobile (≤680px):** the text lifts **out** into its own band **above** the stage
  (`.copy{position:static}`, plain on the cream; `.stage{position:relative;height:clamp(...)}`).
  This is toggled entirely inside the `@media(max-width:680px)` block — leave the desktop
  rules alone when editing.

### About drag-vs-scroll and corner menu  *(the `touch-action` mechanism below is SUPERSEDED — see Latest session; `touch-action:none` is ignored on inner SVG, so a global `touchstart` gate does this now)*

- Drag vs scroll is done with `touch-action`: `svg.art .grab{touch-action:none}` (touch an
  object → drag it) and `.stage{touch-action:pan-y}` (touch empty stage → scroll the page).
  Scenes 1/2 attach listeners to the rock/boat groups; Scene 3 listens on the stage and
  hit-tests bodies. Scene 3's secret ground-line drag is gated to `ev.pointerType!=='touch'`
  (on touch a vertical drag there is a scroll).
- The About page opts **out of the peel drag entirely**: it sets
  `window.dabbleLiftNoDrag=true` before the lift script, and `lift.txt` reads
  `const NODRAG=!!window.dabbleLiftNoDrag`. When set, a drag never starts a peel — the info
  mark is the only opener (tap to open, tap off the open paper to close). Every other page
  keeps drag-to-peel. (The flag deliberately avoids the `__X__` shape so `build.py`'s
  unfilled-placeholder check does not flag it.)

### Corner menu + info-icon hitbox (home hero AND every sub-page)

- **On touch, only a tap on the info mark opens the menu.** The generous corner band
  (`nearCorner` ≤ 340) opening it is now **mouse-only**; a corner *drag* still peels
  (except on About). Implemented in both `H-peel.txt` (hero) and `lift.txt` (sub-pages)
  with a `lastPT` pointer-type tracker, an `onDog(x,y)` hitbox (the dog/info rect + 12px
  pad), and a dedicated touch branch in `pointerup`.
  **This reverses the old handoff line that "the mark is a sign, not the target": on touch
  the mark now IS the target.** Mouse behaviour is unchanged.
- Hover "what if" captions are suppressed on touch (`lastPT==='touch'` /
  `matchMedia('(hover:none)')`); a tap directly on a hero picture opens its card; a ~450ms
  ghost-click guard (`cardTapGuard`) stops the phantom click after a tap from immediately
  closing the card.

### Corner menu rests past the logo on tall screens

- `OPEN()` in **both** `H-peel.txt` and `lift.txt`: on portrait screens
  (`innerHeight>innerWidth`) the peel now rests just **past** the mark (`cMax + pad`, capped
  at `MAXD()*0.9`) so the crease clears the logo and the logo sits cleanly on the cream
  (flips to black). Landscape / desktop is unchanged (still rests short of the mark).

### Bottom scroll room so the fixed logo never overlaps content (phones)

- Team **profile card** (`tpl2/team-page.html`): added `padding-bottom` (~150–210px mobile,
  ~96–132px desktop) so a long bio scrolls clear of the logo.
- Team / Stories / Dabblers **grids**: added `.inner{padding-bottom:clamp(150px,22vh,200px)}`
  in the narrow-screen media query (team `@media(max-width:620px)`, gallery
  `@media(max-width:560px)`) so the last row / card clears the logo.

### Home-page "what if" cards

- The Stories/Dabblers **carousel was ported to the hero cards** (`.caro*` CSS,
  `buildCaro`/`caroGo`, `#cCaro`, arrow-key nav) — supporting images scroll in a carousel.
- Card copy now runs through `escH` / `linkifyH` / `parasH` (mirrors the gallery
  `esc`/`linkify`/`paras`): `above`/`below` split on blank lines into paragraphs and
  `http(s)` URLs become links (e.g. the "when is now?" description link). `.card .body a`
  gets a subtle ink underline.

### Galleries (Stories / Dabblers)

- Built from `tpl2/gallery-page.html`; `stories.html` and `dabblers.html` now exist and are
  in the nav. Masonry `.grid` (column-count 3 / 2 / 1 by width). They already carried
  `esc`/`linkify`/`paras` and the carousel; this session added the phone grid bottom-padding.

### Build fixes

- **A `?` in a slug hid its image.** `012-when is now?`'s folder name contains `?`, a URL
  query delimiter, so the browser dropped the path. Fixed by URL-encoding **every** asset
  path in `build.py` with `urllib.parse.quote` (main src, carousel dir, gallery img,
  supporting) — which also handles spaces. Don't rename folders to dodge this; the encoding
  is the fix.
- **`team.csv` re-encoded to UTF-8.** Mac Roman smart quotes / em-dash (`0xd5…`) crashed
  `build.py` with a `UnicodeDecodeError`; it was re-saved as UTF-8 (backup `team.csv.bak-enc-*`).

### Working on the engine from a cloud session (how this was done)

- Unzip `source/dabble-hero-source.zip` to a temp dir, edit `tpl2/*`, **re-zip from the
  extraction root** (`(cd /tmp/engN && zip -q -r -X out.zip .)`), swap the zip back, run
  `python3 build.py`. `rm` on the mounted folder is blocked, so scratch goes to a temp dir
  or `_to_delete/`.
- Verification is Playwright (headless Chromium): touch is emulated with a context
  `{hasTouch:true,isMobile:true}`. Internal state like `open`/`d` is **not** global, so
  menu-open is read from `#paper`'s transform and card-open from
  `#ovl.classList.contains('on')`. Staging a few `assets/<slug>/main.jpg` files lets the
  hero's picture nodes render for hit-testing.

---

## What this is

I'm building the website for my design collective, **Dabble**. The landing page is meant
to be fully experiential and immersive — no conventional header, the page itself is the
interaction. We have one prototype in active development plus sixteen earlier studies.

**The live prototype:** `~/Desktop/dabble website/hero-peel/dabble-hero-peel.html`

**The content:** `~/Desktop/dabble website/content/` — one folder per image card. This is
where all real content lives and the only place it should be edited. See *Content
workflow* below, and `content/README.txt` — which also carries the **TO BUILD** list, the
canonical record of what is still outstanding.

**The build:** `cd ~/Desktop/dabble\ website/hero-peel && python3 build.py`. The shipped
HTML is *generated* from `content/` — never hand-edit it, the next build overwrites it.

**The engine:** `hero-peel/source/dabble-hero-source.zip` holds the rendering engine
(`tpl2/base.html`, `tpl2/H-peel.txt`, `buildH.py`). `build.py` extracts it to a temp
folder, injects the generated content and runs its `buildH.py`; the archive itself is
never modified by a build. Change the *engine* only for behaviour and styling — unzip,
edit, re-zip, and confirm it still rebuilds. Read `README-source.md` inside it first.

---

## How we got here

1. **Hero, five options.** Full-splash, "What's your what if?" in white centred text,
   images from my folder appearing one by one and flooding the page, always in their
   original aspect ratios with no distortion. → `hero-options/`
2. **I chose option 5, "Bloom"** — a slow spiral drift of images in 3D.
3. **Navigation, ten studies** built on Bloom, for the pages *Stories, Dabblers, Our Team,
   About, Contact*.
4. **I chose H, "Peel,"** and everything since has been refining it.

The built prototypes have since been cleared out. All ten nav studies (A–J) still exist as
source fragments in `tpl2/` inside the engine archive and can be rebuilt. The five hero
studies were only ever built files and are archived at
`~/Desktop/dabble website/archive/hero-options-2026-09-02.zip`.

---

## What Peel does now

- The bloom drifts continuously. Scroll changes its speed; hold the pointer down to dive in.
- **Bottom-right corner peels up** like a page corner. Drag it, or just click it. It stops
  short of the logo on purpose. Click anywhere outside, or press Esc, to lay it back down.
  At rest the corner carries a small **info mark**, `clamp(26px,2.6vw,36px)`, set in from
  both edges, with no glow and no animation. It replaced a plain white triangle that filled
  the corner. The drawing comes from `hero-peel/Info Icon_white.svg` and
  `Info Icon_black.svg` — white on the hero's dark bloom, black on a cream sub-page — so
  the shape is edited in Illustrator, not in CSS. Note the mark is a **sign, not the
  target**: the patch that opens the peel is still the whole corner band
  (`nearCorner` ≤ 340 diagonal px, `cornerCore` ≤ 170 where the peel beats a picture to
  the press), so it stays easy to grab at any size. **(Updated this session: on **touch** only the info mark opens the menu, and a corner *drag* peels; the band-opens-anywhere behaviour is now mouse-only. See *What changed this session*.)**
- **Underneath is a sunrise**: radial, asymmetric, matched to a real sunrise photo I gave
  it — dark blue at the far edge through white to a concentrated orange at the fold, with
  a thin bright limb line on the horizon, tapered at both ends. The five page links live
  on the dark side.
- **Hover a picture** → it darkens slightly, glows, stops moving while the rest keep
  swirling ("picking up an image to inspect it"), comes to the front, and lifts *toward the
  centre* so the caption stays on screen. A "What if …?" question plus a smaller title
  appear over it.
- **Click it** → an overlaid card with a case study: the main image, a subtitle, a title,
  copy, **any number of supporting images**, more copy, and a caption. Each supporting
  image runs the full width of the card at its own proportions — nothing is cropped — with
  its own caption underneath. Scroll controls the card, not the bloom. Esc or click the
  backdrop to close.
- **The logo** sits bottom-left — the stacked mark, not the horizontal one — and flips
  white→black if the paper or a bright sky ever reaches it.

Type is **Roboto Mono** throughout. The headline is Roboto Mono **700** at
`clamp(2.2rem,7vw,7rem)`, `letter-spacing:-.045em`.

**The headline is kerned by hand.** Roboto Mono is monospaced — every glyph gets the same
advance width, so the apostrophe sits alone in a cell as wide as a W while `w` and `h`
nearly fill theirs. The font carries no kern pairs, `font-kerning` does nothing, and
`letter-spacing` moves every pair at once. So `tpl2/base.html` wraps each headline
character in a span and nudges named pairs from a `KERN` map:

    "t’": -0.16   "’s": -0.16   "Wh": 0.055   "wh": 0.055   "ha": 0.020

Values are em; negative closes a pair, positive opens it, and case matters. Edit the
numbers in that map and rebuild — nothing else needs changing. The `.title h1 span`
rule sets `white-space:pre`; without it the spaces between words collapse.

**There is no explanatory copy on screen.** The hints, the tooltip text, the "Dabble / the
other side" credit and the "Read →" affordance were all removed deliberately — see
`copy-clean-2026-09-02.md`. Only `title="lift"` on the corner survives — and that one is
now stale, since the corner is an info mark rather than a page corner; decide whether it
should read differently or go. Don't reintroduce interface narration; if a new element
seems to need instructions, that's a signal about the element.

---

## Decisions that are locked in — please don't undo these

- **Original aspect ratios, no distortion.** This has been true since the first brief.
- **The stacked logo** (`white`/`black`), never the horizontal one.
- Peel stops short of the logo; the sun sits low, centre buried **28%** under the horizon.
- Lift motion is **calm and straight** — no "ducking and weaving" lateral-then-up path.
  This was fixed by analytically cancelling the outward drift that perspective
  magnification causes, plus a one-shot inward pull target.
- **Caption type is sized from each picture's short edge**, clamped 17–30px, so wide
  images don't shout. Sizing on width made landscape captions roughly double.
- Only the hovered picture stops; the rest keep drifting.

---

## Technical notes worth carrying forward

**The engine.** `tpl2/base.html` holds a shared `HERO` state object; each nav prototype is
a fragment that reads and nudges it. 30 pictures on desktop, 18 on mobile, laid out on a
golden-angle spiral, animated with transforms only. Perspective is 1400px; a picked-up
picture lifts 300px forward.

**Motion is time-based, not frame-based.** `HERO.dt` and `HERO.ease(k)` normalise every
lerp to real time. Everything new must use them — a raw `x += (target-x)*0.1` will run at
a different speed on a 120Hz display and lurch whenever frames drop. This was the single
biggest fix for the drift feeling choppy.

**Paint cost is the thing to watch.** Two changes roughly halved idle frame time:
the drop shadow under each picture went from a 60px blur to 26px (it was being re-blurred
every frame as pictures move in depth), and the "near" depth cue went from a
`brightness/saturate` filter to a slight opacity veil on far pictures, with hysteresis on
the threshold so nothing flickers. Avoid reintroducing per-element `filter` or large blurs
on anything that moves.

**Hit testing is manual.** `elementFromPoint` is unreliable inside a `preserve-3d`
rendering context — it left a 419-point dead zone in the middle of the screen. `hitAt(x,y)`
walks the nodes and picks the frontmost by z. Any test script must use it too.

**The bloom cross-fades behind the sky, never in front of it.** Returning home used to look
like the page reloading. Two overlapping fades caused it:

- The sky fades out over `q 0.92 -> 0.42` (`sun`), and the original bloom curve (`1-q*2.2`)
  faded the pictures IN over `q 0.45 -> 0`. The sun was gone by 0.42 with the bloom still at
  8%, so for about half a second neither was on screen: it went black, then the images faded
  up over ~1.4s.
- Narrowing the bloom's fade was not enough on its own. If it finishes any later than the
  sky starts thinning, the night gradient sits over a half-drawn bloom and dims it — which
  still reads as loading.

So the bloom's fade now runs `q 0.95 -> 0.75`, finishing while the sky is still near-solid.
The sky then lifts away over a bloom that has been fully painted the whole time, and closing
is a pure reveal. Fade completes ~66ms after the click, against ~1518ms before.

Measured with the bloom forced opaque: paper + sky occlude it completely for `q >= 0.70`,
and below `q ≈ 0.48` pictures ghost through the night side. **Keep the whole fade window
above 0.70.** If the sky's size or reach (`SKYSCALE`) changes, re-measure that threshold.

**The peel does not slow the swirl.** It drifts at one speed throughout and is already in
motion when the page uncovers it; only an open story card stills it. A stop-and-ease-back-in
was tried — swirl held while lifted, ramping in over ~3s once flat — and removed: with the
refresh fixed, the pause was the thing you noticed. `HERO.freeze` still holds the field while
it is *hidden*, so it returns exactly where it was left, but that stop is never seen and
there is no ramp on either side.

**Nothing eases while it is off screen.** Returning home from the menu used to land the
bloom in visibly new positions — a median jump of ~90px and up to ~300px. Two causes, both
worth remembering:

- `HERO.slow` only *decays* the spiral's speed, so it kept creeping while hidden.
  `HERO.freeze` (in `base.html`) now stops `rot` dead, and `H-peel` sets it from `worldOn`.
- The world hides and returns at the same peel position, but `n.lift` is an eased value, and
  an eased value lags in whichever direction it is travelling. It reached the hide frame
  short of its target and the show frame still short coming back — ~180px apart at the same
  `q`. `lift` drives the perspective compensation, so every picture returned displaced.
  Anything eased is now snapped straight to target while `worldOn` is false.

The general rule: if a value is eased for the look of it, snap it when nobody can see it,
or it will be somewhere else when the view comes back. Measured after: median 3px, max 10px.

Hover is also suppressed until the page is flat (`d>0` in the pick-up guard). `hitAt()`
measures bounding boxes and ignores visibility, so it would otherwise pick up and pull in
pictures hidden behind the paper while it lays back down.

**The sky never repaints.** It's built once on load and resize, then moved by transform
only. Rebuilding those gradients per frame cost 442ms/frame. Similarly, animating `left`
or `width` on the hairlines caused flashing rectangles — fixed width plus transform, and a
raised-cosine mask instead of a blur.

**Measuring.** `final.js` is the smoke test — run it after every change. `perf.js`,
`drift5.js` and `ratetest.js` cover peel drag, idle drift and frame-rate independence.
Sandbox numbers are software-rasterised and much worse than a real machine; only ratios
between runs are meaningful.

---

## Content workflow

Everything on the site is generated from `content/`. One folder per image card:

    content/
      001-light/
        entry.md          title, subtitle, tags, credits, caption, body copy
        main/             exactly ONE image - floats in the swirl, heads the card
        supporting/       any number (or none) - on the card only, never the swirl
                          a .txt of the same name as an image is its caption
      002-flight/
      _TEMPLATE/          copy this to start a new entry; folders starting with _ are skipped
      README.txt          the editing guide, and the TO BUILD list

Two files in `hero-peel/` are artwork rather than output and must stay put:
`Info Icon_white.svg` and `Info Icon_black.svg`, the corner mark. The build reads them
directly and stops with a clear error if either is missing. Illustrator exports an opaque
artboard rectangle behind the drawing; the build drops any `<rect>` the size of the
viewBox, so the files can be re-exported without anyone having to remember to delete it.

**Adding an entry:** copy `_TEMPLATE/`, name it `NNN-short-name`, drop in the images, fill
in `entry.md`, run `python3 build.py`. It joins the swirl and its galleries automatically.

**Captions on supporting images** are sidecar files, not front matter: `01-workshop.jpg`
is captioned by `01-workshop.txt` beside it. The front-matter parser is a deliberately
flat key/value reader with no nesting, and a per-file caption is the one thing that wants
a map — keeping it beside the image avoids growing a schema, survives reordering, and
means a folder still describes itself. The build lists images with no caption yet.
Nothing refers to images by filename, so **replacing a stock image is just swapping the
file in `main/`**.

`entry.md` front matter:

| field | what it does |
|---|---|
| `title` | Heading on the card. |
| `subtitle` | Small line above the title. |
| `story` | `yes` → appears in the **Stories** gallery. |
| `dabbler` | `yes` → appears in the **Dabblers** gallery. |
| `credits` | Collective members, one `  - Name` per line → mini-mentions on the Our Team page. |
| `caption` | Small line at the bottom of the card, under a rule. |

`story` and `dabbler` are independent — both `yes` puts a card in both galleries, both `no`
leaves it floating in the swirl but in neither, and the build prints a note when that
happens. Body copy sits between `:: ABOVE ::` and `:: BELOW ::` markers, both optional.

**What the build produces:** `dabble-hero-peel.html` (~64 KB), `our-team.html` (~37 KB),
`assets/` (every photograph), and `content-manifest.json` (entries, tags and credits — the
data the galleries will read). **Deploy the HTML and `assets/` together**; the pages do not
work without it.

**Every image is a file, and that is load-bearing.** Main images used to be base64 inside
the page, which made them the page weight: 2.6 MB that had to arrive *in full* before
anything appeared, because with one file first paint and full load are the same moment.
Measured over a throttled connection, before and after:

| connection | blank screen, embedded | blank screen, as files |
|---|---|---|
| Home wifi 25 Mbps | 1.6 s | 0.5 s |
| Good 4G 10 Mbps | 3.3 s | 0.4 s |
| Slow 3G 1.6 Mbps | **14 s** | **0.6 s** |

The photographs now stream in behind a page that is already up and animating, which suits a
bloom that fades its pictures in on a 340 ms stagger anyway. It also removes the old
ceiling: adding entries no longer lengthens the wait before anything appears. `build.py`
warns if the page itself ever exceeds 400 KB, which would mean something got embedded
again. `MAIN_Q` is back to 82 — quality costs streaming time now, not time-to-first-paint.

**Running it.** `python3 build.py` in Terminal, from `hero-peel/`. Nothing else is needed —
no chat, no manual image export. It takes about two seconds and is deterministic: the same
content produces a byte-identical page.

It resizes and converts images with **Pillow** if installed, otherwise falls back to
macOS's built-in **`sips`**, so it runs on a stock Mac with nothing to install.
`python3 build.py --backend` prints which one it is using. If neither is available the
build says so and names the fix (`python3 -m pip install --user Pillow`).

---

## Sub-pages

**Each sub-page is its own HTML file.** `our-team.html` is the first, and it sets the
pattern. Clicking a nav label in the peel navigates to a file — `PAGE_URLS` in
`H-peel.txt` maps label to filename, and Stories, Dabblers, About and Contact slot in
there as they get built. The dabble mark, top-left on every sub-page, links back to
`dabble-hero-peel.html`.

The trade-off, so nobody is surprised by it: leaving the hero is a full page load and
the peel resets. That costs much less than it used to, now that the pictures are files
rather than base64: the document itself is ~64 KB and the photographs come from the
browser cache on the way back. An in-place version — sub-pages
as overlays inside the hero document, nothing reloading — was built first and replaced by
this on request. If it ever comes back, two things bite:

- **Lift the overlay to `<body>`.** `.hero` carries the perspective, which makes it a
  stacking context, so a z-index inside it cannot rise above the sky and paper (moved to
  `<body>` on load). A sub-page left inside `.hero` opens *behind* the peel and is simply
  invisible — it looks like the click did nothing.
- **`const TEAM` is not `window.TEAM`.** A top-level `const` is a lexical binding, not a
  property of `window`. Guard with `typeof TEAM === 'undefined'`.

**Markup lives in the engine**, at `tpl2/team-page.html`, so the pages are versioned with
the hero. `build.py` injects the data and the logo and writes `our-team.html`; it fails
loudly if any `__PLACEHOLDER__` is left unfilled. A new sub-page is a new template there
plus a line in `PAGE_URLS` (in `build.py`, alongside `NAV_PAGES`).

**Sub-pages carry the corner lift too**, so the nav is reachable without going back
through the hero. `tpl2/lift.txt` holds it, and it is *generated*, not hand-written:
`tools/extract-lift.py` pulls the sky CSS and the colour and geometry helpers verbatim out
of `H-peel.txt`, and `tools/assemble-lift.py` wraps them in the sub-page host. Rerun both
after retuning the peel, or the two will drift:

    python3 tools/extract-lift.py && python3 tools/assemble-lift.py

Which rules cross over is the `WANT` list at the top of `extract-lift.py`, with hero-only
rules named in `SKIP` beside it. That list is hand-maintained and does not notice new
rules on its own: `.under.live ol{pointer-events:auto}` was left out of it once, and the
sub-page menu was the result — visible, lit, hover-styled in the stylesheet, and
completely inert, because `pointer-events` never came back on. A press on a nav item fell
straight through to the peel's own drag handler. `extract-lift.py` now refuses to run if
`H-peel.txt` grows a lift rule that is in neither list, so the same omission fails loudly
instead of shipping quietly.

One thing the sub-page does *not* inherit is the hero's `body{user-select:none}` — a bio
should be copyable. So the nav list opts out on its own (`.under`, shared by both pages),
and a press that actually starts a peel calls `preventDefault()`, or dragging the corner
open sweeps a text selection across everything behind it.

The peel only ever needed `HERO.ease` and `HERO.frame`; everything else in `HERO` is
bloom-specific. So the sub-page stands up an eight-line frame-loop shim with the same
dt/ease/frame shape rather than carrying the engine. It fades its own content out on the
same `q 0.95 -> 0.75` window the hero uses for the bloom.

**Moving between pages is choreographed, so two documents read as one.** Clicking a nav
link does not follow it immediately: the peel carries on past the far corner until the
paper covers the whole window, the links fade out with the last of the fold, and the mark
has already flipped to black. Only then does the link get followed — about 950ms. The
sub-page opens on that identical frame: bare cream, black mark, no content. Its own frame
loop then eases the content and the info mark in over ~620ms after a 90ms beat.

The mark fades out the moment the peel starts (`clamp(1-q*8,0,1)`), so it is gone long
before the paper reaches its corner.

Two things this depends on, both of which were bugs first:

- **`leaving` is never cleared and the frame is never cut short.** The browser keeps
  painting the old document until the new one commits, so clearing the flag let the fade
  factor fall back to zero and flashed the links bright again on the very last frames.
  Measured: nav opacity fell 1.00 → 0.04 and then snapped back to 1.00.
- **The sub-page starts at `#sheet{opacity:0}`**, with a `<noscript>` override so the page
  is not blank if the script never runs.

**Three things invert because a sub-page is cream, not black**, and each was a real bug
first: the info mark is the black drawing rather than the white one; the wordmark starts
black and turns white only once the night sky is behind it;
and `.logo` drops the hero's `pointer-events:none`, because here it is the link home. The
peel also yields to anything the page owns — the mark, the nav, an open profile card, and
the headshots, since on a narrow screen a headshot can sit inside the corner band and
tapping it must open that person rather than start a peel.

**The people come from `team/`** — `team.csv` (name, role, bio, photo), the headshots, and
`intro.txt` for the paragraph under them. Row order is page order. Photos go to
`assets/team/` at 640px. Anyone named in an entry's `credits:` gets those entries listed
under their bio as a **Projects** block, matched on name case-insensitively; a credit
matching nobody is reported rather than silently dropped.

**The Projects list shows each entry's `subtitle`, not its `title`** — because the field
called `title` holds the *question* ("What if local news was so much more…") while
`subtitle` holds the short name ("Paperboy · 2026"), which is what reads as a project
name. That is a
naming wart inherited from the original placeholder data: the two fields are arguably the
wrong way round. Renaming them means touching every `entry.md`, the schema in
`content/README.txt` and the card renderer in `H-peel.txt`; worth doing before there are
many more entries, not urgent. Until then the fallback is `subtitle or title`, so an entry
with no subtitle still lists as something rather than a blank line.

**The layout.** Heading, then the ten headshots in two rows of five, then the intro
paragraph — and that is the whole page, about 900px with no scroll at desktop. Clicking a
headshot opens that person's profile as an overlay over the page: portrait one side, name,
role, bio and credited projects the other. Esc, the backdrop or Close dismisses it, and
page scroll is locked while it is open. The long scrolling list of profiles this replaced
ran to ~8,000px.

Hovering a headshot fades the person's name in over a bottom-weighted scrim — on a scrim
rather than bare photography, so it stays legible whatever they are wearing. There is no
hover on touch, so `@media (hover:none)` leaves the names permanently visible there.

**Everything is in full colour.** The greyscale-with-colour-on-hover treatment was removed
on request; there are no `filter` rules left on this page.

Below 720px the overlay stacks to one column and its portrait becomes square; below 620px
the headshot grid drops from five columns to three, since five puts the faces under 65px.

---

## Still open

The working list lives in `content/README.txt` under **TO BUILD** — keep it there rather
than here, so there is one list and not two. In short (as of this session): the **Stories and Dabblers galleries and the About page are
now built and in the nav**; still outstanding are **Contact**, bios and roles for the team,
real copy for entries 002–012, captions on supporting images, and an optional watch mode
for rebuilding on save.

**The build runs as of the latest session** (`python3 build.py`, exit 0). The blockers
below were noted in an earlier session, when real images were being swapped into the entry
folders; verify them against the current `content/` state before relying on them:

- `004-pumbit/main/` and `008-awty/main/` each hold two images. `main/` takes exactly one —
  by design, so the build never has to guess which picture is the card. In both cases the
  stock placeholder is the one to move out (`europeana-…unsplash.jpg` and `pdia-…jpg`);
  the build names the folder and stops until one goes.
- `006-fate matchbooks/supporting/New Folder With Items/` holds two PNGs the build cannot
  see — `supporting/` is not scanned recursively. They need to sit directly in
  `supporting/` to appear on the card.

Entries 002, 003, 005, 006 and 007 already have their real main images in place.

Two housekeeping items that are not on that list because they are not content:

- **Seven orphaned asset folders.** Renaming the entries left `assets/001-light`,
  `002-flight`, `003-surface`, `004-spectacle`, `005-repeat`, `006-record` and
  `007-distance` behind — about 1.7 MB. Nothing references them, so they cost nothing at
  runtime; the build reports them each time because it cannot delete them itself.
- **`~/Desktop/dabble website/images/hero shot/`** is a redundant second copy of the
  original twelve files.

`001-paperboy` is the first real entry — real copy, real images, real credits. The other
eleven are still placeholder copy under their new names, so `Sunny Ears · 2026` currently
sits above writing about Leonardo's ornithopter. Subtitles are `Name · 2026` throughout,
taken from the folder name; `team.csv` carries full names, and credits in `entry.md` have
to match them exactly.

On the team page, every bio is blank except Anastasha's, which is a placeholder; no roles
are filled in; and `team/intro.txt` is empty, so there is no paragraph under the
headshots. Anastasha is credited on `003-lab tvs` and `007-lagu hantu` purely to test the
mechanism — those two were invented, unlike Paperboy's four, which are real.

---

## The images

`001-paperboy` carries its own images now — a Frederick Burr Opper satire as the main
picture and a synthesis screenshot in `supporting/`. The remaining eleven are still stock
placeholders: 002 da Vinci wing · 003 orange marbled paper · 004 Vesuvius · 005 grey
marbled paper · 006 mountain laurel botanical · 007 comet · 008 Spalding flying-machine
patent · 009 X-ray hand · 010 umbrellas and bats engraving · 011 weather map · 012 nervous
system.

Each entry's `main/` folder holds its own copy of the original, so `content/` is
self-contained. `~/Desktop/dabble website/images/hero shot/` is now a redundant second copy
of the same twelve files and can be deleted once you're happy.

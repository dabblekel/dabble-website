#!/usr/bin/env python3
"""
Build the Dabble hero from ../content/.

    cd "dabble website/hero-peel" && python3 build.py

Reads every folder in ../content/ (anything starting with "_" is skipped), and writes:

    dabble-hero-peel.html   the hero - ~60 KB, so it paints immediately
    our-team.html           the Our Team page, built from team/team.csv + team/
    assets/<slug>/main.jpg  the picture that floats in the swirl
    assets/<slug>/...       supporting images, fetched only when a card is opened
    assets/team/...         headshots
    content-manifest.json   entries, tags and credits, for the pages still to be built

Every image is a file. The pages are small and paint at once; the photographs stream in
behind them, which suits a bloom that fades its pictures in on a stagger anyway. Deploy
the HTML and assets/ together - the page will not work with assets/ missing.

The rendering engine itself lives in source/dabble-hero-source.zip and is not modified;
this script extracts it to a temp folder, injects the generated content, and runs its
buildH.py. Editing dabble-hero-peel.html by hand is pointless - it is regenerated here.
"""
import base64, csv, io, json, os, re, shutil, subprocess, sys, tempfile
import urllib.parse

# Pillow if it is installed, otherwise macOS's built-in sips. The sips path exists so this
# runs in Terminal on a stock Mac with nothing to install; it is slower and slightly less
# sharp, but produces the same result. `python3 build.py --backend` prints which is in use.
try:
    from PIL import Image, ImageOps
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

HERE     = os.path.dirname(os.path.abspath(__file__))
ROOT     = os.path.dirname(HERE)
CONTENT  = os.path.join(ROOT, "content")
ASSETS   = os.path.join(HERE, "assets")
TEAM_DIR = os.path.join(ROOT, "team")
TEAM_CSV = os.path.join(TEAM_DIR, "team.csv")
TEAM_INTRO = os.path.join(TEAM_DIR, "intro.txt")

# The nav, and where each label goes. Kept here because build.py is what writes the
# sub-pages; the hero has its own copy in H-peel.txt. Add a page in both places.
NAV_PAGES = ["Stories", "Dabblers", "Our Team", "About", "Contact"]
PAGE_URLS = {"Stories": "stories.html", "Dabblers": "dabblers.html", "Our Team": "our-team.html", "About": "about.html", "Contact": "contact.html"}
ENGINE   = os.path.join(HERE, "source", "dabble-hero-source.zip")

# The corner mark that asks for the lift. Two SVGs, one for a dark ground and one for a
# light one, drawn once and used by every page.
ICON_SVG = {"white": os.path.join(HERE, "Info Icon_white.svg"),
            "black": os.path.join(HERE, "Info Icon_black.svg")}

# Main images used to be embedded, which made them the page weight: 2.6 MB of base64 that
# had to arrive in full before anything at all appeared - 14 s of blank screen on slow 3G,
# and worse with every entry added. They are files now, so the page is ~60 KB and quality
# here costs load time rather than time-to-first-paint. Hence 82 rather than the 74 that
# size pressure forced.
MAIN_MAX, MAIN_Q = 1280, 82
SUPP_MAX, SUPP_Q = 1600, 82
TEAM_MAX, TEAM_Q = 640, 82         # headshots are square and shown small; external like supporting
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp", ".heic"}

def read_icon():
    """The corner mark, as two data URIs.

       Illustrator exports an opaque artboard rectangle behind the drawing. Left in, it is
       a solid square sitting over the bloom, so any <rect> the size of the viewBox is
       dropped here rather than by hand - the files can then be re-exported without anyone
       having to remember to delete it."""
    out = {}
    for k, path in ICON_SVG.items():
        if not os.path.isfile(path):
            die("missing %s - the corner needs both Info Icon_white.svg and "
                "Info Icon_black.svg in hero-peel/" % os.path.basename(path))
        svg = open(path, encoding="utf-8").read()
        vb = re.search(r'viewBox\s*=\s*"([-\d.\s]+)"', svg)
        if vb:
            box = vb.group(1).split()
            if len(box) == 4:
                bw, bh = float(box[2]), float(box[3])
                def drop(m):
                    t = m.group(0)
                    w = re.search(r'width="([\d.]+)"', t)
                    h = re.search(r'height="([\d.]+)"', t)
                    if w and h and abs(float(w.group(1)) - bw) < 0.5 \
                                and abs(float(h.group(1)) - bh) < 0.5:
                        return ""
                    return t
                svg = re.sub(r"<rect\b[^>]*?/>", drop, svg, flags=re.S)
        out[k] = "data:image/svg+xml;base64," + base64.b64encode(
            svg.encode("utf-8")).decode("ascii")
    return out

def die(msg):
    print("\n  BUILD FAILED: " + msg + "\n", file=sys.stderr); sys.exit(1)

def pics(folder):
    if not os.path.isdir(folder): return []
    return sorted(f for f in os.listdir(folder)
                  if not f.startswith(".") and os.path.splitext(f)[1].lower() in EXTS)

CAROUSEL_DIR = "carousel"   # supporting/<CAROUSEL_DIR>/ -> the overlay's extra-image carousel

def collect_images(src_dir, asset_dir, url_dir, slug, rel_label, warn, written, warn_missing):
    """Load every image in src_dir, write it to asset_dir as JPEG, and return
       [{src,w,h,caption}] - caption from a .txt of the same name beside it. Used for both
       the full-width supporting plates and the carousel sub-folder."""
    out = []
    for f in pics(src_dir):
        blob, w, h = load(os.path.join(src_dir, f), SUPP_MAX, SUPP_Q)
        os.makedirs(asset_dir, exist_ok=True)
        stem = os.path.splitext(f)[0]
        name = stem + ".jpg"
        dest = os.path.join(asset_dir, name)
        open(dest, "wb").write(blob)
        written.add(os.path.abspath(dest))
        cap, side = "", os.path.join(src_dir, stem + ".txt")
        if os.path.isfile(side):
            cap = " ".join(open(side, encoding="utf-8").read().split())
        if not cap and warn_missing:
            warn.append("%s: %s/%s has no caption yet (write one into %s/%s.txt)"
                        % (slug, rel_label, f, rel_label, stem))
        out.append({"src": url_dir + "/" + urllib.parse.quote(name), "w": w, "h": h, "caption": cap})
    return out

def _sips_dims(path):
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", path],
                         capture_output=True, text=True).stdout
    w = h = 0
    for line in out.splitlines():
        if "pixelWidth"  in line: w = int(line.split(":")[1])
        if "pixelHeight" in line: h = int(line.split(":")[1])
    return w, h

def _load_sips(path, cap, q):
    with tempfile.TemporaryDirectory() as t:
        out = os.path.join(t, "out.jpg")
        cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(q)]
        sw, sh = _sips_dims(path)
        if max(sw, sh) > cap:                 # sips -Z would upscale smaller images
            cmd += ["-Z", str(cap)]
        cmd += [path, "--out", out]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            die("sips could not read %s\n  %s" % (path, r.stderr.strip()))
        w, h = _sips_dims(out)
        return open(out, "rb").read(), w, h

def _load_pil(path, cap, q):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)      # honour EXIF orientation (e.g. phone photos)
    if im.mode not in ("RGB", "L"): im = im.convert("RGB")
    im.thumbnail((cap, cap), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    return buf.getvalue(), im.width, im.height

def backend():
    if HAVE_PIL: return "Pillow"
    if shutil.which("sips"): return "sips"
    return None

def load(path, cap, q):
    b = backend()
    if b == "Pillow": return _load_pil(path, cap, q)
    if b == "sips":   return _load_sips(path, cap, q)
    die("no image backend. Install Pillow with:  python3 -m pip install --user Pillow")

def parse_entry(path):
    """Front matter (a fixed, small schema - parsed by hand so there is no PyYAML
       dependency) followed by :: ABOVE :: and :: BELOW :: copy sections."""
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    if not m: die(path + ": missing the --- front matter block at the top")
    head, body = m.group(1), m.group(2)

    d, key = {"credits": []}, None
    for line in head.splitlines():
        if not line.strip() or line.lstrip().startswith("#"): continue
        item = re.match(r"^\s+-\s*(.*)$", line)
        if item and key == "credits":
            if item.group(1).strip(): d["credits"].append(item.group(1).strip())
            continue
        kv = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", line)
        if kv:
            key, val = kv.group(1).lower(), kv.group(2).strip()
            if key != "credits": d[key] = val
    yes = lambda v: str(v).strip().lower() in ("yes", "true", "y", "1", "on")
    def as_int(v):
        try: return int(str(v).strip())
        except Exception: return None

    def section(name, nxt):
        pat = r"::\s*%s\s*::\s*\n(.*?)(?=::\s*%s\s*::|\Z)" % (name, nxt or "ZZZ_NONE")
        mm = re.search(pat, body, re.S | re.I)
        return mm.group(1).strip() if mm else ""

    return {
        "title":    d.get("title", "").strip(),
        "subtitle": d.get("subtitle", "").strip(),
        "caption":  d.get("caption", "").strip(),
        "story":    yes(d.get("story", "no")),
        "dabbler":  yes(d.get("dabbler", "no")),
        "credits":  d["credits"],
        "order":    as_int(d.get("order")) if str(d.get("order", "")).strip() else None,
        "above":    section("ABOVE", "BELOW"),
        "below":    section("BELOW", None),
    }

def read_team(warn, written):
    """team/team.csv -> the Our Team page. Columns: name, role, bio, photo.
       Row order is the order on the page, so reordering rows in a spreadsheet reorders
       the page. Photos are written to assets/team/ and fetched when the page opens."""
    if not os.path.isfile(TEAM_CSV):
        warn.append("no team/team.csv - the Our Team page will be empty")
        return []
    people, seen = [], set()
    with open(TEAM_CSV, newline="", encoding="utf-8-sig") as fh:   # -sig: Excel writes a BOM
        for i, row in enumerate(csv.DictReader(fh), start=2):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            name = row.get("name", "")
            if not name:
                warn.append("team.csv line %d has no name - skipped" % i); continue
            photo, url = row.get("photo", ""), None
            if photo:
                src = os.path.join(TEAM_DIR, photo)
                if os.path.isfile(src):
                    blob, _, _ = load(src, TEAM_MAX, TEAM_Q)
                    os.makedirs(os.path.join(ASSETS, "team"), exist_ok=True)
                    out = os.path.splitext(photo)[0] + ".jpg"
                    dest = os.path.join(ASSETS, "team", out)
                    open(dest, "wb").write(blob)
                    written.add(os.path.abspath(dest))
                    url = "assets/team/" + out
                    seen.add(photo)
                else:
                    warn.append("%s: photo %r is not in team/" % (name, photo))
            else:
                warn.append("%s: no photo named in team.csv" % name)
            if not row.get("bio"): warn.append("%s: no bio yet" % name)
            people.append({"name": name, "role": row.get("role", ""),
                           "bio": row.get("bio", ""), "photo": url, "projects": []})

    for f in sorted(os.listdir(TEAM_DIR)):
        if f.lower().endswith((".webp", ".jpg", ".jpeg", ".png")) and f not in seen:
            warn.append("team/%s is not used by any row in team.csv" % f)
    return people


def main():
    b = backend()
    if b is None:
        die("no image backend found. Either install Pillow:\n"
            "      python3 -m pip install --user Pillow\n"
            "  or run this on a Mac, where the built-in sips is used automatically.")
    if "--backend" in sys.argv:
        print("  image backend: " + b); return
    if not os.path.isdir(CONTENT): die("no content folder at " + CONTENT)
    entry_dirs = [f for f in os.listdir(CONTENT)
                  if os.path.isdir(os.path.join(CONTENT, f)) and not f.startswith(("_", "."))]
    if not entry_dirs: die("content/ has no entry folders")
    # The page order comes from an optional `order:` field in each entry.md - lower first -
    # so the folder name is just a slug and contributors never have to claim a number.
    # Entries with no `order` fall to the end, arranged by slug so the result is stable.
    def order_of(slug):
        ep = os.path.join(CONTENT, slug, "entry.md")
        if not os.path.isfile(ep): return 10**9
        try:
            o = parse_entry(ep).get("order")
        except SystemExit: raise
        except Exception: return 10**9
        return o if o is not None else 10**9
    slugs = sorted(entry_dirs, key=lambda s: (order_of(s), s.lower()))

    images, stories, manifest, warn, written = [], {}, [], [], set()

    for i, slug in enumerate(slugs):
        d = os.path.join(CONTENT, slug)
        ep = os.path.join(d, "entry.md")
        if not os.path.isfile(ep): die(slug + ": no entry.md")
        e = parse_entry(ep)

        mains = pics(os.path.join(d, "main"))
        if len(mains) == 0: die(slug + ": main/ is empty - it needs exactly one image")
        if len(mains) > 1:
            die(slug + ": main/ has %d images (%s) - it needs exactly one; move the rest "
                "to supporting/" % (len(mains), ", ".join(mains)))
        if not e["story"] and not e["dabbler"]:
            warn.append(slug + ": tagged neither story nor dabbler - it will float in the "
                                "swirl but appear in no gallery")
        if not e["title"]: warn.append(slug + ": no title")

        blob, w, h = load(os.path.join(d, "main", mains[0]), MAIN_MAX, MAIN_Q)
        os.makedirs(os.path.join(ASSETS, slug), exist_ok=True)
        dest = os.path.join(ASSETS, slug, "main.jpg")
        open(dest, "wb").write(blob)
        written.add(os.path.abspath(dest))
        images.append({"id": i, "w": w, "h": h, "src": "assets/%s/main.jpg" % urllib.parse.quote(slug)})

        # Supporting images run full width in the open card, so their real proportions
        # are carried through and written onto the <img> - the browser then holds the
        # right amount of room while the file is still loading. The caption for one lives
        # beside it, in a .txt of the same name, so a folder stays self-describing.
        support = collect_images(os.path.join(d, "supporting"),
                                 os.path.join(ASSETS, slug), "assets/%s" % urllib.parse.quote(slug),
                                 slug, "supporting", warn, written, True)
        # supporting/carousel/ - extra images for image-heavy projects, shown as a compact
        # carousel in the gallery overlay instead of full-height plates, so a big set does
        # not push the rest of the page down. Absent or empty -> no carousel. Captions are
        # optional here (no warning), since these are for bulk sharing.
        carousel = collect_images(os.path.join(d, "supporting", CAROUSEL_DIR),
                                  os.path.join(ASSETS, slug, CAROUSEL_DIR),
                                  "assets/%s/%s" % (urllib.parse.quote(slug), urllib.parse.quote(CAROUSEL_DIR)),
                                  slug, "supporting/" + CAROUSEL_DIR, warn, written, False)

        stories[i] = {"k": e["subtitle"], "q": e["title"], "above": e["above"],
                      "below": e["below"], "caption": e["caption"], "support": support, "carousel": carousel,
                      "story": e["story"], "dabbler": e["dabbler"],
                      "credits": e["credits"], "slug": slug}
        manifest.append({"id": i, "slug": slug, "title": e["title"],
                         "subtitle": e["subtitle"],
                         "story": e["story"], "dabbler": e["dabbler"],
                         "credits": e["credits"], "supporting": len(support), "carousel": len(carousel)})

    team = read_team(warn, written)

    # Credits on an entry become mini-mentions under that person. Matched on name,
    # case-insensitively; a credit matching nobody in team.csv is called out rather than
    # silently dropped, since a typo would otherwise just vanish.
    by_name = {p["name"].strip().lower(): p for p in team}
    for m in manifest:
        # A project's page is its case study in the gallery it belongs to. Link to that
        # gallery with the entry's slug in the hash; the gallery opens that overlay on
        # arrival. Prefer Stories when an entry is in both; blank when it is in neither.
        gpage = "stories.html" if m["story"] else ("dabblers.html" if m["dabbler"] else "")
        gurl  = (gpage + "#" + urllib.parse.quote(m["slug"])) if gpage else ""
        for c in m["credits"]:
            p = by_name.get(c.strip().lower())
            # The Projects list on a profile wants the entry's short name, not its
            # question. That short name lives in `subtitle` - the field called `title`
            # holds the question. Fall back to the question if a subtitle is missing, so
            # a project never appears as a blank line.
            if p: p["projects"].append({"slug": m["slug"],
                                        "name": m["subtitle"] or m["title"],
                                        "url": gurl,
                                        "img": "assets/%s/main.jpg" % urllib.parse.quote(m["slug"])})
            else: warn.append("%s credits %r, who is not in team.csv" % (m["slug"], c))

    # Prune assets that no longer belong to any entry. Best effort by design: a stale file
    # that cannot be deleted - open in another app, locked by a sync client, read-only - is
    # a warning, not a failed build. Wiping the whole folder up front meant one such file
    # took the entire build down with it.
    for root, _, files in os.walk(ASSETS):
        for f in files:
            fp = os.path.abspath(os.path.join(root, f))
            if fp in written: continue
            try: os.remove(fp)
            except OSError:
                warn.append("left a stale asset in place, could not delete: "
                            + os.path.relpath(fp, HERE))
    for root, dirs, _ in os.walk(ASSETS, topdown=False):
        for d in dirs:
            try: os.rmdir(os.path.join(root, d))
            except OSError: pass

    if not os.path.isfile(ENGINE): die("engine archive missing at " + ENGINE)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["unzip", "-q", ENGINE, "-d", tmp], check=True)
        open(os.path.join(tmp, "images.json"), "w").write(json.dumps(images))
        icon = read_icon()
        open(os.path.join(tmp, "icon.json"), "w").write(json.dumps(icon))
        open(os.path.join(tmp, "tpl2", "stories.js"), "w").write(
            "const STORIES=" + json.dumps(stories, ensure_ascii=False) + ";\n"
            "const TEAM=" + json.dumps(team, ensure_ascii=False) + ";")
        subprocess.run([sys.executable, "buildH.py"], cwd=tmp, check=True,
                       stdout=subprocess.DEVNULL)
        shutil.copy(os.path.join(tmp, "build4", "peel-v2.html"),
                    os.path.join(HERE, "dabble-hero-peel.html"))
        # index.html is the site's front door (what a web host serves at "/"); it is the
        # same hero page under a second name so links to dabble-hero-peel.html still work.
        shutil.copy(os.path.join(tmp, "build4", "peel-v2.html"),
                    os.path.join(HERE, "index.html"))

        # Our Team is its own document. Its markup lives in the engine archive beside the
        # hero's, so both are versioned together; only the data is injected here.
        tpl = os.path.join(tmp, "tpl2", "team-page.html")
        if os.path.isfile(tpl):
            logo = json.load(open(os.path.join(tmp, "logo.json")))
            page = open(tpl, encoding="utf-8").read()
            page = page.replace("__TEAM__", json.dumps(team, ensure_ascii=False))

            # The corner lift, so a sub-page carries the site's navigation rather than
            # sending people back through the hero. Its fragment is assembled from
            # H-peel.txt, so the sunrise is the hero's sunrise.
            lift = os.path.join(tmp, "tpl2", "lift.txt")
            if os.path.isfile(lift):
                L = open(lift, encoding="utf-8").read()
                l_style  = L.split("/*=== STYLE ===*/")[1].split("/*=== MARKUP ===*/")[0]
                l_markup = L.split("/*=== MARKUP ===*/")[1].split("/*=== SCRIPT ===*/")[0]
                l_script = L.split("/*=== SCRIPT ===*/")[1]
                pages = [{"label": lb, "url": PAGE_URLS.get(lb, "")} for lb in NAV_PAGES]
                l_script = (l_script
                    .replace("__PAGES__", json.dumps(pages))
                    .replace("__HERE__", json.dumps("Our Team"))
                    .replace("__LOGO__", json.dumps(logo))
                    .replace("__ICON__", json.dumps(icon)))
                page = (page.replace("__LIFT_STYLE__", l_style)
                            .replace("__LIFT_MARKUP__", l_markup)
                            .replace("__LIFT_SCRIPT__", l_script))
            else:
                warn.append("engine has no tpl2/lift.txt - the sub-page has no navigation")
                page = (page.replace("__LIFT_STYLE__", "")
                            .replace("__LIFT_MARKUP__", "")
                            .replace("__LIFT_SCRIPT__", ""))

            # The paragraph under the headshots. Plain text in team/intro.txt; blank lines
            # separate paragraphs. Empty file means no paragraph at all rather than an
            # empty element - there is no placeholder copy anywhere on this site.
            intro = ""
            if os.path.isfile(TEAM_INTRO):
                intro = open(TEAM_INTRO, encoding="utf-8").read().strip()
            if intro:
                esc = lambda t: (t.replace("&", "&amp;").replace("<", "&lt;")
                                  .replace(">", "&gt;"))
                block = "\n  ".join('<p class="intro">%s</p>' % esc(" ".join(par.split()))
                                    for par in re.split(r"\n\s*\n", intro) if par.strip())
            else:
                block = ""
                warn.append("team/intro.txt is empty - no paragraph under the headshots")
            page = page.replace("__INTRO_BLOCK__", block)
            left = re.findall(r"__[A-Z_]+__", page)
            if left: die("team-page.html still has unfilled placeholders: " + ", ".join(sorted(set(left))))
            open(os.path.join(HERE, "our-team.html"), "w", encoding="utf-8").write(page)
        else:
            warn.append("engine has no tpl2/team-page.html - our-team.html not rebuilt")

        # Stories and Dabblers galleries - one shared template, filtered by tag. Same
        # sub-page shell as Our Team: cream page, corner-lift nav, and an overlay per entry
        # carrying the full case study, a carousel of its supporting images, and the people
        # who made it (credits resolved to their headshot, role and bio).
        gtpl = os.path.join(tmp, "tpl2", "gallery-page.html")
        if os.path.isfile(gtpl):
            glogo = json.load(open(os.path.join(tmp, "logo.json")))
            glift = os.path.join(tmp, "tpl2", "lift.txt")
            GL = open(glift, encoding="utf-8").read() if os.path.isfile(glift) else ""
            if GL:
                g_style  = GL.split("/*=== STYLE ===*/")[1].split("/*=== MARKUP ===*/")[0]
                g_markup = GL.split("/*=== MARKUP ===*/")[1].split("/*=== SCRIPT ===*/")[0]
                g_script = GL.split("/*=== SCRIPT ===*/")[1]
            gpages = [{"label": lb, "url": PAGE_URLS.get(lb, "")} for lb in NAV_PAGES]

            img_by_id = {im["id"]: im for im in images}
            mem_by_name = {q["name"].strip().lower(): q for q in team}
            def gallery_view(m):
                s = stories[m["id"]]; im = img_by_id[m["id"]]
                crew = []
                for c in m["credits"]:
                    q = mem_by_name.get(c.strip().lower())
                    crew.append({"name": q["name"] if q else c,
                                 "role": q["role"] if q else "",
                                 "bio":  q["bio"]  if q else "",
                                 "photo": q["photo"] if q else None})
                return {"slug": m["slug"], "src": im["src"], "w": im["w"], "h": im["h"],
                        "subtitle": s["k"], "title": s["q"], "above": s["above"],
                        "below": s["below"], "caption": s["caption"],
                        "support": s["support"], "carousel": s["carousel"], "credits": crew}

            GALLERY_INTRO = {
                "Stories":
                    "These are stories of projects undertaken by our team members. While they "
                    "take many different forms and mediums, and center on a vast variety of "
                    "topics, they all have the essence of dabbling in common: creating new "
                    "meaning and envisioning change for a given system.\n\n"
                    "These projects serve as evidence of our own dedication to refining the "
                    "practice of Dabbling, for ourselves and the world.",
                "Dabblers":
                    "These are projects that we’ve completed in support of our clients "
                    "(who we call Dabblers): visionaries who see the opportunity to uncover "
                    "great potential within their problems of interest.\n\n"
                    "We help them begin to Dabble and see their problems in a new way, helping "
                    "them spot golden opportunities to intervene and refine a new point of view.",
            }
            for label, fname, flag in (("Stories", "stories.html", "story"),
                                       ("Dabblers", "dabblers.html", "dabbler")):
                rows = [gallery_view(m) for m in manifest if m[flag]]
                gp = open(gtpl, encoding="utf-8").read()
                gp = gp.replace("__HEADING__", label)
                _intro = GALLERY_INTRO.get(label, "")
                _introHTML = "\n  ".join('<p>%s</p>' % (" ".join(par.split())).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                                         for par in re.split(r"\n\s*\n", _intro) if par.strip())
                gp = gp.replace("__INTRO__", _introHTML)
                gp = gp.replace("__ENTRIES__", json.dumps(rows, ensure_ascii=False))
                if GL:
                    gs = (g_script.replace("__PAGES__", json.dumps(gpages))
                                  .replace("__HERE__", json.dumps(label))
                                  .replace("__LOGO__", json.dumps(glogo))
                                  .replace("__ICON__", json.dumps(icon)))
                    gp = (gp.replace("__LIFT_STYLE__", g_style)
                             .replace("__LIFT_MARKUP__", g_markup)
                             .replace("__LIFT_SCRIPT__", gs))
                else:
                    warn.append("engine has no tpl2/lift.txt - %s has no navigation" % fname)
                    gp = (gp.replace("__LIFT_STYLE__", "").replace("__LIFT_MARKUP__", "")
                             .replace("__LIFT_SCRIPT__", ""))
                gleft = re.findall(r"__[A-Z_]+__", gp)
                if gleft:
                    die("gallery-page.html still has unfilled placeholders in %s: %s"
                        % (fname, ", ".join(sorted(set(gleft)))))
                open(os.path.join(HERE, fname), "w", encoding="utf-8").write(gp)
        else:
            warn.append("engine has no tpl2/gallery-page.html - galleries not built")

        # About is a hand-built interactive sub-page; its content lives in the engine
        # archive as about-page.html, and only the corner-lift nav is injected here.
        atpl = os.path.join(tmp, "tpl2", "about-page.html")
        if os.path.isfile(atpl):
            ap = open(atpl, encoding="utf-8").read()
            alift = os.path.join(tmp, "tpl2", "lift.txt")
            if os.path.isfile(alift):
                AL = open(alift, encoding="utf-8").read()
                a_style  = AL.split("/*=== STYLE ===*/")[1].split("/*=== MARKUP ===*/")[0]
                a_markup = AL.split("/*=== MARKUP ===*/")[1].split("/*=== SCRIPT ===*/")[0]
                a_script = AL.split("/*=== SCRIPT ===*/")[1]
                alogo = json.load(open(os.path.join(tmp, "logo.json")))
                apages = [{"label": lb, "url": PAGE_URLS.get(lb, "")} for lb in NAV_PAGES]
                a_script = (a_script
                    .replace("__PAGES__", json.dumps(apages))
                    .replace("__HERE__", json.dumps("About"))
                    .replace("__LOGO__", json.dumps(alogo))
                    .replace("__ICON__", json.dumps(icon)))
                ap = (ap.replace("__LIFT_STYLE__", a_style)
                        .replace("__LIFT_MARKUP__", a_markup)
                        .replace("__LIFT_SCRIPT__", a_script))
            else:
                warn.append("engine has no tpl2/lift.txt - about.html has no navigation")
                ap = (ap.replace("__LIFT_STYLE__", "").replace("__LIFT_MARKUP__", "")
                        .replace("__LIFT_SCRIPT__", ""))
            open(os.path.join(HERE, "about.html"), "w", encoding="utf-8").write(ap)
        else:
            warn.append("engine has no tpl2/about-page.html - about.html not built")

        # Contact is a simple hand-built sub-page: its copy and the corner boulder+boat
        # live in the engine archive as contact-page.html, and only the corner-lift nav
        # is injected here, exactly as for About.
        ctpl = os.path.join(tmp, "tpl2", "contact-page.html")
        if os.path.isfile(ctpl):
            cp = open(ctpl, encoding="utf-8").read()
            clift = os.path.join(tmp, "tpl2", "lift.txt")
            if os.path.isfile(clift):
                CL = open(clift, encoding="utf-8").read()
                c_style  = CL.split("/*=== STYLE ===*/")[1].split("/*=== MARKUP ===*/")[0]
                c_markup = CL.split("/*=== MARKUP ===*/")[1].split("/*=== SCRIPT ===*/")[0]
                c_script = CL.split("/*=== SCRIPT ===*/")[1]
                clogo = json.load(open(os.path.join(tmp, "logo.json")))
                cpages = [{"label": lb, "url": PAGE_URLS.get(lb, "")} for lb in NAV_PAGES]
                c_script = (c_script
                    .replace("__PAGES__", json.dumps(cpages))
                    .replace("__HERE__", json.dumps("Contact"))
                    .replace("__LOGO__", json.dumps(clogo))
                    .replace("__ICON__", json.dumps(icon)))
                cp = (cp.replace("__LIFT_STYLE__", c_style)
                        .replace("__LIFT_MARKUP__", c_markup)
                        .replace("__LIFT_SCRIPT__", c_script))
            else:
                warn.append("engine has no tpl2/lift.txt - contact.html has no navigation")
                cp = (cp.replace("__LIFT_STYLE__", "").replace("__LIFT_MARKUP__", "")
                        .replace("__LIFT_SCRIPT__", ""))
            open(os.path.join(HERE, "contact.html"), "w", encoding="utf-8").write(cp)
        else:
            warn.append("engine has no tpl2/contact-page.html - contact.html not built")

    json.dump({"entries": manifest, "team": team},
              open(os.path.join(HERE, "content-manifest.json"), "w"), indent=1)

    kb = os.path.getsize(os.path.join(HERE, "dabble-hero-peel.html")) / 1024
    assets_mb = sum(os.path.getsize(os.path.join(r, f))
                    for r, _, fs in os.walk(ASSETS) for f in fs) / 1048576
    sup = sum(m["supporting"] for m in manifest)
    car = sum(m.get("carousel", 0) for m in manifest)
    print("  %d entries  |  %d story  |  %d dabbler  |  %d supporting images%s"
          % (len(manifest), sum(m["story"] for m in manifest),
             sum(m["dabbler"] for m in manifest), sup,
             ("  |  %d carousel images" % car) if car else ""))
    tp = os.path.join(HERE, "our-team.html")
    print("  %d people   |  %d with a bio  |  %d with a photo   ->  our-team.html  %d KB"
          % (len(team), sum(1 for p in team if p["bio"]),
             sum(1 for p in team if p["photo"]),
             os.path.getsize(tp) // 1024 if os.path.isfile(tp) else 0))
    print("  dabble-hero-peel.html  %d KB   |   assets/  %.1f MB   (via %s)"
          % (round(kb), assets_mb, b))
    for w_ in warn: print("  note: " + w_)
    if kb > 400:
        print("  WARNING: the page itself is %d KB. It should be well under 100 KB - "
              "something\n           large has been embedded again." % round(kb))

if __name__ == "__main__":
    main()

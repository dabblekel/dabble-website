# Contributing a card to the dabble site

Every "what if" card on the site is one folder inside [`content/`](content/).
You don't need to touch any code to add one — you create a folder, fill in a
short text file, and drop in your images. When you open a pull request, an
automated check rebuilds the site to make sure your entry is valid, and a
maintainer merges it.

---

## Easiest way: the Add-a-Project form

The simplest way to add a project — no folders, no `entry.md`, no Git — is the
**Add-a-Project form**, published with the site at **`/add-project.html`**
(for example `https://<your-site>/add-project.html`). You can also open the
`hero-peel/add-project.html` file in a browser.

Fill in the fields, upload the images, and click **Download project folder
(.zip)**. The form packages everything into a small `.zip` file (the images are
resized for the web automatically) and saves it to your computer. Send that
`.zip` to a maintainer — there's nothing to install and no login. The maintainer
unzips it into `content/` and publishes it.

The rest of this document explains the underlying folder format, for anyone
adding a project by hand.

---

## What a card is made of

```
content/your-slug/
├── entry.md          the text of the card (title, copy, credits …)
├── main/             exactly ONE image — the one that floats on the front page
│   └── hero.jpg
└── supporting/       any number of images shown inside the card (or none)
    ├── 01-photo.jpg
    ├── 01-photo.txt  optional one-line caption for 01-photo.jpg
    └── carousel/     optional — extra images shown as a compact carousel
```

- **Folder name** is just a short, readable slug (e.g. `tidal-atlas`). It has to
  be unique, but it does **not** control where the card appears — the `order`
  field does (see below), so you never have to claim a number.
- **`main/`** must contain **exactly one** image. The build fails on purpose if
  it's empty or has more than one, so it never has to guess.
- **`supporting/`** images appear in filename order — name them `01-`, `02-`, …
  Caption one by putting a `.txt` of the same name beside it.

Drop in **full-size** originals (JPEG, PNG, WebP, TIFF, HEIC). The build resizes
and compresses them for you — never export a web version by hand.

---

## `entry.md`

```
---
order: 99
title: What if local news was a locals-only club?
subtitle: Paperboy · 2026
story: no
dabbler: yes
credits:
  - Yousef Al-Riyami
  - Kel Huang
caption: Title Image Reference · Satire Image by Frederick Burr Opper, 1894
---

:: ABOVE ::

Copy that appears above the supporting images. Write as many paragraphs as you
like — just leave a blank line between them.

:: BELOW ::

Copy that appears below the supporting images.
```

| Field      | Required | What it does |
|------------|----------|--------------|
| `order`    | optional | Position on the page — lower comes first. Leave it high (or remove it) and the card lands at the end for a maintainer to place. |
| `title`    | yes      | The heading on the card. |
| `subtitle` | yes      | The short line above the title — also the name the card is credited under, so keep it short (e.g. `Paperboy · 2026`). |
| `story`    | yes/no   | `yes` puts the card in the **Stories** gallery. |
| `dabbler`  | yes/no   | `yes` puts the card in the **Dabblers** gallery. |
| `credits`  | optional | The people who made it — one name per line. |
| `caption`  | optional | Small line at the very bottom of the card (credit, date, source). |

`story` and `dabbler` are independent: a card can be in both galleries, or
neither (it still floats on the front page). The body copy goes between the
`:: ABOVE ::` and `:: BELOW ::` markers, and both are optional.

The easiest way to start is to **copy `content/_TEMPLATE/`** and edit the copy.

---

## Credits and the team

If you name someone new in `credits:`, also add them to
[`team/team.csv`](team/team.csv) (one row: name, role, bio, photo filename) and
drop their headshot in `team/`, so their picture and bio show on the Our Team
page and the card links to them. Names must match `team.csv` exactly. If a name
isn't in `team.csv` the card still builds — it just shows the plain name with no
profile link.

---

## Opening a pull request

You can do all of this **entirely in the browser on github.com** — no tools to
install:

1. Fork the repository (button, top right).
2. Open the `content/` folder and use **Add file → Create new file**. Type
   `your-slug/entry.md` — GitHub creates the folder for you — and paste in your
   filled-in `entry.md`.
3. Add your images the same way (**Add file → Upload files** into
   `content/your-slug/main/` and `content/your-slug/supporting/`).
4. **Create a pull request.**

When you open the PR, a check runs automatically and rebuilds the site. If
something in your entry is off (missing image, malformed `entry.md`, and so on)
the check goes red and tells you what to fix. When it's green, a maintainer
reviews and merges.

---

## Previewing locally (optional)

If you'd rather work on your own machine:

```
git clone <your-fork-url>
cd "dabble website/hero-peel"
python3 -m pip install pillow      # one-time
python3 build.py
```

Then open `hero-peel/dabble-hero-peel.html` in a browser. Edit → save →
`python3 build.py` → refresh. `python3 build.py --backend` checks the build can
run at all without building.

Thanks for adding to dabble!

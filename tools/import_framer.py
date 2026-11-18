"""Rebuild src/content/projects/*.md from the measured Framer pages in tools/framer-data/.

    python3 tools/import_framer.py

Each image/video is attached to the text block it sits beside on the Framer page, a picture
that starts level with a section heading becomes that section's side image, and a few
hand-made fixes (PATCHES below) are re-applied afterwards. Running it overwrites the project
files, so make content edits in PATCHES (or stop using this script once you edit by hand).
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "tools", "framer-data")
OUT = os.path.join(ROOT, "src", "content", "projects")

# media that were hidden on the Framer site or that Anja asked to remove
REMOVE = {
    "MLWPbW1dUQawJLhhun3dBwpgJak.mp4",  # Framer's built-in sample video (ocean)
    "uyTxtAj04Uphc1NtwR58OHs43Kk.gif",  # MoMo: last blue/white square gif
}

# slug, grid cover, cursor label, filter categories
CARDS = [
 ("momo", "momo-if-award.jpg", "Modular Physical Therapy | Arduino Coding",
  ["Creative technology", "Experience design", "Process"]),
 ("speculative-product-design", "KAJUbrnVx49dP47BXX8763Q83o.png", "Umeå Institute of Design | Speculative Branding",
  ["UX design", "Digital product design", "Visual design", "Speculative design", "Branding", "Experience design"]),
 ("snm-brand-identity", "ObxAQt3taQcg22O2gcFIEZ9DPM.png", "SNM Copenhagen | Museum Brand Identity",
  ["Visual design", "Branding", "Motion design", "Process"]),
 ("tripcom-design-process", "O3Hv6ku6diOv3bqNOKXid6Ta5rM.png", "Trip.com | CX Journey",
  ["UX design", "Digital product design", "Visual design", "Experience design", "Motion design", "Process"]),
 ("philips-telehealth-interface", "Owi6GMmTQcBiWnNSdmvU9Ug4fj0.png", "Philips Telehealth Interface | UX+UI",
  ["UX design", "Digital product design", "User research", "Experience design", "Process", "Speculative design"]),
 ("applovin-game-marketing-animation", "Bvk2MAxP3ffLzDh9LRXlaZDNeS4.png", "AppLovin | Animated Mobile Game Ads",
  ["Motion design", "Illustration"]),
 ("illustration-and-animation-gallery", "FCdDtzcuuviBweJ3hPZ31on2uk.png", "Illustration and Animation Gallery",
  ["Illustration", "Motion design"]),
 ("rathenau-instituut-creative-research", "6Ic5M3GNZx7jHCUu0gMwpZ1LiOk.png", "Rathenau Instituut | Motion Capture Prototype",
  ["Creative technology", "User research", "Experience design", "Process"]),
 ("quantum-physics-comic", "wfYv1AHzZKAPpf17nJcTzKlO57I.png", "Quantum Physics Comic Fellowship | Illustration",
  ["Illustration", "Visual design"]),
 ("flexecharge-branding", "thf5e8yDLjCiSXzOvo3q6HVNc.png", "FLEXeCHARGE | EV Motion Branding",
  ["Visual design", "Motion design", "Branding"]),
 ("seed-studio-wireframing", "k1IswG1laMMkthqP9yoHnISj0.png", "SEED Design Studio | Clickable Wireframing",
  ["UX design", "Digital product design", "Process"]),
]
FEATURED = ["philips-telehealth-interface", "momo", "applovin-game-marketing-animation",
            "seed-studio-wireframing", "rathenau-instituut-creative-research"]

# hand-made fixes applied to the finished page body: slug -> [(find, replace), ...]
PATCHES = {
    "momo": [  # give the numbered steps a Process heading like the other pages
        ('<div class="step">\n<div class="step-text">\n<h3>01 Mind mapping',
         '</section>\n\n<section class="sec">\n<header class="sec-head">\n<p class="pill pill-label">Design process</p>\n'
         '<h2>Process</h2>\n</header>\n\n<div class="step">\n<div class="step-text">\n<h3>01 Mind mapping'),
    ],
    "rathenau-instituut-creative-research": [
        ('<div class="step">\n<div class="step-text">\n<h3>01 Aligning',
         '</section>\n\n<section class="sec">\n<header class="sec-head">\n<p class="pill pill-label">Design process</p>\n'
         '<h2>Process</h2>\n</header>\n\n<div class="step">\n<div class="step-text">\n<h3>01 Aligning'),
    ],
    "applovin-game-marketing-animation": [
        ("Check out a storyboard I made to the left to convey a concept to the team.",
         "Check out this storyboard I put together to convey a new concept to the team."),
        # the small sword sits in the text column under the paragraph, as on Framer
        ('<div class="gallery">\n<img src="/media/8jZKKw7w1jnRSaFljsjwUaQnqoA.png" alt="" loading="lazy" />\n</div>\n', ''),
        ("Here is one example of such an asset and animation.</p>\n</div>",
         "Here is one example of such an asset and animation.</p>\n"
         '<img class="media-small" src="/media/8jZKKw7w1jnRSaFljsjwUaQnqoA.png" alt="Illustrated sword game asset" loading="lazy" />\n</div>'),
    ],
    "seed-studio-wireframing": [
        # the two clickable Figma prototypes embedded on the Framer page
        ("<p>[Prototypes may take longer to load.]</p>\n</div>",
         "<p>[Prototypes may take longer to load.]</p>\n</div>\n\n"
         '<div class="embed"><iframe title="Clickable wireframe (Figma prototype)" loading="lazy" allowfullscreen '
         'src="https://embed.figma.com/proto/pVb7oWriOTp0y9TsHh6Tns/moongallery.eu?kind=proto&amp;node-id=38-267&amp;page-id=0%3A1&amp;scaling=scale-down&amp;starting-point-node-id=38%3A267&amp;type=design&amp;embed-host=share"></iframe></div>\n\n'
         '<div class="embed"><iframe title="High-fidelity prototype (Figma prototype)" loading="lazy" allowfullscreen '
         'src="https://embed.figma.com/proto/pVb7oWriOTp0y9TsHh6Tns/moongallery.eu?kind=proto&amp;node-id=305-2889&amp;page-id=214%3A2286&amp;scaling=scale-down&amp;starting-point-node-id=305%3A2889&amp;type=design&amp;content-scaling=responsive&amp;embed-host=share"></iframe></div>'),
    ],
}

# ---------- site-wide consistency: sentence case for headings, labels and tags ----------
HEADINGS = {  # <h2>/<h3> text -> new text
    "At a Glance": "At a glance", "The Challenge": "The challenge", "Challenge": "The challenge",
    "The Situation": "The challenge", "Examples": "Process",
    "07 UI Focus: Prioritization": "07 UI focus: prioritization", "08 UI Focus: Communication": "08 UI focus: communication",
    "09 Feedback Session": "09 Feedback session", "01 Meeting the Researchers": "01 Meeting the researchers",
    "02 Co-Creation": "02 Co-creation", "03 Illustration Iteration": "03 Illustration iteration",
    "02 Hand Sketches": "02 Hand sketches", "03 UI Design": "03 UI design", "03 Asset Illustration": "03 Asset illustration",
    "04 Modules": "06 Modules",  # MoMo numbering went 01-05 then 04 again
}
LABELS = {"Design Process": "Design process", "Design Work": "Design process", "Documentation": None}  # None = drop
TAGS = {  # tag -> replacement tag(s)
    "UX": ["UX design"], "UI": ["UI design"], "UX/UI": ["UX design", "UI design"], "CX": ["CX design"],
    "UX Design": ["UX design"], "UI Design": ["UI design"],
    "Motion Graphics": ["Motion graphics"], "Motion Design": ["Motion design"], "A/B Testing": ["A/B testing"],
    "Design systems": ["Design system"], "Design System": ["Design system"],
    "Product Design": ["Product design"], "Sound Design": ["Sound design"], "Interaction Design": ["Interaction design"],
    "Arduino Electronics": ["Arduino electronics"], "Design for Healthcare": ["Design for healthcare"],
    "Service Design": ["Service design"], "Design Ethnography": ["Design ethnography"], "Co-Creation": ["Co-creation"],
    "Inter-Disciplinary Design": ["Interdisciplinary design"], "Motion Capture": ["Motion capture"],
    "User Testing": ["User testing"], "Political Science": ["Political science"], "Figma Prototyping": ["Figma prototyping"],
    "Visual Design": ["Visual design"], "Type Design": ["Type design"], "Logo Design": ["Logo design"],
    "Graphic Design": ["Graphic design"], "Speculative Design": ["Speculative design"],
    "Customer Journey": ["Customer journey"], "User Personas": ["User personas"], "Success Metrics": ["Success metrics"],
    "Design Hypotheses": ["Design hypotheses"],
}
TYPOS = {"menas": "means", "an such asset": "such an asset", "teammembers": "team members",
         "interactions design": "interaction design"}
EYEBROW = {"flexecharge-branding": "FLEXeCHARGE", "tripcom-design-process": "Trip.com interview task"}  # was "Umeå Institute of Design" on Framer, but it was a work project
# the "Too long, didn't read?" row: same wording pattern on every project page, linking to the final result
TLDR = {
    "momo": "Keep scrolling to see the final prototype",
    "speculative-product-design": "Keep scrolling to see how the ticketer works",
    "snm-brand-identity": "Keep scrolling to see the final product",
    "tripcom-design-process": "Keep scrolling to see the final product",
    "philips-telehealth-interface": "Keep scrolling to see the final interfaces",
    "applovin-game-marketing-animation": "Keep scrolling to see the work",
    "rathenau-instituut-creative-research": "Keep scrolling to see the final experience",
    "quantum-physics-comic": "Keep scrolling to read the whole comic",
    "flexecharge-branding": "Keep scrolling to see the work",
    "seed-studio-wireframing": "Keep scrolling to try the clickable prototypes",
}

STAR = {"situation", "problem", "action", "result", "task"}
GENERIC_ALT = {"design pic", "process pic", "project img", "profile pic"}
HEAD = ("h1", "h2", "h3", "h5", "h6")
MOUSE = ('<svg class="hero-mouse" viewBox="0 0 28 42" width="28" height="42" aria-hidden="true">'
         '<rect x="7" y="9" width="14" height="24" rx="7" fill="none" stroke="currentColor" stroke-width="1.5" />'
         '<line class="wheel" x1="14" y1="14" x2="14" y2="18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" /></svg>')


def plain(t): return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
def m(src): return "/media/" + os.path.basename(src)
def q(t): return json.dumps(t, ensure_ascii=False)
def is_media(x): return x["t"] in ("img", "video")


def media_html(x):
    if x["t"] == "img":
        alt = "" if x.get("alt") in GENERIC_ALT or not x.get("alt") else html.escape(x["alt"])
        return f'<img src="{m(x["src"])}" alt="{alt}" loading="lazy" />'
    return f'<video src="{m(x["src"])}" muted loop playsinline preload="metadata" data-autoplay></video>'


def media_block(run, cls):
    """Images/videos in rows, as on Framer: items that start at the same height sit side by side."""
    if not run: return ""
    rows = []
    for r in run:
        if rows and abs(rows[-1][0]["top"] - r["top"]) < 40: rows[-1].append(r)
        else: rows.append([r])
    # merge consecutive single-item rows of similar width into one stacked block
    out = []
    for row in rows:
        n = min(len(row), 3)
        c = f"{cls} {cls}-{n}" if n > 1 else cls
        out.append(f'<div class="{c}">\n' + "\n".join(media_html(r) for r in row) + "\n</div>")
    return "\n\n".join(out)


def text_html(items):
    out, ul = [], []
    def flush():
        if ul: out.append("<ul>\n" + "\n".join(f"<li>{t}</li>" for t in ul) + "\n</ul>"); ul.clear()
    for x in items:
        t = x["text"]
        if plain(t) == "": continue
        if x.get("href") and x["href"].startswith("./"): continue
        if x.get("href"): t = f'<a href="{html.escape(x["href"])}" target="_blank" rel="noopener">{t}</a>'
        if x.get("li"): ul.append(t)
        else: flush(); out.append(f"<p>{t}</p>")
    flush()
    return "\n".join(out)


def star_html(cells, stacked):
    parts = []
    for h, ps in cells:
        k = plain(h).lower()
        parts.append(f'<div class="star-card" data-k="{k if k in STAR else "other"}">\n<h4>{h}</h4>\n{text_html(ps)}\n</div>')
    return f'<div class="star{" star-stack" if stacked else ""}">\n' + "\n".join(parts) + "\n</div>"


def is_label(items, i):
    """A short line right before a section title is that section's pill label."""
    x = items[i]
    return (x["t"] == "p" and not x.get("li") and len(plain(x["text"])) <= 40
            and i + 1 < len(items) and items[i + 1]["t"] == "h2")


# ---------- step 1: attach every image/video to the text block it sits beside ----------
def sequence(body):
    texts = [x for x in body if not is_media(x)]
    media = [x for x in body if is_media(x)]
    blocks = []
    i = 0
    while i < len(texts):
        x = texts[i]
        b = {"items": [x], "is_section": False}
        if is_label(texts, i):
            b["items"].append(texts[i + 1]); i += 1
        if b["items"][-1]["t"] == "h2": b["is_section"] = True
        i += 1
        # paragraphs that follow a heading belong to it
        if b["items"][0]["t"] in HEAD + ("h4",) or b["is_section"]:
            while i < len(texts) and texts[i]["t"] == "p" and not is_label(texts, i):
                b["items"].append(texts[i]); i += 1
        else:
            while i < len(texts) and texts[i]["t"] == "p" and not is_label(texts, i):
                b["items"].append(texts[i]); i += 1
        blocks.append(b)
    for b in blocks:
        vis = [x for x in b["items"] if x["h"] > 0] or b["items"]
        b["top"] = min(x["top"] for x in vis); b["bot"] = max(x["top"] + x["h"] for x in vis)
        b["left"] = min(x["left"] for x in vis); b["right"] = max(x["left"] + x["w"] for x in vis)
        b["media"], b["side"] = [], []

    # media stacked in one column (same left edge, small vertical gaps) travel together
    stacks = []
    for x in sorted(media, key=lambda r: (r["left"] // 20, r["top"])):
        s = stacks[-1] if stacks else None
        if s and abs(s[-1]["left"] - x["left"]) <= 12 and 0 <= x["top"] - (s[-1]["top"] + s[-1]["h"]) < 60 \
                and abs(s[-1]["w"] - x["w"]) < 40:
            s.append(x)
        else:
            stacks.append([x])
    for st in stacks:
        mt, mb = st[0]["top"], st[-1]["top"] + st[-1]["h"]
        best, score = None, None
        for b in blocks:
            ov = min(mb, b["bot"]) - max(mt, b["top"])
            if ov > 0 and (score is None or ov > score): best, score = b, ov
        if best is None:  # no overlap: it belongs to the text above it
            above = [b for b in blocks if b["top"] <= mt]
            best = above[-1] if above else blocks[0]
        # a picture that starts level with a section title, beside it, is that section's side image
        sec = next((b for b in blocks if b["is_section"] and abs(b["top"] - mt) < 150
                    and (st[0]["left"] + st[0]["w"] <= b["left"] + 10 or st[0]["left"] >= b["right"] - 10)), None)
        if sec and (best is sec or best["items"][0]["t"] == "h4"):
            sec["side"] += st; continue
        best["media"] += st

    seq = []
    for b in blocks:
        for r in sorted(b["side"], key=lambda r: (r["top"], r["left"])): r["_side"] = True; seq.append(r)
        seq += b["items"]
        for r in sorted(b["media"], key=lambda r: (r["top"], r["left"])):
            # beside the text (another column) or underneath it (overlapping the text column)
            r["_below"] = not (r["left"] + r["w"] <= b["left"] + 10 or r["left"] >= b["right"] - 10)
            r["_left"] = r["left"] + r["w"] / 2 < b["left"]
            seq.append(r)
    return seq


# ---------- step 2: turn the sequence into the page layout ----------
def render(rest, slug=''):
    # pull out the "Too long, didn't read?" line; it is drawn once, above the At a Glance box
    hint = None
    for i, x in enumerate(rest):
        if x["t"] == "p" and plain(x["text"]).lower().startswith("too long"):
            nxt = rest[i + 1] if i + 1 < len(rest) and rest[i + 1]["t"] == "p" else None
            hint = (plain(x["text"]), plain(nxt["text"]) if nxt else "")
            rest = [y for y in rest if y is not x and y is not nxt]
            break
    if slug in TLDR: hint = ("Too long, didn't read?", TLDR[slug])
    hint_html = ""
    if hint:
        hint_html = (f'<div class="tldr-row"><a class="tldr" href="#output"><span>{html.escape(hint[0])}</span>'
                     f'<span class="hero-hint-line"></span>{MOUSE}<span class="hero-hint-line"></span>'
                     f'<span>{html.escape(hint[1])}</span></a></div>')

    blocks, cur = [], {"kind": "prelude", "items": []}
    k = 0
    while k < len(rest):
        x = rest[k]
        starts_label = is_label(rest, k)
        if starts_label or x["t"] == "h2":
            side = []
            while cur["items"] and is_media(cur["items"][-1]) and cur["items"][-1].get("_side"):
                side.insert(0, cur["items"].pop())
            blocks.append(cur)
            cur = {"kind": "section", "label": None, "title": None, "side": side, "items": []}
            if starts_label: cur["label"] = x["text"]; k += 1
            cur["title"] = rest[k]["text"]; k += 1
            if k < len(rest) and rest[k]["t"] == "p" and len(plain(rest[k]["text"])) < 200 and not rest[k].get("li"):
                cur["sub"] = rest[k]["text"]; k += 1
            continue
        cur["items"].append(x); k += 1
    blocks.append(cur)
    if len(blocks) == 1: blocks[0]["kind"] = "plain"

    html_out = []
    hint_used = False
    def put_hint():
        nonlocal hint_used
        if hint_html and not hint_used: hint_used = True; return [hint_html]
        return []

    for b in blocks:
        items = b["items"]
        body, i, star_cells = [], 0, []
        glance = b["kind"] == "prelude"; seen_title = False; gl_body = None
        while i < len(items):
            x = items[i]
            if glance and (x["t"] == "h4" or (x["t"] in HEAD and seen_title)):
                glance = False; gl_body = body; body = []
            if x["t"] == "h4":
                cells = []
                while i < len(items) and items[i]["t"] == "h4":
                    h = items[i]; i += 1; ps = []
                    while i < len(items) and items[i]["t"] == "p": ps.append(items[i]); i += 1
                    cells.append((h, ps))
                cells.sort(key=lambda c: (c[0]["top"] // 60, c[0]["left"]))
                star_cells = [(h["text"], ps) for h, ps in cells]
                if not (b["kind"] == "section" and b["side"]):
                    body.append(star_html(star_cells, False)); star_cells = []
                continue
            if x["t"] in HEAD:
                title = x["text"]; i += 1; ps = []
                while i < len(items) and items[i]["t"] == "p": ps.append(items[i]); i += 1
                run = []
                while i < len(items) and is_media(items[i]): run.append(items[i]); i += 1
                anchor = '<div id="animation"></div>\n' if plain(title).startswith("Selected animated") else ""
                if glance:
                    seen_title = True
                    body.append(f'<h3 class="glance-title">{title}</h3>')
                    if run: body.append(media_block(run, "glance-media"))
                    if ps: body.append(f'<div class="prose-text">\n{text_html(ps)}\n</div>')
                    continue
                if not ps:
                    body.append(f'{anchor}<h3 class="sub-head">{title}</h3>')
                    if run: body.append(media_block(run, "gallery"))
                    continue
                beside = [r for r in run if not r.get("_below")]
                below = [r for r in run if r.get("_below")]
                text = f'<div class="step-text">\n<h3>{title}</h3>\n{text_html(ps)}\n</div>'
                if beside:
                    flip = " step-flip" if beside[0].get("_left") else ""
                    body.append(f'<div class="step{flip}">\n{text}\n<div class="step-media">\n'
                                + "\n".join(media_html(r) for r in beside) + '\n</div>\n</div>')
                else:
                    body.append(f'<div class="step step-solo">\n{text}\n</div>')
                if below: body.append(media_block(below, "gallery"))
                continue
            if is_media(x):
                run = []
                while i < len(items) and is_media(items[i]): run.append(items[i]); i += 1
                body.append(media_block(run, "glance-media" if glance else "gallery"))
                continue
            if x["t"] != "p": i += 1; continue
            ps = []
            while i < len(items) and items[i]["t"] == "p": ps.append(items[i]); i += 1
            t = text_html(ps)
            if t: body.append(f'<div class="prose-text">\n{t}\n</div>')

        if b["kind"] == "plain":
            html_out.append('<section class="sec">\n' + "\n\n".join(put_hint() + body) + "\n</section>"); continue
        if b["kind"] == "prelude":
            g = gl_body if gl_body is not None else body
            if g:
                html_out += put_hint()
                html_out.append('<section class="glance">\n' + "\n\n".join(g) + "\n</section>")
            if gl_body is not None and body:
                html_out += put_hint()
                html_out.append('<section class="sec">\n' + "\n\n".join(body) + "\n</section>")
            continue
        html_out += put_hint()
        sid = ' id="output"' if plain(b["title"]).lower() == "output" else ""
        head = []
        if b["label"]: head.append(f'<p class="pill pill-label">{b["label"]}</p>')
        head.append(f'<h2>{b["title"]}</h2>')
        if b.get("sub"): head.append(f'<p class="sec-sub">{b["sub"]}</p>')
        if b["side"]:
            right = "\n".join(head) + ("\n" + star_html(star_cells, True) if star_cells else "")
            html_out.append(f'<section class="sec"{sid}>\n<div class="sec-split">\n<div class="sec-side">\n'
                            + "\n".join(media_html(r) for r in b["side"]) + '\n</div>\n<div class="sec-main">\n'
                            + right + "\n</div>\n</div>\n\n" + "\n\n".join(body) + "\n</section>")
        else:
            html_out.append(f'<section class="sec"{sid}>\n<header class="sec-head">\n' + "\n".join(head) + "\n</header>\n\n"
                            + "\n\n".join(body) + "\n</section>")
    out = "\n\n".join(html_out)
    if hint_html and 'id="output"' not in out:  # no Output section: the row links to the last section
        i = out.rfind('<section class="sec">')
        if i >= 0: out = out[:i] + '<section class="sec" id="output">' + out[i + len('<section class="sec">'):]
    return out


def polish(body):
    for a, b in HEADINGS.items():
        body = body.replace(f"<h2>{a}</h2>", f"<h2>{b}</h2>").replace(f"<h3>{a}</h3>", f"<h3>{b}</h3>")
        body = body.replace(f'<h3 class="glance-title">{a}</h3>', f'<h3 class="glance-title">{b}</h3>')
    for a, b in LABELS.items():
        body = body.replace(f'<p class="pill pill-label">{a}</p>\n', "" if b is None else f'<p class="pill pill-label">{b}</p>\n')
    for a, b in TYPOS.items(): body = body.replace(a, b)
    return body


def build(order, slug, cover, label, cats):
    items = json.load(open(os.path.join(DATA, f"{slug}.json")))
    items = [x for x in items
             if not (x["t"] == "p" and plain(x["text"]) == "Let's connect!")
             and not (x["t"][0] == "h" and plain(x.get("text", "")).startswith("Curious to learn more"))
             and not (is_media(x) and (os.path.basename(x["src"]) in REMOVE or not x["src"] or (x["w"] < 60 and x["h"] < 60)))]
    # drop media sitting completely underneath a later image/video (hidden on the Framer page)
    med = [x for x in items if is_media(x)]
    covered = set()
    for ai, a in enumerate(med):
        for b in med[ai + 1:]:
            if (b["left"] - 12 <= a["left"] and b["top"] - 12 <= a["top"] and a["w"] > 0
                    and b["left"] + b["w"] + 12 >= a["left"] + a["w"] and b["top"] + b["h"] + 12 >= a["top"] + a["h"]):
                covered.add(id(a)); break
    items = [x for x in items if id(x) not in covered]

    i = 0; fm = {"eyebrow": "", "title": "", "summary": "", "team": "", "tags": []}
    while i < len(items) and items[i]["t"] != "h2": fm["eyebrow"] = plain(items[i].get("text", "")); i += 1
    fm["title"] = " ".join(plain(items[i]["text"]).split()); i += 1
    while i < len(items) and items[i]["t"] == "p":
        t = plain(items[i]["text"])
        if items[i].get("href"): pass
        elif not fm["summary"]: fm["summary"] = t
        elif t.startswith("Team"): fm["team"] = t
        else: fm["tags"].append(t)
        i += 1
    hero = None
    if i < len(items) and is_media(items[i]): hero = items[i]; i += 1
    body = polish(render(sequence(items[i:]), slug))
    for a, b in PATCHES.get(slug, []):
        if a not in body: print(f"  ! patch not applied on {slug}: {a[:50]}")
        body = body.replace(a, b)
    fm["eyebrow"] = EYEBROW.get(slug, fm["eyebrow"])
    fm["tags"] = [n for t in fm["tags"] for n in TAGS.get(t, [t])]
    fm["summary"] = polish(fm["summary"])
    lines = ["---", f"title: {q(fm['title'])}", f"eyebrow: {q(fm['eyebrow'])}", f"summary: {q(fm['summary'])}"]
    if fm["team"]: lines.append(f"team: {q(fm['team'])}")
    lines.append("tags: [" + ", ".join(q(t) for t in fm["tags"]) + "]")
    if hero: lines += [f"hero: {q(m(hero['src']))}", f"heroType: {hero['t']}"]
    lines += [f"cover: {q('/media/' + cover)}", f"categories: {json.dumps(cats, ensure_ascii=False)}",
              f"cursorLabel: {q(label)}", f"order: {order}"]
    if slug in FEATURED: lines.append(f"featured: {FEATURED.index(slug)}")
    lines.append("---")
    open(os.path.join(OUT, f"{slug}.md"), "w").write("\n".join(lines) + "\n\n" + body + "\n")
    n_steps = body.count('class="step'); n_media = body.count('<img') + body.count('<video')
    print(f"{slug}: {n_steps} steps, {n_media} media")


if __name__ == "__main__":
    only = os.environ.get("ONLY")
    for order, (slug, cover, label, cats) in enumerate(CARDS):
        if slug == "illustration-and-animation-gallery" and not only:
            continue  # hand-edited page (dark animation section); run with ONLY=... to rebuild it
        if only and slug != only: continue
        build(order, slug, cover, label, cats)

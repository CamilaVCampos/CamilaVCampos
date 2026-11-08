"""Generates the GitHub profile README and its SVG cards (light + dark).

Edit the CONTENT section, then run:  python build.py
Requires: pip install fonttools brotli
"""
import base64
import html
import io
import math
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).parent
FONT_PATH = ROOT / "fonts" / "Outfit-latin.woff2"
ICONS = ROOT / "icons"
ASSETS = ROOT / "assets"
W = 840

# ───────────────────────────── CONTENT ─────────────────────────────
USER = "CamilaVCampos"
LINKEDIN = "https://www.linkedin.com/in/camilavcampos"

HERO = {
    "greeting": "Hi, I'm Camila Campos",
    "role": "Data Scientist",
    "tagline": "Turning data into models, dashboards & web apps",
    "chips": [("ms_location_on", "Mexico City"), ("ms_school", "ESCOM · IPN"), ("ms_cloud", "Learning Azure")],
}

ABOUT = [
    ("ms_school", "Data Science student at ESCOM, Instituto Politécnico Nacional"),
    ("ms_psychology", "Into machine learning, NLP and time-series forecasting"),
    ("ms_bar_chart", "I enjoy building data pipelines and dashboards that tell a story"),
    ("ms_cloud", "Currently learning cloud & AI on Microsoft Azure"),
    ("ms_translate", "Spanish (native) · English · a bit of German"),
]

STACK = [
    ("Languages", [("python", "Python"), ("c", "C"), ("ms_database", "SQL"), ("javascript", "JavaScript"),
                   ("html5", "HTML"), ("css", "CSS")]),
    ("Data & ML", [("pandas", "pandas"), ("numpy", "NumPy"), ("scikitlearn", "scikit-learn"), ("jupyter", "Jupyter")]),
    ("BI & tools", [("powerbi", "Power BI"), ("tableau", "Tableau"), ("git", "Git")]),
    ("Learning", [("microsoftazure", "Microsoft Azure")]),
]

PROJECTS = [
    {
        "repo": "proyecto-ai901-rio-claro",
        "title": "Río Claro AI Agents",
        "icon": "ms_smart_toy",
        "desc": "Prototype of three AI assistants built with Microsoft Foundry, "
                "served through a Flask web app deployed on Azure App Service.",
        "tags": ["Azure", "Flask", "AI agents"],
    },
    {
        "repo": "hackathon-ine-prediccion-abstencion",
        "title": "INE Abstention Forecast",
        "icon": "ms_how_to_vote",
        "desc": "Hackathon project (INE 2026) that forecasts municipal abstention for "
                "Mexico's 2027 election, with risk levels and a Tableau dashboard.",
        "tags": ["Python", "Jupyter", "Tableau"],
    },
]

BUTTONS = [
    ("linkedin", "LinkedIn", LINKEDIN, True),
    ("github", "All repositories", f"https://github.com/{USER}?tab=repositories", False),
]

# ───────────────────────────── THEME ─────────────────────────────
PALETTES = {
    "light": dict(card="#FFF4EE", chip="#FFE1D3", container="#FFD6C4", strong="#FFB59E",
                  primary="#B3432A", onprimary="#FFFFFF", text="#38221B", muted="#7D5F54",
                  sun="#FFC98A"),
    "dark": dict(card="#2B1E19", chip="#3D2A22", container="#5A2E22", strong="#7E3D29",
                 primary="#FFB59E", onprimary="#561A08", text="#FCE7DE", muted="#D6BEB3",
                 sun="#E8AE62"),
}

CSS = """
text{font-family:'Outfit','Segoe UI',Roboto,Helvetica,Arial,sans-serif}
.a{animation:rise .8s cubic-bezier(.2,.8,.2,1) both}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
.pop{animation:pop .8s cubic-bezier(.3,1.5,.5,1) both;transform-box:fill-box;transform-origin:center}
@keyframes pop{from{opacity:0;transform:scale(.5)}to{opacity:1;transform:none}}
.grow{animation:grow 1s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:bottom}
@keyframes grow{from{transform:scaleY(0)}to{transform:none}}
.mark{animation:mark .9s cubic-bezier(.2,.8,.2,1) both;transform-box:fill-box;transform-origin:left}
@keyframes mark{from{transform:scaleX(0)}to{transform:none}}
.draw{stroke-dasharray:1000;animation:draw 1.6s ease-out both}
@keyframes draw{from{stroke-dashoffset:1000}to{stroke-dashoffset:0}}
.float{animation:float 6s ease-in-out infinite}
@keyframes float{50%{transform:translateY(-6px)}}
.flow{animation:flow 5s linear infinite}
@keyframes flow{to{transform:translateX(-80px)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""

# ───────────────────────────── HELPERS ─────────────────────────────
_instances = {}


def _font_at(weight):
    if weight not in _instances:
        _instances[weight] = instancer.instantiateVariableFont(TTFont(FONT_PATH), {"wght": weight})
    return _instances[weight]


def tw(s, size, weight=400):
    """Width of a string in px, measured from the real font."""
    f = _font_at(weight)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), cmap[32])][0] for c in s) * size / upm


def wrap(s, size, weight, maxw):
    lines, cur = [], ""
    for word in s.split():
        test = f"{cur} {word}".strip()
        if tw(test, size, weight) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def font_face(chars):
    f = TTFont(FONT_PATH)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)))
    sub.subset(f)
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'Outfit';src:url(data:font/woff2;base64,{b64}) format('woff2');font-weight:100 900}}"


_icon_cache = {}


def icon(name, x, y, size, fill):
    if name not in _icon_cache:
        src = (ICONS / f"{name}.svg").read_text(encoding="utf-8")
        vb = re.search(r'viewBox="([^"]+)"', src).group(1)
        paths = re.findall(r'\sd="([^"]+)"', src)
        _icon_cache[name] = (vb, paths)
    vb, paths = _icon_cache[name]
    body = "".join(f'<path d="{d}"/>' for d in paths)
    return f'<svg x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" viewBox="{vb}" fill="{fill}">{body}</svg>'


def cookie(cx, cy, r, amp, lobes, steps=240):
    pts = []
    for i in range(steps):
        th = 2 * math.pi * i / steps
        rr = r + amp * math.cos(lobes * th)
        pts.append(f"{cx + rr * math.cos(th):.2f},{cy + rr * math.sin(th):.2f}")
    return "M" + " L".join(pts) + "Z"


def esc(s):
    return html.escape(s, quote=True)


class Svg:
    def __init__(self, w, h, pal, label):
        self.w, self.h, self.p, self.label = w, h, pal, label
        self.parts, self.chars = [], set(" ")

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size, weight=400, fill=None, anchor="start", attrs=""):
        self.chars |= set(s)
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
                 f'fill="{fill or self.p["text"]}" text-anchor="{anchor}"{attrs}>{esc(s)}</text>')

    def render(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{self.h:.0f}" '
                f'viewBox="0 0 {self.w:.0f} {self.h:.0f}" role="img" aria-label="{esc(self.label)}">'
                f'<title>{esc(self.label)}</title><style>{font_face(self.chars)}{CSS}</style>'
                + "".join(self.parts) + "</svg>")


def delay(s):
    return f' style="animation-delay:{s:.2f}s"'


def chip(svg, x, y, ic, label, h=36, size=15, fill=None, fg=None, stroke=None, d=0.0):
    p = svg.p
    w = 14 + 18 + 8 + tw(label, size, 500) + 16
    st = f' stroke="{stroke}" stroke-width="1.5" stroke-dasharray="5 4"' if stroke else ""
    svg.add(f'<g class="a"{delay(d)}><rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{fill or p["chip"]}"{st}/>')
    svg.add(icon(ic, x + 14, y + (h - 18) / 2, 18, p["primary"]))
    svg.text(x + 40, y + h / 2 + size * 0.36, label, size, 500, fg)
    svg.add("</g>")
    return w


def section_title(svg, ic, title, x=40, y=34):
    p = svg.p
    circle = f'<circle cx="{x + 22}" cy="{y + 22}" r="22" fill="{p["container"]}"/>'
    svg.add(f'<g class="pop">{circle}{icon(ic, x + 10, y + 10, 24, p["primary"])}</g>')
    svg.text(x + 58, y + 30, title, 24, 700, attrs=' class="a"')


# ───────────────────────────── CARDS ─────────────────────────────
def hero(p):
    h = 290
    s = Svg(W, h, p, HERO["greeting"])
    s.add(f'<defs><clipPath id="c"><rect width="{W}" height="{h}" rx="32"/></clipPath></defs>')
    s.add(f'<rect width="{W}" height="{h}" rx="32" fill="{p["card"]}"/>')
    s.add(f'<g clip-path="url(#c)"><circle cx="790" cy="300" r="150" fill="{p["chip"]}"/>'
          f'<circle cx="610" cy="-30" r="70" fill="{p["chip"]}" opacity=".7"/></g>')

    # Scallop "cookie" with a tiny bar chart: a little data motif
    cx, cy = 690, 140
    s.add(f'<g class="pop"{delay(.1)}><path d="{cookie(cx, cy, 86, 6, 10)}" fill="{p["strong"]}">'
          f'<animateTransform attributeName="transform" type="rotate" from="0 {cx} {cy}" to="360 {cx} {cy}" '
          f'dur="60s" repeatCount="indefinite"/></path></g>')
    heights, bw, gap, base = [30, 52, 40, 74], 16, 10, 180
    x0 = cx - (4 * bw + 3 * gap) / 2
    tops = []
    for i, bh in enumerate(heights):
        bx = x0 + i * (bw + gap)
        s.add(f'<rect class="grow" x="{bx:.1f}" y="{base - bh}" width="{bw}" height="{bh}" rx="5" '
              f'fill="{p["primary"]}"{delay(.4 + i * .1)}/>')
        tops.append((bx + bw / 2, base - bh - 12))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in tops)
    s.add(f'<polyline class="draw" pathLength="1000" points="{line}" fill="none" stroke="{p["sun"]}" '
          f'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"{delay(.9)}/>')
    for i, (x, y) in enumerate(tops):
        s.add(f'<circle class="pop" cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{p["sun"]}" '
              f'stroke="{p["strong"]}" stroke-width="2"{delay(1.0 + i * .15)}/>')
    for x, y, r, c, d in [(578, 62, 6, "sun", .3), (806, 52, 5, "primary", .5),
                          (590, 238, 7, "container", .6), (800, 236, 5, "sun", .7)]:
        s.add(f'<g class="float"{delay(d)}><circle class="pop" cx="{x}" cy="{y}" r="{r}" '
              f'fill="{p[c]}"{delay(d)}/></g>')

    # Text
    s.text(44, 88, HERO["greeting"], 42, 700, attrs=' class="a"')
    rw = tw(HERO["role"], 40, 700)
    s.add(f'<rect class="mark" x="40" y="128" width="{rw + 10:.1f}" height="20" rx="10" '
          f'fill="{p["container"]}"{delay(.5)}/>')
    s.text(44, 144, HERO["role"], 40, 700, p["primary"], attrs=f' class="a"{delay(.15)}')
    s.text(44, 186, HERO["tagline"], 19, 400, p["muted"], attrs=f' class="a"{delay(.3)}')
    x = 44
    for i, (ic, label) in enumerate(HERO["chips"]):
        x += chip(s, x, 218, ic, label, d=.45 + i * .1) + 10
    return s


def about(p):
    top, step = 112, 38
    h = top + (len(ABOUT) - 1) * step + 40
    s = Svg(W, h, p, "About me")
    s.add(f'<defs><clipPath id="c"><rect width="{W}" height="{h}" rx="32"/></clipPath></defs>')
    s.add(f'<rect width="{W}" height="{h}" rx="32" fill="{p["card"]}"/>')
    s.add(f'<g clip-path="url(#c)"><path class="pop" d="{cookie(800, h + 10, 110, 7, 9)}" '
          f'fill="{p["chip"]}"/></g>')
    section_title(s, "ms_person", "About me")
    for i, (ic, line) in enumerate(ABOUT):
        y = top + i * step
        s.add(f'<g class="a"{delay(.15 + i * .08)}>')
        s.add(icon(ic, 50, y - 16, 21, p["primary"]))
        s.text(84, y, line, 17, 400)
        s.add("</g>")
    return s


def stack(p):
    s_parts = []
    x0, maxx, rowh = 176, W - 36, 52
    rows, y, d = [], 100, .1
    for label, items in STACK:
        x = x0
        placed = []
        for ic, name in items:
            cw = 14 + 18 + 8 + tw(name, 15, 500) + 16
            if x + cw > maxx:
                x, y = x0, y + rowh
            placed.append((x, y, ic, name))
            x += cw + 8
        rows.append((label, placed))
        y += rowh
    h = y + 10
    s = Svg(W, h, p, "Tech stack")
    s.add(f'<rect width="{W}" height="{h}" rx="32" fill="{p["card"]}"/>')
    section_title(s, "ms_code", "Tech stack")
    for gi, (label, placed) in enumerate(rows):
        ly = placed[0][1]
        s.text(48, ly + 24, label.upper(), 13, 600, p["muted"], attrs=f' letter-spacing="1.4" class="a"{delay(d)}')
        learning = label == "Learning"
        for (x, y, ic, name) in placed:
            chip(s, x, y, ic, name, h=38,
                 fill=p["card"] if learning else None,
                 stroke=p["primary"] if learning else None,
                 fg=p["primary"] if learning else None, d=d)
            d += .04
    return s


def projects_title(p):
    s = Svg(W, 84, p, "Featured projects")
    s.add(f'<rect width="{W}" height="84" rx="32" fill="{p["card"]}"/>')
    section_title(s, "ms_folder_open", "Featured projects", x=40, y=20)
    return s


def project_layout():
    cw = 410
    descs = [wrap(pr["desc"], 15, 400, cw - 64) for pr in PROJECTS]
    lines = max(len(d) for d in descs)
    h = 154 + (lines - 1) * 21 + 26 + 28 + 28
    return cw, h, descs


def project(p, i):
    pr = PROJECTS[i]
    cw, h, descs = project_layout()
    s = Svg(cw, h, p, pr["title"])
    s.add(f'<rect width="{cw}" height="{h}" rx="28" fill="{p["card"]}"/>')
    s.add(f'<g class="pop"><circle cx="58" cy="58" r="26" fill="{p["container"]}"/>'
          f'{icon(pr["icon"], 44, 44, 28, p["primary"])}</g>')
    s.add(f'<g class="pop"{delay(.2)}><circle cx="{cw - 52}" cy="52" r="20" fill="{p["chip"]}"/>'
          f'{icon("ms_arrow_outward", cw - 63, 41, 22, p["text"])}</g>')
    s.text(32, 124, pr["title"], 22, 700, attrs=f' class="a"{delay(.1)}')
    for li, line in enumerate(descs[i]):
        s.text(32, 154 + li * 21, line, 15, 400, p["muted"], attrs=f' class="a"{delay(.2)}')
    ty = h - 28 - 28
    x = 32
    s.add(f'<g class="a"{delay(.35)}>')
    for t in pr["tags"]:
        w = tw(t, 13, 500) + 24
        s.add(f'<rect x="{x}" y="{ty}" width="{w:.1f}" height="28" rx="14" fill="{p["chip"]}"/>')
        s.text(x + 12, ty + 18.5, t, 13, 500)
        x += w + 8
    s.add("</g>")
    return s


def wave(p):
    h = 44
    s = Svg(W, h, p, "")
    pts, period = [], 80
    for i in range(0, W + 2 * period + 1, 4):
        pts.append(f"{i:.0f},{h / 2 + 7 * math.sin(2 * math.pi * i / period):.2f}")
    s.add('<defs><linearGradient id="g"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
          '<stop offset=".2" stop-color="#fff"/><stop offset=".8" stop-color="#fff"/>'
          '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
          f'<mask id="m"><rect width="{W}" height="{h}" fill="url(#g)"/></mask></defs>')
    s.add(f'<g mask="url(#m)"><polyline class="flow" points="{" ".join(pts)}" fill="none" '
          f'stroke="{p["strong"]}" stroke-width="4" stroke-linecap="round"/></g>')
    return s


def button(p, ic, label, filled):
    size, h = 17, 52
    w = 24 + 22 + 10 + tw(label, size, 600) + 26
    s = Svg(w, h, p, label)
    bg, fg = (p["primary"], p["onprimary"]) if filled else (p["container"], p["text"])
    s.add(f'<g class="pop"><rect width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{bg}"/>')
    s.add(icon(ic, 24, (h - 22) / 2, 22, fg))
    s.text(56, h / 2 + size * 0.36, label, size, 600, fg)
    s.add("</g>")
    return s


# ───────────────────────────── OUTPUT ─────────────────────────────
THEMES = ["light"]  # add "dark" to also build dark cards


def pic(name, alt, width):
    img = f'<img src="assets/{name}-light.svg" width="{width}" alt="{esc(alt)}">'
    if "dark" not in THEMES:
        return img
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'{img}</picture>')


def main():
    ASSETS.mkdir(exist_ok=True)
    builders = {"hero": hero, "about": about, "stack": stack, "projects": projects_title, "wave": wave}
    for i, pr in enumerate(PROJECTS):
        builders[f"project-{pr['repo']}"] = (lambda p, i=i: project(p, i))
    for i, (ic, label, _, filled) in enumerate(BUTTONS):
        builders[f"button-{i + 1}"] = (lambda p, ic=ic, label=label, filled=filled: button(p, ic, label, filled))

    for old in ASSETS.glob("*.svg"):
        old.unlink()
    for theme in THEMES:
        pal = PALETTES[theme]
        for name, fn in builders.items():
            (ASSETS / f"{name}-{theme}.svg").write_text(fn(pal).render(), encoding="utf-8")

    blocks = [
        pic("hero", HERO["greeting"], "100%"),
        pic("about", "About me", "100%"),
        pic("stack", "Tech stack", "100%"),
        pic("projects", "Featured projects", "100%"),
    ]
    cards = [f'<a href="https://github.com/{USER}/{pr["repo"]}">{pic("project-" + pr["repo"], pr["title"], "49%")}</a>'
             for pr in PROJECTS]
    for i in range(0, len(cards), 2):
        blocks.append("&nbsp;".join(cards[i:i + 2]))
    blocks.append(pic("wave", "", "100%"))
    blocks.append("&nbsp;&nbsp;".join(
        f'<a href="{url}">{pic(f"button-{i + 1}", label, "auto")}</a>'
        for i, (_, label, url, _) in enumerate(BUTTONS)))

    readme = '<div align="center">\n\n' + "\n\n".join(blocks) + "\n\n</div>\n"
    (ROOT / "README.md").write_text(readme, encoding="utf-8")

    preview = PREVIEW.replace("{{README}}", readme)
    (ROOT / "preview.html").write_text(preview, encoding="utf-8")
    print("Built", len(builders) * len(THEMES), "SVGs, README.md and preview.html")


PREVIEW = """<!doctype html><html><head><meta charset="utf-8"><title>Profile preview</title>
<style>
body{margin:0;font-family:-apple-system,'Segoe UI',sans-serif;background:#fff;color:#1f2328}
body.dark{background:#0d1117;color:#e6edf3}
.bar{position:sticky;top:0;padding:10px 16px;background:inherit;border-bottom:1px solid #8884;display:flex;gap:8px;align-items:center}
.wrap{max-width:896px;margin:24px auto;padding:24px;border:1px solid #8884;border-radius:6px}
.wrap p{margin:0 0 16px}
img{max-width:100%;vertical-align:middle}
</style></head><body>
<div class="bar"><button onclick="toggle()">Toggle light / dark</button><span>Simulates github.com profile README width</span></div>
<div class="wrap" id="r">{{README}}</div>
<script>
const r=document.getElementById('r');
r.innerHTML=r.innerHTML.split(/\\n\\n+/).map(b=>b.trim()?'<p>'+b+'</p>':'').join('');
document.querySelectorAll('picture').forEach(pc=>{const img=pc.querySelector('img'),src=pc.querySelector('source');
 img.dataset.light=img.getAttribute('src');img.dataset.dark=src.getAttribute('srcset');src.remove();});
function apply(dark){document.body.classList.toggle('dark',dark);
 document.querySelectorAll('picture img').forEach(img=>{img.src=dark?img.dataset.dark:img.dataset.light;});}
let dark=new URLSearchParams(location.search).has('dark');function toggle(){dark=!dark;apply(dark)}
apply(dark);
</script></body></html>"""

if __name__ == "__main__":
    main()

"""
SVD Studio - Linear Algebra Mini Project (PES University, UE25MA242A)
Image compression, denoising and pattern discovery using the Singular Value Decomposition.

DESIGN (v2)
  Inspired by the "product dark" look of Linear / Vercel / Raycast:
    - tinted near-black surfaces, hairline borders, ONE accent colour, Inter typography
    - solid cards with a cursor spotlight on hover (no text over moving backgrounds)
    - Matrix digital rain lives only in the hero header and scrolls away with the page
    - segmented-control tabs, gradient primary button, quiet charts that match the theme
  Pick a theme in the sidebar: Blue pill (indigo), Green pill (Matrix), Red pill (ember).

Run:  pip install streamlit numpy matplotlib pillow scikit-image
      streamlit run app.py
Tip:  copy config.toml to  .streamlit/config.toml  (restart the app) so Streamlit's own widgets match.
"""
import base64
import colorsys
import json
import re
import time
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

st.set_page_config(page_title="SVD Studio", page_icon="◼", layout="wide")

# ============================================================ THEMES ("choose your pill")
PILLS = {
    "🔵 Blue pill · Indigo": dict(
        acc="#7C7CFF", acc2="#38BDF8", ok="#34D399", warn="#FB7185", head="#C9CCFF",
        bg="#0A0B10", surf="#11131A", surf2="#181B25", line="#262A37", text="#ECEEF6", muted="#8B91A5",
        toast="The story ends. You wake up in your bed."),
    "🟢 Green pill · Matrix": dict(
        acc="#3DDC84", acc2="#5EEAD4", ok="#A3E635", warn="#FB7185", head="#CFFFE0",
        bg="#080B09", surf="#0E1310", surf2="#151B17", line="#223027", text="#E6EFE9", muted="#84968B",
        toast="Follow the white rabbit."),
    "🔴 Red pill · Ember": dict(
        acc="#FF6B4A", acc2="#FBBF24", ok="#34D399", warn="#F43F5E", head="#FFE0D2",
        bg="#0C0A09", surf="#141110", surf2="#1C1816", line="#2E2622", text="#F4EEE9", muted="#9C9088",
        toast="Welcome to the real world."),
}


def rgb_str(h):
    h = h.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


def mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    out = [round(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t) for i in (0, 2, 4)]
    return "#%02X%02X%02X" % tuple(out)


def hue_deg(h):
    r, g, b = (int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)[0] * 360


def streamlit_primary():
    """Colour Streamlit itself uses for sliders/radios (from config.toml), so we can hue-shift them to our accent."""
    try:
        v = st.get_option("theme.primaryColor")
        if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            return v
    except Exception:
        pass
    return "#FF4B4B"


# ============================================================ SIDEBAR (top): theme + rain controls
st.sidebar.markdown("## Theme")
pill = st.sidebar.radio("Choose your pill", list(PILLS), index=0)
with st.sidebar.expander("Matrix rain (hero header)", expanded=False):
    rain_on = st.toggle("Show digital rain", True)
    rain_opacity = st.slider("Brightness", 0.1, 0.9, 0.5, 0.05)
    rain_speed = st.slider("Speed", 0.3, 2.5, 0.9, 0.1)
    rain_density = st.slider("Density", 0.2, 1.0, 0.7, 0.05)
st.sidebar.divider()

if st.session_state.get("_last_pill") not in (None, pill):
    st.toast(PILLS[pill]["toast"], icon="💊")
st.session_state["_last_pill"] = pill

T = PILLS[pill]
ACC, ACC2, OK, WARN, HEAD = T["acc"], T["acc2"], T["ok"], T["warn"], T["head"]
BG, SURF, SURF2, LINE, TEXT, MUTED = T["bg"], T["surf"], T["surf2"], T["line"], T["text"], T["muted"]
PANEL, FG, BORDER = SURF, TEXT, LINE            # names used by the plotting code
ACCD = mix(ACC, "#000000", 0.28)
HUE = int(round((hue_deg(ACC) - hue_deg(streamlit_primary())) % 360))
MX_CMAP = LinearSegmentedColormap.from_list("mx", [BG, mix(ACC, BG, 0.6), ACC, HEAD])

TOKENS = {
    "%ACC%": ACC, "%ACC2%": ACC2, "%ACCD%": ACCD, "%OK%": OK, "%WARN%": WARN, "%HEAD%": HEAD,
    "%BG%": BG, "%SURF%": SURF, "%SURF2%": SURF2, "%LINE%": LINE, "%TEXT%": TEXT, "%MUTED%": MUTED,
    "%ACCRGB%": rgb_str(ACC), "%ACC2RGB%": rgb_str(ACC2), "%SURFRGB%": rgb_str(SURF), "%HUE%": str(HUE),
}


def fill(template, extra=None):
    out = template
    for k, v in {**TOKENS, **(extra or {})}.items():
        out = out.replace(k, str(v))
    return out


# ============================================================ CSS
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body {background-color:%BG% !important;
  background-image:radial-gradient(900px 420px at 50% -140px, rgba(%ACCRGB%,.16), transparent 70%),
                   radial-gradient(circle at 1px 1px, rgba(255,255,255,.05) 1px, transparent 0) !important;
  background-size:auto, 26px 26px !important; background-attachment:fixed !important;}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"], .main {background:transparent !important;}
.stApp {font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif; color:%TEXT%; -webkit-font-smoothing:antialiased;}
button, input, textarea, [data-baseweb] {font-family:inherit !important;}
.block-container {padding-top:2rem; max-width:1280px;}
::-webkit-scrollbar {width:10px; height:10px;}
::-webkit-scrollbar-thumb {background:%LINE%; border-radius:10px; border:2px solid %BG%;}
::-webkit-scrollbar-track {background:transparent;}
::selection {background:rgba(%ACCRGB%,.45);}

/* ---- text */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label, [data-testid="stSidebar"] label,
[data-testid="stMetricLabel"] *, [data-testid="stAlert"] * {color:%TEXT% !important;}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:%MUTED% !important;}
[data-testid="stMarkdownContainer"] h4 {font-size:1.08rem; font-weight:650; letter-spacing:-.01em; margin-top:.2rem;}
[data-testid="stMarkdownContainer"] strong {color:%TEXT% !important; font-weight:650;}

/* ---- rain fallback (CSS only; the canvas version replaces it when JS is allowed) */
div[data-testid="stElementContainer"]:has(.mx-bg), div[data-testid="element-container"]:has(.mx-bg) {position:absolute; height:0; width:0; margin:0; padding:0;}
.mx-bg {position:fixed; top:0; left:0; right:0; height:460px; pointer-events:none; z-index:-1; overflow:hidden; opacity:.35;
  -webkit-mask-image:linear-gradient(to bottom,#000 0%,#000 30%,transparent 100%); mask-image:linear-gradient(to bottom,#000 0%,#000 30%,transparent 100%);}
.mx-js .mx-bg {display:none;}
.rc {position:absolute; top:0; line-height:1.15; white-space:nowrap; text-align:center;
  background:linear-gradient(to bottom, transparent 0%, rgba(%ACCRGB%,.6) 60%, %HEAD% 100%);
  -webkit-background-clip:text; background-clip:text; color:transparent; -webkit-text-fill-color:transparent;
  animation:mxfall linear infinite; will-change:transform;}
@keyframes mxfall {from {transform:translateY(-110%);} to {transform:translateY(460px);}}

/* ---- hero */
.hero {margin:.2rem 0 1.1rem 0; animation:mxup .7s ease both;}
@keyframes mxup {from {opacity:0; transform:translateY(12px);} to {opacity:1; transform:none;}}
.badge {display:inline-flex; align-items:center; gap:8px; padding:5px 12px; border-radius:999px; font-size:.76rem; font-weight:500;
  color:%MUTED%; background:rgba(%SURFRGB%,.85); border:1px solid %LINE%; backdrop-filter:blur(6px);}
.badge .dot {width:7px; height:7px; border-radius:50%; background:%ACC%; box-shadow:0 0 0 0 rgba(%ACCRGB%,.6); animation:mxping 2s infinite;}
@keyframes mxping {70% {box-shadow:0 0 0 8px rgba(%ACCRGB%,0);} 100% {box-shadow:0 0 0 0 rgba(%ACCRGB%,0);}}
.title {font-size:clamp(2.6rem,5.2vw,4.1rem); font-weight:800; letter-spacing:-.04em; line-height:1.04; margin:.7rem 0 .5rem 0;
  background:linear-gradient(180deg,#fff 20%, %HEAD% 60%, %ACC% 120%); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; text-shadow:none; filter:drop-shadow(0 4px 30px rgba(0,0,0,.6));}
.sub {color:%MUTED%; font-size:1.06rem; line-height:1.55; max-width:760px; margin:0 0 1rem 0;}

/* ---- pipeline chips */
.pipe {display:flex; gap:8px; flex-wrap:wrap; margin:.2rem 0 1.4rem 0;}
.chip {display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:10px; font-size:.8rem; font-weight:500;
  color:%TEXT%; cursor:default; border:1px solid %LINE%;
  background:radial-gradient(120px circle at var(--mx,-999px) var(--my,-999px), rgba(%ACCRGB%,.22), transparent 70%), %SURF%;
  transition:border-color .2s, transform .15s; animation:mxup .5s both; animation-delay:calc(var(--i,0) * 50ms + .25s);}
.chip b {font-weight:600; font-size:.7rem; color:%ACC%; font-variant-numeric:tabular-nums;}
.chip:hover {border-color:rgba(%ACCRGB%,.6); transform:translateY(-1px);}

/* ---- concept / purpose / outcome cards */
.cpo {display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:.4rem 0 1rem 0;}
@media (max-width:900px) {.cpo {grid-template-columns:1fr;}}
.cpo div {border:1px solid %LINE%; border-radius:12px; padding:12px 15px; font-size:.9rem; line-height:1.5; color:%TEXT%;
  background:radial-gradient(260px circle at var(--mx,-999px) var(--my,-999px), rgba(%ACCRGB%,.12), transparent 70%), %SURF2%;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.04); transition:border-color .2s;}
.cpo div:hover {border-color:rgba(%ACCRGB%,.45);}
.cpo span {display:flex; align-items:center; gap:8px; font-size:.68rem; font-weight:600; letter-spacing:.12em; text-transform:uppercase;
  color:%MUTED%; margin-bottom:5px;}
.cpo span::before {content:""; width:6px; height:6px; border-radius:50%; background:%ACC%;}
.cpo div:nth-child(2) span::before {background:%ACC2%;}
.cpo div:nth-child(3) span::before {background:%OK%;}
.stage {font-size:1.08rem; font-weight:650; letter-spacing:-.01em; margin-bottom:.35rem; color:%TEXT%;}
.stage i {font-style:normal; font-size:.78rem; font-weight:600; font-variant-numeric:tabular-nums; color:%ACC%;
  background:rgba(%ACCRGB%,.12); border:1px solid rgba(%ACCRGB%,.32); border-radius:8px; padding:2px 9px; margin-right:11px;}

/* ---- metrics (bento row) */
div[data-testid="stMetric"] {border:1px solid %LINE%; border-radius:14px; padding:16px 18px; box-shadow:inset 0 1px 0 rgba(255,255,255,.04);
  background:radial-gradient(280px circle at var(--mx,-999px) var(--my,-999px), rgba(%ACCRGB%,.13), transparent 70%), %SURF%;
  transition:border-color .2s, transform .15s;}
div[data-testid="stMetric"]:hover {border-color:rgba(%ACCRGB%,.5); transform:translateY(-1px);}
[data-testid="stMetricLabel"] * {font-size:.8rem !important; font-weight:500; color:%MUTED% !important;}
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {font-size:2.05rem !important; font-weight:700 !important; letter-spacing:-.03em;
  font-variant-numeric:tabular-nums; color:%TEXT% !important;}

/* ---- tabs = segmented control */
[data-baseweb="tab-list"] {background:%SURF%; border:1px solid %LINE%; border-radius:12px; padding:4px; gap:2px; width:fit-content; max-width:100%;}
button[data-baseweb="tab"] {height:36px; padding:0 14px; border-radius:8px; background:transparent; color:%MUTED%; transition:background .15s,color .15s;}
button[data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {color:inherit !important; font-size:.86rem; font-weight:500;}
button[data-baseweb="tab"]:hover {color:%TEXT%; background:rgba(255,255,255,.04);}
button[data-baseweb="tab"][aria-selected="true"] {color:%TEXT%; background:%SURF2%; box-shadow:0 0 0 1px %LINE%, 0 1px 3px rgba(0,0,0,.5);}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display:none !important;}
[data-baseweb="tab-panel"] {padding-top:1.1rem; animation:mxfade .35s ease;}
@keyframes mxfade {from {opacity:0; transform:translateY(6px);} to {opacity:1; transform:none;}}

/* ---- buttons */
.stButton > button, .stDownloadButton > button {border-radius:10px; font-weight:550; background:%SURF2%; border:1px solid %LINE%; color:%TEXT%;
  transition:border-color .2s, transform .15s, box-shadow .2s, filter .2s;}
.stButton button p, .stDownloadButton button p {color:inherit !important; font-weight:550;}
.stButton > button:hover, .stDownloadButton > button:hover {border-color:rgba(%ACCRGB%,.7); transform:translateY(-1px); color:%TEXT%;}
.stButton > button:active, .stDownloadButton > button:active {transform:scale(.98);}
button[kind="primary"], button[data-testid="stBaseButton-primary"] {color:#fff !important; border:1px solid rgba(255,255,255,.14) !important;
  background:linear-gradient(180deg, %ACC% 0%, %ACCD% 100%) !important; box-shadow:0 8px 24px rgba(%ACCRGB%,.32), inset 0 1px 0 rgba(255,255,255,.25);}
button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover {filter:brightness(1.12); box-shadow:0 10px 30px rgba(%ACCRGB%,.5), inset 0 1px 0 rgba(255,255,255,.3);}

/* ---- sidebar + inputs */
[data-testid="stSidebar"] {background:%SURF% !important; border-right:1px solid %LINE%;}
[data-testid="stSidebar"] h2 {font-size:.7rem !important; font-weight:600; letter-spacing:.14em; text-transform:uppercase; color:%MUTED% !important; padding-top:.4rem;}
[data-baseweb="select"] > div {background:%SURF2% !important; border:1px solid %LINE% !important; color:%TEXT% !important; border-radius:10px !important;}
[data-baseweb="select"] * {color:%TEXT% !important;}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {background:%SURF2% !important;}
[data-baseweb="popover"] li:hover {background:rgba(%ACCRGB%,.16) !important;}
[data-testid="stExpander"] {background:%SURF2%; border:1px solid %LINE% !important; border-radius:12px;}
[data-testid="stSlider"], [data-testid="stSelectSlider"], [data-testid="stProgress"], [data-testid="stRadio"],
[data-testid="stToggle"], [data-testid="stCheckbox"] {filter:hue-rotate(%HUE%deg);}

/* ---- containers, images, alerts */
div[data-testid="stVerticalBlockBorderWrapper"] {border-color:%LINE% !important; border-radius:14px !important; background:%SURF%;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.035);}
[data-testid="stImage"] img {border-radius:10px; border:1px solid %LINE%;}
[data-testid="stAlert"] {background:%SURF2% !important; border:1px solid %LINE%; border-radius:12px;}
[data-testid="stDataFrame"] {border:1px solid %LINE%; border-radius:10px; overflow:hidden;}
"""
CSS = "\n".join(line for line in fill(CSS).splitlines() if line.strip())      # no blank lines (markdown safe)
st.markdown(f"<style>\n{CSS}\n</style>", unsafe_allow_html=True)


# ---------------------------------------------------------------- CSS-only rain (fallback if JS is blocked)
def css_rain(n=48, seed=7):
    rng = np.random.default_rng(seed)
    glyphs = [chr(c) for c in range(0xFF66, 0xFF9E)] + list("0123456789")
    cols = []
    for i in range(n):
        length = int(rng.integers(10, 22))
        txt = "<br>".join(str(g) for g in rng.choice(glyphs, length))
        dur = float(rng.uniform(6, 13))
        cols.append(f'<div class="rc" style="left:{(i + rng.uniform(.1, .9)) / n * 100:.2f}%;'
                    f'font-size:{int(rng.integers(13, 19))}px;animation-duration:{dur:.1f}s;'
                    f'animation-delay:-{rng.uniform(0, dur):.1f}s">{txt}</div>')
    return "".join(cols)


st.markdown('<div class="mx-bg">' + (css_rain() if rain_on else "") + '</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------- JS: hero rain (canvas) + card spotlight
MX_JS = r"""
(function(){
var cfg = __CFG__;
if (window.__mx) { window.__mx.set(cfg); return; }
var D = document, root = D.documentElement;
var HH = 520;                                   // rain only fills the top "hero" band
var cv = D.createElement('canvas');
cv.id = 'mx-canvas';
var mask = 'linear-gradient(to bottom,#000 0%,#000 28%,transparent 100%)';
cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:' + HH + 'px;z-index:-1;pointer-events:none;will-change:transform;' +
  '-webkit-mask-image:' + mask + ';mask-image:' + mask;
D.body.appendChild(cv);
var ctx = cv.getContext('2d');
var fs = 16, W = 0, H = HH, cols = 0, drops = [], spd = [], act = [], mx = -9999, my = -9999, last = 0, sy = 0;
var CH = [];
for (var c = 0xFF66; c <= 0xFF9D; c++) CH.push(String.fromCharCode(c));
'0123456789:.=*+-<>|'.split('').forEach(function(ch){ CH.push(ch); });
function rnd(){ return CH[(Math.random() * CH.length) | 0]; }

function layout(){
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  W = window.innerWidth;
  cv.width = W * dpr; cv.height = H * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  cols = Math.ceil(W / fs);
  drops = []; spd = []; act = [];
  for (var i = 0; i < cols; i++){
    drops.push(Math.random() * -40);
    spd.push(0.35 + Math.random() * 0.65);
    act.push(Math.random());
  }
}

function frame(ts){
  requestAnimationFrame(frame);
  if (!cfg.on || sy > H || ts - last < 40) return;       // idle when off-screen or disabled
  last = ts;
  ctx.globalCompositeOperation = 'destination-out';      // fade trails to transparent (keeps page background visible)
  ctx.fillStyle = 'rgba(0,0,0,0.09)';
  ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'source-over';
  ctx.font = fs + 'px "Share Tech Mono", ui-monospace, monospace';
  for (var i = 0; i < cols; i++){
    if (act[i] > cfg.density) continue;
    var x = i * fs, prev = Math.floor(drops[i]);
    drops[i] += Math.min(1, spd[i] * cfg.speed);
    var cur = Math.floor(drops[i]);
    if (cur === prev) continue;
    var y = cur * fs;
    ctx.fillStyle = cfg.color;
    ctx.fillText(rnd(), x, y - fs);
    var dx = x - mx, dy = y - my;
    ctx.fillStyle = (dx * dx + dy * dy < 14400) ? '#ffffff' : cfg.head;
    ctx.fillText(rnd(), x, y);
    if (y > H && Math.random() > 0.97) drops[i] = Math.random() * -12;
  }
  if (mx > 0 && my < H){
    ctx.fillStyle = '#ffffff';
    for (var j = 0; j < 3; j++){
      var a = Math.random() * 6.283, r = Math.random() * 80;
      ctx.fillText(rnd(), Math.round((mx + Math.cos(a) * r) / fs) * fs, Math.round((my + Math.sin(a) * r) / fs) * fs);
    }
  }
}

function set(c){
  cfg = c;
  cv.style.display = cfg.on ? 'block' : 'none';
  cv.style.opacity = cfg.opacity;
  root.classList.toggle('mx-js', !!cfg.on);
}

// scroll the rain away together with the page (Streamlit scrolls an inner container)
D.addEventListener('scroll', function(e){
  var t = e.target;
  if (t && t !== D && t.clientHeight > 300){ sy = t.scrollTop || 0; cv.style.transform = 'translate3d(0,' + (-sy) + 'px,0)'; }
}, true);

// cursor spotlight on cards
var SEL = 'div[data-testid="stMetric"], .cpo > div, .chip';
D.addEventListener('mousemove', function(e){
  mx = e.clientX; my = e.clientY + sy;
  var t = e.target, el = (t && t.closest) ? t.closest(SEL) : null;
  if (el){
    var b = el.getBoundingClientRect();
    el.style.setProperty('--mx', (e.clientX - b.left) + 'px');
    el.style.setProperty('--my', (e.clientY - b.top) + 'px');
  }
}, {passive: true});
D.addEventListener('mouseout', function(e){
  var t = e.target, el = (t && t.closest) ? t.closest(SEL) : null;
  if (el){ el.style.setProperty('--mx', '-999px'); el.style.setProperty('--my', '-999px'); }
});
root.addEventListener('mouseleave', function(){ mx = my = -9999; });
window.addEventListener('click', function(e){
  var c = Math.floor(e.clientX / fs), r = Math.floor((e.clientY + sy) / fs);
  if (r * fs > H) return;
  for (var i = Math.max(0, c - 12); i < Math.min(cols, c + 12); i++){
    drops[i] = r + Math.random() * 6 - 3; spd[i] = 0.9 + Math.random() * 0.4; act[i] = 0;
  }
}, true);
var rt = 0;
window.addEventListener('resize', function(){ clearTimeout(rt); rt = setTimeout(layout, 150); });

window.__mx = {set: set};
layout(); set(cfg);
requestAnimationFrame(frame);
})();
"""


def inject_js(cfg):
    """Runs the rain/spotlight engine inside the *parent* page (so it can sit behind the whole app)."""
    js = MX_JS.replace("__CFG__", json.dumps(cfg))
    html = ("<!-- mx-inject --><script>(function(){try{var D=window.parent.document;"
            "var s=D.createElement('script');s.textContent=" + json.dumps(js) + ";D.head.appendChild(s);}"
            "catch(e){}})();</script>")
    try:
        if hasattr(st, "iframe"):
            st.iframe(html, height=1)
        else:
            components.html(html, height=0)
    except Exception:
        components.html(html, height=0)


inject_js(dict(color=ACC, head=HEAD, speed=rain_speed, density=rain_density, opacity=rain_opacity, on=bool(rain_on)))
st.markdown("<style>div[data-testid='stElementContainer']:has(iframe[srcdoc*='mx-inject']),"
            "div[data-testid='element-container']:has(iframe[srcdoc*='mx-inject'])"
            "{position:absolute;height:0;width:0;margin:0;overflow:hidden;}</style>", unsafe_allow_html=True)


# ============================================================ UI HELPERS
def cpo(concept, purpose, outcome):
    st.markdown(
        f'<div class="cpo"><div><span>Concept</span>{concept}</div>'
        f'<div><span>Purpose</span>{purpose}</div>'
        f'<div><span>Outcome</span>{outcome}</div></div>', unsafe_allow_html=True)


def stage(num, title):
    st.markdown(f'<div class="stage"><i>{num:02d}</i>{title}</div>', unsafe_allow_html=True)


def style_ax(ax):
    ax.set_facecolor(PANEL)
    for sp in ax.spines.values():
        sp.set_color(BORDER)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.title.set_color(FG)
    ax.grid(color=TEXT, alpha=0.07)


def new_fig(w=6, h=3.2, ncols=1):
    fig, ax = plt.subplots(1, ncols, figsize=(w, h))
    fig.patch.set_facecolor(PANEL)
    for a in np.atleast_1d(ax):
        style_ax(a)
    return fig, ax


def legend(ax, **kw):
    return ax.legend(facecolor=SURF2, labelcolor=FG, edgecolor=BORDER, **kw)


# ============================================================ HELPERS
def rank_k(U, s, Vt, k):
    return (U[:, :k] * s[:k]) @ Vt[:k, :]


def psnr(a, b):
    return 10 * np.log10(1 / max(np.mean((a - b) ** 2), 1e-12))


def to_b64(arr):
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    buf = BytesIO()
    im.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def rref(M, tol=1e-9):
    M = M.astype(float).copy()
    r, piv = 0, []
    for c in range(M.shape[1]):
        if r >= M.shape[0]:
            break
        p = r + np.argmax(np.abs(M[r:, c]))
        if abs(M[p, c]) < tol:
            continue
        M[[r, p]] = M[[p, r]]
        M[r] /= M[r, c]
        for i in range(M.shape[0]):
            if i != r:
                M[i] -= M[i, c] * M[r]
        piv.append(c)
        r += 1
    return M, piv


def gram_schmidt(M):
    Q = np.zeros(M.shape)
    for j in range(M.shape[1]):
        v = M[:, j].copy()
        for i in range(j):
            v -= (Q[:, i] @ M[:, j]) * Q[:, i]
        Q[:, j] = v / np.linalg.norm(v)
    return Q


@st.cache_data(show_spinner=False)
def load_image(source, upload_bytes, size):
    if upload_bytes is not None:
        im = Image.open(BytesIO(upload_bytes)).convert("RGB")
    else:
        from skimage import data
        a = getattr(data, source)()
        if a.ndim == 2:
            a = np.stack([a] * 3, axis=2)
        im = Image.fromarray(a)
    im.thumbnail((size, size))
    return np.asarray(im, dtype=float) / 255.0


@st.cache_data(show_spinner=False)
def svd(A):
    return np.linalg.svd(A, full_matrices=False)


@st.cache_data(show_spinner=False)
def denoise_curve(G, sigma, kmax=120):
    rng = np.random.default_rng(0)
    noisy = np.clip(G + rng.normal(0, sigma, G.shape), 0, 1)
    U, s, Vt = np.linalg.svd(noisy, full_matrices=False)
    R = np.zeros_like(G)
    curve = []
    for i in range(min(kmax, len(s))):
        R = R + s[i] * np.outer(U[:, i], Vt[i])
        curve.append(psnr(G, np.clip(R, 0, 1)))
    return noisy, s, U, Vt, np.array(curve)


# ============================================================ SIDEBAR (rest)
st.sidebar.markdown("## Input")
src = st.sidebar.selectbox("Image", ["camera", "astronaut", "coffee", "chelsea", "rocket", "moon", "coins", "Upload my own"])
upload = None
if src == "Upload my own":
    f = st.sidebar.file_uploader("PNG / JPG", type=["png", "jpg", "jpeg"])
    upload = f.getvalue() if f else None
    if upload is None:
        src = "camera"
size = st.sidebar.select_slider("Resolution (max side, px)", [64, 128, 192, 256, 384], value=256)
mode = st.sidebar.radio("Mode", ["Color (SVD per channel)", "Grayscale"], horizontal=False)

RGB = load_image(src, upload, size)
G = RGB @ np.array([0.299, 0.587, 0.114])          # luminance matrix used for analysis
m, n = G.shape
kmax = min(m, n)
st.sidebar.markdown("## Rank")
k = st.sidebar.slider("k = number of components kept", 1, kmax, min(20, kmax))
st.sidebar.caption("k is the dimension of the subspace we project onto.")

Ug, sg, Vtg = svd(G)
energy = np.cumsum(sg ** 2) / np.sum(sg ** 2)

if mode.startswith("Color"):
    parts = [svd(RGB[:, :, c]) for c in range(3)]
    ORIG = RGB
    def recon(kk):
        return np.clip(np.stack([rank_k(*p, kk) for p in parts], axis=2), 0, 1)
    ch = 3
    tot = sum(np.sum(p[1] ** 2) for p in parts)
    kept = sum(np.sum(p[1][:k] ** 2) for p in parts) / tot
else:
    ORIG = G
    def recon(kk):
        return np.clip(rank_k(Ug, sg, Vtg, kk), 0, 1)
    ch = 1
    kept = energy[k - 1]

Ak = recon(k)
stored = ch * k * (m + n + 1)
full = ch * m * n
ratio = full / stored
Q = psnr(ORIG, Ak)

# ============================================================ HERO
st.markdown(
    '<div class="hero">'
    '<div class="badge"><span class="dot"></span>PES University &nbsp;·&nbsp; UE25MA242A &nbsp;·&nbsp; Linear Algebra</div>'
    '<div class="title">SVD Studio</div>'
    '<div class="sub">Watch an image get rebuilt from a handful of orthogonal patterns. '
    'Every panel below is one stage of the linear algebra workflow.</div></div>', unsafe_allow_html=True)
stages = ["Matrix", "RREF", "Rank & Nullity", "Basis", "Gram-Schmidt", "Projection",
          "Least squares", "Eigen", "Diagonalization", "Compression"]
st.markdown('<div class="pipe">' + "".join(
    f'<span class="chip" style="--i:{i}"><b>{i+1:02d}</b>{t}</span>' for i, t in enumerate(stages)) + '</div>',
    unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Compression", f"{ratio:.1f}x", f"saves {100*(1-stored/full):.0f}% of storage")
c2.metric("Image quality (PSNR)", f"{Q:.1f} dB")
c3.metric("Energy kept", f"{kept:.2%}")
c4.metric("Numbers stored", f"{stored:,}", f"vs {full:,}", delta_color="off")
st.write("")

tabs = st.tabs(["Compress", "Build-up", "The math, stage by stage",
                "Projection lab", "Denoise", "Sweet spot"])

# ============================================================ TAB 1 COMPRESS
with tabs[0]:
    st.markdown("#### Drag the divider: original vs rank-k image")
    W = 540 * ORIG.shape[1] / ORIG.shape[0]
    html = fill("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600&display=swap');
      body{margin:0;background:transparent;font-family:'Inter',system-ui,sans-serif}
      .box{position:relative;margin:auto;width:min(100%,%W%px);aspect-ratio:%AR%;border-radius:14px;overflow:hidden;
           border:1px solid %LINE%;box-shadow:0 24px 60px rgba(0,0,0,.55);user-select:none}
      .box img{position:absolute;inset:0;width:100%;height:100%;display:block}
      #top{clip-path:inset(0 50% 0 0)}
      #bar{position:absolute;top:0;bottom:0;left:50%;width:2px;margin-left:-1px;background:#fff;box-shadow:0 0 14px rgba(0,0,0,.6)}
      #knob{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:42px;height:42px;border-radius:50%;
            background:#fff;color:#111;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;
            box-shadow:0 6px 20px rgba(0,0,0,.5),0 0 0 6px rgba(255,255,255,.18);transition:transform .15s}
      .box:hover #knob{transform:translate(-50%,-50%) scale(1.08)}
      .tag{position:absolute;top:14px;padding:5px 12px;border-radius:999px;background:rgba(10,11,16,.62);color:#fff;
           font-size:12px;font-weight:500;border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(8px)}
      .tag b{color:%ACC%;font-weight:600}
      #pct{position:absolute;bottom:14px;left:50%;transform:translateX(-50%);padding:4px 12px;border-radius:999px;
           background:rgba(10,11,16,.62);color:#fff;font-size:12px;font-weight:500;border:1px solid rgba(255,255,255,.14);
           backdrop-filter:blur(8px);font-variant-numeric:tabular-nums}
      input{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:ew-resize;margin:0}
    </style>
    <div class="box" id="b">
      <img src="data:image/png;base64,%AKB64%">
      <img id="top" src="data:image/png;base64,%ORB64%">
      <span class="tag" style="left:14px">Original%GRAY%</span>
      <span class="tag" style="right:14px">Rank <b>%K%</b> &middot; <b>%RATIO%x</b> smaller</span>
      <div id="bar"><div id="knob">&#8596;</div></div>
      <span id="pct">50% original</span>
      <input type="range" min="0" max="100" value="50" id="r">
    </div>
    <script>
      const r=document.getElementById('r'),t=document.getElementById('top'),b=document.getElementById('bar'),p=document.getElementById('pct');
      r.addEventListener('input',()=>{t.style.clipPath='inset(0 '+(100-r.value)+'% 0 0)';b.style.left=r.value+'%';
        p.textContent=r.value+'% original';});
    </script>""", dict(**{"%W%": f"{W:.0f}", "%AR%": f"{ORIG.shape[1]}/{ORIG.shape[0]}", "%AKB64%": to_b64(Ak),
                          "%ORB64%": to_b64(ORIG), "%GRAY%": " (grayscale)" if ch == 1 else "",
                          "%K%": k, "%RATIO%": f"{ratio:.1f}"}))
    if hasattr(st, "iframe"):            # newer Streamlit
        st.iframe(html.strip(), height=560)
    else:                                # older Streamlit
        components.html(html, height=560, scrolling=False)

    a, b = st.columns([1, 1])
    with a:
        st.markdown("**Where did the error go?** (|original − approximation|, brighter = larger error)")
        fig, ax = new_fig(5, 3.4)
        ax.imshow(np.abs(G - np.clip(rank_k(Ug, sg, Vtg, k), 0, 1)), cmap=MX_CMAP)
        ax.grid(False); ax.axis("off")
        st.pyplot(fig)
        st.caption("Errors concentrate on fine texture and sharp edges. Smooth regions are captured by the first few components.")
    with b:
        st.markdown("**Singular values σᵢ (importance of each pattern)**")
        fig, ax = new_fig(5, 3.4)
        ax.semilogy(np.arange(1, len(sg) + 1), sg, color=ACC2, lw=2)
        ax.axvline(k, color=WARN, ls="--", lw=1.5, label=f"k = {k}")
        ax.fill_between(np.arange(1, k + 1), sg[:k], sg.min(), color=ACC, alpha=0.25)
        ax.set_xlabel("component i"); legend(ax)
        st.pyplot(fig)
        st.caption("Sharp drop = the image is highly redundant. The shaded region is what we keep.")

    buf = BytesIO()
    Image.fromarray((Ak * 255).astype(np.uint8)).save(buf, "PNG")
    st.download_button("Download compressed image", buf.getvalue(), f"svd_rank_{k}.png", "image/png")

# ============================================================ TAB 2 BUILD-UP
with tabs[1]:
    st.markdown("#### The image is a sum of rank-1 layers  A = σ₁u₁v₁ᵀ + σ₂u₂v₂ᵀ + …")
    cpo("A = Σ σᵢ uᵢ vᵢᵀ", "Order the layers by importance so we can stop early",
        "The first few layers already look like the whole image")
    steps = sorted({s_ for s_ in [1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 120, 200, 300, 384] if s_ <= kmax})
    if st.button("Play: rebuild the image layer by layer", type="primary"):
        left, right = st.columns([1, 1])
        ph, info, bar = left.empty(), right.empty(), st.progress(0)
        for i, kk in enumerate(steps):
            ph.image(recon(kk), width=430, clamp=True)
            info.markdown(f"### k = {kk}\n**Compression:** {full/(ch*kk*(m+n+1)):.1f}x  \n"
                          f"**PSNR:** {psnr(ORIG, recon(kk)):.1f} dB  \n"
                          f"**Energy:** {energy[kk-1]:.2%}")
            bar.progress((i + 1) / len(steps))
            time.sleep(0.45)
    st.markdown("**The first 8 layers on their own** (each is σᵢ·uᵢvᵢᵀ, a rank-1 picture)")
    fig, axs = new_fig(14, 2.2, 8)
    for i, ax in enumerate(axs):
        L = sg[i] * np.outer(Ug[:, i], Vtg[i])
        ax.imshow(L, cmap="gray"); ax.grid(False); ax.axis("off")
        ax.set_title(f"σ{i+1} = {sg[i]:.1f}", fontsize=9)
    st.pyplot(fig)
    st.caption("Early layers = broad shapes. Later layers = ever finer stripes and texture.")

# ============================================================ TAB 3 MATH
with tabs[2]:
    # 01 matrix
    with st.container(border=True):
        stage(1, "Real-world data → Matrix representation")
        st.caption("The analysis stages use the grayscale (luminance) matrix so we work with a single m×n matrix.")
        cpo("Image as an m×n matrix A", "Turn pixels into something linear algebra can act on",
            f"A is {m}×{n} = {m*n:,} entries; it maps Rⁿ → Rᵐ")
        st.dataframe(np.round(G[:6, :8], 3), width="stretch")

    # 02 RREF
    with st.container(border=True):
        stage(2, "Matrix simplification: Gaussian elimination / RREF")
        r0, c0 = m // 2, n // 2
        blk = np.round(G[r0:r0 + 5, c0:c0 + 5] * 10)
        R, piv = rref(blk)
        cpo("Row-reduce to RREF", "Expose pivots and dependent columns",
            f"5×5 patch has {len(piv)} pivot column(s) → rank {len(piv)}; the other columns are combinations of them")
        x, y = st.columns(2)
        x.markdown("Patch (scaled ints)"); x.dataframe(blk.astype(int), width="stretch")
        y.markdown("RREF of patch"); y.dataframe(np.round(R, 2), width="stretch")
        st.caption("Full images are noisy, so exact RREF is meaningless at full size. SVD is the numerically stable version of this idea.")

    # 03 rank nullity
    with st.container(border=True):
        stage(3, "Structure of the space: rank & nullity")
        rk = int(np.linalg.matrix_rank(G))
        eff = int(np.searchsorted(energy, 0.99) + 1)
        cpo("rank(A) + nullity(A) = n", "Measure how many independent directions the data really has",
            f"rank = {rk}, nullity = {n - rk}. But 99% of the energy lives in only {eff} directions")
        st.progress(eff / rk, text=f"Effective dimension: {eff} of {rk}")

    # 04-05 basis + gram-schmidt
    with st.container(border=True):
        stage(4, "Remove redundancy → Orthogonalization (Gram-Schmidt)")
        Qg = gram_schmidt(G[:, :8])
        cpo("Independent columns → Gram-Schmidt → orthonormal basis",
            "Replace overlapping directions by perpendicular ones (QᵀQ = I)",
            f"Max off-diagonal of QᵀQ = {np.max(np.abs(Qg.T @ Qg - np.eye(8))):.1e}, i.e. perfectly orthogonal")
        x, y = st.columns(2)
        fig, ax = new_fig(4, 3.2)
        ax.imshow(np.abs(np.corrcoef(G[:, :8].T)), cmap=MX_CMAP, vmin=0, vmax=1); ax.grid(False)
        ax.set_title("|correlation| of raw columns (overlapping)")
        x.pyplot(fig)
        fig, ax = new_fig(4, 3.2)
        ax.imshow(np.abs(Qg.T @ Qg), cmap=MX_CMAP, vmin=0, vmax=1); ax.grid(False)
        ax.set_title("|QᵀQ| after Gram-Schmidt (identity)")
        y.pyplot(fig)
        st.caption(f"SVD gives orthonormal bases for free: UᵀU = I → {np.allclose(Ug.T @ Ug, np.eye(Ug.shape[1]))},  VᵀV = I → {np.allclose(Vtg @ Vtg.T, np.eye(Vtg.shape[0]))}")

    # 06-07 projection + LS
    with st.container(border=True):
        stage(6, "Projection → Least squares approximation")
        P_ = Ug[:, :k] @ Ug[:, :k].T
        err = np.linalg.norm(G - P_ @ G, "fro")
        cpo("P = UₖUₖᵀ projects onto the best k-dim subspace", "Keep only the closest rank-k picture to A",
            f"‖A−PA‖ = {err:.3f} = √(Σ discarded σ²) = {np.sqrt(np.sum(sg[k:]**2)):.3f} → provably optimal (Eckart–Young)")
        st.caption(f"P² = P → {np.allclose(P_ @ P_, P_)}    Pᵀ = P → {np.allclose(P_, P_.T)}    (Try the Projection lab tab to see this on a single column.)")

    # 08-09 eigen
    with st.container(border=True):
        stage(8, "Pattern discovery → Diagonalization of a symmetric matrix")
        S = G.T @ G
        w, V = np.linalg.eigh(S)
        w, V = w[::-1], V[:, ::-1]
        cpo("AᵀA is symmetric → AᵀA = VΛVᵀ", "Its eigenvectors are the dominant patterns; eigenvalues are their strength",
            f"λᵢ = σᵢ² (verified: {np.allclose(w[:10], sg[:10]**2)}). Top eigenvalue holds {w[0]/w.sum():.1%} of the energy")
        fig, axs = new_fig(12, 2.1, 6)
        for i, ax in enumerate(axs):
            ax.plot(V[:, i], color=[ACC, ACC2, OK, WARN, "#FBBF24", "#F472B6"][i], lw=1.2)
            ax.set_title(f"eigenvector {i+1}  (λ={w[i]:.0f})", fontsize=8)
            ax.set_yticks([])
        st.pyplot(fig)
        st.caption("Eigenvector 1 is smooth: the average brightness profile across columns. Higher ones oscillate faster: finer detail.")

# ============================================================ TAB 4 PROJECTION LAB
with tabs[3]:
    st.markdown("#### Projection = least squares, on one column of the image")
    cpo("Project a column a onto span(Uₖ)", "Find the closest vector inside the k-dim subspace",
        "The leftover error is perpendicular to the subspace, which is what makes it the best")
    j = st.slider("Choose image column", 0, n - 1, n // 2)
    a = G[:, j]
    Uk = Ug[:, :k]
    coef, *_ = np.linalg.lstsq(Uk, a, rcond=None)
    proj = Uk @ coef
    resid = a - proj
    fig, (ax1, ax2) = new_fig(12, 3.3, 2)
    ax1.plot(a, color=MUTED, lw=1.6, label="original column a")
    ax1.plot(proj, color=ACC2, lw=2, label=f"projection onto {k} directions")
    ax1.set_title("Column vs its projection"); legend(ax1, fontsize=8)
    ax2.bar(range(len(resid)), resid, color=WARN, width=1.0)
    ax2.set_title("Residual r = a − Pa")
    st.pyplot(fig)
    x, y, z = st.columns(3)
    x.metric("‖residual‖", f"{np.linalg.norm(resid):.4f}")
    y.metric("max |Uₖᵀ r|  (should be ≈ 0)", f"{np.max(np.abs(Uk.T @ resid)):.1e}")
    z.metric("lstsq coeffs = Uₖᵀa ?", "yes" if np.allclose(coef, Uk.T @ a) else "no")
    st.info("The residual is orthogonal to every direction we kept (Uₖᵀ r ≈ 0). "
            "That is exactly the normal-equation condition for a least-squares solution.")

# ============================================================ TAB 5 DENOISE
with tabs[4]:
    st.markdown("#### Application: noise reduction (on the grayscale version of your image)")
    cpo("Truncated SVD as a low-pass filter", "Real structure lives in big σ; random noise spreads over all σ",
        "Dropping small σ removes noise while keeping the picture")
    sigma = st.slider("Noise level (σ of Gaussian noise)", 0.0, 0.4, 0.15, 0.01)
    noisy, sn, Un, Vtn, curve = denoise_curve(G, sigma)
    kb = int(np.argmax(curve)) + 1
    den = np.clip(rank_k(Un, sn, Vtn, kb), 0, 1)
    x, y, z = st.columns(3)
    x.image(G, caption="Clean (grayscale)", clamp=True, width="stretch")
    y.image(noisy, caption=f"Noisy ({psnr(G, noisy):.1f} dB)", clamp=True, width="stretch")
    z.image(den, caption=f"Denoised with k={kb} ({curve[kb-1]:.1f} dB)", clamp=True, width="stretch")
    a, b = st.columns(2)
    fig, ax = new_fig(5.5, 3.2)
    ax.plot(np.arange(1, len(curve) + 1), curve, color=ACC2, lw=2)
    ax.axvline(kb, color=OK, ls="--"); ax.axhline(psnr(G, noisy), color=WARN, ls=":", label="noisy input")
    ax.set_xlabel("k"); ax.set_ylabel("PSNR vs clean (dB)"); ax.set_title(f"Best k = {kb}")
    legend(ax)
    a.pyplot(fig)
    fig, ax = new_fig(5.5, 3.2)
    ax.semilogy(sg, color=MUTED, label="clean σ"); ax.semilogy(sn, color=WARN, label="noisy σ")
    ax.set_xlabel("i"); ax.set_title("Noise lifts the tail of the spectrum")
    legend(ax)
    b.pyplot(fig)
    st.caption("Too small k blurs the image, too large k lets noise back in. The peak is the best trade-off.")

# ============================================================ TAB 6 SWEET SPOT
with tabs[5]:
    st.markdown("#### Quality vs storage: pick your operating point")
    cpo("Error² = Σ discarded σᵢ² (Eckart–Young)", "Predict quality for every k without recomputing",
        "A curve that shows diminishing returns")
    ks = np.arange(1, kmax + 1)
    tail = np.concatenate([np.cumsum((sg ** 2)[::-1])[::-1][1:], [0]])
    mse = np.maximum(tail / (m * n), 1e-12)
    ps = 10 * np.log10(1 / mse)
    rat = (m * n) / (ks * (m + n + 1))
    target = st.slider("I need at least this quality (PSNR dB)", 15, 45, 30)
    ok = np.where(ps >= target)[0]
    kt = int(ok[0] + 1) if len(ok) else kmax
    fig, ax = new_fig(9, 3.6)
    ax.plot(rat, ps, color=ACC2, lw=2)
    ax.scatter([rat[k - 1]], [ps[k - 1]], color=WARN, s=70, zorder=5, label=f"your k = {k}")
    ax.scatter([rat[kt - 1]], [ps[kt - 1]], color=OK, s=70, zorder=5, label=f"smallest k for {target} dB: {kt}")
    ax.set_xscale("log"); ax.invert_xaxis()
    ax.set_xlabel("compression ratio (log, higher = smaller file)"); ax.set_ylabel("PSNR (dB)")
    legend(ax)
    st.pyplot(fig)
    st.success(f"For ≥ {target} dB you need k = {kt}, giving **{rat[kt-1]:.1f}x** compression.")
    st.caption(f"Compression only helps while k < mn/(m+n+1) = {m*n/(m+n+1):.0f}. Beyond that, storing U, σ, V costs more than the raw image.")
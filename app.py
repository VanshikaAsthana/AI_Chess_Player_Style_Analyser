import base64
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="ChessDNA — Player Style Analyzer", page_icon="♞", layout="centered")


@st.cache_resource
def load_bundle():
    return joblib.load(Path(__file__).parent / "style_model.joblib")


B = load_bundle()
if "num_imp" not in B:
    st.error(f"Wrong model file loaded. Keys found: {list(B.keys())}")
    st.stop()

# ----------------------------------------------------------------------------- look & feel
PAWN = "♟\ufe0e"
STYLE_INFO = {
    "Tactical attacker": ("♞", "#f2a93b",
        "Hunts the king. Lots of checks and sacrifices, and castles early so the attack stays safe."),
    "Early-queen risk-taker": ("♛", "#e0566b",
        "Brings the queen out early, castles late and trades pieces freely. Sharp, risk-friendly play."),
    "Quiet / positional": (PAWN, "#4cc9b0",
        "Few checks and sacrifices, many pawn moves. Slow, structural chess that waits for mistakes."),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;800&family=Inter:wght@400;500;600&display=swap');
.stApp, .stApp p, .stApp label, .stApp li, .stApp button, .stApp input, .stApp textarea,
.stApp [data-baseweb="select"] div { font-family: 'Inter', sans-serif; }
.stApp {
  background:
    radial-gradient(ellipse at 50% -10%, rgba(212,175,55,.16), transparent 55%),
    radial-gradient(ellipse at 50% 115%, rgba(76,201,176,.10), transparent 50%),
    #0b0c10;
}
.stApp::before {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: repeating-conic-gradient(rgba(255,255,255,.04) 0% 25%, transparent 0% 50%) 50% / 96px 96px;
  -webkit-mask-image: radial-gradient(ellipse at center, #000 25%, transparent 80%);
          mask-image: radial-gradient(ellipse at center, #000 25%, transparent 80%);
}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"], .block-container { position: relative; z-index: 1; max-width: 960px; padding-top: 1.5rem; }

.pieces { position: fixed; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
.pieces span { position: absolute; bottom: -12%; color: rgba(212,175,55,.17); text-shadow: 0 0 24px rgba(212,175,55,.3);
  animation: floatUp linear infinite; }
.pieces span.ivory { color: rgba(245,236,210,.10); text-shadow: 0 0 22px rgba(245,236,210,.18); }
@keyframes floatUp {
  0%   { transform: translateY(0) rotate(0deg); opacity: 0; }
  10%  { opacity: 1; } 90% { opacity: 1; }
  100% { transform: translateY(-125vh) rotate(35deg); opacity: 0; }
}
@keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-7px); } }
@keyframes shimmer { to { background-position: 200% center; } }
@keyframes pop { 0% { opacity: 0; transform: scale(.88) translateY(14px); } 100% { opacity: 1; transform: none; } }
@keyframes grow { from { width: 0; } }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: none; } }

.hero { text-align: center; padding: .6rem 0 .2rem; animation: fadeUp .8s ease-out both; }
.hero .crest { font-size: 58px; line-height: 1; color: #d4af37; filter: drop-shadow(0 0 20px rgba(212,175,55,.6));
  animation: bob 4s ease-in-out infinite; }
.hero .title { font-family: 'Playfair Display', serif; font-size: 3.6rem; font-weight: 800; letter-spacing: .02em; line-height: 1.1;
  background: linear-gradient(90deg, #f5e6b3, #d4af37, #f5e6b3); background-size: 200% auto;
  -webkit-background-clip: text; background-clip: text; color: transparent; animation: shimmer 6s linear infinite; }
.hero .tag { color: #b9b29a; font-size: 1.02rem; margin: .3rem 0 0; letter-spacing: .03em; }
.hero .rule { height: 1px; width: 180px; margin: 1rem auto 0;
  background: linear-gradient(90deg, transparent, #d4af37, transparent); }


/* ---- sliders: green -> yellow -> red track ---- */
[data-testid="stSlider"] [role="group"] > div > div:first-child,
[data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child > div:first-child {
  background: linear-gradient(to right, #2ecc71 0%, #f1c40f 50%, #e74c3c 100%) !important;
  height: 6px !important; border-radius: 99px !important; box-shadow: 0 0 10px rgba(241,196,15,.18);
}
[data-testid="stSlider"] [role="group"] > div > div:nth-child(2),
[data-testid="stSlider"] div[data-baseweb="slider"] div[role="slider"] {
  background: #f5f0e1 !important; border: 3px solid #0b0c10 !important;
  box-shadow: 0 0 0 2px #f5f0e1, 0 0 14px rgba(255,255,255,.55) !important;
}
[data-testid="stSliderThumbValue"], [data-testid="stSliderThumbValue"] p { color: #f5f0e1 !important; font-weight: 600; }
[data-testid="stSliderTickBar"], [data-testid="stSliderTickBar"] p { color: #a8a18a !important; }

/* ---- dropdowns stay dark even if the Streamlit theme file is missing ---- */
[data-testid="stSelectbox"] [role="group"], div[data-baseweb="select"] > div {
  background: rgba(23,25,35,.95) !important; border: 1px solid rgba(212,175,55,.3) !important; }
[data-testid="stSelectbox"] [role="group"]:focus-within { border-color: #d4af37 !important; box-shadow: 0 0 0 1px #d4af37 !important; }
[data-testid="stSelectbox"] input, [data-testid="stSelectbox"] [role="group"] *, div[data-baseweb="select"] div,
div[data-baseweb="select"] span { color: #f3efe2 !important; -webkit-text-fill-color: #f3efe2 !important; }
[data-testid="stSelectbox"] svg, div[data-baseweb="select"] svg { fill: #d4af37 !important; color: #d4af37 !important; }
[data-testid="stSelectboxVirtualDropdown"], [data-baseweb="popover"] ul, [data-baseweb="popover"] [data-baseweb="menu"] {
  background: #171923 !important; border: 1px solid rgba(212,175,55,.3); border-radius: 10px; }
[role="option"], [role="option"] *, [data-baseweb="popover"] li, [data-baseweb="popover"] li * { color: #f3efe2 !important; }
[role="option"]:hover, [role="option"][aria-selected="true"], [data-baseweb="popover"] li:hover {
  background: rgba(212,175,55,.2) !important; }

.sect { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #f5e6b3; margin: 1.1rem 0 .5rem; }
.hint { color: #9d9783; font-size: .88rem; margin: -.2rem 0 .6rem; }

[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(18,20,28,.74); -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
  border: 1px solid rgba(212,175,55,.25) !important; border-radius: 18px; box-shadow: 0 12px 40px rgba(0,0,0,.45);
}
[data-testid="stWidgetLabel"] p, label p { color: #ddd6bf !important; font-weight: 500; }

div[data-testid="stButton"], div[data-testid="stElementContainer"]:has(> div[data-testid="stButton"]) { width: 100% !important; }
div[data-testid="stButton"] > button {
  width: 100%; border-radius: 999px; border: 1px solid rgba(212,175,55,.45); background: rgba(212,175,55,.08);
  color: #f3efe2; font-weight: 500; transition: all .25s ease;
}
div[data-testid="stButton"] > button:hover {
  transform: translateY(-2px); background: rgba(212,175,55,.2); border-color: #d4af37;
  box-shadow: 0 8px 26px rgba(212,175,55,.28); color: #fff;
}

.result { display: flex; gap: 20px; align-items: center; padding: 22px 24px; border-radius: 18px;
  background: linear-gradient(135deg, rgba(255,255,255,.07), rgba(255,255,255,.02)); border: 1px solid var(--accent);
  box-shadow: 0 12px 40px rgba(0,0,0,.45), 0 0 40px -10px var(--accent);
  animation: pop .7s cubic-bezier(.2,1.3,.4,1) both; }
.result .glyph { font-size: 84px; line-height: 1; color: var(--accent); filter: drop-shadow(0 0 18px var(--accent));
  animation: bob 3.5s ease-in-out infinite; }
.result .kicker { text-transform: uppercase; letter-spacing: .18em; font-size: .72rem; color: #a8a18a; }
.result .sname { font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 800; color: #fff; margin: .1rem 0 .3rem; }
.result .sdesc { color: #cfc8b0; font-size: .95rem; line-height: 1.5; }

.pbox { margin-top: 14px; padding: 16px 18px; border-radius: 16px; background: rgba(18,20,28,.7);
  border: 1px solid rgba(255,255,255,.07); animation: fadeUp .9s ease-out both; }
.prow { display: flex; align-items: center; gap: 12px; margin: 9px 0; }
.pname { width: 170px; color: #ddd6bf; font-size: .9rem; }
.ptrack { flex: 1; height: 10px; border-radius: 99px; background: rgba(255,255,255,.08); overflow: hidden; }
.pfill { height: 100%; border-radius: 99px; animation: grow 1.1s cubic-bezier(.2,.8,.2,1) both; }
.ppct { width: 44px; text-align: right; color: #f3efe2; font-weight: 600; font-size: .9rem; }

.radar { animation: fadeUp .9s ease-out both; text-align: center; }
.radar img { width: 100%; max-width: 440px; }
.legend { display: flex; justify-content: center; gap: 18px; color: #cfc8b0; font-size: .85rem; margin-top: -6px; }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }

.foot { text-align: center; color: #8d8873; font-size: .8rem; margin: 2rem 0 .5rem; line-height: 1.6; }
</style>
"""

_PIECES = [("♞", 4, 54, 26, 0, 0), ("♜", 13, 40, 31, 7, 1), ("♛", 22, 64, 24, 15, 0), ("♝", 31, 36, 34, 3, 1),
           ("♚", 40, 58, 28, 19, 0), (PAWN, 49, 32, 30, 11, 1), ("♞", 58, 46, 33, 5, 1), ("♛", 67, 38, 27, 22, 0),
           ("♜", 75, 60, 29, 9, 0), ("♝", 83, 42, 32, 16, 1), (PAWN, 90, 50, 25, 2, 0), ("♚", 96, 34, 35, 13, 1)]
PIECES_HTML = '<div class="pieces">' + "".join(
    f'<span class="{"ivory" if iv else ""}" style="left:{l}%;font-size:{s}px;animation-duration:{d}s;animation-delay:-{dl}s">{g}</span>'
    for g, l, s, d, dl, iv in _PIECES) + "</div>"

HERO_HTML = ('<div class="hero"><div class="crest">♞</div><div class="title">ChessDNA</div>'
             '<div class="tag">Read a player\'s style from the way they move</div><div class="rule"></div></div>')

st.markdown(CSS + PIECES_HTML + HERO_HTML, unsafe_allow_html=True)

# ----------------------------------------------------------------------------- model
def predict(row):
    x = pd.DataFrame([row])
    x["castling_habit_bin"] = 0 if pd.isna(x.loc[0, "avg_castling_move"]) else 1   # flag BEFORE imputing
    x[B["NUM"]] = B["num_imp"].transform(x[B["NUM"]])
    x[B["CAT_IMP"]] = B["cat_imp"].transform(x[B["CAT_IMP"]])
    x["time_control_ord"] = x["preferred_time_control"].map(B["tc_order"])
    x[B["eco_cols"]] = B["ohe"].transform(x[["main_eco_family"]])
    x[B["log_cols"]] = np.log1p(x[B["log_cols"]])
    x[B["NUM"]] = B["scaler"].transform(x[B["NUM"]])
    Z = B["pca"].transform(x[B["F2"]])
    proba = pd.Series(B["clf"].predict_proba(Z)[0], index=[B["names"][c] for c in B["clf"].classes_])
    return proba.idxmax(), proba   # headline always = top probability


AXES = [("avg_capture_rate", "Captures", 0.15, 0.30), ("avg_checks_given", "Checks", 0, 12),
        ("avg_castling_move", "Late castling", 6, 16), ("avg_dev_speed", "Slow development", 10, 20),
        ("avg_queen_early_moves", "Early queen", 0, 2), ("avg_pawn_move_ratio", "Pawn moves", 0.2, 0.4),
        ("avg_sacrifice_count", "Sacrifices", 0, 7)]


def radar_img(user_row, style_name, color):
    n, cx, cy, R = len(AXES), 230, 200, 112

    def pt(i, v, r=R):
        a = -math.pi / 2 + 2 * math.pi * i / n
        return cx + r * v * math.cos(a), cy + r * v * math.sin(a)

    def norm(col, val, lo, hi):
        if pd.isna(val):                       # never castles -> treat as "very late"
            return 1.0
        return float(min(1, max(0, (val - lo) / (hi - lo))))

    u = [norm(c, user_row[c], lo, hi) for c, _, lo, hi in AXES]
    s = [norm(c, B["profile"].loc[style_name, c], lo, hi) for c, _, lo, hi in AXES]
    poly = lambda vals: " ".join("%.1f,%.1f" % pt(i, v) for i, v in enumerate(vals))
    rings = "".join(f'<polygon points="{poly([k / 4] * n)}" fill="none" stroke="rgba(255,255,255,0.11)"/>' for k in (1, 2, 3, 4))
    spokes = "".join('<line x1="230" y1="200" x2="%.1f" y2="%.1f" stroke="rgba(255,255,255,0.11)"/>' % pt(i, 1) for i in range(n))
    labels = ""
    for i, (_, name, _, _) in enumerate(AXES):
        x, y = pt(i, 1, R + 20)
        anchor = "middle" if abs(x - cx) < 8 else ("start" if x > cx else "end")
        labels += f'<text x="{x:.1f}" y="{y + 4:.1f}" fill="#cfc8b0" font-size="12.5" font-family="Arial,sans-serif" text-anchor="{anchor}">{name}</text>'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 460 400"><style>'
           f'.a{{transform-origin:230px 200px;animation:in 1s ease-out both}}@keyframes in{{from{{transform:scale(.15);opacity:0}}}}'
           f'</style>{rings}{spokes}'
           f'<polygon class="a" points="{poly(s)}" fill="{color}" fill-opacity="0.22" stroke="{color}" stroke-width="2"/>'
           f'<polygon class="a" points="{poly(u)}" fill="#ffffff" fill-opacity="0.14" stroke="#f5f0e1" stroke-width="2.4" stroke-dasharray="6 4"/>{labels}</svg>')
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


# ----------------------------------------------------------------------------- inputs
DEFAULTS = dict(capture=0.216, checks=5.5, castle=9.6, dev=13.7, queen=0.7, pawn=0.28, sac=3.3,
                tc="Blitz", eco="B", never=False)
PRESETS = {
    "♞  Heavy attacker": dict(capture=0.20, checks=8.5, castle=8.5, dev=13.7, queen=0.6, pawn=0.25, sac=4.5, tc="Blitz", eco="C", never=False),
    "♛  Early-queen player": dict(capture=0.23, checks=5.2, castle=11.5, dev=13.7, queen=1.1, pawn=0.29, sac=3.4, tc="Blitz", eco="A", never=False),
    f"{PAWN}  Quiet strategist": dict(capture=0.22, checks=3.2, castle=8.7, dev=13.7, queen=0.4, pawn=0.32, sac=2.0, tc="Blitz", eco="D", never=False),
}
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)


def apply_preset(name):
    for k, v in PRESETS[name].items():
        st.session_state[k] = v


st.markdown('<div class="sect">Try a sample player</div>', unsafe_allow_html=True)
cols = st.columns(3)
for col, name in zip(cols, PRESETS):
    col.button(name, on_click=apply_preset, args=(name,), key=f"preset_{name}")

st.markdown('<div class="sect">Or build your own</div><div class="hint">Average stats over several of the player\'s games.</div>',
            unsafe_allow_html=True)
with st.container(border=True):
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.slider("Capture rate", 0.10, 0.35, step=0.005, key="capture")
        st.slider("Checks given per game", 0.0, 25.0, step=0.1, key="checks")
        st.slider("Sacrifices per game", 0.0, 9.0, step=0.1, key="sac")
        st.slider("Early queen moves", 0.0, 4.0, step=0.05, key="queen")
    with c2:
        st.slider("Average castling move", 3.0, 25.0, step=0.1, key="castle", disabled=st.session_state["never"])
        st.checkbox("This player never castles", key="never")
        st.slider("Development speed (move)", 7.0, 28.0, step=0.1, key="dev")
        st.slider("Pawn-move ratio", 0.10, 0.60, step=0.005, key="pawn")
    c3, c4 = st.columns(2, gap="large")
    c3.selectbox("Preferred time control", ["Bullet", "Blitz", "Rapid", "Classical"], key="tc")
    c4.selectbox("Main opening family (ECO)", ["A", "B", "C", "D", "E", "Unknown"], key="eco")

S = st.session_state
row = {"avg_capture_rate": S["capture"], "avg_checks_given": S["checks"],
       "avg_castling_move": np.nan if S["never"] else S["castle"], "avg_dev_speed": S["dev"],
       "avg_queen_early_moves": S["queen"], "avg_pawn_move_ratio": S["pawn"], "avg_sacrifice_count": S["sac"],
       "preferred_time_control": S["tc"], "main_eco_family": np.nan if S["eco"] == "Unknown" else S["eco"]}

# ----------------------------------------------------------------------------- result
style, proba = predict(row)
glyph, color, desc = STYLE_INFO[style]
st.markdown('<div class="sect">The verdict</div>', unsafe_allow_html=True)
left, right = st.columns([1.15, 1], gap="large")
with left:
    st.markdown(f'<div class="result" style="--accent:{color}"><div class="glyph">{glyph}</div><div>'
                f'<div class="kicker">Predicted style</div><div class="sname">{style}</div>'
                f'<div class="sdesc">{desc}</div></div></div>', unsafe_allow_html=True)
    bars = "".join(
        f'<div class="prow"><span class="pname">{n}</span><div class="ptrack"><div class="pfill" '
        f'style="width:{p * 100:.0f}%;background:{STYLE_INFO[n][1]}"></div></div><span class="ppct">{p * 100:.0f}%</span></div>'
        for n, p in proba.sort_values(ascending=False).items())
    st.markdown(f'<div class="pbox">{bars}</div>', unsafe_allow_html=True)
with right:
    st.markdown(f'<div class="radar"><img src="{radar_img(row, style, color)}"/>'
                f'<div class="legend"><span><i style="background:#f5f0e1"></i>This player</span>'
                f'<span><i style="background:{color}"></i>Average {style.lower()}</span></div></div>', unsafe_allow_html=True)

with st.expander("See the numbers"):
    table = pd.concat([B["profile"], pd.DataFrame([row], index=["This player"])[B["NUM"]]]).round(2)
    st.dataframe(table)

st.markdown('<div class="foot">Trained on 5,000 Lichess Elite games · 1,112 players · PCA + KMeans<br>'
            'Playing style is a continuum, so groups overlap and an average player still gets a label. '
            'The percentages show how strongly this player matches each style.</div>', unsafe_allow_html=True)
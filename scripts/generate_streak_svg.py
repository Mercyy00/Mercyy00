#!/usr/bin/env python3
"""
Generate an ultra-vivid, high-vibrancy animated GitHub contribution heatmap SVG.
Real unauthenticated GitHub data, illuminated with radiant electric & neon greens.
Usage: python generate_streak_svg.py [username] [output.svg]
"""
import sys, json, os, datetime

USER = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_PROFILE_USER", "Mercyy00")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "contrib-heatmap.svg")

def get_data(user):
    snap = os.path.join(HERE, "..", "data", "contributions.json")
    if os.path.exists(snap):
        d = json.load(open(snap, encoding="utf-8"))
        if d.get("username", "").lower() == user.lower() and all("level" in x for x in d.get("days", [])):
            return d
    raise FileNotFoundError(f"Contributions snapshot not found at {snap}. Run fetch_contributions.py first.")

data = get_data(USER)
contribs = data["days"]
total = data["total_contributions"]
best = data["best_day"]
lng = data["longest_streak"]

# ---- Layout ----
CELL, GAP, RAD, LEFT, TOP = 13, 3, 2.8, 36, 40

# ULTRA-VIBRANT NEON GREEN PALETTE:
# Level 0: Clean dark terminal emerald tile
# Level 1: Bright, crisp emerald (NOT dark sludge)
# Level 2: Intense cyber green
# Level 3: Radiant lime neon green
# Level 4: Hyper-bright electric neon
COLORS = [
    "#0d1814",  # Level 0 (sleek dark terminal emerald)
    "#00c853",  # Level 1 (crisp vivid emerald)
    "#00e676",  # Level 2 (electric green)
    "#39d353",  # Level 3 (hyper-bright neon green)
    "#69f0a0",  # Level 4 (radiant neon top end)
]
STROKES = [
    "#15291f",  # Level 0 border
    "#00e676",  # Level 1 border
    "#39d353",  # Level 2 border
    "#69f0a0",  # Level 3 border
    "#b9f6ca",  # Level 4 border
]
GRAY = "#7d8590"
GREEN_GLOW = "#00ff88"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

n = len(contribs)
NW = (n + 6) // 7
W = LEFT + NW * (CELL + GAP) + 16
H = TOP + 7 * (CELL + GAP) + 38

# Timing
REVEAL, DUR = 3.6, 0.55
maxorder = (NW - 1) + 6 * 0.55

rects, labels = [], []
sd = datetime.date.fromisoformat(contribs[0]["date"])
last_m = None
for wk in range(NW):
    d = sd + datetime.timedelta(days=wk * 7)
    if d.month != last_m:
        last_m = d.month
        labels.append(f'<text class="lbl" x="{LEFT + wk * (CELL + GAP)}" y="{TOP - 10}">{MONTHS[d.month - 1]}</text>')

for name, r in [("Mon", 1), ("Wed", 3), ("Fri", 5)]:
    labels.append(f'<text class="lbl" x="4" y="{TOP + r * (CELL + GAP) + CELL - 2}">{name}</text>')

for i, c in enumerate(contribs):
    wk, row, lvl = i // 7, i % 7, min(c["level"], 4)
    x = LEFT + wk * (CELL + GAP)
    y = TOP + row * (CELL + GAP)
    delay = round((wk + row * 0.55) / maxorder * REVEAL, 3)
    cls = "c g" if lvl >= 1 else "c e"
    stroke_attr = f'stroke="{STROKES[lvl]}" stroke-width="0.8"' if lvl > 0 else 'stroke="#14241b" stroke-width="0.6"'
    rects.append(
        f'<rect class="{cls}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{RAD}" '
        f'fill="{COLORS[lvl]}" {stroke_attr} style="animation-delay:{delay}s"/>'
    )

# Legend on bottom right
leg_x = W - 146
leg_y = H - 18
legend_parts = [
    f'<text class="leg" x="{leg_x - 30}" y="{leg_y + 9}">Less</text>'
]
for li, (lc, ls) in enumerate(zip(COLORS, STROKES)):
    legend_parts.append(
        f'<rect x="{leg_x + li * 15}" y="{leg_y}" width="10" height="10" rx="2" fill="{lc}" stroke="{ls}" stroke-width="0.6"/>'
    )
legend_parts.append(f'<text class="leg" x="{leg_x + 5 * 15 + 4}" y="{leg_y + 9}">More</text>')

best_text = f" · Best day: {best['count']} commits" if best.get("count") else ""

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">
<style>
  text.lbl {{ fill:{GRAY}; font-size:12px; font-weight:600; }}
  text.total {{ fill:#00e676; font-size:14px; font-weight:700; }}
  text.sub {{ fill:#8b949e; font-size:12px; font-weight:500; }}
  text.leg {{ fill:#8b949e; font-size:11px; font-weight:500; }}
  .c {{ transform-box:fill-box; transform-origin:center; opacity:0; animation:pop {DUR}s ease-out both; }}
  .g {{ animation:pop {DUR}s ease-out both, flash {DUR+0.15}s ease-out both; }}
  @keyframes pop {{ 0%{{opacity:0;transform:scale(.2)}} 60%{{opacity:1;transform:scale(1.15)}} 100%{{opacity:1;transform:scale(1)}} }}
  @keyframes flash {{ 0%{{filter:brightness(3.2) drop-shadow(0 0 5px {GREEN_GLOW})}} 50%{{filter:brightness(2.2)}} 100%{{filter:brightness(1)}} }}
  @media (prefers-reduced-motion: reduce) {{ .c {{ opacity:1 !important; animation:none !important; }} }}
</style>
<rect width="{W}" height="{H}" rx="10" fill="#0b120f" stroke="#182b22" stroke-width="1"/>
{''.join(labels)}
{''.join(rects)}
<g transform="translate({LEFT}, {H - 12})">
  <text class="total" x="0" y="0">⚡ {total:,} contributions</text>
  <text class="sub" x="145" y="0">in the last year{best_text}</text>
</g>
{''.join(legend_parts)}
</svg>'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Wrote {OUT}: {n} days, {total:,} contributions, {len(svg)//1024} KB")

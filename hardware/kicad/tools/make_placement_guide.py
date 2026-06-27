#!/usr/bin/env python3
"""Render a clean placement-guide PNG for the integrated system board (SRM-20 double-sided)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow, Circle, Rectangle, Patch
from pathlib import Path

OUT = Path(__file__).parents[1] / "system" / "placement_guide.png"

fig, ax = plt.subplots(figsize=(16.5, 11.2), dpi=120)
ax.set_xlim(-52, 252); ax.set_ylim(-30, 158); ax.set_aspect("equal"); ax.axis("off")

# ---- stock / mill-limit / board outline ----
ax.add_patch(Rectangle((0, 0), 220, 133, fill=False, ec="#bbb", ls="--", lw=1))
ax.text(110, 135.5, "copper stock 220 × 133 mm (raw blank)", ha="center", color="#999", fontsize=9)
ax.plot([203.2, 203.2], [-6, 139], color="#e06666", ls=":", lw=1.3)
ax.text(204, -10, "SRM-20 X-limit 203.2 mm →| board stays left", ha="left", color="#cc4125", fontsize=8.5)
BX, BY, BW, BH = 4, 6, 196, 122
ax.add_patch(Rectangle((BX, BY), BW, BH, fill=False, ec="#111", lw=2.4))
ax.text(BX + BW/2, BY + BH + 3.5, "BOARD OUTLINE (Edge.Cuts)  ≈ 196 × 122 mm",
        ha="center", fontweight="bold", fontsize=12)

# ---- functional blocks ----
def block(x, y, w, h, title, color, lines):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=2.5",
                 fc=color, ec="#333", lw=1.4, alpha=0.95))
    ax.text(x + w/2, y + h - 5, title, ha="center", va="top", fontweight="bold", fontsize=11.5)
    ax.text(x + w/2, y + h - 11.5, "\n".join(lines), ha="center", va="top", fontsize=8.6, color="#222")

C_MP, C_MF, C_MPPT, C_BO, C_C2K = "#f3b0a8", "#f6cfa2", "#bfe3b6", "#b3ddda", "#b6cdf0"
block(16, 42, 64, 74, "MOTOR POWER (2xx)", C_MP,
      ["rectifier 6× diode bridge", "3× 4700 µF V1 filter", "V1 buck: IR2110+IRF+L",
       "motor drive: IR2110+IRF+D", "LM7805 / NE555 / optos", "", "HIGH CURRENT → wide traces"])
block(16, 12, 64, 26, "MOTOR FEEDBACK (3xx)", C_MF,
      ["IL300 + op-amps", "V1 sense → Arduino"])
block(90, 74, 50, 42, "MPPT BUCK (4xx)", C_MPPT,
      ["PV→INA219→IRF530", "L401 150µ + 1N5822", "IR2110 gate", "→ STORE 5 V"])
block(90, 42, 50, 28, "BOOST (5xx)", C_BO,
      ["STORE → L501 470µ", "IR2110 + IRF + D", "→ LOAD (pulsing)"])
block(150, 42, 44, 74, "C2000 FEEDBACK (6xx)", C_C2K,
      ["V1/LOAD/STORE dividers", "÷11 / ÷7 / ÷3", "+ 3.0 V zener clamps", "→ ADC_V1/LOAD/STORE",
       "", "QUIET ANALOG —", "keep clear of switchers"])

# ground-domain hints
ax.text(48, 9, "power-GND domain", color="#b04a3a", fontsize=8.5, ha="center", style="italic")
ax.text(172, 39, "GND_MCU domain", color="#3a6", fontsize=8.5, ha="center", style="italic")

# ---- signal-flow arrows ----
def arr(x, y, dx, dy, c):
    ax.add_patch(FancyArrow(x, y, dx, dy, width=0.9, head_width=3.6, head_length=3.6,
                 length_includes_head=True, fc=c, ec=c, zorder=6))
arr(80, 100, 9, 0, "#b04a3a")          # 3ph/rect inside MP -> (toward center) hint
arr(80, 100, 9, 0, "#b04a3a")
arr(140, 92, 9, 0, "#2a8")             # MPPT region toward C2000 sense
ax.text(145, 95, "sense", color="#2a8", fontsize=7.5)
arr(112, 74, 0, -4, "#2a8")            # MPPT -> BOOST (STORE)
ax.text(114, 71.5, "STORE", color="#2a8", fontsize=7.5, va="center")

# ---- star tie ----
ax.add_patch(Circle((145, 34), 3.4, fc="#ffd24d", ec="#222", lw=1.4, zorder=7))
ax.text(145, 34, "★", ha="center", va="center", fontsize=11, zorder=8)
ax.text(145, 28.5, "R_STAR  GND↔GND_MCU (single tie)", ha="center", va="top", fontsize=7.6, color="#7a5c00")

# ---- edge connectors: square on border + label OUTSIDE with leader ----
def edge(x, y, label, side):
    ax.add_patch(Rectangle((x-2.4, y-2.4), 4.8, 4.8, fc="#222", ec="#000", zorder=7))
    if side == "L":   tx, ty, ha, va = x-7, y, "right", "center"
    elif side == "R": tx, ty, ha, va = x+7, y, "left", "center"
    elif side == "T": tx, ty, ha, va = x, y+7, "center", "bottom"
    else:             tx, ty, ha, va = x, y-7, "center", "top"
    ax.annotate(label, xy=(x, y), xytext=(tx, ty), ha=ha, va=va, fontsize=8.4, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color="#555", lw=0.8))

def hdr(x, y, label):
    ax.add_patch(FancyBboxPatch((x-2.4, y-2.4), 4.8, 4.8, boxstyle="round,pad=0.2",
                 fc="#3b4a8a", ec="#000", zorder=7))
    ax.annotate(label, xy=(x, y), xytext=(x+7, y), ha="left", va="center", fontsize=8.4,
                fontweight="bold", color="#243", arrowprops=dict(arrowstyle="-", color="#555", lw=0.8))

edge(BX, 104, "J_3PH  3-phase in", "L")
edge(BX, 60,  "J_MOT  motor out", "L")
edge(105, BY+BH, "J_PV + J_INA  (PV → INA219)", "T")
edge(128, BY+BH, "J_STO  1 F supercap", "T")
edge(112, BY,  "J_LOAD  pulsing load", "B")
edge(BX+BW, 104, "J_15V  +15 V supply", "R")
edge(BX+BW, 90,  "J_5V  +5 V supply", "R")
hdr(BX+BW, 72, "J_C2K  C2000 (off-board)")
hdr(BX+BW, 58, "J_ARD  Arduino Nano")

# ---- probe header row ----
ax.add_patch(FancyBboxPatch((90, 12), 104, 16, boxstyle="round,pad=0.4,rounding_size=2",
             fc="#eee", ec="#444", lw=1.2, hatch="...."))
ax.text(142, 23, "PROBE HEADER ROW  —  TP101–117", ha="center", va="center", fontsize=9, fontweight="bold")
ax.text(142, 16.5, "V1·STORE·LOAD·+5V·+3V3·+15V·GND·GND_MCU·PWM×3·ADC×3·MCU_V1·SDA·SCL",
        ha="center", va="center", fontsize=6.8, color="#444")

# ---- tooling / flip holes (diagonal) ----
for hx, hy, lx, ly, va in [(9, 124, 9, 128.5, "bottom"), (195, 10, 195, 5.5, "top")]:
    ax.add_patch(Circle((hx, hy), 2.6, fc="none", ec="#111", lw=1.6, zorder=7))
    ax.plot([hx-3.6, hx+3.6], [hy, hy], color="#111", lw=0.8, zorder=7)
    ax.plot([hx, hx], [hy-3.6, hy+3.6], color="#111", lw=0.8, zorder=7)
    ax.text(lx, ly, "⊕ tooling/flip hole", ha="center", va=va, fontsize=7.6)

# ---- title, legend, notes ----
ax.text(-50, 152, "62768 system board — placement guide  (double-sided, SRM-20 mill)",
        fontsize=15, fontweight="bold")
legend = [Patch(fc=C_MP, ec="#333", label="Motor power (high current)"),
          Patch(fc=C_MF, ec="#333", label="Motor feedback"),
          Patch(fc=C_MPPT, ec="#333", label="MPPT buck (switching)"),
          Patch(fc=C_BO, ec="#333", label="Boost (switching)"),
          Patch(fc=C_C2K, ec="#333", label="C2000 feedback (analog)")]
ax.legend(handles=legend, loc="lower left", bbox_to_anchor=(-0.155, 0.74),
          fontsize=8.5, frameon=True, title="Regions", title_fontsize=9)

notes = ("RULES  track ≥1.0 mm · clearance 0.9–1.0 mm (0.8 mm bit) · hand-stitched vias "
         "(GND free, signal vias rare) · pour GND on BOTH layers.\n"
         "SEPARATION  keep MPPT/BOOST/motor switching nodes (L401, L501, IR2110 outputs) "
         "away from the C2000 dividers and the MCU headers.\n"
         "CONNECTORS  one per interface (shown). All board-level I/O connectors are deleted — "
         "inter-board nets (V1, STORE, +15V, PWM, ADC…) become copper traces.")
ax.text(-50, -16, notes, fontsize=8.6, color="#333", va="top")

fig.savefig(OUT, bbox_inches="tight", facecolor="white", pad_inches=0.25)
fig.savefig(OUT.with_suffix(".pdf"), bbox_inches="tight", facecolor="white", pad_inches=0.25)
print("wrote", OUT, "and", OUT.with_suffix(".pdf"))

#!/usr/bin/env python3
"""Genererer bom/BOM.md fra bom/footprint_map.csv (CSV'en er source of truth).

Koeres fra hardware/kicad:  py -3.13 tools/bom_to_md.py
"""
import csv
from collections import Counter
from pathlib import Path

SRC = Path(__file__).parent.parent / "bom" / "footprint_map.csv"
DST = SRC.parent / "BOM.md"

BOARD_TITLES = {
    "buck": "Buck-converter",
    "boost": "Boost-converter",
    "drive": "Motor-drive",
    "feedback": "Feedback (isoleret)",
    "rectifier": "Rectifier (3-faset bro)",
    "mppt": "MPPT / PV",
    "current_sense": "Current sense (3 kanaler)",
    "c2000_feedback": "C2000 feedback/sensor (TI-port, 3.3 V)",
}

rows = list(csv.DictReader(SRC.open(encoding="utf-8")))

out = []
out.append("# BOM — 62768 energy system")
out.append("")
out.append("> Genereret fra [`footprint_map.csv`](footprint_map.csv) med "
           "`tools/bom_to_md.py` — **redigér CSV'en, ikke denne fil.** "
           "Alle substitutioner er flagget i note-kolonnen.")
out.append("")

# --- Samlet indkoebsliste: grupperet paa (indkoebsdel, footprint) = det man
# --- faktisk koeber. Footprinten skiller fx 1x02/1x03/1x05-headers ad.
counts = Counter()
source = {}
for r in rows:
    key = (r["chosen_part_number"], r["footprint"])
    counts[key] += 1
    source[key] = r["source"]

out.append("## Samlet indkøbsliste")
out.append("")
out.append("| Antal | Del | Pakke | Kilde |")
out.append("|---|---|---|---|")
for (part, fp), n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0][0])):
    pkg = fp.split(":", 1)[-1]
    out.append(f"| {n} | {part} | `{pkg}` | {source[(part, fp)]} |")
out.append("")

# --- Pr. board ---
for board in dict.fromkeys(r["board"] for r in rows):
    out.append(f"## {BOARD_TITLES.get(board, board)} (`{board}`)")
    out.append("")
    out.append("| Ref | Værdi | Del (indkøb) | Kilde | Footprint | Noter |")
    out.append("|---|---|---|---|---|---|")
    for r in rows:
        if r["board"] != board:
            continue
        note = r["notes"].replace("|", "\\|")
        out.append(f"| {r['schematic_ref']} | {r['value']} | "
                   f"{r['chosen_part_number']} | {r['source']} | "
                   f"`{r['footprint']}` | {note} |")
    out.append("")

DST.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"wrote {DST} ({len(rows)} rækker, {len(counts)} unikke dele)")

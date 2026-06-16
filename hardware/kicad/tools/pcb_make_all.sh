#!/usr/bin/env bash
# Linux/proot-pendant til pcb_make_all.ps1: netliste -> placeret PCB ->
# to-trins Freerouting -> DRC + render. Samme flow og samme scripts som .ps1'en;
# kun shell + stier er anderledes (Ubuntu-i-Termux, hvor teamets PC'er er Windows).
#
# Forudsaetninger (apt + pip i proot'en):
#   kicad 9 (kicad-cli + pcbnew til /usr/bin/python3), python3-pip, sexpdata,
#   default-jre + openjdk-21-jre, xvfb, og freerouting-1.9.0.jar i ~/.freerouting/.
#   Freerouting koeres under xvfb-run med JAVA 21 (ikke system-Java 25) — 1.9.0
#   bygger paa 21; 2.x-jars kraever 25 og aeder SES-gemningen (se WORKFLOW.md).
#
# Brug (fra hardware/kicad):  bash tools/pcb_make_all.sh mosfet_test [board2 ...]
# (kald med 'bash ...' — repoen ligger paa et noexec /sdcard-mount i Termux)
set -euo pipefail

JAR="${FREEROUTING_JAR:-$HOME/.freerouting/freerouting-1.9.0.jar}"
JAVA21="${JAVA21:-$(ls /usr/lib/jvm/java-21-openjdk-*/bin/java 2>/dev/null | head -1)}"
KC="${KICAD_CLI:-kicad-cli}"
PY="${KICAD_PYTHON:-/usr/bin/python3}"   # samme interpreter som har pcbnew
HERE="$(cd "$(dirname "$0")/.." && pwd)"  # hardware/kicad
cd "$HERE"

[ -f "$JAR" ]      || { echo "mangler freerouting-jar: $JAR"; exit 1; }
[ -x "$JAVA21" ]   || { echo "mangler Java 21 (openjdk-21-jre)"; exit 1; }

boards=("$@")
[ ${#boards[@]} -gt 0 ] || { echo "brug: $0 <board> [board ...]"; exit 1; }

route() {  # route <masked-or-locked.dsn> <ud.ses>
  rm -f "$2"
  timeout 300 xvfb-run -a "$JAVA21" -jar "$JAR" -de "$1" -do "$2" -mp 100 2>&1 \
    | grep -iE 'completed in|Saving|ERROR|Exception' | sed 's/^/    /' || true
}

for b in "${boards[@]}"; do
  echo "=== $b ==="
  sch="boards/$b/$b.kicad_sch"; pcb="boards/$b/$b.kicad_pcb"; out="boards/$b/pcb"
  mkdir -p "$out"
  tmp="$(mktemp -d)"

  "$KC" sch export netlist --format kicadsexpr -o "$tmp/$b.net" "$sch" >/dev/null
  "$PY" tools/pcb_netlist_json.py "$tmp/$b.net" "$tmp/$b.json"
  "$PY" tools/pcb_build.py "$tmp/$b.json" "$pcb"

  # TRIN 1: kun bagsiden — maskér F.Cu som power-lag (Specctra springer power over)
  "$PY" tools/pcb_route.py dsn "$pcb" "$tmp/$b.dsn"
  "$PY" - "$tmp/$b.dsn" "$tmp/${b}_1l.dsn" <<'PYEOF'
import re, sys
s = open(sys.argv[1], encoding='utf-8').read()
s = re.sub(r'\(layer F\.Cu\s*\n\s*\(type signal\)', '(layer F.Cu\n      (type power)', s)
open(sys.argv[2], 'w', encoding='utf-8', newline='\n').write(s)   # BOM-fri
PYEOF
  route "$tmp/${b}_1l.dsn" "$tmp/$b.ses"
  if [ -f "$tmp/$b.ses" ]; then "$PY" tools/pcb_route.py sesraw "$pcb" "$tmp/$b.ses"
  else echo "  trin 1: INGEN SES"; rm -rf "$tmp"; continue; fi

  # TRIN 2: laas bagside-kobber (type fix), lad Freerouting tage resten paa toppen
  "$PY" tools/pcb_route.py lockdsn "$pcb" "$tmp/${b}_2l.dsn"
  route "$tmp/${b}_2l.dsn" "$tmp/$b.ses"
  if [ -f "$tmp/$b.ses" ]; then "$PY" tools/pcb_route.py ses "$pcb" "$tmp/$b.ses"
  else echo "  trin 2: INGEN SES - kun bagside"; "$PY" tools/pcb_route.py ses "$pcb" "-"; fi

  "$KC" pcb drc -o "$out/$b.drc.txt" "$pcb" >/dev/null || true
  grep -iE 'Found' "$out/$b.drc.txt" | sed 's/^/  /' || true
  "$KC" pcb render --side bottom --background opaque -o "$out/${b}_bottom.png" "$pcb" >/dev/null 2>&1 || true
  "$KC" pcb render --side top    --background opaque -o "$out/${b}_top.png"    "$pcb" >/dev/null 2>&1 || true
  rm -rf "$tmp"
done

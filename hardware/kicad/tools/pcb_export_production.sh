#!/usr/bin/env bash
# Linux/proot-pendant til pcb_export_production.ps1 — samme kicad-cli-kald/flag.
# Pr. board i production/<board>/:
#   <board>.dxf          B.Cu + Edge.Cuts (BUNDEN) — SKAL spejlvendes i xTool
#   <board>_top_cu.dxf   F.Cu + Edge.Cuts (TOPPEN/traadbroer) — IKKE spejlvendes
#   <board>_silk_top.dxf valgfri topside-tekst — IKKE spejlvendes
#   gerbers/             komplet Gerber-saet + Excellon-drill
# Brug (fra hardware/kicad):  bash tools/pcb_export_production.sh mosfet_test [board2 ...]
set -euo pipefail
KC="${KICAD_CLI:-kicad-cli}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"; cd "$HERE"
[ $# -gt 0 ] || { echo "brug: bash $0 <board> [board ...]"; exit 1; }
for b in "$@"; do
  pcb="boards/$b/$b.kicad_pcb"; out="production/$b"
  mkdir -p "$out/gerbers"
  echo "=== $b ==="
  "$KC" pcb export dxf --mode-single -l "B.Cu,Edge.Cuts" --ou mm --drill-shape-opt 1 -o "$out/$b.dxf" "$pcb" >/dev/null
  "$KC" pcb export dxf --mode-single -l "F.Cu,Edge.Cuts" --ou mm --drill-shape-opt 1 -o "$out/${b}_top_cu.dxf" "$pcb" >/dev/null
  "$KC" pcb export dxf --mode-single -l "F.Silkscreen,Edge.Cuts" --ou mm --drill-shape-opt 0 -o "$out/${b}_silk_top.dxf" "$pcb" >/dev/null
  "$KC" pcb export gerbers -l "F.Cu,B.Cu,Edge.Cuts,B.Mask,F.Mask,F.Silkscreen,F.Fab" -o "$out/gerbers/" "$pcb" >/dev/null
  "$KC" pcb export drill --format excellon -o "$out/gerbers/" "$pcb" >/dev/null
  echo "  dxf + $(ls "$out/gerbers" | wc -l) gerber/drill-filer"
done

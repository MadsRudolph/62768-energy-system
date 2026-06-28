#!/usr/bin/env python3
"""Inspect the integrated system board: layers, netclass, tracks, zones, footprints, nets."""
import pcbnew
PCB = r"C:\Users\Mads2\DTU\4. Semester\Electrical Energy Systems\team\hardware\kicad\system\system.kicad_pcb"
b = pcbnew.LoadBoard(PCB)
cu = [l for l in b.GetEnabledLayers().CuStack()]
print("copper layers:", [b.GetLayerName(l) for l in cu])
print("footprints:", len(b.GetFootprints()))
print("tracks:", len(b.GetTracks()))
zones = b.Zones()
print("zones:", len(zones), [(z.GetNetname(), b.GetLayerName(z.GetLayer())) for z in zones])
ds = b.GetDesignSettings()
nc = b.GetAllNetClasses()
for name in nc:
    c = nc[name]
    print(f"netclass {name}: clearance={pcbnew.ToMM(c.GetClearance()):.2f} track={pcbnew.ToMM(c.GetTrackWidth()):.2f} "
          f"via={pcbnew.ToMM(c.GetViaDiameter()):.2f}/{pcbnew.ToMM(c.GetViaDrill()):.2f}")
# net list summary
nets = b.GetNetInfo()
nnames = sorted({b.GetNetInfo().GetNetItem(i).GetNetname() for i in range(b.GetNetCount())})
print("netcount:", b.GetNetCount())
# count pads per GND-ish net
from collections import Counter
padnets = Counter()
for fp in b.GetFootprints():
    for p in fp.Pads():
        padnets[p.GetNetname()] += 1
for n in sorted(padnets, key=lambda k: -padnets[k])[:20]:
    print(f"  net {n!r}: {padnets[n]} pads")
# board bbox
bb = b.GetBoardEdgesBoundingBox()
print("edge bbox mm:", pcbnew.ToMM(bb.GetWidth()), "x", pcbnew.ToMM(bb.GetHeight()))

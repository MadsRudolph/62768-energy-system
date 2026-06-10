#!/usr/bin/env python3
"""
3-faset ensretter -> V1-bus (Krav 1-3).

Generator (3f, via 3x ringkerne-trafo 1:8) -> J1 -> 6-diode bro (1N4006)
-> ladekondensator ~15 mF (3x 4700u/50V parallel) -> V1 = 15 V.
Teori: Lec 4 (V_dc = 1.654*V_m). R1 er bleeder.

Bro-orientering: top-diode A=fase K=V1, bund-diode A=GND K=fase.
Kør: py -3.13 build_rectifier.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))   # schbuild ligger i tools/
from schbuild import build

FP_TERM2 = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
FP_TERM3 = "TerminalBlock:TerminalBlock_bornier-3_P5.08mm"
FP_DO41  = "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
FP_CP18  = "Capacitor_THT:CP_Radial_D18.0mm_P7.50mm"
FP_R     = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"

comps = [
  {"lib":"Connector:Screw_Terminal_01x03","ref":"J1","val":"3-fase ind","fp":FP_TERM3,
   "x":40,"y":100,"nets":{"1":"PH_A","2":"PH_B","3":"PH_C"}},
  # top-dioder: fase -> V1   (Diode pin 1=K, 2=A)
  {"lib":"Diode:1N4006","ref":"D1","val":"1N4006","fp":FP_DO41,"x":80,"y":80,
   "nets":{"2":"PH_A","1":"V1"}},
  {"lib":"Diode:1N4006","ref":"D2","val":"1N4006","fp":FP_DO41,"x":80,"y":95,
   "nets":{"2":"PH_B","1":"V1"}},
  {"lib":"Diode:1N4006","ref":"D3","val":"1N4006","fp":FP_DO41,"x":80,"y":110,
   "nets":{"2":"PH_C","1":"V1"}},
  # bund-dioder: GND -> fase
  {"lib":"Diode:1N4006","ref":"D4","val":"1N4006","fp":FP_DO41,"x":110,"y":80,
   "nets":{"2":"GND","1":"PH_A"}},
  {"lib":"Diode:1N4006","ref":"D5","val":"1N4006","fp":FP_DO41,"x":110,"y":95,
   "nets":{"2":"GND","1":"PH_B"}},
  {"lib":"Diode:1N4006","ref":"D6","val":"1N4006","fp":FP_DO41,"x":110,"y":110,
   "nets":{"2":"GND","1":"PH_C"}},
  # ladekondensator ~15 mF: 3x 4700u/50V parallel (14.1 mF - taet nok, se BOM-note)
  {"lib":"Device:C_Polarized","ref":"C1","val":"4700u/50V","fp":FP_CP18,"x":145,"y":95,
   "nets":{"1":"V1","2":"GND"}},
  {"lib":"Device:C_Polarized","ref":"C2","val":"4700u/50V","fp":FP_CP18,"x":160,"y":95,
   "nets":{"1":"V1","2":"GND"}},
  {"lib":"Device:C_Polarized","ref":"C3","val":"4700u/50V","fp":FP_CP18,"x":175,"y":95,
   "nets":{"1":"V1","2":"GND"}},
  # bleeder
  {"lib":"Device:R","ref":"R1","val":"10k","fp":FP_R,"x":190,"y":95,
   "nets":{"1":"V1","2":"GND"}},
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J2","val":"V1 ud","fp":FP_TERM2,
   "x":215,"y":95,"ang":180,"nets":{"1":"V1","2":"GND"}},
]

if __name__ == "__main__":
    build("3-fase ensretter + ladekondensator  (gen -> 6x 1N4006 -> ~15 mF -> V1 15 V)",
          "system", comps, [], {"V1", "GND"},
          Path(__file__).parents[2] / "boards/rectifier/rectifier.kicad_sch")

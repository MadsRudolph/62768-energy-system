#!/usr/bin/env python3
"""
Simpelt MOSFET gate-drive testboard (benk-test af effekt-switchen).

Lavside N-kanal MOSFET (TO-220, fx IRLZ44N): gate drives fra et 2-pin header
gennem en serie-gateresistor Rg, med pulldown Rpd til GND saa gaten ikke flyder.
Drain/Source + forsyning gaar ud paa en 3-pin skrueterminal saa man kan haenge
en rigtig last + forsyning paa. Friloebs-/flyback-diode D1 over lasten (anode paa
drain, katode paa V+) saa induktiv last (motor/spole) ikke slaar Q1 ihjel.

GATE_IN --[Rg]--+--G  Q1
                |      D --(DRAIN, V+ via last)
              [Rpd]    S --GND
                |
               GND

Pin-noter:
  Q1  Device:Q_NMOS  pin-numre G/D/S (pcb_build mapper TO-220 pad 1/2/3 -> G/D/S;
      standard IRLZ44N/IRF540-pinout = 1:G 2:D 3:S).
  D1  1N4007 DO-41   pin 1=K (katode), 2=A (anode) -> flyback: A=DRAIN, K=VPLUS.
  M1  skrueterminal  1=VPLUS 2=DRAIN 3=GND.

Koer (proot/Linux):  python3 tools/generators/build_mosfet_test.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))   # schbuild ligger i tools/
from schbuild import build

FP_R     = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_TO220 = "energy_system:TO-220-3_Vertical_LaserPads"
FP_DO41  = "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
FP_HDR2  = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
# Ubuntu/proot-pakken har ikke bornier-serien; MaiXu MX126 (5.0 mm) er en
# tilsvarende vertikal skrueterminal der findes i kicad-footprints her.
FP_TERM3 = "TerminalBlock:TerminalBlock_MaiXu_MX126-5.0-03P_1x03_P5.00mm"

comps = [
  # gate-indgang (signal-header): pin1 = GATE_IN, pin2 = GND
  {"lib":"Connector_Generic:Conn_01x02","ref":"J1","val":"GATE drive ind","fp":FP_HDR2,
   "x":40,"y":80,"nets":{"1":"GATE_IN","2":"GND"}},
  # R1 = serie-gateresistor
  {"lib":"Device:R","ref":"R1","val":"10R","fp":FP_R,"x":70,"y":80,
   "nets":{"1":"GATE_IN","2":"GATE"}},
  # R2 = gate pulldown saa gaten ikke flyder (MOSFET sikkert OFF uden drive)
  {"lib":"Device:R","ref":"R2","val":"10k","fp":FP_R,"x":95,"y":92,"ang":90,
   "nets":{"1":"GATE","2":"GND"}},
  # effekt-switchen
  {"lib":"Device:Q_NMOS","ref":"Q1","val":"IRLZ44N","fp":FP_TO220,"x":120,"y":80,
   "nets":{"G":"GATE","D":"DRAIN","S":"GND"}},
  # flyback over lasten: anode (2) paa DRAIN, katode (1) paa V+
  {"lib":"Diode:1N4007","ref":"D1","val":"1N4007","fp":FP_DO41,"x":155,"y":68,
   "nets":{"1":"VPLUS","2":"DRAIN"}},
  # effekt-terminal: V+, drain (last-retur), GND
  {"lib":"Connector:Screw_Terminal_01x03","ref":"M1","val":"V+/DRAIN/GND","fp":FP_TERM3,
   "x":185,"y":82,"nets":{"1":"VPLUS","2":"DRAIN","3":"GND"}},
]

if __name__ == "__main__":
    build("MOSFET gate-drive testboard  (lavside N-MOS + Rg/Rpd + flyback)",
          "mosfet_test", comps, [], {"VPLUS", "GND"},
          Path(__file__).parents[2] / "boards/mosfet_test/mosfet_test.kicad_sch")

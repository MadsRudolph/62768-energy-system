#!/usr/bin/env python3
"""
Stroemmaaling, 3 kanaler (Krav 10: diskret, kun op-amps tilladt).

Lavside-maaling: hver grens returledning foeres gennem 1R00-shunt til GND.
Returstroemmen loeber RET_k -> GND, saa RET_k ligger 0..0.3 V OVER GND
(positivt) og en ikke-inverterende LM358 (gain 10.09 = 1+9k09/1k00)
skalerer 300 mA -> 3.0 V til Arduinoens ADC.

LM358 er valgt fordi dens indgange gaar til GND (TL07x kan ikke).
Forsyning +5 V fra Arduino: max udgang ~3.5 V -> ADC-sikker.

Kanaler: 1 = V1 -> buck, 2 = boost -> last, 3 = lager (V3).
Kør: py -3.13 build_current_sense.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))   # schbuild ligger i tools/
from schbuild import build

FP_TERM2 = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
FP_CDISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_R     = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_DIP8  = "Package_DIP:DIP-8_W7.62mm_LongPads"
FP_HDR5  = "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical"

def channel(k, y, opamp_ref, unit, pin_out, pin_minus, pin_plus):
    return [
      {"lib":"Connector:Screw_Terminal_01x02","ref":f"J{k}","val":f"kanal {k} retur",
       "fp":FP_TERM2,"x":40,"y":y,"nets":{"1":f"RET{k}","2":"GND"}},
      {"lib":"Device:R","ref":f"R{k}1","val":"1R00","fp":FP_R,"x":62,"y":y+5,
       "nets":{"1":f"RET{k}","2":"GND"}},
      {"lib":"Amplifier_Operational:LM358","ref":opamp_ref,"val":"LM358","fp":FP_DIP8,
       "x":95,"y":y,"unit":unit,
       "nets":{pin_plus:f"RET{k}",pin_minus:f"FB{k}",pin_out:f"I_SENSE{k}"}},
      {"lib":"Device:R","ref":f"R{k}2","val":"1k00","fp":FP_R,"x":85,"y":y+13,
       "nets":{"1":f"FB{k}","2":"GND"}},
      {"lib":"Device:R","ref":f"R{k}3","val":"9k09","fp":FP_R,"x":100,"y":y-12,
       "nets":{"1":f"FB{k}","2":f"I_SENSE{k}"}},
    ]

comps = (
  channel(1, 70,  "U1", 1, "1", "2", "3") +
  channel(2, 105, "U1", 2, "7", "6", "5") +
  channel(3, 140, "U2", 1, "1", "2", "3") +
  [
    # U2B ubrugt: unity-buffer paa GND (god praksis, undgaar oscillation)
    {"lib":"Amplifier_Operational:LM358","ref":"U2","val":"LM358","fp":FP_DIP8,
     "x":95,"y":170,"unit":2,"nets":{"5":"GND","6":"U2B_FB","7":"U2B_FB"}},
    # forsyninger
    {"lib":"Amplifier_Operational:LM358","ref":"U1","val":"LM358","fp":FP_DIP8,
     "x":140,"y":70,"unit":3,"nets":{"8":"+5V","4":"GND"}},
    {"lib":"Amplifier_Operational:LM358","ref":"U2","val":"LM358","fp":FP_DIP8,
     "x":140,"y":105,"unit":3,"nets":{"8":"+5V","4":"GND"}},
    {"lib":"Device:C","ref":"C1","val":"100n","fp":FP_CDISC,"x":155,"y":70,
     "nets":{"1":"+5V","2":"GND"}},
    {"lib":"Device:C","ref":"C2","val":"100n","fp":FP_CDISC,"x":155,"y":105,
     "nets":{"1":"+5V","2":"GND"}},
    # PWR_FLAGs: +5V/GND kommer udefra via J4
    {"lib":"power:PWR_FLAG","ref":"#FLG01","val":"PWR_FLAG","x":170,"y":70,
     "nets":{"1":"+5V"}},
    {"lib":"power:PWR_FLAG","ref":"#FLG02","val":"PWR_FLAG","x":170,"y":85,
     "nets":{"1":"GND"}},
    # samlet interface til Arduino
    {"lib":"Connector_Generic:Conn_01x05","ref":"J4","val":"Arduino","fp":FP_HDR5,
     "x":185,"y":120,"ang":180,
     "nets":{"1":"+5V","2":"I_SENSE1","3":"I_SENSE2","4":"I_SENSE3","5":"GND"}},
  ]
)

if __name__ == "__main__":
    build("Stroemmaaling 3 kanaler  (lavside 1R-shunt + LM358 x10 -> Arduino ADC)",
          "system", comps, [], {"GND", "+5V"},
          Path(__file__).parents[2] / "boards/current_sense/current_sense.kicad_sch")

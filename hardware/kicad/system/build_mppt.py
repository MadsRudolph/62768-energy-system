#!/usr/bin/env python3
"""
PV front-end (Krav 9, 11): Sun Plus 10 -> MPPT-kondensator (~15 mF)
-> diskret linear regulator (5 V) -> energilager (V3).

Blokskemaet i spec'en: Solcelle-panel -> MPPT Kondensator (15 mF)
-> Linear regulator (5V) -> lager. Regulatoren er diskret (Krav 9):
LM358 + BZX55C5V1 zener-reference + BD139 emitterfoelger. Vout = 5.1 V.

Sense-udgange til Arduino (P&O-beregning): PV-spaending via deler
(100k/22k6, 21 V -> 3.9 V) og PV-stroem via lavside-shunt 2x1R parallel
(0.5 ohm) + inverterende LM358 (x-9.09): 0.6 A -> 2.7 V.

OBS: BD139 afsaetter op til ~7 W ved fuld PV-stroem (linear reg fra ~17 V
-> 5 V) - skal have koeleplade. Krav 17 tillader at erstatte med buck senere.

Kør: py -3.13 build_mppt.py
"""
from pathlib import Path
from schbuild import build

FP_TERM2 = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
FP_DO41  = "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"
FP_DO35  = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
FP_CP18  = "Capacitor_THT:CP_Radial_D18.0mm_P7.50mm"
FP_CP8   = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
FP_CDISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_R     = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_DIP8  = "Package_DIP:DIP-8_W7.62mm_LongPads"
FP_TO220 = "energy_system:TO-220-3_Vertical_LaserPads"
FP_HDR3  = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"

comps = [
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J1","val":"PV ind","fp":FP_TERM2,
   "x":40,"y":95,"nets":{"1":"PV_PLUS","2":"PV_RET"}},
  # seriediode: blokerer tilbage-stroem i panelet (nat/skygge). 1=K 2=A
  {"lib":"Diode:1N5817","ref":"D1","val":"1N5817","fp":FP_DO41,"x":62,"y":85,
   "nets":{"2":"PV_PLUS","1":"PV_BUS"}},
  # MPPT-kondensator ~15 mF
  {"lib":"Device:C_Polarized","ref":"C1","val":"4700u/50V","fp":FP_CP18,"x":80,"y":95,
   "nets":{"1":"PV_BUS","2":"GND"}},
  {"lib":"Device:C_Polarized","ref":"C2","val":"4700u/50V","fp":FP_CP18,"x":92,"y":95,
   "nets":{"1":"PV_BUS","2":"GND"}},
  {"lib":"Device:C_Polarized","ref":"C3","val":"4700u/50V","fp":FP_CP18,"x":104,"y":95,
   "nets":{"1":"PV_BUS","2":"GND"}},
  # PV-spaendingsdeler til Arduino ADC
  {"lib":"Device:R","ref":"R1","val":"100k","fp":FP_R,"x":120,"y":85,
   "nets":{"1":"PV_BUS","2":"PV_V"}},
  {"lib":"Device:R","ref":"R2","val":"22k6","fp":FP_R,"x":120,"y":105,
   "nets":{"1":"PV_V","2":"GND"}},
  # zener-reference 5.1 V
  {"lib":"Device:R","ref":"R3","val":"4k75","fp":FP_R,"x":140,"y":80,
   "nets":{"1":"PV_BUS","2":"VREF"}},
  {"lib":"Device:D_Zener","ref":"DZ1","val":"BZX55C5V1","fp":FP_DO35,"x":140,"y":100,
   "ang":90,"nets":{"1":"VREF","2":"GND"}},
  {"lib":"Device:C","ref":"C6","val":"100n","fp":FP_CDISC,"x":150,"y":100,
   "nets":{"1":"VREF","2":"GND"}},
  # regulator: LM358-A + BD139 emitterfoelger, unity-feedback fra udgangen
  {"lib":"Amplifier_Operational:LM358","ref":"U1","val":"LM358","fp":FP_DIP8,
   "x":170,"y":85,"unit":1,"nets":{"3":"VREF","2":"V3_OUT","1":"U1A_OUT"}},
  {"lib":"Device:R","ref":"R4","val":"1k00","fp":FP_R,"x":185,"y":85,"ang":90,
   "nets":{"1":"U1A_OUT","2":"Q1_B"}},
  # TIP41A TO-220: 1=B 2=C 3=E (BD139/TO-126 droppet - 2.28mm pitch kan ikke
  # overholde laser-guidens 0.8mm clearance; TIP41A er ogsaa bedre termisk)
  {"lib":"Transistor_BJT:TIP41A","ref":"Q1","val":"TIP41A","fp":FP_TO220,"x":200,"y":85,
   "nets":{"1":"Q1_B","2":"PV_BUS","3":"V3_OUT"}},
  {"lib":"Device:C_Polarized","ref":"C5","val":"47u","fp":FP_CP8,"x":215,"y":95,
   "nets":{"1":"V3_OUT","2":"GND"}},
  # lavside stroemshunt 2x1R00 parallel = 0.5 ohm (2x for effekt: 0.6A -> 0.36W)
  {"lib":"Device:R","ref":"R5","val":"1R00","fp":FP_R,"x":55,"y":115,
   "nets":{"1":"PV_RET","2":"GND"}},
  {"lib":"Device:R","ref":"R6","val":"1R00","fp":FP_R,"x":65,"y":115,
   "nets":{"1":"PV_RET","2":"GND"}},
  # inverterende stroemmaaler: PV_RET er negativ (returstroem), gain -9.09
  {"lib":"Device:R","ref":"R7","val":"1k00","fp":FP_R,"x":150,"y":120,
   "nets":{"1":"PV_RET","2":"U1B_FB"}},
  {"lib":"Amplifier_Operational:LM358","ref":"U1","val":"LM358","fp":FP_DIP8,
   "x":170,"y":120,"unit":2,"nets":{"5":"GND","6":"U1B_FB","7":"PV_I"}},
  {"lib":"Device:R","ref":"R8","val":"9k09","fp":FP_R,"x":170,"y":108,
   "nets":{"1":"U1B_FB","2":"PV_I"}},
  # LM358 forsyning = PV_BUS (op til ~21 V, ok for LM358 max 32 V)
  {"lib":"Amplifier_Operational:LM358","ref":"U1","val":"LM358","fp":FP_DIP8,
   "x":170,"y":140,"unit":3,"nets":{"8":"PV_BUS","4":"GND"}},
  {"lib":"Device:C","ref":"C4","val":"100n","fp":FP_CDISC,"x":185,"y":140,
   "nets":{"1":"PV_BUS","2":"GND"}},
  # PWR_FLAGs: forsyningsnettene drives af J1, ikke af power-outputs
  {"lib":"power:PWR_FLAG","ref":"#FLG01","val":"PWR_FLAG","x":210,"y":140,
   "nets":{"1":"PV_BUS"}},
  {"lib":"power:PWR_FLAG","ref":"#FLG02","val":"PWR_FLAG","x":220,"y":140,
   "nets":{"1":"GND"}},
  # udgange
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J2","val":"til lager (V3)","fp":FP_TERM2,
   "x":235,"y":95,"ang":180,"nets":{"1":"V3_OUT","2":"GND"}},
  {"lib":"Connector_Generic:Conn_01x03","ref":"J3","val":"sense -> Arduino","fp":FP_HDR3,
   "x":235,"y":120,"ang":180,"nets":{"1":"PV_V","2":"PV_I","3":"GND"}},
]

if __name__ == "__main__":
    build("PV front-end  (PV -> 1N5817 -> ~15 mF -> diskret 5V-regulator -> lager + sense)",
          "system", comps, [], {"GND"},
          Path(__file__).parent / "mppt.kicad_sch")

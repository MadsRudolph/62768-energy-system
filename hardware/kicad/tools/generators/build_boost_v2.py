#!/usr/bin/env python3
"""
Boost v2  (5 V -> 10 V, Krav 8/9) med on-board IR2110 gate-driver.

Samme effekttrin som det oprindelige boost-board (lavside-switch: M1 drain = SW,
source = GND), men den langsomme bare-4N25 gate-drive er erstattet af den rigtige
opto -> IR2110 -> MOSFET kaede fra drive_circuit (Exp 3A):

    PWM -> R1(200) -> CNY17 LED      (isolation)
    CNY17 transistor (collector=+15V, emitter=LIN, R2 1k pulldown) -> IR2110 LIN
    IR2110 LO -> R3(10) || D2(1N4007 anti-parallel) -> M1 gate ; R4(1k) pulldown

Lavside => IR2110 LO (pin 1), VS=GND, ingen bootstrap. HIN/SD tied low.
Drive-forsyning = separat +15V (J4). Isolation: GND_MCU (PWM-side) adskilt fra GND.

Pin-koordinater laeses automatisk af schbuild ud af stock-symbolbibliotekerne, og
footprints saettes ved genereringen. Koer:  py -3.13 build_boost_v2.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))   # schbuild ligger i tools/
from schbuild import build

FP_R    = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_TERM = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
FP_HDR  = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_DIP6 = "Package_DIP:DIP-6_W7.62mm_LongPads"
FP_DIP14= "Package_DIP:DIP-14_W7.62mm_LongPads"
FP_TO   = "energy_system:TO-220-3_Vertical_LaserPads"
FP_TOR  = "energy_system:L_Toroid_Vertical_L34.5mm_W15.0mm_P28.20mm_LaserPads"
FP_CP   = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
FP_CDISC= "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_DO41 = "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal"

comps = [
  # --- effekttrin (lavside boost, samme som boost v1) ---
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J1","val":"lager ind (5V)","fp":FP_TERM,
   "x":50,"y":60,"nets":{"1":"VIN_5V","2":"GND"}},
  {"lib":"Device:L","ref":"L1","val":"470u","fp":FP_TOR,"x":75,"y":55,"ang":90,
   "nets":{"1":"VIN_5V","2":"SW"}},
  {"lib":"Device:Q_NMOS","ref":"M1","val":"IRF530","fp":FP_TO,"x":100,"y":60,
   "nets":{"G":"GATE","D":"SW","S":"GND"}},
  {"lib":"Device:D_Schottky","ref":"D1","val":"1N5819","fp":FP_DO41,"x":120,"y":50,"ang":180,
   "nets":{"2":"SW","1":"VOUT_V2"}},                         # 1=K, 2=A -> anode=SW
  {"lib":"Device:C_Polarized","ref":"C1","val":"47u","fp":FP_CP,"x":135,"y":60,
   "nets":{"1":"VOUT_V2","2":"GND"}},
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J2","val":"V2 ud (10V)","fp":FP_TERM,
   "x":160,"y":60,"ang":180,"nets":{"1":"VOUT_V2","2":"GND"}},
  # --- gate-driver: opto -> IR2110 LO -> gate ---
  {"lib":"Connector_Generic:Conn_01x02","ref":"J3","val":"PWM (isoleret)","fp":FP_HDR,
   "x":40,"y":110,"nets":{"1":"PWM","2":"GND_MCU"}},
  {"lib":"Device:R","ref":"R1","val":"200","fp":FP_R,"x":55,"y":110,
   "nets":{"1":"PWM","2":"OPTO_A"}},                         # LED serie-R
  {"lib":"Isolator:4N25","ref":"U1","val":"CNY17","fp":FP_DIP6,"x":80,"y":110,
   "nets":{"1":"OPTO_A","2":"GND_MCU","5":"+15V","4":"LIN"}},  # 1=LED-A,2=LED-K,5=C,4=E
  {"lib":"Device:R","ref":"R2","val":"1k","fp":FP_R,"x":100,"y":125,
   "nets":{"1":"LIN","2":"GND"}},                            # LIN pulldown
  {"lib":"Driver_FET:IR2110","ref":"U2","val":"IR2110","fp":FP_DIP14,"x":125,"y":110,
   "nets":{"9":"+15V","3":"+15V","13":"GND","2":"GND","5":"GND","10":"GND","11":"GND",
           "12":"LIN","1":"LO"}},                            # VDD/VCC=+15, VSS/COM/VS/HIN/SD=GND
  {"lib":"Device:R","ref":"R3","val":"10","fp":FP_R,"x":150,"y":110,
   "nets":{"1":"LO","2":"GATE"}},                            # serie gate-R
  {"lib":"Diode:1N4007","ref":"D2","val":"1N4007","fp":FP_DO41,"x":150,"y":120,
   "nets":{"1":"LO","2":"GATE"}},                            # anti-parallel (1=K=LO,2=A=GATE)
  {"lib":"Device:R","ref":"R4","val":"1k","fp":FP_R,"x":165,"y":125,
   "nets":{"1":"GATE","2":"GND"}},                           # gate pulldown
  {"lib":"Device:C_Polarized","ref":"C2","val":"22u","fp":FP_CP,"x":95,"y":98,
   "nets":{"1":"+15V","2":"GND"}},                           # bulk decoupling
  {"lib":"Device:C","ref":"C3","val":"100n","fp":FP_CDISC,"x":108,"y":98,
   "nets":{"1":"+15V","2":"GND"}},                           # HF decoupling (skal staa fri af IR2110 VDD-stub)
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J4","val":"drive +15V","fp":FP_TERM,
   "x":40,"y":90,"nets":{"1":"+15V","2":"GND"}},
  # --- PWR_FLAGs: forsyningsnettene drives udefra (J1/J4), ikke af power-outputs ---
  {"lib":"power:PWR_FLAG","ref":"#FLG01","val":"PWR_FLAG","x":40,"y":140,"nets":{"1":"+15V"}},
  {"lib":"power:PWR_FLAG","ref":"#FLG02","val":"PWR_FLAG","x":55,"y":140,"nets":{"1":"GND"}},
  {"lib":"power:PWR_FLAG","ref":"#FLG03","val":"PWR_FLAG","x":70,"y":140,"nets":{"1":"VIN_5V"}},
]

ncs = [  # IR2110 ubrugt: HO,VB,NC,NC,NC  +  CNY17 NC/base
  ("Driver_FET:IR2110","7",125,110,0,1), ("Driver_FET:IR2110","6",125,110,0,1),
  ("Driver_FET:IR2110","4",125,110,0,1), ("Driver_FET:IR2110","8",125,110,0,1),
  ("Driver_FET:IR2110","14",125,110,0,1),
  ("Isolator:4N25","3",80,110,0,1), ("Isolator:4N25","6",80,110,0,1),
]
globals_ = {"PWM","+15V","GND","GND_MCU","VIN_5V","VOUT_V2","GATE"}

if __name__ == "__main__":
    out = Path(__file__).parents[2] / "boards/boost/boost_v2/boost_v2.kicad_sch"
    out.parent.mkdir(parents=True, exist_ok=True)
    build("Boost v2  5V->10V  (IR2110 gate drive, lavside)", "energy_system",
          comps, ncs, globals_, str(out))

#!/usr/bin/env python3
"""
MPPT buck  (PV 17.6 V -> 5 V lager) med IR2110 HIGH-SIDE driver, styret af Arduino-PWM
(Perturb & Observe). Erstatter det LINEAERE mppt-board (TIP41A + LM358 servo).

Samme gate-driver som buck_v2 (high-side: HO + bootstrap), men UDEN NE555 - dutyen
saettes 100% af Arduinoen. Sensing er eksternt (INA219), saa boardet er kun:
effekttrin + gate-driver + PV-indgangskondensator.

Effekt-dimensionering (P_MPP ~10W, Vout 5V => ~2A ud, vs buck_v2's lette last):
  - Friloebsdiode D1: >=3A Schottky (1N5822 40V/3A) paa DO-201AD - IKKE 1N5819 (1A).
  - L1: L = Vout(Vin-Vout)/(dIL*f*Vin); ved Vin=17.6 Vout=5 dIL=0.6A:
        f=31kHz -> ~174uH, f=62kHz -> ~87uH. Sat 150u (31kHz). HAANDVIKLET -> juster.
  - C1 PV-bulk: >=25V (Voc 20.3V). 470u/25V + keramik. MAAL den fysiske kolbe.

Verificeres via ERC + netliste. Koer: py -3.13 build_mppt_buck.py
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
FP_CP   = "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"           # MAAL de rigtige kolber
FP_CDISC= "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_DO201= "Diode_THT:D_DO-201AD_P15.24mm_Horizontal"         # ~3A Schottky friloeb
FP_DO35 = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"       # 1N4148 boot/gate

comps = [
  # --- effekttrin (high-side buck: PV -> SW -> L -> 5V lager) ---
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J1","val":"PV ind","fp":FP_TERM,
   "x":45,"y":60,"nets":{"1":"VPV","2":"GND"}},
  {"lib":"Device:C_Polarized","ref":"C1","val":"470u/25V","fp":FP_CP,"x":60,"y":60,
   "nets":{"1":"VPV","2":"GND"}},                            # PV bulk; >=25V, MAAL
  {"lib":"Device:Q_NMOS","ref":"Q1","val":"IRF530","fp":FP_TO,"x":82,"y":58,
   "nets":{"D":"VPV","G":"GATE","S":"SW"}},                  # high-side switch
  {"lib":"Device:D_Schottky","ref":"D1","val":"1N5822","fp":FP_DO201,"x":100,"y":70,"ang":270,
   "nets":{"1":"SW","2":"GND"}},                             # friloeb: K=SW,A=GND; >=3A
  {"lib":"Device:L","ref":"L1","val":"150u","fp":FP_TOR,"x":120,"y":58,"ang":90,
   "nets":{"1":"SW","2":"VOUT_5V"}},                         # dimensioner efter f (se hoved)
  {"lib":"Device:C_Polarized","ref":"C2","val":"47u","fp":FP_CP,"x":140,"y":60,
   "nets":{"1":"VOUT_5V","2":"GND"}},                        # lokal udgangskondensator
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J2","val":"lager ud (5V)","fp":FP_TERM,
   "x":160,"y":60,"ang":180,"nets":{"1":"VOUT_5V","2":"GND"}},
  # --- gate-driver: opto -> IR2110 HO + bootstrap (PWM fra Arduino, INGEN 555) ---
  {"lib":"Connector_Generic:Conn_01x02","ref":"J3","val":"PWM (Arduino)","fp":FP_HDR,
   "x":40,"y":110,"nets":{"1":"PWM","2":"GND_MCU"}},
  {"lib":"Device:R","ref":"R1","val":"200","fp":FP_R,"x":55,"y":110,
   "nets":{"1":"PWM","2":"OPTO_A"}},
  {"lib":"Isolator:4N25","ref":"U1","val":"CNY17","fp":FP_DIP6,"x":80,"y":110,
   "nets":{"1":"OPTO_A","2":"GND_MCU","5":"+15V","4":"HIN"}},  # 1=LED-A,2=LED-K,5=C,4=E
  {"lib":"Device:R","ref":"R2","val":"1k","fp":FP_R,"x":100,"y":125,
   "nets":{"1":"HIN","2":"GND"}},                            # HIN pulldown
  {"lib":"Driver_FET:IR2110","ref":"U2","val":"IR2110","fp":FP_DIP14,"x":125,"y":108,
   "nets":{"9":"+15V","3":"+15V","13":"GND","2":"GND","12":"GND","11":"GND",
           "10":"HIN","7":"HO","6":"VB","5":"SW"}},          # high-side: VS=SW,VB,HO; LIN/SD=GND
  {"lib":"Device:R","ref":"R3","val":"10","fp":FP_R,"x":152,"y":108,
   "nets":{"1":"HO","2":"GATE"}},                            # serie gate-R
  {"lib":"Diode:1N4148","ref":"D3","val":"1N4148","fp":FP_DO35,"x":152,"y":118,
   "nets":{"1":"HO","2":"GATE"}},                            # anti-parallel (K=HO,A=GATE)
  {"lib":"Device:R","ref":"R4","val":"1k","fp":FP_R,"x":167,"y":118,
   "nets":{"1":"GATE","2":"SW"}},                            # gate pulldown -> SW (high-side ref)
  {"lib":"Diode:1N4148","ref":"D2","val":"1N4148","fp":FP_DO35,"x":140,"y":90,
   "nets":{"1":"VB","2":"+15V"}},                            # boot-diode: K=VB,A=+15V
  {"lib":"Device:C","ref":"C3","val":"1u","fp":FP_CDISC,"x":152,"y":94,
   "nets":{"1":"VB","2":"SW"}},                              # boot-cap VB->VS(SW); MAAL
  {"lib":"Device:C_Polarized","ref":"C4","val":"22u","fp":FP_CP,"x":100,"y":92,
   "nets":{"1":"+15V","2":"GND"}},                           # +15V bulk-afkobling
  {"lib":"Device:C","ref":"C5","val":"100n","fp":FP_CDISC,"x":113,"y":92,
   "nets":{"1":"+15V","2":"GND"}},                           # +15V HF-afkobling
  {"lib":"Connector:Screw_Terminal_01x02","ref":"J4","val":"drive +15V","fp":FP_TERM,
   "x":40,"y":92,"nets":{"1":"+15V","2":"GND"}},
  # --- PWR_FLAGs: forsyninger drives udefra (J1/J4) ---
  {"lib":"power:PWR_FLAG","ref":"#FLG01","val":"PWR_FLAG","x":45,"y":140,"nets":{"1":"+15V"}},
  {"lib":"power:PWR_FLAG","ref":"#FLG02","val":"PWR_FLAG","x":60,"y":140,"nets":{"1":"GND"}},
  {"lib":"power:PWR_FLAG","ref":"#FLG03","val":"PWR_FLAG","x":75,"y":140,"nets":{"1":"VPV"}},
]

ncs = [  # IR2110 ubrugt: LO(1), NC 4/8/14  +  CNY17 NC/base 3/6
  ("Driver_FET:IR2110","1",125,108,0,1), ("Driver_FET:IR2110","4",125,108,0,1),
  ("Driver_FET:IR2110","8",125,108,0,1), ("Driver_FET:IR2110","14",125,108,0,1),
  ("Isolator:4N25","3",80,110,0,1), ("Isolator:4N25","6",80,110,0,1),
]
globals_ = {"PWM","+15V","GND","GND_MCU","VPV","VOUT_5V","SW"}

if __name__ == "__main__":
    out = Path(__file__).parents[2] / "boards/mppt_buck/mppt_buck.kicad_sch"
    out.parent.mkdir(parents=True, exist_ok=True)
    build("MPPT buck  PV 17.6V -> 5V lager  (Arduino P&O, IR2110 high-side)",
          "energy_system", comps, ncs, globals_, str(out))

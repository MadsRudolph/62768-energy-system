#!/usr/bin/env python3
"""
C2000 feedback-/sensorprint (TI-port) - INTEGRERET-SYSTEM revision (2026-06-27).

Front-end mellem effektsystemet og LAUNCHXL-F28027. Alt skaleret til
0..3.3 V (C2000 ADC abs-max = 3.3 V). Jf. docs/c2000-pinmap.md og
docs/superpowers/specs/2026-06-27-system-integrated-pcb-interface-contract.md.

Reduceret til **kun 3 spaendingskanaler** til C2000'ens PID-loops:
  V1   : motor-bus 15 V -> 10k/1k (/11) -> ~1.36 V
  LOAD : boost-udgang   -> 12k/2k (/7)  -> op til 3.3 V
  STORE: 5 V-lager      -> 2k/1k  (/3)  -> ~1.67 V
hver: deler -> 1k serie + 3.0 V zener-klemme + 10n -> ADC.

FJERNET ift. den gamle standalone-version (split-MCU + integreret board):
  - I1/I2/I3 stroemkanaler (MCP601) -> stroem maales nu af current_sense -> Arduino.
  - PWM-pass (EPWM1A -> 220R -> opto) -> C2000 EPWM gaar direkte til hver konverters
    egen opto-frontend paa top-arket. (NB drive-strength: en EPWM-GPIO @3.3 V kan ikke
    noedvendigvis traekke ~10 mA gennem optoens 200R - se kontrakten, evt. NPN-buffer.)

NB net-labels forbinder paa navn, ikke geometri -> komponenter spredt med god
afstand (auto-stub kortslutter ellers naboben). Kør: py -3.13 build_c2000_feedback.py
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))   # schbuild ligger i tools/
from schbuild import build

FP_TERM2 = "TerminalBlock:TerminalBlock_bornier-2_P5.08mm"
FP_CDISC = "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm"
FP_R     = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal"
FP_DO35  = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
FP_HDR2  = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_HDR3  = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
SCREW = "Connector:Screw_Terminal_01x02"


def vchan(k, y, rhigh, rlow, jref, name):
    """Spaendingskanal: deler -> serie-R -> zener-klemme -> 10n -> ADC."""
    rail, tap, adc = f"V{k}IN", f"TAP{k}", f"ADCV{k}"
    return [
        {"lib": SCREW, "ref": jref, "val": f"{name} in", "fp": FP_TERM2,
         "x": 35, "y": y, "nets": {"1": rail, "2": "GND"}},
        {"lib": "Device:R", "ref": f"RV{k}1", "val": rhigh, "fp": FP_R, "x": 62, "y": y,
         "nets": {"1": rail, "2": tap}},
        {"lib": "Device:R", "ref": f"RV{k}2", "val": rlow, "fp": FP_R, "x": 62, "y": y + 14,
         "nets": {"1": tap, "2": "GND"}},
        {"lib": "Device:R", "ref": f"RV{k}3", "val": "1k00", "fp": FP_R, "x": 90, "y": y,
         "nets": {"1": tap, "2": adc}},
        {"lib": "Device:D_Zener", "ref": f"DV{k}", "val": "BZX55C3V0", "fp": FP_DO35,
         "x": 118, "y": y, "nets": {"1": adc, "2": "GND"}},   # 1=K -> ADC, 2=A -> GND
        {"lib": "Device:C", "ref": f"CV{k}", "val": "10n", "fp": FP_CDISC, "x": 118, "y": y + 14,
         "nets": {"1": adc, "2": "GND"}},
    ]


# NB: skrueterminaler = ulige J (venstre kant), MCU-headers = lige J (hoejre kant)
comps = (
    vchan(1, 35, "10k0", "1k00", "J1", "V1") +      # motor-bus 15 V (/11)
    vchan(2, 75, "12k0", "2k00", "J3", "LOAD") +    # boost-udgang (/7)
    vchan(3, 115, "2k00", "1k00", "J5", "STORE") +  # 5 V lager (/3)
    [
        # interface til LaunchPad - korte headers (lang header kortslutter i auto-stub)
        {"lib": "Connector_Generic:Conn_01x02", "ref": "J2", "val": "+3V3/GND (LaunchPad)",
         "fp": FP_HDR2, "x": 195, "y": 40, "ang": 180,
         "nets": {"1": "+3V3", "2": "GND"}},
        {"lib": "Connector_Generic:Conn_01x03", "ref": "J4", "val": "V1/LOAD/STORE -> ADC",
         "fp": FP_HDR3, "x": 195, "y": 80, "ang": 180,
         "nets": {"1": "ADCV1", "2": "ADCV2", "3": "ADCV3"}},
        # +3V3/GND kommer udefra (LaunchPad) via J2
        {"lib": "power:PWR_FLAG", "ref": "#FLG1", "val": "PWR_FLAG", "x": 225, "y": 40,
         "nets": {"1": "+3V3"}},
        {"lib": "power:PWR_FLAG", "ref": "#FLG2", "val": "PWR_FLAG", "x": 225, "y": 80,
         "nets": {"1": "GND"}},
    ]
)

ncs = []   # ingen IC'er -> ingen NC-ben at binde

if __name__ == "__main__":
    build("C2000 feedback/sensor (3.3 V): V1/LOAD/STORE delere -> ADC (split-MCU revision)",
          "c2000_feedback", comps, ncs, {"+3V3", "GND"},
          Path(__file__).parents[2] / "boards/c2000_feedback/c2000_feedback.kicad_sch")

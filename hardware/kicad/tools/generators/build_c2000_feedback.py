#!/usr/bin/env python3
"""
C2000 feedback-/sensorprint (TI-port).

Front-end mellem effektsystemet og LAUNCHXL-F28027. Alt skaleret til
0..3.3 V (C2000 ADC abs-max = 3.3 V). Jf. docs/c2000-pinmap.md.

6 kanaler + PWM-pass:
  Spaending  V1/V2/V3 : modstandsdeler -> 1k serie + 3.0 V zener-klemme + 10n
               V1 10k/1k (/11), V2 12k/2k (/7), V3 2k/1k (/3)
  Stroem     I1/I2    : lavside 1R-shunt + MCP601 ikke-inv. (gain 7.5 / 10),
                        forsynet fra +3V3 -> udgang kan ikke overstige 3.3 V
  Stroem     I3 (bidir): 1R-shunt + MCP601 differensforstaerker (gain 5)
                        refereret til 1.65 V midt-skala (lager lader+aflader)
  PWM        EPWM1A fra C2000 -> 220R -> drivkreds-opto (CNY17)

MCP601 (rail-to-rail udgang, CMOS) valgt frem for LM358: ved 3V3-forsyning
naar LM358 kun ~1.8 V ud - for lavt. MCP601 naar ~3.3 V. Indgange gaar til GND.

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
FP_DIP8  = "Package_DIP:DIP-8_W7.62mm_LongPads"
FP_DO35  = "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
FP_HDR2  = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
FP_HDR3  = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
MCP = "Amplifier_Operational:MCP601-xP"   # pins 3=+ 2=- 6=ud 7=V+ 4=V-  (1/5/8 NC)
SCREW = "Connector:Screw_Terminal_01x02"


def vchan(k, y, rhigh, rlow, jref):
    """Spaendingskanal: deler -> serie-R -> zener-klemme -> 10n -> ADC."""
    rail, tap, adc = f"V{k}IN", f"TAP{k}", f"ADCV{k}"
    return [
        {"lib": SCREW, "ref": jref, "val": f"V{k} in", "fp": FP_TERM2,
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


def ichan_ni(k, y, uref, rf, jref):
    """Ikke-inverterende stroemkanal (unidirektionel): 1R-shunt + MCP601."""
    ret, fb, out = f"RET{k}", f"FB{k}", f"ISENSE{k}"
    return [
        {"lib": SCREW, "ref": jref, "val": f"I{k} retur", "fp": FP_TERM2,
         "x": 35, "y": y, "nets": {"1": ret, "2": "GND"}},
        {"lib": "Device:R", "ref": f"RSH{k}", "val": "1R00", "fp": FP_R, "x": 60, "y": y + 16,
         "nets": {"1": ret, "2": "GND"}},
        {"lib": MCP, "ref": uref, "val": "MCP601", "fp": FP_DIP8, "x": 92, "y": y,
         "nets": {"3": ret, "2": fb, "6": out, "7": "+3V3", "4": "GND"}},
        {"lib": "Device:R", "ref": f"RG{k}", "val": "1k00", "fp": FP_R, "x": 70, "y": y + 28,
         "nets": {"1": fb, "2": "GND"}},
        {"lib": "Device:R", "ref": f"RF{k}", "val": rf, "fp": FP_R, "x": 118, "y": y,
         "nets": {"1": fb, "2": out}},
        {"lib": "Device:C", "ref": f"CD{k}", "val": "100n", "fp": FP_CDISC, "x": 150, "y": y,
         "nets": {"1": "+3V3", "2": "GND"}},
    ]


def ichan_diff(y, uref, jref):
    """Bidirektionel stroemkanal I3: differensforstaerker refereret til 1.65 V."""
    ret, nin, pin_, out, vb = "RET3", "N3", "P3", "ISENSE3", "VBIAS"
    return [
        {"lib": SCREW, "ref": jref, "val": "I3 retur (bidir)", "fp": FP_TERM2,
         "x": 35, "y": y, "nets": {"1": ret, "2": "GND"}},
        {"lib": "Device:R", "ref": "RSH3", "val": "1R00", "fp": FP_R, "x": 60, "y": y + 16,
         "nets": {"1": ret, "2": "GND"}},
        {"lib": MCP, "ref": uref, "val": "MCP601", "fp": FP_DIP8, "x": 100, "y": y,
         "nets": {"3": pin_, "2": nin, "6": out, "7": "+3V3", "4": "GND"}},
        {"lib": "Device:R", "ref": "R31", "val": "10k0", "fp": FP_R, "x": 75, "y": y,
         "nets": {"1": ret, "2": nin}},                      # RET3 -> IN-
        {"lib": "Device:R", "ref": "R32", "val": "49k9", "fp": FP_R, "x": 128, "y": y,
         "nets": {"1": nin, "2": out}},                      # IN- -> ud (feedback)
        {"lib": "Device:R", "ref": "R33", "val": "10k0", "fp": FP_R, "x": 75, "y": y + 16,
         "nets": {"1": "GND", "2": pin_}},                   # GND -> IN+
        {"lib": "Device:R", "ref": "R34", "val": "49k9", "fp": FP_R, "x": 100, "y": y + 16,
         "nets": {"1": pin_, "2": vb}},                      # IN+ -> VBIAS
        {"lib": "Device:C", "ref": "CD3", "val": "100n", "fp": FP_CDISC, "x": 158, "y": y,
         "nets": {"1": "+3V3", "2": "GND"}},
    ]


# NB: skrueterminaler = ulige J (venstre kant), MCU-headers = lige J (hoejre kant)
comps = (
    vchan(1, 35, "10k0", "1k00", "J1") +
    vchan(2, 75, "12k0", "2k00", "J3") +
    vchan(3, 115, "2k00", "1k00", "J5") +
    ichan_ni(1, 165, "U1", "6k49", "J7") +    # gain 7.49 -> 400 mA -> 3.0 V
    ichan_ni(2, 210, "U2", "9k09", "J9") +    # gain 10.09 -> 300 mA -> 3.03 V
    ichan_diff(255, "U3", "J11") +            # gain 5, 1.65 V midt -> +/-300 mA -> 0.15..3.15 V
    [
        # I3 1.65 V bias-deler (placeret frit - VBIAS forbindes paa navn)
        {"lib": "Device:R", "ref": "RB1", "val": "1k00", "fp": FP_R, "x": 165, "y": 255,
         "nets": {"1": "+3V3", "2": "VBIAS"}},
        {"lib": "Device:R", "ref": "RB2", "val": "1k00", "fp": FP_R, "x": 165, "y": 271,
         "nets": {"1": "VBIAS", "2": "GND"}},
        {"lib": "Device:C", "ref": "CB", "val": "1u", "fp": FP_CDISC, "x": 190, "y": 263,
         "nets": {"1": "VBIAS", "2": "GND"}},
        # PWM-pass: EPWM1A -> 220R -> drivkreds-opto
        {"lib": "Device:R", "ref": "RPWM", "val": "220R", "fp": FP_R, "x": 165, "y": 40,
         "nets": {"1": "PWMMCU", "2": "PWMDRV"}},
        {"lib": SCREW, "ref": "J10", "val": "til drivkreds", "fp": FP_TERM2,
         "x": 195, "y": 40, "nets": {"1": "PWMDRV", "2": "GND"}},   # lige J -> hoejre kant (ved RPWM/J8)
        # interface til LaunchPad - korte headers (lang 1x10 kortslutter i auto-stub)
        {"lib": "Connector_Generic:Conn_01x02", "ref": "J2", "val": "+3V3/GND (LaunchPad)",
         "fp": FP_HDR2, "x": 195, "y": 95, "ang": 180,
         "nets": {"1": "+3V3", "2": "GND"}},
        {"lib": "Connector_Generic:Conn_01x03", "ref": "J4", "val": "V1/V2/V3 -> ADC",
         "fp": FP_HDR3, "x": 195, "y": 130, "ang": 180,
         "nets": {"1": "ADCV1", "2": "ADCV2", "3": "ADCV3"}},
        {"lib": "Connector_Generic:Conn_01x03", "ref": "J6", "val": "I1/I2/I3 -> ADC",
         "fp": FP_HDR3, "x": 195, "y": 165, "ang": 180,
         "nets": {"1": "ISENSE1", "2": "ISENSE2", "3": "ISENSE3"}},
        {"lib": "Connector_Generic:Conn_01x02", "ref": "J8", "val": "EPWM1A in + GND",
         "fp": FP_HDR2, "x": 195, "y": 65, "ang": 180,
         "nets": {"1": "PWMMCU", "2": "GND"}},
        # +3V3/GND kommer udefra (LaunchPad) via JMCU
        {"lib": "power:PWR_FLAG", "ref": "#FLG1", "val": "PWR_FLAG", "x": 225, "y": 95,
         "nets": {"1": "+3V3"}},
        {"lib": "power:PWR_FLAG", "ref": "#FLG2", "val": "PWR_FLAG", "x": 225, "y": 165,
         "nets": {"1": "GND"}},
    ]
)

# MCP601 NC-ben (1/5/8) -> no-connect, holder ERC ren
ncs = []
for uref, (ox, oy) in (("U1", (92, 165)), ("U2", (92, 210)), ("U3", (100, 255))):
    for p in ("1", "5", "8"):
        ncs.append((MCP, p, ox, oy, 0, 1))

if __name__ == "__main__":
    build("C2000 feedback/sensor (3.3 V): V1/V2/V3 delere + I1/I2/I3 MCP601 + PWM-pass",
          "c2000_feedback", comps, ncs, {"+3V3", "GND"},
          Path(__file__).parents[2] / "boards/c2000_feedback/c2000_feedback.kicad_sch")

"""
Buck converter (15 V -> 5 V) -- SpicePilot / PySpice generator.

Generates an LTspice-compatible SPICE netlist (buck.net) for the 62768
energy-system buck stage: rectifier bus V1 (15 V) stepped down to ~5 V to
charge the 1 F energy store (V3 = 5 V).

Design (see README.md), from the Lec 2 / Lec 5 converter formulas:
    Vin  = 15 V, Vout = 5 V  ->  D = Vout/Vin = 0.333
    fsw  = 50 kHz
    L    = 470 uH  (continuous conduction, ~28% peak-peak inductor ripple)
    C    = 47 uF   (output voltage ripple < 10 mV)
    Rload= 10 ohm  (~0.5 A bench load)

The switch + diode are ideal-ish SPICE models for this first design pass.
The real, discrete build uses an IRF540N MOSFET + high-side gate driver
(IR2110, see Exp 3A) and a Schottky freewheel diode -- swap those in later.

Run:   py -3.13 buck_converter.py
Open:  buck.net in LTspice  (File > Open, then Run)
"""
import os
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# ---------------- design parameters ----------------
Vin   = 15.0      # V  rectifier bus (V1)
Vout  = 5.0       # V  target output (charges the V3 store)
fsw   = 50e3      # Hz switching frequency
duty  = Vout / Vin                 # ideal buck duty = 0.333
L     = 470e-6    # H  filter inductor
C     = 47e-6     # F  output capacitor
Rload = 10.0      # ohm  bench load (~0.5 A at 5 V)

period = 1.0 / fsw
pw     = duty * period             # gate on-time

# ---------------- build circuit (PySpice) ----------------
c = Circuit('Buck 15V to 5V - 62768 energy system')

# input bus
c.V('in', 'in', c.gnd, Vin @ u_V)

# gate drive: 0..5 V PWM at fsw, duty = D
c.PulseVoltageSource('gate', 'gate', c.gnd,
                     initial_value=0 @ u_V, pulsed_value=5 @ u_V,
                     delay_time=0 @ u_s, rise_time=10 @ u_ns,
                     fall_time=10 @ u_ns, pulse_width=pw @ u_s,
                     period=period @ u_s)

# high-side switch:  in -> sw   (closes when gate > Vt)
c.raw_spice += 'S1 in sw gate 0 MYSW\n'
# freewheel diode:   anode = gnd, cathode = sw
c.Diode('1', c.gnd, 'sw', model='MYDIODE')
# output filter
c.L('1', 'sw', 'out', L @ u_H)
c.C('1', 'out', c.gnd, C @ u_F)
c.R('load', 'out', c.gnd, Rload @ u_Ohm)

# device models (ideal switch + Schottky-ish diode)
c.raw_spice += '.model MYSW SW(Ron=20m Roff=1Meg Vt=2.5 Vh=0.1)\n'
c.model('MYDIODE', 'D', IS=1e-9, N=1, RS=20e-3)

# transient + measurements (read back from the .log after a batch run)
c.raw_spice += '.tran 0 5m 0 1u\n'
c.raw_spice += '.meas TRAN Vout_avg AVG V(out) FROM 4m TO 5m\n'
c.raw_spice += '.meas TRAN Vout_pp  PP  V(out) FROM 4m TO 5m\n'
c.raw_spice += '.meas TRAN IL_pp    PP  I(L1)  FROM 4m TO 5m\n'

# ---------------- emit netlist ----------------
netlist = str(c)
if '.end' not in netlist.lower():
    netlist = netlist.rstrip() + '\n.end\n'

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'buck.net')
with open(out_path, 'w') as f:
    f.write(netlist)

print(netlist)
print('--- wrote', out_path)
print(f'--- D={duty:.3f}  pw={pw*1e6:.2f}us  period={period*1e6:.2f}us')

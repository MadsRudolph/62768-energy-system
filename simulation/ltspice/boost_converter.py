"""
Boost converter (5 V -> 15 V) -- SpicePilot / PySpice generator.

Generates an LTspice-compatible SPICE netlist (boost.net) for the 62768
energy-system boost stage: the 1 F energy store (V3 = 5 V) stepped up to
~15 V to drive the pulsing load (V2).

Design (see README.md), from the Lec 2 / Lec 5 converter formulas:
    Vin  = 5 V, Vout = 15 V  ->  D = 1 - Vin/Vout = 0.667
    fsw  = 50 kHz
    L    = 470 uH  (continuous conduction, ~31% peak-peak inductor ripple)
    C    = 47 uF   (output voltage ripple < 0.1 V)
    Rload= 100 ohm (150 mA at 15 V)

The switch + diode are ideal-ish SPICE models for this first design pass.
The real, discrete build uses an IRF530N MOSFET + gate driver (low-side here,
simpler than the buck) and a Schottky output diode -- swap those in later.

Run:   py -3.13 boost_converter.py
Open:  boost.net in LTspice  (File > Open, then Run)
"""
import os
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# ---------------- design parameters ----------------
Vin   = 5.0       # V  energy store (V3)
Vout  = 15.0      # V  target output (pulsing load V2)
fsw   = 50e3      # Hz switching frequency
duty  = 1.0 - Vin / Vout           # ideal boost duty = 0.667
L     = 470e-6    # H  input inductor
C     = 47e-6     # F  output capacitor
Rload = 100.0     # ohm  load (~150 mA at 15 V)

period = 1.0 / fsw
pw     = duty * period             # gate on-time

# ---------------- build circuit (PySpice) ----------------
c = Circuit('Boost 5V to 15V - 62768 energy system')

# input from the store
c.V('in', 'in', c.gnd, Vin @ u_V)

# gate drive: 0..5 V PWM at fsw, duty = D
c.PulseVoltageSource('gate', 'gate', c.gnd,
                     initial_value=0 @ u_V, pulsed_value=5 @ u_V,
                     delay_time=0 @ u_s, rise_time=10 @ u_ns,
                     fall_time=10 @ u_ns, pulse_width=pw @ u_s,
                     period=period @ u_s)

# boost inductor:  in -> sw
c.L('1', 'in', 'sw', L @ u_H)
# low-side switch:  sw -> gnd   (closes when gate > Vt, charging L)
c.raw_spice += 'S1 sw 0 gate 0 MYSW\n'
# output diode:  anode = sw, cathode = out
c.Diode('1', 'sw', 'out', model='MYDIODE')
# output filter
c.C('1', 'out', c.gnd, C @ u_F)
c.R('load', 'out', c.gnd, Rload @ u_Ohm)

# device models (ideal switch + Schottky-ish diode)
c.raw_spice += '.model MYSW SW(Ron=20m Roff=1Meg Vt=2.5 Vh=0.1)\n'
c.model('MYDIODE', 'D', IS=1e-9, N=1, RS=20e-3)

# transient + measurements (read back from the .log after a batch run).
# Output time-constant R*C = 100*47u = 4.7 ms, so run 25 ms (~5 tau) to reach
# steady state, then measure the last switching cycles.
c.raw_spice += '.tran 0 25m 0 1u\n'
c.raw_spice += '.meas TRAN Vout_avg AVG V(out) FROM 24m TO 25m\n'
c.raw_spice += '.meas TRAN Vout_pp  PP  V(out) FROM 24m TO 25m\n'
c.raw_spice += '.meas TRAN IL_pp    PP  I(L1)  FROM 24m TO 25m\n'

# ---------------- emit netlist ----------------
netlist = str(c)
if '.end' not in netlist.lower():
    netlist = netlist.rstrip() + '\n.end\n'

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'boost.net')
with open(out_path, 'w') as f:
    f.write(netlist)

print(netlist)
print('--- wrote', out_path)
print(f'--- D={duty:.3f}  pw={pw*1e6:.2f}us  period={period*1e6:.2f}us')

#!/usr/bin/env python3
"""AD3 test instrument driver for the C2000 F28027 bring-up tests.

Subcommands
-----------
  measure   Capture scope CH1 and report frequency / duty / Vmin / Vmax.
            Used for the GPIO-blink and ePWM tests (steps 3.1 / 3.2).
  awg       Set wavegen W1 to a DC level. HARD-CLAMPED to 0..3.3 V —
            safe to point at an ADC pin. Used for the ADC test (3.3).
  sweep     Step W1 through a series of DC levels (clamped), dwelling at
            each so the live ADC count can be read in Monitor & Tune.
  off       Disable W1 and close cleanly.

Wiring: AD3 GND (black down-arrow lead) -> LaunchPad GND (J2-1). Scope 1+ -> pin under
test, 1- -> GND. W1 (yellow) -> ADC pin ONLY via the awg/sweep commands.

Close the WaveForms GUI first — only one app can own the AD3.

Examples
--------
  python ad3_check.py measure --expect-freq 5000 --expect-duty 50
  python ad3_check.py awg --volts 1.65
  python ad3_check.py sweep --start 0.0 --stop 3.3 --steps 12 --dwell 5
  python ad3_check.py off
"""

import argparse
import sys
import time

from pydwf import (DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction,
                   DwfState, DwfDeviceParameter)
from pydwf.utilities import openDwfDevice

V_ABS_MAX = 3.3  # F28027 absolute max on every pin. Never raise this.


def clamp_voltage(v):
    if v < 0.0 or v > V_ABS_MAX:
        clamped = min(max(v, 0.0), V_ABS_MAX)
        print(f"!! {v:.3f} V outside 0..{V_ABS_MAX} V -> clamped to {clamped:.3f} V")
        return clamped
    return v


def set_w1_dc(device, volts):
    volts = clamp_voltage(volts)
    out = device.analogOut
    ch = 0  # W1
    node = DwfAnalogOutNode.Carrier
    out.nodeEnableSet(ch, node, True)
    out.nodeFunctionSet(ch, node, DwfAnalogOutFunction.DC)
    out.nodeOffsetSet(ch, node, volts)
    out.configure(ch, True)
    return volts


def capture(device, sample_hz, n_samples, ch_range=5.0, attenuation=1.0):
    ain = device.analogIn
    ain.channelEnableSet(0, True)
    ain.channelAttenuationSet(0, attenuation)
    ain.channelRangeSet(0, ch_range)
    ain.frequencySet(sample_hz)
    ain.bufferSizeSet(n_samples)
    ain.configure(False, True)
    while True:
        status = ain.status(True)
        if status == DwfState.Done:
            break
        time.sleep(0.01)
    return ain.statusData(0, n_samples)


def edge_stats(samples, sample_hz):
    """Threshold at mid-level, return (freq_hz, duty_pct, vmin, vmax) or None."""
    vmin, vmax = min(samples), max(samples)
    if vmax - vmin < 0.5:  # no real signal swing
        return None
    mid = 0.5 * (vmin + vmax)
    hyst = 0.05 * (vmax - vmin)
    state = samples[0] > mid
    rising = []
    high_count = 0
    for i, v in enumerate(samples):
        if state and v < mid - hyst:
            state = False
        elif not state and v > mid + hyst:
            state = True
            rising.append(i)
        if v > mid:
            high_count += 1
    if len(rising) < 2:
        return None
    periods = [(b - a) for a, b in zip(rising, rising[1:])]
    avg_period = sum(periods) / len(periods)
    freq = sample_hz / avg_period
    # duty over whole-period span only, to avoid partial-cycle bias
    span = slice(rising[0], rising[-1])
    seg = samples[span]
    duty = 100.0 * sum(1 for v in seg if v > mid) / len(seg)
    return freq, duty, vmin, vmax


def cmd_measure(device, args):
    # Two-pass: rough capture to find the frequency, then a capture scaled
    # so ~20 cycles fill the buffer for a clean duty estimate.
    n = 16384
    att = args.attenuation
    for sample_hz in (10e6, 1e6, 100e3, 10e3, 1e3):
        samples = capture(device, sample_hz, n, attenuation=att)
        stats = edge_stats(samples, sample_hz)
        if stats is None:
            continue
        freq = stats[0]
        cycles_in_buffer = freq * n / sample_hz
        if 4 <= cycles_in_buffer:
            # refine: aim for ~20 cycles in the buffer
            ideal_hz = min(10e6, max(1e3, freq * n / 20))
            samples = capture(device, ideal_hz, n, attenuation=att)
            refined = edge_stats(samples, ideal_hz)
            if refined:
                stats = refined
            break
    else:
        print("FAIL: no periodic signal found on scope CH1 (check probe/GND)")
        return 1

    freq, duty, vmin, vmax = stats
    print(f"CH1: f = {freq:.2f} Hz, duty = {duty:.1f} %, "
          f"Vmin = {vmin:.3f} V, Vmax = {vmax:.3f} V")

    ok = True
    if args.expect_freq is not None:
        tol = args.freq_tol_pct / 100.0 * args.expect_freq
        good = abs(freq - args.expect_freq) <= tol
        print(f"  freq vs {args.expect_freq} Hz +/-{args.freq_tol_pct}%: "
              f"{'PASS' if good else 'FAIL'}")
        ok &= good
    if args.expect_duty is not None:
        good = abs(duty - args.expect_duty) <= args.duty_tol
        print(f"  duty vs {args.expect_duty} % +/-{args.duty_tol}: "
              f"{'PASS' if good else 'FAIL'}")
        ok &= good
    return 0 if ok else 1


def cmd_awg(device, args):
    v = set_w1_dc(device, args.volts)
    print(f"W1 = {v:.3f} V DC (expected ADC count ~ {v * 4095 / 3.3:.0f})")
    print("W1 stays on after this script exits (device closed without reset).")
    return 0


def cmd_sweep(device, args):
    if args.steps < 2:
        print("need at least 2 steps")
        return 1
    for i in range(args.steps):
        v = args.start + (args.stop - args.start) * i / (args.steps - 1)
        v = set_w1_dc(device, v)
        print(f"[{i + 1}/{args.steps}] W1 = {v:.3f} V "
              f"-> expect count ~ {v * 4095 / 3.3:.0f}", flush=True)
        time.sleep(args.dwell)
    print("sweep done — W1 left at final level")
    return 0


def cmd_off(device, args):
    device.analogOut.reset(-1)  # all channels
    print("W1 off")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("measure", help="measure freq/duty on scope CH1")
    m.add_argument("--expect-freq", type=float, default=None)
    m.add_argument("--freq-tol-pct", type=float, default=2.0)
    m.add_argument("--expect-duty", type=float, default=None)
    m.add_argument("--duty-tol", type=float, default=3.0)
    m.add_argument("--attenuation", type=float, default=1.0,
                   help="scope probe attenuation, e.g. 10 for a 10x probe")

    a = sub.add_parser("awg", help="set W1 DC level (clamped 0..3.3 V)")
    a.add_argument("--volts", type=float, required=True)

    s = sub.add_parser("sweep", help="step W1 through DC levels (clamped)")
    s.add_argument("--start", type=float, default=0.0)
    s.add_argument("--stop", type=float, default=3.3)
    s.add_argument("--steps", type=int, default=12)
    s.add_argument("--dwell", type=float, default=5.0)

    sub.add_parser("off", help="disable W1")

    args = p.parse_args()
    dwf = DwfLibrary()

    try:
        with openDwfDevice(dwf) as device:
            if args.cmd in ("awg", "sweep"):
                # Keep W1 running after the script exits, so the level
                # persists while the user reads Monitor & Tune.
                device.paramSet(DwfDeviceParameter.OnClose, 0)
            handler = {"measure": cmd_measure, "awg": cmd_awg,
                       "sweep": cmd_sweep, "off": cmd_off}[args.cmd]
            return handler(device, args)
    except Exception as e:
        msg = str(e)
        if "device is being used" in msg.lower() or "DwfErrorBusy" in msg:
            print("FAIL: AD3 is in use — close the WaveForms GUI first.")
            return 2
        raise


if __name__ == "__main__":
    sys.exit(main())

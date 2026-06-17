#!/usr/bin/env python3
"""Boost bring-up: drive W1 as the gate PWM (into the opto on J3) and capture
both scope channels in ONE device session, so the wavegen and scope don't
fight over the AD3.

Channel map (set your probes to 10x):
  CH1 (1+) -> switch node   (M1 drain / D1 anode / L1)
  CH2 (2+) -> output        (J2, ~10 V)
  both 1-/2- -> power GND
  W1 (yellow) -> J3 pin1 (PWM),  AD3 GND -> J3 pin2 (GND_MCU)

Examples
  python boost_test.py --freq 10000 --duty 20      # start gentle
  python boost_test.py --duty 35                    # nudge duty up, re-measure
  python boost_test.py --off                        # stop PWM (gate -> low)

W1 keeps running after the script exits (OnClose=0) so the converter stays
driven while you read the numbers. Use --off to stop it.
"""
import argparse
import sys
import time

from pydwf import (DwfLibrary, DwfAnalogOutNode, DwfAnalogOutFunction,
                   DwfState, DwfDeviceParameter)
from pydwf.utilities import openDwfDevice

W1 = 0
CARRIER = DwfAnalogOutNode.Carrier


def set_pwm(device, freq, duty, amp=2.5, offset=2.5):
    """W1 square wave 0..5 V (offset 2.5, amp 2.5), duty = % high."""
    out = device.analogOut
    out.reset(W1)
    out.nodeEnableSet(W1, CARRIER, True)
    out.nodeFunctionSet(W1, CARRIER, DwfAnalogOutFunction.Square)
    out.nodeFrequencySet(W1, CARRIER, freq)
    out.nodeAmplitudeSet(W1, CARRIER, amp)
    out.nodeOffsetSet(W1, CARRIER, offset)
    out.nodeSymmetrySet(W1, CARRIER, duty)   # % of period high
    out.configure(W1, True)


def capture_both(device, sample_hz, n, ch_range=50.0, att=10.0):
    ain = device.analogIn
    for ch in (0, 1):
        ain.channelEnableSet(ch, True)
        ain.channelAttenuationSet(ch, att)
        ain.channelRangeSet(ch, ch_range)
    ain.frequencySet(sample_hz)
    ain.bufferSizeSet(n)
    ain.configure(False, True)
    while ain.status(True) != DwfState.Done:
        time.sleep(0.01)
    return ain.statusData(0, n), ain.statusData(1, n)


def edge_stats(s, sample_hz):
    vmin, vmax = min(s), max(s)
    if vmax - vmin < 0.5:
        return None
    mid = 0.5 * (vmin + vmax)
    hyst = 0.05 * (vmax - vmin)
    state = s[0] > mid
    rising = []
    for i, v in enumerate(s):
        if state and v < mid - hyst:
            state = False
        elif not state and v > mid + hyst:
            state = True
            rising.append(i)
    if len(rising) < 2:
        return None
    periods = [b - a for a, b in zip(rising, rising[1:])]
    freq = sample_hz / (sum(periods) / len(periods))
    seg = s[rising[0]:rising[-1]]
    duty = 100.0 * sum(1 for v in seg if v > mid) / len(seg)
    return freq, duty, vmin, vmax


def mean(s):
    return sum(s) / len(s)


def cmd_run(device, args):
    if not args.measure_only:
        set_pwm(device, args.freq, args.duty)
        print(f"W1 PWM: {args.freq/1000:.1f} kHz, duty {args.duty:.0f} % "
              f"(0..5 V into J3)")
        time.sleep(0.2)  # let the output settle
    n = 16384
    sw, out = capture_both(device, 10e6, n)
    st = edge_stats(sw, 10e6)
    if st:
        f, d, vmn, vmx = st
        print(f"CH1 switch node: f = {f/1000:.1f} kHz, duty = {d:.0f} %, "
              f"Vmin = {vmn:.2f} V, Vmax = {vmx:.2f} V")
    else:
        print("CH1 switch node: no clean switching detected "
              "(no PWM? gate not moving? probe/GND?)")
    omin, omax, omean = min(out), max(out), mean(out)
    print(f"CH2 output:      Vavg = {omean:.2f} V, ripple = "
          f"{(omax-omin)*1000:.0f} mVpp (Vmin {omin:.2f}, Vmax {omax:.2f})")
    return 0


def cmd_off(device, args):
    device.analogOut.reset(-1)
    print("W1 off (gate pulled low by R2 -> M1 off)")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--freq", type=float, default=10000.0,
                   help="PWM frequency Hz (default 10k; keep modest, 4N25 is slow)")
    p.add_argument("--duty", type=float, default=20.0,
                   help="PWM duty %% high (default 20)")
    p.add_argument("--measure-only", action="store_true",
                   help="don't touch W1, just capture both channels")
    p.add_argument("--off", action="store_true", help="stop W1 and exit")
    args = p.parse_args()

    dwf = DwfLibrary()
    try:
        with openDwfDevice(dwf) as device:
            device.paramSet(DwfDeviceParameter.OnClose, 0)  # keep W1 alive
            return cmd_off(device, args) if args.off else cmd_run(device, args)
    except Exception as e:
        if "device is being used" in str(e).lower() or "DwfErrorBusy" in str(e):
            print("FAIL: AD3 in use — close the WaveForms GUI first.")
            return 2
        raise


if __name__ == "__main__":
    sys.exit(main())

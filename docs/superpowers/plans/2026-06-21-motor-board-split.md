# Motor board split — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Derive two new, ERC-clean KiCad projects — `motor_power` and `motor_feedback` — from Ask-ham's `CompleteMotorCircuit`, with a real isolation barrier on the feedback board, without modifying the original.

**Architecture:** Copy the verified `CompleteMotorCircuit.kicad_sch` into two new project folders. Trim each copy to its half by removing the other half's symbol instances and their orphaned wiring (sexpdata, structural — reformatting the *derived* files is fine, they're fresh). Add inter-board connectors and the feedback-side ground/supply re-reference. The "test" after every change is KiCad-10 ERC (0 errors) plus a netlist membership check.

**Tech stack:** KiCad 10 (`C:\Program Files\KiCad\10.0\bin\kicad-cli.exe`), Python 3.13 + `sexpdata`, the skill's `pcb_netlist_json.py`. The source file is KiCad format `version 20260306`; only the 10.0 CLI can read it.

**Reference data (from the verified netlist):**
- Feedback components (keep on `motor_feedback`): `U9, U10, U11, R14, R15, R16, R17, R18`
- V1 sense node = net `Net-(C12-Pin_2)` (also on J6/L1/C12)
- Isolation re-reference (feedback board, move to MCU rails): pins `U10.6`, `U11.4`, `U11.7`, `R18.2`
- Power-side rails: `GND`, `+5v`. New MCU-side rails: `GND_MCU`, `+5V_MCU`.

**Preconditions:**
- KiCad must be **closed** on `CompleteMotorCircuit` during Task 1+ (copies are read-only of it, but close to avoid a mid-run re-save changing the source). Verify: no `~CompleteMotorCircuit.kicad_*.lck` files.
- `CompleteMotorCircuit` is ERC 0 / fully footprinted (already true).

---

## Helper: net-membership check (used as the "test" throughout)

Save once as `hardware/kicad/tools/netcheck.py` (Task 0) and reuse:

```python
import json, sys, collections
d = json.load(open(sys.argv[1], encoding="utf8"))
nets = collections.defaultdict(list)
refs = set()
nofp = []
for c in d["components"]:
    refs.add(c["ref"])
    if not c.get("footprint"): nofp.append(c["ref"])
    for p, n in c["pads"].items():
        nets[n].append(f'{c["ref"]}.{p}')
print("components:", len(refs))
print("missing footprint:", nofp or "none")
for q in sys.argv[2:]:               # extra queries: "ref.pad" -> prints its net
    hit = [n for n, m in nets.items() if q in m]
    print(f"  {q} -> {hit[0] if hit else '(NOT CONNECTED)'}")
```

Netlist+check one-liner (PowerShell), used after every change:
```
$kc="C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
& $kc sch export netlist --format kicadsexpr -o "$env:TEMP\b.net" <board>.kicad_sch
py -3.13 <skill>\scripts\pcb_netlist_json.py "$env:TEMP\b.net" "$env:TEMP\b.json"
py -3.13 hardware\kicad\tools\netcheck.py "$env:TEMP\b.json" U11.4 U9.4
& $kc sch erc --severity-error -o "$env:TEMP\b.erc" <board>.kicad_sch   # expect: Found 0 violations
```

---

## Task 0: Scaffold the two new projects

**Files:**
- Create: `hardware/kicad/boards/motor_power/motor_power.kicad_{sch,pro}`
- Create: `hardware/kicad/boards/motor_feedback/motor_feedback.kicad_{sch,pro}`
- Create: `hardware/kicad/tools/netcheck.py`

- [ ] **Step 1: Confirm KiCad closed on the source**

Run: `ls hardware/kicad/boards/CompleteMotorCircuit/CompleteMotorCircuit/~*.lck`
Expected: no such file (if present, stop and ask the user to close KiCad).

- [ ] **Step 2: Copy the source schematic + project into both new folders**

```bash
SRC="hardware/kicad/boards/CompleteMotorCircuit/CompleteMotorCircuit"
for b in motor_power motor_feedback; do
  mkdir -p "hardware/kicad/boards/$b"
  cp "$SRC/CompleteMotorCircuit.kicad_sch" "hardware/kicad/boards/$b/$b.kicad_sch"
  cp "$SRC/CompleteMotorCircuit.kicad_pro" "hardware/kicad/boards/$b/$b.kicad_pro"
done
```

- [ ] **Step 3: Write `netcheck.py`** (content above).

- [ ] **Step 4: Verify both copies are identical to source and ERC-clean**

Run the netlist+check one-liner on each. Expected: `components: 65`, `missing footprint: none`, `Found 0 violations` for both. (They are exact copies, so they must match the source.)

- [ ] **Step 5: Commit**

```bash
git add hardware/kicad/boards/motor_power hardware/kicad/boards/motor_feedback hardware/kicad/tools/netcheck.py
git commit -m "Scaffold motor_power and motor_feedback as copies of the motor circuit"
```

---

## Task 1: Trim `motor_power` (remove the 8 feedback parts) + add the V1 sense connector

**Files:**
- Modify: `hardware/kicad/boards/motor_power/motor_power.kicad_sch`

- [ ] **Step 1: Remove the 8 feedback symbol instances and their orphaned wiring**

Run this script (`py -3.13 - <<'PY'` … `PY`) against `motor_power.kicad_sch`:

```python
import sexpdata; from sexpdata import Symbol
f="hardware/kicad/boards/motor_power/motor_power.kicad_sch"
d=sexpdata.load(open(f,encoding="utf8"))
car=lambda x:x[0] if isinstance(x,list) and x else None
REMOVE={"U9","U10","U11","R14","R15","R16","R17","R18"}
# 1) collect pin coordinates of the symbols we remove
def at(e):
    a=[p for p in e if car(p)==Symbol("at")][0]; return (round(float(a[1]),2),round(float(a[2]),2))
# remove the symbol instances; collect their footprints' pin anchor points is hard,
# so instead: after removal, drop wires/labels/junctions whose endpoint no longer
# touches ANY remaining symbol pin. Simpler proxy used here: KiCad re-ERC will report
# dangling endpoints as WARNINGS only (acceptance bar is 0 ERRORS), and the user tidies
# placement in the GUI. We remove instances + any label whose text is a feedback-only net.
out=[]
for e in d:
    if isinstance(e,list) and car(e)==Symbol("symbol"):
        ref=None
        for p in e:
            if isinstance(p,list) and car(p)==Symbol("property") and p[1]=="Reference": ref=p[2]
        if ref in REMOVE: continue
    out.append(e)
# drop labels naming feedback-only local nets
FEEDBACK_NETS={"Net-(U9-+)","Net-(U9--)","Net-(U11-+)","Net-(R17-Pad1)","Net-(R17-Pad2)"}
out=[e for e in out if not (isinstance(e,list) and car(e) in (Symbol("label"),Symbol("global_label"))
       and len(e)>1 and e[1] in FEEDBACK_NETS)]
sexpdata.dump(out, open(f,"w",encoding="utf8"))
print("removed", REMOVE)
PY
```

- [ ] **Step 2: Verify the 8 are gone, 57 remain, footprints intact**

Run netlist+check. Expected: `components: 57`, `missing footprint: none`. ERC: 0 errors (dangling-endpoint *warnings* are acceptable and will be tidied in GUI).

- [ ] **Step 3: Add a 3-pin V1-sense output connector**

The V1 node (`Net-(C12-Pin_2)`) and `GND`, `+5v` already exist on this board. Add a `Connector:Conn_01x03_Socket` instance (lib symbol already present in the file) with footprint `TerminalBlock:TerminalBlock_bornier-3_P5.08mm`, and three net **labels** on its pins: `Net-(C12-Pin_2)` (V1), `GND`, `+5v`. Place it at a free coordinate (e.g. `(at 60 60 0)`). Script appends the symbol + three short wires + three labels before `(sheet_instances`. (Reference designator: next free `J*`, e.g. `J7`.)

- [ ] **Step 4: Verify the connector lands on the right nets**

Run netlist+check with queries `J7.1 J7.2 J7.3`. Expected: one pin on `Net-(C12-Pin_2)`, one on `GND`, one on `+5v`. ERC: 0 errors.

- [ ] **Step 5: Commit**

```bash
git add hardware/kicad/boards/motor_power/motor_power.kicad_sch
git commit -m "motor_power: drop feedback amp, add V1/GND/+5V sense connector"
```

---

## Task 2: Trim `motor_feedback` (keep the 8 parts) + connectors + real isolation

**Files:**
- Modify: `hardware/kicad/boards/motor_feedback/motor_feedback.kicad_sch`

- [ ] **Step 1: Remove the 57 power components, keep the 8 feedback parts**

Same removal script as Task 1 Step 1, but invert the set: `KEEP={"U9","U10","U11","R14","R15","R16","R17","R18"}` and remove every symbol whose Reference is not in KEEP (and is a real component, i.e. has a Reference not starting with `#`). Keep power symbols (`#PWR*`) for GND/+5v that the kept parts use. Drop labels for nets that no longer have ≥2 members.

- [ ] **Step 2: Verify only the 8 remain**

Run netlist+check. Expected: `components: 8`, `missing footprint: none`. ERC may now show power-not-driven errors (rails lost their source) — expected, fixed in Step 4–5.

- [ ] **Step 3: Re-reference the MCU side onto isolated rails**

Change the net on these pins from the shared rails to new MCU-side rails, by editing the labels/wires at those pins: `U11.4` GND→`GND_MCU`, `U11.7` +5v→`+5V_MCU`, `U10.6` +5v→`+5V_MCU`, `R18.2` GND→`GND_MCU`. (U9 + IL300 input side `U10.1`/`U10.3`/`U9.4`/`U9.7` stay on power `GND`/`+5v`.)

- [ ] **Step 4: Add P1 (power-side) and P2 (MCU-side) connectors**

Two `Connector:Conn_01x03_Socket` (footprint `TerminalBlock:TerminalBlock_bornier-3_P5.08mm`):
- **P1** pins labelled: `Net-(C12-Pin_2)` (V1 into R14.1), `GND`, `+5v`.
- **P2** pins labelled: `MCU`, `GND_MCU`, `+5V_MCU`.
Also add power-port symbols (`power:GND` for `GND` and a `+5v` label source) so ERC sees the power-side rails driven via P1, and `GND_MCU`/`+5V_MCU` driven via P2. (Add `PWR_FLAG` on V1, GND, +5v, GND_MCU, +5V_MCU at the connector pins so ERC's power-driven check passes.)

- [ ] **Step 5: Verify isolation + connectivity in the netlist**

Run netlist+check with queries `U9.4 U11.4 U11.7 U10.6 R18.2`. Expected:
- `U9.4 -> GND`, and `U11.4 -> GND_MCU` (two distinct ground nets — the barrier).
- `U11.7 -> +5V_MCU`, `U10.6 -> +5V_MCU`, `R18.2 -> GND_MCU`.
- ERC: `Found 0 violations`.

- [ ] **Step 6: Commit**

```bash
git add hardware/kicad/boards/motor_feedback/motor_feedback.kicad_sch
git commit -m "motor_feedback: isolated linear amp with split power/MCU grounds + connectors"
```

---

## Task 3: Final cross-board verification + handoff note

**Files:**
- Modify: `PCB_RESULTS.md` (add the two new boards' status)

- [ ] **Step 1: Confirm the original is untouched**

Run: `git status --short hardware/kicad/boards/CompleteMotorCircuit/`
Expected: no changes listed for it from this work (only the pre-existing in-progress edits, if any).

- [ ] **Step 2: Both boards ERC 0 + fully footprinted**

Run the netlist+check + ERC one-liner on both boards. Expected: `Found 0 violations` and `missing footprint: none` for each; `motor_power` 58 components (57 + J7), `motor_feedback` 11 (8 + P1 + P2... count connectors/PWR as they land).

- [ ] **Step 3: Record status in PCB_RESULTS.md**

Add a short section: the two boards, their component counts, the V1/GND/+5V and MCU/GND_MCU/+5V_MCU interface, and that the IL300 now isolates (two ground nets). Note placement is auto/rough pending GUI tidy + routing via the pipeline.

- [ ] **Step 4: Commit**

```bash
git add PCB_RESULTS.md
git commit -m "Record motor_power / motor_feedback split status"
```

---

## Notes / known soft spots

- **Dangling wire endpoints** after symbol removal are ERC *warnings*, not errors; the acceptance bar is 0 errors. Tidy placement/stray wires in the KiCad GUI before routing.
- **sexpdata re-dump reformats** the derived files — acceptable because they are fresh derivatives (not Ask-ham's source). KiCad normalizes on next open.
- If the label-based net assignment for a connector pin doesn't take (KiCad needs the label exactly on the pin endpoint), fall back to drawing that one wire/label in the GUI — same lesson as the CONT/C4 fix.
- Routing each board to laser DXF/Gerber is a **separate** step via the `kicad-laser-pcb` pipeline once placement is tidied.

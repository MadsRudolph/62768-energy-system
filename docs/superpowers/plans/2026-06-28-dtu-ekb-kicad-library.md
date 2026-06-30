# DTU-EKB KiCad Library — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Populate the empty `DTU-EKB/KiCad-components` library with ~18 curated 62768 parts and register it as a live git checkout in KiCad 10 so it works across all projects on this PC.

**Architecture:** A reproducible `kiutils` build script clones base symbols from KiCad 10's stock symbol libraries and derives shop-named parts from them, driven by a curated CSV. The library lives as a git checkout outside the umbrella repo; KiCad 10's global library tables point at it so edits are live and PR-ready.

**Tech Stack:** Python 3.13, `kiutils` (already installed), KiCad 10.0, git.

## Global Constraints

- **No AI mention in commits/code/docs** — commit messages read like a developer wrote them (umbrella + team CLAUDE.md). Applies to the DTU-EKB repo too.
- **Commit/push only when the user asks** (umbrella CLAUDE.md) — overrides the skill's auto-commit steps. Tasks below stage and prepare commits; the user gives the go for the actual `git commit`/`push`/PR.
- **Target KiCad version: 10.0** — author symbols in KiCad 10 format; register in `%APPDATA%\kicad\10.0\` tables only.
- **Clone path:** `C:\Users\Mads2\KiCad\DTU-EKB-components` — deliberately outside `C:\Users\Mads2\DTU` (umbrella git repo) and outside OneDrive-redirected Documents.
- **Stock symbol source:** `C:\Program Files\KiCad\10.0\share\kicad\symbols\`.
- **All footprints are stock KiCad libs** (`Diode_THT`, `Package_DIP`, `Package_TO_SOT_THT`) — no custom footprints in v1.
- **Edit KiCad config files only while KiCad is closed** (it rewrites lib tables / `kicad_common.json` on exit). Back up before editing.

---

### Task 1: Clone repo + scaffold tooling + curated CSV

**Files:**
- Clone into: `C:\Users\Mads2\KiCad\DTU-EKB-components`
- Create: `C:\Users\Mads2\KiCad\DTU-EKB-components\Components\parts\dtu-shop-parts.csv`
- Create (empty dir): `C:\Users\Mads2\KiCad\DTU-EKB-components\tools\`

**Interfaces:**
- Produces: the curated CSV with columns `part,source_lib,source_symbol,footprint,datasheet,shop_location,description`. `part == source_symbol` ⇒ copy that stock symbol as-is and set fields ("self"); otherwise create a derived symbol `part extends source_symbol` ("derived"). Consumed by Task 2's build script.

- [ ] **Step 1: Clone the repo to the permanent path**

```bash
mkdir -p /c/Users/Mads2/KiCad
git clone https://github.com/DTU-EKB/KiCad-components.git /c/Users/Mads2/KiCad/DTU-EKB-components
cd /c/Users/Mads2/KiCad/DTU-EKB-components && git checkout -b feat/curated-62768-parts
```

Expected: clone succeeds, new branch `feat/curated-62768-parts` checked out.

- [ ] **Step 2: Create the curated parts CSV**

Create `Components/parts/dtu-shop-parts.csv` with exactly this content:

```csv
part,source_lib,source_symbol,footprint,datasheet,shop_location,description
1N4148,Device,D,Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal,https://www.vishay.com/docs/81857/1n4148.pdf,CSM,Signal diode 100V 200mA DO-35
1N4006,Device,D,Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal,https://www.vishay.com/docs/88503/1n4001.pdf,CSM,Rectifier diode 800V 1A DO-41
1N5817,Device,D_Schottky,Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal,https://www.vishay.com/docs/88525/1n5817.pdf,CSM,Schottky 20V 1A DO-41
1N5822,Device,D_Schottky,Diode_THT:D_DO-201AD_P15.24mm_Horizontal,https://www.onsemi.com/pdf/datasheet/1n5820-d.pdf,order,Schottky 40V 3A DO-201AD (order - not in shop)
BZX55C5V1,Device,D_Zener,Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal,https://www.vishay.com/docs/85604/bzx55.pdf,CSM,Zener 5.1V 0.5W DO-35
BZX55C3V0,Device,D_Zener,Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal,https://www.vishay.com/docs/85604/bzx55.pdf,CSM,Zener 3.0V 0.5W DO-35
IRF530,Transistor_FET,Q_NMOS_GDS,Package_TO_SOT_THT:TO-220-3_Vertical,https://www.vishay.com/docs/91019/irf530.pdf,CSM,N-MOSFET 100V 14A TO-220 (G-D-S)
IRF540,Transistor_FET,IRF540N,Package_TO_SOT_THT:TO-220-3_Vertical,https://www.vishay.com/docs/91021/irf540.pdf,CSM,N-MOSFET 100V 28A TO-220 (G-D-S)
TIP41A,Transistor_BJT,TIP41A,Package_TO_SOT_THT:TO-220-3_Vertical,https://www.onsemi.com/pdf/datasheet/tip41a-d.pdf,CSM,NPN BJT 60V 6A TO-220
LM358,Amplifier_Operational,LM358,Package_DIP:DIP-8_W7.62mm_LongPads,https://www.ti.com/lit/ds/symlink/lm358.pdf,CSM,Dual op-amp DIP-8
MCP601,Amplifier_Operational,TL071,Package_DIP:DIP-8_W7.62mm_LongPads,https://ww1.microchip.com/downloads/en/DeviceDoc/21314g.pdf,kit,Single op-amp 2.8MHz DIP-8 (kit part)
NE555,Timer,NE555P,Package_DIP:DIP-8_W7.62mm_LongPads,https://www.ti.com/lit/ds/symlink/ne555.pdf,CSM,Timer DIP-8
LM7805,Regulator_Linear,LM7805_TO220,Package_TO_SOT_THT:TO-220-3_Vertical,https://www.onsemi.com/pdf/datasheet/mc7800-d.pdf,CSM,5V linear regulator TO-220 (IN-GND-OUT)
4N25,Isolator,4N25,Package_DIP:DIP-6_W7.62mm_LongPads,https://www.vishay.com/docs/83725/4n25.pdf,CSM,Optocoupler phototransistor DIP-6
CNY17,Isolator,CNY17-1,Package_DIP:DIP-6_W7.62mm_LongPads,https://www.vishay.com/docs/83606/cny17.pdf,CSM,Optocoupler phototransistor DIP-6
IR2110,Driver_FET,IR2110,Package_DIP:DIP-14_W7.62mm_LongPads,https://www.infineon.com/dgdl/Infineon-IR2110-DataSheet-v01_00-EN.pdf,kit,High/low-side gate driver DIP-14 (kit part)
ILD74,Isolator,ILD74,Package_DIP:DIP-8_W7.62mm_LongPads,https://www.vishay.com/docs/83663/ild74.pdf,kit,Dual optocoupler DIP-8 (kit part)
IL300,Isolator_Analog,IL300,Package_DIP:DIP-8_W7.62mm_LongPads,https://www.vishay.com/docs/83622/il300.pdf,kit,Linear optocoupler DIP-8 (kit part)
```

- [ ] **Step 3: Verify the CSV parses and base symbols exist in stock**

Run:
```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components
python -c "
import csv
from pathlib import Path
stock=Path(r'C:/Program Files/KiCad/10.0/share/kicad/symbols')
rows=list(csv.DictReader(open('Components/parts/dtu-shop-parts.csv',encoding='utf-8')))
print('rows:',len(rows))
import re
for r in rows:
    lib=stock/f\"{r['source_lib']}.kicad_sym\"
    txt=lib.read_text(encoding='utf-8')
    assert f'(symbol \"{r[\"source_symbol\"]}\"' in txt, f'MISSING {r[\"source_lib\"]}:{r[\"source_symbol\"]}'
print('all base symbols present in stock libs OK')
"
```
Expected: `rows: 18` then `all base symbols present in stock libs OK`.

- [ ] **Step 4: Stage (do not commit yet)**

```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components && git add Components/parts/dtu-shop-parts.csv
```

---

### Task 2: Build script + validation test

**Files:**
- Create: `tools/build_symbols.py`
- Create: `tools/test_build_symbols.py`
- Output (generated, overwrites stub): `Components/symbols/dtu-ballerup-componentshop.kicad_sym`

**Interfaces:**
- Consumes: `Components/parts/dtu-shop-parts.csv` (Task 1).
- Produces: `build_library()` writing the target `.kicad_sym`. Test asserts every `part` is present, each has a `Footprint` and `Shop_Location` property, and the file round-trips through `kiutils`.

- [ ] **Step 1: Write the failing test**

Create `tools/test_build_symbols.py`:

```python
import csv, subprocess, sys
from pathlib import Path
from kiutils.symbol import SymbolLib

REPO = Path(__file__).resolve().parents[1]
CSV = REPO / "Components" / "parts" / "dtu-shop-parts.csv"
OUT = REPO / "Components" / "symbols" / "dtu-ballerup-componentshop.kicad_sym"

def _names(sym):
    # symbol name irrespective of kiutils version (libId or entryName)
    return getattr(sym, "entryName", None) or getattr(sym, "libId", None)

def _prop(sym, key):
    for p in sym.properties:
        if p.key == key:
            return p.value
    return None

def test_build_produces_all_parts():
    subprocess.run([sys.executable, str(REPO / "tools" / "build_symbols.py")], check=True)
    lib = SymbolLib.from_file(str(OUT))
    present = {_names(s) for s in lib.symbols}
    want = {r["part"] for r in csv.DictReader(open(CSV, encoding="utf-8"))}
    missing = want - present
    assert not missing, f"missing parts: {missing}"

def test_each_part_has_footprint_and_shop_location():
    lib = SymbolLib.from_file(str(OUT))
    by_name = {_names(s): s for s in lib.symbols}
    for r in csv.DictReader(open(CSV, encoding="utf-8")):
        s = by_name[r["part"]]
        assert _prop(s, "Footprint") == r["footprint"], r["part"]
        assert _prop(s, "Shop_Location") == r["shop_location"], r["part"]

def test_roundtrip_parses():
    # re-parse must not raise
    SymbolLib.from_file(str(OUT))
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /c/Users/Mads2/KiCad/DTU-EKB-components && python -m pytest tools/test_build_symbols.py -x -q`
Expected: FAIL — `build_symbols.py` does not exist yet (ModuleNotFoundError / FileNotFoundError on subprocess).

- [ ] **Step 3: Write the build script**

Create `tools/build_symbols.py`:

```python
#!/usr/bin/env python3
"""Generate dtu-ballerup-componentshop.kicad_sym from the curated CSV.

For each CSV row:
  - part == source_symbol  -> copy that stock symbol verbatim, then override fields ("self")
  - part != source_symbol  -> copy the base symbol once, then add a derived
                              symbol `part (extends source_symbol)` with overridden fields
Idempotent: fully regenerates the output file each run.
"""
import csv
import copy
from pathlib import Path
from kiutils.symbol import SymbolLib, Symbol
from kiutils.items.common import Property

STOCK = Path(r"C:/Program Files/KiCad/10.0/share/kicad/symbols")
REPO = Path(__file__).resolve().parents[1]
CSV = REPO / "Components" / "parts" / "dtu-shop-parts.csv"
OUT = REPO / "Components" / "symbols" / "dtu-ballerup-componentshop.kicad_sym"

_stock_cache = {}

def stock_lib(name):
    if name not in _stock_cache:
        _stock_cache[name] = SymbolLib.from_file(str(STOCK / f"{name}.kicad_sym"))
    return _stock_cache[name]

def sym_name(sym):
    return getattr(sym, "entryName", None) or getattr(sym, "libId", None)

def find(lib, name):
    for s in lib.symbols:
        if sym_name(s) == name:
            return s
    raise KeyError(f"{name} not found")

def get_prop(sym, key):
    for p in sym.properties:
        if p.key == key:
            return p
    return None

def set_prop(sym, key, value):
    p = get_prop(sym, key)
    if p is None:
        sym.properties.append(Property(key=key, value=value))
    else:
        p.value = value

def apply_fields(sym, row):
    set_prop(sym, "Value", row["part"])
    set_prop(sym, "Footprint", row["footprint"])
    set_prop(sym, "Datasheet", row["datasheet"])
    set_prop(sym, "Description", row["description"])
    set_prop(sym, "Shop_Location", row["shop_location"])

def rename(sym, new):
    """Rename a concrete symbol incl. its unit child symbols (which embed the name)."""
    old = sym_name(sym)
    if hasattr(sym, "entryName"):
        sym.entryName = new
    if hasattr(sym, "libId"):
        sym.libId = new
    for u in getattr(sym, "units", []) or []:
        un = sym_name(u)
        if un and un.startswith(old):
            newun = new + un[len(old):]
            if hasattr(u, "entryName"):
                u.entryName = newun
            if hasattr(u, "libId"):
                u.libId = newun

def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))
    out = SymbolLib(version="20251024", generator="dtu_build_symbols")
    copied_bases = {}  # source_symbol name -> Symbol object in `out`

    # Pass 1: copy each needed base/concrete symbol exactly once.
    for r in rows:
        key = (r["source_lib"], r["source_symbol"])
        if key in copied_bases:
            continue
        src = find(stock_lib(r["source_lib"]), r["source_symbol"])
        clone = copy.deepcopy(src)
        out.symbols.append(clone)
        copied_bases[key] = clone

    # Pass 2: realize each catalog part.
    for r in rows:
        base = copied_bases[(r["source_lib"], r["source_symbol"])]
        if r["part"] == r["source_symbol"]:
            apply_fields(base, r)               # "self": the base IS the catalog part
        else:
            derived = Symbol.create_new(id=r["part"], reference=get_prop(base, "Reference").value if get_prop(base, "Reference") else "U", value=r["part"])
            derived.units = []                  # derived symbols inherit graphics
            derived.extends = r["source_symbol"]
            apply_fields(derived, r)
            out.symbols.append(derived)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_file(str(OUT))
    print(f"wrote {OUT} with {len(out.symbols)} symbols")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the build, then the test**

Run: `cd /c/Users/Mads2/KiCad/DTU-EKB-components && python tools/build_symbols.py && python -m pytest tools/test_build_symbols.py -x -q`
Expected: build prints `wrote ... with 27 symbols` (18 parts + 9 base-only bases), tests PASS.

> If `kiutils` attribute/API names differ (e.g. `entryName` vs `libId`, `Symbol.create_new` signature, `extends` setter), adjust the helpers — the helpers are deliberately defensive (`getattr`) for exactly this. Re-run until green.

- [ ] **Step 5: Stage (no commit)**

```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components && git add tools/build_symbols.py tools/test_build_symbols.py Components/symbols/dtu-ballerup-componentshop.kicad_sym
```

---

### Task 3: Validate footprints resolve + KiCad can open the library

**Files:**
- Read-only checks against `Components/symbols/dtu-ballerup-componentshop.kicad_sym` and stock footprint libs.

**Interfaces:**
- Consumes: generated lib (Task 2). Produces: confidence that every `Footprint` reference resolves to an existing `.kicad_mod` and that KiCad parses the lib.

- [ ] **Step 1: Verify every footprint reference exists on disk**

Run:
```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components
python -c "
import csv
from pathlib import Path
fp=Path(r'C:/Program Files/KiCad/10.0/share/kicad/footprints')
for r in csv.DictReader(open('Components/parts/dtu-shop-parts.csv',encoding='utf-8')):
    lib,name=r['footprint'].split(':')
    f=fp/f'{lib}.pretty'/f'{name}.kicad_mod'
    assert f.exists(), f'MISSING FOOTPRINT {r[\"footprint\"]} for {r[\"part\"]}'
print('all footprints resolve OK')
"
```
Expected: `all footprints resolve OK`. If any footprint name is wrong, correct it in the CSV and re-run Task 2 build before continuing.

- [ ] **Step 2: Verify KiCad's CLI can read the library (real KiCad parse)**

Run:
```bash
"/c/Program Files/KiCad/10.0/bin/kicad-cli.exe" sym upgrade --force "C:/Users/Mads2/KiCad/DTU-EKB-components/Components/symbols/dtu-ballerup-componentshop.kicad_sym" 2>&1 | tail -5
```
Expected: completes without a parse/error message (it normalizes the file in place to canonical KiCad 10 format — this is desirable). If it errors, the generated s-expr is malformed; fix the build script.

- [ ] **Step 3: Re-run the build test to confirm upgrade didn't break expectations**

Run: `cd /c/Users/Mads2/KiCad/DTU-EKB-components && python -m pytest tools/test_build_symbols.py -x -q`
Expected: PASS (kicad-cli output is canonical and still satisfies the assertions).

- [ ] **Step 4: Stage the normalized file (no commit)**

```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components && git add Components/symbols/dtu-ballerup-componentshop.kicad_sym
```

---

### Task 4: Add full shop inventory CSV + convention doc + README link

**Files:**
- Create: `Components/parts/dtu_component_shop.csv` (copy of the 1464-row inventory)
- Create: `Components/CONVENTION.md`
- Modify: `README.md` (add a link under the shop-components section)

**Interfaces:**
- Produces: reference inventory + passives convention. No code dependency; documentation deliverable.

- [ ] **Step 1: Copy the shop inventory into the repo**

```bash
cp "/c/Users/Mads2/Downloads/Misc/dtu_component_shop.csv" "/c/Users/Mads2/KiCad/DTU-EKB-components/Components/parts/dtu_component_shop.csv"
wc -l "/c/Users/Mads2/KiCad/DTU-EKB-components/Components/parts/dtu_component_shop.csv"
```
Expected: `1465` lines (header + 1464 parts).

- [ ] **Step 2: Write the passives convention doc**

Create `Components/CONVENTION.md`:

```markdown
# Component conventions

The curated `dtu-ballerup-componentshop` symbol library contains the **named parts**
(ICs, transistors, optocouplers, specific diodes) the DTU Ballerup shop stocks, each with a
verified footprint, datasheet, and `Shop_Location` field.

**Passives are not individual symbols.** The shop stocks the full E96 resistor decade plus
common capacitor/inductor values (see `parts/dtu_component_shop.csv` for the complete list).
Use the standard KiCad generic symbols and set the value:

| Type | Symbol | Default THT footprint we stock |
|---|---|---|
| Resistor (1/4 W) | `Device:R` | `Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal` |
| Ceramic cap | `Device:C` | `Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm` |
| Electrolytic cap | `Device:C_Polarized` | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` (larger for >100µF) |
| Inductor | `Device:L` | per part — most power inductors are hand-wound toroids |

`parts/dtu_component_shop.csv` is the authoritative stock inventory
(Category, Subcategory, Part_Number, Value, Description).
```

- [ ] **Step 3: Add a README link to the inventory**

In `README.md`, immediately under the heading `## Table of components in the component shop`, add this line (keep the existing table below it):

```markdown
> Full machine-readable inventory: [`Components/parts/dtu_component_shop.csv`](Components/parts/dtu_component_shop.csv) (1464 parts). See [`Components/CONVENTION.md`](Components/CONVENTION.md) for the passives convention.
```

- [ ] **Step 4: Stage (no commit)**

```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components && git add Components/parts/dtu_component_shop.csv Components/CONVENTION.md README.md
```

---

### Task 5: Register the live checkout globally in KiCad 10

**Files:**
- Modify: `%APPDATA%\kicad\10.0\kicad_common.json` (add `DTU_EKB_DIR` env var)
- Modify: `%APPDATA%\kicad\10.0\sym-lib-table` (remove dangling `PCM_*` dtu/ekb entries; add live entries)
- Modify: `%APPDATA%\kicad\10.0\fp-lib-table` (add the two `.pretty` dirs)

**Interfaces:**
- Consumes: the cloned repo path. Produces: KiCad 10 lists `dtu-ballerup-componentshop` (with the 18 parts) in every project's symbol chooser.

> **KiCad must be CLOSED for this entire task** (it rewrites these files on exit, clobbering edits). Confirm no `kicad.exe` is running first.

- [ ] **Step 1: Confirm KiCad is not running, then back up the three config files**

```bash
tasklist 2>/dev/null | grep -i kicad || echo "kicad not running OK"
cd /c/Users/Mads2/AppData/Roaming/kicad/10.0
cp kicad_common.json kicad_common.json.bak
cp sym-lib-table sym-lib-table.bak
cp fp-lib-table fp-lib-table.bak
echo "backed up"
```
Expected: `kicad not running OK` then `backed up`. If KiCad is running, close it before proceeding.

- [ ] **Step 2: Add the `DTU_EKB_DIR` path variable**

Run:
```bash
python -c "
import json
p=r'C:/Users/Mads2/AppData/Roaming/kicad/10.0/kicad_common.json'
d=json.load(open(p,encoding='utf-8'))
env=d.setdefault('environment',{})
if not isinstance(env.get('vars'),dict): env['vars']={}
env['vars']['DTU_EKB_DIR']='C:/Users/Mads2/KiCad/DTU-EKB-components'
json.dump(d,open(p,'w',encoding='utf-8'),indent=2)
print('DTU_EKB_DIR set')
"
```
Expected: `DTU_EKB_DIR set`.

- [ ] **Step 3: Replace the dangling PCM entries with live-checkout entries in `sym-lib-table`**

Run:
```bash
python -c "
import re
p=r'C:/Users/Mads2/AppData/Roaming/kicad/10.0/sym-lib-table'
t=open(p,encoding='utf-8').read()
# drop the empty/dangling PCM dtu+ekb lines
t=re.sub(r'\s*\(lib \(name \"PCM_(dtu-ballerup-componentshop|ekb-component-stock)\".*?\)\)','',t)
add=(
 '\t(lib (name \"dtu-ballerup-componentshop\") (type \"KiCad\") (uri \"\${DTU_EKB_DIR}/Components/symbols/dtu-ballerup-componentshop.kicad_sym\") (options \"\") (descr \"DTU Ballerup component shop (live checkout)\"))\n'
 '\t(lib (name \"ekb-component-stock\") (type \"KiCad\") (uri \"\${DTU_EKB_DIR}/Components/symbols/ekb-component-stock.kicad_sym\") (options \"\") (descr \"EKB component stock (live checkout)\"))\n'
)
t=t.rstrip().rstrip(')')+add+')\n'   # insert before final closing paren
open(p,'w',encoding='utf-8').write(t)
print('sym-lib-table updated')
"
grep -n "dtu-ballerup-componentshop" "/c/Users/Mads2/AppData/Roaming/kicad/10.0/sym-lib-table"
```
Expected: `sym-lib-table updated`, and the grep shows exactly ONE `dtu-ballerup-componentshop` line (the live one, no `PCM_` prefix).

- [ ] **Step 4: Register the footprint `.pretty` dirs in `fp-lib-table`**

Run:
```bash
python -c "
p=r'C:/Users/Mads2/AppData/Roaming/kicad/10.0/fp-lib-table'
t=open(p,encoding='utf-8').read()
add=(
 '\t(lib (name \"dtu-ballerup-componentshop\") (type \"KiCad\") (uri \"\${DTU_EKB_DIR}/Components/footprints/dtu-ballerup-componentshop.pretty\") (options \"\") (descr \"DTU Ballerup footprints (live)\"))\n'
 '\t(lib (name \"ekb-component-stock\") (type \"KiCad\") (uri \"\${DTU_EKB_DIR}/Components/footprints/ekb-component-stock.pretty\") (options \"\") (descr \"EKB footprints (live)\"))\n'
)
t=t.rstrip().rstrip(')')+add+')\n'
open(p,'w',encoding='utf-8').write(t)
print('fp-lib-table updated')
"
```
Expected: `fp-lib-table updated`. (The `.pretty` dirs exist but are empty in v1 — KiCad tolerates empty footprint libs.)

- [ ] **Step 5: Verify in KiCad — library lists the parts**

Open KiCad 10 → any project (or standalone Symbol Editor) → the symbol chooser. Confirm:
- `dtu-ballerup-componentshop` appears once (no `PCM_` duplicate).
- It contains the 18 named parts (e.g. `IRF530`, `LM358`, `IL300`).
- Place `1N4148` and confirm its footprint field reads `Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal`.

Expected: all three confirmed. If KiCad shows a "library not found" error, check `DTU_EKB_DIR` resolved (Preferences → Configure Paths).

> This task edits PC-local config only — nothing here is committed to the repo.

---

### Task 6: Open the PR (on the user's go)

**Files:** none new — finalizes the branch from Tasks 1–4.

**Interfaces:** Consumes the staged changes. Produces a PR on `DTU-EKB/KiCad-components`.

- [ ] **Step 1: Show the user the staged diff and ask for the go-ahead**

```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components && git status && git diff --staged --stat
```
Per the Global Constraints, **do not commit until the user confirms.**

- [ ] **Step 2: Commit (after user confirms) — developer-voiced message, no AI mention**

```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components
git commit -m "Add curated 62768 parts + shop inventory

Populate dtu-ballerup-componentshop with 18 named shop parts (diodes,
MOSFETs, op-amps, optocouplers, gate driver, regulator), each with a
verified THT footprint, datasheet and Shop_Location. Symbols are generated
from Components/parts/dtu-shop-parts.csv via tools/build_symbols.py.
Add the full shop inventory CSV and a passives convention doc."
```

- [ ] **Step 3: Push and open the PR (after user confirms)**

```bash
cd /c/Users/Mads2/KiCad/DTU-EKB-components
git push -u origin feat/curated-62768-parts
gh pr create --repo DTU-EKB/KiCad-components --title "Curated 62768 parts + shop inventory" --body "Populates the empty component-shop symbol library with the 18 named parts used on the 62768 boards (verified footprints + datasheets + shop location), adds the full 1464-row shop inventory CSV, and documents the passives convention. Symbols generated reproducibly from a curated CSV via tools/build_symbols.py."
```
Expected: PR URL printed.

---

## Part C (optional follow-up, NOT in this plan's scope)

Cut a `v0.3` PCM release so classmates receive the parts: fix the broken `v0.1` `download_url` in `packages.json`, rebuild the package zip, compute sha256/size via `releases/pcm-info.sh`, update `packages.json`, and create the GitHub release. Record the "symbols are KiCad-10 format" caveat in the release notes. Spin this into its own plan when wanted.

---

## Self-Review

**Spec coverage:** Part A (live global setup) → Tasks 1, 5. Part B curated set → Tasks 1–3 (all 18 parts from the spec table, footprints from verified BOM). Full shop CSV → Task 4. CONVENTION.md → Task 4. Part C flagged optional → end section. PR/local split → Task 5 note + Task 6. All spec sections covered.

**Placeholder scan:** No TBD/TODO. All code blocks complete (CSV content, build script, test, config edits all literal). Datasheet URLs are concrete (executor may correct any that 404 — noted).

**Type consistency:** `build_symbols.py` helpers (`sym_name`, `get_prop`, `set_prop`, `apply_fields`, `rename`) match their uses; the test uses the same `_names`/`_prop` accessor pattern. CSV columns (`part,source_lib,source_symbol,footprint,datasheet,shop_location,description`) are identical across Tasks 1, 2, 3, 4. Lib nickname `dtu-ballerup-componentshop` consistent across Tasks 5–6.

**Known risk (flagged in-task):** exact `kiutils` API names may vary by version — Task 2 Step 4 explicitly instructs adjusting the defensive helpers until tests pass. The `rename()` helper is defined but only exercised if a future row needs a concrete-symbol rename; all current rows are either "self" (name matches) or "derived" (no rename), so it is currently a safety net.

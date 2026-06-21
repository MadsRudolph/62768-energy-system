"""Add a repo 'TerminalBlock' lib entry to each board's fp-lib-table that lacks one,
mirroring the relative path of its existing 'energy_system' entry (or computing it).
"""
import os, re, sys

ROOT = "hardware/kicad"
LIBDIR = os.path.join(ROOT, "lib")
SKIP_DIRS = {"motor_power", "motor_feedback"}  # already done
targets = []
for dirpath, _, files in os.walk(os.path.join(ROOT, "boards")):
    if "fp-lib-table" in files:
        targets.append(os.path.join(dirpath, "fp-lib-table"))
sysfp = os.path.join(ROOT, "system", "fp-lib-table")
if os.path.exists(sysfp):
    targets.append(sysfp)

patched = []
for fp in targets:
    d = os.path.dirname(fp)
    if os.path.basename(d) in SKIP_DIRS:
        continue
    s = open(fp, "r", encoding="utf8", newline="").read()
    if 'name "TerminalBlock"' in s:
        continue
    # derive ${KIPRJMOD}/.../lib/ prefix from energy_system entry, else compute
    m = re.search(r'uri "(\$\{KIPRJMOD\}/.*?/lib)/energy_system\.pretty"', s)
    if m:
        prefix = m.group(1)
    else:
        rel = os.path.relpath(LIBDIR, d).replace("\\", "/")
        prefix = "${KIPRJMOD}/" + rel
    entry = ('\t(lib (name "TerminalBlock")(type "KiCad")'
             f'(uri "{prefix}/TerminalBlock.pretty")(options "")'
             '(descr "Bornier terminals (repo copy; removed from KiCad 10 stock lib)"))\n')
    # insert before the final ')'
    idx = s.rstrip().rfind(")")
    s = s[:idx] + entry + s[idx:]
    open(fp, "w", encoding="utf8", newline="").write(s)
    patched.append(fp)

print(f"patched {len(patched)} fp-lib-tables:")
for p in patched:
    print("  ", p)

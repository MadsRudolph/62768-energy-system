"""Ensure every board project that uses the repo footprint libs (energy_system,
TerminalBlock) registers them in its OWN fp-lib-table with a portable
`${KIPRJMOD}/.../lib/*.pretty` path (correct relative depth computed per board).
Creates the fp-lib-table if missing, or adds only the missing lib entries.
Idempotent; never touches CompleteMotorCircuit (teammate's project).

    py -3.13 hardware/kicad/tools/fix_fplib.py
"""
import os, re, glob

REPO_LIBS = {
    "energy_system": "Projekt-footprints",
    "TerminalBlock": "Bornier terminals (repo copy; removed from KiCad 10 stock lib)",
}
KICAD_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LIBDIR = os.path.join(KICAD_ROOT, "lib")
BOARDS_DIR = os.path.join(KICAD_ROOT, "boards")


def used_repo_libs(sch):
    s = open(sch, encoding="utf-8").read()
    return {lib for lib, _ in re.findall(r'\(property "Footprint" "([^":]+):([^"]+)"', s)
            if lib in REPO_LIBS}


def lib_entry(name, prefix):
    return (f'\t(lib (name "{name}")(type "KiCad")'
            f'(uri "{prefix}/{name}.pretty")(options "")(descr "{REPO_LIBS[name]}"))\n')


changed = []
for pro in glob.glob(os.path.join(BOARDS_DIR, "**", "*.kicad_pro"), recursive=True):
    proj_dir = os.path.dirname(pro)
    base = os.path.splitext(os.path.basename(pro))[0]
    if base == "CompleteMotorCircuit":
        continue
    sch = os.path.join(proj_dir, base + ".kicad_sch")
    if not os.path.exists(sch):
        continue
    need = used_repo_libs(sch)
    if not need:
        continue
    # portable prefix: relative path from THIS project dir to hardware/kicad/lib
    prefix = "${KIPRJMOD}/" + os.path.relpath(LIBDIR, proj_dir).replace("\\", "/")
    fp = os.path.join(proj_dir, "fp-lib-table")
    if os.path.exists(fp):
        s = open(fp, encoding="utf-8").read()
        add = [n for n in need if f'name "{n}"' not in s]
        if not add:
            continue
        idx = s.rstrip().rfind(")")
        s = s[:idx] + "".join(lib_entry(n, prefix) for n in add) + s[idx:]
    else:
        s = "(fp_lib_table\n\t(version 7)\n" + "".join(lib_entry(n, prefix) for n in sorted(need)) + ")\n"
        add = sorted(need)
    open(fp, "w", encoding="utf-8", newline="").write(s)
    changed.append(f"{os.path.relpath(proj_dir, KICAD_ROOT)}: +{add}")

print(f"patched {len(changed)} fp-lib-tables")
for c in changed:
    print("  ", c)

"""Verify every board's REPO footprints (energy_system, TerminalBlock) resolve from
its OWN project fp-lib-table - i.e. portably, on any PC after a git pull, with no
dependence on a machine-specific global KiCad footprint table.

Background: KiCad 10 dropped the stock `TerminalBlock` bornier footprints and split
some TO pad names; this repo vendors the needed libs under hardware/kicad/lib/ and
registers them per board via `${KIPRJMOD}/.../lib/*.pretty` paths. A board that uses
`TerminalBlock:` / `energy_system:` footprints but does NOT register them in its own
fp-lib-table will "work" only on a PC whose global table happens to have them, and
will fail with "footprint not found" elsewhere. This script catches that.

Pure stdlib (no pcbnew) so it runs anywhere. Run from the repo root or anywhere:
    py -3.13 hardware/kicad/tools/verify_footprints.py
Exit code 0 = all good; 1 = problems found.
"""
import os, re, sys, glob

REPO_LIBS = ("energy_system", "TerminalBlock")   # the vendored repo libs
KICAD_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BOARDS_DIR = os.path.join(KICAD_ROOT, "boards")


def parse_fp_lib_table(path):
    """nickname -> .pretty uri (raw, may contain ${KIPRJMOD})."""
    out = {}
    if not os.path.exists(path):
        return out
    s = open(path, encoding="utf-8").read()
    for m in re.finditer(r'\(lib\s+\(name "([^"]+)"\).*?\(uri "([^"]+)"\)', s):
        out[m.group(1)] = m.group(2)
    return out


def resolve_uri(uri, proj_dir):
    return os.path.normpath(uri.replace("${KIPRJMOD}", proj_dir))


def footprints_in_sch(sch):
    s = open(sch, encoding="utf-8").read()
    return set(re.findall(r'\(property "Footprint" "([^":]+):([^"]+)"', s))


def main():
    problems = 0
    boards = 0
    # a board project = a dir containing a .kicad_pro AND a .kicad_sch of the same name
    for pro in glob.glob(os.path.join(BOARDS_DIR, "**", "*.kicad_pro"), recursive=True):
        proj_dir = os.path.dirname(pro)
        base = os.path.splitext(os.path.basename(pro))[0]
        sch = os.path.join(proj_dir, base + ".kicad_sch")
        if not os.path.exists(sch):
            continue
        if base == "CompleteMotorCircuit":
            continue                              # teammate's project - do not touch
        boards += 1
        rel = os.path.relpath(proj_dir, KICAD_ROOT)
        table = parse_fp_lib_table(os.path.join(proj_dir, "fp-lib-table"))
        used = footprints_in_sch(sch)
        repo_used = sorted({(lib, name) for lib, name in used if lib in REPO_LIBS})
        issues = []
        for lib, name in repo_used:
            if lib not in table:
                issues.append(f"{lib}:{name}  -> lib '{lib}' NOT in project fp-lib-table")
                continue
            libdir = resolve_uri(table[lib], proj_dir)
            mod = os.path.join(libdir, name + ".kicad_mod")
            if not os.path.isdir(libdir):
                issues.append(f"{lib}:{name}  -> .pretty missing: {libdir}")
            elif not os.path.exists(mod):
                issues.append(f"{lib}:{name}  -> footprint file missing: {mod}")
        if issues:
            problems += 1
            print(f"[FAIL] {rel}  ({len(repo_used)} repo footprints)")
            for i in issues:
                print(f"        {i}")
        else:
            print(f"[ ok ] {rel}  ({len(repo_used)} repo footprints resolve)")
    print(f"\n{boards} boards checked, {problems} with problems.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

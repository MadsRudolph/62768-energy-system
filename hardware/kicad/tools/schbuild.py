#!/usr/bin/env python3
"""
Fælles generator for system-skemaerne (rectifier / mppt / current_sense).

Samme mønster som exp3a/build_drive.py (sexpdata, net-labels, 2.54 mm grid),
men pin-koordinaterne læses automatisk ud af KiCads symbolbiblioteker i stedet
for håndskrevne tabeller, og Footprint-property sættes ved genereringen.
"""
import copy, os, uuid as _uuid
from pathlib import Path
import sexpdata
from sexpdata import Symbol as S

# Windows (teamets PC'er) som standard; Linux/proot via $KICAD_SYMBOL_DIR-override.
LIBDIR = Path(os.environ.get("KICAD_SYMBOL_DIR")
              or (r"C:\Program Files\KiCad\9.0\share\kicad\symbols" if os.name == "nt"
                  else "/usr/share/kicad/symbols"))

def uid(): return str(_uuid.uuid4())

def _find(tree, name):
    for it in tree:
        if isinstance(it, list) and len(it) > 1 and isinstance(it[0], S) \
                and it[0].value() == "symbol" and it[1] == name:
            return it

def _extends_of(sym):
    for c in sym:
        if isinstance(c, list) and c and isinstance(c[0], S) and c[0].value() == "extends":
            return c[1]

_cache = {}
def extract(lib_id):
    """Hent symbol fra stock-lib; flad 'extends' ud (basens grafik, omdøbt)."""
    if lib_id in _cache:
        return _cache[lib_id]
    libf, name = lib_id.split(":")
    t = sexpdata.loads((LIBDIR / f"{libf}.kicad_sym").read_text(encoding="utf-8"))
    s = _find(t, name)
    if s is None:
        raise KeyError(f"symbol {lib_id} ikke fundet")
    bn = _extends_of(s)
    if bn:
        base = copy.deepcopy(_find(t, bn))
        # behold det afledte symbols egne properties (Value/Datasheet/ki_*)
        props = [c for c in s if isinstance(c, list) and c and isinstance(c[0], S)
                 and c[0].value() == "property"]
        base_no_props = [c for c in base if not (isinstance(c, list) and c and
                         isinstance(c[0], S) and c[0].value() == "property")]
        out = base_no_props[:2] + props + base_no_props[2:]
        for ch in out:
            if isinstance(ch, list) and ch and isinstance(ch[0], S) \
                    and ch[0].value() == "symbol" and isinstance(ch[1], str):
                ch[1] = ch[1].replace(bn, name, 1)
        out[1] = lib_id
        _cache[lib_id] = out
        return out
    s = copy.deepcopy(s); s[1] = lib_id
    _cache[lib_id] = s
    return s

def pins(lib_id, unit=1):
    """pin-nummer -> (x, y) i lib-koordinater (Y op) for unit 0 (fælles) + unit."""
    sym = extract(lib_id)
    name = lib_id.split(":")[1]
    res = {}
    for ch in sym:
        if not (isinstance(ch, list) and ch and isinstance(ch[0], S)
                and ch[0].value() == "symbol" and isinstance(ch[1], str)):
            continue
        parts = ch[1].rsplit("_", 2)
        if len(parts) != 3 or parts[0] != name:
            continue
        u = int(parts[1])
        if u not in (0, unit):
            continue
        for p in ch:
            if isinstance(p, list) and p and isinstance(p[0], S) and p[0].value() == "pin":
                at = num = None
                for c in p:
                    if isinstance(c, list) and c and isinstance(c[0], S):
                        if c[0].value() == "at": at = (c[1], c[2])
                        elif c[0].value() == "number": num = c[1]
                if at and num:
                    res[str(num)] = at
    return res

def _rot(a, b, ang):
    return {0: (a, b), 90: (b, -a), 180: (-a, -b), 270: (-b, a)}[ang]

def pin_xy(lib_id, p, x, y, ang, unit=1):
    px, py = pins(lib_id, unit)[p]
    ox, oy = _rot(px, -py, ang)          # lib Y-op -> skema Y-ned
    return (round(x + ox, 2), round(y + oy, 2))

def _prop(n, v, x, y, hide=False):
    p = [S("property"), n, str(v), [S("at"), x, y, 0],
         [S("effects"), [S("font"), [S("size"), 1.27, 1.27]]]]
    if hide: p[4].append(S("hide"))
    return p

def symbol(lib_id, ref, val, fp, x, y, ang, unit, pinlist, root, project):
    s = [S("symbol"), [S("lib_id"), lib_id], [S("at"), x, y, ang], [S("unit"), unit],
         [S("exclude_from_sim"), S("no")], [S("in_bom"), S("yes")], [S("on_board"), S("yes")],
         [S("dnp"), S("no")], [S("uuid"), uid()],
         _prop("Reference", ref, x + 7.62, y - 1.27), _prop("Value", val, x + 7.62, y + 1.27),
         _prop("Footprint", fp, x, y, hide=True), _prop("Datasheet", "", x, y, hide=True),
         _prop("Description", "", x, y, hide=True)]
    for p in pinlist:
        s.append([S("pin"), str(p), [S("uuid"), uid()]])
    s.append([S("instances"), [S("project"), project,
              [S("path"), f"/{root}", [S("reference"), ref], [S("unit"), unit]]]])
    return s

def wire(x1, y1, x2, y2):
    return [S("wire"), [S("pts"), [S("xy"), x1, y1], [S("xy"), x2, y2]],
            [S("stroke"), [S("width"), 0], [S("type"), S("default")]], [S("uuid"), uid()]]

def label(net, x, y, glob):
    if glob:
        return [S("global_label"), net, [S("shape"), S("input")], [S("at"), x, y, 0],
                [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("justify"), S("left")]],
                [S("uuid"), uid()],
                [S("property"), "Intersheetrefs", "${INTERSHEET_REFS}", [S("at"), 0, 0, 0],
                 [S("effects"), [S("font"), [S("size"), 1.27, 1.27]], [S("hide"), S("yes")]]]]
    return [S("label"), net, [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 1.27, 1.27]],
             [S("justify"), S("left"), S("bottom")]], [S("uuid"), uid()]]

def noconnect(x, y):
    return [S("no_connect"), [S("at"), x, y], [S("uuid"), uid()]]

def text(t, x, y):
    return [S("text"), t, [S("at"), x, y, 0],
            [S("effects"), [S("font"), [S("size"), 2, 2], [S("thickness"), 0.4], S("bold")],
             [S("justify"), S("left")]], [S("uuid"), uid()]]

def snap(v): return round(round(v / 1.27) * 1.27, 2)

def build(title, project, comps, ncs, globals_, out):
    """comps: dicts med lib/ref/val/fp/x/y/ang/unit/nets {pin: net}."""
    root = uid(); elems = []; libs = []
    for c in comps:
        c["x"], c["y"] = snap(c["x"]), snap(c["y"])
        ang, unit = c.get("ang", 0), c.get("unit", 1)
        if c["lib"] not in libs: libs.append(c["lib"])
        elems.append(symbol(c["lib"], c["ref"], c["val"], c.get("fp", ""),
                            c["x"], c["y"], ang, unit, list(c["nets"].keys()), root, project))
        for p, net in c["nets"].items():
            ex, ey = pin_xy(c["lib"], p, c["x"], c["y"], ang, unit)
            rx, ry = ex - c["x"], ey - c["y"]
            if abs(rx) >= abs(ry): sx, sy = ex + (2.54 if rx >= 0 else -2.54), ey
            else: sx, sy = ex, ey + (2.54 if ry >= 0 else -2.54)
            elems.append(wire(ex, ey, round(sx, 2), round(sy, 2)))
            elems.append(label(net, round(sx, 2), round(sy, 2), net in globals_))
    for (lib, p, x, y, ang, unit) in ncs:
        ex, ey = pin_xy(lib, p, snap(x), snap(y), ang, unit)
        elems.append(noconnect(ex, ey))
    elems.append(text(title, min(c["x"] for c in comps) - 5,
                      min(c["y"] for c in comps) - 20))
    libsyms = [S("lib_symbols")] + [extract(l) for l in libs]
    tree = [S("kicad_sch"), [S("version"), 20250114], [S("generator"), "eeschema"],
            [S("generator_version"), "9.0"], [S("uuid"), root], [S("paper"), "A4"], libsyms,
            *elems, [S("sheet_instances"), [S("path"), "/", [S("page"), "1"]]],
            [S("embedded_fonts"), S("no")]]
    Path(out).write_text(sexpdata.dumps(tree), encoding="utf-8")
    print("wrote", out)

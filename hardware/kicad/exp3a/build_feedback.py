#!/usr/bin/env python3
"""
Exp 3A "Drive Circuit" (PWM motor drive) -> KiCad 9 schematic.

Topology (best read off the reference slide -- VERIFY against it):
  PWM -> R1(200) -> ILD74 opto LED -> GND
  ILD74 transistor -> IR2110 inputs (HIN/LIN), SD->GND
  +15V -> C2(22u)+C1(100n) decoupling, -> IR2110 VDD/VCC ; VSS/COM -> GND
  IR2110 LO -> D1(1N4007) -> R3(10) -> Q1(IRF540N) gate ; R4(1k) gate pulldown
  Q1 drain -> DC motor (+20V, D2 1N4007 freewheel) ; Q1 source -> GND

Connectivity is by net labels (no wire routing) so the netlist is right even if
the layout needs tidying. Run: py -3.13 build_drive.py ; open drive_circuit.kicad_sch
"""
import copy, uuid as _uuid
from pathlib import Path
import sexpdata
from sexpdata import Symbol as S

LIBDIR = Path(r"C:\Program Files\KiCad\9.0\share\kicad\symbols")
SYMLIB = {  # lib_id -> (lib file, symbol name)
    "Device:R": ("Device", "R"), "Device:C": ("Device", "C"),
    "Device:C_Polarized": ("Device", "C_Polarized"),
    "Diode:1N4007": ("Diode", "1N4007"),
    "Transistor_FET:IRF540N": ("Transistor_FET", "IRF540N"),
    "Isolator:ILD74": ("Isolator", "ILD74"),
    "Driver_FET:IR2110": ("Driver_FET", "IR2110"),
    "Motor:Motor_DC": ("Motor", "Motor_DC"),
    "Amplifier_Operational:MCP601-xP": ("Amplifier_Operational", "MCP601-xP"),
    "Isolator_Analog:IL300": ("Isolator_Analog", "IL300"),
}
PIN = {  # pin -> (x,y) in symbol (lib Y-up)
    "Device:R": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:C": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:C_Polarized": {"1": (0, 3.81), "2": (0, -3.81)},
    "Diode:1N4007": {"1": (-3.81, 0), "2": (3.81, 0)},          # 1=K 2=A
    "Transistor_FET:IRF540N": {"G": (-5.08, 0), "D": (2.54, 5.08), "S": (2.54, -5.08)},
    "Isolator:ILD74": {"1": (-7.62, 2.54), "2": (-7.62, -2.54), "7": (7.62, 2.54), "8": (7.62, -2.54)},
    "Driver_FET:IR2110": {"1": (7.62, -7.62), "2": (0, -12.7), "3": (7.62, -5.08), "4": (-5.08, 7.62),
        "5": (7.62, -2.54), "6": (7.62, 7.62), "7": (7.62, 5.08), "8": (-5.08, 5.08), "9": (0, 12.7),
        "10": (-7.62, 0), "11": (-7.62, -5.08), "12": (-7.62, -2.54), "13": (-2.54, -12.7), "14": (-5.08, 2.54)},
    "Motor:Motor_DC": {"1": (0, 5.08), "2": (0, -7.62)},
    "Amplifier_Operational:MCP601-xP": {"1":(-5.08,-2.54),"2":(-7.62,-2.54),"3":(-7.62,2.54),"4":(-2.54,-7.62),"5":(-2.54,-2.54),"6":(7.62,0),"7":(-2.54,7.62),"8":(0,-2.54)},
    "Isolator_Analog:IL300": {"1":(-7.62,2.54),"2":(-7.62,7.62),"3":(-7.62,-2.54),"4":(-7.62,-7.62),"5":(7.62,-5.08),"6":(7.62,5.08),"7":(5.08,2.54),"8":(5.08,0)},
}
GLOBAL = {"INPUT", "FB_OUT", "+5V", "GND"}

def uid(): return str(_uuid.uuid4())
def rot(a, b, ang):
    return {0:(a,b),90:(b,-a),180:(-a,-b),270:(-b,a)}[ang]
def pin_xy(lib, p, x, y, ang):
    px, py = PIN[lib][p]; ox, oy = rot(px, -py, ang)
    return (round(x+ox,2), round(y+oy,2))
def find(t, name):
    for it in t:
        if isinstance(it,list) and len(it)>1 and isinstance(it[0],S) and it[0].value()=="symbol" and it[1]==name: return it
def extends_of(sym):
    for c in sym:
        if isinstance(c,list) and c and isinstance(c[0],S) and c[0].value()=="extends": return c[1]
    return None
def extract(lib_id):
    libf, name = SYMLIB[lib_id]
    t = sexpdata.loads((LIBDIR/f"{libf}.kicad_sym").read_text(encoding="utf-8"))
    s = find(t, name)
    bn = extends_of(s)
    if bn:  # flatten: use the base's full graphics/pins, renamed to this symbol
        base = copy.deepcopy(find(t, bn))
        for ch in base:
            if isinstance(ch,list) and ch and isinstance(ch[0],S) and ch[0].value()=="symbol" and isinstance(ch[1],str):
                ch[1] = ch[1].replace(bn, name, 1)   # IR2010_0_1 -> IR2110_0_1
        base[1] = lib_id
        return base
    s = copy.deepcopy(s); s[1] = lib_id
    return s
def _prop(n,v,x,y,hide=False):
    p=[S("property"),n,str(v),[S("at"),x,y,0],[S("effects"),[S("font"),[S("size"),1.27,1.27]]]]
    if hide: p[4].append(S("hide"))
    return p
def symbol(lib_id,ref,val,x,y,ang,unit,pinlist,root):
    s=[S("symbol"),[S("lib_id"),lib_id],[S("at"),x,y,ang],[S("unit"),unit],
       [S("exclude_from_sim"),S("no")],[S("in_bom"),S("yes")],[S("on_board"),S("yes")],
       [S("dnp"),S("no")],[S("uuid"),uid()],
       _prop("Reference",ref,x+7.62,y-1.27),_prop("Value",val,x+7.62,y+1.27),
       _prop("Footprint","",x,y,hide=True),_prop("Datasheet","",x,y,hide=True),
       _prop("Description","",x,y,hide=True)]
    for p in pinlist: s.append([S("pin"),str(p),[S("uuid"),uid()]])
    s.append([S("instances"),[S("project"),"exp3a",[S("path"),f"/{root}",[S("reference"),ref],[S("unit"),unit]]]])
    return s
def wire(x1,y1,x2,y2):
    return [S("wire"),[S("pts"),[S("xy"),x1,y1],[S("xy"),x2,y2]],
            [S("stroke"),[S("width"),0],[S("type"),S("default")]],[S("uuid"),uid()]]
def label(net,x,y,glob):
    if glob:
        return [S("global_label"),net,[S("shape"),S("input")],[S("at"),x,y,0],
                [S("effects"),[S("font"),[S("size"),1.27,1.27]],[S("justify"),S("left")]],[S("uuid"),uid()],
                [S("property"),"Intersheetrefs","${INTERSHEET_REFS}",[S("at"),0,0,0],
                 [S("effects"),[S("font"),[S("size"),1.27,1.27]],[S("hide"),S("yes")]]]]
    return [S("label"),net,[S("at"),x,y,0],
            [S("effects"),[S("font"),[S("size"),1.27,1.27]],[S("justify"),S("left"),S("bottom")]],[S("uuid"),uid()]]
def noconnect(x,y): return [S("no_connect"),[S("at"),x,y],[S("uuid"),uid()]]
def text(t,x,y):
    return [S("text"),t,[S("at"),x,y,0],[S("effects"),[S("font"),[S("size"),2,2],[S("thickness"),0.4],S("bold")],
            [S("justify"),S("left")]],[S("uuid"),uid()]]

def snap(v): return round(round(v/1.27)*1.27, 2)   # nearest 1.27 mm grid

def build(title, comps, ncs, out):
    root=uid(); elems=[]; libs=[]
    for c in comps:
        c["x"], c["y"] = snap(c["x"]), snap(c["y"])
        if c["lib"] not in libs: libs.append(c["lib"])
        elems.append(symbol(c["lib"],c["ref"],c["val"],c["x"],c["y"],c.get("ang",0),
                            c.get("unit",1),list(c["nets"].keys()),root))
        for p,net in c["nets"].items():
            ex,ey=pin_xy(c["lib"],p,c["x"],c["y"],c.get("ang",0))
            # stub outward along dominant axis
            rx,ry=ex-c["x"],ey-c["y"]
            if abs(rx)>=abs(ry): sx,sy=ex+(2.54 if rx>=0 else -2.54),ey
            else: sx,sy=ex,ey+(2.54 if ry>=0 else -2.54)
            elems.append(wire(ex,ey,round(sx,2),round(sy,2)))
            elems.append(label(net,round(sx,2),round(sy,2),net in GLOBAL))
    for (lib,ref,p,x,y,ang,unit) in ncs:
        ex,ey=pin_xy(lib,p,snap(x),snap(y),ang); elems.append(noconnect(ex,ey))
    elems.append(text(title, comps[0]["x"]-5, min(c["y"] for c in comps)-22))
    libsyms=[S("lib_symbols")]+[extract(l) for l in libs]
    tree=[S("kicad_sch"),[S("version"),20250114],[S("generator"),"eeschema"],
          [S("generator_version"),"9.0"],[S("uuid"),root],[S("paper"),"A4"],libsyms,*elems,
          [S("sheet_instances"),[S("path"),"/",[S("page"),"1"]]],[S("embedded_fonts"),S("no")]]
    Path(out).write_text(sexpdata.dumps(tree),encoding="utf-8")
    print("wrote",out)


# ---------------- Feedback Circuit (isolated linear amp, IL300 servo) ----------------
OA = "Amplifier_Operational:MCP601-xP"
fb=[
  {"lib":"Device:R","ref":"R1","val":"10k","x":40,"y":86,"nets":{"1":"INPUT","2":"IN_P"}},
  {"lib":"Device:R","ref":"R2","val":"2k","x":53,"y":102,"nets":{"1":"IN_P","2":"GND"}},
  {"lib":OA,"ref":"U3","val":"MCP601","x":70,"y":92,"nets":{"3":"IN_P","2":"SERVO","6":"U3_OUT","7":"+5V","4":"GND"}},
  {"lib":"Device:R","ref":"R3","val":"33k","x":58,"y":112,"nets":{"1":"SERVO","2":"GND"}},
  {"lib":"Device:R","ref":"R4","val":"200","x":92,"y":92,"nets":{"1":"U3_OUT","2":"LED"}},
  {"lib":"Isolator_Analog:IL300","ref":"U1","val":"IL300","x":116,"y":92,
     "nets":{"1":"+5V","2":"LED","3":"SERVO","4":"GND","5":"GND","6":"OUT_PD"}},
  {"lib":OA,"ref":"U4","val":"MCP601","x":150,"y":92,"nets":{"2":"OUT_PD","3":"GND","6":"FB_OUT","7":"+5V","4":"GND"}},
  {"lib":"Device:R","ref":"R5","val":"33k","x":150,"y":74,"nets":{"1":"OUT_PD","2":"FB_OUT"}},
]
ncs=[(OA,"U3","1",70,92,0,1),(OA,"U3","5",70,92,0,1),(OA,"U3","8",70,92,0,1),
     (OA,"U4","1",150,92,0,1),(OA,"U4","5",150,92,0,1),(OA,"U4","8",150,92,0,1),
     ("Isolator_Analog:IL300","U1","7",116,92,0,1),("Isolator_Analog:IL300","U1","8",116,92,0,1)]

if __name__=="__main__":
    build("Feedback Circuit  (Exp 3A: isolated linear amp - MCP601 -> IL300 servo -> MCP601)",
          fb, ncs, Path(__file__).parent/"feedback_circuit.kicad_sch")

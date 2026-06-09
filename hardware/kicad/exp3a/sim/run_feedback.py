import re
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
ng=NgSpiceShared.new_instance()
ng.load_circuit(open("feedback_behavioral.cir").read())
def node(n):
    s="".join(ng.exec_command(f"print {n}"))
    m=re.findall(r"[-+]?\d+\.?\d*[eE][-+]?\d+|[-+]?\d+\.\d+",s);return float(m[-1]) if m else float("nan")
print("INPUT  FB_OUT  ratio")
for i in range(0,16):
    ng.exec_command(f"alter vin = {i}");ng.exec_command("op")
    fb=node("v(fb_out)");print(f"{i:5d} {fb:8.4f} {fb/i if i else 0:7.4f}")

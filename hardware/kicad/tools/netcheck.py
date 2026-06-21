import json, sys, collections

d = json.load(open(sys.argv[1], encoding="utf8"))
nets = collections.defaultdict(list)
refs = set()
nofp = []
for c in d["components"]:
    refs.add(c["ref"])
    if not c.get("footprint"):
        nofp.append(c["ref"])
    for p, n in c["pads"].items():
        nets[n].append(f'{c["ref"]}.{p}')

print("components:", len(refs))
print("missing footprint:", nofp or "none")
for q in sys.argv[2:]:                # extra queries: "ref.pad" -> prints its net
    hit = [n for n, m in nets.items() if q in m]
    print(f"  {q} -> {hit[0] if hit else '(NOT CONNECTED)'}")

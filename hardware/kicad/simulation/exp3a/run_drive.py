import numpy as np
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
ng=NgSpiceShared.new_instance()
ng.load_circuit(open("drive_behavioral.cir").read())
ng.exec_command("tran 1u 3m uic")
p=ng.plot(None,ng.last_plot)
t=np.array(p["time"].to_waveform());ila=np.array(p["la#branch"].to_waveform());vsw=np.array(p["sw"].to_waveform())
m=t>2e-3;imot=-ila[m]
print(f"motor I avg={imot.mean():.3f}A pp={imot.max()-imot.min():.3f}A | SW {vsw[m].min():.2f}..{vsw[m].max():.2f}V")

"""Write an OrcaSlicer project (.3mf) with the printed parts of the machine (feeder parts excluded, they have
their own project: feeder/orca_project.py). PETG, 0.4 mm nozzle, settings from report.md "Printing".

    python orca_machine.py [template.3mf] [out.3mf]

Run `pnp build` first so out/parts_stl is current. Printer, process and PETG come from the newest Adventurer 5M
project in Documents (or the template given), as for the feeder project.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "feeder"))
import orca_project as O  # noqa: E402

STL = os.path.join(HERE, "out", "parts_stl")

# report.md: 0.2 mm, 4 perimeters, 5 top/bottom, 40 % gyroid, elephant-foot 0.2, no supports
BASE = {"wall_loops": "4", "top_shell_layers": "5", "bottom_shell_layers": "5", "sparse_infill_density": "40%",
        "sparse_infill_pattern": "gyroid", "elefant_foot_compensation": "0.2", "enable_support": "0"}
# bridge ends: 100 % infill (report); head parts are specified in PETG-CF: in plain PETG they get 6 walls and 60 %
SOLID = dict(BASE, sparse_infill_density="100%")
HEAD = dict(BASE, wall_loops="6", sparse_infill_density="60%")

PARTS = [  # stl, count, settings (identical copies share one STL)
    ("Corner_FrontLeft", 1, BASE), ("Corner_FrontRight", 1, BASE), ("Corner_RearLeft", 1, BASE),
    ("Corner_RearRight", 1, BASE),
    ("Bridge_End_Front", 2, SOLID),                 # front and rear ends are the same part
    ("Head_Carriage", 1, HEAD), ("Head_BeltClamp", 1, HEAD),
    ("XIdler_Slider_Front", 2, BASE),               # front and rear sliders are the same part
    ("XChain_TrayBracket_1", 3, BASE), ("XChain_Arm", 1, BASE),
    ("PCB_SlideClamp", 1, BASE), ("UpCam_Housing", 1, BASE),
]


def plates(w=220.0, d=220.0):
    parts = []
    for name, count, opts in PARTS:
        bb = O.read_stl(os.path.join(STL, name + ".stl"))[2]
        sx, sy = bb[3] - bb[0], bb[4] - bb[1]
        parts.append((name, count, opts, 1, sx * sy, sx, sy))
    return O.auto_plates(parts, w, d, "Machine")


if __name__ == "__main__":
    tpl = sys.argv[1] if len(sys.argv) > 1 else O.default_template()
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out", "TEVO_BW_PnP_machine_parts.3mf")
    O.build(tpl, out, plates(), STL, "TEVO-BW PnP - machine printed parts (PETG, 0.4 mm)", add_tpu=False)

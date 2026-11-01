# TEVO-BW pick-and-place: FreeCAD model (scripts + CLI)

A parametric FreeCAD model of the TEVO Black Widow pick-and-place conversion. The current implementation has
changed from parts of the original specification; use [BUILD_AND_ASSEMBLY.md](BUILD_AND_ASSEMBLY.md) and the
generated `out/report.md` to understand the current architecture. Everything runs headless with the Python
bundled with FreeCAD 1.1. You don't need the FreeCAD GUI.

```
.\pnp.ps1 build    # FCStd, STEP/STL parts, BOM, report and OpenPnP coordinate JSON in out/
.\pnp.ps1 check    # modeled interference checks at selected poses
.\pnp.ps1 render   # review PNGs in out/render/
.\pnp.ps1 all      # build + check + render
.\pnp.ps1 info     # derived dimensions and OpenPnP coordinates as JSON
.\pnp.ps1 gui      # open the model in the FreeCAD GUI

options: --pose X Y Z C   machine pose (mm from home, Z <= 0, deg)   e.g. --pose 200 150 -30 90
         --views iso,head --size 1600x1000 --ss 2 --zoom 1.0 --prefix name_
```

Use `pnp.cmd` in cmd or `.\pnp.ps1` in PowerShell. The wrappers detect the common `FreeCAD_1_1` and `FreeCAD 1.1` install folders. If FreeCAD is installed somewhere else, set `FREECAD_BIN`.

| File | Contents |
| --- | --- |
| `params.py` | All dimensions and choices (TS sections cited). Edit this file first. |
| `model/frame.py` | Reoriented C-beam frame, ties and corner/drive blocks |
| `model/xaxis.py` | Dual GT2 X belts, jackshaft, bridge ends and bridge beam |
| `model/yaxis.py` | MGN12 Y rail, carriage and stock belt drive |
| `model/head.py` | Lightweight carriage, MGN9 Z, NEMA8 linear motor/T5x2 slide, C nozzle rotation and down camera |
| `model/tooling.py` | Tooling plate, PCB fixture, up camera, feeder bank and 6-pocket magazine |
| `model/services.py` | Vacuum panel, E-stop and pump switch, X and Y drag chains (built for each pose) |
| `model/assembly.py` | Motion groups (bridge / carriage / zslide / rotor), pose placements, FCStd writer |
| `render.py` | Coin3D offscreen renderer to PNG |
| `model/feeder.py` | TBW-Feeder v3.0 lane + bank geometry (exit chute, waste bin, reel rack) |
| `feeder/` | Feeder build, audit, firmware and production documents, see `feeder/README.md` |
| `electronics/` | Preliminary 24 V power distribution, SBC and enclosure concept, diagrams and BOM |

Colours: `pnp gui` (or `freecad.exe open_gui.py`) applies them and saves them into the FCStd. Every object also has
`MoveGroup`, `Kind`, `MassGram` and `BOM` properties.

See [BUILD_AND_ASSEMBLY.md](BUILD_AND_ASSEMBLY.md) for the physical build sequence, assembly diagrams, changes
from the original specification and prioritized project improvements. The CAD interference check does not
replace physical fit, wiring or acceptance tests.

The complete 82-page PDF dossier is `out/TEVO_BW_PnP_Dossier.pdf`; it contains a contents page, illustrated overview, source manuals, three BOMs and the render catalog. Rebuild from the workspace root with `powershell -NoProfile -ExecutionPolicy Bypass -File .\pnp\out\build_master_dossier.ps1`. See `out/render/RENDER_STATUS.md` for the current-vs-legacy feeder render manifest. Electrical architecture, detailed terminal wiring and software setup are documented in `electronics/POWER_CONTROL_DESIGN.md`, `WIRING_DETAILS.md` and `PI5_SOFTWARE.md`.

## Printed parts (rev E)

`model/printing.py` handles every `kind="print"` part: it is coloured orange, given a print orientation
(`UP` / `LANE_UP` tables), horizontal holes over 5.2 mm get a 45 deg teardrop roof, and the STL in
`out/parts_stl/` is written already lying on the bed. `report.md` -> "Printing" lists orientation, size,
bed contact, overhang and bridge area per part. No part needs supports.

# TBW-Feeder v2.1: motorised 8 mm SMD tape feeder

This folder holds the tape feeder for the TEVO-BW pick-and-place: 8 lanes at a 22 mm pitch. One servo per lane
drives both the feed and the peel. The geometry is in `../model/feeder.py`. The machine model uses the same code,
so the two can't drift apart.

```
feeder build   # out/: one lane + bank parts as FCStd/STEP, stl/ (printed, lying on the bed), step/ (laser cut, incl.
               #       CoverPlate_flat.dxf), bom.csv (per lane, per bank, totals for 8 lanes)
feeder audit   # out/audit.md: overlaps, motion sweep, assembly paths, wall thickness, loads, bank vs machine
feeder all
feeder animate # out/feeder_animation.gif: one 4 mm feed cycle rendered from the model (lane, pawl, peel drive)
python orca_project.py   # out/TBW_Feeder_v2.1.3mf: OrcaSlicer project, one lane + bank parts on 6 plates
```

`orca_project.py` takes the printer, process and PETG settings from the newest Adventurer 5M project in
`Documents` (or a `.3mf` given as the first argument) and adds Orca's Flashforge Generic TPU as filament 2 for the
drive roller. Each part carries its own settings from `ASSEMBLY.md` (0.12 mm and 100 % for the precision parts,
4 walls and 40 % gyroid for the body). Run `feeder build` first so the STLs are current.

To view the feeder in FreeCAD with one colour per part, open it through `open_gui.py`. Opening the FCStd directly
shows grey parts.

```
$env:PNP_FCSTD = "D:\TEVO_BW\pnp\feeder\out\tbw_feeder_lane.FCStd"
& "$env:LOCALAPPDATA\Programs\FreeCAD_1_1\bin\freecad.exe" D:\TEVO_BW\pnp\open_gui.py
```

`pnp gui` does the same for the whole machine. `PNP_COLORS=kind` switches back to orange for all printed parts.

Use `feeder.cmd` (cmd) or `.\feeder.ps1` (PowerShell), with `FREECAD_BIN` set to FreeCAD's `bin` folder. On this PC
that is `%LOCALAPPDATA%\Programs\FreeCAD_1_1\bin`. `audit` exits with code 1 if any check fails.

| Document | Contents |
| --- | --- |
| [DESIGN.md](DESIGN.md) | How it works, layout, numbers, load cases, limits |
| [ASSEMBLY.md](ASSEMBLY.md) | Print and laser settings, part preparation, assembly order, calibration, tape loading |
| [ELECTRONICS.md](ELECTRONICS.md) | Controller modules, wiring table, power budget, flashing |
| [OPENPNP.md](OPENPNP.md) | Driver, actuators, feeder setup |
| [TEST.md](TEST.md) | First-article and acceptance tests |
| `firmware/tbw_feeder_fw/` | Controller firmware (Arduino Nano), G-code M600–M620, settings in EEPROM |

## How it works

An SG90 servo hangs upside down in the tower above the tape. A pin in its horn reaches down beside the tape to a
slider underneath, forming a scotch yoke with a 4.2 mm stroke. A printed flexure pawl pushes the tape exactly one
sprocket hole (4.0 mm), and a half stroke gives 2 mm. A spring tongue in the printed cover plate is the detent.
The same servo stroke peels the cover tape. A peg in the slider tail lifts a printed lifter through an inclined
slot, and a flexure pawl on the lifter turns an 18-tooth ratchet that carries a TPU roller: 2 teeth (4.9 mm) per
4 mm fed. A flexure hold pawl keeps the tension between feeds. A sprung printed nip roller pulls the cover tape into
a waste bin and slips at about 1.2 N, which limits the tension and absorbs the surplus. Empty tape drops through a
slot in the tooling plate, and the reels stand on a rack behind the machine.

## Status (2026-10-18)

**Design complete: revision 2.1 (servo-driven peel, no N20), ready for the first article.**

- `feeder audit`: all checks pass (see `out/audit.md`).
- `pnp check`: no head collisions with all 8 lanes, the chute, the bin and the rack.
- The firmware compiles for the Nano.

What remains needs hardware: build one lane plus the controller and pass `TEST.md` (feed accuracy, endurance,
picks in the machine). Only then print the other seven lanes. The SG90 is modelled from catalogue dimensions; test
A7 checks the delivered one. The ratchet and the two peel pawls are new in v2.1 and have not been tested in hardware
yet (A4, B5, B7). Apart from the servo, horn pin, pinch spring and screws, every lane part is printed, the
cover plate included (a steel cover plate stays available as a fallback).

The technical specification (TS 2.2, 7.7, WP8) still describes head-actuated lever lanes. Decision D12 in
`../out/report.md` records the change to this feeder.

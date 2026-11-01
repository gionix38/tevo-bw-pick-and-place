# TBW-Feeder v3.0: motorised 8 mm SMD tape feeder

This folder holds the tape feeder for the TEVO-BW pick-and-place: 8 lanes at a 22 mm pitch. One servo per lane
drives both the feed and the peel. The geometry is in `../model/feeder.py`. The machine model uses the same code,
so the two can't drift apart.

```
feeder build   # out/: one lane + bank parts as FCStd/STEP, stl/ (printed, lying on the bed), bom.csv
               #       (per lane, per bank, totals for 8 lanes)
feeder audit   # out/audit.md: overlaps, motion sweep, pawl ride-over, assembly paths, cover plate bayonet,
               #       support-free printing, walls, loads, bank vs machine
feeder all
feeder animate # out/feeder_animation.gif: one 4 mm feed cycle rendered from the model (lane, pawls, peel drive)
python orca_project.py   # out/TBW_Feeder_v3.0.3mf: OrcaSlicer project, one lane + bank parts
python print_time.py ... # slicer time + filament per part on your printer profile (see DESIGN.md)
```

`orca_project.py` takes the printer, process and PETG settings from the newest Adventurer 5M project in
`Documents` (or a `.3mf` given as the first argument). Each part carries its own settings from `ASSEMBLY.md`. Run
`feeder build` first so the STLs are current.

To view the feeder in FreeCAD with one colour per part, open it through `open_gui.py`. Opening the FCStd directly
shows grey parts.

```
$env:PNP_FCSTD = "D:\TEVO_BW\pnp\feeder\out\tbw_feeder_lane.FCStd"
& "$env:LOCALAPPDATA\Programs\FreeCAD_1_1\bin\freecad.exe" D:\TEVO_BW\pnp\open_gui.py
```

Use `feeder.cmd` (cmd) or `.\feeder.ps1` (PowerShell), with `FREECAD_BIN` set to FreeCAD's `bin` folder. On this PC
that is `%LOCALAPPDATA%\Programs\FreeCAD_1_1\bin`. `audit` exits with code 1 if any check fails.

| Document | Contents |
| --- | --- |
| [DESIGN.md](DESIGN.md) | Why v3.0, TRIZ analysis, layout, mechanisms, numbers, print times, limits |
| [ASSEMBLY.md](ASSEMBLY.md) | Print settings, bought parts, preparation, assembly order, calibration, tape loading |
| [ELECTRONICS.md](ELECTRONICS.md) | Controller modules, wiring table, power budget, flashing |
| [OPENPNP.md](OPENPNP.md) | Driver, actuators, feeder setup |
| [TEST.md](TEST.md) | First-article and acceptance tests |
| `firmware/tbw_feeder_fw/` | Controller firmware (Arduino Nano), G-code M600–M620, settings in EEPROM (µs) |

The feeder bank's power branch is part of the machine panel design in [`../electronics/POWER_CONTROL_DESIGN.md`](../electronics/POWER_CONTROL_DESIGN.md). Keep the Nano on USB serial and feed servo current from the separate fused 5 V rail described in [`ELECTRONICS.md`](ELECTRONICS.md).

The v2.1 sources and outputs are kept in `../legacy/feeder_v2.1/`.

## How it works

An MG90S servo hangs upside down in the tower above the tape. A printed gear on its spline drives a rack on the
slider, which runs in a tunnel under the tape: 4.2 mm stroke = 37° of servo rotation.

- **Feed:** a rigid printed pawl on a screw pivot, pressed up by a steel spring, pushes the tape exactly one
  sprocket hole (4.0 mm); a half stroke gives 2 mm. The pawl's pivot sits below and behind its tooth, so the push
  load drives the tooth deeper into the hole.
- **Detent:** the same pawl, mounted in the body, blocks back-drag.
- **Peel:** the same stroke peels the cover tape. A rack fixed to the slider turns a 36-tooth idler, and the
  idler turns a 14-tooth pinion printed with its shaft. An HF0612 one-way bearing in the
  drive roller passes the motion on only in the feed direction, giving 4.8 mm of cover tape per 4 mm fed. A
  second HF0612 in the pinch roller keeps the cover tape taut on the retract. The sprung nip slips at about 1.2 N,
  which limits the tension.
- **Cover plate:** it sits in segmented rails and is locked by 2 countersunk M2 screws. Take them out, slide it
  6.8 mm and lift it off to load a tape.
- **Body:** a main body plus a side plate. Every part is laid in from the split face, and every printed part
  prints flat in PETG on a 0.4 mm nozzle without supports.

## Status (2026-10-22)

**Design revision 3.0, ready for the first article.** It replaces v2.1 after that lane's first article: weak,
slipping feed; ratchet slipping or jamming; printed springs and the snap cap not holding; 10 h of printing per lane
with supports on a 0.25 mm nozzle.

- `feeder audit`: see `out/audit.md`.
- The firmware (3.0.0) compiles for the Nano.

What remains needs hardware. Build one lane plus the controller and pass `TEST.md`, including A0 (print without
supports and compare the times) and the tests marked as v2.1 issues. Only then print the other seven lanes. The
lane mounting holes are the same as for v2.1, so the tooling plate doesn't change. The waste bin tray is new: it
is 3 mm lower and 2.5 mm further back.

The technical specification (TS 2.2, 7.7, WP8) still describes head-actuated lever lanes. Decisions D12 and D14
in `../out/report.md` record the change to this feeder.

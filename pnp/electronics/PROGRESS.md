# Power/control design progress

Date: 2026-10-31

## Delivered in this revision

- Proposed 24 V distribution architecture with independently protected motion, vacuum and servo branches.
- Selected Raspberry Pi 5 as the first SBC candidate with a separate official USB-C PSU; documented the ARM64/OpenPnP/dual-camera gate and x86-64 fallback.
- Specified an enclosure concept envelope of 300 x 240 x 120 mm and separated AC, motor power, servo DC and SBC/camera zones.
- Added editable vector wiring and enclosure diagrams, PNG concept renders, preliminary BOM and machine-readable power/control notes.
- Replaced feeder electronics note with v3.0 wiring, explicit USB backfeed prevention and revised power validation instructions.
- Added power/control pages to the combined technical dossier and clarified which feeder render is current.
- Regenerated `feeder.png`, `feeder_mech.png`, `feeder_sheet.png` and `peel_exploded.png` from the current FreeCAD v3.0 model; corrected FreeCAD install-path discovery in the PowerShell wrappers.
- Regenerated the feeder cycle animation from the current model (38 frames).
- Added terminal-level AC/PE/DC/E-stop wiring and detailed host/camera/USB/Nano topology diagrams in editable SVG and PNG.
- Added Raspberry Pi OS/OpenPnP preparation notes with official download locations and the ARM64 packaging limitation.

## Limits and next engineering gates

The donor board/drivers, PSU voltage, pump and valve, motors, servo stall currents, camera models and physical enclosure mounting have not been measured or identified. Protection ratings and cable gauges therefore remain TBD. The diagrams are concepts, not mains wiring or manufacturing drawings. Do not apply power until the actual module ratings, protective earth, E-stop behavior, branch protection and DC/DC outputs have been checked.

Next: identify all donor electrical components; perform an OpenPnP ARM64/camera bring-up; confirm the 24 V and 5 V load budgets; choose branch fuse/cable/contactors; check component clearances and ventilation; then produce a dimensioned mechanical panel drawing.

## Source/render status

The current feeder model source is `pnp/model/feeder.py`; all four current feeder renders were regenerated with FreeCAD 1.1 on 2026-10-31. `pnp/out/render/revD.png` remains a historical render. The electrical enclosure renders are concept illustrations generated from editable SVG/source scripts.

## Version control

Commit requested by the user. The supplied directory does not currently contain a `.git` repository (`git status` reports “not a git repository”), so a commit cannot be created in this workspace state. Preserve this progress record and commit the changes after restoring/initializing the intended repository.

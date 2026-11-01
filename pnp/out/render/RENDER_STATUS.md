# Render manifest

Current feeder geometry comes from `../../model/feeder.py` and `../../feeder/tbw_feeder.py` (TBW-Feeder v3.0).

- `feeder.png` — regenerated from the current machine CAD scene on 2026-10-31; shows the eight-lane bank in context.
- `feeder_mech.png` — regenerated from the current machine CAD scene on 2026-10-31; shows the v3 lane kinematics.
- `feeder_sheet.png` — regenerated composite of the bank, mechanism and peel-head exploded view on 2026-10-31.
- `../../feeder/out/peel_exploded.png` — regenerated from feeder v3.0 source on 2026-10-31.
- `../../feeder/out/feeder_animation.gif` — regenerated from the current feeder cycle on 2026-10-31, 38 frames.
- `revD.png` remains a historical render and is not the current assembly.

Rebuild the composite with `../../feeder/make_feeder_sheet.ps1`. `../../pnp.ps1 render --views feeder,feeder_mech` discovers both common FreeCAD Windows install folders. Other main machine views remain from October 2026; rerender them after future geometry changes.

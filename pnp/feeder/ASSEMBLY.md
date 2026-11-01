# TBW-Feeder v3.0: manufacturing and assembly

Quantities are per lane unless marked "per bank". `out/bom.csv` has the full list with totals for 8 lanes. Run
`feeder build` first; it writes every file named below.

## 1. Make the parts

### Printed (STLs in `out/stl/`, already lying in print orientation)

One material (PETG) and one 0.4 mm nozzle for everything. Use 0.20 mm layers and no supports; every part lies
flat on a face, and every pocket opens upward. `python orca_project.py` writes `out/TBW_Feeder_v3.0.3mf` with the
three lane plates and the bank plates already set up.

| File | Qty | Settings |
| --- | --- | --- |
| `Body.stl` | 1 | 4 walls, 40 % gyroid. The main body prints on its +Y outer face. |
| `SidePlate.stl` | 1 | 4 walls, 40 % gyroid, on its outer face. Each of the 3 counterbores ends in a 0.2 mm bridging layer; pierce it with a 3 mm drill by hand. |
| `CoverPlate.stl` | 1 | 100 %. It prints tape side down, so the smooth bed side touches the tape. |
| `PinchYoke.stl` | 1 | 4 walls, 40 %, bridge down |
| `Slider.stl`, `Rack.stl`, `Idler.stl`, `Pinion.stl` | 1 each | 100 %, flat as exported |
| `DriveRoller.stl` | 2 | 100 %. The same roller body serves as the drive roller and the pinch roller. |
| `ServoGear.stl` | 1 | 100 %, flat as exported. It replaces the stock horn. |
| `Pawl.stl` | 2 | 100 %. One part serves as both the feed pawl and the detent. |
| `Feeder_ExitChute.stl` | 1 per bank | 3 walls, 30 %, standing on its end |
| `Feeder_WasteBin.stl`, `Feeder_WasteBinLeg.stl` | 1 + 2 per bank | 3 walls, 20 % |
| `ReelRack_Side.stl` | 2 per bank | 4 walls, 30 % |
| `ReelHub.stl` | 8 per bank | 3 walls, 30 % |

Check the printed parts:
- The tape channel passes an 8.0 mm gauge strip.
- The slider lies in its tunnel and slides over 4.2 mm without force.
- Both pawls turn freely on an M2 screw.
- `python print_time.py` gives the slicer's time per part on your printer profile (see the table in
  `DESIGN.md`).

### Purchased

All standard parts. Order them per 8 lanes from `out/bom.csv`.

| Part | Qty | Use |
| --- | --- | --- |
| Servo MG90S (metal gears and a metal spline, SG90 size) | 1 | Advance. An SG90 fits, but its plastic spline grips the gear less. |
| Set screw M2 × 5 | 2 | Pawl pivots, threaded into the printed holes |
| M2 × 6 SHCS | 2 | Take-up rack to slider |
| M2 × 8 countersunk, DIN 965 | 2 | Cover plate upstand to the tower (self-tapping into PETG) |
| One-way needle bearing HF0612 (6 × 10 × 12) | 2 | Drive roller, pinch roller |
| O-ring 12 × 1.5, NBR 70 | 4 | Tyres on both rollers |
| Compression spring OD 3 × 0.3 wire × L0 8 (≈ 0.5 N/mm) | 2 | Pawls |
| Compression spring OD 5 × 0.4 wire × L0 9 (≈ 0.75 N/mm) | 1 | Pinch |
| M3 heat-set insert | 6 | 3 in the lane bottom, 3 in the split face |
| M3 × 8 SHCS | 3 | Tooling plate to lane, from below |
| M3 × 10 SHCS | 3 | Side plate to main body |
| (servo kit screw) | 1 | Servo gear on the spline |

There are no metal pins: the drive shaft (on the pinion), the pinch axle and the guide bar are printed PETG,
the pawl pivots are screws. There is no TPU, no laser-cut part, no thumb screw and no stock horn.

## 2. Prepare

For a trial assembly before the bearings arrive, print plate 4 of the Orca project: 2 × `TestFit_HF0612`, a
plain Ø9.8 × 12 tube with a 6.3 bore. It slides into the rollers and onto the shafts but has **no clutch**,
so with it the peel doesn't work; swap in the real HF0612 before running tape. `out/peel_exploded.png` shows
the order.

1. **Inserts.** Use a soldering iron at 220 °C. Put 3 M3 inserts in the lane bottom and 3 in the holes in the
   split face of the main body (6 per lane, matching `out/bom.csv`). Each insert finishes flush.
2. **Servo gear.** Set the servo to 90° (`M604 N<lane> S90`). Push the gear sector onto the spline with its teeth
   along +Y; the metal spline cuts its teeth into the 4.8 mm bore. Fit the servo's screw from below. Try to turn
   the gear against the servo by
   hand: there must be no play.
3. **One-way bearings.** Press one HF0612 into each of the two roller bodies, flush, in a vise, and roll two
   O-rings onto each roller.
   The direction matters:
   - Drive roller, on its shaft: the roller must turn freely when its top moves toward the tower front (the pick
     side) and lock the other way.
   - Pinch roller, on its axle: it must turn freely when its top moves toward the rear (the waste bin) and lock
     the other way.
   - If a direction is wrong, press the bearing out and turn it around.
4. **Drive group.** The pinion and the drive shaft are one printed part. Slide one roller onto the shaft from
   its free end, up to the pinion. If the HF0612 is tight on the printed shaft, sand the shaft lightly; it
   must not wobble.
5. **Pinch group.** Push the printed 6 × 14 axle through the pinch roller into the yoke arm (the yoke has one
   arm, on +Y). The axle is a press fit in the yoke; add a drop of CA glue if it is loose.
6. **Cover plate screws.** Turn the 2 M2 × 8 countersunk screws once into the pilot holes in the tower face
   (side plate) to cut the threads, then take them out again.
7. **Pawls.** Put a spring into the bore under each pawl seat, lay the pawl on it (tooth toward the tape),
   and turn the M2 × 5 set screw through both walls. The pawl must spring back onto its stop by itself.

## 3. Assemble one lane

Lay the main body on its +Y outer face, split face up. Every part goes in from above, in this order. `feeder
audit` checks each path.

1. **Slider.** Fit the feed pawl (step 2.7). Screw the take-up rack to the slider tail with 2 × M2 × 6, teeth
   up. Lay the slider into its tunnel; its rack arm goes into the passage beside the tape channel.
2. **Servo.** With the gear fitted (step 2.2) at 90° and the slider at mid stroke, lay the servo into its pocket.
   The gear teeth come into mesh with the slider rack. The tabs go into the tab slot. No screws: the side plate
   captures the tabs.
3. **Detent.** Put the second pawl with its spring into its housing in front of the slider; it goes in through
   the opening in the tape floor. Turn its M2 × 5 set screw in from the split face.
4. **Guide bar.** It is fitted after the side plate (step 8).
5. **Drive group.** Put the shaft into the hole in the +Y cheek, with the pinion on the split side.
6. **Pinch group.** Put the pinch spring into its pocket in the tower top. Press the yoke down onto it and lay
   it in with the roller under the drive roller.
7. **Idler.** Lay the 36T idler (axle stub toward you) onto the side of the servo, so it meshes with the
   rack below and the pinion above. Turn the drive roller a little until the teeth slide in.
8. **Side plate.** Lay it on; the idler's stub goes into its hole and the journal pin into the end of the pinion
   shaft. Fit 3 × M3 × 10, then push the printed guide bar (head first in the counterbore) through the side
   plate, across the riser, into the post. The idler, the pawl screws, the drive shaft and the servo tabs are
   now captured.
9. **Function check.** Step the servo with `M604 N<lane> U1291` and `U1709`:
   - The slider and the rack move 4.2 mm; the idler turns about 13° back and forth.
   - The roller turns only on the feed stroke (`U1291` → `U1709`) and stands still on the retract.
10. **Cover plate.** Lower it with its rear end about 7 mm in front of the post, so the edge tongues drop into the
    gaps between the rail lips. Slide it toward the tower until the upstand touches it, then fit the 2 M2 × 8
    countersunk screws. Lifting it at home must not be possible.
11. **Cable.** Run the servo lead out at the rear and label it with the lane number.

## 4. Mount the bank

1. **Tooling plate.** Tap M3 into the six chute holes and the two waste-bin holes. The lane holes and the
   empty-tape slot are machined from the plate drawing (`../out/parts_step/Tooling_Plate.step`). They are the
   same as for v2.1.
2. **Lanes.** Set each lane on the plate and fix it from below with 3 × M3 × 8. The heads sit in the 3.2 mm
   counterbores. Lane 1 is at Y 150 and the pitch is 22 mm.
3. **Exit chute.** Fix it with 6 × M3 × 20. Put a box at least 200 × 150 mm on the bench under the slot.
4. **Waste bin.** Stand the two legs behind the lanes and set the tray on top. Fix it with 2 × M3 × 50 through
   the tray floor, the legs and into the plate. In v3.0 the tray is 3 mm lower than in v2.1 and starts 2.5 mm
   further back, under the cover tape exit.
5. **Reel rack.** Fit the two side plates and the two M8 rods with the 8 hubs between them (flange toward +Y).
   Stand the rack on the bench with the axle 760 mm from the machine origin X.
6. **Controller.** Wire it as in `ELECTRONICS.md` and flash firmware 3.0.0. Send `M502` and `M500` to store
   the defaults: settings from v2.1 are not carried over.

## 5. Calibrate each lane (once, with a tape loaded)

The positions are servo pulse widths in microseconds. 1 µs is about 0.01 mm at the pawl, so the forward end
can be set to a hundredth of a millimetre (v2.1 had whole degrees, 0.11 mm per step).

1. `M604 N<n> U1709` moves the pawl forward and `U1291` moves it back. If the slider moves the wrong way, the
   servo turns the other way on this unit. Mirror the values around 1500: `M603 N<n> A1291 B1490 C1709`.
2. Load a tape (section 6). Send `M600 N<n>` repeatedly and watch the pocket in the pick window with the down
   camera.
3. Adjust the forward end with `M603 N<n> A<us>` in steps of 5 to 10 µs until the pocket is centred.
4. Set the retract end C about 20 µs past the point where the tooth clicks into the next hole.
5. Set B so that a half stroke moves the tape 2.0 mm (for 2 mm tapes). The default is 1510.
6. Peel check: run 20 × `M600 N<n>`. The roller turns on every feed, the cover tape stays taut and clear of
   the pick window. There is nothing to set; the nip slips the surplus.
7. `M500` to save. Re-teach the pick location in OpenPnP (`OPENPNP.md`).

## 6. Load a tape

1. Take out the 2 cover plate screws, slide the plate 7 mm toward the pick end and lift it off.
2. Peel about 150 mm of cover tape back by hand. Push the carrier into the inlet at the rear, with the sprocket
   holes on the −Y side (the side plate side) and the pockets up, until it is under the pick window. The pawl
   and detent ramps let it pass.
3. Pass the free cover tape up through the peel slot of the plate from below. Lay the plate on, 7 mm short of
   the post, slide it home and fit the 2 screws.
4. Lead the cover tape up the riser in the post, over the guide bar and along the top of the servo. Push the
   tab of the pinch yoke down (about 3 mm), slide the cover tape between the rollers and let go. Lay the end into
   the waste bin.
5. Pull the cover tape rearward by hand until it is taut. It stays taut, because the pinch roller cannot turn
   back. Then send `M600 N<n>` twice; the first pocket is now at the pick window.

Empty the waste bin and the empty-tape box at every reel change.

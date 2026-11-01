# TBW-Feeder v2.1: manufacturing and assembly

Quantities are per lane unless marked "per bank". `out/bom.csv` has the full list with totals for 8 lanes. Run
`feeder build` first; it writes every file named below.

## 1. Make the parts

### Printed (STLs in `out/stl/`, already lying in print orientation)

| File | Qty | Material | Settings |
| --- | --- | --- | --- |
| `Body.stl` | 1 | PETG | 0.2 mm layers, 4 walls, 40 % gyroid, no supports |
| `Slider.stl` | 1 | PETG | 0.12 mm layers, 4 walls, 100 % infill, no supports, prints on its side. The flexure must be solid. |
| `Lifter.stl`, `HoldPawl.stl`, `Ratchet.stl` | 1 each | PETG | 0.12 mm layers, 100 % infill, no supports, flat on their side as exported. The pawl flexures must be solid, and the ratchet teeth sharp. |
| `RollerShaft.stl`, `PinchAxle.stl`, `SliderPeg.stl` | 1 each | PETG | 0.12 mm layers, 100 % infill. The pins print lying on their 0.3 mm flat, so the layers run along the pin. Never print them standing. |
| `PinchRoller.stl` | 1 | PETG | 0.12 mm layers, 100 % infill, flat |
| `CoverPlate.stl` | 1 | PETG | 0.12 mm layers, 100 % infill, upside down as exported (tabs up), no supports. Smooth bed side up = top of the plate. |
| `PinchYoke.stl`, `CheekCap.stl` | 1 each | PETG | 0.2 mm, 4 walls, 40 % (the cap's snap legs print solid at 0.85 mm) |
| `DriveRoller.stl` | 1 | TPU 95A | 0.2 mm, 100 % infill (Ø14, D-bore onto the ratchet hub) |
| `Feeder_ExitChute.stl` | 1 per bank | PETG | 0.2 mm, 3 walls, 30 %, prints standing on its end |
| `Feeder_WasteBin.stl`, `Feeder_WasteBinLeg.stl` | 1 + 2 per bank | PETG | 0.2 mm, 3 walls, 20 % |
| `ReelRack_Side.stl` | 2 per bank | PETG | 0.2 mm, 4 walls, 30 % |
| `ReelHub.stl` | 8 per bank | PETG | 0.2 mm, 3 walls, 30 % |
| `HornDrillJig.stl` | 1 (tool) | PETG | 0.2 mm, 100 % |

Check every printed body: the 8.2 mm tape channel passes an 8.0 mm gauge strip, the slider slides through the
tunnel from the rear without force, and the lifter slides through its channel beside the servo pocket.

### Laser cut (only for the steel fallback cover plate)

The printed cover plate is the default. Order the steel one only if the printed detent fails TEST B6.
`out/step/CoverPlate_flat.dxf`: 0.5 mm 1.4310 (X10CrNi18-8) spring-hard, C1300. Layer CUT is the contour, layer
BEND marks three 90° bends, all downward with inner radius 0.5 mm. The two rear tabs are 3.0 mm high, and the detent
tab is 1.1 mm high at the tip of the tongue. Deburr the peel slot edge at X 548: the cover tape folds over it.
`out/step/CoverPlate_steel.step` is the bent part, for checking. After bending, the tongue must lie flat with the plate
within 0.1 mm.

### Purchased

Per lane only: the SG90 servo with its horns, a 2 × 18 dowel (horn pin), the spring OD 5 × 0.4 × L0 9, and the
inserts and screws listed in the BOM. Everything else in the lane is printed, the cover plate included.
The guide rod is moulded into the body.

## 2. Prepare

1. **Inserts.** Use a soldering iron at 220 °C. Put M3 inserts in the 3 holes in the lane bottom, and M2 inserts in
   the 2 cover-plate holes and the 2 servo-ledge holes. Each insert finishes flush.
2. **Horn pin.** Put the single-arm horn on the jig (hub on the boss, arm in the groove) and drill Ø2.0 through the
   guide. Press the 2 × 18 dowel in from the arm's top face until 16.5 mm stands below the arm. Secure it with one
   drop of retaining compound.
3. **Centre the servo.** With the controller connected, send `M604 N<lane> S90`. Fit the horn so that the arm points
   along +Y (toward the open side of the lane, square to the tape) and the pin points down. Fit the horn screw.

## 3. Assemble one lane

The order follows the insertion paths that `feeder audit` checks.

1. **Slider.** Press the printed peg into the hole in the slider tail from the +Y side, flat toward the rear, until
   it stands 3.95 mm out of the −Y face. Lay the body on its side and slide the slider into the tunnel from the
   rear face: front end first, flexure upward, peg toward −Y (it runs in its own slot to the rear face). Push it in until its front
   is about 2 mm behind the pick window. It must slide freely over the full 4.2 mm stroke.
2. **Servo.** Hold the servo with its output down and the pin at 90°. Lower it into the pocket; the pin passes through
   the open slot on the +Y side and drops into the slider's ear slot. Fix the tabs with 2 × M2 × 6.
3. **Lifter.** Send `M604 N<lane> S109` so the slider is at its forward end. Drop the lifter into its channel on the
   −Y side of the servo, foot first with the pawl toward the rear, until the vertical entry at the foot slides over
   the peg. Step the servo to `S71` and back to `S109`: the lifter must go down 5.1 mm and back up without sticking.
4. **Hold pawl.** Press its peg into the square hole in the tower top behind the lifter, beam pointing forward.
5. **Ratchet and roller.** Press the TPU roller onto the ratchet hub (flat to flat) until it touches the ratchet.
   Put the pair between the cheeks, ratchet toward −Y, pressing both pawls aside. Press the printed axle (flat
   down) through the −Y cheek, the ratchet and the roller into the +Y cheek, flush on both faces. The roller must turn freely forward
   (top toward the rear) with two clicks per tooth, one from each pawl, and must not turn backward.
6. **Pinch yoke and cap.** Press the printed pinch axle through the yoke and the pinch roller from the +Y side.
   The roller must spin freely on it. Drop the yoke into the cheek grooves with the roller down. Put the spring in
   its seat, then press the cap down until both snap legs click into the notches on the outer cheek faces. Its
   front tab sits 1 mm over the lifter and keeps it in place. Lift the yoke by its rear tab: it should spring back
   onto the roller. To remove the cap, push the two legs outward with a thin screwdriver.
7. **Cover plate.** Check that the detent tongue moves freely in its slit (clear any stringing with a knife).
   Hook the rear tabs into their slots, lower the plate and fit 2 × M2 thumb screws.
8. **Cable.** Run the servo lead out at the rear and label it with the lane number.

## 4. Mount the bank

1. **Tooling plate.** Tap M3 into the six chute holes and the two waste-bin holes. The lane holes and the empty-tape
   slot are machined from the plate drawing (`../out/parts_step/Tooling_Plate.step`).
2. **Lanes.** Set each lane on the plate and fix it from below with 3 × M3 × 12. Lane 1 is at Y 150 and the pitch is
   22 mm.
3. **Exit chute.** Fix it with 6 × M3 × 20. Put a box at least 200 × 150 mm on the bench under the slot.
4. **Waste bin.** Stand the two legs behind the lanes and set the tray on top. Fix it with 2 × M3 × 55 through the
   tray floor, the legs and into the plate.
5. **Reel rack.** Fit the two side plates and the two M8 rods with the 8 hubs between them (flange toward +Y). Stand
   the rack on the bench with the axle 760 mm from the machine origin X (about 150 mm behind the plate end).
6. **Controller.** Wire it as in `ELECTRONICS.md`, flash it, then send `M502` and `M500` to store the defaults.

## 5. Calibrate each lane (once, with a tape loaded)

1. `M604 N<n> S109` – the pawl goes forward. `M604 N<n> S71` – it goes back. If the slider moves the wrong way,
   the servo turns the other way on this unit: swap A and C below (A 71, C 109).
2. Load a tape (section 6). Send `M600 N<n>` repeatedly and watch the pocket in the pick window with the down
   camera.
3. Adjust the forward angle with `M603 N<n> A<deg>` until each feed stops with the pocket centred and the detent
   tab clicks into its hole without the tape moving back on the next retract. Set the retract angle C so that the
   tooth drops into the next hole: you hear a click and the tape doesn't move. Set B halfway between them for 2 mm
   tapes.
4. Peel check: run 20 × `M600 N<n>`. The ratchet clicks twice per feed and the cover tape stays taut. Nothing to
   set; the nip slips the surplus.
5. `M500` to save. Re-teach the pick location in OpenPnP (`OPENPNP.md`).

## 6. Load a tape

1. Undo the two thumb screws and swing the cover plate up.
2. Peel about 150 mm of cover tape back by hand. Push the carrier into the inlet at the rear with the sprocket holes
   on the −Y side (the side away from the pin slot) and the pockets up, until it is under the pick window. The pawl
   and detent ramps let it slide in.
3. Pass the free cover tape up through the peel slot from below, fold it back over the plate, and close and screw
   down the plate.
4. Lead the cover tape up the tower front groove, over the guide rod and along the top of the servo. Lift the pinch
   yoke by its tab, slide the cover tape under the bearing, and let the yoke drop. Lay the end into the waste bin.
5. Pull the end of the cover tape rearward by hand until it is taut (the roller can only turn forward).
   `M600 N<n>` twice; the first pocket is then at the pick window.

Empty the waste bin and the empty-tape box at every reel change.

# TBW-Feeder v2.1: design notes

All numbers come from `../model/feeder.py` and are checked by `feeder audit` (`out/audit.md`). Heights are
measured from the tooling plate top. X runs along the tape: the tape moves toward −X and the pick is at the inner
end. Y is measured from the lane centre line.

## Why v2.0 replaces v1.0

v1.0 couldn't be built. Its SG90 and lane PCB sat in the tape path: the carrier tape passed straight through the
servo case. The horn pin also hit the end of the yoke slot, the slider was trapped in a closed channel, and the
side walls were 0.1 mm thick. The peel unit wasn't attached to anything. An SG90 is 12 mm wide and 23 mm tall. At a
22 mm lane pitch with the tape 16 mm above the plate, it fits neither beside the tape nor under it. v2.0 therefore
hangs the servo above the tape and reaches under the tape with a pin.

## Why v2.1 drops the N20

v2.0 peeled with a second motor per lane (N20 gearmotor, worm, wheel, clip, ULN2003 channel). v2.1 takes the peel
from the servo stroke that already advances the tape, through a lifter and a ratchet. Per lane that removes the N20,
the worm set, the clip, a set screw, a screw, an insert and a driver channel, and the firmware no longer waits for a
peel time. In return the lane gets three printed parts (lifter, ratchet, hold pawl) and a printed peg, and the
servo works harder (still 3.9× under stall).

v2.1 also prints everything that doesn't need steel. The guide rod is moulded into the body. The roller axle, the
pinch roller (it replaces the 683ZZ), the pinch axle and the slider peg are printed. The cheek cap snaps on instead
of using 2 screws, and the cover plate is printed too (below). Bought per lane: the SG90 with its horn, the Ø2 horn
pin, the pinch spring, 4 M2 inserts + 4 M2 screws and 3 M3 inserts + 3 M3 screws. These stay bought on purpose:

- **Horn pin:** a printed Ø2 pin under the 7 N push would see about 140 MPa, three times what PETG takes.
- **Pinch spring:** it is always loaded; a plastic spring would creep and the nip would lose its slip force.

## Layout (one lane, 127 × 20.5 × 72 mm)

| Zone | X (frame) | Height | Contents |
| --- | --- | --- | --- |
| Low section | 526–592 | ≤ 17.5 | Tape channel, cover plate with pick window, peel slot and detent tongue, slider tunnel under the tape |
| Tower front | 592–599 | ≤ 55.5 | Cover-tape riser groove, Ø3 guide bar moulded into the post |
| Servo | 600–633 | ≤ 48 | SG90 hanging upside down; horn chamber and pin passage below it; lifter channel on its −Y side |
| Peel head | 632–653 | ≤ 72 | Cheeks, Ø14 drive roller + ratchet on a fixed printed axle, hold pawl, pinch yoke, snap-on cap |

The head reaches X 567 at most, and the machine interference check (`pnp check`) passes with all 8 lanes. The low
section is the same height as v1.0.

## Tape path

- Channel 8.2 × 1.2 mm (paper carriers up to 1.1 mm, embossed carriers 0.2–0.4 mm). A relief groove 4.0 × 2.5 mm
  sits under the pockets for embossed tape.
- Pick pocket at X 540 (`params.PICK_X`), Y lane + 1.25. Sprocket holes are at Y −2.25, with a hole centre at
  X 542 (EIA-481 P2 = 2.0).
- Empty tape leaves the lane at X 526. A printed chute bends it down (R 11) through a slot in the tooling plate
  (X 508–522), and it falls beside the right tie to a bin on the bench.
- Reels (7") sit on a free-standing rack behind the machine (axle at X 760, 95 mm above the bench). The tape leaves
  the top of the reel and enters the flared inlet at X 653.

## Advance mechanism

- SG90, upside down, with its output axis at X 611. A single-arm horn carries a Ø2 × 18 dowel pin at R 6.5,
  drilled with the jig (`stl/HornDrillJig.stl`).
- The pin runs beside the tape (Y 5.2–7.5) down into the yoke slot of the slider. The slider runs in a closed
  tunnel under the tape (floor 5 mm, roof at 12.6 mm). It goes in from the rear face, and its rib passes up through
  the hole-row slot.
- Scotch yoke: stroke 4.2 mm = 2 × 6.5 × sin 18.85°. Servo angles: forward 108.9°, half 90.9°, retract 71.1°
  (the firmware defaults are 109 / 91 / 71, calibrated per lane).
- Pawl: a printed PETG flexure, 14 × 2.6 × 0.9 mm, anchored at its +X end so that the push load drives the tooth
  deeper. The tooth is 0.8 mm wide with a vertical hook face, a 0.3 mm flat and a 45° ramp. At the tape underside
  it is 1.05 mm long, so it fits a Ø1.5 hole at both stroke ends (checked: no overlap at forward or retract).
- Feed per stroke is exactly 4.0 mm. The 0.2 mm of free travel only changes where the tooth starts. The pick
  position is set by the servo's forward angle, which the firmware holds. A half stroke gives 2.0 mm, so 2 mm-pitch
  tapes need no extra pick logic.
- Cover plate: printed PETG, 1.2 mm (`COVER_PLATE = "printed"` in `model/feeder.py`). It is the channel roof,
  carries the pick window and the peel slot, and its top is 17.5 mm above the plate, still under the 20 mm the head
  already clears over the nozzle magazine, so Safe Z doesn't change.
- Detent: a tongue 16 × 3 × 1.2 mm printed into the cover plate, inside a 0.6 mm slit. It's anchored at +X with a
  1.0 × 0.9 mm tab at the −X tip that drops into the hole two holes upstream of the pawl. The tab's −X face is
  vertical and blocks back-drag (play 0.15 mm). When the tape moves forward it pushes the tab below the tongue's
  axis, which bends the tongue up and lifts the tab out, as on the steel plate; a 0.18 mm chamfer helps.
  The tab reaches 15.2 mm, which also catches 0.3 mm embossed carriers.
- Fallback: the v2.0 steel plate (0.5 mm 1.4310, 18.4 × 2 mm tongue, ≈ 1.6 N) is still exported
  (`out/step/CoverPlate_flat.dxf`, `CoverPlate_steel.step`). Use it if the printed detent fails TEST B6; both fit the
  same body. Set `COVER_PLATE = "steel"` to model it.

| Load case | Value | Limit / margin |
| --- | --- | --- |
| Flexure spring force (0.75 mm lift) | 0.26 N | Enough to snap the tooth into a hole |
| Flexure strain | 0.52 % | PETG fatigue ≈ 0.8 % |
| Detent tongue force, printed (0.8 mm lift on paper tape) | ≈ 0.5 N | steel fallback ≈ 1.6 N |
| Detent tongue strain, printed | ≈ 0.56 % | PETG fatigue ≈ 0.8 % |
| Servo torque to push the tape | 0.016 N m | SG90 stall 0.18 N m (11×) |
| Servo positioning error (0.5° dead band at the stroke end) | ≈ 0.05 mm | Vision corrects the first pick |

## Peel mechanism

- Path of the cover tape: the peel slot in the plate (X 546–548) → back over the plate → up the tower front
  groove → over the Ø3 guide bar (top at 54.5) → horizontal above the servo → nip on top of the drive roller
  (X 638) → rearward into the waste bin.
- Drive, from the servo:
  - A printed Ø3 peg pressed into the slider tail (X 624.5 at the forward end, 9.5 mm up) sticks out 4 mm on the
    −Y side into the foot of the **lifter**. It prints lying, so the layers run along it (bending stress about
    9 MPa at the worst-case peel load). The lifter is a flat printed plate in a channel beside the servo
    (Y −8.3…−6.1), free to move only up and down.
  - The peg runs in an inclined slot (50.4°, rise 1.21 mm per mm of slider travel), so the lifter rises 5.08 mm
    on the feed stroke and is pulled back down on the retract. No spring. A vertical entry at the bottom of the slot
    lets the lifter drop over the peg during assembly; the cheek cap stops it 1 mm above its highest pose, so it
    can't climb out of the slot.
  - At its top a flexure finger (0.8 × 5.8 × 18.6 mm, hanging from a bridge) carries a pawl tooth that pushes the
    teeth of an 18-tooth **ratchet** (Ø12, root Ø10.8) upward on its front side. The ratchet hub runs on a
    stationary printed Ø3 × 20 axle, and the TPU 95A drive roller (Ø14 × 6) sits on the hub with a D-flat.
  - Over the full stroke the pawl tip travels 54.8° around the axle, so it always advances exactly 2 teeth (40°):
    4.89 mm of roller surface per 4 mm of tape, 22 % surplus. It is 14.8° past the 2nd tooth and 5.2° short of
    the 3rd, so a few degrees of servo calibration don't change the count.
  - In 2 mm mode two half strokes share the same 2 teeth (about 1.5 mm and 3.4 mm of roller). The nip slips the
    small lag of the first one.
  - A printed **hold pawl** under the ratchet (0.8 mm beam, 9.9 mm free, loaded in compression) stops the ratchet
    turning back, so the cover tape stays taut between feeds, as the self-locking worm did in v2.0.
- Nip: a printed Ø7 pinch roller on a printed axle, in a printed yoke that slides in grooves in the cheeks
  (the roller turns 4.9 mm per feed, so a plain PETG bearing is enough), pressed down by a spring
  (OD 5 × 0.4 wire × L0 9, ≈ 0.75 N/mm, compressed 2 mm → 1.5 N). At μ ≈ 0.8 (TPU) the nip slips at about 1.2 N.
  That limits the peel tension (EIA-481 peel force is 0.1–1.3 N) without any sensor.
- The peel happens during the feed stroke, while the tape moves, so it adds no time. The pawl first travels 14.8°
  before it meets a tooth (about the first quarter of the stroke); the nip slips back the small amount of cover
  tape released in that time.

| Peel load case | Value | Limit / margin |
| --- | --- | --- |
| Ratchet face force at nip slip (1.2 N at R 7) | 1.5 N | — |
| Extra slider force from the lifter slot (μ 0.3) | 4.2 N | — |
| Servo torque, tape + peel | 0.046 N m | SG90 stall 0.18 N m (3.9×) |
| Lifter pawl finger, ride-over 1.2 mm | 0.42 % strain | PETG fatigue ≈ 0.8 % |
| Hold pawl beam, ride-over 0.55 mm | 0.67 % strain | PETG fatigue ≈ 0.8 % |
| Hold pawl beam buckling | 8.2 N | 5.6× the 1.5 N load |

## Fastening and assembly

- The lane bolts to the tooling plate from below with 3 × M3 into heat-set inserts in the lane bottom. A lane comes
  off without touching its neighbours.
- Cover plate: two rear tabs hook into slots so the plate swings up for tape loading, and two M2 knurled thumb
  screws hold the front.
- Servo: 2 × M2 into inserts in the tab ledge. Lifter and hold pawl: drop in from the top (the hold pawl's peg is
  a press fit in the tower top). Pinch yoke: drops in from the top, held by a snap-on cap that also stops the
  lifter. Its two 0.85 mm legs sit in pockets in the cheek outer faces (flush, so lanes still fit at 22 mm) and their
  lips catch a notch; snapping on bends them 0.6 mm (1.2 % strain, a one-time snap).
- The audit checks every insertion path: slider + peg +X, servo with horn at 90° +Z, lifter +Z (servo at the
  forward end), hold pawl +Z, ratchet + roller +Z (the pawls flex aside), shafts ±Y, yoke +Z, cover plate +Z.

## Electronics and firmware

There's one controller per bank: an Arduino Nano on an IO shield and a 5 V 4 A supply, with no custom PCB and no
motor drivers. See `ELECTRONICS.md`. The firmware is in `firmware/tbw_feeder_fw` (G-code over USB, settings in
EEPROM) and compiles for the Nano: 6.3 kB flash, 377 B RAM.

## Known limits

- Only 8 mm tape with 4 mm sprocket pitch. Part pitch can be 2 or 4 mm, or any multiple of 2 up to 24 mm.
- Feed time is about 0.55 s per 4 mm (3 servo moves with the default settle time of 180 ms per move). It can be
  tuned down per lane.
- The peel can't be run on its own: slack after loading a tape is taken up by pulling the cover tape by hand (the
  roller turns forward only).
- The SG90 dimensions are catalogue typicals. Before printing a batch, check the delivered parts against the
  pockets (`TEST.md`, first article).
- The animation and the audit draw the flexures rigid; their ride-over is checked by strain, not by geometry.

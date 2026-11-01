# TBW-Feeder v3.0: design notes

All numbers come from `../model/feeder.py` and are checked by `feeder audit` (`out/audit.md`). Heights are
measured from the tooling plate top. X runs along the tape: the tape moves toward −X and the pick is at the inner
end. Y is measured from the lane centre line.

## Why v3.0: what the v2.1 first article showed

| Problem on the v2.1 lane | Cause in the v2.1 design |
| --- | --- |
| Weak feed that's hard to adjust; the tape slips | The pawl was a 0.9 mm PETG flexure with 0.26 N of spring force, so the tooth lifted out of the hole under load. The servo positions were whole degrees, 0.11 mm steps at the pawl. |
| The "gear" slips or doesn't move | The peel ratchet was Ø12 with 18 teeth only 0.6 mm deep, driven by a 0.8 mm flexure finger. Even with a 0.25 mm nozzle the teeth print rounded. |
| The springs don't hold | Every spring was printed PETG (pawl, lifter finger, hold pawl, detent tongue), and PETG creeps. |
| The cover latch doesn't hold firmly | The cover plate was held only at its ends (2 M2 thumb screws and 2 hinge tabs 58 mm apart), so it bowed over the pawl. The cheek cap snapped on with 0.85 mm legs. |
| Printing took long, and the supports were hard to remove | One body full of closed tunnels and chambers needed supports inside. The fine features forced a 0.25 mm nozzle: 10.0 h per lane, 8.3 h of it the body. |

The servo-driven swing feed stays: one SG90 per lane, the same controller and the same wiring. The mechanism
around it is new.

## TRIZ analysis

Ideal final result: *the tape itself holds the pawl in the hole, the cover tape stays taut by itself, and the
lane prints without supports in one material.* Each contradiction below was resolved with existing resources
(the push load, the servo stroke, the cover tape tension, standard bought parts) instead of with extra parts.

| # | Contradiction | Principles | v3.0 solution |
| --- | --- | --- | --- |
| 1 | Physical: the pawl must be **stiff** to push the tape and **compliant** to ride back under it | 1 Segmentation, 40 Composite, 25 Self-service | Rigid printed lever with a separate steel spring on an M2 set screw pivot. The pivot is 5.9 mm below and behind the tooth, so the push load turns the tooth deeper into the hole (self-locking) against a positive up-stop. The spring only has to seat the tooth: 1.25–1.57 N, 5× v2.1. |
| 2 | The detent needs the same function as the pawl in the other direction | 6 Universality, 33 Homogeneity | It is the same part, pivot screw and spring as the feed pawl, mounted in the body. Same self-locking geometry, play 0.15 mm. |
| 3 | Technical: a reliable one-way peel drive (27) against manufacturability (32): fine ratchet teeth can't be printed. Then: a second moving member (the lifter) against simplicity (36) | 2 Taking out, 14 Curvature, 5 Merging, 6 Universality | The one-way function moves out of the printed parts into a bought HF0612 needle clutch. The rack sits on the slider, which already moves: a 36T idler passes the motion to the 14T pinion on the roller shaft and sets the direction. There is no second moving member. Teeth are 2.25 mm deep instead of 0.6. |
| 4 | Hold the cover tape taut between feeds without a hold pawl | 5 Merging, 25 Self-service | A second HF0612 goes in the pinch roller that already exists. It can't turn back, so the nip holds the cover tape on the retract. |
| 5 | Limit the peel tension without a sensor | 11 Beforehand cushioning | Kept from v2.1: the sprung nip (now on NBR O-rings) slips at 1.2 N and takes the 20 % surplus. |
| 6 | Physical: the cover plate must be **fixed** firmly and **free** for tape loading without tools | 1 Segmentation, 15 Dynamics, 28 Mechanics substitution | Segmented rails: 3 lips per side and 2 rear tongues hold the plate down every 14 mm. Slide it 6.8 mm toward the pick (bayonet) and lift it off. Two countersunk M2 screws through its upstand into the tower lock it home instead of snaps or magnets. Deflection over the pawl drops from 2.2 mm to 0.03 mm. |
| 7 | Technical: manufacturability (32, no supports, larger nozzle) against device complexity (36, tunnels and pockets) | 1 Segmentation, 17 Another dimension, 7 Nested doll, 2 Taking out | The body is split into a main body and a side plate. Every pocket opens to the split face, so both halves print flat on their outer faces and all moving parts are laid in from one side. Shafts, axles and the guide bar are printed PETG; the drive shaft is printed in one piece with the pinion (5 Merging). |
| 8 | A few features still face down in print | 3 Local quality, 4 Asymmetry | A 45° chamfer goes only on the one edge that faces down. The strip beside the pawl slot and the riser wall belong to the side plate, where they print standing up. Bridging layers sit in the counterbores. |
| 9 | Fine pick adjustment (accuracy, 29) without extra hardware (36) | 35 Parameter change, 23 Feedback | Servo positions are in microseconds instead of degrees: 0.01 mm per step instead of 0.11. Calibrated with the down camera. |

Result: there are 13 printed parts per lane (11 different), all PETG, none needing supports on a 0.4 mm
nozzle. Every spring and axle is steel, and every one-way function is a bought needle clutch.

## Layout (one lane, 127 × 20.5 × 68 mm)

| Zone | X (frame) | Height | Contents |
| --- | --- | --- | --- |
| Low section | 526–592 | ≤ 16.3 (lips 18.3) | Tape channel, cover plate on segmented rails, detent under the hole row, slider tunnel under the tape |
| Tower front | 592–600 | ≤ 52 | Post: cover tape riser, printed Ø2.9 guide bar, 2 M2 pilot holes for the cover plate screws, slots for the rear tongues of the plate |
| Servo | 600–633 | ≤ 48.2 | SG90 hanging upside down, tabs captured in a slot between the halves |
| Peel head | 612–652 | ≤ 67 | Drive roller (O-rings) over the pinch roller. On the −Y side: take-up rack on the slider, 36T idler beside the servo, 14T pinion on the roller shaft |

The body is split at y = −4.85 into a **main body** (prints on its +Y face) and a **side plate** (prints on its
−Y face), held together by 4 M3 screws into inserts. All moving parts lie in pockets that open to the split
face. The lane mounting holes and the tooling plate are the same as for v2.1. The rail lips are 18.3 mm high,
still under the 20 mm the head clears, and the parts above 20 mm are beyond X 588, which the head never reaches
(`pnp check`).

## Tape path

- Channel 8.2 × 1.2 mm (paper carriers up to 1.1 mm, embossed 0.2–0.4 mm). A relief groove 4.0 × 2.1 mm
  sits under the pockets for embossed tape (2.4 mm pockets clear). Its sprocket-side edge has a 45° chamfer.
- The slider tunnel roof (11.8) ties the sprocket-side tape floor to the main body. In v2.1 that strip was held
  only by the solid side wall, which is now the side plate.
- Pick pocket at X 540, Y lane + 1.25. Sprocket holes at Y −2.25, with a hole centre at X 542.
- Empty tape leaves at X 526 through the chute. Reels stand on the rack behind the machine.

## Advance mechanism

- Servo upside down (MG90S, SG90 size), output axis at X 611. The model includes the round boss around the
  output gear (Ø11.8 × 4 mm under the case face) and the spline (Ø4.8 × 2.8). The case face is at 27.1 mm, and the
  servo top at 49.8 mm, under the cover tape path. SG90/MG90S drawings: body 22.2–22.8 × 11.8–12.2 mm, tab span
  32.2–32.5, tab top 18.5 above the base, 28.4–28.5 high without the horn. Check the delivered servo (TEST A7).
- A printed **servo gear**, a 13T m1 sector (teeth only within ±55° of the rack side, the rest is hub, so it clears
  the idler), replaces horn, crank and pin. It is pressed onto the spline (the metal spline cuts its teeth into
  the bore) and held by the servo's screw from below.
- It drives a **rack moulded on the slider**: an arm rises beside the tape on two short necks, and its teeth face
  the gear at Y + 6.5. The stroke is 4.2 mm = 37° of servo rotation, linear in the angle (the scotch yoke was
  not), so 1 µs ≈ 0.01 mm everywhere in the stroke. The slider prints standing on its bottom, so the rack teeth
  lie in the print plane.
- Feed pawl: a rigid 2 mm PETG lever on an M2 × 5 set screw (pivot, threaded into the slider walls) in the slider
  fork. A steel spring (OD 3 × 0.3 × L0 8,
  installed 5.5 mm) presses it up. The tooth is 0.8 mm wide (flush with the face it prints on), with a vertical
  hook face 0.75 mm into the tape, a 0.3 mm flat and a 45° ramp. At the tape underside it is 1.05 mm long, so
  it fits a hole at both stroke ends with 0.2 mm free travel.
- Self-locking: the tooth contact is 5.9 mm above the pivot, behind the tooth. The push load therefore turns the
  tooth deeper, against the up-stop (the tail on the fork floor). It can't climb out under load. Riding back
  under the tape it turns 5.8° down (checked for clearance in the audit).
- Detent: the same pawl, in a housing in the body at the hole next to the pick pocket. Its hook face sits 0.15
  mm behind the hole edge and blocks back-drag. The tape pushes it down over its ramp on the feed stroke.
- Feed per stroke is 4.0 mm, and a half stroke gives 2.0 mm. Positions are in µs: forward 1709, half 1510,
  retract 1291 (108.9 / 90.9 / 71.1°), calibrated per lane in steps of about 0.01 mm.

| Load case | Value | Limit / margin |
| --- | --- | --- |
| Pawl spring, seated / riding over | 1.25 / 1.57 N | v2.1 flexure 0.26 N |
| Tape push (detent ramp + friction + reel drag) | 3.8 N | — |
| Servo torque, tape only (gear R 6.5) | 0.024 N m | Stall 0.18 N m (7×) |
| Pawl tooth root bending (prints lying, in-plane) | 10.7 MPa | PETG ≈ 45 MPa |
| Servo positioning resolution | 1 µs ≈ 0.01 mm | v2.1: 1° ≈ 0.11 mm |

## Peel mechanism (gears + one-way bearings)

- Path of the cover tape: peel slot in the plate (X 546–548), back over the plate, up the riser in the post,
  over the printed Ø2.9 guide bar, horizontally above the servo at 50.9 mm, into the nip **under** the drive roller,
  and out rearward over the waste bin lip.
- Drive:
  - A printed **rack** (m1, teeth up, pitch line 16.8 mm) is fixed to the slider tail with two M2 × 6 screws.
    It moves with the slider, 4.2 mm per stroke, with no extra member and no cam.
  - The rack turns a 36T m1 **idler** (Ø36, axis at X 631.7 / Z 34.8). Its Ø5 axle stub is printed on and runs
    in a hole through the side plate. It bridges the 42 mm up to the roller shaft.
  - The idler turns a 14T m1 **pinion**, printed in one piece with its Ø6 drive shaft (no press fit to slip).
    The shaft runs in the body at +Y; its −Y end runs on a Ø2.9 journal pin printed on the side plate.
  - Rack → idler → pinion is one gear more than rack → pinion, which gives the right winding direction (the nip
    pulls the cover tape rearward on the feed stroke). The idler's size doesn't change the ratio.
  - The shaft is the inner race of an HF0612 needle clutch in the **drive roller** (PETG body, two NBR O-rings
    12 × 1.5, Ø16). The clutch drives the roller on the feed stroke and freewheels on the retract.
  - Per full stroke the roller surface moves 4.2 × 8 / 7 = 4.8 mm per 4 mm of tape (20 % surplus). A half
    stroke gives 2.4 mm per 2 mm, so every 2 mm feed now peels its own share.
- Hold on the idle (return) stroke: the rack goes back and turns the idler, pinion and shaft back. The drive roller's
  HF0612 freewheels, so the roller isn't taken back. The **pinch roller** is the same roller body (O-rings) on
  a second HF0612, on a fixed printed Ø6 × 14 axle pressed into the single yoke arm (+Y side, the idler is on −Y), and
  it can't turn back. With the cover tape
  clamped between the two rollers at 1.5 N, the drive roller and the cover tape stand still: the nip holds
  1.2 N, the same as the most it can pull, so nothing slips back. The carrier tape is held by the detent at
  the same time.
- Nip: a steel spring (OD 5 × 0.4 × L0 9, installed 7 mm) pushes the yoke up: 1.5 N. On NBR (μ ≈ 0.8) the nip
  slips at 1.2 N, which limits the peel tension (EIA-481 peel force 0.1–1.3 N). To thread the cover tape, push
  the yoke tab down 3 mm.

| Peel load case | Value | Limit / margin |
| --- | --- | --- |
| Rack force at nip slip (1.2 N at R 8 / R 7) | 1.4 N | — |
| Slider force for the peel (two spur meshes) | 1.5 N | v3.0 lifter slot: 3.1 N |
| Servo torque, tape + peel | 0.036 N m | Stall 0.18 N m (5×) |
| Rack / idler / pinion tooth bending (Lewis, face 1.8) | 2.8 MPa | PETG fatigue ≈ 10 MPa |
| Pinion on its shaft | one printed part | no press fit |
| HF0612 torque | 9.6 N mm | Rated ≈ 1.8 N m |
| Cover tape tension held on the idle stroke | 1.2 N | = nip slip tension |

## Cover plate

- Printed PETG 1.2 mm, tape side down. It has the pick window (8 × 5.2), the peel slot, rail tongues at both
  edges (3 segments per side), 2 rear tongues into the post, and an upstand at the rear with 2 countersunk holes: 2 × M2 × 8
  countersunk screws (DIN 965) go through it along X into the tower.
- To load tape: take out the 2 screws, slide it 6.8 mm toward the pick and lift it off. At home it can't lift (checked in the audit).
- Deflection under the pawl spring, rails every 14 mm: 0.03 mm. With the v2.1 supports (58 mm apart) the same
  load would bow it 2.2 mm.
- Hold: the screws are a positive lock (≈ 40 N pull-out each, self-tapped into PETG) against 0.9 N of tape
  drag on the feed stroke.

## Manufacturing

Per lane there are 15 printed parts (Body, SidePlate, CoverPlate, Slider, 2 × Pawl, Rack, Idler, Pinion with
its shaft, 2 × roller body, PinchYoke, PinchAxle, GuideBar, ServoGear), all PETG on one 0.4 mm nozzle at 0.20 mm layers. The audit checks each one
in its print orientation:
- longest bridge ≤ 10 mm
- no flat ceiling that hangs from one side by more than 1 mm
- no overhang steeper than 45°
- walls ≥ 0.8 mm

Print time and filament, sliced by OrcaSlicer on the AD5M profile (`print_time.py`):

| Version | Nozzle / layers | Supports | Body (+ side plate) | Small parts | Per lane | 8 lanes |
| --- | --- | --- | --- | --- | --- | --- |
| v2.1, as printed | 0.25 / 0.12 | tree, in the body | 498 min | 103 min | **10.0 h, 56 g** | 80 h |
| v2.1 on a 0.4 nozzle (reference only: its 0.6 mm ratchet teeth don't print at 0.4) | 0.4 / 0.2 (0.12 small parts) | tree | 147 min | 38 min | 3.1 h, 62 g | 25 h |
| **v3.0** | **0.4 / 0.2** | **none** | 134 min (incl. side plate, yoke) | 25 min | **2.7 h, 66 g** | **22 h** |

v3.0 prints 3.7× faster than v2.1 as printed. It also needs no support removal, and nothing inside the tunnels
has to be cleaned out.

Bought per lane: the SG90 and the following standard parts (`ASSEMBLY.md`):
- 2 HF0612 one-way bearings
- 4 O-rings
- 3 springs
- 6 M3 inserts, 6 M3 screws, 2 M2 set screws, 2 M2 screws and 2 M2 countersunk screws (plus the servo's own
  screw)

Every shaft and axle is printed (or a screw): no steel pins, no magnets, no TPU, no laser-cut plate.

## Electronics and firmware

One controller per bank: an Arduino Nano on an IO shield with a 5 V 4 A supply, servos only (`ELECTRONICS.md`).
Firmware 3.0.0 (`firmware/tbw_feeder_fw`) stores the positions in µs (EEPROM layout 3) and compiles for the Nano:
6.4 kB flash, 401 B RAM.

## Known limits

- 8 mm tape with 4 mm sprocket pitch only. Part pitch 2 or 4 mm, or any multiple of 2 up to 24 mm.
- Feed time is about 0.55 s per 4 mm (3 servo moves, 180 ms settle each); it can be tuned down per lane.
- The HF0612 is made to run on a hardened shaft (HRC 58+). On the printed PETG shafts the needles lock on a
  softer surface: the clutch can slip or wear the shaft. Print the pinion shaft and the pinch axle solid
  (100 % infill) and check them in `TEST.md` A10. If they wear, the drop-in fix is a hardened Ø6 dowel
  (6 × 20 for the shaft, then the pinion needs its old Ø6 bore; 6 × 14 for the pinch axle).
- Over the rack (X 619–643, under the servo, 80 mm from the pick) the tape channel has no −Y wall above the
  tape floor, so the side plate can pass the rack. The tape can move 0.85 mm sideways there. It is guided
  everywhere else.
- The servo dimensions are SG90/MG90S catalogue typicals. Check the delivered parts (`TEST.md` A7).
- The audit draws the springs at their installed length. The pawl ride-over is checked by rotating the pawl,
  and the spring forces by calculation.

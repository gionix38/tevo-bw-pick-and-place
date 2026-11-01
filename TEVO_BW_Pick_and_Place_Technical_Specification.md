# Technical Specification

> **Implementation status:** This is the original rev 1.1 work specification, not a fully synchronized as-built
> manual. The current CAD has since changed several decisions, especially the Z/C head and feeder architecture.
> Before fabrication, read [`pnp/BUILD_AND_ASSEMBLY.md`](pnp/BUILD_AND_ASSEMBLY.md), the current generated
> [`pnp/out/report.md`](pnp/out/report.md), and the feeder's [`ASSEMBLY.md`](pnp/feeder/ASSEMBLY.md). Where this
> document conflicts with the current model, treat it as historical intent and verify dimensions against the
> actual printer. A controlled rev 2 specification is still needed.

## Conversion of the Tevo Black Widow into a Single-Head SMT Pick-and-Place Machine

| Field | Value |
| --- | --- |
| Document | TEVO-BW-PNP-TS-001 |
| Revision | 1.1 |
| Date | 2026-10-16 |
| Language | English |
| Machine baseline | Tevo Black Widow, OpenBuilds V-slot Cartesian, stock envelope about 370 × 250 × 300 mm |
| Project files | Frame and plate models in `Tevo Black Widow 3d printer - 1933864/`, modular X mother plate in `TEVO BW/Tevo Black Widow - Modular X Carriage - 1829292/` |

This document is the build specification and the implementation plan. Requirements use **shall**. Work packages in section 12 are the build instructions.

Revision 1.1 reorients the frame with its own members. The two vertical C-Beam Z columns become the horizontal X rails. The existing belt-driven X beam becomes the Y bridge. The Z leadscrews are removed and do not drive X.

---

## 1. Purpose

Convert the printer mechanism into a desktop placer for surface-mount components. The placement head is a fast XY carriage with a vacuum tweezer, a nozzle changer, a positioning camera, and a bank of tape holders. The existing controller board, stepper drivers, power supply, endstops, and wiring stay in service. New electronics are limited to the vacuum circuit, camera lighting, and any I/O the installed board does not already provide.

The machine places passive and small active parts from 8 mm carrier tape onto a bare PCB: 0603, 0805, 1206, SOT-23, SOD-123, and SOIC up to 8–16 pins. 0402 is a stretch goal after vision calibration. Fine-pitch QFP, BGA, and parts heavier than about 2 g are outside this revision.

## 2. Scope

### 2.1 In scope

- Kinematic conversion to a light, belt-driven XY carriage.
- Placement head: short Z stroke, nozzle rotation, spring compliance, vacuum tweezer.
- Passive nozzle magazine (the tool changer).
- Down-looking positioning camera on the head, plus one fixed up-looking camera so a picked part can be oriented before placement.
- Mechanical holders for 8 mm EIA-481 tapes, advanced by the head.
- PCB fixture on a fixed table.
- I/O map onto the existing board, firmware changes, and OpenPnP setup.
- Acceptance tests.

### 2.2 Out of scope

- Replacing the motion controller, power supply, or stepper drivers.
- Solder paste dispensing and reflow. Paste is applied outside this machine, or by a later dispenser tool.
- Motorized commercial feeders. The tape holders are head-actuated. A motorized feeder bus is a later option and must not require a new motion board.
- Automatic optical inspection after reflow.
- Enclosure HVAC and production-line safety certification. Section 10 covers workshop safety for this build.

### 2.3 Definitions

| Term | Meaning |
| --- | --- |
| Carriage | The moving XY head. It carries Z, rotation, the vacuum nozzle, and the down-looking camera. |
| Vacuum tweezer | Spring-loaded nozzle on a vacuum line. It picks a part from a tape pocket and releases it on the pad. |
| Tool | One nozzle tip. Tips differ by orifice and outer diameter. |
| Tool changer | A fixed magazine. The head drops the current tip and picks up another. No extra motor. |
| Positioning camera | The down-looking camera on the carriage. It finds PCB fiducials and tape pockets. |
| Up-looking camera | A fixed camera under the travel path. The part flies over it so OpenPnP can correct X, Y, and angle. |
| Tape holder | A lane that locates an 8 mm tape, peels or holds the cover tape, and advances one pocket when the head presses a lever. |
| Existing electronics | The board, drivers, PSU, and harness already on this machine. Stock Black Widow class is an MKS Gen-class board running Marlin. The installed board is confirmed in WP0 and may differ. |

## 3. Assets that stay

| Asset | Use in the placer |
| --- | --- |
| Two C-Beam Z columns, 40×80, assembly length 574 mm in the project model | Laid horizontal. These are the X rails. |
| 40×80×550 mm X beam, X motor plate, belt tension plate, X carriage | Y bridge. The beam spans the two C-beams. Carriage travel along the beam is Y. |
| 20×80×500 mm member | Fixed tie that holds the C-beams parallel. A second tie comes from the retired bed extrusion if the frame has only one. |
| Two 20×80×210 mm members | Legs. Their length does not span the gap between the C-beams. |
| X carriage body and the modular mother plate (`LP_MotherPlate` pattern: plate bolted to the OpenBuilds X carriage, daughter plates swapped with M3 hardware) | Head mounting plate on the Y beam. Hotend daughter plates are removed. |
| NEMA 17 now on the X beam | Y motor. It stays on that beam. |
| NEMA 17 now on the bed (stock Y) | X motor, driving both C-beam belts through a jackshaft. |
| NEMA 17 now on Z | Head Z motor. |
| Endstop switches | Home X, Y, and head Z. |
| Controller, drivers, 12 V or 24 V PSU, display | Motion and valves. Heater outputs are reassigned. |
| Z leadscrews, Delrin nut blocks, Z couplers | Removed in WP1. Not an axis drive. |
| Bed axis extrusion (Y-axis assembly, about 571 mm in the model) and heated bed plate | Bed motion is removed. The plate becomes the tooling plate only if it is flat within 0.05 mm over the PCB area. Otherwise it is replaced. The extrusion is a spare tie. |
| Bowden or direct-drive extruder, hotend, part cooling, bed heater, thermistors | Removed from the motion path and disconnected. |
| Electronics box, drag-chain brackets | Kept. The chain is re-terminated on the moving bridge. |

Sizes above are bounding sizes from `Tevo Black Widow assembly.step`. WP0 measures the machine and replaces them where they differ. Stock travels are about X 370 mm, Y 250 mm, Z 300 mm. After the reorientation the useful envelope is about 400 mm along the C-beams (X) and about 320–350 mm along the 550 mm beam (Y), before the camera, magazine, and tape bank take their edge space.

## 4. Selected architecture

The carriage moves in X and in Y. The PCB and the tapes stay still. The frame is rebuilt from its own extrusions: stock Z structure becomes X, stock X structure becomes Y.

1. Both C-Beam columns are unbolted from the vertical Z position and laid horizontal, parallel, as the X rails. The Z leadscrews and Delrin nuts come off. A leadscrew cannot meet PR-1.
2. The 550 mm X beam spans the two C-beams and is the moving bridge. Travel of that bridge along the C-beams is machine X.
3. The belt, motor plate, tension plate, and carriage that already live on the 550 mm beam stay there. Travel of that carriage along the beam is machine Y.
4. X is driven by two GT2 belts, one on each C-beam, turned by one motor through a jackshaft so the bridge cannot yaw. The motor is the former bed motor.
5. Y is the existing single GT2 belt on the 550 mm beam.
6. Both X and Y run on MGN12H linear rails bolted to those extrusions. Stock V-wheels may hold the bridge only while the rails are aligned, then they come off.
7. The fixed table sits in the rectangle between the C-beams, on the 20×80 ties. The 210 mm profiles are the legs. Bed motion is removed.
8. Pick and place strokes are a 35 mm Z axis on the head, driven by the former Z motor. The bridge has no vertical axis.
9. The nozzle rotates on its own axis (machine axis C, wired as Marlin axis A).
10. Vacuum is a diaphragm pump, a pick valve, a short blow-off pulse, and a vacuum switch.
11. Nozzle tips are Juki-compatible (CP40 / 500 series pattern) and live in a 6-pocket passive magazine.
12. The down-looking camera is bolted to the carriage at a fixed offset from the nozzle.
13. The up-looking camera is bolted to the table on the path between the tape bank and the PCB.
14. Tape holders sit along the front of the table, outside the PCB clamp zone. Each lane advances when the nozzle presses its lever.
15. A host PC runs OpenPnP, talks G-code to the existing board over USB, and captures both cameras over USB.

Coordinate system, right-handed, origin at the front-left home of the carriage:

- +X along the C-beams, from the home end toward the far end. Home is the left end when the operator faces the tape bank.
- +Y along the 550 mm beam, from the front tape bank toward the rear of the table.
- +Z up, nozzle descending toward the board as Z decreases.
- +C counterclockwise when looking down on the nozzle. Zero is the flat of a two-pin part parallel to X.

Every later offset (camera, magazine, feeders, fiducials) is stored in this frame.

## 5. Functional requirements

### 5.1 Carriage

- FR-1. The carriage shall move in X and Y with the PCB and the tape holders stationary.
- FR-2. X and Y shall be GT2 belt driven, 2 mm pitch, closed loop in the mechanical sense (tensioned belt, no spring compliance in the drive path).
- FR-3. X and Y shall home against limit switches. Homing direction is toward the switches. The firmware shall back off and re-approach at no more than 10 mm/s.
- FR-4. Moving mass of the carriage, including Z motor, C motor, nozzle, camera, and bracket, shall be at most 500 g.
- FR-5. The drag chain shall carry vacuum tube, camera USB, valve wires, and motor cables without tugging the carriage inside the work envelope.

### 5.2 Vacuum tweezer

- FR-6. The nozzle shall pick a part by vacuum and release it with a timed positive pressure pulse of 5–20 ms.
- FR-7. The nozzle shall have 1.0–1.5 mm of spring compliance so a slightly low Z command does not crush a part.
- FR-8. A vacuum sensor shall report “part present” after a pick and “part released” after a place. OpenPnP shall abort the place if the pick check fails.
- FR-9. The nozzle stem shall be interchangeable without tools beyond the magazine cycle. Stem runout at the tip shall be within 0.03 mm.
- FR-10. The vacuum pump shall remain on during a job. The pick valve shall open only for the pick-and-carry interval.

### 5.3 Head Z and rotation

- FR-11. Head Z travel shall be at least 35 mm, enough to clear the tallest nozzle in the magazine and the tallest tape cover.
- FR-12. Z shall be driven by a leadscrew or ball screw of 2 mm lead or finer, on a linear guide, with the nozzle axis parallel to Z within 0.05 mm over the stroke.
- FR-13. Axis C shall rotate the nozzle continuously through more than 360° and hold any commanded angle.
- FR-14. C and Z shall be coaxial: rotating C shall not shift the tip by more than 0.03 mm in X or Y.

### 5.4 Tool changer

- FR-15. The magazine shall hold 6 nozzle tips in known machine coordinates.
- FR-16. A change shall be a sequence of moves only: descend, twist to release, rise, move, descend, twist to engage, rise. No magazine actuator.
- FR-17. Each pocket shall reject a wrong engagement. A failed seat shall be detectable by a Z stall, a pocket switch, or a vacuum leak check before the next pick.
- FR-18. OpenPnP shall be the only authority for which tip is loaded. The operator shall be able to read the loaded tip name on the OpenPnP UI.

### 5.5 Positioning camera

- FR-19. The down-looking camera shall see PCB fiducials and tape pockets in the same machine coordinates as the nozzle, through a stored nozzle-to-camera offset.
- FR-20. The camera shall be global shutter, USB, with a lockable M12 lens focused at the PCB surface.
- FR-21. A light on the carriage shall illuminate the field of view. The light shall be switchable from the controller so it is off while the machine is idle.
- FR-22. The up-looking camera shall image the bottom of a part hovering at a fixed height. OpenPnP shall apply the measured X, Y, and angle error before the place move.
- FR-23. Both cameras shall be rigid. Focus, aperture, and mounting screws shall be thread-locked after calibration.

### 5.6 Tape holders

- FR-24. The bank shall provide at least 8 lanes of 8 mm tape. Lane pitch shall allow the lever of lane N to be pressed without striking lane N+1.
- FR-25. Each lane shall locate the tape by its sprocket holes, 4 mm pitch, per EIA-481.
- FR-26. Each lane shall advance exactly one pocket per head press, for part pitches of 2 mm and 4 mm. 2 mm pitch is two presses or a lever set to half index; the build record shall state which.
- FR-27. Cover tape shall be peeled back and held so the pocket is open at the pick point and the cover does not rise into the nozzle path.
- FR-28. The pick point of every lane shall be a single OpenPnP feeder coordinate, re-found by the positioning camera when a tape is changed.

### 5.7 Worktable and PCB

- FR-29. The PCB shall be clamped flat on a fixed plate. Datum is two pins or two edges against hard stops, plus a clamp.
- FR-30. Board thickness from 0.8 mm to 1.6 mm shall be supported. A change of thickness is a Z offset in OpenPnP, not a mechanical rebuild.
- FR-31. The plate shall be electrically idle. Heater power shall be disconnected and the heater MOSFET output reused or capped.

### 5.8 Existing electronics

- FR-32. The installed motion board shall generate steps for X, Y, Z, and C.
- FR-33. Two switched outputs shall drive the pick valve and the blow valve. A third output shall drive the camera light. The bed-heater and hotend-heater channels are the first candidates.
- FR-34. One digital input shall read the vacuum sensor.
- FR-35. Heaters, thermistors, and the extruder motor shall be removed from the configuration so a fault cannot turn them on.
- FR-36. Any shortfall in drivers or inputs shall be filled by a small add-on module on the existing supply. The motion board itself is not replaced under this specification.

## 6. Performance requirements

Targets apply after WP10, with the rails installed, at 20–25 °C, on the reoriented frame.

| ID | Metric | Requirement |
| --- | --- | --- |
| PR-1 | XY travel speed | At least 400 mm/s in the clear area between feeders and board |
| PR-2 | XY acceleration | At least 3000 mm/s² on X (the bridge) and 4000 mm/s² on Y (the light carriage) |
| PR-3 | Head Z speed | At least 60 mm/s |
| PR-4 | C speed | 360° in under 150 ms for a 90° index |
| PR-5 | Pick check | Vacuum decides pass/fail within 30 ms of the pick dwell |
| PR-6 | Nozzle change | Complete 6-tip cycle under 8 s each way, including moves from the board center |
| PR-7 | Fiducial repeatability | Down-looking camera returns the same fiducial within 0.03 mm over 20 measurements |
| PR-8 | Placement, 0603 and larger | At least 95% of 50 parts inside 0.10 mm of pad center and inside 2° of pad angle, after up-looking correction |
| PR-9 | Placement, 0402 | Goal: 90% inside 0.08 mm. Failure does not fail the machine; it is recorded |
| PR-10 | Cycle rate | At least 800 parts per hour on a demo board with one nozzle and parts from at least 4 lanes, vision on |
| PR-11 | Lost-part rate | Under 2% picks aborted by the vacuum check on fresh tape |
| PR-12 | Homing repeatability | Nozzle returns to a dial indicator within 0.03 mm after 10 home cycles |

Stock marketing figures (XY 0.012 mm, Z 0.004 mm) are not acceptance criteria. PR-7, PR-8, and PR-12 are.

## 7. Mechanical design

### 7.1 Frame and X axis

The two C-beams are the X rails. The 550 mm beam is the bridge that travels on them. Square the rectangle before any rail is drilled.

- Remove both leadscrews, Delrin nut blocks, and couplers before the C-beams are laid down. Bag them with the lead written on the bag (measure it: turns of the nut over 20 mm of screw). A TR8×8 screw at a realistic NEMA 17 speed stays near 30–60 mm/s, which fails PR-1, so the screw is not refitted on X.
- Lay the C-beams horizontal and parallel. Set the gap so the 550 mm beam and its end plates bolt on as they do between the Z columns today. The model gap is inside a machine width of about 580 mm.
- Tie the beams with the 20×80×500 member. Add a second tie from the retired bed extrusion so the rectangle has two crossmembers. Stand the frame on the two 20×80×210 members as legs.
- Diagonals of the rectangle equal within 0.5 mm. Top faces of the two C-beams coplanar within 0.05 mm.
- Mount one MGN12H rail on each C-beam, reference edges facing the same way. Tighten from the center outward.
- Two blocks per rail carry a bridge plate. Bolt the 550 mm beam to those plates. Tram the beam: a pointer at the future nozzle changes height by no more than 0.05 mm from X minimum to X maximum.
- X drive is one NEMA 17, the former bed motor, and a jackshaft across the two C-beam ends. The shaft carries two 20-tooth GT2 pulleys, one aligned to each beam. Each beam has its own 9 mm GT2 loop, an idler at the far end, and the belt ends clamped to that side’s bridge plate. Both belts are the same length and the same tooth phase.
- If a shaft cannot span the gap, use two matched NEMA 17 motors, one at each C-beam, wired in series on the single X driver. Pulleys still match tooth for tooth. Series wiring keeps the driver current equal to one motor. Parallel wiring is not used.
- X home switch is on the bridge at the left end.
- Both belt runs get a cover. Leave at least 10 mm of unused rail at each end so the blocks never hit the rail screws.
- Yaw check: move X through 200 mm and read a dial indicator on the bridge plate at the far C-beam. Drift above 0.05 mm means the two belts are out of phase or unequal in length. Correct that before any placement test.

### 7.2 Y axis

Y is the belt axis already built on the 550 mm beam. The beam now lies across the C-beams, so this travel runs from the tape bank toward the rear.

- Remove V-wheels, hotend, extruder, and any plate that exists only to carry them.
- Bolt one MGN12H rail to the face of the beam. The modular mother plate bolts to two MGN12H blocks. The nozzle axis is the hole on the plate centerline, drilled if the stock plate has none.
- Keep the X motor plate, the tension plate, and the GT2 belt. Use a 20-tooth pulley. Tension so the belt is one span and the carriage has no dead band when pushed 0.1 mm and released.
- The motor on this beam is the Y motor. Plug it into the board’s Y driver (section 8.1).
- Y home switch is at the front end of the beam, on the tape-bank side.
- Leave at least 10 mm of unused rail at each end.

### 7.3 Head

Build the head as a stack on the mother plate. Keep it inside the 500 g budget. A practical stack, top to bottom:

1. Z motor, NEMA 17, on a printed or aluminum cage.
2. Z screw, TR8×2 (2 mm lead) with a spring-loaded anti-backlash nut, or a 2 mm lead ball screw if one is on hand. Travel 40 mm, soft stops at 2 mm and 38 mm.
3. Z carriage on an MGN9 or MGN12 short rail. This carriage holds the rotation assembly.
4. C motor, NEMA 11 or NEMA 14, driving the nozzle shaft by a 20-tooth / 20-tooth GT2 loop or by spur gears of equal count. Ratio 1:1 keeps the steps-per-degree integer. Use a closed belt, not an open one.
5. Nozzle shaft, 6 mm ground rod or a hollow stainless tube, in two bearings. The shaft is the vacuum path if hollow. If the shaft is solid, a side port and a flexible PU tube enter above the lower bearing through a swivel that does not twist the tube more than ±180° during a normal job. A hard stop on C at ±180° from zero is acceptable if jobs are planned inside that range; continuous rotation through a pneumatic slip ring is the upgrade when a job needs it.
6. Compliance spring between the shaft and the nozzle holder, preload about 1 N, stroke 1.0–1.5 mm. The holder is a Juki-style collet: the tip snaps in on a 1/4 turn or on the clutch geometry of the chosen tip family. Buy the tips and the holder as a set. Do not invent a collet that does not match a commercial tip.
7. Down-looking camera bracket on the mother plate, not on the Z carriage, so the camera stays in focus when Z moves. Nozzle-to-camera offset is constant in X and Y.

Z home is a switch at the top of the stroke. The nozzle then travels down by increasing negative Z, or the firmware uses a tool offset so the operator commands Z = 0 at the PCB surface. Pick one convention in WP9 and keep it:

- Machine Z zero is the home switch.
- OpenPnP “part height zero” is the top of the PCB, stored as a camera and nozzle Z offset.

Cable the Z and C motors in the drag chain. Vacuum tube is 4 mm OD PU, one continuous run from the valve block on the frame to the swivel. A tube that piggybacks on the Z carriage must have a service loop so Z can move 40 mm without lifting the nozzle.

### 7.4 Vacuum circuit

Mount the pump and valves on the frame, not on the carriage.

- Diaphragm pump, same supply voltage as the board (confirm 12 V or 24 V in WP0), free-air flow enough to reach −60 kPa in the nozzle line in under 100 ms with the valve open.
- Pick valve: 2-way normally closed, between pump and nozzle. Energized = vacuum at the nozzle.
- Blow valve: 3-way or a separate normally closed valve from a regulated 10–30 kPa puff into the nozzle line, for the release pulse. A simple arrangement that works: pick valve NC to vacuum, blow valve NC to a tee, and a small orifice leak so the line decays when both are off. Document the plumbing in the build record with a one-line diagram.
- Sensor: a vacuum switch set to about −40 kPa, or an analog sensor read by a spare thermistor input scaled in firmware. A digital switch is enough for FR-8.
- Inline filter, 10 µm, between nozzle and valves, so a dropped chip does not enter the pump.
- Muffler on the pump exhaust.

Nozzle set for the first articles:

| Tip | Typical parts |
| --- | --- |
| 0.4–0.5 mm | 0603, small SOT |
| 0.7–0.8 mm | 0805, 1206, SOT-23 |
| 1.0–1.2 mm | SOD, tantalum A/B, SOIC |
| 1.5–2.0 mm | Larger SOIC, inductors under 2 g |
| Spare | Second 0.7 mm, the size that wears first |
| Plug | Solid tip used only to prove the magazine |

### 7.5 Tool changer magazine

- Aluminum or thick printed bar, bolted to the table at the left or right end, outside the PCB clamps and outside the tape bank.
- Six pockets on a straight line parallel to X, so a change is mostly one-axis motion.
- Pocket pitch at least 18 mm so the camera bracket clears the neighboring tip.
- Each pocket holds the tip the way the commercial holder releases it: for a twist-lock family, the pocket grips the tip collar and the head rotates C by the unlock angle (often 90°) while Z is at the engage height.
- Z engage height is the same for every pocket. A stepped pocket is a defect.
- Add a small leaf spring or magnet so a parked tip cannot bounce out when the machine homes.
- Engrave or mark pocket index 1 through 6 on the bar. OpenPnP nozzle tip names match those marks.
- Teach procedure is in WP6. The magazine origin is the center of pocket 1 at engage height.

### 7.6 Positioning camera

Down-looking camera:

- Global-shutter USB board camera, 720p or better. Rolling shutter is rejected because the carriage images on the move during setup and the blur is direction-dependent.
- M12 lens, focal length chosen so the field of view on the PCB is about 15–25 mm across. That is wide enough for a fiducial search and narrow enough that one pixel is under 0.03 mm. Compute it: FOV mm / pixel count = mm per pixel. Record the number after calibration; the calculation only sizes the lens.
- Working distance fixed by a slotted bracket. Set focus on a fiducial, then glue the focus ring.
- Light: a ring or two LED bars around the lens, diffuse, white or red. Red reduces glare on ENIG and HASL. The light is a MOSFET load, not a USB-powered always-on LED.
- Mount so the nozzle, at Z safe, is outside the field of view. The stored offset is the only link between camera center and nozzle center.

Up-looking camera:

- Same camera family, lens aimed up through a hole in the table or from a bracket at the front edge.
- Diffuse backlight or a low-angle ring so the part outline is a dark silhouette. A silhouette is more repeatable than a top light for angle measurement.
- Fixed hover height: nozzle tip 3–5 mm above the lens cover, recorded as the up-camera Z.
- Place the camera so the Y move from the tape bank to the board passes over it. The detour shall be under 80 mm.

### 7.7 Tape holders

One lane is a module. Eight modules bolt to a front rail.

Each module:

- Body locates a 8 mm tape width within 0.2 mm.
- Sprocket wheel, tooth pitch 4.0 mm, engages the tape holes. A 12-tooth or 16-tooth wheel is easy to print and to check with a pin: 4.0 mm chord between adjacent teeth.
- Ratchet so the wheel moves only in the feed direction.
- Lever on the top of the module. The nozzle comes down on the lever pad, travels 3–4 mm, and the sprocket advances one pitch. A hard stop limits the press so a low Z command cannot break the lever.
- Cover-tape peel: a fixed blade and a spring finger that fold the cover back over a take-up pin. The operator pulls the cover onto the pin when loading. The pick pocket is the first open pocket past the blade.
- Pick clearance: at the pick Z, the nozzle body clears the module walls by at least 1 mm.

Lane pitch 20–24 mm. Number the lanes 1–8 from left to right. Leave a 30 mm gap between the last lane and the magazine if they share a side.

Loading a lane is an operator procedure, written on a card at the machine:

1. Lift the cover finger.
2. Seat the tape, sprocket holes on the teeth, parts facing up.
3. Close the finger and peel 3 pockets onto the take-up pin.
4. In OpenPnP, select the feeder and run “vision home” so the positioning camera centers that pocket.

Head motion for one feed, before the pick: move to the lever XY, Z down to the press height, Z up, move to the pick pocket, Z down to pick, vacuum on, dwell, Z up, vacuum check.

### 7.8 PCB fixture

- Tooling plate, aluminum, at least 6 mm thick, bolted to the frame on three points so it can be trammed. Target: 0.05 mm flatness over a 200 × 150 mm board area.
- Two hardened pins, 3 mm, in a line parallel to X, as the board’s rear or front datum. A slide clamp opposite the pins pushes the board against them.
- A third point, a spring plunger or a screw stop, sets the X datum.
- Record pin coordinates in the machine frame. OpenPnP board location uses those datums plus the fiducials.
- Do not rely on the old bed clips.

## 8. Electronics

WP0 writes the actual connector list. The map below is the assignment for an MKS Gen-class board, which is the stock Black Widow controller. If the installed board is a later 32-bit board, keep the same signal names and move them to the matching pins.

### 8.1 Axis map

| Signal | Driver socket | Motor and mechanism |
| --- | --- | --- |
| X | board X | Former bed motor, jackshaft, both C-beam belts. Series pair if WP2 uses two motors |
| Y | board Y | Motor that is already on the 550 mm beam |
| Z | board Z | Former Z motor, head screw |
| A (extruder E0 driver) | existing E0 | Nozzle rotation C |
| E1 | left unplugged | Do not assign a feeder motor in this revision |

Rewire by the machine axis, not by the old printer label. The motor on the 550 mm beam moves to the Y socket. The bed motor moves to the X socket.

Steps per mm, starting values to correct by measurement in WP9:

- X and Y, 20-tooth pulley, 2 mm pitch: 80 steps/mm at 16 microsteps and 200 full steps. Formula: `(200 × microsteps) / (teeth × 2)`.
- Z, TR8×2, 16 microsteps: `(200 × 16) / 2 = 1600` steps/mm.
- C, 1:1, 16 microsteps: `(200 × 16) / 360 = 8.888…` steps/degree. Prefer 8 microsteps if the driver allows a cleaner number, and record the value used.

Set motor currents for the load, not for the old heated-bed era. X and Y lose the bed and the extruder mass, so current comes down until the motor is warm, not hot, after 20 minutes of PR-2 moves. C is a small motor; set its current at the driver pot or digipot before the first powered move.

### 8.2 Outputs and inputs

| Function | First-choice pin | Notes |
| --- | --- | --- |
| Pick valve | former hotend MOSFET | 12/24 V, flyback diode at the valve |
| Blow valve | former fan MOSFET | same |
| Camera light | former part-fan MOSFET | same |
| Bed heater | capped, connector removed | FR-31 |
| Vacuum switch | a spare endstop or probe input | active low, internal pull-up |
| X, Y, Z home | existing endstops | NC switches preferred so a broken wire homes into the stop instead of crashing |

Pump power is a manual switch on the supply, fused. The pump is not on a firmware MOSFET, so a locked-up board cannot leave a valve clicking with the pump off and cannot cycle the pump every pick. Valves do the per-pick work.

### 8.3 Firmware behavior

- Marlin (or the firmware already on the board) with four axes, `DISTINCT_E_AXES` unused, A axis enabled as a rotational axis if the firmware supports degrees. If it only supports linear E, command C in degrees by setting steps per mm equal to steps per degree and sending millimeters that mean degrees. Document the convention in the OpenPnP driver.
- Disable `PREHEAT`, bed PID, and thermal protection for the removed heaters so the board boots with no thermistor attached.
- Accelerations: start at 1500 mm/s², raise toward PR-2 only after the belts stay tracked.
- Jerk or junction deviation low enough that a full tape does not walk in its holder. Start at 8 mm/s junction speed.
- Add two M-codes or fan numbers for the valves, and use them from OpenPnP actuator G-code. Example pattern, final pins from WP0: pick on `M42 P<pin> S255`, pick off `M42 P<pin> S0`, blow as a short script `M42 … S255` / `G4 P10` / `M42 … S0`.
- Vacuum check: either a firmware macro that sets a pin OpenPnP can read, or OpenPnP reads the endstop state over `M119`. Choose `M119` unless WP0 shows the board cannot report that pin.

### 8.4 Host

- PC next to the machine, USB to the board, USB to both cameras.
- OpenPnP current stable release.
- 5 V camera current comes from the PC, not from the motion board.

## 9. Software configuration

OpenPnP objects to create, in this order, after the axes move correctly by hand-jog:

1. Driver: G-code driver to the board’s serial port. Motion command `G1 X Y Z A F`. Confirm the letter used for C.
2. Head: one head, nozzle on it, vacuum actuator, blow actuator.
3. Nozzle tip library: the six tips, with diameter and the pick/place Z offsets measured in WP6.
4. Cameras: down-looking units-per-pixel from a calibration square; up-looking the same way with a known pin.
5. Nozzle-to-camera offset: commanded move that puts a fiducial under the nozzle, then under the camera. The difference is the offset.
6. Axis C on the nozzle, with the unlock angle used by the magazine.
7. ReferenceNozzleTipChanger or the equivalent actuator, one drop location and one pick location per pocket.
8. Feeders: one ReferencePushPullFeeder or script feeder per lane. Vision calibration enabled.
9. Bottom vision pipeline on the up-looking camera, one pipeline per package outline (rectangle for chips, rectangle with leads for SOT and SOIC).
10. A test job: four fiducials optional, a 10 × 5 grid of 0603 or 0805, four feeders.

Homing script order: Z up first, then X and Y. A job start homes Z, X, Y, then moves to the up-looking camera and checks that the light works.

## 10. Safety

- Disconnect the bed heater at the PSU and remove the connector before any other rewire. A placer job must have no path that can heat the table.
- E-stop cuts motor power and both valve coils. The pump switch is next to it. After an E-stop the nozzle stays where it is; the operator lifts Z by hand if a part is under it. Do not home until the carriage is clear.
- Belt pinch points on both X loops and on the Y belt get a printed cover.
- Vacuum pump exhaust points away from the operator.
- Nozzle tips are small and sharp enough to pierce skin if a hand is under the head during a jog. Jog Z downward only from the up-looking camera view or from a measured height.
- Laser or super-bright LED ring: choose a diffuse LED. Do not use a focusable laser module as the camera light.
- The frame ground stays bonded to the PSU earth.

## 11. Acceptance

The machine is accepted when every row below is signed in the build record.

| Test | Setup | Pass |
| --- | --- | --- |
| T1 Homes | Cold start | X, Y, Z home without contact other than the switches. Repeat 10 times, PR-12 |
| T2 Square | Dial indicator or camera on a straight edge | X motion changes Y by under 0.05 mm over 200 mm. Y motion changes X by under 0.05 mm over 150 mm |
| T3 Speed | OpenPnP jog script | PR-1 and PR-2 held for 5 minutes, belts stay on pulleys, carriage stays under 500 g on a kitchen scale check done once in WP4 |
| T4 Vacuum | 20 picks of 0805 from lane 1 into a cup | PR-5 and PR-11 |
| T5 Changer | 10 cycles through all 6 tips | PR-6, every tip seated, vacuum leak check passes on the open tip |
| T6 Fiducials | One fiducial, 20 finds | PR-7 |
| T7 Up-camera | 20 parts of one 0805 reel, reported angle | Standard deviation under 0.5° on a square part after pipeline tuning |
| T8 Place | 50 parts, at least 0603 and SOT-23, on a scrap PCB with paste or on tacky flux | PR-8, checked under a microscope or by the down-looking camera against pad centers |
| T9 Rate | The T8 job timed | PR-10 on a longer run of 100 parts, or the T8 time scaled only if no faults occurred |
| T10 Power-off heaters | Thermistor channels and bed MOSFET inspected | No heater wired, board boots without thermal error |

A failed row returns to the work package named in the fault note. Acceptance is the set of rows, not a single demo video.

## 12. Implementation plan

Do the work packages in order. WP4 and WP5 can be built on the bench in parallel with WP2 and WP3, and mounted only after the bridge homes. Do not skip WP0.

Each package lists the actions in the order to perform them.

### WP0 — Survey the machine you have

Objective: a one-page baseline so later steps use measured numbers.

1. Photograph the frame from the front, the X carriage, the electronics box with the cover off, and the PSU label.
2. Record supply voltage, board name and revision, driver chips, and which connectors are occupied. This replaces the MKS assumption everywhere it differs.
3. Measure both C-beams, the 550 mm beam, the 500 mm tie, and the 210 mm legs. Write down the gap between the two C-beams while they are still the Z columns. That gap is the bridge span to reproduce.
4. Measure the leadscrew lead (nut travel for one motor turn) and bag the screws. Record how many Z motors and bed motors actually turn.
5. Weigh the current X carriage with a scale. The difference from 500 g is the mass budget for the new head.
6. List working motors (wire count, NEMA size) and working endstops.
7. Decide and write down: pump voltage, valve voltage, and whether the drag chain already reaches a moving gantry or only a moving bed. A bed chain must be re-terminated on the bridge.
8. Quarantine the hotend, extruder, bed power wires, and thermistors in a labeled bag. They are out of the build.

Done when: a single note contains voltage, board identity, travels, carriage mass, and the connector map, and the heater wires are off the machine.

### WP1 — Reorient the frame and fix the table

Objective: both C-beams horizontal, the 550 mm beam spanning them, a trammed plate, no bed motion.

1. Remove the bed belt and the bed heater leads (already isolated in WP0). Keep the bed motor for the X jackshaft.
2. Remove both leadscrews, Delrin nuts, and couplers. Confirm they match the bag from WP0.
3. Unbolt the two C-beams and lay them horizontal at the gap recorded in WP0. Bolt the 550 mm beam across them with its existing end plates, still without the new rails.
4. Fit the 20×80×500 tie and a second tie from the bed extrusion. Fit the 210 mm profiles as legs. Equalize the diagonals within 0.5 mm.
5. Strip or replace the bed plate per section 7.8. Bolt it to the ties on three adjustable screws, inside the rectangle.
6. Put a dial indicator on a temporary arm on the 550 mm beam. Sweep along both beams. Shim the plate screws and the ties until the central 200 × 150 mm is within 0.05 mm.
7. Mark the PCB datum corner. Drill and ream two pin holes and one clamp slot. Fit the pins and the clamp from section 7.8.
8. Confirm a bare 100 × 80 mm PCB sits without rock. If it rocks, spot the plate. Do not shim the PCB with tape.

Done when: the C-beams do not shift when the bridge is pushed by hand, a PCB seats against the pins, and the indicator sweep meets 0.05 mm.

### WP2 — X belts on the two C-beams

Objective: the bridge travels along the C-beams on rails, both belts in phase.

1. Mount both MGN12H rails as in section 7.1. Move the 550 mm beam from its temporary end plates onto the rail blocks.
2. Tram again. Twist shows up as a height change along the beam at two X positions. Shim the bridge plates.
3. Fit the jackshaft, two 20-tooth pulleys, two idlers, and two belts. Anchor each belt on its own bridge plate. Mark one tooth on each pulley that meets the belt at the same shaft angle.
4. Fit the X home switch at the left end. Confirm continuity unpowered, then `M119`.
5. Plug the bed motor into the X driver. Set steps/mm from section 8.1. Command a 100 mm move against a steel rule. Correct steps/mm by `current × (commanded / measured)`.
6. Read yaw at the far bridge plate over 200 mm. Above 0.05 mm, re-phase the belts before raising speed.
7. Raise acceleration only after 100 mm moves are within 0.1 mm. Stop at 3000 mm/s² or at the first skipped step, whichever is lower, and record it.
8. Fit both belt covers.

Done when: X homes, a 200 mm move repeats within 0.05 mm, yaw stays within 0.05 mm, and the beam height stays inside 0.05 mm.

### WP3 — Y carriage on the 550 mm beam

Objective: the light carriage on a rail along the bridge, belt driven, ready for the head.

1. Remove V-wheels and the extruder stack from the carriage on the 550 mm beam.
2. Mount the MGN12H rail on the beam. Mount the mother plate on two blocks. The nozzle hole is the plate centerline.
3. Refit the belt and the motor that belongs on this beam. Set tension as in section 7.2. Plug that motor into the Y driver.
4. Fit the Y home switch at the front end. Confirm with `M119`.
5. Calibrate Y steps/mm the same way as X.
6. Run a 150 mm move at 100 mm/s, then 200, then 400. At each speed, listen for pulley skip and watch the belt walk off the pulley flange. Flange contact means the pulley is skewed. Shim the motor plate before raising speed.
7. Install the drag chain from the frame to the mother plate. Leave a loop at full X and full Y. Nothing in the chain may go tight at the corners of travel.

Done when: X and Y home and interpolate a rectangle (command a 150 × 100 mm box) whose diagonal closes within 0.1 mm at the indicator, at 400 mm/s.

### WP4 — Head, Z, and rotation

Objective: coaxial Z and C on the carriage, within the mass budget.

Build this on the bench before it goes on the rail.

1. Assemble the Z rail, screw, anti-backlash nut, and NEMA 17. One motor revolution shall move the carriage 2.0 mm ±0.05 mm on a rule.
2. Couple the nozzle shaft through two bearings on the Z carriage. Spin the shaft by hand. A dial indicator on the future tip shall read under 0.03 mm total runout. If it reads more, the bearings are not coaxial; fix the printed bores or switch that part to aluminum.
3. Add the compliance spring and the commercial nozzle holder. Fit one tip. Press the tip on a scale: it shall start moving at about 1 N and bottom at 1.0–1.5 mm.
4. Mount the C motor and the 1:1 belt. Command 90°, 180°, 360° with the driver on the bench. The tip angle shall match a protractor within 1° before OpenPnP backlash compensation, and the indicator runout shall stay under 0.03 mm while it turns (FR-14).
5. Fit the Z home switch at the top.
6. Weigh the finished head. If it is over 500 g, move the C motor up, shorten the bracket, or change NEMA 17 Z for NEMA 14 before installing it. Do not accept the overrun.
7. Bolt the head to the mother plate. The nozzle axis is vertical when the carriage sits on the rail: check with a small square against the table.
8. Connect Z as the board’s Z driver and C as E0. Home Z upward only, by hand-jogging the first time with a finger on the power switch.
9. Set Z = 0 at the PCB surface using the convention in section 7.3. A feeler of 0.1 mm between tip and PCB, with the compliance just starting to move, is the place height for a 0 mm part. Record it.
10. Set acceleration on Z low (500 mm/s²) until the screw stays quiet, then raise it toward PR-3.

Done when: the nozzle touches a PCB, lifts 20 mm, rotates 90°, and returns to the same touch point within 0.05 mm, and the head mass is recorded under 500 g.

### WP5 — Vacuum tweezer

Objective: pick and release with a sensor check.

1. Mount the pump, filter, pick valve, and blow valve on the rear frame. Wire the pump through its own fused switch.
2. Plumb 4 mm PU tube: pump, filter, pick valve, tee, blow valve, carriage loop, swivel, nozzle. Leak-check with soapy water or by pinching the nozzle: the sensor shall reach its trip point.
3. Wire pick and blow to the MOSFET outputs from WP0, with a diode across each coil.
4. Wire the vacuum switch to the spare input. `M119` shall change when the nozzle is sealed with a finger.
5. Tune the blow pulse. Start at 10 ms. An 0805 shall leave the tip and fall, and shall not be blown sideways off a pad. If it sticks, add 5 ms. If it scatters, subtract 5 ms or lower the puff pressure.
6. In OpenPnP, write the pick actuator (valve on), the place actuator (blow script), and the pick-check that reads `M119`.
7. Pick 20 parts from a tape held in a vise, drop them in a cup. A missed sensor trip fails the test even if the part is on the nozzle.

Done when: T4 passes on the bench, and the blow time is written in the build record.

### WP6 — Tool changer

Objective: six tips, exchanged by motion only.

1. Buy the tip family before cutting the magazine. The pocket is a copy of the holder’s release geometry.
2. Machine or print the six-pocket bar. Bolt it to the table. Indicate the pocket centers: they shall lie on a line parallel to X within 0.1 mm, and at one height within 0.05 mm.
3. Jog the nozzle, with tip 1 loaded, into pocket 1. Lower Z until the clutch is at the release height. Record X, Y, Z.
4. Command the C unlock angle. Lift Z. The tip shall stay in the pocket.
5. Move to pocket 2, lower, command the lock angle, lift. Pull upward gently on the head: the tip shall come along. A tip that stays in the pocket is under-rotated or high.
6. Repeat for all pockets. Store the six coordinate triples in OpenPnP.
7. Add the seat check: after a pick-up, open the pick valve for 50 ms with the tip uncovered. A seated tip seals enough to trip the sensor or, on an open orifice, shows a stable vacuum different from a missing tip. Record both sensor states and use the missing-tip state as the failure.
8. Run 10 full exchanges.

Done when: T5 passes.

### WP7 — Positioning camera and up-looking camera

Objective: fiducials and part angle in machine units.

1. Mount the down-looking camera on the mother plate. Set the lens to a 15–25 mm field at the PCB. Lock the lens.
2. Wire the light to its MOSFET. `M42` shall turn it on and off.
3. In OpenPnP, set the camera resolution and run the units-per-pixel calibration on a scale or a known grid.
4. Find a fiducial with the camera. Jog the nozzle onto that fiducial. The jog delta is the nozzle-to-camera offset. Enter it and repeat from the other side of the board. The two results shall agree within 0.05 mm; average them.
5. Mount the up-looking camera on the fly path. Build the silhouette light.
6. Hover a known 0805 at the hover Z. Tune the bottom-vision pipeline until the reported center is stable to one pixel and the angle is stable to 0.5°.
7. Run a loop: pick, fly over the up camera, place on a marked cross, 20 times. Measure the scatter. This is the first look at PR-8, before the formal acceptance.

Done when: T6 and T7 pass.

### WP8 — Tape holders

Objective: eight lanes the head can index.

1. Print or machine one lane. Check sprocket pitch with a 4.00 mm pin gauge or a stack of feeler checks: eight pitches shall be 32.0 mm ±0.2 mm.
2. Load a scrap 8 mm tape. Press the lever with the nozzle at the design stroke. Exactly one pocket shall advance. If it advances two, shorten the lever arm. If it advances none, lengthen the stroke or the arm.
3. Cycle 50 presses. The pick pocket shall not wander more than half a pocket. Ratchet backlash is the usual cause; add a drag spring on the wheel.
4. Duplicate the module to eight lanes. Bolt them to the front rail, numbers 1–8 left to right.
5. Set each lever XY and press Z, and each pick XY and pick Z, in OpenPnP.
6. Run the camera feeder calibration on each lane.
7. Pick 10 parts from each lane into a cup.

Done when: every lane feeds one pocket per press and 10 picks succeed, and the operator card from section 7.7 is at the machine.

### WP9 — Firmware and OpenPnP integration

Objective: one homing script and one job file that runs the whole cycle.

1. Apply the firmware changes from section 8.3 on a copy of the current configuration. Keep the previous binary.
2. Remove every heater from the configuration. Boot and confirm T10: no thermal error, bed connector absent.
3. Enter the calibrated steps/mm, speeds, and accelerations from WP2, WP3, and WP4.
4. Home order in the start G-code: raise Z, home X, home Y, home Z to the switch, then apply the PCB Z offset.
5. Build the OpenPnP objects from section 9.
6. Dry-run a job with vacuum off and Z raised by 5 mm (a “Z probe” or a global placement offset). The nozzle shall trace picks, the up-camera hover, and places without touching tape or PCB.
7. Remove the 5 mm offset. Run 10 real parts.
8. Back up firmware configuration and the OpenPnP profile to the project folder.

Done when: a cold start, one button, places 10 parts, and both backups exist.

### WP10 — Acceptance

Objective: sign section 11.

1. Run T1 through T10 in order.
2. For T8, use a scrap PCB with flux or paste, 50 parts, at least two package sizes.
3. Record speed, acceleration, blow time, steps/mm, nozzle-to-camera offset, and head mass in the build record next to the test results.
4. Any failed row goes back to the WP named in the note. Re-run that row and the rows after it.

Done when: the acceptance table is filled and PR-8 and PR-10 are met. PR-9 is recorded and does not gate acceptance.

## 13. Bill of materials, added parts

Quantities are for one machine. Stock motors, board, PSU, endstops, and frame hardware are not listed.

| Item | Qty | Notes |
| --- | --- | --- |
| MGN12H rail and 2 blocks | 2 sets | X, one on each C-beam, length to the measured 574 mm beam |
| MGN12H rail and 2 blocks | 1 set | Y, on the 550 mm beam |
| MGN9 or MGN12 short rail and block | 1 | Head Z |
| GT2 belt, 9 mm, 2 mm pitch | 2 loops plus spare | One loop per C-beam. The existing X belt stays on the Y beam |
| GT2 pulley, 20 tooth, 5 mm bore | 4 | Two on the X jackshaft, two idlers. The Y pulley is the one already on the 550 mm beam |
| Jackshaft, bearings, couplers | 1 | Spans the two C-beam ends. Dropped only if WP2 uses two series motors |
| NEMA 17 | 0 extra | Bed motor drives X. Beam motor drives Y. Z motor drives the head |
| NEMA 11 or 14 | 1 | Axis C |
| TR8×2 screw, nut, and anti-backlash nut | 1 | Head Z, or a 2 mm ball screw |
| Juki-compatible holder and 6 tips | 1 set | Section 7.4 |
| Diaphragm vacuum pump | 1 | Matched to PSU voltage |
| Solenoid valve, NC | 2 | Pick and blow |
| Vacuum switch | 1 | About −40 kPa |
| PU tube 4 mm and filter | 1 set | |
| USB global-shutter camera and M12 lens | 2 | Down-looking and up-looking |
| LED ring or bar, 12/24 V | 2 | With series resistor or the driver it ships with |
| Aluminum tooling plate | 1 | If the old bed fails the flatness check |
| 3 mm datum pins, clamps | 1 set | |
| Tape-holder hardware | 8 lanes | Sprocket, ratchet, lever, peel finger |
| Fasteners, shims, thread locker | as needed | M3 and M5, the frame’s existing sizes |

## 14. Risks and the response built into this plan

| Risk | What the plan does |
| --- | --- |
| V-wheel backlash is too large for 0603 | Rails are part of the specified machine, installed in WP2 and WP3, before vision tuning |
| The Z leadscrew is reused as the fast X drive | WP1 removes both screws. X is a dual GT2 belt. A screw on X fails PR-1 |
| The bridge yaws because the two C-beam belts differ | One jackshaft and matched tooth phase. WP2 stops on a 0.05 mm yaw reading |
| The board has only five drivers | Two X motors, if used, share the X driver in series. C uses E0. Feeders are head-actuated |
| Belt stretch under acceleration | PR-2 is a ceiling reached by test, not a starting value. WP2 and WP3 stop at the first skipped step |
| Tip family does not match the magazine | WP6 step 1 buys the tips before the pockets are made |
| Camera mm/pixel too coarse | Lens field of view is sized in section 7.6 and checked in WP7 before placement tests |
| Heater output left live | WP0 disconnects it, WP9 removes it from firmware, T10 confirms it |

## 15. Build record

Keep one page with the machine and fill it during the work packages.

- Board name, voltage, firmware binary name.
- Measured C-beam length, beam length, rail gap, X travel, and Y travel.
- Head mass.
- Steps/mm for X, Y, Z, and steps/degree for C.
- Accelerations actually used.
- Blow pulse width.
- Nozzle-to-camera offset.
- Pocket coordinates 1–6.
- Lever and pick coordinates for lanes 1–8.
- Acceptance table from section 11, with dates.

End of specification TEVO-BW-PNP-TS-001.

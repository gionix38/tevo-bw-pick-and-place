# TBW-Feeder v3.0: first-article and acceptance tests

v3.0 is verified in CAD (`feeder audit`: geometry, motion, assembly paths, support-free printing, loads;
`pnp check`), and the firmware compiles for the target. Build **one lane plus the controller** and pass these
tests before printing the other seven lanes. Record the results in a copy of the table at the end. The tests
marked *(v2.1 issue)* check the problems found on the v2.1 first article.

## A. First article: parts against the model

| # | Check | Pass |
| --- | --- | --- |
| A0 | Print every lane part on a 0.4 mm nozzle, 0.20 mm layers, **supports off**; note the printer's time per plate *(v2.1 issue)* | No part needs support or cleanup beyond piercing the 4 counterbore membranes; the times are within 15 % of `print_time.py` |
| A1 | The tape channel takes an 8.0 mm gauge strip along its full length, with no binding at the inlet flare | It slides under its own weight with the body tilted 30° |
| A2 | The slider lies in its tunnel; with the side plate fitted (no servo) it moves over 4.2 mm | It moves when pushed with ≤ 0.2 N |
| A3 | The SG90 tabs slide into the tab slot; with the side plate fitted, the servo can't move | No play you can feel up or down |
| A4 | Peel drive: step the servo between `U1291` and `U1709` by hand commands *(v2.1 issue)* | Rack, idler and pinion run without binding or skipping. The roller turns forward on every feed stroke and stands still on every retract. With the shaft held, the drive roller locks in one direction. The pinion doesn't slip on the shaft at 50 N mm (500 g at 10 mm). |
| A5 | Pinch: push the yoke tab down 3 mm and let go. Then step the servo back (idle stroke) with the cover tape loaded and 100 g hung on it on the peel side | It springs back onto the roller. During the idle stroke the roller and the cover tape don't move back. |
| A6 | Cover plate: slide it home; try to lift it; pull it toward the pick end *(v2.1 issue)* | With the 2 screws in, it can't be lifted or slid. Without them it slides out freely. It lies flat: a 0.1 mm feeler doesn't enter between the plate and the body anywhere. |
| A7 | The servo matches the size used in the model: case 22.5 × 12 × 22.7, tab span 32.2, tab top 4.2 below the output-side face, output boss Ø11.8 × 4.0, spline Ø4.8 × 2.8 | Within ±0.2 mm, otherwise update `model/feeder.py` and reprint |
| A9 | Servo gear: pressed on the spline, try to turn it against the held servo; run the slider over its stroke by hand commands *(new)* | No play you can feel; gear and slider rack run without binding or skipping over 37°. |
| A8 | Pawls: both turn freely on their pins; the spring returns each to its stop; the tooth stands 0.75 ± 0.1 mm above the tape floor *(v2.1 issue)* | Pushing the tooth down 0.85 mm needs 1.2–1.8 N (120–180 g), and it returns fully |
| A10 | Printed shafts in the HF0612: hold the pinion and turn the drive roller (and the pinch roller on its axle) in the locking direction with 50 N mm (50 g on a 10 cm lever arm, 5× the 9.6 N mm in use); then run 2000 feed strokes and repeat | Both clutches lock with no slip, before and after the 2000 strokes; no visible flats or dents on the shafts. If one slips, fit a hardened Ø6 dowel there (see DESIGN.md, Known limits). |

## B. Function, one lane on the bench

| # | Test | Pass |
| --- | --- | --- |
| B1 | Calibrate as in ASSEMBLY.md §5 | The forward end centres the pocket. The tooth drops into the next hole with ≥ 20 µs margin on the retract. |
| B2 | 4 mm feed accuracy: 200 × `M600 F4` on 0805 paper tape, measuring the pocket centre with the down camera after each feed *(v2.1 issue)* | 3σ ≤ 0.10 mm along X, no lost or double feeds |
| B3 | 2 mm feed accuracy: 200 × `M600 F2` on 0402 paper tape | 3σ ≤ 0.10 mm, every pocket presented |
| B4 | Embossed tape (SOT-23): 100 × `M600 F4` | No missed feeds; the pockets clear the groove; the detent catches every hole |
| B5 | Peel: 200 × `M600 F4`, then 200 × `M600 F2` *(v2.1 issue)* | The cover tape is always clear of the pick pocket and taut between feeds. No tape tear. The servo never stalls. |
| B6 | Back-drag: after a feed, pull the inlet tape rearward with 1 N; repeat over 200 feeds | The tape doesn't move by more than 0.15 mm |
| B7 | Endurance: 20 000 × `M600 F4` on a tape loop (≈ 3 h) | Pawl teeth, rack and pinion show wear within 0.1 mm. The pins and springs are unchanged. The one-way bearings still lock (A4). B2 and A5 still pass afterwards. |
| B8 | Push the slider back by hand with the servo detached (`M610 S0`) | The detent holds the tape. The slider moves back, and the pawl rides out of the hole without lifting the plate. |

## C. In the machine

| # | Check | Pass |
| --- | --- | --- |
| C1 | `pnp check` with the as-built heights (measure the tower and update the model if different) | 0 overlaps |
| C2 | Dry run: the head picks from every lane with vacuum off, Z raised by 5 mm | No contact with the cover plate, its rail lips (top 18.3 mm), the tower or the cover tape |
| C3 | 100 picks of 0805 per lane with vacuum and bottom vision | Lost-part rate < 2 % (PR-11) |
| C4 | Empty tape runs through the chute into the box; used cover tape lands in the waste bin over a full reel | No jam; nothing reaches the reel path |

## Record

| Test | Date | Lane | Result | Note |
| --- | --- | --- | --- | --- |
| | | | | |

# TBW-Feeder v2.1: first-article and acceptance tests

The design is verified in CAD (`feeder audit`, `pnp check`), and the firmware compiles for the target. Nothing has
been printed or run yet. Build **one lane plus the controller** and pass these tests before printing the other
seven lanes. Record the results in a copy of the table at the end.

## A. First article: parts against the model

| # | Check | Pass |
| --- | --- | --- |
| A1 | Tape channel takes an 8.0 mm gauge strip along its full length, with no binding at the inlet flare | slides under its own weight with the body tilted 30° |
| A2 | Slider goes in from the rear face and moves over 4.2 mm | moves when pushed with ≤ 0.2 N (5 g on a string) |
| A3 | SG90 case and tabs fit the pocket; the tab holes line up with the inserts | no forcing, screws start by hand |
| A4 | Peel drive: the lifter slides in its channel; stepping the servo with `M604` from 71° to 109° turns the ratchet; the ratchet can't be turned backwards by hand | 2 clicks per full stroke (2 teeth); the hold pawl holds 1.5 N at the roller rim (150 g hung on the cover tape) |
| A5 | The pinch yoke drops into the grooves and springs back onto the roller; the printed pinch roller spins freely; the cap snaps on and holds | returns from a 3 mm lift; the cap doesn't come off with the yoke lifted 3 mm |
| A6 | Printed cover plate: the tongue moves freely in its slit and springs back flat, the detent tab is 1.1 ± 0.1 mm high, the plate lies flat on the body | feeler gauge 0.1 mm doesn't enter between plate and body |
| A7 | The SG90 matches the catalogue size used in the model (32.2 × 12 × 22.7, tab face 4.3 below the output face); the printed ratchet teeth are sharp (tip flat ≤ 0.2 mm) | within ±0.2 mm, otherwise update `model/feeder.py` and reprint |

## B. Function, one lane on the bench

| # | Test | Pass |
| --- | --- | --- |
| B1 | Calibrate as in ASSEMBLY.md §5 | angles found with ≥ 2° margin on each side before a feed is missed |
| B2 | 4 mm feed accuracy: 200 × `M600 F4` on 0805 paper tape, measuring the pocket centre with the down camera after each feed | 3σ ≤ 0.10 mm along X, no lost or double feeds |
| B3 | 2 mm feed accuracy: 200 × `M600 F2` on 0402 paper tape | 3σ ≤ 0.10 mm, every pocket presented |
| B4 | Embossed tape (SOT-23): 100 × `M600 F4` | no missed feeds, the detent catches every hole |
| B5 | Peel: 200 × `M600 F4`, then 200 × `M600 F2` | cover tape always clear of the pick pocket and taut between feeds, the roller turns 2 teeth per full stroke, no tape tear, the servo never stalls |
| B6 | Back-drag: pull the inlet tape rearward with 1 N after a feed; watch the printed detent tab over 200 feeds on paper tape | the tape doesn't move by more than 0.15 mm, and the tab drops into every hole. If not, fit the steel fallback cover plate (`out/step/CoverPlate_flat.dxf`) |
| B7 | Endurance: 20 000 × `M600 F4` on a tape loop (≈ 3 h) | the slider flexure and both peel pawls have no cracks or whitening, tooth wear (pawls and ratchet) stays within 0.1 mm, B2 and A4 still pass afterwards |

## C. In the machine

| # | Test | Pass |
| --- | --- | --- |
| C1 | `pnp check` with the as-built heights (measure the tower and update the model if different) | 0 overlaps |
| C2 | Dry run: head picks from every lane with vacuum off, Z raised by 5 mm | no contact with the cover plate, tower or cover tape |
| C3 | 100 picks of 0805 per lane with vacuum and bottom vision | lost-part rate < 2 % (PR-11) |
| C4 | Empty tape runs through the chute into the box; used cover tape lands in the waste bin over a full reel | no jam, nothing reaches the reel path |

## Record

| Test | Date | Lane | Result | Note |
| --- | --- | --- | --- | --- |
| | | | | |

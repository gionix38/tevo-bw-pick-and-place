# TBW-Feeder v2.1: OpenPnP setup

The feeder controller is a second G-code device next to the motion board. Field names are from OpenPnP 2.x. If your
version labels a field differently, the values stay the same.

## Driver

Machine Setup → Drivers → add a **GcodeDriver** named `Feeders`:

| Field | Value |
| --- | --- |
| Communications | Serial, the Nano's COM port, 115200 8N1, no flow control |
| `CONNECT_COMMAND` | `M115` |
| `COMMAND_CONFIRM_REGEX` | `^ok.*` |
| `COMMAND_ERROR_REGEX` | `^error.*` |
| Timeout | 5000 ms (a 24 mm feed takes about 3.5 s) |
| Axes | none |

## Actuators

Add two actuators on the `Feeders` driver, value type **Double**:

| Actuator | `ACTUATE_DOUBLE_COMMAND` | Used for |
| --- | --- | --- |
| `Feed4` | `M600 N{IntegerValue} F4` | 4 mm part pitch (0603 / 0805 / 1206 paper, SOT-23 / SOD-123 embossed) |
| `Feed2` | `M600 N{IntegerValue} F2` | 2 mm part pitch (0402 paper) |

## Feeders

Add one **ReferenceAutoFeeder** per lane:

| Field | Value |
| --- | --- |
| Feed actuator | `Feed4` or `Feed2`, depending on the part pitch |
| Feed actuator value | lane index 0–7 (lane 1 = 0, the front lane) |
| Post-pick actuator | none |
| Location | `pick_xyz` of that lane from `../out/openpnp_coords.json`, then taught with the down camera on the first pocket |
| Rotation in tape | 0° for parts as they sit in the tape, measured along the feed direction (−X) |

Each feed moves the next pocket to the same pick location, so 2 mm tapes need no second location. Use bottom
vision on every part. The servo-defined stop repeats within about 0.05 mm, and bottom vision corrects the rest.

## Head Safe Z

Set the nozzle's Safe Z to `safe_z` from `../out/openpnp_coords.json` (−16.0 with the current model: the tip
2 mm above the tallest tooling the head passes over, the magazine tips). `pnp check` checks travel at that
height across the tooling strip. Don't travel at Z 0: the PR-10 estimate falls from about 840 to about 610
parts/h.

## First run

1. Connect the driver. The log should show `FIRMWARE_NAME:TBW-Feeder FIRMWARE_VERSION:2.0.0 LANES:8`.
2. Feeders tab → select a lane → **Feed**. One pocket moves into the window.
3. Teach the location on that pocket (camera), then **Pick** to check the height. The pick Z is the tape top
   minus 0.6 mm (`pick_xyz` Z).

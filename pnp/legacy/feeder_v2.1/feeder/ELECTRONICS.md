# TBW-Feeder v2.1: electronics

One controller runs a bank of 8 lanes. It's built only from off-the-shelf modules, so there is no custom PCB.
It talks to OpenPnP over its own USB port and doesn't use the printer board (FR-36).

## Parts (per bank)

| Qty | Part | Note |
| --- | --- | --- |
| 1 | Arduino Nano (ATmega328P, CH340 or FT232) | Flash with `firmware/tbw_feeder_fw` |
| 1 | Nano IO shield (GVS 3-pin header on every pin, external power terminal) | Servos plug in directly |
| 1 | 5 V 4 A power supply (e.g. Mean Well LRS-35-5), or a 24→5 V 5 A buck module from the printer PSU | Servo power |
| 1 | Electrolytic capacitor 1000 µF / 10 V | Across the servo rail at the shield terminal |
| 8 | Servo extension cable 3-pin, 300 mm | Lane servo → shield |
| 1 | USB cable mini/micro (to match the Nano) | To the OpenPnP PC |

## Wiring

```
5 V PSU +  ──┬── IO shield external power terminal V (set the shield jumper so the servo V rail comes from
             │   this terminal, not from the Nano / USB)
             └── 1000 µF +  (at the shield terminal)
5 V PSU −  ──┴── shield GND terminal, capacitor −
Nano USB  ────── OpenPnP PC (logic power and serial). USB GND and PSU GND are tied on the shield.
```

| Lane (N) | Servo signal (shield GVS header) |
| --- | --- |
| 0 | D2 |
| 1 | D3 |
| 2 | D4 |
| 3 | D5 |
| 4 | D6 |
| 5 | D7 |
| 6 | D8 |
| 7 | D9 |

Lane N = 0 is lane 1 in the model, which is the front lane (lowest Y). Servo colours: brown = GND, red = 5 V,
orange = signal. The cover tape peel is driven mechanically by each lane's servo (v2.1), so there are no motor
drivers. D10–D13 and A0–A7 stay free.

## Power budget

| Load | Current |
| --- | --- |
| 1 servo moving (others idle) | 0.15–0.7 A peak |
| 7 servos holding (light load) | 0.1–0.35 A |
| Nano + LEDs | 0.05 A |
| **Peak** | **≈ 1.1 A**, so a 4 A supply leaves margin for servo jitter and the inrush when the servos first attach |

The firmware moves one lane at a time. Servos attach on their first move, so the pawls don't jump when the board
powers up.

## Mounting and cable routing

The controller and its supply go in the machine's electronics box (TS 8). The model doesn't include that box
(report D10). Run each lane's servo cable out of the rear face, down the back of the bank and under the
tooling plate edge to the box. Keep them clear of the reel tape path and the waste bin.

## Flashing

```
arduino-cli lib install Servo
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328 firmware/tbw_feeder_fw
arduino-cli upload  --fqbn arduino:avr:nano:cpu=atmega328 -p COMx firmware/tbw_feeder_fw
```

Clones with the old bootloader need `cpu=atmega328old`. After power-up the board prints
`start TBW-Feeder 2.1.0`. `M115` answers with the firmware name, `M620` lists the lane settings.

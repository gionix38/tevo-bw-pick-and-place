# TBW-Feeder v3.0: electronics

One Arduino Nano controls one bank of eight lanes. It connects to the machine host over USB serial. The servo rail is supplied from the machine's dedicated 24-to-5 V DC/DC converter described in [`../electronics/POWER_CONTROL_DESIGN.md`](../electronics/POWER_CONTROL_DESIGN.md).

## Per bank

| Qty | Part | Note |
| --- | --- | --- |
| 1 | Arduino Nano (ATmega328P, CH340 or FT232) | `firmware/tbw_feeder_fw` |
| 1 | Nano IO shield with GVS headers and external servo-power terminal | Set jumper to external servo rail |
| 1 | 5 V DC/DC supply, 8 A design rating for the whole bank | Dedicated servo branch; validate with actual servos |
| 1 | 1000 uF / 10 V electrolytic capacitor | At the servo rail distribution point; observe polarity |
| 8 | 3-wire servo extension, 300 mm | Route away from tape and moving gantry |
| 1 | USB cable matching Nano connector | Host serial and Nano logic power |

## Wiring

```text
Machine 24 V fused branch -> DC/DC set to 5.0 V -> IO shield external servo V+
                                              -> capacitor + at the distribution point
DC/DC 0 V ------------------------------------> IO shield GND
                                              -> capacitor -
Nano USB -------------------------------------> Raspberry Pi / host USB
Servo signal pins ----------------------------> D2..D9 (lane N = N+1)
```

The USB cable powers the Nano logic. The external 5 V rail powers servos only. Configure the shield jumper so external V+ does not feed USB 5 V or the Nano 5 V pin. Join signal ground and servo supply ground once at the shield. Confirm continuity and jumper wiring on the exact shield revision before connecting the Nano or servos. Do not connect 24 V to the Nano.

| Lane index | Physical lane | Servo signal |
| --- | --- | --- |
| 0 | 1, front lane | D2 |
| 1 | 2 | D3 |
| 2 | 3 | D4 |
| 3 | 4 | D5 |
| 4 | 5 | D6 |
| 5 | 6 | D7 |
| 6 | 7 | D8 |
| 7 | 8, rear lane | D9 |

Servo colours are typically brown/black = GND, red = +5 V, orange/yellow = signal; verify the actual cable. D10-D13 and A0-A7 remain unused by this firmware.

## Power budget and validation

Previous project estimate: one moving servo 0.15-0.7 A peak, seven servos lightly holding 0.1-0.35 A, Nano/LEDs about 0.05 A, total roughly 1.1 A. This is not a worst-case stall rating. Select the converter using the real servo stall current and measured simultaneous load. Use a converter with thermal headroom and check 5 V at the farthest servo during repeated feeds. If 5 V drops or any servo resets, increase wire gauge/branch capacity or reduce rail length; do not solve it by powering servos from USB.

The master design proposes an 8 A converter rating as a capacity target, not a measured load. Verify the converter can dissipate its losses inside the electronics enclosure. Branch protection must be selected from measured load, conductor rating and converter data. Keep servo power cables away from motor phase wires.

## Firmware and bring-up

```powershell
arduino-cli lib install Servo
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328 firmware/tbw_feeder_fw
arduino-cli upload  --fqbn arduino:avr:nano:cpu=atmega328 -p COMx firmware/tbw_feeder_fw
```

Some Nano clones need `cpu=atmega328old`. After flash, verify `start TBW-Feeder 3.0.0`, `M115`, `M620`, then send `M502` and `M500` once if EEPROM layout 3 is new. First power the Nano without servos; then test one servo at low force; finally connect the bank and verify all eight channels and USB serial recovery.

The machine host may be Raspberry Pi 5 only after the ARM64 OpenPnP/camera acceptance gate in [`../electronics/POWER_CONTROL_DESIGN.md`](../electronics/POWER_CONTROL_DESIGN.md). The feeder Nano itself remains a separate USB serial controller.

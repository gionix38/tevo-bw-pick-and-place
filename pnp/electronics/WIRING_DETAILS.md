# Detailed wiring sheets — concept A

This sheet defines the terminal-to-terminal intent for the proposed panel. It is deliberately explicit about interfaces while leaving fuse ratings, wire sizes and exact motherboard pins unresolved until the physical parts are identified.

## 1. AC and protective earth

| From | To | Conductors | Notes |
|---|---|---|---|
| X1.1 L | Q1 input L | Brown / local code | AC input connector; voltage per site |
| X1.2 N | Q1 input N | Blue / local code | Switch both poles where required by the chosen device and code |
| X1.3 PE | PE bar, chassis stud, door bond, PSU FG/PE | Green-yellow | PE is unswitched and unfused |
| Q1 output L/N | F0 and protected AC distribution | L/N | F0/input protection is selected from supply datasheets and installation code |
| AC distribution | PS1 L/N | L/N | 24 V PSU AC input; respect its input range/selector |
| AC distribution | PS2 input | L/N | Dedicated certified Pi USB-C PSU; can be outside the low-voltage enclosure |

Never use the CAD drawing to choose AC conductor size, fuse or contactor rating. Cover live terminals; keep the AC path physically segregated from all SELV DC terminals; bond any conductive door with a flexible PE braid.

## 2. 24 V DC and safety shutdown

```text
PS1 V+ -> TB24+ -> F1 -> K1 power contact -> X-MOTION (+24 V) -> board VIN / motor drivers (only if rated)
                  -> F2 --------------------> X-VAC (+24 V) -> pump / valve branch (by nameplate)
                  -> F3 --------------------> DC/DC1 IN+ -> DC/DC1 OUT+ (5.0 V) -> F4 -> TB5-SERVO V+
                  -> F5 --------------------> X-AUX (spare, fuse fitted only for a defined load)
PS1 V- -> TB0 star -> X-MOTION 0 V; X-VAC 0 V; DC/DC1 IN-; controller signal reference as required

S0 E-stop, dual NC channels -> SR1 safety relay -> K1 coil + isolated DRIVER_EN path
K1 drops the motion branch. The Pi host stays powered for fault logging; servo/vacuum stop behavior must be validated.
```

F1-F5 are identifiers, **not fuse ratings**. Measure the loads; select each fuse from maximum continuous/inrush current, conductor ampacity, DC interrupt rating, PSU behavior and protection coordination. Keep the pump and motion return wiring separate back to TB0; do not route motor return current through the Nano/Pi ground.

## 3. Feeder controller and servo connector schedule

The Nano IO shield uses GVS signal connectors. Verify the shield's external power jumper with a meter before insertion. USB powers Nano logic; the isolated external 5 V branch powers only servo V+. Join grounds at the shield star point so signal levels have a reference. Never tie external servo V+ to USB VBUS.

| X-SERVO connector | Lane | Signal | V+ | GND |
|---|---:|---|---|---|
| X3.1 | Front / 1 | Nano D2 | DC/DC1 OUT+ via F4 | TB0 / DC/DC1 OUT- |
| X3.2 | 2 | Nano D3 | same | same |
| X3.3 | 3 | Nano D4 | same | same |
| X3.4 | 4 | Nano D5 | same | same |
| X3.5 | 5 | Nano D6 | same | same |
| X3.6 | 6 | Nano D7 | same | same |
| X3.7 | 7 | Nano D8 | same | same |
| X3.8 | Rear / 8 | Nano D9 | same | same |

Typical servo cable: brown/black = GND, red = +5 V, orange/yellow = signal. Check the actual servo lead, connector orientation, voltage range and locked-rotor current. Add the existing 1000 uF / 10 V capacitor across servo V+/GND at the distribution point, correct polarity. Keep the Nano's USB serial connection physically distinct from the servo rail.

## 4. Host I/O and camera wiring

| Host port | Device | Cable/role | Routing |
|---|---|---|---|
| USB 3.x | Powered USB hub (if needed) | Camera data only; hub must have a certified separate supply | Keep away from stepper phase bundles |
| Hub port 1 | Down-looking camera | UVC video | Fix device identity in OpenPnP, not only enumeration index |
| Hub port 2 | Up-looking camera | UVC video | Prefer MJPEG if supported to reduce USB bandwidth |
| USB 2.x | Motion board | USB serial / control | Add strain relief; verify actual board protocol/baud |
| USB 2.x | Feeder Nano | USB serial / feeder commands | Separate serial port identity in OpenPnP |
| Ethernet | Machine LAN | Setup, logs, remote access | Do not expose an unauthenticated remote desktop on an untrusted network |

Use a powered hub only after its current rating is verified. Measure both camera streams concurrently under exposure/lighting settings. If Pi 5 is selected, OpenPnP/camera support is a commissioning gate; the official OpenPnP Linux package does not currently list ARM64 as a packaged platform. For reliable production use, host OpenPnP on x86-64 and use Pi as an optional auxiliary computer until an ARM build is demonstrated.

## 5. Connector IDs and wire labels

| ID | Function | Label at both ends |
|---|---|---|
| X1 | AC input L/N/PE | `AC-L`, `AC-N`, `PE` |
| X2 | 24 V PSU output | `24V+`, `0V` |
| X3 | Eight feeder servo ports | `SV1..SV8`, each `SIG/V+/GND` |
| X4 | Motion branch after K1 | `MOTION+`, `MOTION-`, `DRIVER_EN` |
| X5 | Vacuum pump/valve branch | `VAC+`, `VAC-`, `VALVE+`, `VALVE-` |
| X6 | SBC host and camera USB | `HOST`, `CAM-DOWN`, `CAM-UP` |

Do not connect any connector based only on color. Check continuity, polarity and protective earth before fitting the boards. Record actual pin numbers and wire gauges in the as-built copy of this table.

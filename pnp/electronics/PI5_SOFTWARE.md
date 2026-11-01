# SBC software preparation — Raspberry Pi 5 candidate

Date checked: 2026-10-31. This is a preparation guide; no Pi board or microSD card is attached to this workstation, so the image cannot be flashed and no software can be installed on hardware here.

## Compatibility decision

Raspberry Pi OS 64-bit supports Pi 5 and is available on Debian Trixie. Choose the Desktop edition because OpenPnP is a desktop application. Raspberry Pi Imager is the preferred installer.

OpenPnP's official Linux download exists, but its developer guide lists packaged Linux binaries for x86/x64 and does not list ARM64. The OpenPnP OpenCV Java package has an ARMv8 build; that alone does not provide the missing OpenPnP application packaging or prove camera capture. Therefore:

- **Recommended machine host for dependable control:** x86-64 mini-PC running the official OpenPnP Linux package.
- **Optional Raspberry Pi 5:** use as auxiliary machine computer/logger, or as an experimental OpenPnP ARM port only after the build and dual-camera acceptance test below.
- **Orange Pi:** same OpenPnP ARM64 packaging caveat; it does not avoid the application compatibility issue.

## Official downloads

| Item | Official source | Selection |
|---|---|---|
| Raspberry Pi Imager | https://www.raspberrypi.com/software/ | Windows Imager; use it to fetch and write the OS to a new microSD/SSD |
| Raspberry Pi OS | https://www.raspberrypi.com/software/operating-systems/ | Raspberry Pi OS (64-bit), Desktop, Debian Trixie, Pi 5 |
| Direct OS image | https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2026-06-19/2026-06-18-raspios-trixie-arm64.img.xz | Published size 1,282 MB; SHA-256 `123287c05f27b0eebd8f65456f6369b8f6635fa50a3d440a4f9f6223bf58c8e2` |
| OpenPnP Linux | https://openpnp.org/downloads/ | Official Linux packages; verify target CPU architecture before installation |
| OpenPnP source/release | https://github.com/openpnp/openpnp/releases | Stable release currently shown as 2.6 |
| Capture library source | https://github.com/openpnp/openpnp-capture | V4L2 camera capture library; ARM64 application packaging remains unverified |

The current OS image is about 1.3 GB compressed and requires a separate boot device. Raspberry Pi Imager downloads the image directly and performs its integrity checks; prefer that workflow. Do not overwrite an existing SD card without first backing it up.

## Setup procedure when hardware is available

1. Use a new high-endurance 64 GB microSD card or a supported USB SSD. Back up any card that will be erased.
2. Install Raspberry Pi Imager on the setup PC. Select Raspberry Pi 5 → Raspberry Pi OS (64-bit) Desktop → new storage.
3. In Imager settings, set device name, user/password, locale/timezone, Wi-Fi only if needed, and enable SSH only if remote maintenance is required. Prefer wired Ethernet for setup.
4. Boot Pi 5 with active cooling and its official 27 W USB-C supply. Update using the supported OS updater; record OS/kernel and firmware versions.
5. For Pi diagnostics / source-build experiments, install basic tools: `sudo apt update && sudo apt install -y v4l-utils usbutils openjdk-17-jre git cmake build-essential pkg-config libusb-1.0-0-dev`.
6. Connect one UVC camera and verify it with `v4l2-ctl --list-devices`; repeat for the second camera. Check MJPEG/YUYV modes and bandwidth.
7. Confirm that USB serial adapters / motion board / Nano are enumerated consistently. Use stable device paths/identifiers; do not rely only on `/dev/ttyUSB0` ordering.
8. For production, install the official Linux package on the x86-64 host from https://openpnp.org/downloads/ and complete OpenPnP's quick-start camera/controller setup.
9. For an ARM OpenPnP experiment, build from the official OpenPnP source with an ARM64 JDK, build/install OpenPnP Capture for AArch64/V4L2, and follow the project build instructions. Start with one camera; then validate both cameras, image processing, serial motion and feeder communication for at least a 30-minute run.
10. If application launch, native camera capture, serial latency or dual-camera operation fails, move OpenPnP to an x86-64 host; retain Pi only for auxiliary monitoring.

## Software test record

| Test | Expected record |
|---|---|
| OS boot/update | OS release, kernel, boot media, supply voltage, temperature |
| Camera 1/2 | UVC device ID, resolutions/fps, pixel formats, dropped frames and exposure control |
| Motion serial | Controller name, VID/PID, baud, command/reply and safe-stop behavior |
| Feeder serial | Nano VID/PID, firmware 3.0.0, `M115`, `M620`, one-lane feed test |
| OpenPnP | Version/commit, CPU architecture, Java version, camera driver and 30-minute run result |

## Network limitation in this workspace

Direct binary retrieval was attempted from the provided workstation but HTTPS download failed at Windows TLS credential negotiation, and the web download endpoint denied the image fetch. No incomplete OS image or unsupported OpenPnP binary was saved. Official links and the published image checksum are recorded above so the OS can be obtained with Raspberry Pi Imager on the board setup PC.

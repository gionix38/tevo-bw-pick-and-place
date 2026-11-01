# TEVO-BW Pick-and-Place Conversion

Open engineering project for converting a TEVO Black Widow 3D printer into a desktop pick-and-place machine. The repository contains parametric FreeCAD models, the TBW-Feeder v3.0 design, assembly and electrical documentation, preliminary bills of materials, and illustrated design renders.

> **Status:** prototype design. CAD checks and diagrams do not certify a built machine. Verify fit, wiring, protection, motion limits, and feeder performance on the actual hardware before operation.

## Read this first

- [Full illustrated documentation binder (PDF, 82 pages)](pnp/out/TEVO_BW_PnP_Dossier.pdf)
- [Machine build and assembly guide](pnp/BUILD_AND_ASSEMBLY.md)
- [Current machine model report](pnp/out/report.md)
- [Power and detailed wiring design](pnp/electronics/POWER_CONTROL_DESIGN.md)
- [Feeder v3.0 guide](pnp/feeder/README.md)
- [Main machine BOM](pnp/out/bom.csv)

## Languages

- [Русский — краткое описание проекта](docs/i18n/ru/README.md)
- [Português — resumo do projeto](docs/i18n/pt-BR/README.md)
- [简体中文 — 项目简介](docs/i18n/zh-CN/README.md)

The translated pages are project summaries and navigation aids. The detailed engineering source documents and the PDF binder are currently in English.

## Build the CAD

Install FreeCAD 1.1, then run in PowerShell:

```powershell
cd pnp
.\pnp.ps1 build
.\pnp.ps1 check
.\pnp.ps1 all
```

The model check covers defined CAD poses; it does not validate the physical donor frame, electrical safety, or production performance. The control architecture currently recommends an x86-64 host for OpenPnP; Raspberry Pi is documented as an auxiliary/experimental option pending ARM64 application and camera validation.

## License and source assets

No repository-wide license has been assigned yet. Some folders contain third-party reference CAD and images with separate or unclear licensing. Check the origin and license of those assets before redistribution or commercial use.

The GitHub-ready copy leaves the large imported reference libraries out. See [REFERENCE_ASSETS.md](REFERENCE_ASSETS.md) for the scope and the files retained in this package.

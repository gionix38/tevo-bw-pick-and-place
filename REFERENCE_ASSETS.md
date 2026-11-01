# Publication package scope

This folder is a curated copy of the TEVO-BW project. The original workspace remains untouched.

## Included

- Parametric machine and feeder sources, scripts and firmware.
- Current assembly/build documentation, electrical diagrams, reports, CSV BOMs, renders and the combined PDF dossier.
- Current CAD exports that are modest in size and useful for fabrication or inspection.
- The archived feeder v2.1 source and instructions, without duplicate generated output trees.
- English project documentation plus short Russian, Brazilian Portuguese and Simplified Chinese README summaries.

## Left out of this copy

- Large imported printer/reference CAD libraries in `TEVO BW/` and `Tevo Black Widow 3d printer - 1933864/`.
- Old standalone STL exports and full-printer STL meshes. The current parametric build does not consume these STL assemblies; its machine dimensions are maintained in `pnp/params.py`.
- Temporary PDF raster pages, browser PDF profile/cache, Python bytecode, lock files and backup files.
- Duplicate spreadsheets and generated intermediate formats that can be rebuilt from the checked-in CSV and CAD source.

These excluded assets are still in the parent workspace. They were not deleted or moved. Large third-party reference files should only be added to a public repository after their distribution licenses are verified. This package does not include a repository license; public visibility alone does not grant reuse rights.

## Size check

This curated copy is intended to stay below GitHub's ordinary per-file limit; no Git LFS is needed for the files currently included. Recheck the largest files before adding new exports.

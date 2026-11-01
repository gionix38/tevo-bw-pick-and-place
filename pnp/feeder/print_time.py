"""Print time and filament per part, sliced by OrcaSlicer's CLI with the printer profile of a saved project.

    python print_time.py [--nozzle 0.25|0.4] [--template t.3mf] [--out report.md] group:<settings> <stl> ... ...

Orca's CLI slices projects saved by the GUI but not bare STLs with system presets, so this takes a saved AD5M
project (default: the newest one in Documents, as orca_project.py), slices it alone, then slices it again with
the STLs of one settings group added; the difference is the group's time and filament. Settings of a group are
project-level overrides, e.g. group:wall_loops=4,sparse_infill_density=40%,enable_support=1. With --nozzle
0.25 the machine / process / filament values of Orca's 'AD5M 0.25 Nozzle' system profiles are laid over the
project first (layer 0.12, 0.25 line widths, the 0.25 speeds and flow limits).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile

ORCA = r"C:\Program Files\OrcaSlicer\orca-slicer.exe"
PROFILES = r"C:\Program Files\OrcaSlicer\resources\profiles\Flashforge"
SYS_025 = ("Flashforge Adventurer 5M 0.25 Nozzle", "0.12mm Standard @Flashforge AD5M 0.25 Nozzle",
           "Flashforge Generic PETG @FF AD5M 0.25 Nozzle")
KEEP = {"name", "inherits", "from", "type", "version", "setting_id", "filament_id", "instantiation",
        "compatible_printers", "compatible_printers_condition", "compatible_prints", "compatible_prints_condition",
        "is_custom_defined", "description", "print_settings_id", "printer_settings_id", "filament_settings_id",
        "printer_model", "default_print_profile", "default_filament_profile", "post_process"}


def _sys(name):
    for sub in ("machine", "process", "filament"):
        p = os.path.join(PROFILES, sub, name + ".json")
        if os.path.exists(p):
            d = json.load(open(p, encoding="utf-8"))
            if d.get("inherits"):
                base = _sys(d["inherits"])
                base.update(d)
                d = base
            return d
    raise FileNotFoundError(name)


def project(template, dst, over, nozzle):
    """Copy of the template with post_process cleared (the CLI refuses it), the 0.25 profile laid over if
    asked, and the group overrides."""
    zi = zipfile.ZipFile(template)
    cfg = json.loads(zi.read("Metadata/project_settings.config"))
    cfg["post_process"] = []
    if nozzle == "0.25":
        for prof in SYS_025:
            for k, v in _sys(prof).items():
                if k in KEEP or k not in cfg:
                    continue
                cur = cfg[k]
                if isinstance(cur, list):
                    cfg[k] = (v if isinstance(v, list) else [v]) * 1
                    if len(cfg[k]) < len(cur):
                        cfg[k] = cfg[k] + cfg[k][-1:] * (len(cur) - len(cfg[k]))
                else:
                    cfg[k] = v[0] if isinstance(v, list) else v
    for k, v in over.items():
        cur = cfg.get(k)
        cfg[k] = [v] * len(cur) if isinstance(cur, list) else v
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            data = zi.read(it.filename)
            if it.filename == "Metadata/project_settings.config":
                data = json.dumps(cfg, indent=4).encode()
            zo.writestr(it, data)


def slice_(proj, stls, work):
    od = tempfile.mkdtemp(dir=work)
    cmd = [ORCA, "--arrange", "1", "--slice", "0", "--outputdir", od, proj] + list(stls)
    subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    t = g = 0.0
    found = False
    for fn in os.listdir(od):
        if fn.endswith(".gcode"):
            txt = open(os.path.join(od, fn), encoding="utf-8", errors="ignore").read()
            mt = re.search(r"estimated printing time \(normal mode\)\s*=\s*(.+)", txt)
            mg = re.search(r"; filament used \[g\]\s*=\s*([\d.]+)", txt)
            if mt:
                found = True
                t += sum(int(v) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
                         for v, u in re.findall(r"(\d+)([dhms])", mt.group(1)))
            if mg:
                g += float(mg.group(1))
    shutil.rmtree(od, ignore_errors=True)
    return (t, g) if found else (None, None)


def default_template():
    import glob
    docs = os.path.expanduser(r"~\Documents")
    for p in sorted(glob.glob(os.path.join(docs, "**", "*.3mf"), recursive=True), key=os.path.getmtime, reverse=True):
        try:
            cfg = json.loads(zipfile.ZipFile(p).read("Metadata/project_settings.config"))
        except (KeyError, ValueError, zipfile.BadZipFile):
            continue
        if "Adventurer 5M" in cfg.get("printer_model", ""):
            return p
    raise SystemExit("no AD5M project found in Documents; pass --template")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nozzle", default="0.4", choices=("0.25", "0.4"))
    ap.add_argument("--template")
    ap.add_argument("--out")
    ap.add_argument("items", nargs="+")
    a = ap.parse_args()
    groups, cur = [], None
    for it in a.items:
        if it.startswith("group:"):
            over = dict(kv.split("=", 1) for kv in it[6:].split(",") if kv)
            cur = (it[6:], over, [])
            groups.append(cur)
        else:
            cur[2].append(it)
    tpl = a.template or default_template()
    work = tempfile.mkdtemp(prefix="print_time_")
    rows = []
    for label, over, stls in groups:
        proj = os.path.join(work, "p.3mf")
        project(tpl, proj, over, a.nozzle)
        t0, g0 = slice_(proj, [], work)
        t1, g1 = slice_(proj, stls, work)
        if t0 is None or t1 is None:
            print("slice failed:", label, stls, flush=True)
            continue
        rows.append((label, [os.path.splitext(os.path.basename(s))[0] for s in stls], t1 - t0, g1 - g0))
        print("%-55s %6.0f min %6.1f g  %s" % (label, (t1 - t0) / 60, g1 - g0,
                                                " ".join(os.path.basename(s) for s in stls)), flush=True)
    tt, gg = sum(r[2] for r in rows), sum(r[3] for r in rows)
    print("TOTAL nozzle %s: %.1f h, %.0f g" % (a.nozzle, tt / 3600, gg))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("| Settings (nozzle %s) | Parts | Time | Filament |\n|---|---|---|---|\n" % a.nozzle)
            for label, parts, t, g in rows:
                f.write("| %s | %s | %.0f min | %.1f g |\n" % (label or "project defaults", ", ".join(parts), t / 60, g))
            f.write("| **Total** | | **%.1f h** | **%.0f g** |\n" % (tt / 3600, gg))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()

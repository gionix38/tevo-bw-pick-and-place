"""TEVO-BW pick-and-place model: command line driver.

Run with FreeCAD's bundled Python (see pnp.ps1 / pnp.cmd):
    pnp build   [--pose X Y Z C]      FCStd, STEP, STL, BOM, report, OpenPnP coordinates
    pnp render  [--views iso,head..]  PNG renders, headless
    pnp check                         interference check over the travel corners
    pnp all                           build + check + render
    pnp gui                           open the model in the FreeCAD GUI with colours (saved into the FCStd)
"""
import argparse
import csv
import json
import math
import os
import sys
import time

FREECAD_BIN = os.environ.get("FREECAD_BIN",
                             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "FreeCAD 1.1", "bin"))
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (FREECAD_BIN, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import params as P  # noqa: E402
from model import assembly, feeder, head, printing, tooling  # noqa: E402

OUT = os.path.join(HERE, "out")
REF_STEP = os.path.join(os.path.dirname(HERE), "Tevo Black Widow 3d printer - 1933864", "files", "Step_files")


def log(*a):
    print("[pnp]", *a, flush=True)


def ensure(*parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(p, exist_ok=True)
    return p


def safe(name):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in name)


# ------------------------------------------------------------------ coordinates for OpenPnP
def to_machine(x, y, z=None):
    o = P.machine_origin()
    r = [round(x - o[0], 2), round(y - o[1], 2)]
    if z is not None:
        r.append(round(z - o[2], 2))
    return r


def machine_points():
    d = P.derive()
    zt = P.TABLE_TOP_Z
    ztape = zt + feeder.TAPE_TOP
    pts = {"units": "mm, machine frame (TS 4): origin = nozzle at home, Z 0 = home switch, Z down negative",
           "travel": {"X": round(d["x_travel"], 2), "Y": round(d["y_travel"], 2), "Z": -P.Z_STROKE},
           "nozzle_to_down_camera": [P.CAMERA_OFFSET[0], P.CAMERA_OFFSET[1]],
           "pcb_top_Z": round(d["pcb_top_z"] - P.NOZZLE_TIP_HOME_Z, 2),
           "feeders": [], "magazine": [], "up_camera": None, "pcb": {},
           "safe_z": round(z_checks()[3] + P.SAFE_Z_MARGIN - P.NOZZLE_TIP_HOME_Z, 1)}
    for i in range(P.LANES):
        pick = tooling.feeder_points(i)
        pts["feeders"].append({"lane": i + 1, "type": "TBW-Feeder v3.0 (servo advance + geared peel, 2/4 mm per feed)",
                               "feed_gcode": "M600 N%d F4" % i,
                               "pick_xyz": to_machine(pick[0], pick[1], ztape - 0.6)})
    for k, (x, y) in enumerate(tooling.magazine_pockets()):
        pts["magazine"].append({"pocket": k + 1, "engage_xyz": to_machine(x, y, zt + 16.0)})
    ux, uy = P.UPCAM_XY
    pts["up_camera"] = {"xyz_hover": to_machine(ux, uy, zt + 2.5 + 4.0)}
    px, py = P.PCB_ORIGIN
    L, W, T = P.PCB_SIZE
    pts["pcb"] = {"datum_corner": to_machine(px, py, zt + T),
                  "fiducials": [to_machine(px + 6, py + 6), to_machine(px + L - 6, py + 6), to_machine(px + 6, py + W - 6)],
                  "datum_pins": [to_machine(px + 20, py - 1.5), to_machine(px + L - 20, py - 1.5)]}
    return pts


# ------------------------------------------------------------------ report pieces
def mass_table(items):
    rows = [(it.name, it.mass, it.move) for it in items if it.move in ("carriage", "zslide", "rotor")]
    rows.sort(key=lambda r: -r[1])
    return rows


def reach_checks():
    d = P.derive()
    xs = (d["nozzle_x_min"], d["nozzle_x_max"])
    ys = (d["nozzle_y_min"], d["nozzle_y_max"])
    res = []

    def chk(label, x, y):
        ok = xs[0] <= x <= xs[1] and ys[0] <= y <= ys[1]
        res.append((label, to_machine(x, y), ok))
    for i in range(P.LANES):
        chk("lane %d pick" % (i + 1), *tooling.feeder_points(i))
    for k, (x, y) in enumerate(tooling.magazine_pockets()):
        chk("magazine pocket %d" % (k + 1), x, y)
    chk("up camera", *P.UPCAM_XY)
    px, py = P.PCB_ORIGIN
    L, W, _ = P.PCB_SIZE
    for nm, (x, y) in (("PCB front-left", (px, py)), ("PCB rear-right", (px + L, py + W)),
                       ("PCB area 200x150 far corner", (px + P.PCB_AREA[0], py + P.PCB_AREA[1]))):
        chk(nm, x, y)
    # down camera must reach the pick pockets and fiducials too
    for i in (0, P.LANES - 1):
        pick = tooling.feeder_points(i)
        x, y = pick[0] - P.CAMERA_OFFSET[0], pick[1] - P.CAMERA_OFFSET[1]
        chk("down camera over lane %d pick" % (i + 1), x, y)
    return res


def z_checks():
    d = P.derive()
    zt = P.TABLE_TOP_Z
    tip_min = P.NOZZLE_TIP_HOME_Z + P.Z_SOFT_MIN     # firmware soft limit
    rows = []

    def row(label, z_needed):
        rows.append((label, round(z_needed - P.NOZZLE_TIP_HOME_Z, 2), z_needed >= tip_min + 1.0))
    row("place on PCB (top)", d["pcb_top_z"])
    row("pick from tape pocket", zt + feeder.TAPE_TOP - 0.6)
    row("magazine engage height", zt + 16.0)
    row("up-camera hover (4 mm above ring)", zt + 2.5 + 4.0)
    # fixed head parts must clear the tallest tooling at any XY
    items = assembly.static_items()
    low_fixed = min(it.shape.BoundBox.ZMin for it in items if it.move == "carriage")
    # tallest tooling the head can pass over: everything left of the feeder towers (X < feeder.X_TOWER)
    reach = Part.makeBox(feeder.X_TOWER + 1000, 3000, 1000, App.Vector(-1000, -1000, P.TABLE_TOP_Z - 1))
    tall = 0.0
    for it in items:
        if it.system not in ("feeders", "magazine", "table") or it.name.endswith(("Tape", "TapeParts")):
            continue
        bb = it.shape.BoundBox
        if bb.XMin >= feeder.X_TOWER:
            continue
        z = bb.ZMax if bb.XMax <= feeder.X_TOWER else it.shape.common(reach).BoundBox.ZMax
        tall = max(tall, z)
    return rows, tip_min, low_fixed, tall


def _pullout(rpm):
    pts = P.PULLOUT[P.PSU_V]
    for (r0, f0), (r1, f1) in zip(pts, pts[1:]):
        if rpm <= r1:
            return f0 + (f1 - f0) * (rpm - r0) / (r1 - r0)
    return pts[-1][1]


def _move_t(dist, v, a):
    """Trapezoid (or triangle) move time."""
    if dist <= 0:
        return 0.0
    return dist / v + v / a if dist >= v * v / a else 2 * (dist / a) ** 0.5


def dynamics(items, tall):
    """Drive checks against PR-1..PR-4 and a PR-10 cycle estimate; tall = tallest tooling the head passes over.
    Returns (rows, cycle dict, X mass, Y mass)."""
    d = P.derive()
    m = {}
    for it in items:
        m[it.move] = m.get(it.move, 0.0) + it.mass / 1000.0
    m_y = m.get("carriage", 0) + m.get("zslide", 0) + m.get("rotor", 0)
    m_x = m_y + m.get("bridge", 0)
    r = d["pulley_pd"] / 2000.0
    rows = []
    for ax, mass, j_extra, blocks in (("X", m_x, P.XJACK_INERTIA, 2), ("Y", m_y, 0.0, 2)):
        a = P.PR_A[ax] / 1000.0
        need = (mass * a + blocks * P.RAIL_DRAG + 1.0) * r + (P.NEMA17_ROTOR + j_extra) * a / r
        rpm = P.PR_V_XY / (math.pi * d["pulley_pd"]) * 60
        avail = P.NEMA17_HOLD * _pullout(rpm)
        rate = d["steps_xy"] * P.PR_V_XY
        rows.append(("%s drive: %.2f kg at %.0f mm/s2, %.0f mm/s (%.0f rpm)" % (ax, mass, P.PR_A[ax], P.PR_V_XY, rpm),
                     "need %.3f N m, pull-out %.3f N m, margin %.1f" % (need, avail, avail / need),
                     avail / need >= P.TORQUE_SF))
        rows.append(("%s step rate at %.0f mm/s" % (ax, P.PR_V_XY), "%.0f steps/s (board %.0f)" % (rate, P.BOARD_STEP_RATE),
                     rate <= P.BOARD_STEP_RATE))
    vz_max = P.BOARD_STEP_RATE / d["steps_z"]
    rows.append(("Z step rate at PR-3 %.0f mm/s (1/%d, %.0f steps/mm)" % (P.PR_V_Z, P.Z_MICROSTEPS, d["steps_z"]),
                 "%.0f steps/s, board limit gives %.0f mm/s" % (d["steps_z"] * P.PR_V_Z, vz_max), vz_max >= P.PR_V_Z))
    zm = P.MOTORS[P.Z_MOTOR]
    rpm_z = P.PR_V_Z / P.Z_SCREW_LEAD * 60
    m_z = m.get("zslide", 0) + m.get("rotor", 0)
    k = P.Z_SCREW_LEAD / 1000.0 / (2 * math.pi * P.Z_SCREW_EFF)
    for lbl, f_z, rpm in (("travel (slide %.2f kg, %.0f mm/s2)" % (m_z, P.Z_ACCEL), m_z * (9.81 + P.Z_ACCEL / 1000.0), rpm_z),
                          ("contact (slide weight + %.1f N compliance, slow)" % P.Z_COMPLIANCE,
                           m_z * 9.81 + P.Z_COMPLIANCE, 300.0)):
        need_z, avail_z = f_z * k, zm["torque"] * _pullout(rpm)
        rows.append(("Z drive %s %s: %.1f N at %.0f rpm" % (P.Z_MOTOR, lbl, f_z, rpm),
                     "need %.4f N m, pull-out %.4f N m, margin %.1f" % (need_z, avail_z, avail_z / need_z),
                     avail_z / need_z >= P.TORQUE_SF))
    c_rate = 2 * 90.0 / 0.150 * d["steps_c"]
    rows.append(("C step rate, 90 deg in 150 ms (PR-4)", "%.0f steps/s peak" % c_rate, c_rate <= P.BOARD_STEP_RATE))

    # PR-10: one part = feed, feeder -> up camera -> PCB centre -> feeder, Z at pick / hover / place
    lanes_y = [tooling.lane_y(i) for i in range(P.LANES)]
    fx, fy = P.PICK_X, sum(lanes_y) / len(lanes_y)
    ux, uy = P.UPCAM_XY
    px, py = P.PCB_ORIGIN[0] + P.PCB_SIZE[0] / 2, P.PCB_ORIGIN[1] + P.PCB_SIZE[1] / 2

    def xy_t(a, b):
        return max(_move_t(abs(b[0] - a[0]), P.PR_V_XY, P.PR_A["X"]), _move_t(abs(b[1] - a[1]), P.PR_V_XY, P.PR_A["Y"]))
    t_xy = xy_t((fx, fy), (ux, uy)) + xy_t((ux, uy), (px, py)) + xy_t((px, py), (fx, fy))
    vz = min(P.PR_V_Z, vz_max)
    safe = tall + P.SAFE_Z_MARGIN                                # tip height while travelling
    zs = [safe - (P.TABLE_TOP_Z + 16.0 - 0.6), safe - (P.TABLE_TOP_Z + 6.5), safe - d["pcb_top_z"]]
    t_z = sum(2 * _move_t(z, vz, P.Z_ACCEL) for z in zs)
    t = t_xy + t_z + P.VISION_S + P.VAC_S + P.FEED_S
    cyc = dict(t_xy=t_xy, t_z=t_z, vz=vz, t=t, pph=3600.0 / t, safe_z=safe - P.NOZZLE_TIP_HOME_Z,
               pph_prefeed=3600.0 / (t - P.FEED_S))
    rows.append(("PR-10 cycle estimate (avg lane -> up camera -> PCB centre -> back)",
                 "%.2f s/part = %.0f parts/h (%.0f with the feed done during the place)" % (t, cyc["pph"], cyc["pph_prefeed"]),
                 cyc["pph"] >= 800))
    return rows, cyc, m_x, m_y


# ------------------------------------------------------------------ commands
def cmd_build(args):
    t0 = time.time()
    pose = dict(zip("XYZC", args.pose))
    ensure()
    fcstd = os.path.join(OUT, "pnp_machine.FCStd")
    doc, items = assembly.make_document(pose, fcstd)
    log("FCStd  ", fcstd, "(%d objects, %.1fs)" % (len(items), time.time() - t0))

    import Import
    objs = [o for o in doc.Objects if o.TypeId == "Part::Feature"]
    step = os.path.join(OUT, "pnp_machine.step")
    Import.export([g for g in doc.Objects if g.TypeId == "App::DocumentObjectGroup"], step)
    log("STEP   ", step)

    # parts to make: STEP for machined plates, STL for printing (reference pose, frame coordinates)
    sdir, pdir = ensure("parts_step"), ensure("parts_stl")
    for dd in (sdir, pdir):
        for fn in os.listdir(dd):
            os.remove(os.path.join(dd, fn))
    seen = set()
    n_stl = n_step = 0
    for it in items:
        if it.kind not in ("make", "print") or it.move == "posed" and not it.printed:
            continue
        key = it.bom or it.name
        if key in seen and it.name.startswith("Lane") and not it.name.startswith("Lane1_"):
            continue
        seen.add(key)
        if it.kind == "make":
            it.shape.exportStep(os.path.join(sdir, safe(it.name) + ".step"))
            n_step += 1
        if it.printed:
            import Mesh
            import MeshPart
            from model import printing
            m = MeshPart.meshFromShape(Shape=printing.orient(it.shape, it.print_up), LinearDeflection=0.05,
                                       AngularDeflection=0.3)
            m.write(os.path.join(pdir, safe(it.name) + ".stl"))
            n_stl += 1
    log("parts  ", "%d STEP (machined) in %s, %d STL (printed) in %s" % (n_step, sdir, n_stl, pdir))

    # BOM
    bom = {}
    for it in items:
        if not it.bom:
            continue
        k = (it.kind, it.bom)
        e = bom.setdefault(k, dict(qty=0, mass=0.0, systems=set(), note=it.note))
        e["qty"] += it.qty
        e["mass"] += it.mass
        e["systems"].add(it.system)
    for it in items:
        for spec, q in it.fasteners.items():
            e = bom.setdefault(("fastener", spec), dict(qty=0, mass=0.0, systems=set(), note=""))
            e["qty"] += q
            e["systems"].add(it.system)
    bom_path = os.path.join(OUT, "bom.csv")
    with open(bom_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kind", "item", "qty", "systems", "mass_g_total", "note"])
        order = {"stock": 0, "buy": 1, "make": 2, "print": 3, "fastener": 4}
        for (kind, txt), e in sorted(bom.items(), key=lambda kv: (order.get(kv[0][0], 9), kv[0][1])):
            w.writerow([kind, txt, e["qty"], "/".join(sorted(e["systems"])), round(e["mass"], 1), e["note"]])
    log("BOM    ", bom_path, "(%d lines)" % len(bom))

    pts = machine_points()
    with open(os.path.join(OUT, "openpnp_coords.json"), "w", encoding="utf-8") as f:
        json.dump(pts, f, indent=2)
    log("coords ", os.path.join(OUT, "openpnp_coords.json"))

    write_color_macro()
    write_report(items, pose)
    log("build done in %.1fs" % (time.time() - t0))


def write_color_macro():
    macro = '''# Apply PnP colours after opening pnp_machine.FCStd in the FreeCAD GUI (Macro > Execute).
import FreeCAD as App
import FreeCADGui as Gui
doc = App.ActiveDocument
for o in doc.Objects:
    src = "PartColor" if hasattr(o, "PartColor") else "PnpColor"
    if hasattr(o, src) and o.ViewObject is not None:
        c = getattr(o, src)[:3]
        o.ViewObject.ShapeColor = c
        o.ViewObject.LineColor = (0.05, 0.05, 0.06)
Gui.SendMsgToActiveView("ViewFit")
'''
    with open(os.path.join(OUT, "apply_colors.FCMacro"), "w", encoding="utf-8") as f:
        f.write(macro)


def write_report(items, pose, check_rows=None):
    d = P.derive()
    lines = []
    A = lines.append
    A("# TEVO-BW PnP - model report")
    A("")
    A("Generated by `pnp build` from `params.py`. Spec: TEVO-BW-PNP-TS-001 rev 1.1. Date: %s." % time.strftime("%Y-%m-%d %H:%M"))
    A("")
    A("## Envelope (TS 3, 7.1, 7.2)")
    A("")
    A("| Quantity | Value |")
    A("| --- | --- |")
    A("| Frame footprint (C-beams, without drive blocks) | %.0f x %.0f mm |" % (P.CB_LEN, d["frame_width"]))
    A("| C-beam inner gap (measured in stock STEP) | %.0f mm |" % P.CB_GAP)
    A("| X travel (bridge on MGN12, 10 mm rail margin) | %.1f mm |" % d["x_travel"])
    A("| Y travel (carriage on MGN12, 10 mm rail margin) | %.1f mm |" % d["y_travel"])
    A("| Z stroke / usable (FR-11 >= 35) | %.0f / %.0f mm |" % (P.Z_STROKE, P.Z_USABLE))
    A("| Z soft limit (tip 1.0 mm into compliance at PCB top) | %.1f mm |" % P.Z_SOFT_MIN)
    A("| Bridge beam underside | Z %.0f mm (frame) |" % d["bridge_z"][0])
    A("| Table top / PCB top | Z %.1f / %.1f mm (frame) |" % (P.TABLE_TOP_Z, d["pcb_top_z"]))
    A("| Nozzle tip at Z home | Z %.1f mm (frame) |" % P.NOZZLE_TIP_HOME_Z)
    A("| Machine origin (nozzle home) in frame coords | %s |" % str(tuple(round(v, 1) for v in P.machine_origin())))
    A("")
    A("## Steps per unit (TS 8.1)")
    A("")
    A("| Axis | Value |")
    A("| --- | --- |")
    A("| X, Y (GT2, 20T, 1/%d) | %.3f steps/mm |" % (P.MICROSTEPS, d["steps_xy"]))
    A("| Z (T5x2 lead %.0f, 1/%d) | %.1f steps/mm |" % (P.Z_SCREW_LEAD, P.Z_MICROSTEPS, d["steps_z"]))
    A("| C (1:1, 1/%d) | %.4f steps/deg |" % (P.MICROSTEPS, d["steps_c"]))
    A("")
    A("## Carriage mass budget (FR-4, <= %.0f g)" % P.MASS_BUDGET)
    A("")
    rows = mass_table(items)
    tot = sum(r[1] for r in rows)
    blocks = sum(r[1] for r in rows if r[0].startswith("YBlock"))
    A("| Part | Group | Mass g |")
    A("| --- | --- | ---: |")
    for nm, m, mv in rows:
        if m >= 0.5:
            A("| %s | %s | %.1f |" % (nm, mv, m))
    A("| **Total moving in Y** | | **%.0f** |" % tot)
    A("| Total without the two MGN12H blocks | | %.0f |" % (tot - blocks))
    zm_alt = P.MOTORS["NEMA17_40"]["mass"] - P.MOTORS[P.Z_MOTOR]["mass"]
    A("")
    status = "PASS" if tot <= P.MASS_BUDGET else ("PASS excluding rail blocks" if tot - blocks <= P.MASS_BUDGET else "OVER")
    A("Status: **%s** (Z motor %s). With the stock NEMA17 40 mm on Z the total is %.0f g (+%.0f g)." %
      (status, P.Z_MOTOR, tot + zm_alt, zm_alt))
    A("Purchased-part masses are catalogue typicals; printed parts use PETG 1.27 g/cm3 x %.0f%% effective fill. "
      "WP4 step 6 weighs the real head." % (P.PRINT_FILL * 100))
    A("")
    A("## Reach (machine coordinates)")
    A("")
    A("Nozzle reach: X %.1f..%.1f, Y %.1f..%.1f (frame)." % (d["nozzle_x_min"], d["nozzle_x_max"],
                                                             d["nozzle_y_min"], d["nozzle_y_max"]))
    A("")
    A("| Target | X, Y | Reachable |")
    A("| --- | --- | --- |")
    for lbl, xy, ok in reach_checks():
        A("| %s | %.1f, %.1f | %s |" % (lbl, xy[0], xy[1], "yes" if ok else "**NO**"))
    A("")
    A("## Z heights (machine Z, 0 = home switch)")
    A("")
    zr, tip_min, low_fixed, tall = z_checks()
    A("Lowest tip (soft limit): Z %.1f. Lowest fixed head part at home: frame Z %.1f; tallest tooling the head "
      "passes over (X < %.0f, feeder towers excluded): frame Z %.1f; clearance %.1f mm." %
      (tip_min - P.NOZZLE_TIP_HOME_Z, low_fixed, feeder.X_TOWER, tall, low_fixed - tall))
    A("")
    A("| Operation | Z needed | Reachable with >= 1 mm margin |")
    A("| --- | ---: | --- |")
    for lbl, z, ok in zr:
        A("| %s | %.1f | %s |" % (lbl, z, "yes" if ok else "**NO**"))
    A("")
    A("## Dynamics (PR-1..PR-4, PR-10)")
    A("")
    drows, cyc, m_x, m_y = dynamics(items, tall)
    A("Moving mass: X (bridge + head) %.2f kg, Y (head) %.2f kg. Profiles use catalogue kg/m (WP0 weighs the beam); "
      "motors are the stock NEMA17 40 mm, %.0f V supply, required margin %.1f on pull-out torque." %
      (m_x, m_y, P.PSU_V, P.TORQUE_SF))
    A("")
    A("| Check | Result | Pass |")
    A("| --- | --- | --- |")
    for lbl, res, ok in drows:
        A("| %s | %s | %s |" % (lbl, res, "yes" if ok else "**NO**"))
    A("")
    A("Cycle breakdown: XY %.2f s, Z %.2f s (at %.0f mm/s, from Safe Z), vision %.2f s, vacuum %.2f s, feed %.2f s. "
      "**OpenPnP Safe Z = %.1f** (machine Z: tip %.0f mm above the tallest tooling the head passes over). Moving "
      "between pick, camera and place at Safe Z instead of Z 0 is what makes PR-10." %
      (cyc["t_xy"], cyc["t_z"], cyc["vz"], P.VISION_S, P.VAC_S, P.FEED_S, cyc["safe_z"], P.SAFE_Z_MARGIN))
    A("")
    if check_rows is not None:
        A("## Interference check")
        A("")
        if not check_rows:
            A("No interference between moving and fixed parts at the checked poses.")
        else:
            A("| Pose | A | B | Overlap mm3 |")
            A("| --- | --- | --- | ---: |")
            for r in check_rows:
                A("| %s | %s | %s | %.1f |" % r)
        A("")
    A("## Custom parts (what has to be made)")
    A("")
    A("| Part | Kind | Qty | Mass each g |")
    A("| --- | --- | ---: | ---: |")
    cust = {}
    for it in items:
        if it.kind in ("print", "make") and it.bom:
            e = cust.setdefault(it.bom, [it.kind, 0, it.mass])
            e[1] += 1
    for txt, (k, q, m) in sorted(cust.items(), key=lambda kv: (kv[1][0], kv[0])):
        A("| %s | %s | %d | %.0f |" % (txt, "printed" if k == "print" else "machined", q, m))
    nf = sum(sum(it.fasteners.values()) for it in items)
    A("")
    A("%d printed + %d machined parts; %d fasteners (see bom.csv, kind = fastener)." % (
        sum(v[1] for v in cust.values() if v[0] == "print"), sum(v[1] for v in cust.values() if v[0] == "make"), nf))
    A("")
    A("## Printing (printed parts)")
    A("")
    A("All printed parts are orange PETG (PETG-CF for the head parts). STLs in `parts_stl/` are already turned "
      "to the print orientation below and lie on Z = 0. Horizontal holes over %.1f mm diameter have a 45 deg "
      "teardrop roof (no support). Settings: 0.2 mm layers, 4 perimeters, 5 top/bottom layers, 40%% gyroid, "
      "elephant-foot compensation 0.2 mm, no supports. Bed check: %.0f x %.0f x %.0f mm." % (
          2 * printing.TEAR_MIN_R, *P.PRINT_BED))
    A("")
    A("| Part | Qty | Orientation (bed face) | Size on bed mm | Bed contact mm2 | Overhang mm2 | Flat bridge mm2 "
      "| Teardrops | Fits |")
    A("| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |")
    rows = {}
    for it in items:
        if it.kind != "print":
            continue
        key = it.bom or it.name
        if key in rows:
            rows[key][1] += 1
            continue
        rows[key] = [it, 1]
    for key, (it, q) in rows.items():
        a = printing.analyse(it.shape, it.print_up)
        A("| %s | %d | %s | %s | %.0f | %.0f | %.0f | %d | %s |" % (
            it.name if not it.name.startswith("Lane") else "Lane*_" + it.name.split("_", 1)[1], q,
            printing.up_label(it.print_up), " x ".join("%.0f" % v for v in a["size"]), a["contact"], a["overhang"],
            a["bridge"], it.teardrops, "yes" if printing.fits_bed(a["size"]) else "**NO**"))
    A("")
    A("Flat bridges left: corner-block pocket roofs (8 mm flat between 45 deg chamfers), down-facing "
      "counterbores under the feet, feeder body slider tunnel (5 / 13 mm) and pinch-yoke pocket (3.3 mm). All are "
      "within normal PETG bridging. Feeder waste bin is printed upside down; its floor bridges 34 mm.")
    A("")
    A("## Design notes against the TS")
    A("")
    A("- **D1** The stock C-beams are 480 mm apart (inner faces) in `Tevo Black Widow assembly.step`, not 500. "
      "The 20x80x500 top tie sits on the C-beam ends and does not fit between them; it is cut to 480. WP0 confirms.")
    A("- **D2** In the project model the 40x80x550 extrusion is the bed (Y) axis beam; the stock X gantry is two "
      "20x40x485 bars. This model uses the 40x80x550 as the Y bridge (TS 4 item 2) and the 20x40 pair, cut to 480, "
      "as the second tie (TS 7.1).")
    A("- **D3** The bridge sits on %.0f mm risers so the beam underside (Z %.0f) clears the tape bank, magazine "
      "and clamps. The head hangs in front of the beam (+X), so the nozzle reach is offset by %.1f mm in X." %
      (P.BRIDGE_RISER_H, d["bridge_z"][0], d["nozzle_dx"]))
    A("- **D4** The X belts run inside the open C channels; the C-beam end caps are replaced by printed drive and "
      "idler blocks. The jackshaft sits at the left end (TS 7.1).")
    A("- **D5** Head Z motor defaults to %s to cut mass; the stock NEMA17 is the fallback named in WP4 step 6." % P.Z_MOTOR)
    A("- **D6 (rev B)** The 20x80x210 legs are gone. Four printed corner blocks are end cap, pulley/idler housing, "
      "jackshaft bearing seat (608ZZ pressed in), tie corner bracket and leg in one; the front-left one also holds "
      "the X motor. Rubber feet screw into them.")
    A("- **D7 (rev B)** Tape lanes, up camera and nozzle magazine sit in a strip right of the bridge travel "
      "(X > %.0f, beam right face at most X %.0f), so the beam never passes over them. Tapes feed in from the "
      "right end. Magazine pockets run along Y (TS 7.5 says along X; the change is still single-axis motion)."
      % (P.FEEDER_X[0], d["bx_max"] + P.BRIDGE_SECTION[0] / 2))
    A("- **D8 (rev B)** One tooling plate carries the PCB fixture and the whole tooling strip, so all feeder, "
      "camera and magazine coordinates share one datum. 3-point support: left tie + two posts on the right tie.")
    A("- **D9 (rev B)** Head = one printed head carriage (mother plate, head plate, Z motor bracket, camera "
      "bracket, switch arm, belt clamp, chain post) + one machined Z slide (Z plate, both bearing bores in one "
      "setup for FR-14, nut seat, C motor shelf). Bridge = one printed end per side (foot plate, riser, belt "
      "clamp, chain arm). The LP mother plate is no longer used.")
    A("- **D10 (rev B)** Vacuum panel and electronics box are not modelled for now; TS 7.4 and 8 still apply.")
    A("- **D11 (rev D, current head)** The head uses a NEMA8 hollow-shaft C motor and a NEMA8 external "
      "linear Z motor with integral T5x2 screw. The nozzle stack is approximately 15 g; the model estimates "
      "low C torque demand, but bearing runout and loaded repeatability must be measured on the selected motor. "
      "The Z motor choice keeps modeled moving head mass below 500 g. Weigh the assembled head and verify "
      "the motor torque at the actual supply voltage before setting acceleration.")
    A("- **D12 (superseded feeder history)** The v2.0/v2.1 lane used a flexure pawl and ratchet-based peel "
      "mechanism and is archived under `legacy/feeder_v2.1/`. It is not the current geometry. Current feeder "
      "details are D14 and `feeder/ASSEMBLY.md`.")
    A("- **D13 (rev F, dynamics)** (1) Aluminium profiles now carry catalogue kg/m instead of the solid-core model "
      "volume: the bridge beam was 3.6 kg in the model, ~1.3 kg in reality, so X moves %.2f kg, not ~5.3 kg. "
      "(2) Z runs at 1/%d microstepping (%.0f steps/mm, 2.5 um): at 1/16 PR-3 needs 96k steps/s, over the "
      "~40k of the 8-bit board. Configure the Z driver jumpers and Marlin DEFAULT_AXIS_STEPS_PER_UNIT to match. "
      "(3) OpenPnP Safe Z = %.1f (tip 2 mm over the tallest tooling in reach, the magazine tips); travel at "
      "Safe Z is checked in `pnp check`. Together they bring the PR-10 estimate from ~610 to ~%.0f parts/h. "
      "(4) The torque checks assume a %.0f V supply; at 12 V the X margin drops to ~1.9 (WP0 confirms)."
      % (m_x, P.Z_MICROSTEPS, d["steps_z"], cyc["safe_z"], cyc["pph"], P.PSU_V))
    A("- **D14 (current v3.0 feeder)** Eight independent servo lanes use a rigid spring-loaded feed pawl and "
      "detent, plus a rack/idler/pinion peel drive with two HF0612 one-way bearings per lane. The segmented "
      "cover plate is screw-locked; lane body and side plate split so PETG parts print without supports. One "
      "separate Nano controller runs the servos. This geometry is awaiting its documented physical first article; "
      "see `feeder/README.md` and `feeder/TEST.md`.")
    A("")
    with open(os.path.join(OUT, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    log("report ", os.path.join(OUT, "report.md"))


def check_poses():
    d = P.derive()
    X, Y = d["x_travel"], d["y_travel"]
    place_z = round(d["pcb_top_z"] + 0.1 - P.NOZZLE_TIP_HOME_Z, 2)    # lowest working height (TS WP4 step 9)
    poses = []
    for x in (0.0, X):
        for y in (0.0, Y):
            for z, c in ((0.0, 0.0), (place_z, 90.0)):
                poses.append(dict(X=x, Y=y, Z=z, C=c))
    poses.append(dict(X=X / 2, Y=Y / 2, Z=place_z, C=45.0))
    # working moves on the tooling strip
    mp = machine_points()
    for f in (mp["feeders"][0], mp["feeders"][-1]):
        x, y, z = f["pick_xyz"]
        poses.append(dict(X=x, Y=y, Z=z, C=0.0))
        poses.append(dict(X=x - 2, Y=y - 57, Z=0.0, C=0.0))      # down camera over the pick pocket
    for m in (mp["magazine"][0], mp["magazine"][-1]):
        x, y, z = m["engage_xyz"]
        poses.append(dict(X=x, Y=y, Z=z, C=90.0))
    x, y, z = mp["up_camera"]["xyz_hover"]
    poses.append(dict(X=x, Y=y, Z=z, C=0.0))
    # travel at OpenPnP Safe Z across the tooling strip, the exit chute and the board (rev F)
    sz = mp["safe_z"]
    for x in (X, X - 30.0, X - 60.0):
        for y in (0.0, Y / 2, Y):
            poses.append(dict(X=x, Y=y, Z=sz, C=45.0))
    return poses


def cmd_check(args):
    t0 = time.time()
    base = assembly.static_items()
    found = []
    seen = set()
    for pose in check_poses():
        items, shapes = assembly.posed_items(pose, base)
        cand = [(it, s) for it, s in zip(items, shapes) if it.check]
        for i in range(len(cand)):
            a, sa = cand[i]
            for j in range(i + 1, len(cand)):
                b, sb = cand[j]
                if a.move == b.move:
                    continue        # rigid relative to each other
                ba, bb = sa.BoundBox, sb.BoundBox
                if not ba.intersect(bb):
                    continue
                try:
                    v = sa.common(sb).Volume
                except Exception:
                    continue
                if v > 0.5:
                    tag = "X%.0f Y%.0f Z%.0f C%.0f" % (pose["X"], pose["Y"], pose["Z"], pose["C"])
                    found.append((tag, a.name, b.name, v))
                    seen.add((a.name, b.name))
    log("check: %d poses, %d overlaps (%d distinct pairs), %.1fs" %
        (len(check_poses()), len(found), len(seen), time.time() - t0))
    for r in found[:60]:
        log("  %-28s %-28s %-28s %8.1f mm3" % r)
    ensure()
    items, _ = assembly.posed_items(dict(zip("XYZC", args.pose)), base)
    write_report(items, None, found)
    return found


def scene_entries(pose):
    items, shapes = assembly.posed_items(pose)
    ents = []
    for it, s in zip(items, shapes):
        tags = {it.system, it.move}
        if it.system == "head" or it.move in ("carriage", "zslide", "rotor"):
            tags.add("head")
        if it.system in ("table", "feeders", "magazine"):
            tags.add("table")
        if it.system in ("feeders", "magazine") or it.name.startswith("UpCam"):
            tags.add("strip")
        if it.name.startswith("Head_Carriage") or it.name.startswith("Z_Slide"):
            tags.add("headparts")
        for tag, pref in (("ymotor", ("YMotor_Bracket", "XChain_Arm")), ("yidler", ("YIdler_Bracket",)),
                          ("xidler", ("XIdler_Slider_Front", "Corner_FrontRight")),
                          ("bridgeend", ("Bridge_End_Front",)), ("tray", ("XChain_TrayBracket_1",)),
                          ("camera", ("Camera_Angle",)), ("feeder", ("Lane1_",)),
                          ("feeder_mech", ("Lane1_Slider", "Lane1_Servo", "Lane1_Crank", "Lane1_Rack",
                                           "Lane1_Idler", "Lane1_DriveRoller", "Lane1_PinchRoller",
                                           "Lane1_PinchYoke"))):
            if it.name.startswith(pref):
                tags.add(tag)
        if (it.system in ("x_axis", "frame") and s.BoundBox.XMax < 70 and s.BoundBox.YMax < 70
                and s.BoundBox.YMin > -100 and not it.name.startswith(("CBeam", "Tie", "XRail", "XBelt", "XJack"))):
            tags.add("xdrive")
        ents.append((it.name, s, it.color, tags))
    # floor
    ents.append(("Floor", Part.makeBox(1400, 1200, 1, App.Vector(-450, -350, -1)), (0.70, 0.71, 0.74), {"floor", "noedge"}))
    return ents


def cmd_render(args):
    t0 = time.time()
    import render
    pose = dict(zip("XYZC", args.pose))
    p = assembly.clamp_pose(pose)
    sc = render.Scene(scene_entries(p))
    log("scene built %.1fs" % (time.time() - t0))
    rdir = ensure("render")
    views = args.views.split(",") if args.views else list(render.VIEWS)
    w, h = (int(v) for v in args.size.lower().split("x"))
    sub = "Pose X %.0f  Y %.0f  Z %.0f  C %.0f  (machine mm/deg)   TEVO-BW-PNP-TS-001 rev 1.1" % (
        p["X"], p["Y"], p["Z"], p["C"])
    for v in views:
        t1 = time.time()
        if v == "feeder_mech":      # lane 1 alone, body and cover see-through
            ents = [(n, s, c, set(t) | {"fine"} | ({"ghost"} if n.endswith(("_Body", "_SidePlate", "_CoverPlate")) else set()))
                    for n, s, c, t in sc.entries if n.startswith(("Lane1_", "Screws_Lane1"))]
            sub_sc = render.Scene(ents)
            path = os.path.join(rdir, "%s%s.png" % (args.prefix, v))
            sub_sc.render(path, "feeder_mech", (w, h), ss=args.ss, title="TBW-Feeder v3.0  |  lane mechanism",
                          subtitle="SG90 above the tape, horn pin -> slider under the tape, rigid pawl on a pin (4.0 mm/feed); "
                                   "slider rack -> idler -> pinion -> one-way roller: the same stroke peels", zoom=args.zoom)
            log("render ", path, "%.1fs" % (time.time() - t1))
            continue
        path = os.path.join(rdir, "%s%s.png" % (args.prefix, v))
        sc.render(path, v, (w, h), ss=args.ss, title="TEVO Black Widow -> SMT pick & place  |  %s" % v,
                  subtitle=sub, zoom=args.zoom)
        log("render ", path, "%.1fs" % (time.time() - t1))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pnp", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("build", "render", "check", "all", "info", "gui"))
    ap.add_argument("--pose", nargs=4, type=float, default=None, metavar=("X", "Y", "Z", "C"),
                    help="machine pose: X Y from home (mm), Z <= 0 (mm), C (deg)")
    ap.add_argument("--views", default=None, help="comma list, default all: " + ",".join(
        ("iso", "iso_rear", "front", "top", "side", "head", "head_front", "table", "strip", "xdrive",
         "ymotor", "yidler", "xidler", "bridgeend", "tray", "camera", "feeder", "feeder_mech")))
    ap.add_argument("--size", default="1600x1000")
    ap.add_argument("--ss", type=int, default=2, help="supersampling factor")
    ap.add_argument("--zoom", type=float, default=1.0)
    ap.add_argument("--prefix", default="")
    args = ap.parse_args(argv)
    if args.pose is None:
        d = P.derive()
        args.pose = [d["x_travel"] * 0.45, d["y_travel"] * 0.55, -12.0, 30.0]
    if args.cmd == "gui":
        import subprocess
        exe = os.path.join(FREECAD_BIN, "freecad.exe")
        env = dict(os.environ, PNP_FCSTD=os.path.join(OUT, "pnp_machine.FCStd"))
        subprocess.Popen([exe, os.path.join(HERE, "open_gui.py")], cwd=HERE, env=env)
        log("FreeCAD GUI started with", env["PNP_FCSTD"])
        return
    if args.cmd == "info":
        print(json.dumps({k: v for k, v in P.derive().items()}, indent=1, default=str))
        print(json.dumps(machine_points(), indent=1))
        return
    if args.cmd in ("build", "all"):
        cmd_build(args)
    if args.cmd in ("check", "all"):
        cmd_check(args)
    if args.cmd in ("render", "all"):
        cmd_render(args)


if __name__ == "__main__":
    main()

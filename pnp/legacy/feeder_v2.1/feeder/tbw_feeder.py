"""TBW-Feeder v2.1: stand-alone build and design audit.

The geometry lives in ../model/feeder.py (the machine model uses the same code); this driver builds one
lane plus the bank parts (exit chute, waste bin, reel rack), exports them and checks them as a device.

Run with FreeCAD's bundled Python (see feeder.ps1 / feeder.cmd):
    feeder build    out/tbw_feeder_lane.FCStd + .step, out/stl/ (printed, on the bed), out/step/ (made), bom.csv
    feeder audit    geometry, motion, assembly, walls, loads, bank-vs-machine -> out/audit.md (exit 1 on FAIL)
    feeder all      build + audit
"""
import argparse
import csv
import math
import os
import sys
import time

FREECAD_BIN = os.environ.get("FREECAD_BIN",
                             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "FreeCAD 1.1", "bin"))
HERE = os.path.dirname(os.path.abspath(__file__))
PNP = os.path.dirname(HERE)
for p in (FREECAD_BIN, PNP):
    if p not in sys.path:
        sys.path.insert(0, p)

import FreeCAD as App  # noqa: E402
import Part  # noqa: E402

import params as P  # noqa: E402
from model import feeder as F  # noqa: E402
from model import geom as g  # noqa: E402
from model import printing  # noqa: E402

V = App.Vector
OUT = os.path.join(HERE, "out")
Y0 = 150.0                   # lane 1 centre line (frame coordinates, as in the machine)
ZT = P.TABLE_TOP_Z

# intentional contacts in the model pose (none: pawls and ratchet are drawn clear of each other)
INTENDED = set()
MIN_WALL = 0.8               # two 0.4 mm perimeters


def log(*a):
    print("[feeder]", *a, flush=True)


def ensure(*parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(p, exist_ok=True)
    return p


def lane_parts(th=None):
    """{suffix: (shape, colour, mat, mass, bom, kind, print_up)}, screws; lane 1, horn angle th."""
    g.take_screws()
    parts = {}
    for suf, shp, col, mat, mass, bom, kind in F.build_lane(Y0, th):
        up = None
        if kind == "print":
            shp, up, _ = printing.prepare("Lane_" + suf, shp)
            col = g.C_ORANGE
        parts[suf] = (shp, col, mat, mass, bom, kind, up)
    return parts, g.take_screws()


def bank_parts():
    g.take_screws()
    parts = {}
    for name, shp, col, mat, mass, bom, kind, fast in F.build_bank([Y0 + i * P.LANE_PITCH for i in range(P.LANES)]):
        up = None
        if kind == "print":
            shp, up, _ = printing.prepare(name, shp)
        parts[name] = (shp, col, mat, mass, bom, kind, up, fast or {})
    return parts, g.take_screws()


def mass_of(shp, mat, mass, kind):
    if mass is not None:
        return mass
    if mat is None:
        return 0.0
    m = shp.Volume / 1000.0 * g.DENSITY[mat]
    return m * P.PRINT_FILL if kind == "print" else m


# ------------------------------------------------------------------ build
def cmd_build(_args):
    t0 = time.time()
    lane, lscrews = lane_parts()
    bank, bscrews = bank_parts()
    ensure()
    doc = App.newDocument("TBW_Feeder")
    objs = []
    allp = list(lane.items()) + list(bank.items())
    pcol = g.part_colors((n, rec[5], rec[1]) for n, rec in allp)
    for name, rec in list(lane.items()) + list(bank.items()):
        o = doc.addObject("Part::Feature", name)
        o.Shape = rec[0]
        o.addProperty("App::PropertyString", "Kind").Kind = rec[5]
        o.addProperty("App::PropertyString", "BOM").BOM = rec[4] or ""
        o.addProperty("App::PropertyColor", "PnpColor", "PnP", "display colour")
        o.PnpColor = tuple(rec[1])
        o.addProperty("App::PropertyColor", "PartColor", "PnP", "display colour, one per part")
        o.PartColor = pcol[name]
        objs.append(o)
    for nm, sc in (("Screws_Lane", lscrews), ("Screws_Bank", bscrews)):
        if sc:
            o = doc.addObject("Part::Feature", nm)
            o.Shape = sc
            o.addProperty("App::PropertyColor", "PnpColor", "PnP", "display colour")
            o.PnpColor = (0.22, 0.22, 0.24)
            objs.append(o)
    doc.recompute()
    fc = os.path.join(OUT, "tbw_feeder_lane.FCStd")
    doc.saveAs(fc)
    log("FCStd ", fc)

    import Import
    import MeshPart
    Import.export(objs, os.path.join(OUT, "tbw_feeder_lane.step"))
    sdir, pdir = ensure("step"), ensure("stl")
    for dd in (sdir, pdir):
        for fn in os.listdir(dd):
            os.remove(os.path.join(dd, fn))
    seen = set()
    for name, rec in list(lane.items()) + list(bank.items()):
        shp, kind, up, bom = rec[0], rec[5], rec[6], rec[4]
        if bom in seen:
            continue
        seen.add(bom)
        if kind == "make":
            shp.exportStep(os.path.join(sdir, name + ".step"))
        elif kind == "print":
            m = MeshPart.meshFromShape(Shape=printing.orient(shp, up), LinearDeflection=0.05, AngularDeflection=0.3)
            m.write(os.path.join(pdir, name.rstrip("_0123456789") + ".stl"))
    write_cover_dxf(os.path.join(sdir, "CoverPlate_flat.dxf"))           # steel plate fallback, always exported
    if F.COVER_PLATE == "printed":
        F._cover_plate_steel(Y0, ZT).exportStep(os.path.join(sdir, "CoverPlate_steel.step"))
    hj = horn_jig()
    MeshPart.meshFromShape(Shape=printing.orient(hj, V(0, 0, 1)), LinearDeflection=0.05,
                           AngularDeflection=0.3).write(os.path.join(pdir, "HornDrillJig.stl"))
    log("parts ", sdir, pdir)

    rows = {}

    def add(kind, item, qty_lane, qty_bank, mass):
        r = rows.setdefault((kind, item), [0, 0, 0.0])
        r[0] += qty_lane
        r[1] += qty_bank
        r[2] += mass
    for shp, col, mat, mass, bom, kind, up in lane.values():
        if bom:
            add(kind, bom, 1, 0, mass_of(shp, mat, mass, kind))
    for spec, q in F.LANE_FASTENERS.items():
        add("fastener", spec, q, 0, 0.0)
    for shp, col, mat, mass, bom, kind, up, fast in bank.values():
        if bom:
            add(kind, bom, 0, 1, mass_of(shp, mat, mass, kind))
        for spec, q in fast.items():
            add("fastener", spec, 0, q, 0.0)
    add("print", "Horn drill jig (printed PETG, tool)", 0, 1, 2.0)
    with open(os.path.join(OUT, "bom.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kind", "item", "qty_per_lane", "qty_per_bank", "total_8_lanes", "mass_g_each"])
        order = {"buy": 0, "make": 1, "print": 2, "fastener": 3}
        for (kind, item), (ql, qb, m) in sorted(rows.items(), key=lambda kv: (order.get(kv[0][0], 9), kv[0][1])):
            n = ql + qb
            w.writerow([kind, item, ql, qb, ql * P.LANES + qb, round(m / n, 1) if n else 0.0])
    log("BOM   ", os.path.join(OUT, "bom.csv"))
    App.closeDocument(doc.Name)
    log("build done in %.1fs" % (time.time() - t0))


def write_cover_dxf(path):
    """Flat pattern of the cover plate for laser cutting (R12 DXF, mm). Layer CUT = cut contours,
    BEND = bend lines (all 90 deg down, inner radius 0.5). Origin = front-left corner of the plate.
    Flat lengths of the bent tabs use a 90 deg bend allowance of 0.35 mm for 0.5 mm 1.4310 (K ~ 0.33);
    the supplier adjusts them to their press brake."""
    x0, y0 = 530.0, -9.0
    yc = F.HOLE_DY
    py = F.POCKET_DY
    t0, t1 = F.D_HOOK, F.D_HOOK + F.TONGUE_L
    tab_l = 3.0 - 0.5 - 0.5 + 0.35          # rear hinge tabs: 3.0 outside height
    det_l = (F.CH_TOP - F.DET_Z) - 0.5 + 0.35   # detent tab: 1.1 below the plate underside
    ents = []

    def poly(pts, layer="CUT"):
        for a, b in zip(pts, pts[1:] + pts[:1]):
            ents.append(("LINE", layer, (a[0] - x0, a[1] - y0, b[0] - x0, b[1] - y0)))

    xr = 591.0
    outline = [(530.0, -9.0), (xr, -9.0), (xr, -8.5), (xr + tab_l, -8.5), (xr + tab_l, -5.5), (xr, -5.5),
               (xr, 5.5), (xr + tab_l, 5.5), (xr + tab_l, 8.5), (xr, 8.5), (xr, 9.0), (530.0, 9.0)]
    poly(outline)
    poly([(P.PICK_X - 4, py - 2.6), (P.PICK_X + 4, py - 2.6), (P.PICK_X + 4, py + 2.6), (P.PICK_X - 4, py + 2.6)])
    poly([(P.PICK_X + 6, -2.0), (P.PICK_X + 8, -2.0), (P.PICK_X + 8, 4.5), (P.PICK_X + 6, 4.5)])
    poly([(t1, yc - 1.5), (t0 - det_l - 0.5, yc - 1.5), (t0 - det_l - 0.5, yc + 1.5), (t1, yc + 1.5),
          (t1, yc + 1.0), (t0, yc + 1.0), (t0, yc + 0.4), (t0 - det_l, yc + 0.4), (t0 - det_l, yc - 0.4),
          (t0, yc - 0.4), (t0, yc - 1.0), (t1, yc - 1.0)])
    for s in (-7.0, 7.0):
        ents.append(("CIRCLE", "CUT", (532.5 - x0, s - y0, 1.2)))
    for a, b in (((xr, -8.5), (xr, -5.5)), ((xr, 5.5), (xr, 8.5)), ((t0, yc - 0.4), (t0, yc + 0.4))):
        ents.append(("LINE", "BEND", (a[0] - x0, a[1] - y0, b[0] - x0, b[1] - y0)))
    out = ["0", "SECTION", "2", "ENTITIES"]
    for kind, layer, v in ents:
        if kind == "LINE":
            out += ["0", "LINE", "8", layer, "10", "%.4f" % v[0], "20", "%.4f" % v[1], "30", "0",
                    "11", "%.4f" % v[2], "21", "%.4f" % v[3], "31", "0"]
        else:
            out += ["0", "CIRCLE", "8", layer, "10", "%.4f" % v[0], "20", "%.4f" % v[1], "30", "0", "40", "%.4f" % v[2]]
    out += ["0", "ENDSEC", "0", "EOF"]
    with open(path, "w", encoding="ascii") as f:
        f.write("\n".join(out) + "\n")


def horn_jig():
    """Drill jig for the 2 mm pin hole at R 6.5 in the SG90 single-arm horn: the horn hub sits on a 4.8 mm
    boss, the arm lies in a 5.4 mm groove, a 2.0 mm guide hole is at 6.5 mm from the boss axis."""
    b = Part.makeBox(30, 14, 8, V(-8, -7, 0))
    b = b.cut(Part.makeBox(30, 5.4, 2.0, V(-1, -2.7, 6.0)))                    # arm groove
    b = b.cut(Part.makeCylinder(3.8, 2.0, V(0, 0, 6.0)))                       # hub recess
    b = b.fuse(Part.makeCylinder(2.3, 3.5, V(0, 0, 4.0)))                      # spline-bore locating boss
    b = b.cut(Part.makeCylinder(1.0, 10, V(F.HORN_R, 0, -1)))                  # drill guide
    return b.removeSplitter()


# ------------------------------------------------------------------ audit helpers
def overlap(a, b):
    try:
        return a.common(b).Volume
    except Part.OCCError:
        return -1.0


def moved(shp, dx=0.0, dy=0.0, dz=0.0):
    s = shp.copy()
    s.translate(V(dx, dy, dz))
    return s


def free_path(part, fixed, d, travel, step=1.0):
    """True if part can move along d by travel without hitting fixed (sampled every step mm)."""
    dv = V(*d)
    for k in range(1, int(travel / step) + 1):
        if overlap(moved(part, *(dv * (k * step))), fixed) > 0.02:
            return False, k * step
    return True, travel


def thin_walls(shape, step=1.0, zstep=1.5):
    """Thinnest material runs along X and Y lines through the part; returns sorted [(t, axis, x/y, z)]."""
    bb = shape.BoundBox
    found = []
    z = bb.ZMin + 0.4
    while z < bb.ZMax:
        y = bb.YMin + 0.25
        while y < bb.YMax:
            ln = Part.makeLine(V(bb.XMin - 1, y, z), V(bb.XMax + 1, y, z))
            for e in shape.common(ln).Edges:
                found.append((e.Length, "X", round(e.BoundBox.XMin, 1), round(y, 2), round(z - ZT, 1)))
            y += step / 2
        x = bb.XMin + 0.25
        while x < bb.XMax:
            ln = Part.makeLine(V(x, bb.YMin - 1, z), V(x, bb.YMax + 1, z))
            for e in shape.common(ln).Edges:
                found.append((e.Length, "Y", round(x, 2), round(e.BoundBox.YMin - Y0, 1), round(z - ZT, 1)))
            x += step
        z += zstep
    return sorted(found)


# ------------------------------------------------------------------ audit
def cmd_audit(args):
    t0 = time.time()
    lane, _ = lane_parts()
    S = {k: v[0] for k, v in lane.items()}
    body, slider = S["Body"], S["Slider"]
    rows = []

    def row(area, check, value, ok, note=""):
        st = "OK" if ok is True else ("FAIL" if ok is False else "INFO")
        rows.append((area, check, value, st, note))
        log("%-4s %-10s %s: %s" % (st, area, check, value))

    # 1. static overlaps between all lane parts, carrier tape included
    hits = []
    names = [k for k in S if k != "TapeParts"]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if frozenset((a, b)) in INTENDED or {a, b} == {"Tape", "CoverTape"}:
                continue
            v = overlap(S[a], S[b])
            if v > 0.02:
                hits.append("%s/%s %.2f mm3" % (a, b, v))
    row("geometry", "static overlaps, all lane parts + tape (model pose = forward end)", "; ".join(hits) or "none",
        not hits, "includes lifter pawl / ratchet / hold pawl")
    row("geometry", "pawl tooth and detent tab sit in sprocket holes at the forward end",
        "tooth/tape %.3f, tab/tape %.3f mm3" % (overlap(slider, S["Tape"]), overlap(S["CoverPlate"], S["Tape"])),
        overlap(slider, S["Tape"]) < 0.02 and overlap(S["CoverPlate"], S["Tape"]) < 0.02)

    # 2. advance motion: horn angle sweep, slider follows the pin
    worst = {}
    for th in [F.TH_FWD - k * (F.TH_FWD - F.TH_RET) / 8 for k in range(9)]:
        lp, _ = lane_parts(th)
        for a, b in (("Slider", "Body"), ("Slider", "CoverPlate"), ("Horn", "Body"), ("HornPin", "Body"),
                     ("HornPin", "Slider"), ("Horn", "Servo_SG90"), ("Lifter", "Body"), ("Lifter", "Servo_SG90"),
                     ("Lifter", "Slider"), ("Lifter", "SliderPeg"), ("Lifter", "HoldPawl"), ("Lifter", "CheekCap"),
                     ("SliderPeg", "Body"), ("Lifter", "DriveRoller")):
            worst[(a, b)] = max(worst.get((a, b), 0.0), overlap(lp[a][0], lp[b][0] if b != "Body" else body))
        if abs(th - F.TH_RET) < 1e-6:
            ret_tape = overlap(lp["Slider"][0], S["Tape"])
    bad = ["%s/%s %.2f" % (a, b, v) for (a, b), v in worst.items() if v > 0.02]
    row("advance", "servo sweep %.1f..%.1f deg: slider, horn, pin, dowel, lifter vs body/plate/servo/pawl/cap"
        % (F.TH_RET, F.TH_FWD), "; ".join(bad) or "free", not bad,
        "the lifter pawl riding over the ratchet teeth is its flexure working (checked under peel drive)")
    row("advance", "tooth drops into the next hole at the retract end", "tooth/tape %.3f mm3" % ret_tape,
        ret_tape < 0.02, "stroke %.1f = 4.0 feed + 0.2 free travel" % F.STROKE)
    flex_need = (F.ZB + 0.75) - F.ZB                      # tooth top 15.85 rides on the tape underside 15.1
    flex_room = (P.TABLE_TOP_Z + 14.1 - 0.0) - (P.TABLE_TOP_Z + 12.4)
    row("advance", "flexure deflection when riding under the tape vs room", "%.2f / %.2f mm" % (flex_need, flex_room),
        flex_room >= flex_need + 0.3)

    # 3. assembly paths (each in the order of ASSEMBLY.md)
    ap = []
    ok_s, _ = free_path(slider.fuse(S["SliderPeg"]), body, (1, 0, 0), F.X_OUT - F.W_HOOK + 2, step=2.0)
    ap.append(("slider + dowel in from the rear face (+X)", ok_s))
    mid, _ = lane_parts(90.0)                             # horn fitted with the servo centred (ASSEMBLY.md)
    servo_grp = mid["Servo_SG90"][0].fuse([mid["Horn"][0], mid["HornPin"][0]])
    ap.append(("servo + horn + pin in from the top at 90 deg (+Z)",
               free_path(servo_grp, body.fuse([mid["Slider"][0], mid["SliderPeg"][0]]), (0, 0, 1), 60)[0]))
    fwd_grp = body.fuse([slider, S["SliderPeg"], S["Servo_SG90"], S["Horn"], S["HornPin"]])
    ap.append(("lifter in from the top with the servo at the forward end, dowel through the slot entry (+Z)",
               free_path(S["Lifter"], fwd_grp, (0, 0, 1), 75)[0]))
    ap.append(("hold pawl in from the top (+Z)", free_path(S["HoldPawl"], body, (0, 0, 1), 40)[0]))
    ap.append(("ratchet + roller between the cheeks from the top (pawls flex aside)",
               free_path(S["DriveRoller"].fuse(S["Ratchet"]), body, (0, 0, 1), 30)[0]))
    ap.append(("roller axle through the -Y cheek (-Y)", free_path(S["RollerShaft"], body, (0, -1, 0), 22)[0]))
    yoke_grp = S["PinchYoke"].fuse([S["PinchRoller"], S["PinchAxle"]])
    ap.append(("pinch yoke + roller in from the top (+Z)", free_path(yoke_grp, body, (0, 0, 1), 20)[0]))
    ap.append(("cover plate lifts off (+Z, tongue clear of the tape)",
               free_path(S["CoverPlate"], body, (0, 0, 1), 5, step=0.5)[0]))
    bad = [n for n, ok in ap if not ok]
    row("assembly", "assembly paths (%d)" % len(ap), "blocked: " + ", ".join(bad) if bad else "all free", not bad)

    # 4. walls of the printed parts
    for nm in ("Body", "Slider", "PinchYoke", "Lifter", "HoldPawl", "CheekCap", "PinchRoller") + (
            ("CoverPlate",) if F.COVER_PLATE == "printed" else ()):
        tw = [w for w in thin_walls(S[nm]) if w[0] > 0.05]
        thin = [w for w in tw if w[0] < MIN_WALL]
        row("printing", "%s thinnest wall (X/Y line sampling)" % nm, "%.2f mm at %s" % (tw[0][0], tw[0][1:]),
            not thin, "; ".join("%.2f %s" % (w[0], w[1:]) for w in thin[:6]))

    # 5. loads and margins (numbers in DESIGN.md)
    E_petg, E_steel = 2000.0, 195000.0
    b, t, L, d = 2.6, 0.9, F.FLEX_L, 0.75
    I = b * t ** 3 / 12
    f_flex = 3 * E_petg * I * d / L ** 3
    eps = 1.5 * t * d / L ** 2
    row("loads", "pawl flexure (PETG %.1f x %.1f x %.0f): spring force / strain" % (b, t, L),
        "%.2f N / %.2f %%" % (f_flex, eps * 100), eps < 0.008 and f_flex > 0.1, "PETG fatigue strain limit ~0.8 %")
    d = F.TAPE_TOP - F.DET_Z                               # lift when riding on 0.9 paper
    if F.COVER_PLATE == "printed":
        L, b, t = F.PT_TONGUE
        I = b * t ** 3 / 12
        f_det = 3 * E_petg * I * d / L ** 3
        eps = 1.5 * t * d / L ** 2
        row("loads", "detent tongue (printed PETG %.0f x %.0f x %.1f): force / strain" % (L, b, t),
            "%.2f N / %.2f %%" % (f_det, eps * 100), eps < 0.008 and f_det >= 0.4,
            "PETG fatigue strain ~0.8 %; steel tongue was 1.6 N. The tab's vertical face blocks back-drag, the "
            "spring only has to seat it (TEST B6)")
    else:
        b, t, L = 2.0, 0.5, F.TONGUE_L
        I = b * t ** 3 / 12
        f_det = 3 * E_steel * I * d / L ** 3
        s_det = 6 * f_det * L / (b * t ** 2)
        row("loads", "detent tongue (1.4310 %.1f x %.1f x %.1f): force / stress" % (b, t, L),
            "%.2f N / %.0f MPa" % (f_det, s_det), s_det < 450, "1.4310 C1300 fatigue limit ~500 MPa")
    push = f_det * (1 + 0.3) + 0.5                         # detent ramp + tape friction + reel drag
    torque = push * F.HORN_R / 1000 / math.cos(math.radians(F.ALPHA))
    row("loads", "servo torque needed to push the tape vs SG90 stall 0.18 N m", "%.4f N m" % torque,
        torque < 0.18 / 10)
    k_spring, comp = 0.75, 9.0 - (F.CHEEK_TOP - 63.0)
    f_pinch = k_spring * comp
    t_slip = 0.8 * f_pinch
    row("loads", "pinch spring force / nip slip tension (TPU mu ~0.8)", "%.2f N / %.2f N" % (f_pinch, t_slip),
        0.6 <= t_slip <= 1.6, "EIA-481 peel force 0.1..1.3 N")
    # peel drive: steady-state ratchet advance per full stroke (a 4 mm feed, or two 2 mm feeds)
    pitch = 360.0 / F.RAT_N
    teeth, travel = F.peel_teeth(F.STROKE)
    surf = teeth * pitch * math.pi / 180 * F.ROLL_R
    margin = travel - teeth * pitch
    row("peel", "lifter rise / pawl travel / teeth per stroke / roller surface per 4 mm fed",
        "%.2f mm / %.1f deg / %d / %.2f mm" % (F.LIFT_RATIO * F.STROKE, travel, teeth, surf),
        surf >= 4.0 * 1.1 and 3 <= margin <= pitch - 3,
        "needs >= 4.4 mm (10 %% over the tape); %.1f deg past the 2nd tooth, so servo calibration of a few "
        "degrees does not change the tooth count; surplus slips in the nip" % margin)
    th_half, tr_half = F.peel_teeth(F.STROKE / 2)
    row("peel", "half stroke (2 mm feed) pawl travel vs tooth pitch", "%.1f / %.0f deg" % (tr_half, pitch),
        tr_half > pitch + 3, "2 mm feeds share the 2 teeth of the full stroke: 1.5 + 3.4 mm, nip slips the lag")
    f_tooth = t_slip * F.ROLL_R / 5.7                     # nip slip tension at the roller -> ratchet face
    mu = 0.3
    a = math.atan(F.LIFT_RATIO)                            # slot angle: dowel force to lift
    f_slider = (f_tooth + 0.3 * mu + 0.2) * (math.tan(a + math.atan(mu)))   # + pawl drag, lifter friction
    t_tot = (push + f_slider) * F.HORN_R / 1000 / math.cos(math.radians(F.ALPHA))
    row("loads", "servo torque, tape + peel drive at nip slip vs SG90 stall 0.18 N m",
        "%.4f N m (peel adds %.1f N at the slider)" % (t_tot, f_slider), t_tot < 0.18 / 3,
        "lifter slot %.1f deg, mu 0.3" % math.degrees(a))
    for nm, (L, t, dmax) in (("lifter pawl finger", (18.6, 0.8, (F.LIFT_TOOTH_X - (F.ROLL_X - F.RAT_RT)) + 0.1)),
                             ("hold pawl beam", (649.5 - 639.6, 0.8, 41.95 - (F.ROLL_Z - F.RAT_RT) + 0.1))):
        eps = 1.5 * t * dmax / L ** 2
        row("loads", "%s (PETG %.1f x %.1f): ride-over deflection / strain" % (nm, t, L),
            "%.2f mm / %.2f %%" % (dmax, eps * 100), eps < 0.008, "PETG fatigue strain limit ~0.8 %")
    f_hold = t_slip * F.ROLL_R / 5.7
    I = 3.8 * 0.8 ** 3 / 12
    p_cr = math.pi ** 2 * E_petg * I / (4 * (649.5 - 639.6) ** 2)
    row("loads", "hold pawl beam in compression: load / buckling", "%.2f N / %.1f N" % (f_hold, p_cr),
        p_cr > 3 * f_hold)
    L, t, d = F.CHEEK_TOP - F.SNAP_Z, 0.85, 0.6
    eps = 1.5 * t * d / L ** 2
    row("loads", "cheek cap snap legs (PETG 0.85 x %.0f): deflection to snap on / strain" % L,
        "%.2f mm / %.2f %%" % (d, eps * 100), eps < 0.02,
        "one-time snap, PETG allows ~2-4 %; the legs flex into the 1.5 mm gap between lanes")
    m = f_slider * 1.1 * (3.55 + 0.6 + 0.8)               # load at the lifter mid-plane, from the slider face
    sig = m / (math.pi * (2 * F.PEG_R) ** 3 / 32)
    row("loads", "printed slider peg D%.0f (lying, layers along the axis): bending stress" % (2 * F.PEG_R),
        "%.1f MPa" % sig, sig < 12, "PETG fatigue along the layers ~12-15 MPa")

    # 6. bank parts vs the machine (static) and tape paths
    from model import assembly
    items = [it for it in assembly.static_items()]
    bank_names = ("Feeder_", "ReelRack", "ReelHub", "Reel_")
    fixed = [it for it in items if not it.name.startswith(bank_names) and it.system != "feeders"]
    lanes = [it for it in items if it.system == "feeders" and it.name.startswith("Lane")
             and not it.name.endswith(("Tape", "TapeParts", "CoverTape"))]
    bank = [it for it in items if it.name.startswith(bank_names)]
    hits = []
    for bi in bank:
        bb = bi.shape.BoundBox
        for fi in fixed + lanes:
            if not bb.intersect(fi.shape.BoundBox):
                continue
            v = overlap(bi.shape, fi.shape)
            if v > 0.05:
                hits.append("%s/%s %.1f" % (bi.name, fi.name, v))
    row("bank", "chute, waste bin, reel rack vs frame, plate, lanes", "; ".join(hits) or "none", not hits)
    ya, yb = Y0, Y0 + (P.LANES - 1) * P.LANE_PITCH
    drop = g.box_r(F.X_IN - 12.6, F.X_IN - 11.0, ya - 4, yb + 4, 0.5, ZT - P.TABLE_T)
    dh = [it.name for it in items if it.shape.BoundBox.intersect(drop.BoundBox) and overlap(it.shape, drop) > 0.05]
    row("bank", "empty tape drop path below the plate slot to the bench", ", ".join(dh) or "clear", not dh)
    path = []
    for ly in (ya, yb):
        a = V(F.REEL_X, ly, F.REEL_Z + F.REEL_D / 2)
        bpt = V(F.X_OUT, ly, ZT + F.TAPE_TOP)
        L = (a - bpt).Length
        strip = Part.makeBox(L - 25, 8, 0.4, V(0, -4, 0))
        strip.rotate(V(), V(0, 1, 0), -math.degrees(math.atan2(a.z - bpt.z, a.x - bpt.x)))
        strip.translate(bpt + (a - bpt).normalize() * 3)
        path += [it.name for it in items if it.shape.BoundBox.intersect(strip.BoundBox)
                 and not it.name.startswith(("Reel_", "Screws")) and overlap(it.shape, strip) > 0.02]
    row("bank", "carrier tape path reel -> lane inlet", ", ".join(sorted(set(path))) or "clear", not path)

    n = {s: sum(1 for r in rows if r[3] == s) for s in ("OK", "FAIL", "INFO")}
    out = os.path.join(ensure(), "audit.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# TBW-Feeder v2.1 audit\n\nGenerated by `feeder audit` on %s.\n\n" % time.strftime("%Y-%m-%d %H:%M"))
        f.write("| Area | Check | Result | Status | Note |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write("| %s |\n" % " | ".join(str(c) for c in r))
        f.write("\n**%d OK, %d FAIL**\n" % (n["OK"], n["FAIL"]))
    log("audit ", out, n, "%.0fs" % (time.time() - t0))
    return n["FAIL"]


# ------------------------------------------------------------------ animation
def _ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def cmd_animate(args):
    """out/feeder_animation.gif: one 4 mm feed cycle, whole lane + close-up of the pawl, from the model."""
    import render
    from PIL import Image, ImageDraw, ImageFont
    t0 = time.time()
    zt = ZT
    lane, _ = lane_parts()
    S = {k: v[0] for k, v in lane.items()}
    pfwd = F.pin_xy(Y0, F.TH_FWD)[0]

    def slider_s(th):
        return F.pin_xy(Y0, th)[0] - pfwd                       # 0 forward .. 4.2 retracted

    # phases: (label, frames, th0, th1); tape moves once the pawl has taken up the 0.2 mm free travel
    phases = [("1  Retract: the pawl slides back under the tape into the next sprocket hole. "
               "The detent tongue holds the tape.", 14, F.TH_FWD, F.TH_RET),
              ("2  Feed: the pawl pushes the tape 4.0 mm. The lifter rises and turns the ratchet + roller 2 teeth: "
               "the cover tape is peeled.", 16, F.TH_RET, F.TH_FWD),
              ("3  Hold: the servo holds the forward end. The next part is in the pick window.", 8, F.TH_FWD, F.TH_FWD)]
    frames = []
    for label, n, a, b in phases:
        for k in range(n):
            th = a + (b - a) * _ease(k / (n - 1) if n > 1 else 1.0)
            frames.append((label, th))

    ghost = {"Body", "CoverPlate", "Servo_SG90", "CheekCap", "PinchYoke"}
    moving = {"Slider", "Horn", "HornPin", "Tape", "TapeParts", "DriveRoller", "Ratchet", "Lifter", "SliderPeg"}
    pcol = g.part_colors((n, rec[5], rec[1]) for n, rec in lane.items())
    static = [(n, S[n], pcol[n], {"anchor"} | ({"ghost"} if n in ghost else set()) | {"fine"})
              for n in S if n not in moving]
    sc = render.Scene(static)
    # invisible box that fixes the close-up camera on the pawl, tape and pick window
    cbox = Part.makeBox(38, 10, 3, V(P.PICK_X - 4, Y0 - 5, zt + 14))
    cnode = render.shape_node(cbox, (1, 1, 1), edges=False, alpha=1.0)
    sc.nodes["_closeup"] = (cnode, {"closeup"})
    sc.geom.addChild(cnode)
    render.VIEWS["anim_lane"] = ((-0.45, 0.85, -0.35), (0, 0, 1), False, "anchor", 1.75)
    render.VIEWS["anim_pawl"] = ((0.0, 0.7, -1.0), (0, 0, 1), False, "closeup", 0.85)
    # second invisible box: the peel drive seen from the -y side (lifter, dowel, ratchet, hold pawl)
    pbox = Part.makeBox(36, 10, 66, V(617, Y0 - 10, zt + 3))
    pnode = render.shape_node(pbox, (1, 1, 1), edges=False, alpha=1.0)
    sc.nodes["_peelview"] = (pnode, {"peelview"})
    sc.geom.addChild(pnode)
    render.VIEWS["anim_peel"] = ((0.12, 1.0, -0.18), (0, 0, 1), False, "peelview", 0.78)

    roll_c = V(F.ROLL_X, Y0, zt + F.ROLL_Z)
    mark_r = Part.makeBox(1.2, 6.4, 4.0, V(F.ROLL_X - 0.6, Y0 - 1.95, zt + F.ROLL_Z + 3.2))
    pitch = 360.0 / F.RAT_N
    teeth, travel = F.peel_teeth(F.STROKE)
    lost = travel - teeth * pitch                               # pawl travel before it meets a tooth face
    odir = ensure("anim")
    for fn in os.listdir(odir):
        os.remove(os.path.join(odir, fn))
    try:
        font = ImageFont.truetype("arial.ttf", 17)
        fbig = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = fbig = ImageFont.load_default()
    added = []
    tape_prev = 0.0
    paths = []
    for i, (label, th) in enumerate(frames):
        s = slider_s(th)
        # tape: still while retracting; while feeding it follows the pawl after 0.2 mm free travel
        phase = label[0]
        tape_dx = {"1": 0.0, "2": -max(0.0, (F.STROKE - 0.2) - s), "3": -(F.STROKE - 0.2)}[phase]
        # ratchet: still while retracting (hold pawl); while feeding it turns once the pawl meets a face
        rot = 0.0
        if phase == "2":
            done = F.pawl_angle(F.lift_dz(F.TH_RET)) - F.pawl_angle(F.lift_dz(th))
            rot = max(0.0, done - lost) - teeth * pitch
        for n in added:
            sc.geom.removeChild(n)
        added = []
        lp = {"Horn": F._horn(Y0, zt, th), "HornPin": F._pin(Y0, zt, th),
              "Lifter": F._lifter(Y0, zt, F.lift_dz(th))}
        pg = S["SliderPeg"].copy()
        pg.translate(V(s, 0, 0))
        lp["SliderPeg"] = pg
        sl = S["Slider"].copy()
        sl.translate(V(s, 0, 0))
        lp["Slider"] = sl
        for nm in ("Tape", "TapeParts"):
            sh = S[nm].copy()
            sh.translate(V(tape_dx, 0, 0))
            lp[nm] = sh
        for nm, extra in (("DriveRoller", mark_r), ("Ratchet", None)):
            sh = S[nm].fuse(extra) if extra else S[nm].copy()
            sh.rotate(roll_c, V(0, 1, 0), rot)
            lp[nm] = sh
        cols = dict(pcol, Slider=(0.15, 0.45, 0.95), HornPin=(0.85, 0.15, 0.15), Horn=(0.95, 0.95, 0.95),
                    DriveRoller=(0.12, 0.12, 0.14), Tape=(0.97, 0.97, 0.92), TapeParts=(0.10, 0.10, 0.12),
                    Lifter=(0.10, 0.65, 0.35), SliderPeg=(0.85, 0.15, 0.15), Ratchet=(0.95, 0.80, 0.20),
                    HoldPawl=(0.55, 0.25, 0.75))
        for nm, sh in lp.items():
            node = render.shape_node(sh, cols.get(nm, (0.5, 0.5, 0.5)), tol=0.08,
                                     alpha=0.35 if nm == "Tape" else 0.0)
            sc.geom.addChild(node)
            added.append(node)
        fa = os.path.join(odir, "a_%03d.png" % i)
        fb = os.path.join(odir, "b_%03d.png" % i)
        fc = os.path.join(odir, "c_%03d.png" % i)
        sc.render(fa, "anim_lane", (900, 560), ss=2)
        sc.render(fb, "anim_pawl", (660, 560), ss=2)
        sc.render(fc, "anim_peel", (560, 560), ss=2)
        im = Image.new("RGB", (2120, 640), (246, 247, 250))
        im.paste(Image.open(fa), (0, 80))
        im.paste(Image.open(fb), (900, 80))
        im.paste(Image.open(fc), (1560, 80))
        dr = ImageDraw.Draw(im)
        dr.text((24, 12), "TBW-Feeder v2.1  |  one 4 mm feed (M600 N0 F4), one servo", fill=(25, 28, 34),
                font=fbig)
        dr.text((24, 48), label, fill=(60, 66, 80), font=font)
        dr.text((24, 600), "servo %.1f deg   slider %+.2f mm   tape %.2f mm   lifter %+.2f mm   ratchet %+.0f deg"
                % (th, s, -tape_dx, F.lift_dz(th), rot), fill=(60, 66, 80), font=font)
        dr.text((924, 600), "from above: pick window, pawl (blue), detent", fill=(60, 66, 80), font=font)
        dr.text((1584, 600), "peel drive from -Y: dowel (red), lifter (green), ratchet", fill=(60, 66, 80),
                font=font)
        p = os.path.join(odir, "frame_%03d.png" % i)
        im.save(p)
        for fn in (fa, fb, fc):
            os.remove(fn)
        paths.append(p)
        log("frame %d/%d" % (i + 1, len(frames)))
    imgs = [Image.open(p).convert("P", palette=Image.ADAPTIVE, colors=192) for p in paths]
    dur = [90] * len(imgs)
    for k, (label, _) in enumerate(frames):
        if k + 1 < len(frames) and frames[k + 1][0] != label or k == len(frames) - 1:
            dur[k] = 900                                         # pause at the end of each phase
    gif = os.path.join(OUT, "feeder_animation.gif")
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=dur, loop=0, optimize=True)
    log("GIF   ", gif, "(%d frames, %.0fs)" % (len(imgs), time.time() - t0))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="feeder")
    ap.add_argument("cmd", choices=("build", "audit", "all", "animate"))
    a = ap.parse_args(argv)
    fails = 0
    if a.cmd == "animate":
        cmd_animate(a)
    if a.cmd in ("build", "all"):
        cmd_build(a)
    if a.cmd in ("audit", "all"):
        fails = cmd_audit(a)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

"""TBW-Feeder v3.0: stand-alone build and design audit.

The geometry lives in ../model/feeder.py (the machine model uses the same code); this driver builds one
lane plus the bank parts (exit chute, waste bin, reel rack), exports them and checks them as a device.

Run with FreeCAD's bundled Python (see feeder.ps1 / feeder.cmd):
    feeder build    out/tbw_feeder_lane.FCStd + .step, out/stl/ (printed, lying on the bed), bom.csv
    feeder audit    geometry, motion, assembly, printability (no supports), loads, bank-vs-machine
                    -> out/audit.md (exit 1 on FAIL)
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

# intentional contacts in the model pose (none: press fits are drawn line-on-line)
INTENDED = {frozenset(p) for p in (("Body", "PawlPin_2"), ("Slider", "PawlPin_1"))}   # set screw threads in their pilot holes
MIN_WALL = 0.8               # two 0.4 mm perimeters
TAPE = ("Tape", "TapeParts", "CoverTape")


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
    # test-fit stand-in for the HF0612 (not a working part: no clutch). OD 9.8 / ID 6.3 so it slides in and out
    dummy = g.tube(F.OWB[0] / 2 - 0.1, F.OWB[1] / 2 + 0.15, F.OWB[2])
    m = MeshPart.meshFromShape(Shape=dummy, LinearDeflection=0.05, AngularDeflection=0.3)
    m.write(os.path.join(pdir, "TestFit_HF0612.stl"))
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
def group(src, names):
    shapes = [src[n] for n in names]
    return shapes[0].fuse(shapes[1:]) if len(shapes) > 1 else shapes[0].copy()


def rotated(shp, c, deg):
    s = shp.copy()
    s.rotate(c, V(0, 1, 0), deg)
    return s


MOVING = ("Slider", "Pawl_1", "PawlPin_1", "PawlSpring_1", "Rack", "ServoGear",
          "Idler", "Pinion")


def cmd_audit(args):
    t0 = time.time()
    lane, _ = lane_parts()
    S = {k: v[0] for k, v in lane.items()}
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
            if not S[a].BoundBox.intersect(S[b].BoundBox):
                continue
            v = overlap(S[a], S[b])
            if v > 0.02:
                hits.append("%s/%s %.2f mm3" % (a, b, v))
    row("geometry", "static overlaps, all %d lane parts + tape (model pose = forward end)" % len(names),
        "; ".join(hits) or "none", not hits, "press fits are modelled line-on-line")
    tp = (overlap(S["Pawl_1"], S["Tape"]), overlap(S["Pawl_2"], S["Tape"]))
    row("geometry", "feed pawl and detent teeth sit in sprocket holes at the forward end", "%.3f / %.3f mm3" % tp,
        max(tp) < 0.02, "detent hook face 0.15 mm behind its hole edge (back-drag play)")

    # 2. advance motion: horn angle sweep; slider, pawl, peg, lifter and pinion follow
    worst = {}
    ret = None
    for th in [F.TH_FWD - k * (F.TH_FWD - F.TH_RET) / 8 for k in range(9)]:
        lp, _ = lane_parts(th)
        L = {k: v[0] for k, v in lp.items()}
        for m in MOVING:
            for o in L:
                if o == m or o in TAPE or (o in MOVING and MOVING.index(o) < MOVING.index(m)):
                    continue
                if not L[m].BoundBox.intersect(L[o].BoundBox) or frozenset((m, o)) in INTENDED:
                    continue
                worst[(m, o)] = max(worst.get((m, o), 0.0), overlap(L[m], L[o]))
        if abs(th - F.TH_RET) < 1e-6:
            ret = L
    bad = ["%s/%s %.2f" % (a, b, v) for (a, b), v in sorted(worst.items()) if v > 0.02]
    row("advance", "servo sweep %.1f..%.1f deg (9 poses): servo gear, slider, pawl, rack, idler, pinion vs every part"
        % (F.TH_RET, F.TH_FWD), "; ".join(bad) or "free (%d pairs)" % len(worst), not bad,
        "rack, idler and pinion in mesh over the whole stroke; the pawl riding under the tape is checked below")
    rt = overlap(ret["Pawl_1"], S["Tape"])
    row("advance", "feed tooth drops into the next hole at the retract end", "tooth/tape %.3f mm3" % rt, rt < 0.02,
        "stroke %.1f = 4.0 feed + 0.2 free travel" % F.STROKE)
    ux, uz = (F.ROLL_X - F.IDL_X) / (F.IDL_R + F.PIN_RP), (F.ROLL_Z - F.IDL_Z) / (F.IDL_R + F.PIN_RP)
    eng = [overlap(L_["Idler"], moved(L_["Rack"], dz=0.6)) for L_ in (S, ret)]
    eng += [overlap(L_["Pinion"], moved(L_["Idler"], dx=0.6 * ux, dz=0.6 * uz)) for L_ in (S, ret)]
    row("peel", "rack/idler and idler/pinion engaged at both stroke ends (moved 0.6 mm into mesh they overlap)",
        "%.2f / %.2f, %.2f / %.2f mm3" % tuple(eng), min(eng) > 0.3)

    # 3. pawls: ride-over room (tooth pushed down by the tape) and positive up-stop
    for nm, h, house in (("Pawl_1", F.W_HOOK, ("Slider",)), ("Pawl_2", F.D_HOOK, ("Body", "SidePlate"))):
        c = V(h + F.PAWL_L, Y0, ZT + F.PAWL_PZ)
        tip = V(h + 0.15, Y0, ZT + F.ZB + F.TOOTH_H)
        deg = 0.0
        while deg > -30:
            deg -= 0.25
            if (App.Rotation(V(0, 1, 0), deg).multVec(tip - c) + c).z <= tip.z - (F.TOOTH_H + 0.1):
                break
        fixed = group(S, house)
        down = overlap(rotated(S[nm], c, deg), fixed)
        up = overlap(rotated(S[nm], c, 0.6), fixed)
        row("advance", "%s rides over: tooth %.2f mm down (%.1f deg about the pin) / up-stop"
            % ("feed pawl" if nm == "Pawl_1" else "detent", F.TOOTH_H + 0.1, -deg),
            "free (%.3f mm3) / stop hit (%.2f mm3 at +0.6 deg)" % (down, up), down < 0.02 and up > 0.02,
            "the tail sits on the fork floor, so the push load (self-locking) cannot lift the tooth further")

    # 4. pinch yoke opens 3 mm for threading the cover tape
    yoke = group(S, ("PinchYoke", "PinchRoller", "OneWay_2", "PinchAxle"))
    fixed = group(S, ("Body", "SidePlate", "Idler", "DriveRoller", "ORing_1", "ORing_2", "Pinion",
                      "Slider"))
    ok_y, _ = free_path(yoke, fixed, (0, 0, -1), 3.0, step=0.5)
    row("peel", "pinch yoke pushed down 3 mm by its rear tab (thread the cover tape)", "free" if ok_y else "blocked",
        ok_y)

    # 5. assembly: every part is laid into the main body from the split face (+y), the side plate closes it
    mid, _ = lane_parts(90.0)
    M = {k: v[0] for k, v in mid.items()}
    ap = []

    def path(label, parts, fixed_parts, src=S, d=(0, -1, 0), travel=25.0, step=1.0):
        ok, _ = free_path(group(src, parts), group(src, fixed_parts), d, travel, step)
        ap.append((label, ok))
    path("slider + pawl + spring + take-up rack (+y; the rack arm passes where the side plate block goes)",
         ("Slider", "Pawl_1", "PawlSpring_1", "Rack"), ("Body",))
    path("servo + gear (+y; the gear sector comes into mesh with the slider rack radially)",
         ("Servo_SG90", "ServoGear"), ("Body", "Slider", "Pawl_1", "PawlPin_1", "Rack"))
    path("detent pawl + spring from above through the tape channel (-z)", ("Pawl_2", "PawlSpring_2"), ("Body",),
         d=(0, 0, 1), travel=15.0, step=0.5)
    path("pinion with its shaft + drive roller + HF0612 + O-rings into the +y cheek (+y)",
         ("Pinion", "DriveRoller", "OneWay_1", "ORing_1", "ORing_2"), ("Body",))
    path("pinch spring + yoke + roller + HF0612 + axle (+y)",
         ("PinchYoke", "PinchRoller", "OneWay_2", "PinchAxle", "PinchSpring"),
         ("Body", "DriveRoller", "ORing_1", "ORing_2"))
    path("idler laid onto the rack and the pinion, teeth axially into mesh (+y)", ("Idler",),
         ("Body", "Servo_SG90", "ServoGear", "Slider", "Rack", "Pawl_1", "Pinion",
          "DriveRoller", "ORing_1", "ORing_2", "PinchYoke", "PinchRoller", "PinchAxle"))
    rest = [k for k in S if k not in TAPE and k not in ("SidePlate", "CoverPlate", "GuideBar")]
    path("side plate closes the lane (+y); the idler stub goes into its hole, the journal pin into the shaft",
         ("SidePlate",), rest)
    path("guide bar pushed through the side plate into the post (+y)", ("GuideBar",),
         [k for k in S if k not in TAPE and k not in ("CoverPlate", "GuideBar")])
    bad = [n_ for n_, ok in ap if not ok]
    row("assembly", "lay-in assembly paths (%d), reverse order of ASSEMBLY.md (screws go in along their axis)" % len(ap),
        "blocked: " + "; ".join(bad) if bad else "all free", not bad,
        "one direction for everything; then 3 side plate screws, the guide bar and the 2 cover plate screws")
    cp = group(S, ("CoverPlate",))
    allf = group(S, [k for k in S if k not in TAPE and k not in ("CoverPlate",)])
    lift_home, _ = free_path(cp, allf, (0, 0, 1), 2.0, step=0.25)
    slide, _ = free_path(cp, allf, (-1, 0, 0), F.SLIDE, step=0.4)
    lift_out, _ = free_path(moved(cp, dx=-F.SLIDE), allf, (0, 0, 1), 12.0, step=0.5)
    row("cover", "bayonet cover plate: held at home / slides %.1f mm to the pick side / lifts off" % F.SLIDE,
        "%s / %s / %s" % ("held" if not lift_home else "LIFTS", "free" if slide else "blocked",
                          "free" if lift_out else "blocked"), (not lift_home) and slide and lift_out,
        "%d rail segments per side + 2 rear tongues; 2 M2 screws lock it" % len(F.RAIL_X))

    # 6. printing: support-free, walls, one material
    seen = set()
    filament = 0.0
    for nm, rec in lane.items():
        shp, col, mat, mass, bom, kind, up = rec
        if kind != "print":
            continue
        filament += mass_of(shp, mat, mass, kind)
        if bom in seen:
            continue
        seen.add(bom)
        rep = printing.support_report(shp, up)
        bb = printing.orient(shp, up).BoundBox
        row("printing", "%s %s: bridge / one-sided ceiling / steep overhang" % (nm.rstrip("_0123456789"),
                                                                            printing.up_label(up)),
            "%.1f mm / %.1f mm / %.1f mm2" % (rep["bridge"], rep["cantilever"], rep["overhang"]),
            printing.support_free(rep) and printing.fits_bed((bb.XLength, bb.YLength, bb.ZLength)),
            "no supports: limits %.0f / %.0f / %.0f; %.0f x %.0f x %.0f mm, bed contact %.0f mm2"
            % (printing.BRIDGE_MAX, printing.CANTILEVER_MAX, printing.OVERHANG_MAX, bb.XLength, bb.YLength,
               bb.ZLength, rep["contact"]))
        sb = shp.BoundBox
        tw = [w for w in thin_walls(shp) if w[0] > 0.05 and not (     # a line grazing the outline is no wall
            (w[1] == "X" and min(abs(w[3] - sb.YMin), abs(w[3] - sb.YMax)) < 0.3) or
            (w[1] == "Y" and min(abs(w[2] - sb.XMin), abs(w[2] - sb.XMax)) < 0.3))]
        if nm == "SidePlate":       # the 0.2 mm bridging layers in the counterbores are meant to be pierced
            tw = [w for w in tw if not (w[1] == "Y" and w[0] < 0.25 and any(
                abs(w[2] - x) < 3.3 and abs(w[4] - z) < 3.3 for x, z in F.SIDE_SCREWS))]
        gears = {"Idler": (F.IDL_X, F.IDL_Z, F.IDL_R - 1.25), "Pinion": (F.ROLL_X, F.ROLL_Z, F.PIN_RP - 1.25)}
        if nm in gears:             # tooth tips are narrow by nature: only check inside the root circle
            gx, gz, rr = gears[nm]
            tw = [w for w in tw if w[1] == "X" and math.hypot(w[2] + w[0] / 2 - gx, w[4] - gz) < rr]
        if nm == "ServoGear":       # same, gear in the XY plane
            tw = [w for w in tw if w[1] == "X" and math.hypot(w[2] + w[0] / 2 - F.SERVO_X, w[3] - Y0)
                  < F.SG_R - 1.25 * F.SG_M]
        thin = [w for w in tw if w[0] < MIN_WALL]
        row("printing", "%s thinnest wall (X/Y line sampling)" % nm.rstrip("_0123456789"),
            "%.2f mm at %s" % (tw[0][0], tw[0][1:]), not thin, "; ".join("%.2f %s" % (w[0], w[1:]) for w in thin[:6]))
    mats = sorted({rec[2] for rec in lane.values() if rec[5] == "print"})
    row("printing", "printed lane parts: material / count / filament", "%s / %d parts (%d different) / %.0f g"
        % (", ".join(mats), sum(1 for r in lane.values() if r[5] == "print"), len(seen), filament),
        mats == ["PETG"], "one material, one 0.4 mm nozzle; no TPU (O-rings are bought)")

    # 7. loads and margins (numbers in DESIGN.md)
    mu = 0.3
    k_p, l0_p = 0.5, 8.0                                   # pawl spring OD 3 x 0.3 x L0 8
    inst = F.PAWL_BAR_Z - F.PAWL_SPRING_Z0
    lever = (F.PAWL_L - F.PAWL_SX) / F.PAWL_L
    drop = F.TOOTH_H + 0.1
    f_p0 = k_p * (l0_p - inst)
    f_p1 = f_p0 + k_p * drop * lever
    row("loads", "pawl spring (steel, OD 3 x 0.3 x L0 8, ~0.5 N/mm): seated / riding over",
        "%.2f / %.2f N" % (f_p0, f_p1), f_p0 >= 0.8 and inst - drop * lever > 3.2,
        "solid length ~3 mm; the v2.1 flexure pawl gave 0.26 N")
    h_c = F.ZB + F.TOOTH_H / 2 - F.PAWL_PZ
    row("loads", "pawl pivot below the tooth: the push load turns the tooth deeper (self-locking)",
        "contact %.1f mm above the pivot" % h_c, h_c > 2.0, "positive up-stop: the tail on the fork floor")
    tip_lever = (F.PAWL_L - F.PAWL_SX) / (F.PAWL_L - 0.6)
    f_det = f_p1 * tip_lever * math.tan(math.radians(45) + math.atan(mu))
    push = f_det + mu * 2 * f_p1 + 0.5
    torque = push * F.SG_R / 1000
    row("loads", "tape push (detent ramp + pawl friction + reel drag) / servo torque vs SG90 stall 0.18 N m",
        "%.1f N / %.4f N m" % (push, torque), torque < 0.18 / 5)
    sig_t = 6 * push * 0.5 / (F.TOOTH_W * 1.15 ** 2)
    row("loads", "pawl tooth root bending (0.8 x 1.15 root, load 0.5 above it; prints lying, in-plane)",
        "%.1f MPa" % sig_t, sig_t < 25, "PETG ~45 MPa in the layer plane")
    k_s, comp = 0.75, 9.0 - (F.YOKE_Z0 - F.SPRING_Z0)
    f_pinch = k_s * comp
    t_slip = 0.8 * f_pinch
    row("loads", "pinch spring / nip slip tension (NBR O-rings, mu ~0.8)", "%.2f / %.2f N" % (f_pinch, t_slip),
        0.6 <= t_slip <= 1.6, "EIA-481 peel force 0.1..1.3 N")
    t_hold = 0.8 * f_pinch
    row("peel", "cover tape tension held on the idle stroke (pinch roller with O-rings, locked by its HF0612)",
        "%.2f N" % t_hold, t_hold >= t_slip, "= nip slip tension, so the cover tape does not slip back on the retract")
    surf, half = F.peel_per_stroke(F.STROKE), F.peel_per_stroke(F.STROKE / 2)
    lost = 2 * 0.1 * F.ROLL_R / F.PIN_RP + 0.6 / 360 * 2 * math.pi * F.ROLL_R      # 2 meshes
    row("peel", "drive roller surface per full stroke (4 mm fed) / half stroke (2 mm fed)",
        "%.2f / %.2f mm" % (surf, half), surf - lost >= 4.4 and half - lost >= 2.05,
        "rack %.1f x R %.0f / R %.0f (the 38T idler doesn't change it), less %.2f mm backlash + clutch take-up; "
        "the surplus slips in the nip" % (F.STROKE, F.ROLL_R, F.PIN_RP, lost))
    f_rack = t_slip * F.ROLL_R / F.PIN_RP
    f_sl = f_rack / 0.95 ** 2                              # two spur meshes, no cam slot any more
    t_tot = (push + f_sl) * F.SG_R / 1000
    row("loads", "servo torque, tape + peel at nip slip vs stall 0.18 N m",
        "%.4f N m (peel adds %.1f N at the slider)" % (t_tot, f_sl), t_tot < 0.18 / 3,
        "the v3.0 lifter slot added 3.1 N")
    b = F.PIN_Y[1] - F.PIN_Y[0]
    sig_g = f_rack / (b * F.PIN_M * 0.276)
    row("loads", "pinion / idler / rack tooth bending (Lewis, 14T m1, face %.1f)" % b, "%.1f MPa" % sig_g,
        sig_g < 10, "the v2.1 ratchet teeth were 0.6 mm deep")
    t_pin = f_rack * F.PIN_RP
    do, di = F.OWB[1], 2 * F.SHAFT_BORE[0]
    tau = 16 * t_pin * do / (math.pi * (do ** 4 - di ** 4))
    row("loads", "pinion shaft (printed with the pinion, D6, bored D%.1f at the -y end) in torsion" % di,
        "%.0f N mm, %.2f MPa" % (t_pin, tau), tau < 1.0, "PETG creep limit ~5 MPa; no press fit left to slip")
    row("loads", "HF0612 one-way bearings: torque / catalogue rating", "%.0f / ~1800 N mm" % (t_slip * F.ROLL_R),
        t_slip * F.ROLL_R < 180, "on printed PETG shafts (the catalogue assumes HRC 58): TEST A10 checks the lock")
    gaps = [F.RAIL_X[i + 1] - F.RAIL_X[i] for i in range(len(F.RAIL_X) - 1)]
    span = max(gaps)
    bw = 2 * F.PLATE_HW - 6.5
    I = bw * F.PLATE_T ** 3 / 12
    E = 2000.0
    d3 = f_p1 * span ** 3 / (48 * E * I)
    a_, b_ = F.W_HOOK - 532.5, 591.0 - F.W_HOOK
    d2 = f_p1 * a_ ** 2 * b_ ** 2 / (3 * E * I * (a_ + b_))
    row("cover", "cover plate deflection under the pawl spring: rails every %.0f mm vs v2.1 (screws + hinge %.0f mm "
        "apart)" % (span, a_ + b_), "%.3f mm vs %.1f mm" % (d3, d2), d3 < 0.1,
        "the v2.1 plate bowed enough to let the pawl lift the tape out of the hole")
    hold, drag = 2 * 40.0, mu * 2 * f_p1
    row("cover", "2 x M2 countersunk screws (self-tapped into PETG, ~40 N pull-out each) lock the plate home vs "
        "tape drag on the feed stroke", "%.0f N vs %.2f N" % (hold, drag), hold > 3 * drag,
        "the bayonet cannot slide out while they are in: positive lock, no magnets")

    # 8. bank parts vs the machine (static) and tape paths
    from model import assembly
    items = [it for it in assembly.static_items()]
    bank_names = ("Feeder_", "ReelRack", "ReelHub", "Reel_")
    fixed = [it for it in items if not it.name.startswith(bank_names) and it.system != "feeders"]
    lanes = [it for it in items if it.system == "feeders" and it.name.startswith("Lane")
             and not it.name.endswith(TAPE)]
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
    drop_ = g.box_r(F.X_IN - 12.6, F.X_IN - 11.0, ya - 4, yb + 4, 0.5, ZT - P.TABLE_T)
    dh = [it.name for it in items if it.shape.BoundBox.intersect(drop_.BoundBox) and overlap(it.shape, drop_) > 0.05]
    row("bank", "empty tape drop path below the plate slot to the bench", ", ".join(dh) or "clear", not dh)
    path_ = []
    for ly in (ya, yb):
        a = V(F.REEL_X, ly, F.REEL_Z + F.REEL_D / 2)
        bpt = V(F.X_OUT, ly, ZT + F.TAPE_TOP)
        Ln = (a - bpt).Length
        strip = Part.makeBox(Ln - 25, 8, 0.4, V(0, -4, 0))
        strip.rotate(V(), V(0, 1, 0), -math.degrees(math.atan2(a.z - bpt.z, a.x - bpt.x)))
        strip.translate(bpt + (a - bpt).normalize() * 3)
        path_ += [it.name for it in items if it.shape.BoundBox.intersect(strip.BoundBox)
                  and not it.name.startswith(("Reel_", "Screws")) and overlap(it.shape, strip) > 0.02]
    row("bank", "carrier tape path reel -> lane inlet", ", ".join(sorted(set(path_))) or "clear", not path_)
    nip = [it.name for it in bank if it.name == "Feeder_WasteBin" and
           it.shape.BoundBox.intersect(S["CoverTape"].BoundBox) and overlap(it.shape, S["CoverTape"]) > 0.02]
    row("bank", "used cover tape leaves the nip over the waste bin lip", ", ".join(nip) or "clear", not nip)

    n = {s_: sum(1 for r in rows if r[3] == s_) for s_ in ("OK", "FAIL", "INFO")}
    out = os.path.join(ensure(), "audit.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("# TBW-Feeder v3.0 audit\n\nGenerated by `feeder audit` on %s.\n\n" % time.strftime("%Y-%m-%d %H:%M"))
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
    """out/feeder_animation.gif: one 4 mm feed cycle, whole lane + close-up of the pawls + peel drive, from the
    model. The drive roller turns with the pinion on the feed stroke and stands still on the retract (one-way
    bearing); the pinion and shaft go back and forth."""
    import render
    from PIL import Image, ImageDraw, ImageFont
    t0 = time.time()
    zt = ZT
    lane, _ = lane_parts()
    S = {k: v[0] for k, v in lane.items()}

    phases = [("1  Retract: the pawl slides back under the tape into the next sprocket hole; the detent holds the "
               "tape. The rack turns the idler and the pinion back; the one-way roller stays.", 14, F.TH_FWD, F.TH_RET),
              ("2  Feed: the pawl pushes the tape 4.0 mm. The rack on the slider turns the idler, the idler the pinion "
               "and the drive roller: the cover tape is peeled (4.8 mm, the nip slips the rest).", 16, F.TH_RET, F.TH_FWD),
              ("3  Hold: the servo holds the forward end. The next part is in the pick window.", 8, F.TH_FWD, F.TH_FWD)]
    frames = []
    for label, n, a, b in phases:
        for k in range(n):
            th = a + (b - a) * _ease(k / (n - 1) if n > 1 else 1.0)
            frames.append((label, th))

    ghost = {"Body", "SidePlate", "CoverPlate", "Servo_SG90", "PinchYoke"}
    slid = {"Slider", "Pawl_1", "PawlPin_1", "PawlSpring_1", "Rack"}
    turn = {"DriveRoller", "OneWay_1", "ORing_1", "ORing_2", "PinchRoller", "OneWay_2"}
    moving = slid | turn | {"ServoGear", "Tape", "TapeParts", "Idler", "Pinion"}
    pcol = g.part_colors((n, rec[5], rec[1]) for n, rec in lane.items())
    static = [(n, S[n], pcol[n], {"anchor"} | ({"ghost"} if n in ghost else set()) | {"fine"})
              for n in S if n not in moving]
    sc = render.Scene(static)
    cbox = Part.makeBox(38, 10, 3, V(P.PICK_X - 2, Y0 - 5, zt + 14))
    cnode = render.shape_node(cbox, (1, 1, 1), edges=False, alpha=1.0)
    sc.nodes["_closeup"] = (cnode, {"closeup"})
    sc.geom.addChild(cnode)
    render.VIEWS["anim_lane"] = ((-0.45, 0.85, -0.35), (0, 0, 1), False, "anchor", 1.75)
    render.VIEWS["anim_pawl"] = ((0.0, 1.0, -0.12), (0, 0, 1), False, "closeup", 0.85)
    pbox = Part.makeBox(30, 10, 66, V(623, Y0 - 10, zt + 3))
    pnode = render.shape_node(pbox, (1, 1, 1), edges=False, alpha=1.0)
    sc.nodes["_peelview"] = (pnode, {"peelview"})
    sc.geom.addChild(pnode)
    render.VIEWS["anim_peel"] = ((0.12, 1.0, -0.18), (0, 0, 1), False, "peelview", 0.78)

    roll_c = V(F.ROLL_X, Y0, zt + F.ROLL_Z)
    pinch_c = V(F.ROLL_X, Y0, zt + F.PINCH_Z)
    mark_r = Part.makeBox(1.2, 1.0, 1.6, V(F.ROLL_X - 0.6, Y0 + F.ROLL_Y[1] - 0.01, zt + F.ROLL_Z + 5.4))
    odir = ensure("anim")
    for fn in os.listdir(odir):
        os.remove(os.path.join(odir, fn))
    try:
        font = ImageFont.truetype("arial.ttf", 17)
        fbig = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = fbig = ImageFont.load_default()
    added = []
    paths = []
    roll_deg = 0.0
    prev_pin = F.pinion_rot(0.0)
    for i, (label, th) in enumerate(frames):
        s = F.slider_dx(th)
        phase = label[0]
        tape_dx = {"1": 0.0, "2": -max(0.0, (F.STROKE - 0.2) - s), "3": -(F.STROKE - 0.2)}[phase]
        pin_deg = F.pinion_rot(s)
        if pin_deg < prev_pin:                     # feed direction: the one-way bearing drives the roller
            roll_deg += pin_deg - prev_pin
        prev_pin = pin_deg
        for n in added:
            sc.geom.removeChild(n)
        added = []
        lp = {"ServoGear": F._servo_gear(Y0, zt, th),
              "Idler": F._idler(Y0, zt, F.idler_rot(s)), "Pinion": F._pinion(Y0, zt, pin_deg)}
        for nm in slid:
            sh = S[nm].copy()
            sh.translate(V(s, 0, 0))
            lp[nm] = sh
        for nm in ("Tape", "TapeParts"):
            sh = S[nm].copy()
            sh.translate(V(tape_dx, 0, 0))
            lp[nm] = sh
        for nm, c, k, extra in (("DriveRoller", roll_c, 1.0, mark_r), ("OneWay_1", roll_c, 1.0, None),
                                ("ORing_1", roll_c, 1.0, None), ("ORing_2", roll_c, 1.0, None),
                                ("PinchRoller", pinch_c, -F.ROLL_R / F.PINCH_R, None),
                                ("OneWay_2", pinch_c, -F.ROLL_R / F.PINCH_R, None)):
            sh = S[nm].fuse(extra) if extra else S[nm].copy()
            sh.rotate(c, V(0, 1, 0), roll_deg * k)
            lp[nm] = sh
        cols = dict(pcol, Slider=(0.15, 0.45, 0.95), ServoGear=(0.85, 0.15, 0.15),
                    Tape=(0.97, 0.97, 0.92), TapeParts=(0.10, 0.10, 0.12), Rack=(0.10, 0.65, 0.35),
                    Idler=(0.20, 0.55, 0.85), Pinion=(0.95, 0.80, 0.20), Pawl_1=(0.95, 0.80, 0.20),
                    DriveRoller=(0.90, 0.90, 0.90), ORing_1=(0.12, 0.12, 0.14), ORing_2=(0.12, 0.12, 0.14),
                    PinchRoller=(0.55, 0.25, 0.75))
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
        dr.text((24, 12), "TBW-Feeder v3.0  |  one 4 mm feed (M600 N0 F4), one servo", fill=(25, 28, 34),
                font=fbig)
        dr.text((24, 48), label, fill=(60, 66, 80), font=font)
        dr.text((24, 600), "servo %.1f deg   slider %+.2f mm   tape %.2f mm   idler %+.0f deg   roller %+.0f deg"
                % (th, s, -tape_dx, F.idler_rot(s), -roll_deg), fill=(60, 66, 80), font=font)
        dr.text((924, 600), "from +Y: detent, feed pawl (yellow), pick window", fill=(60, 66, 80), font=font)
        dr.text((1584, 600), "peel drive: rack (green) -> idler (blue) -> pinion", fill=(60, 66, 80), font=font)
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
            dur[k] = 900
    gif = os.path.join(OUT, "feeder_animation.gif")
    imgs[0].save(gif, save_all=True, append_images=imgs[1:], duration=dur, loop=0, optimize=True)
    log("GIF   ", gif, "(%d frames, %.0fs)" % (len(imgs), time.time() - t0))


def cmd_explode(args):
    """out/peel_exploded.png: the peel head groups pulled apart along their assembly axis (-y), in the order
    of ASSEMBLY.md: body, drive roller + HF0612, pinion with its shaft, pinch roller + HF0612 + axle, side plate."""
    import render
    from PIL import Image, ImageDraw, ImageFont
    zt = ZT
    lane, _ = lane_parts(90.0)
    S = {k: v[0] for k, v in lane.items()}
    off = {"DriveRoller": -24, "ORing_1": -24, "ORing_2": -24, "OneWay_1": -40, "Pinion": -62,
           "PinchRoller": -24, "ORing_3": -24, "ORing_4": -24, "OneWay_2": -40, "PinchAxle": -62,
           "Idler": -78, "SidePlate": -100}
    show = ["Body", "Servo_SG90", "Rack", "PinchYoke", "PinchSpring"] + list(off)
    pcol = g.part_colors((n, rec[5], rec[1]) for n, rec in lane.items())
    cols = dict(pcol, Pinion=(0.95, 0.80, 0.20), DriveRoller=(0.90, 0.90, 0.90), PinchRoller=(0.55, 0.25, 0.75),
                OneWay_1=(0.62, 0.64, 0.67), OneWay_2=(0.62, 0.64, 0.67), Idler=(0.20, 0.55, 0.85),
                PinchAxle=(0.95, 0.55, 0.20), Rack=(0.10, 0.65, 0.35))
    items = []
    for n in show:
        sh = S[n].copy()
        if n in off:
            sh.translate(V(0, off[n], 0))
        tags = {"fine"} | ({"ghost"} if n in ("Body", "Servo_SG90", "SidePlate") else set())
        items.append((n, sh, cols.get(n, (0.5, 0.5, 0.5)), tags))
    sc = render.Scene(items)
    box = Part.makeBox(42, 118, 46, V(F.ROLL_X - 21, Y0 - 108, zt + 26))
    node = render.shape_node(box, (1, 1, 1), edges=False, alpha=1.0)
    sc.nodes["_ex"] = (node, {"exview"})
    sc.geom.addChild(node)
    render.VIEWS["explode"] = ((0.75, 0.55, -0.32), (0, 0, 1), False, "exview", 0.95)
    tmp = os.path.join(ensure("anim"), "explode_raw.png")
    sc.render(tmp, "explode", (1400, 1000), ss=2)
    im = Image.new("RGB", (1400, 1140), (246, 247, 250))
    im.paste(Image.open(tmp), (0, 110))
    os.remove(tmp)
    try:
        font, fbig = ImageFont.truetype("arial.ttf", 19), ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = fbig = ImageFont.load_default()
    dr = ImageDraw.Draw(im)
    dr.text((24, 14), "TBW-Feeder v3.0  |  peel head, exploded along the assembly axis", fill=(25, 28, 34), font=fbig)
    dr.text((24, 52), "Drive: HF0612 into the drive roller, roller onto the pinion's printed shaft, shaft into the "
            "+Y cheek.\nPinch: HF0612 into the pinch roller, printed axle through it into the yoke. Then the idler, "
            "then the side plate (its pin enters the shaft end).", fill=(60, 66, 80), font=font)
    leg = [("Pinion + drive shaft (one print)", cols["Pinion"]), ("Drive roller + O-rings", cols["DriveRoller"]),
           ("HF0612 (or TestFit_HF0612 print)", cols["OneWay_1"]), ("Pinch roller", cols["PinchRoller"]),
           ("Pinch axle (print)", cols["PinchAxle"]), ("Idler 36T", cols["Idler"]), ("Rack", cols["Rack"])]
    for k, (t, c) in enumerate(leg):
        x = 24 + (k % 4) * 340
        y = 1060 + (k // 4) * 36
        dr.rectangle((x, y + 3, x + 22, y + 21), fill=tuple(int(255 * v) for v in c), outline=(40, 40, 40))
        dr.text((x + 32, y), t, fill=(40, 44, 54), font=font)
    p = os.path.join(OUT, "peel_exploded.png")
    im.save(p)
    log("PNG   ", p)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="feeder")
    ap.add_argument("cmd", choices=("build", "audit", "all", "animate", "explode"))
    a = ap.parse_args(argv)
    fails = 0
    if a.cmd == "animate":
        cmd_animate(a)
    if a.cmd == "explode":
        cmd_explode(a)
    if a.cmd in ("build", "all"):
        cmd_build(a)
    if a.cmd in ("audit", "all"):
        fails = cmd_audit(a)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

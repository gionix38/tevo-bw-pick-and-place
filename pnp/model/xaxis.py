"""X axis (TS 7.1, WP2), rev C.

MGN12 rails on both C-beams, one MGN12H per bridge end, dual GT2 belts on a jackshaft. Each belt is
an open belt: both ends are clamped in the toothed slot of the bridge end, so the belt pulls the bridge.
Tension: idler sliders in the right corner blocks (frame.py). Jackshaft bearings and the X motor sit
in the left corner blocks.
"""
import math

import FreeCAD as App

import params as P
from . import geom as g
from .item import Item

V = g.V

ROT_Z_TO_Y = App.Rotation(V(1, 0, 0), -90)    # +Z -> +Y
ROT_Z_TO_MY = App.Rotation(V(1, 0, 0), 90)    # +Z -> -Y
RAIL_FAST = "M3x8 SHCS + M3 T-nut (MGN rail)"
BLOCK_FAST = "M3x12 SHCS (MGN block)"
SCREW_COLOR = (0.22, 0.22, 0.24)


def _pl(shape, base, rot):
    shape.Placement = App.Placement(V(*base), rot)
    return shape


def belt_y(side):
    fw = P.derive()["frame_width"]
    return 12.5 if side == "Front" else fw - 12.5


def bridge_end():
    """Front bridge end: foot on one MGN12H + riser under the beam + belt clamp bracket.
    Returns (shape, fasteners); screws are recorded in geom._SCREWS. Rear = mirror."""
    d = P.derive()
    xr = P.mgn(P.X_RAIL)
    bx = d["bx_min"]
    ry = P.CB_SECTION[0] / 2
    zf = d["x_block_top"]
    zr = d["riser_top"]
    fz = zf + P.BRIDGE_PLATE[2]
    hx = P.BRIDGE_PLATE[0] / 2
    by = belt_y("Front")
    ztop_run = P.DRIVE_Z + d["pulley_pd"] / 2              # inner face of the upper belt run
    # rev E: every section is 44 mm wide in X, so the part is one Y-Z profile and prints on its side
    hx = 22.0
    foot = g.box_r(bx - hx, bx + hx, -12, 52, zf, fz)
    riser = g.box_r(bx - hx, bx + hx, d["bridge_y"][0], 52, fz, zr)
    brk = g.box_r(bx - hx, bx + hx, -12, -6, P.DRIVE_Z + 2, zf + 1)
    clamp = g.box_r(bx - hx, bx + hx, -6, by + 8, P.DRIVE_Z + 3, P.DRIVE_Z + 13)
    body = foot.fuse(riser).fuse(brk).fuse(clamp).removeSplitter()
    # toothed belt slot, open at both ends: the belt ends are pressed in from the two sides
    body = body.cut(g.box_r(bx - hx - 1, bx + hx + 1, by - 5.0, by + 5.0, ztop_run - 0.3, ztop_run + 1.7))
    fast = {}
    pts = [(bx + sx * xr["hole_c"] / 2, ry + sy * xr["hole_b"] / 2) for sx in (-1, 1) for sy in (-1, 1)]
    body = g.drill(body, "M3", [(x, y, zr) for x, y in pts], d=(0, 0, -1), depth=zr - zf + 1,
                   cbore=zr - fz + 3.0, screw=12)
    fast[BLOCK_FAST] = 4
    pts = [(bx + sx * 10, y, zf) for sx in (-1, 1) for y in (40.0, 48.0)]
    body = g.drill(body, "M5", pts, d=(0, 0, 1), depth=zr - zf + 1, cbore=zr - zf - 6, screw=10)
    fast["M5x10 SHCS + M5 T-nut (bridge beam)"] = 4
    body = g.drill(body, "M3", [(bx + sx * 12, -1.0, P.DRIVE_Z + 13) for sx in (-1, 1)], d=(0, 0, -1),
                   depth=12, cbore=0, screw=12)
    fast["M3x12 SHCS + nut (belt clamp)"] = 2
    return body, fast


def build_belts(pose):
    """Open X belts at the given pose: loop around pulley and idler, cut where both ends sit in the clamp."""
    d = P.derive()
    bx = d["bx_min"] + pose["X"]
    r = d["pulley_pd"] / 2
    items = []
    for side in ("Front", "Rear"):
        y = belt_y(side)
        belt = g.belt_loop((P.JACKSHAFT_X, y, P.DRIVE_Z), (P.CB_LEN + 10, y, P.DRIVE_Z), r, P.X_BELT_W,
                           normal=(0, 1, 0))
        belt = belt.cut(g.box_r(bx - 2, bx + 2, y - 6, y + 6, P.DRIVE_Z + r - 1, P.DRIVE_Z + r + 3))
        L = 2 * (P.CB_LEN + 10 - P.JACKSHAFT_X) + 2 * math.pi * r + 60
        items.append(Item("XBelt_" + side, belt, g.C_BELT, "x_axis", move="posed", mass=L * 0.0084 * P.X_BELT_W,
                          bom="GT2 belt 9 mm, open, %.0f mm (ends clamped in the bridge end)" % L, kind="buy",
                          check=False))
    return items


def build():
    d = P.derive()
    xr = P.mgn(P.X_RAIL)
    fw = d["frame_width"]
    ztop = d["cb_z"][1]
    bx = d["bx_min"]
    items = []
    rail_y = {"Front": P.CB_SECTION[0] / 2, "Rear": fw - P.CB_SECTION[0] / 2}
    n_rail = int(P.X_RAIL_LEN // xr["rail_pitch"])

    for side in ("Front", "Rear"):
        ry = rail_y[side]
        rail = g.mgn_rail(xr, P.X_RAIL_LEN)
        rail.translate(V(d["x_rail_x"][0], ry, ztop))
        items.append(Item("XRail_" + side, rail, g.C_STEEL, "x_axis", mass=xr["rail_gpm"] * P.X_RAIL_LEN,
                          bom="MGN12 rail %.0f mm" % P.X_RAIL_LEN, kind="buy", fasteners={RAIL_FAST: n_rail}))
        b = g.mgn_block(xr)
        b.translate(V(bx, ry, ztop))
        items.append(Item("XBlock_" + side, b, g.C_STEEL, "x_axis", move="bridge", mass=xr["blk_g"],
                          bom="MGN12H block", kind="buy"))

        g.take_screws()
        be, fast = bridge_end()
        scr = g.take_screws()
        if side == "Rear":
            be = be.mirror(V(0, fw / 2, 0), V(0, 1, 0))
            scr = scr.mirror(V(0, fw / 2, 0), V(0, 1, 0))
        items.append(Item("Bridge_End_" + side, be, g.C_ORANGE, "x_axis", move="bridge", mat="PETG",
                          bom="Bridge end: foot + riser + belt clamp (printed PETG-CF, 100% infill)",
                          kind="print", fasteners=fast))
        items.append(Item("Screws_BridgeEnd" + side, scr, SCREW_COLOR, "x_axis", move="bridge", mass=0,
                          check=False))

        pul = g.gt2_pulley(P.PULLEY_TEETH, P.X_BELT_W, 8.0, hub=7.0)
        if side == "Front":
            _pl(pul, (P.JACKSHAFT_X, 25.0, P.DRIVE_Z), ROT_Z_TO_MY)       # hub inward, clear of the 608
        else:
            _pl(pul, (P.JACKSHAFT_X, fw - 25.0, P.DRIVE_Z), ROT_Z_TO_Y)
        items.append(Item("XPulley_" + side, pul, g.C_ALU, "x_axis", mat="alu",
                          bom="GT2 pulley 20T, 8 mm bore, 9 mm belt", kind="buy"))
        y = belt_y(side)
        idl = g.idler(P.X_BELT_W)
        _pl(idl, (P.CB_LEN + 10, y - 5.0, P.DRIVE_Z), ROT_Z_TO_Y)
        items.append(Item("XIdler_" + side, idl, g.C_ALU, "x_axis", mat="alu",
                          bom="GT2 idler 20T, 5 mm bore, 9 mm belt", kind="buy"))
        axle = g.cyl(2.5, 21, (P.CB_LEN + 10, y - 10.5, P.DRIVE_Z), (0, 1, 0))
        items.append(Item("XIdlerAxle_" + side, axle, g.C_STEEL, "x_axis", mat="steel",
                          bom="Idler axle M5x25 + nyloc", kind="buy", check=False))

    y_a, y_b = -26.0, fw + 6.0
    items.append(Item("XJackshaft", g.cyl(P.JACKSHAFT_D / 2, y_b - y_a, (P.JACKSHAFT_X, y_a, P.DRIVE_Z), (0, 1, 0)),
                      g.C_STEEL, "x_axis", mat="steel", bom="Jackshaft 8 mm ground rod, %.0f mm" % (y_b - y_a),
                      kind="buy", check=False,
                      fasteners={"Shaft collar 8 mm": 2, "Grub screw M4 (pulley)": 4}))
    m = P.MOTORS["NEMA17_40"]
    body, shaft = g.nema(m)
    face_y = -40.0
    _pl(body, (P.JACKSHAFT_X, face_y - 0.01, P.DRIVE_Z), ROT_Z_TO_Y)
    _pl(shaft, (P.JACKSHAFT_X, face_y, P.DRIVE_Z), ROT_Z_TO_Y)
    items.append(Item("XMotor_NEMA17", body, g.C_DARK, "x_axis", mass=m["mass"],
                      bom="NEMA17 (stock bed motor) -> X", kind="stock"))
    items.append(Item("XMotor_Shaft", shaft, g.C_STEEL, "x_axis", mat="steel", check=False))
    cpl = g.cyl(9.5, 25, (P.JACKSHAFT_X, face_y + 6, P.DRIVE_Z), (0, 1, 0))
    items.append(Item("XCoupler_5x8", cpl, g.C_ALU, "x_axis", mass=18, bom="Coupler 5-8 mm", kind="buy",
                      check=False))

    sec = g.vslot_section(*P.BRIDGE_SECTION)
    beam = g.profile_along(sec, P.BRIDGE_LEN, "y", (bx - P.BRIDGE_SECTION[0] / 2, d["bridge_y"][0], d["bridge_z"][0]))
    items.append(Item("Bridge_Beam_40x80x550", beam, g.C_ALU_BLACK, "y_axis", move="bridge",
                      mass=P.PROFILE_KG_M["40x80"] * P.BRIDGE_LEN,
                      bom="V-slot 40x80x550 (stock), Y bridge", kind="stock"))
    return items

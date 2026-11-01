"""Y axis (TS 7.2, WP3), rev C.

MGN12 rail on the bridge face; stock GT2 6 mm belt, open, both ends clamped in the head carriage.
Y motor: machined Al bracket on the rear beam end (6 x M5 into the end taps, 4 x M5 into the side
slots, two gussets). Front idler: Al bracket with a belt window and two M3 tension screws pulling the
idler axle forward in slotted cheeks.
"""
import math

import FreeCAD as App

import params as P
from . import geom as g
from .item import Item

V = g.V
ROT_RAIL_Y = App.Rotation(V(0, 1, 0), V(0, 0, 1), V(1, 0, 0), "ZXY")   # rail length -> +Y, height -> +X
ROT_Z_TO_MX = App.Rotation(V(0, 1, 0), -90)                            # +Z -> -X
ROT_Z_TO_X = App.Rotation(V(0, 1, 0), 90)                              # +Z -> +X
SCREW_COLOR = (0.22, 0.22, 0.24)
BELT_X = 8.0                  # belt centre plane relative to the bridge centre


def belt_center_z():
    d = P.derive()
    return d["bridge_z"][1] + d["pulley_pd"] / 2 + 1.4 + 1.0


def _ends():
    d = P.derive()
    return d["bridge_y"][0] - 13.0, d["bridge_y"][1] + 25.0       # idler centre, motor pulley centre


def motor_bracket():
    d = P.derive()
    bx = d["bx_min"]
    y1 = d["bridge_y"][1]
    z0b, z1b = d["bridge_z"]
    bz = belt_center_z()
    _, y_rear = _ends()
    t = 6.0
    end = g.box_r(bx - 26, bx + 20 + t, y1, y1 + t, z0b, bz + 26)
    side = g.box_r(bx + 20, bx + 20 + t, y1, y_rear + 25, bz - 24, bz + 26)
    flange = g.box_r(bx - 20 - t, bx - 20, y1 - 46, y1 + t, z0b, z1b)
    gus_top = g.box_r(bx - 26, bx + 20, y1 + t, y1 + t + 34, bz + 20, bz + 26)
    gus_bot = g.box_r(bx - 26, bx + 20, y1 + t, y1 + t + 34, bz - 24, bz - 18)
    body = end.fuse(side).fuse(flange).fuse(gus_top).fuse(gus_bot).removeSplitter()
    body = body.cut(g.rbox(bx + 1, bx + 17, y1 - 1, y1 + t + 1, z1b - 6, bz + 12, 3, axis="y"))   # belt window
    body = body.cut(g.cyl(11.5, 10, (bx + 18, y_rear, bz), (1, 0, 0)))                         # motor boss
    fast = {}
    body = g.drill(body, "M5", [(bx + sx, y1 + t, z0b + z) for sx in (-10, 10) for z in (10, 30, 50)],
                   d=(0, -1, 0), depth=t, cbore=0, screw=16)
    fast["M5x16 SHCS (beam end tap)"] = 6
    body = g.drill(body, "M5", [(bx - 20 - t, y, z0b + z) for y in (y1 - 36, y1 - 12) for z in (10, 70)],
                   d=(1, 0, 0), depth=t, cbore=0, screw=12)
    fast["M5x12 SHCS + M5 T-nut (beam side slot)"] = 4
    p = g.nema_pattern(42.3) / 2
    body = g.drill(body, "M3", [(bx + 20, y_rear + sy * p, bz + sz * p) for sy in (-1, 1) for sz in (-1, 1)],
                   d=(1, 0, 0), depth=t, cbore=0, screw=10)
    fast["M3x10 SHCS (NEMA)"] = 4
    return body, fast


def idler_bracket():
    d = P.derive()
    bx = d["bx_min"]
    y0 = d["bridge_y"][0]
    z0b, z1b = d["bridge_z"]
    bz = belt_center_z()
    yf, _ = _ends()
    t = 6.0
    end = g.box_r(bx - 26, bx + 20, y0 - t, y0, z0b, bz + 14)
    flange = g.box_r(bx - 20 - t, bx - 20, y0 - t, y0 + 46, z0b, z1b)
    cheeks = g.box_r(bx + BELT_X - 7.5, bx + BELT_X - 5, yf - 26, y0 - t, bz - 13, bz + 13).fuse(
        g.box_r(bx + BELT_X + 5, bx + BELT_X + 7.5, yf - 26, y0 - t, bz - 13, bz + 13))
    cross = g.box_r(bx + BELT_X - 7.5, bx + BELT_X + 7.5, yf - 26, yf - 22, bz - 13, bz + 13)
    body = end.fuse(flange).fuse(cheeks).fuse(cross).removeSplitter()
    body = body.cut(g.rbox(bx + 1, bx + 15, y0 - t - 1, y0 + 1, z1b - 6, bz + 12, 3, axis="y"))   # belt window
    body = body.cut(g.box_r(bx + BELT_X - 5, bx + BELT_X + 5, yf - 22, y0 - t + 0.1, bz - 14, bz + 14))
    body = g.slot(body, "M5", (bx + BELT_X - 8, yf, bz), (1, 0, 0), (0, 1, 0), 10, depth=16)      # axle slots
    fast = {}
    body = g.drill(body, "M5", [(bx + sx, y0 - t, z0b + z) for sx in (-10, 10) for z in (10, 30, 50)],
                   d=(0, 1, 0), depth=t, cbore=0, screw=16)
    fast["M5x16 SHCS (beam end tap)"] = 6
    body = g.drill(body, "M5", [(bx - 20 - t, y, z0b + z) for y in (y0 + 12, y0 + 36) for z in (10, 70)],
                   d=(1, 0, 0), depth=t, cbore=0, screw=12)
    fast["M5x12 SHCS + M5 T-nut (beam side slot)"] = 4
    body = body.fuse(g.box_r(bx + BELT_X - 15, bx + BELT_X + 15, yf - 26, yf - 22, bz - 13, bz - 7)).removeSplitter()
    body = g.drill(body, "M3", [(bx + BELT_X + sx * 11.5, yf - 26, bz - 10) for sx in (-1, 1)], d=(0, 1, 0),
                   depth=4, cbore=0)
    fast["M3x30 SHCS (Y belt tension)"] = 2
    return body, fast


def tension_parts():
    """Two tension blocks on the idler axle outside the cheeks + the M3 tension screws."""
    d = P.derive()
    bx = d["bx_min"]
    bz = belt_center_z()
    yf, _ = _ends()
    out = []
    for sx in (-1, 1):
        xb = bx + BELT_X + sx * 11.5
        blk = g.rbox(xb - 3.5, xb + 3.5, yf - 5, yf + 5, bz - 13, bz + 6, 1, axis="y")
        blk = blk.cut(g.cyl(2.6, 10, (xb - 5, yf, bz), (1, 0, 0)))
        blk = blk.cut(g.cyl(1.25, 12, (xb, yf - 6, bz - 10), (0, 1, 0)))
        out.append(blk)
    return out


def build_belt(pose):
    d = P.derive()
    bx = d["bx_min"] + pose["X"]
    cy = d["cy_min"] + pose["Y"]
    bz = belt_center_z()
    r = d["pulley_pd"] / 2
    yf, yr = _ends()
    belt = g.belt_loop((bx + BELT_X, yf, bz), (bx + BELT_X, yr, bz), r, P.Y_BELT_W, normal=(1, 0, 0))
    belt = belt.cut(g.box_r(bx + BELT_X - 5, bx + BELT_X + 5, cy - 2, cy + 2, bz + r - 1, bz + r + 3))
    L = 2 * (yr - yf) + 2 * math.pi * r + 60
    return [Item("YBelt", belt, g.C_BELT, "y_axis", move="posed", mass=L * 0.0084 * P.Y_BELT_W,
                 bom=None, kind="stock", note="stock belt, open, %.0f mm, ends clamped in the head carriage" % L,
                 check=False)]


def build():
    d = P.derive()
    yr = P.mgn(P.Y_RAIL)
    bx, cy = d["bx_min"], d["cy_min"]
    zc = d["y_rail_zc"]
    xf = bx + d["y_rail_x0"]
    bz = belt_center_z()
    yf, y_rear = _ends()
    items = []

    rail = g.mgn_rail(yr, P.Y_RAIL_LEN)
    rail.Placement = App.Placement(V(xf, d["y_rail_y"][0], zc), ROT_RAIL_Y)
    items.append(Item("YRail", rail, g.C_STEEL, "y_axis", move="bridge", mass=yr["rail_gpm"] * P.Y_RAIL_LEN,
                      bom="MGN12 rail %.0f mm" % P.Y_RAIL_LEN, kind="buy",
                      fasteners={"M3x8 SHCS + M3 T-nut (MGN rail)": int(P.Y_RAIL_LEN // yr["rail_pitch"])}))
    for k, sy in (("A", -1), ("B", 1)):
        b = g.mgn_block(yr)
        b.Placement = App.Placement(V(xf, cy + sy * P.Y_BLOCK_PITCH / 2, zc), ROT_RAIL_Y)
        items.append(Item("YBlock_" + k, b, g.C_STEEL, "y_axis", move="carriage", mass=yr["blk_g"],
                          bom="MGN12H block", kind="buy"))

    m = P.MOTORS["NEMA17_40"]
    body, shaft = g.nema(m)
    body.Placement = App.Placement(V(bx + 26.01, y_rear, bz), ROT_Z_TO_MX)
    shaft.Placement = App.Placement(V(bx + 26, y_rear, bz), ROT_Z_TO_MX)
    items.append(Item("YMotor_NEMA17", body, g.C_DARK, "y_axis", move="bridge", mass=m["mass"],
                      bom="NEMA17 (stock X motor) -> Y", kind="stock"))
    items.append(Item("YMotor_Shaft", shaft, g.C_STEEL, "y_axis", move="bridge", mat="steel", check=False))
    pul = g.gt2_pulley(P.PULLEY_TEETH, P.Y_BELT_W, 5.0, hub=6.0)
    pul.Placement = App.Placement(V(bx + BELT_X + 11, y_rear, bz), ROT_Z_TO_MX)
    items.append(Item("YPulley", pul, g.C_ALU, "y_axis", move="bridge", mat="alu", bom=None, kind="stock",
                      check=False))

    g.take_screws()
    mb, fast = motor_bracket()
    items.append(Item("YMotor_Bracket", mb, g.C_ALU, "y_axis", move="bridge", mat="alu", fasteners=fast,
                      bom="Y motor bracket, machined Al 6 mm (end plate + motor plate + side flange + gussets)",
                      kind="make"))
    items.append(Item("Screws_YMotorBracket", g.take_screws(), SCREW_COLOR, "y_axis", move="bridge", mass=0,
                      check=False))
    ib, fast = idler_bracket()
    items.append(Item("YIdler_Bracket", ib, g.C_ALU, "y_axis", move="bridge", mat="alu", fasteners=fast,
                      bom="Y idler bracket, machined Al (end plate + side flange + slotted cheeks)", kind="make"))
    scr = g.take_screws()
    for sx in (-1, 1):   # tension screws: head on the cross plate, thread into the tension block
        s = g.screw_solid("M3", (bx + BELT_X + sx * 11.5, yf - 26, bz - 10), (0, 1, 0), 24, head_at=-0.01)
        scr = s if scr is None else scr.fuse(s)
    items.append(Item("Screws_YIdlerBracket", scr, SCREW_COLOR, "y_axis", move="bridge", mass=0, check=False))
    for k, tb in enumerate(tension_parts()):
        items.append(Item("YTension_Block_%d" % (k + 1), tb, g.C_STEEL, "y_axis", move="bridge", mat="steel",
                          bom="Y tension block, steel 7x10x12, M3 tapped", kind="make", check=False))
    idl = g.idler(P.Y_BELT_W)
    idl.Placement = App.Placement(V(bx + BELT_X - 3.5, yf, bz), ROT_Z_TO_X)
    items.append(Item("YIdler", idl, g.C_ALU, "y_axis", move="bridge", mat="alu", bom=None, kind="stock",
                      check=False))
    items.append(Item("YIdler_Axle", g.cyl(2.5, 30, (bx + BELT_X - 15, yf, bz), (1, 0, 0)), g.C_STEEL, "y_axis",
                      move="bridge", mat="steel", bom="Idler axle M5x30 + nyloc", kind="buy", check=False))

    # X chain arm: bolted to the back of the Y motor bracket end plate
    from .services import X_CHAIN_Y, CHAIN_R, CHAIN_LINK
    y1 = d["bridge_y"][1] + 6.0
    zl = d["cb_z"][1] + 2 + CHAIN_LINK[2] / 2
    ztop = zl + 2 * CHAIN_R + CHAIN_LINK[2] / 2 + 8
    arm = g.rbox(bx - 8, bx + 8, y1, X_CHAIN_Y + 8, ztop - 8, ztop, 3, axis="z")
    arm = arm.fuse(g.rbox(bx - 14, bx + 14, y1, y1 + 6, ztop - 8, d["bridge_z"][0] + 26, 3, axis="y"))
    arm = g.fillet_safe(arm.removeSplitter(), 1.0)
    arm = g.drill(arm, "M3", [(bx + sx * 9, y1 + 6, d["bridge_z"][0] + 20) for sx in (-1, 1)], d=(0, -1, 0),
                  depth=6, cbore=0, screw=10)
    arm = g.drill(arm, "M3", [(bx + sx * 4, X_CHAIN_Y, ztop - 8) for sx in (-1, 1)], d=(0, 0, 1), depth=8,
                  insert=True)
    items.append(Item("XChain_Arm", arm, g.C_ORANGE, "chains", move="bridge", mat="PETG",
                      bom="X chain arm (printed PETG), on the Y motor bracket", kind="print",
                      fasteners={"M3x10 SHCS (into bracket, tapped)": 2,
                                 "M3x8 SHCS + heat-set insert (chain end)": 2}))
    items.append(Item("Screws_XChainArm", g.take_screws(), SCREW_COLOR, "chains", move="bridge", mass=0,
                      check=False))

    sw = g.microswitch()
    sw.rotate(V(), V(0, 1, 0), 90)
    sw.translate(V(xf, d["bridge_y"][0] + 22, zc + 22))
    items.append(Item("YHome_Switch", sw, g.C_BLUE, "y_axis", move="bridge", mass=3,
                      bom="Endstop microswitch (stock)", kind="stock",
                      fasteners={"M2x10 screw + M3 T-nut adapter (microswitch)": 2}))
    return items

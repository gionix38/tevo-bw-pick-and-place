"""Placement head (TS 7.3, 7.6, WP4, WP7), rev D: small direct drives.

C: NEMA8 hollow-shaft stepper on the nozzle axis. The nozzle stem is the motor's hollow shaft; the
   vacuum goes through it to a rotary swivel on top. No belt, pulleys, bearing housings or shelf.
Z: NEMA8 external linear stepper on the head carriage, integral T5x2 screw (2 mm lead, FR-12),
   flange nut on the Z slide. No coupler, no separate leadscrew.
Loads (see report): C needs ~1e-4 N m for PR-4; Z needs ~0.007 N m for 7 N at 2 mm lead. A NEMA8
(~0.018 N m) covers both with margin; NEMA11/14/17 were oversized and cost ~250 g of FR-4 budget.

Custom parts: head carriage (printed, one piece), Z slide (machined Al), camera angle (Al).
Head-local coordinates: origin on the nozzle axis at the tip, Z home; axes parallel to machine X/Y/Z.
Motion groups: carriage = with the Y blocks, zslide = Z slide, rotor = turns with C.
"""
import FreeCAD as App

import params as P
from . import geom as g
from .item import Item

V = g.V
ROT_RAIL_Z = App.Rotation(V(0, 0, 1), V(0, -1, 0), V(1, 0, 0), "ZXY")   # rail length -> +Z, height -> +X
ROT_FLIP = App.Rotation(V(1, 0, 0), 180)                                # +Z -> -Z
SCREW_COLOR = (0.22, 0.22, 0.24)

Z_RAIL_Z0 = 2.0
Z_BLOCK_C = 60.0              # MGN9H block centre at Z home
ZS_Z = (24.0, 84.0)           # Z slide plate
ARM_Z = (24.0, 28.0)          # C motor arm (motor face sits on top)
CMOT_FACE = ARM_Z[1]
SCREW_XY = (0.0, 22.0)        # Z screw axis
NUT_Z = (50.0, 56.0)          # nut seat on the Z slide
ZMOT_FACE = 100.0             # Z motor face (on the carriage shelf, body above)
PLATE_X = (-24.0 - P.HEAD_PLATE_T, -24.0)
PLATE_Y = (-50.0, 78.0)
PLATE_Z = (-6.0, 108.0)
CAM_SLOT_Z = 56.0


def nozzle_world_ref():
    d = P.derive()
    return V(d["bx_min"] + d["nozzle_dx"], d["cy_min"], P.NOZZLE_TIP_HOME_Z)


def _nema8(spec, hollow):
    """NEMA8 body: face on Z=0, body toward +Z (mounted face-down), axis on origin."""
    s, L = spec["size"], spec["length"]
    ch = 1.5
    pts = [(-s / 2 + ch, -s / 2), (s / 2 - ch, -s / 2), (s / 2, -s / 2 + ch), (s / 2, s / 2 - ch),
           (s / 2 - ch, s / 2), (-s / 2 + ch, s / 2), (-s / 2, s / 2 - ch), (-s / 2, -s / 2 + ch)]
    body = g.poly_face(pts).extrude(V(0, 0, L))
    body = body.fuse(g.cyl(spec["boss"] / 2, 1.5, (0, 0, -1.5)))
    body = body.cut(g.cyl(2.6 if hollow else 1.6, L + 4, (0, 0, -2)))
    p = g.nema_pattern(s) / 2
    for a in (-1, 1):
        for b in (-1, 1):
            body = body.cut(g.cyl(0.8, 4, (a * p, b * p, -0.1)))
    return body.removeSplitter()


def head_carriage():
    d = P.derive()
    yr = P.mgn(P.Y_RAIL)
    zr = P.mgn(P.Z_RAIL)
    n = nozzle_world_ref()
    x0, x1 = PLATE_X
    cam = P.CAMERA_OFFSET
    sx, sy = SCREW_XY
    fast = {}

    # rev E: the plate prints flat on its back face; everything behind it is the separate belt clamp
    plate = g.rbox(x0, x1, PLATE_Y[0], PLATE_Y[1], PLATE_Z[0], PLATE_Z[1], 8, axis="x")
    shelf = g.box_r(x1 - 1, 12, sy - 12, sy + 12, ZMOT_FACE - 5, ZMOT_FACE)
    web = g.box_r(x1 - 1, x1 + 5, sy - 12, sy + 12, ZMOT_FACE - 20, ZMOT_FACE - 5)
    swa = g.box_r(x1 - 1, -16, -19, -11, 85, 95)
    body = plate
    for s in (shelf, web, swa):
        body = body.fuse(s)
    body = body.removeSplitter()
    body = g.drill(body, "M3", [(x1, s, CLAMP_SCREW_Z) for s in (-CLAMP_SCREW_DY, CLAMP_SCREW_DY)], d=(-1, 0, 0),
                   depth=P.HEAD_PLATE_T + 1, cbore=0, screw=14)
    fast["M3x14 SHCS (plate -> belt clamp insert)"] = 2
    zc = d["y_rail_zc"] - n.z
    pts = [(x1, yb + s1 * yr["hole_c"] / 2, zc + s2 * yr["hole_b"] / 2)
           for yb in (-P.Y_BLOCK_PITCH / 2, P.Y_BLOCK_PITCH / 2) for s1 in (-1, 1) for s2 in (-1, 1)]
    body = g.drill(body, "M3", pts, d=(-1, 0, 0), depth=P.HEAD_PLATE_T + 1, cbore=3.5, screw=8)
    fast["M3x8 SHCS (MGN block)"] = 8
    nr = int(P.Z_RAIL_LEN // zr["rail_pitch"])
    z_first = Z_RAIL_Z0 + (P.Z_RAIL_LEN - (nr - 1) * zr["rail_pitch"]) / 2
    body = g.drill(body, "M3", [(x1, 0, z_first + i * zr["rail_pitch"]) for i in range(nr)], d=(-1, 0, 0),
                   depth=6, insert=True)
    fast["M3x8 SHCS + heat-set insert (MGN9 rail)"] = nr
    p = g.nema_pattern(20.0) / 2
    body = body.cut(g.cyl(8.5, 10, (sx, sy, ZMOT_FACE - 8)))
    body = g.drill(body, "M2", [(sx + a * p, sy + b * p, ZMOT_FACE - 5) for a in (-1, 1) for b in (-1, 1)],
                   d=(0, 0, 1), depth=6, cbore=0, screw=8)
    fast["M2x8 SHCS (NEMA8)"] = 4
    body = g.drill(body, "M3", [(x1, cam[1] + s, CAM_SLOT_Z) for s in (-9, 9)], d=(-1, 0, 0), depth=6, insert=True)
    fast["M3x8 SHCS + washer + heat-set insert (camera angle)"] = 2
    body = g.drill(body, "M2", [(-6 + dx, -15, 95) for dx in (-4.75, 4.75)], d=(0, 0, -1), depth=8, insert=True)
    fast["M2x10 screw (microswitch)"] = 2
    return body, fast


CLAMP_SCREW_Z = 103.0
CLAMP_SCREW_DY = 8.0


def belt_clamp():
    """Head belt clamp + Y chain post, rev E: one X-Z profile 24 mm thick (prints on its side). A flange
    sits on the back of the head plate above the bridge beam; 2 x M3 from the plate front into inserts."""
    d = P.derive()
    from .yaxis import belt_center_z, BELT_X
    from .services import Y_CHAIN_DX, CHAIN_R
    n = nozzle_world_ref()
    x0 = PLATE_X[0]
    fast = {}
    bxw = d["bx_min"]
    belt_top = belt_center_z() + d["pulley_pd"] / 2 + 1.4 - n.z
    ax0 = bxw + Y_CHAIN_DX - 7 - n.x
    post_top = d["bridge_z"][1] + 2 * CHAIN_R - n.z
    w = 12.0
    arm = g.box_r(ax0, x0, -w, w, belt_top + 1.5, belt_top + 7.5)
    jaw = g.box_r(bxw + BELT_X - 5 - n.x, bxw + BELT_X + 5 - n.x, -w, w, belt_top - 4.5, belt_top + 1.5)
    post = g.box_r(ax0, bxw + 3 - n.x, -w, w, belt_top + 7.5, post_top)
    flange = g.box_r(x0 - 6, x0, -w, w, CLAMP_SCREW_Z - 19, PLATE_Z[1])
    body = arm.fuse(jaw).fuse(post).fuse(flange).removeSplitter()
    body = body.cut(g.box_r(bxw + BELT_X - 3.5 - n.x, bxw + BELT_X + 3.5 - n.x, -w - 1, w + 1,
                            belt_top - 1.7, belt_top + 0.3))                         # belt slot
    body = g.drill(body, "M3", [(x0, s, CLAMP_SCREW_Z) for s in (-CLAMP_SCREW_DY, CLAMP_SCREW_DY)], d=(-1, 0, 0),
                   depth=6, insert=True)
    fast["M3 heat-set insert"] = 2
    body = g.drill(body, "M3", [(bxw + BELT_X - n.x, s, belt_top + 7.5) for s in (-8, 8)], d=(0, 0, -1),
                   depth=6.5, insert=True)
    for s in (-8, 8):
        g._SCREWS.append(g.screw_solid("M3", (bxw + BELT_X - n.x, s, belt_top + 7.5), (0, 0, -1), 6, head_at=-0.01))
    fast["M3x6 set screw + heat-set insert (belt clamp, presses belt end)"] = 2
    body = g.drill(body, "M3", [(bxw + Y_CHAIN_DX - n.x, s, post_top) for s in (-4, 4)], d=(0, 0, -1),
                   depth=8, insert=True)
    fast["M3x8 SHCS + heat-set insert (chain end)"] = 2
    return body, fast


# both cameras (down on the head, up under the table) use this board
CAM_BOARD = "Camera board OV9281 global shutter 1280x800 mono, USB UVC, M12 mount, 38x38 mm (down + up)"


def camera_angle():
    """Down camera bracket: 3 mm Al angle, two vertical slots (focus), camera board on 4 x M2."""
    cam = P.CAMERA_OFFSET
    x1 = PLATE_X[1]
    t = 3.0
    vert = g.rbox(x1, x1 + t, cam[1] - 16, cam[1] + 16, 35.6, CAM_SLOT_Z + 12, 3, axis="x")
    hor = g.rbox(x1, cam[0] + 19, cam[1] - 19, cam[1] + 19, 35.6, 35.6 + t, 4, axis="z")
    br = vert.fuse(hor).removeSplitter()
    br = br.cut(g.cyl(8.5, 10, (cam[0], cam[1], 30)))
    for s in (-9, 9):
        br = g.slot(br, "M3", (x1 + t, cam[1] + s, CAM_SLOT_Z), (-1, 0, 0), (0, 0, 1), 8, depth=t + 1)
        g._SCREWS.append(g.screw_solid("M3", (x1 + t, cam[1] + s, CAM_SLOT_Z), (-1, 0, 0), 8, head_at=-0.8))
    br = g.drill(br, "M2", [(cam[0] + a * 16, cam[1] + b * 16, 35.6 + t) for a in (-1, 1) for b in (-1, 1)],
                 d=(0, 0, -1), depth=t + 1, cbore=0, screw=8)
    return br


def z_slide():
    """Machined Z slide: plate on the MGN9H block, arm under the C motor face, nut seat."""
    zr = P.mgn(P.Z_RAIL)
    x_cp = PLATE_X[1] + zr["H"]
    sx, sy = SCREW_XY
    plate = g.box_r(x_cp, x_cp + 4, -14, 14, ZS_Z[0], ZS_Z[1])
    arm = g.box_r(x_cp + 4 - 0.5, 12, -12, 12, ARM_Z[0], ARM_Z[1])
    nut = g.box_r(x_cp + 4 - 0.5, 8, sy - 8, sy + 8, NUT_Z[0], NUT_Z[1])
    body = plate.fuse(arm).fuse(nut).removeSplitter()
    body = body.cut(g.cyl(8.2, 10, (0, 0, ARM_Z[0] - 1)))                    # C motor boss / hollow shaft
    body = body.cut(g.cyl(3.2, 20, (sx, sy, NUT_Z[0] - 1)))                  # screw clearance
    fast = {}
    body = g.drill(body, "M3", [(x_cp + 4, a * zr["hole_b"] / 2, Z_BLOCK_C + b * zr["hole_c"] / 2)
                                for a in (-1, 1) for b in (-1, 1)], d=(-1, 0, 0), depth=5, cbore=0, screw=6)
    fast["M3x6 low-head screw (MGN9H block)"] = 4
    p = g.nema_pattern(20.0) / 2
    body = g.drill(body, "M2", [(a * p, b * p, ARM_Z[0]) for a in (-1, 1) for b in (-1, 1)], d=(0, 0, 1),
                   depth=5, cbore=0, screw=6)
    fast["M2x6 SHCS (NEMA8 hollow, from below)"] = 4
    body = g.drill(body, "M2", [(sx + a * 6.5, sy, NUT_Z[1] + 2) for a in (-1, 1)], d=(0, 0, -1), depth=8,
                   cbore=0, screw=8)
    fast["M2x8 SHCS + nut (flange nut)"] = 2
    return body, fast


def build():
    items = []
    zr = P.mgn(P.Z_RAIL)
    cam = P.CAMERA_OFFSET

    def add(name, shape, color, move, **kw):
        items.append(Item(name, shape, color, "head", move=move, **kw))

    g.take_screws()
    hc, fast = head_carriage()
    add("Head_Carriage", hc, g.C_ORANGE, "carriage", mat="PETG", fasteners=fast,
        bom="Head carriage plate: block mount + Z rail + Z motor shelf (printed PETG-CF)", kind="print")
    bc, fast = belt_clamp()
    add("Head_BeltClamp", bc, g.C_ORANGE, "carriage", mat="PETG", fasteners=fast,
        bom="Head belt clamp + Y chain post (printed PETG-CF)", kind="print")
    add("Camera_Angle", camera_angle(), g.C_ALU, "carriage", mat="alu",
        bom="Down camera angle, Al 3 mm, slotted for focus", kind="make",
        fasteners={"M2x8 screw + 3 mm spacer (camera board)": 4})
    add("Screws_HeadCarriage", g.take_screws(), SCREW_COLOR, "carriage", mass=0, check=False)

    rail = g.mgn_rail(zr, P.Z_RAIL_LEN)
    rail.Placement = App.Placement(V(PLATE_X[1], 0, Z_RAIL_Z0), ROT_RAIL_Z)
    add("ZRail_MGN9", rail, g.C_STEEL, "carriage", mass=zr["rail_gpm"] * P.Z_RAIL_LEN,
        bom="MGN9 rail %.0f mm" % P.Z_RAIL_LEN, kind="buy")

    sx, sy = SCREW_XY
    zm = P.MOTORS[P.Z_MOTOR]
    zbody = _nema8(zm, hollow=False)
    zbody.translate(V(sx, sy, ZMOT_FACE))
    add("ZMotor_" + P.Z_MOTOR, zbody, g.C_DARK, "carriage", mass=zm["mass"],
        bom="NEMA8 external linear stepper 20x20x30, T5x2 screw 95 mm (head Z)", kind="buy")
    add("ZScrew_T5x2", g.cyl(2.5, ZMOT_FACE - 1.5 - 8, (sx, sy, 8)), g.C_STEEL, "carriage", mat="steel",
        bom=None, kind="buy", check=False)
    sw = g.microswitch()
    sw.rotate(V(), V(1, 0, 0), 180)
    sw.translate(V(-6, -15, 95))
    add("ZHome_Switch", sw, g.C_BLUE, "carriage", mass=3, bom="Endstop microswitch (stock)", kind="stock",
        check=False)

    cx, cy = cam
    add("DownCam_LEDRing", g.tube(16, 9.5, 3, (cx, cy, 6)), g.C_WHITE, "carriage", mass=6,
        bom="LED ring 12/24 V, diffuse (camera light)", kind="buy")
    add("DownCam_Lens_M12", g.cyl(7, 17, (cx, cy, 9)), g.C_DARK, "carriage", mass=8,
        bom="M12 lens f = 10 mm, for 1/4\" sensor or larger, low distortion, with lock nut (down camera: "
            "FOV ~18.5 x 11.6 mm at the PCB, 0.014 mm/px)", kind="buy")
    add("DownCam_LensHolder", g.box_c(cx, cy, 30, 14, 14, 8), g.C_DARK, "carriage", mass=4)
    board = g.box_c(cx, cy, 34.8, 38, 38, 1.6)
    board = g.drill(board, "M2", [(cx + a * 16, cy + b * 16, 36) for a in (-1, 1) for b in (-1, 1)], depth=4, cbore=0)
    add("DownCam_Board", board, g.C_PCB, "carriage", mass=10, bom=CAM_BOARD,
        kind="buy")

    zs, fast = z_slide()
    add("Z_Slide", zs, g.C_ALU, "zslide", mat="alu", fasteners=fast,
        bom="Z slide, one piece: block plate + C motor arm + nut seat (CNC Al 6061)", kind="make")
    add("Screws_ZSlide", g.take_screws(), SCREW_COLOR, "zslide", mass=0, check=False)
    blk = g.mgn_block(zr)
    blk.Placement = App.Placement(V(PLATE_X[1], 0, Z_BLOCK_C), ROT_RAIL_Z)
    add("ZBlock_MGN9H", blk, g.C_STEEL, "zslide", mass=zr["blk_g"], bom="MGN9H block", kind="buy")
    nut = g.cyl(7.5, 2, (sx, sy, NUT_Z[1])).fuse(g.cyl(3.5, 8, (sx, sy, NUT_Z[1] + 2)))
    nut = nut.cut(g.cyl(2.5, 14, (sx, sy, NUT_Z[1] - 1)))
    add("ZNut_T5x2_Flange", nut, g.C_BRASS, "zslide", mass=5, bom=None, kind="buy", check=False)
    cm = P.MOTORS[P.C_MOTOR]
    cbody = _nema8(cm, hollow=True)
    cbody.translate(V(0, 0, CMOT_FACE))
    add("CMotor_" + P.C_MOTOR, cbody, g.C_DARK, "zslide", mass=cm["mass"],
        bom="NEMA8 hollow-shaft stepper 20x20x30, shaft OD5/ID3, runout <= 0.02 mm (nozzle C)", kind="buy")
    swv = g.cyl(6, 10, (0, 0, CMOT_FACE + cm["length"] + 8)).fuse(
        g.cyl(2.5, 12, (5, 0, CMOT_FACE + cm["length"] + 13), (1, 0, 0)))
    add("Vacuum_Swivel", swv, g.C_BRASS, "zslide", mass=10, bom="Rotary vacuum swivel M5 for 5 mm shaft, 4 mm push-in",
        kind="buy")

    z_top = CMOT_FACE + cm["length"] + 8
    add("Hollow_Shaft", g.tube(2.5, 1.5, z_top - 18, (0, 0, 18)), g.C_STEEL, "rotor", mat="steel",
        bom=None, kind="buy", check=False)
    add("Compliance_Sleeve", g.tube(5, 2.6, 6, (0, 0, 12)), g.C_STEEL, "rotor", mat="steel",
        bom="Compliance spring + sleeve on the hollow shaft, ~1 N, 1.0-1.5 mm stroke", kind="buy")
    add("Juki_Holder", g.cyl(4.5, 7, (0, 0, 5)).cut(g.box_r(3.2, 6, -6, 6, 5.5, 9)), g.C_STEEL, "rotor",
        mat="steel", bom="Juki-compatible nozzle holder (CP40/500 pattern), 5 mm shaft bore", kind="buy")
    tip = g.cyl(3, 2, (0, 0, 3)).fuse(g.cone(0.4, 1.8, 3, (0, 0, 0)))
    add("Nozzle_Tip_loaded", tip, g.C_BRASS, "rotor", mass=1.5, bom=None, kind="buy")

    o = nozzle_world_ref()
    for it in items:
        it.shape.translate(o)
    return items

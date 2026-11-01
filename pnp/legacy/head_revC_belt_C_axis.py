"""Placement head (TS 7.3, 7.6, WP4, WP7), rev B.

rev C: the down camera sits on its own Al angle bracket (2 x M3 in vertical slots = focus
adjustment); the Y belt passes through a closed toothed slot in the carriage; the C motor sits on
slotted holes (belt tension); screws are modelled.

Custom parts:
  Head carriage (printed): bolts to the two Y blocks; carries the Z rail, Z motor shelf, down camera
      bracket, Z home switch, Y belt clamp and Y chain post. Replaces mother plate, head plate,
      Z motor bracket, camera bracket, switch arm, belt clamp and chain post.
  Z slide (machined Al, one setup): Z carriage plate, both nozzle bearing bores (FR-14 coaxiality),
      leadscrew nut seat and C motor shelf.

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

Z_CARR = (28.0, 108.0)
Z_BLOCK_C = 75.0
H_LOWER = (28.0, 42.0)
H_UPPER = (96.0, 108.0)
SHELF = (78.0, 82.0)
PULLEY_Z = 76.0
BELT_ZC = 86.5
SCREW_XY = (0.0, 27.0)
ZMOT_FACE = 105.0
PLATE_X = (-24.0 - P.HEAD_PLATE_T, -24.0)
PLATE_Y = (-50.0, 78.0)
PLATE_Z = (-6.0, 125.0)


def nozzle_world_ref():
    d = P.derive()
    return V(d["bx_min"] + d["nozzle_dx"], d["cy_min"], P.NOZZLE_TIP_HOME_Z)


def head_carriage():
    d = P.derive()
    yr = P.mgn(P.Y_RAIL)
    zr = P.mgn(P.Z_RAIL)
    from .yaxis import belt_center_z
    from .services import Y_CHAIN_DX, CHAIN_R, CHAIN_LINK
    n = nozzle_world_ref()
    x0, x1 = PLATE_X
    cam = P.CAMERA_OFFSET
    sx, sy = SCREW_XY
    fast = {}

    plate = g.rbox(x0, x1, PLATE_Y[0], PLATE_Y[1], PLATE_Z[0], PLATE_Z[1], 8, axis="x")
    # Y belt clamp arm over the beam + Y chain post (world positions converted to head-local)
    bxw = d["bx_min"]
    belt_top = belt_center_z() + d["pulley_pd"] / 2 + 1.4 - n.z
    ax0 = bxw + Y_CHAIN_DX - 7 - n.x
    arm = g.rbox(ax0, x1 - 2, -12, 12, belt_top + 1.5, belt_top + 7.5, 3, axis="z")
    jaw = g.box_r(bxw + 3 - n.x, bxw + 13 - n.x, -12, 12, belt_top - 4.5, belt_top + 1.5)
    post_top = d["bridge_z"][1] + 2 * CHAIN_R - n.z
    post = g.rbox(ax0, bxw + 3 - n.x, -8, 8, belt_top + 7.5, post_top, 3, axis="z")
    # Z motor shelf + web, camera bracket + rib, Z switch arm
    shelf = g.rbox(x1 - 1, 20, 10, 46, ZMOT_FACE - 5, ZMOT_FACE, 4, axis="z")
    web = g.box_r(x1 - 1, x1 + 5, 10, 46, ZMOT_FACE - 22, ZMOT_FACE - 5)
    swa = g.box_r(x1 - 1, -16, -19, -11, 112, 122)
    body = plate
    for s in (arm, jaw, post, shelf, web, swa):
        body = body.fuse(s)
    body = g.fillet_safe(body.removeSplitter(), 1.5)
    # closed belt slot in the clamp (belt passes through, clamp screws press both ends)
    body = body.cut(g.box_r(bxw + 4.5 - n.x, bxw + 11.5 - n.x, -13, 13, belt_top - 1.7, belt_top + 0.3))
    # lightening pockets
    body = body.cut(g.rbox(x0 - 1, x1 + 1, -46, -14, 58, 106, 5, axis="x"))
    body = body.cut(g.rbox(x0 - 1, x1 + 1, 50, 74, 80, 120, 5, axis="x"))
    # 8 x M3 into the Y blocks, counterbored from the front
    zc = d["y_rail_zc"] - n.z
    pts = [(x1, yb + s1 * yr["hole_c"] / 2, zc + s2 * yr["hole_b"] / 2)
           for yb in (-P.Y_BLOCK_PITCH / 2, P.Y_BLOCK_PITCH / 2) for s1 in (-1, 1) for s2 in (-1, 1)]
    body = g.drill(body, "M3", pts, d=(-1, 0, 0), depth=P.HEAD_PLATE_T + 1, cbore=3.5, screw=8)
    fast["M3x8 SHCS (MGN block)"] = 8
    # Z rail screws into heat-set inserts
    nr = int(P.Z_RAIL_LEN // zr["rail_pitch"])
    z_first = 5.0 + (P.Z_RAIL_LEN - (nr - 1) * zr["rail_pitch"]) / 2
    body = g.drill(body, "M3", [(x1, 0, z_first + i * zr["rail_pitch"]) for i in range(nr)], d=(-1, 0, 0),
                   depth=6, insert=True)
    fast["M3x8 SHCS + heat-set insert (MGN9 rail)"] = nr
    # Z motor through the shelf
    p = g.nema_pattern(P.MOTORS[P.Z_MOTOR]["size"]) / 2
    body = body.cut(g.cyl(11.5, 10, (sx, sy, ZMOT_FACE - 8)))
    body = g.drill(body, "M3", [(sx + a * p, sy + b * p, ZMOT_FACE - 5) for a in (-1, 1) for b in (-1, 1)],
                   d=(0, 0, 1), depth=6, cbore=0, screw=8)
    fast["M3x8 SHCS (NEMA)"] = 4
    # camera angle: 2 x M3 heat-set inserts
    body = g.drill(body, "M3", [(x1, cam[1] + s, CAM_SLOT_Z) for s in (-9, 9)], d=(-1, 0, 0), depth=6, insert=True)
    fast["M3x8 SHCS + washer + heat-set insert (camera angle)"] = 2
    body = g.drill(body, "M2", [(-6 + dx, -15, 122) for dx in (-4.75, 4.75)], d=(0, 0, -1), depth=8, insert=True)
    for dx in (-4.75, 4.75):
        g._SCREWS.append(g.screw_solid("M2", (-6 + dx, -15, 112), (0, 0, 1), 12, head_at=-0.01))
    fast["M2x10 screw (microswitch)"] = 2
    # belt clamp plate screws and chain end inserts
    body = g.drill(body, "M3", [(bxw + 8 - n.x, s, belt_top + 7.5) for s in (-8, 8)], d=(0, 0, -1),
                   depth=6.5, insert=True)
    for s in (-8, 8):
        g._SCREWS.append(g.screw_solid("M3", (bxw + 8 - n.x, s, belt_top + 7.5), (0, 0, -1), 6, head_at=-0.01))
    fast["M3x6 set screw + heat-set insert (belt clamp, presses belt end)"] = 2
    body = g.drill(body, "M3", [(bxw + Y_CHAIN_DX - n.x, s, post_top) for s in (-4, 4)], d=(0, 0, -1),
                   depth=8, insert=True)
    fast["M3x8 SHCS + heat-set insert (chain end)"] = 2
    return body, fast


CAM_SLOT_Z = 56.0


def camera_angle():
    """Down camera bracket: 3 mm Al angle. Vertical leg on the carriage front face with two vertical
    slots (focus / working distance), horizontal leg carries the camera board on 4 x M2."""
    cam = P.CAMERA_OFFSET
    x1 = PLATE_X[1]
    t = 3.0
    vert = g.rbox(x1, x1 + t, cam[1] - 16, cam[1] + 16, 35.6, CAM_SLOT_Z + 12, 3, axis="x")
    hor = g.rbox(x1, cam[0] + 19, cam[1] - 19, cam[1] + 19, 35.6, 35.6 + t, 4, axis="z")
    br = vert.fuse(hor).removeSplitter()
    br = br.cut(g.cyl(8.5, 10, (cam[0], cam[1], 30)))                       # lens / ring clearance
    for s in (-9, 9):
        br = g.slot(br, "M3", (x1 + t, cam[1] + s, CAM_SLOT_Z), (-1, 0, 0), (0, 0, 1), 8, depth=t + 1)
        g._SCREWS.append(g.screw_solid("M3", (x1 + t, cam[1] + s, CAM_SLOT_Z), (-1, 0, 0), 8, head_at=-0.8))
    br = g.drill(br, "M2", [(cam[0] + a * 16, cam[1] + b * 16, 35.6 + t) for a in (-1, 1) for b in (-1, 1)],
                 d=(0, 0, -1), depth=t + 1, cbore=0, screw=8)
    return br


def z_slide():
    zr = P.mgn(P.Z_RAIL)
    x_cp = PLATE_X[1] + zr["H"]
    sx, sy = SCREW_XY
    plate = g.rbox(x_cp, x_cp + 4, -14, 14, Z_CARR[0], Z_CARR[1], 3, axis="x")
    plate = plate.cut(g.box_r(x_cp - 1, x_cp + 5, 9.2, 15, Z_CARR[1] - 14, Z_CARR[1] + 1))   # Z motor clearance
    xh = x_cp + 4
    body = plate
    for s in (g.rbox(xh - 0.5, 9, -9, 9, H_LOWER[0], H_LOWER[1], 3, axis="z"),
              g.rbox(xh - 0.5, 9, -9, 9, H_UPPER[0], H_UPPER[1], 3, axis="z"),
              g.rbox(xh - 0.5, 9, sy - 9, sy + 9, 60, 78, 3, axis="z"),         # nut seat
              g.box_r(xh - 0.5, -5, 8, sy - 8, 60, 78),                         # nut seat web
              g.rbox(xh - 0.5, 22, -40, -8, SHELF[0], SHELF[1], 4, axis="z")):  # C motor shelf
        body = body.fuse(s)
    body = body.removeSplitter()
    for z0, z1 in (H_LOWER, H_UPPER):
        body = body.cut(g.cyl(6.5, z1 - z0 + 2, (0, 0, z0 - 1)))            # 686 bores, one setup
    body = body.cut(g.cyl(5.2, 30, (sx, sy, 55)))                           # nut body
    body = body.cut(g.cyl(11.5, 10, (8, -26, SHELF[0] - 2)))                # C motor boss
    fast = {}
    body = g.drill(body, "M3", [(xh, a * zr["hole_b"] / 2, Z_BLOCK_C + b * zr["hole_c"] / 2)
                                for a in (-1, 1) for b in (-1, 1)], d=(-1, 0, 0), depth=5, cbore=0, screw=6)
    fast["M3x6 low-head screw (MGN9H block)"] = 4
    body = g.drill(body, "M3", [(sx + a * 8, sy, 81.5) for a in (-1, 1)], d=(0, 0, -1), depth=14, cbore=0, screw=14)
    fast["M3x12 SHCS + nut (anti-backlash nut)"] = 2
    p = g.nema_pattern(28.0) / 2
    for a in (-1, 1):
        for b in (-1, 1):   # slotted toward the nozzle axis: C belt tension
            body = g.slot(body, "M2.5", (8 + a * p, -26 + b * p, SHELF[1]), (0, 0, -1), (-8, 26, 0), 3, depth=6)
            g._SCREWS.append(g.screw_solid("M2.5", (8 + a * p, -26 + b * p, SHELF[1]), (0, 0, -1), 6, head_at=0))
    fast["M2.5x6 SHCS + washer (NEMA11, slotted)"] = 4
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
        bom="Head carriage, one piece: block mount + Z rail + motor shelf + belt clamp + chain post "
            "(printed PETG-CF)", kind="print")
    add("Camera_Angle", camera_angle(), g.C_ALU, "carriage", mat="alu",
        bom="Down camera angle, Al 3 mm, slotted for focus", kind="make",
        fasteners={"M2x8 screw + 3 mm spacer (camera board)": 4})
    add("Screws_HeadCarriage", g.take_screws(), (0.22, 0.22, 0.24), "carriage", mass=0, check=False)
    rail = g.mgn_rail(zr, P.Z_RAIL_LEN)
    rail.Placement = App.Placement(V(PLATE_X[1], 0, 5.0), ROT_RAIL_Z)
    add("ZRail_MGN9", rail, g.C_STEEL, "carriage", mass=zr["rail_gpm"] * P.Z_RAIL_LEN,
        bom="MGN9 rail %.0f mm" % P.Z_RAIL_LEN, kind="buy")

    sx, sy = SCREW_XY
    add("ZScrew_TR8x2", g.cyl(4.0, ZMOT_FACE - 28, (sx, sy, 18)), g.C_STEEL, "carriage", mat="steel",
        bom="TR8x2 leadscrew 80 mm", kind="buy", check=False)
    add("ZCoupler", g.cyl(9.5, 18, (sx, sy, ZMOT_FACE - 18)), g.C_ALU, "carriage", mass=12,
        bom="Coupler 5-8 mm", kind="buy", check=False)
    zm = P.MOTORS[P.Z_MOTOR]
    body, shaft = g.nema(zm)
    body.Placement = App.Placement(V(sx, sy, ZMOT_FACE), ROT_FLIP)
    shaft.Placement = App.Placement(V(sx, sy, ZMOT_FACE), ROT_FLIP)
    add("ZMotor_" + P.Z_MOTOR, body, g.C_DARK, "carriage", mass=zm["mass"],
        bom="%s mm stepper (head Z)" % P.Z_MOTOR.replace("_", " "), kind="buy")
    add("ZMotor_Shaft", shaft, g.C_STEEL, "carriage", mat="steel", check=False)
    sw = g.microswitch()
    sw.rotate(V(), V(1, 0, 0), 180)
    sw.translate(V(-6, -15, 122))
    add("ZHome_Switch", sw, g.C_BLUE, "carriage", mass=3, bom="Endstop microswitch (stock)", kind="stock")

    cx, cy = cam
    add("DownCam_LEDRing", g.tube(16, 9.5, 3, (cx, cy, 6)), g.C_WHITE, "carriage", mass=6,
        bom="LED ring 12/24 V, diffuse (camera light)", kind="buy")
    add("DownCam_Lens_M12", g.cyl(7, 17, (cx, cy, 9)), g.C_DARK, "carriage", mass=8,
        bom="M12 lens, FOV 15-25 mm at PCB", kind="buy")
    add("DownCam_LensHolder", g.box_c(cx, cy, 30, 14, 14, 8), g.C_DARK, "carriage", mass=4)
    board = g.box_c(cx, cy, 34.8, 38, 38, 1.6)
    board = g.drill(board, "M2", [(cx + a * 16, cy + b * 16, 36) for a in (-1, 1) for b in (-1, 1)], depth=4, cbore=0)
    add("DownCam_Board", board, g.C_PCB, "carriage", mass=10, bom="USB global-shutter camera board 720p+",
        kind="buy")

    zs, fast = z_slide()
    add("Z_Slide", zs, g.C_ALU, "zslide", mat="alu", fasteners=fast,
        bom="Z slide, one piece: carriage + bearing bores + nut seat + C motor shelf (CNC Al 6061)", kind="make")
    add("Screws_ZSlide", g.take_screws(), (0.22, 0.22, 0.24), "zslide", mass=0, check=False)
    blk = g.mgn_block(zr)
    blk.Placement = App.Placement(V(PLATE_X[1], 0, Z_BLOCK_C), ROT_RAIL_Z)
    add("ZBlock_MGN9H", blk, g.C_STEEL, "zslide", mass=zr["blk_g"], bom="MGN9H block", kind="buy")
    for nm, (z0, z1) in (("Lower", H_LOWER), ("Upper", H_UPPER)):
        bz = z0 + 2 if nm == "Lower" else z1 - 7
        add("Bearing_686_" + nm, g.tube(6.5, 3, 5, (0, 0, bz)), g.C_STEEL, "zslide", mat="steel",
            bom="Bearing 686ZZ 6x13x5", kind="buy", check=False)
    nut = g.tube(11, 4.0, 3.5, (sx, sy, 78)).fuse(g.tube(5.1, 4.0, 12, (sx, sy, 66)))
    add("ZNut_AntiBacklash", nut, g.C_BRASS, "zslide", mat="brass", bom="TR8x2 anti-backlash nut", kind="buy",
        check=False)
    cm = P.MOTORS[P.C_MOTOR]
    body, shaft = g.nema(cm)
    body.translate(V(8, -26, SHELF[0]))
    shaft.translate(V(8, -26, SHELF[0]))
    add("CMotor_" + P.C_MOTOR, body, g.C_DARK, "zslide", mass=cm["mass"],
        bom="%s mm stepper (nozzle C)" % P.C_MOTOR.replace("_", " "), kind="buy")
    add("CMotor_Shaft", shaft, g.C_STEEL, "zslide", mat="steel", check=False)
    mp = g.gt2_pulley(20, 6.0, 5.0, hub=6.0)
    mp.Placement = App.Placement(V(8, -26, PULLEY_Z + 21), ROT_FLIP)
    add("CMotor_Pulley", mp, g.C_ALU, "zslide", mat="alu", bom="GT2 pulley 20T 5 mm bore 6 mm", kind="buy")
    r = 20 * 2.0 / 3.141592653589793 / 2
    belt = g.belt_loop((0, 0, BELT_ZC), (8, -26, BELT_ZC), r, 6.0, normal=(0, 0, 1))
    items.append(Item("CBelt_GT2_closed", belt, g.C_BELT, "head", move="zslide", mass=1.5,
                      bom="GT2 closed loop belt 6 mm, ~110 mm", kind="buy", check=False))
    swv = g.cyl(6, 10, (0, 0, 114)).fuse(g.cyl(2.5, 12, (5, 0, 119), (1, 0, 0)))
    add("Vacuum_Swivel", swv, g.C_BRASS, "zslide", mass=12, bom="Rotary vacuum swivel M5, 4 mm push-in", kind="buy")

    add("Nozzle_Shaft", g.tube(3, 2, 96, (0, 0, 18)), g.C_STEEL, "rotor", mat="steel",
        bom="Nozzle shaft, 6 mm hollow stainless tube", kind="buy", check=False)
    np_ = g.gt2_pulley(20, 6.0, 6.0, hub=6.0)
    np_.translate(V(0, 0, PULLEY_Z))
    add("Nozzle_Pulley", np_, g.C_ALU, "rotor", mat="alu", bom="GT2 pulley 20T 6 mm bore 6 mm", kind="buy")
    add("Compliance_Sleeve", g.tube(5, 3.5, 6, (0, 0, 12)), g.C_STEEL, "rotor", mat="steel",
        bom="Compliance spring + sleeve, ~1 N preload, 1.0-1.5 mm stroke", kind="buy")
    add("Juki_Holder", g.cyl(4.5, 7, (0, 0, 5)).cut(g.box_r(3.2, 6, -6, 6, 5.5, 9)), g.C_STEEL, "rotor",
        mat="steel", bom="Juki-compatible nozzle holder (CP40/500 pattern)", kind="buy")
    tip = g.cyl(3, 2, (0, 0, 3)).fuse(g.cone(0.4, 1.8, 3, (0, 0, 0)))
    add("Nozzle_Tip_loaded", tip, g.C_BRASS, "rotor", mass=1.5, bom=None, kind="buy")

    o = nozzle_world_ref()
    for it in items:
        it.shape.translate(o)
    return items

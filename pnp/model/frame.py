"""Frame (TS 7.1, WP1), rev B.

C-beams laid horizontal as X rails, two ties, and four printed corner blocks. Each corner block is
end cap + belt pulley/idler housing + tie corner bracket + leg in one part; the front-left one also
carries the X motor. Rubber feet screw into the corner blocks. The 20x80x210 legs are no longer used.
rev C: X idlers ride in tension sliders (M4 screw through the block end), cast corner brackets at the
tie ends, the chain tray has its own brackets (services.py), screws are modelled.
rev E: the front-left block and the X motor housing are one solid block (closed coupler bore).
"""
import params as P
from . import geom as g
from .item import Item

V = g.V

M5_END = "M5x45 SHCS (corner block -> C-beam end tap)"
M5_TNUT = "M5x10 SHCS + M5 T-nut"
M3_MOTOR = "M3x10 SHCS (NEMA, from the inner face, 2.5 mm ball-end key 100 mm)"
FOOT = "Rubber foot M6 stud, D24x10"
BRG608 = "Bearing 608ZZ 8x22x7"


def _corner_base(left):
    """Front corner block, left (drive) or right (idler) end. Frame coordinates, front side."""
    w, h = P.CB_SECTION
    z0, z1 = P.FOOT_H, P.BASE_Z + h
    zb = P.BASE_Z
    if left:
        ex0, ex1 = MOTOR_X0, P.CB_CAP       # end part (beyond the C-beam end), flush with the motor face
        fx0, fx1 = MOTOR_X0, 64.0           # foot under C-beam + tie end
        gx0, gx1 = 36.0, 48.0               # gusset beside the tie (tie at X 16..36)
    else:
        ex0, ex1 = P.CB_LEN - P.CB_CAP, P.CB_LEN + 32.0
        fx0, fx1 = 506.0, P.CB_LEN + 32.0
        gx0, gx1 = 506.0, 518.0             # tie bar at X 518..558
    # square: the block continues the profile end, no rounding (rev D)
    end = g.box_r(ex0, ex1, -4, w + 4, z0, z1)
    foot = g.box_r(fx0, fx1, -4, w + 24, z0, zb)
    gus = g.box_r(gx0, gx1, w, w + 24, zb, zb + 36)
    return end.fuse(foot).fuse(gus).removeSplitter()


def _pocket(x0, x1, y0, y1, z0, z1, ch=7.0):
    """Pocket with a 45 deg chamfered roof (prints without support; flat bridge only in the middle)."""
    pts = [(y0, z0), (y1, z0), (y1, z1), (y1 - ch, z1 + ch), (y0 + ch, z1 + ch), (y0, z1)]
    f = g.Part.Face(g.Part.makePolygon([V(x0, y, z) for y, z in pts] + [V(x0, pts[0][0], pts[0][1])]))
    return f.extrude(V(x1 - x0, 0, 0))


def _corner_cuts(body, left):
    w, h = P.CB_SECTION
    zb = P.BASE_Z
    dz = P.DRIVE_Z
    jx = P.JACKSHAFT_X
    fast = {}
    if left:
        body = body.cut(_pocket(-29, P.CB_CAP + 1, 5, 27, dz - 17, dz + 17))             # pulley pocket
        body = body.cut(g.cyl(4.5, 120, (jx, -60, dz), (0, 1, 0)))                       # jackshaft
        body = body.cut(g.cyl(11.1, 7.5, (jx, -4.5, dz), (0, 1, 0)))                     # 608 outer
        body = body.cut(g.cyl(11.1, 7.5, (jx, w + 4.5 - 7.5, dz), (0, 1, 0)))            # 608 inner
        xe, de = MOTOR_X0, (1, 0, 0)
    else:
        body = body.cut(_pocket(P.CB_LEN - P.CB_CAP - 1, P.CB_LEN + 26, 1, 24, dz - 17, dz + 17))  # slider pocket
        body = g.drill(body, "M4", [(P.CB_LEN + 32.0, 12.5, dz)], d=(-1, 0, 0), depth=8, cbore=0, screw=20)
        fast["M4x20 SHCS + nut (idler tension)"] = 1
        xe, de = P.CB_LEN + 32.0, (-1, 0, 0)
    # M5 into the tapped C-beam end (core holes)
    cb = (-18.0 - xe) if left else 12.0     # head 30 mm before the beam end face
    body = g.drill(body, "M5", [(xe, y, zb + z) for y in (10.0, 30.0) for z in (10.0, 70.0)], d=de,
                   depth=60, cbore=cb, screw=45)
    fast[M5_END] = 4
    # foot: M5 up into the C-beam and tie bottom slots, counterbored from below
    xs = (30.0, 54.0) if left else (520.0, 544.0)
    pts = [(x, y, P.FOOT_H) for x in xs for y in (10.0, 30.0)]
    pts.append((26.0 if left else 538.0, 52.0, P.FOOT_H))
    body = g.drill(body, "M5", pts, d=(0, 0, 1), depth=12, cbore=5, screw=10)
    fast[M5_TNUT] = len(pts)
    # gusset: into the C-beam inner face and into the tie side
    gx = 42.0 if left else 512.0
    body = g.drill(body, "M5", [(gx, w + 24, zb + 10), (gx, w + 24, zb + 28)], d=(0, -1, 0), depth=26, cbore=12,
                   screw=16)
    tx = 48.0 if left else 506.0
    body = g.drill(body, "M5", [(tx, w + 12, zb + 10)] + ([(tx, w + 12, zb + 28)] if left else []),
                   d=(-1 if left else 1, 0, 0), depth=14, cbore=4, screw=12)
    fast[M5_TNUT] += 4 if left else 3
    # rubber foot (M6 heat-set insert)
    body = g.drill(body, "M6", [((-10.0 if left else 586.0), 20.0, P.FOOT_H)], d=(0, 0, 1), depth=12, cbore=0)
    fast[FOOT] = 1
    return body, fast


MOTOR_X0 = -40.0     # left end face of the left corner blocks (= X motor housing outer face)
MOTOR_FACE_Y = -40.0


def _motor_housing():
    """X motor housing, rev E: solid, flush with the front-left corner block on all faces (no open U)."""
    return g.box_r(MOTOR_X0, P.CB_CAP, MOTOR_FACE_Y, -4, P.FOOT_H, P.BASE_Z + P.CB_SECTION[1])


def _motor_cuts(body):
    """Closed coupler bore behind the motor face; motor screws go in from the block's inner face (Y 44)
    through long counterbored channels (ball-end key); two top holes reach the coupler grub screws."""
    jx, dz = P.JACKSHAFT_X, P.DRIVE_Z
    fy, t = MOTOR_FACE_Y, 5.0
    body = body.cut(g.cyl(11.5, t + 2, (jx, fy - 1, dz), (0, 1, 0)))             # motor boss
    body = body.cut(g.cyl(12.0, -4 - fy - t + 0.5, (jx, fy + t, dz), (0, 1, 0)))   # coupler bore
    body = g.drill(body, "M4", [(jx, y, P.BASE_Z + P.CB_SECTION[1]) for y in (-31.0, -12.0)],
                   depth=30, cbore=0)                                             # key access, coupler
    p = g.nema_pattern(42.3) / 2
    yin = P.CB_SECTION[0] + 4
    body = g.drill(body, "M3", [(jx + sx * p, yin, dz + sz * p) for sx in (-1, 1) for sz in (-1, 1)],
                   d=(0, -1, 0), depth=yin - fy, cbore=yin - fy - t, screw=10)
    return body


def screws_item(name, compound, system, move="fixed"):
    return Item(name, compound, (0.22, 0.22, 0.24), system, move=move, mass=0, bom=None, check=False)


def idler_slider(belt_y):
    """U-shaped slider in the right corner block pocket; carries the X idler axle. The M4 tension
    screw through the block end pulls it outward. belt_y = belt centre plane."""
    dz = P.DRIVE_Z
    xi = P.CB_LEN + 10.0
    y0, y1 = belt_y - 10.5, belt_y + 10.5
    sl = g.rbox(xi - 10, xi + 12, y0, y1, dz - 14, dz + 14, 2, axis="y")
    sl = sl.cut(g.box_r(xi - 11, xi + 9.5, belt_y - 6.2, belt_y + 6.2, dz - 15, dz + 15))   # idler gap
    sl = sl.cut(g.cyl(2.6, 30, (xi, y0 - 1, dz), (0, 1, 0)))                               # axle
    sl = sl.cut(g.cyl(2.3, 8, (xi + 9, belt_y, dz), (1, 0, 0)))                            # M4 path
    sl = sl.cut(g.box_r(xi + 9.6, xi + 12.5, belt_y - 3.8, belt_y + 3.8, dz - 4, dz + 15))   # nut trap
    return sl


SW_Y = 37.2        # X home switch: on the front-left corner block, struck by the bridge foot at home
SW_Z = 106.0


def _switch_pad():
    return g.box_r(-8, P.CB_CAP, 30, 44, P.BASE_Z + P.CB_SECTION[1] - 1, SW_Z)


def x_switch():
    """Microswitch, lever pointing +X past the C-beam end; the bridge foot presses it at X home."""
    body = g.box_r(-6, 14, SW_Y - 3.2, SW_Y + 3.2, SW_Z, SW_Z + 10)
    lever = g.box_r(-2, 26, SW_Y - 2, SW_Y + 2, SW_Z + 10.5, SW_Z + 11.1)
    return body.fuse(lever)


def corner_bracket():
    """40x40 cast angle in the vertical corner between the left tie (+X face, X 36) and the front
    C-beam inner face (Y 40), upper half."""
    w = P.CB_SECTION[0]
    zb = P.BASE_Z
    x0, y0 = 36.0, w
    z0, z1 = zb + 40.0, zb + 80.0
    a = g.box_r(x0, x0 + 4, y0, y0 + 40, z0, z1)
    b = g.box_r(x0, x0 + 40, y0, y0 + 4, z0, z1)
    gus = g.poly_face([(0, 0), (34, 0), (0, 34)]).extrude(V(0, 0, 3))
    gus.translate(V(x0, y0, (z0 + z1) / 2 - 1.5))
    br = g.fillet_safe(a.fuse(b).fuse(gus).removeSplitter(), 1.0)
    br = g.drill(br, "M5", [(x0 + 4, y0 + 22, z) for z in (zb + 50, zb + 70)], d=(-1, 0, 0), depth=6,
                 cbore=0, screw=10)
    br = g.drill(br, "M5", [(x0 + 22, y0 + 4, z) for z in (zb + 50, zb + 70)], d=(0, -1, 0), depth=6,
                 cbore=0, screw=10)
    return br


def build():
    d = P.derive()
    items = []
    w, h = P.CB_SECTION
    z0 = d["cb_z"][0]
    rear_y0 = d["cb_rear_y"][0]
    fw = d["frame_width"]

    # C-beams: channel opens outward (front beam -> -Y, rear beam -> +Y). The X belt runs in it.
    sec = g.cbeam_section(w, h, P.CB_CHANNEL)
    for nm, y0, flip in (("Front", 0.0, False), ("Rear", rear_y0, True)):
        items.append(Item("CBeam_" + nm, g.profile_along(sec, P.CB_EXTR_LEN, "x", (P.CB_CAP, y0, z0), flip_u=flip),
                          g.C_ALU_BLACK, "frame", mass=P.PROFILE_KG_M["C40x80"] * P.CB_EXTR_LEN,
                          bom="C-Beam 40x80x550 (stock Z column), laid horizontal",
                          kind="stock"))

    ta, tb = P.TIE_A, P.TIE_B
    items.append(Item("Tie_Left_20x80", g.profile_along(g.vslot_section(ta[0], ta[1]), ta[2], "y", (16.0, w, z0)),
                      g.C_ALU_BLACK, "frame", mass=P.PROFILE_KG_M["20x80"] * ta[2],
                      bom="V-slot 20x80x500 (stock top tie) cut to 480, tie",
                      kind="stock", fasteners={"M5x12 SHCS (tie end tap -> C-beam slot)": 4}))
    items.append(Item("Tie_Right_20x40", g.profile_along(g.vslot_section(tb[0], tb[1]), tb[2], "y", (518.0, w, z0)),
                      g.C_ALU_BLACK, "frame", mass=P.PROFILE_KG_M["20x40"] * tb[2],
                      bom="V-slot 20x40x485 (stock X gantry bar) cut to 480, tie",
                      kind="stock", fasteners={"M5x12 SHCS (tie end tap -> C-beam slot)": 2}))

    # corner blocks (legs); rear ones are mirror images
    for left, xname in ((True, "Left"), (False, "Right")):
        base = _corner_base(left)
        front = base.fuse(_motor_housing()).fuse(_switch_pad()).removeSplitter() if left else base
        g.take_screws()
        front, fast = _corner_cuts(front, left)
        if left:
            front = _motor_cuts(front)
            fast[M3_MOTOR] = 4
            front = g.drill(front, "M2", [(x, SW_Y, SW_Z) for x in (-0.75, 8.75)], depth=8, insert=True)
            fast["M2x10 screw (X home switch)"] = 2
            items.append(Item("XHome_Switch", x_switch(), g.C_BLUE, "x_axis", mass=4,
                              bom="Endstop microswitch with long lever (stock)", kind="stock", check=False))
        scr = g.take_screws()
        items.append(Item("Corner_Front%s" % xname, front, g.C_ORANGE, "frame", mat="PETG",
                          bom="Corner block front-%s%s (printed PETG/ASA)" %
                              (xname.lower(), " with X motor mount" if left else ""),
                          kind="print", fasteners=fast))
        items.append(screws_item("Screws_CornerFront%s" % xname, scr, "frame"))
        rear, fast = _corner_cuts(base, left)
        rear = rear.mirror(V(0, fw / 2, 0), V(0, 1, 0))
        scr = g.take_screws().mirror(V(0, fw / 2, 0), V(0, 1, 0))
        items.append(Item("Corner_Rear%s" % xname, rear, g.C_ORANGE, "frame", mat="PETG",
                          bom="Corner block rear-%s (printed PETG/ASA)" % xname.lower(), kind="print",
                          fasteners=fast))
        items.append(screws_item("Screws_CornerRear%s" % xname, scr, "frame"))
        fx = -10.0 if left else 586.0
        for nm, fy in (("Front", 20.0), ("Rear", fw - 20.0)):
            items.append(Item("Foot_%s%s" % (nm, xname), g.cyl(12, P.FOOT_H, (fx, fy, 0)).fuse(
                g.cyl(3, 12, (fx, fy, P.FOOT_H))), g.C_DARK, "frame", mat="rubber", bom=None, check=False))
        if not left:
            for nm, by in (("Front", 12.5), ("Rear", fw - 12.5)):
                items.append(Item("XIdler_Slider_" + nm, idler_slider(by), g.C_ORANGE, "x_axis", mat="PETG",
                                  bom="X idler tension slider (printed PETG)", kind="print",
                                  fasteners={"M4 nut (in slider trap)": 1}))
    # cast corner brackets at the upper inner corners of the left tie
    for nm, mirror in (("Front", False), ("Rear", True)):
        g.take_screws()
        br = corner_bracket()
        scr = g.take_screws()
        if mirror:
            br = br.mirror(V(0, fw / 2, 0), V(0, 1, 0))
            scr = scr.mirror(V(0, fw / 2, 0), V(0, 1, 0))
        items.append(Item("TieBracket_" + nm, br, g.C_ALU_BLACK, "frame", mass=40,
                          bom="Corner bracket 40x40 cast Al (tie -> C-beam)", kind="buy",
                          fasteners={"M5x10 SHCS + M5 T-nut": 4}))
        items.append(screws_item("Screws_TieBracket" + nm, scr, "frame"))
    # jackshaft bearings pressed into the left corner blocks
    for nm, y in (("FO", -4.5), ("FI", w + 4.5 - 7.5), ("RI", fw - w - 4.5), ("RO", fw + 4.5 - 7.5)):
        items.append(Item("Bearing608_" + nm, g.tube(11, 4, 7, (P.JACKSHAFT_X, y, P.DRIVE_Z), (0, 1, 0)),
                          g.C_STEEL, "x_axis", mass=12, bom=BRG608, kind="buy"))
    return items

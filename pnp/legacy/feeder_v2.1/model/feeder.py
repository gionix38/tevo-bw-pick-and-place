"""TBW-Feeder v2.1: motorised 8 mm tape lane (0816 principle), one servo per lane.

Per lane (tape along X, moves toward -X, pick at the inner end; all heights from the table top):
  advance   SG90 servo hangs upside down in the tower ABOVE the tape. A 2 mm pin in its horn (R 6.5)
            reaches down beside the tape (y +5..+7.5) into the ear of a slider that runs in a closed
            tunnel UNDER the tape (scotch yoke, stroke 4.2 mm). A printed flexure pawl on the slider
            front pushes the tape one sprocket hole per stroke (exactly 4.0 mm: the stroke has 0.2 mm
            free travel). Half strokes give 2 mm feeds.
  detent    a spring tongue cut into the 0.5 mm stainless cover plate drops into a sprocket hole from
            above and stops the tape from being dragged back (play 0.15 mm).
  peel      the cover tape is peeled at a slot in the cover plate, runs back on top of the plate, up
            the tower front, over a 3 mm guide rod and into a nip on top of the tower: a TPU drive roller
            and a 683ZZ pinch roller pressed by a 1.5 N spring. The nip slips above ~1.2 N, which limits
            the peel tension. Used cover tape leaves the nip rearward into the bank's waste bin.
  peel drive the same servo stroke turns the roller (no second motor). A printed 3 mm peg in the slider tail
            runs in an inclined slot of a printed lifter beside the servo, so the lifter rises 5.1 mm on
            every feed stroke and comes back down on the retract (positive both ways, no spring). A
            flexure pawl on the lifter pushes an 18-tooth ratchet that carries the roller: 2 teeth =
            4.9 mm of roller surface per 4 mm feed, 1 tooth per 2 mm feed. A flexure hold pawl on the
            tower keeps the cover tape tension between feeds. Surplus slips in the nip.
  pick      window in the cover plate; first open pocket at PICK_X.
  assembly  one printed body. Slider (with its dowel) goes in from the rear face, lifter and hold pawl
            drop in from the top, servo + horn + pin from the top, ratchet + roller between the cheeks,
            pinch yoke from the top under a snap-on cap that also stops the lifter. Bought per lane: SG90,
            horn pin, steel cover plate, pinch spring, screws/inserts; everything else is printed.
            The lane bolts to the tooling plate from below (3 x M3 into heat-set inserts).
  control   one servo cable per lane to the bank controller (Arduino Nano + IO shield), firmware
            ../feeder/firmware. OpenPnP feeds with M600 N<lane> F<mm>.
The tall parts are beyond X 592, which the head never reaches; the inner part is as low as v1.0.
Geometry in world (frame) coordinates; lane centre line at y. Model pose: slider at the forward end.
"""
import math

import FreeCAD as App

import params as P
from . import geom as g

V = g.V

# ------------------------------------------------------------------ tape (EIA-481, 8 mm)
TAPE_TOP = 16.0            # carrier top above the table (pick height reference)
TAPE_T = 0.9               # paper tape (thickest common 8 mm carrier)
ZB = TAPE_TOP - TAPE_T     # carrier underside = channel floor
CH_HW = 4.1                # tape channel half width (8.0 tape)
CH_TOP = 16.3              # channel roof / cover plate underside
HOLE_DY = -2.25            # sprocket hole row (1.75 from the tape edge)
HOLE_R = 0.75
POCKET_DY = 1.25           # pocket centre line (F = 3.5)
COVER_Y = (-1.4, 3.9)      # 5.3 mm cover tape over the pockets
COVER_T = 0.06
GROOVE_Y = (-0.75, 3.25)   # relief under embossed pockets
GROOVE_Z = 12.6
PITCH = P.TAPE_POCKET_PITCH
HOLE_C0 = P.PICK_X + 2.0   # hole centre next to the pick pocket (EIA P2 = 2.0)

# ------------------------------------------------------------------ lane body
BW = 10.25                 # body half width (lane pitch 22 -> 1.5 mm gap)
X_IN = 526.0               # inner end (empty tape exit)
X_TOWER = 592.0            # start of the tall part
X_OUT = 653.0              # rear face (tape inlet)
FLOOR = 5.0                # tunnel floor (M3 inserts from below)
TUN_TOP = 12.6
TUN_N = (-3.75, 1.2)       # narrow tunnel (low section)
TUN_W = (-3.75, 8.9)       # wide tunnel (slider ear, tower)
SLOT_Y = (-3.75, -0.75)    # hole-row slot from the tunnel up to the tape (slider rib / pawl)
TOP_T = 36.0               # tower top around the servo

# ------------------------------------------------------------------ advance
STROKE = 4.2               # 4.0 feed + 0.2 free travel (tooth 0.8 wide fits a 1.5 hole at both ends)
HORN_R = 6.5
ALPHA = math.degrees(math.asin(STROKE / 2 / HORN_R))
TH_FWD = 90.0 + ALPHA      # horn angle at the forward end (pin x = shaft - 2.1)
TH_RET = 90.0 - ALPHA
SERVO_X = 611.0            # servo output axis
ZF = 25.5                  # servo output face (facing down)
W_HOOK = HOLE_C0 + 4 * PITCH - math.sqrt(HOLE_R ** 2 - 0.4 ** 2)   # pawl hook face at the forward end
FLEX_L = 14.0              # flexure beam length
D_HOOK = HOLE_C0 + 6 * PITCH - math.sqrt(HOLE_R ** 2 - 0.4 ** 2) + 0.15   # detent hook face (0.15 play)
TONGUE_L = 18.4            # steel plate tongue (fallback)
DET_Z = ZB + 0.1            # detent tab bottom: reaches into 0.3 mm embossed carriers too

# ------------------------------------------------------------------ cover plate: printed PETG (default) or steel
COVER_PLATE = "printed"    # "steel": the 0.5 mm 1.4310 laser-cut plate of v2.0 (DXF/STEP still exported)
PLATE_T = 1.2 if COVER_PLATE == "printed" else 0.5
PT_TONGUE = (16.0, 3.0, 1.2)   # printed detent tongue length, width, thickness
PT_SLIT = 0.6              # printed slit around the tongue
PT_TAB = (1.0, 0.9, 0.18)  # printed detent tab along x / across, 45 deg chamfer on its +x lower edge

# ------------------------------------------------------------------ peel
ROD = (595.5, 53.0)        # guide rod axis (x, z), D3
ROLL_X, ROLL_Z = 638.0, 47.5   # roller axis on a stationary 3 mm dowel; nip line at ROLL_Z + ROLL_R = 54.5
ROLL_R = 7.0
PINCH_Z = ROLL_Z + ROLL_R + COVER_T + 3.5
CHEEK_X = (632.0, 644.0)
CHEEK_TOP = 70.0

# ------------------------------------------------------------------ peel drive (servo powered)
RAT_N = 18                 # ratchet teeth (20 deg pitch)
RAT_RT, RAT_RR = 6.0, 5.4  # tip / root radius
RAT_Y = (-6.2, -1.95)      # ratchet disc, next to the roller on the -y side
RAT_FACE0 = 151.8          # angle of one radial tooth face in the model pose (deg, x = cos, z = sin)
HUB_R, HUB_FLAT, BORE_R = 3.0, 2.5, 1.6   # ratchet hub through the roller (D-flat drives the roller)
LIFT_RATIO = 1.21          # lifter rise per mm of slider travel (inclined slot, 50.4 deg)
LIFT_B = 7.1               # lifter bottom above the table at the forward end (highest pose)
LIFT_Y = (-8.0, -6.4)      # thin part in the tower channel (clear of the servo tabs at -6.0)
LIFT_YH = (-8.0, -2.2)     # head above the tower: finger and tooth reach the ratchet plane
LIFT_TOOTH_X = 633.1       # pawl tip (free, undeflected)
LIFT_TOP = 61.9            # lifter height; top 1.0 under the cheek cap at the highest pose
PEG_X, PEG_Z, PEG_R = 624.5, 9.5, 1.5   # printed slider peg (D3) at the forward end
CAP_SNAPS = ((-1, 633.5, 636.0), (1, 639.5, 642.0))   # snap legs of the cheek cap: side, x0, x1
SNAP_Z = 62.0              # leg tips; the lips catch a notch in the cheek outer face
HOLD_X = 638.25            # hold pawl blocking face (+x side of the radial face at 271.8 deg)


def pin_y(r, x, y0, length, z, flat=(0, 0, -1)):
    """Printed pin along Y with a 0.3 mm flat on the side 'flat' (+-x or +-z), the face it prints on."""
    fx, _, fz = flat
    k = r - 0.3
    if fx:
        a, b = sorted((x + fx * k, x + fx * (r + 1)))
        cut = g.box_r(a, b, y0 - 1, y0 + length + 1, z - r - 1, z + r + 1)
    else:
        a, b = sorted((z + fz * k, z + fz * (r + 1)))
        cut = g.box_r(x - r - 1, x + r + 1, y0 - 1, y0 + length + 1, a, b)
    return g.cyl(r, length, (x, y0, z), (0, 1, 0)).cut(cut)



LANE_FASTENERS = {
    "M3 heat-set insert (lane bottom)": 3, "M3x12 SHCS (tooling plate -> lane, from below)": 3,
    "M2 heat-set insert": 4, "M2x6 knurled thumb screw (cover plate)": 2,
    "M2x6 SHCS (servo tabs)": 2,
}


def pick_xy(y):
    return P.PICK_X, y + POCKET_DY


def mount_points(y):
    """Lane bottom insert positions (x, y) for the tooling plate screws."""
    return [(531.0, y + 6.5), (588.0, y - 7.0), (648.0, y + 3.0)]


def pin_xy(y, th):
    a = math.radians(th)
    return SERVO_X + HORN_R * math.cos(a), y + HORN_R * math.sin(a)


def slider_dx(th):
    """Slider displacement from the forward end (0 .. +STROKE, +x = retract)."""
    return pin_xy(0.0, th)[0] - pin_xy(0.0, TH_FWD)[0]


def lift_dz(th):
    """Lifter height change from its highest pose (forward end); negative = lower."""
    return -LIFT_RATIO * slider_dx(th)


def pawl_angle(dz):
    """Angle (deg) of the lifter pawl tip about the roller axis; dz from lift_dz."""
    zt = LIFT_B + 42.94 + dz          # tooth top above the table
    return math.degrees(math.atan2(zt - ROLL_Z, LIFT_TOOTH_X - ROLL_X)) % 360


def peel_teeth(stroke):
    """Ratchet teeth advanced per slider stroke (steady state) and the pawl's angular travel."""
    travel = pawl_angle(-LIFT_RATIO * stroke) - pawl_angle(0.0)
    return int(travel // (360.0 / RAT_N)), travel


def _xz_poly(pts, y0, y1):
    """Prism from an XZ polygon, extruded y0..y1."""
    s = g.poly_face(pts).extrude(V(0, 0, y1 - y0))
    s.rotate(V(), V(1, 0, 0), 90)       # local y -> z, local z -> -y
    s.translate(V(0, y1, 0))
    return s


def _rz(shape, deg, c):
    s = shape.copy()
    s.rotate(V(*c), V(0, 0, 1), deg)
    return s


# ------------------------------------------------------------------ parts
def _body(y, zt):
    zb, ztp = zt + ZB, zt + TAPE_TOP
    y0, y1 = y - BW, y + BW
    xs = SERVO_X
    low = g.box_r(X_IN, X_TOWER, y0, y1, zt, zt + CH_TOP)
    tower = g.box_r(X_TOWER, X_OUT, y0, y1, zt, zt + TOP_T)
    post = g.box_r(X_TOWER, 598.5, y0, y1, zt + TOP_T - 1, zt + ROD[1] + 2.5)
    ch0, ch1 = CHEEK_X
    cheek_p = g.box_r(ch0, ch1, y + 6.5, y1, zt + TOP_T - 1, zt + CHEEK_TOP)
    cheek_m = g.box_r(ch0, 639.0, y0, y - 6.6, zt + TOP_T - 1, zt + CHEEK_TOP).fuse(
        g.box_r(ch0, ch1, y0, y - 6.6, zt + 44.0, zt + CHEEK_TOP))
    body = low.fuse([tower, post, cheek_p, cheek_m]).removeSplitter()
    body = g.fillet_safe(body, 0.8)

    cuts = []
    # tape channel (through), inlet flare, embossed pocket groove
    cuts.append(g.box_r(X_IN - 1, X_OUT + 1, y - CH_HW, y + CH_HW, zb, zt + CH_TOP))
    cuts.append(_xz_poly([(X_OUT - 4, zt + CH_TOP), (X_OUT + 1, zt + CH_TOP + 3), (X_OUT + 1, zt + CH_TOP)],
                         y - CH_HW - 1, y + CH_HW + 1))
    cuts.append(g.box_r(X_IN - 1, X_OUT + 1, y + GROOVE_Y[0], y + GROOVE_Y[1], zt + GROOVE_Z, zb + 0.1))
    # slider tunnel: narrow under the low section, wide (ear) in the tower, open at the rear face
    xt0 = W_HOOK - 1.4
    cuts.append(g.box_r(xt0, X_OUT + 1, y + TUN_N[0], y + TUN_N[1], zt + FLOOR, zt + TUN_TOP))
    pfx, _ = pin_xy(y, TH_FWD)
    cuts.append(g.box_r(pfx - 5.2, X_OUT + 1, y + TUN_W[0], y + TUN_W[1], zt + FLOOR, zt + TUN_TOP))
    cuts.append(g.box_r(xt0, X_OUT + 1, y + SLOT_Y[0], y + SLOT_Y[1], zt + TUN_TOP - 0.1, zb + 0.1))
    # pin passage (open +y face), horn chamber, servo pocket and tab ledge
    cuts.append(g.box_r(xs - 3.5, xs + 3.5, y + 4.9, y1 + 1, zt + TUN_TOP - 0.1, zt + TOP_T + 1))
    cuts.append(g.box_r(xs - 6.0, xs + 6.0, y - 4.5, y1 + 1, zt + 19.5, zt + ZF + 0.1))
    cuts.append(g.box_r(xs - 6.1, xs + 16.8, y - 6.2, y + 6.2, zt + ZF - 0.2, zt + TOP_T + 1))
    cuts.append(g.box_r(xs - 10.95, xs + 21.65, y - 6.2, y + 6.2, zt + ZF + 4.3, zt + TOP_T + 1))
    # cover tape riser groove (tower front) and channel over the guide rod
    cuts.append(g.box_r(X_TOWER - 1, X_TOWER + 3.2, y - 2.2, y + 4.7, zt + 16.9, zt + ROD[1] + 4))
    cuts.append(g.box_r(X_TOWER - 1, 599.0, y - 2.2, y + 4.7, zt + ROD[1] + 0.5, zt + ROD[1] + 4))
    # peel drive: lifter channel (-y side of the servo, open at the top), dowel slot from the slider tail
    # (open to the rear face for slider insertion), hold pawl peg hole in the tower top
    cuts.append(g.box_r(619.7, 632.1, y - 8.3, y - 6.1, zt + 1.5, zt + TOP_T + 1))
    cuts.append(g.box_r(PEG_X - PEG_R - 0.4, X_OUT + 1, y - 7.7, y - 3.7, zt + PEG_Z - PEG_R - 0.3,
                        zt + PEG_Z + PEG_R + 0.3))
    cuts.append(g.box_r(649.9, 652.1, y - 6.3, y - 2.3, zt + 32.0, zt + TOP_T + 0.1))
    # pinch yoke guide grooves (inner cheek faces, open at the top)
    cuts.append(g.box_r(ROLL_X - 1.4, ROLL_X + 1.4, y - 7.5, y - 6.5, zt + 55.0, zt + CHEEK_TOP + 1))
    cuts.append(g.box_r(ROLL_X - 1.4, ROLL_X + 1.4, y + 6.4, y + 7.4, zt + 55.0, zt + CHEEK_TOP + 1))
    # cover plate rear tab slots (room to swing the plate open)
    for s in (-1, 1):
        a, b = sorted((y + s * 5.3, y + s * 8.7))
        cuts.append(g.box_r(591.0 - PLATE_T - 0.4, 595.0, a, b, zt + 13.0, zt + CH_TOP + 0.1))
    body = body.cut(g.compound(cuts))

    # shafts and rod (press / running fits), fastener holes
    # cover tape guide rod moulded in: a D3 bar across the riser channel (was a stainless rod)
    body = body.fuse(g.cyl(1.5, 7.5, (ROD[0], y - 2.5, zt + ROD[1]), (0, 1, 0)))
    # snap pockets for the cheek cap legs (outer faces), with a notch for the lip
    for sd, x0, x1 in CAP_SNAPS:
        f = y + sd * BW
        body = body.cut(g.box_r(x0 - 0.1, x1 + 0.1, min(f - sd * 0.9, f + sd), max(f - sd * 0.9, f + sd),
                                zt + SNAP_Z - 0.4, zt + CHEEK_TOP + 1))
        body = body.cut(g.box_r(x0 - 0.1, x1 + 0.1, min(f - sd * 1.5, f), max(f - sd * 1.5, f),
                                zt + SNAP_Z - 0.4, zt + SNAP_Z + 1.0))
    body = body.cut(g.cyl(1.5, 2 * BW + 2, (ROLL_X, y0 - 1, zt + ROLL_Z), (0, 1, 0)))       # axle press fit
    body = g.drill(body, "M3", [(x, yy, zt) for x, yy in mount_points(y)], d=(0, 0, 1), depth=5.5, insert=True)
    body = g.drill(body, "M2", [(532.5, y - 7.0, zt + CH_TOP), (532.5, y + 7.0, zt + CH_TOP)], depth=4.5,
                   insert=True)
    body = g.drill(body, "M2", [(xs - 8.6, y, zt + ZF + 4.3), (xs + 19.2, y, zt + ZF + 4.3)], depth=4.5,
                   insert=True)
    return body.removeSplitter()


def _slider(y, zt):
    """Slider at the forward end: base + rib under the hole row, flexure pawl at the front, yoke ear."""
    w = W_HOOK
    pfx, _ = pin_xy(y, TH_FWD)
    xe = pfx + 4.7
    zs0 = zt + FLOOR + 0.1
    base = g.box_r(w, PEG_X + 2.5, y - 3.55, y + 1.0, zs0, zt + 12.4)        # tail carries the lifter peg
    rib = g.box_r(w + FLEX_L, xe, y - 3.55, y - 0.95, zt + 12.4, zt + 15.0)
    beam = g.box_r(w, w + FLEX_L, y - 3.55, y - 0.95, zt + 14.1, zt + 15.0)
    tooth = _xz_poly([(w, zt + 15.0), (w, zt + 15.85), (w + 0.3, zt + 15.85), (w + 1.15, zt + 15.0)],
                     y + HOLE_DY - 0.4, y + HOLE_DY + 0.4)
    ear = g.box_r(pfx - 4.7, xe, y - 3.55, y + 8.7, zs0, zt + 12.4)
    s = base.fuse([rib, beam, tooth, ear]).removeSplitter()
    s = s.cut(g.box_r(pfx - 1.05, pfx + 1.05, y + 4.8, y + 7.7, zs0 - 1, zt + 13))      # yoke slot
    s = s.cut(g.cyl(PEG_R, 6.0, (PEG_X, y - 4.0, zt + PEG_Z), (0, 1, 0)))              # peg press hole
    return s


def _peg(y, zt):
    """Printed D3 peg; prints lying on a flat on its +x side (low-load side, the feed load is on -x)."""
    return pin_y(PEG_R, PEG_X, y - 7.5, 8.0, zt + PEG_Z, flat=(1, 0, 0))


def _lifter(y, zt, dz=0.0):
    """Printed lifter, an XZ profile: foot with the inclined dowel slot (vertical entry at the bottom for
    assembly), thin bar in the tower channel, head with the hanging flexure pawl above the tower."""
    zb = zt + LIFT_B
    foot = g.box_r(620.0, 631.8, y + LIFT_Y[0], y + LIFT_Y[1], zb, zb + 12.0)
    bar = g.box_r(628.3, 631.8, y + LIFT_Y[0], y + LIFT_Y[1], zb + 11.9, zb + 35.5)
    yh0, yh1 = y + LIFT_YH[0], y + LIFT_YH[1]
    head = [g.box_r(628.3, 631.8, yh0, yh1, zb + 35.4, zb + 37.4),        # base
            g.box_r(628.3, 629.5, yh0, yh1, zb + 37.3, zb + LIFT_TOP),     # spine
            g.box_r(628.3, 631.6, yh0, yh1, zb + 59.9, zb + LIFT_TOP),     # top bridge
            g.box_r(630.8, 631.6, yh0, yh1, zb + 41.3, zb + 60.0)]         # flexure finger 0.8 x 5.8 x 18.6
    tooth = _xz_poly([(631.5, zb + 41.34), (LIFT_TOOTH_X, zb + 42.94), (631.5, zb + 42.94)], y - 6.2, yh1)
    s = foot.fuse([bar, tooth] + head).removeSplitter()
    # peg slot: centre line x = PEG_X + s, z = (PEG_Z - LIFT_B) + LIFT_RATIO * s above the foot (s = slider travel)
    r = PEG_R + 0.1
    p0, p1 = (PEG_X, PEG_Z - LIFT_B), (PEG_X + 4.6, PEG_Z - LIFT_B + LIFT_RATIO * 4.6)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    nx, nz = -math.sin(ang) * r, math.cos(ang) * r
    slot = _xz_poly([(p0[0] + nx, zb + p0[1] + nz), (p1[0] + nx, zb + p1[1] + nz),
                     (p1[0] - nx, zb + p1[1] - nz), (p0[0] - nx, zb + p0[1] - nz)], y - 9, y - 5)
    for px, pz in (p0, p1):
        slot = slot.fuse(g.cyl(r, 4, (px, y - 9, zb + pz), (0, 1, 0)))
    slot = slot.fuse(g.box_r(PEG_X - r, PEG_X + r, y - 9, y - 5, zb - 1, zb + p0[1]))     # vertical entry
    s = s.cut(slot).removeSplitter()
    if dz:
        s.translate(V(0, 0, dz))
    return s


def _ratchet(y, zt, rot=0.0):
    """Printed ratchet + hub (D-flat drives the TPU roller); runs on the stationary axle. rot: forward
    rotation in deg (top of the roller toward +x)."""
    pts = []
    pitch = 360.0 / RAT_N
    for k in range(RAT_N):
        a0 = RAT_FACE0 + k * pitch
        for j in range(7):                                  # ramp root -> tip, then the radial face
            a = math.radians(a0 + (pitch - 0.02) * j / 6)
            r = RAT_RR + (RAT_RT - RAT_RR) * j / 6
            pts.append((ROLL_X + r * math.cos(a), zt + ROLL_Z + r * math.sin(a)))
    wheel = _xz_poly(pts, y + RAT_Y[0], y + RAT_Y[1])
    hub = g.cyl(HUB_R, 4.25 - RAT_Y[1] + 0.01, (ROLL_X, y + RAT_Y[1] - 0.01, zt + ROLL_Z), (0, 1, 0))
    hub = hub.cut(g.box_r(ROLL_X - 4, ROLL_X + 4, y + RAT_Y[1], y + 5, zt + ROLL_Z + HUB_FLAT, zt + ROLL_Z + 4))
    s = wheel.fuse(hub).cut(g.cyl(BORE_R, 12, (ROLL_X, y - 7, zt + ROLL_Z), (0, 1, 0))).removeSplitter()
    if rot:
        s.rotate(V(ROLL_X, y, zt + ROLL_Z), V(0, 1, 0), rot)
    return s


def _hold_pawl(y, zt):
    """Printed hold pawl, an XZ profile: peg in the tower top, base, 0.8 mm flexure beam running forward under
    the ratchet, tooth that blocks backward rotation (the beam takes the load in compression)."""
    y0, y1 = y - 6.2, y - 2.4
    peg = g.box_r(650.0, 652.0, y0, y1, zt + 32.2, zt + TOP_T)
    base = g.box_r(649.5, 652.5, y0, y1, zt + TOP_T, zt + 41.0)
    beam = g.box_r(HOLD_X, 649.6, y0, y1, zt + 40.1, zt + 40.9)
    tooth = _xz_poly([(HOLD_X, zt + 40.85), (HOLD_X, zt + 41.95), (639.6, zt + 41.4), (639.6, zt + 40.85)], y0, y1)
    return peg.fuse([base, beam, tooth]).removeSplitter()


def _cover_plate(y, zt):
    return _cover_plate_printed(y, zt) if COVER_PLATE == "printed" else _cover_plate_steel(y, zt)


def _cover_plate_printed(y, zt):
    """PETG plate, 1.2 mm, printed upside down (tabs up). Same outline, window and peel slot as the steel plate;
    detent tongue 16 x 3 x 1.2 anchored at +X with a 1.0 x 0.9 mm tab, hook face at D_HOOK. The tape moving forward
    (-x) pushes the tab below the tongue axis, which bends the tongue up (as on the steel plate); a small chamfer
    on the +x edge helps; the hinge tabs are 1.2 mm thick."""
    z0, z1 = zt + CH_TOP, zt + CH_TOP + PLATE_T
    py = y + POCKET_DY
    cp = g.box_r(530.0, 591.0, y - 9.0, y + 9.0, z0, z1)
    tl, tw, _ = PT_TONGUE
    t0, t1 = D_HOOK, D_HOOK + tl
    yc = y + HOLE_DY
    cuts = [g.box_r(P.PICK_X - 4, P.PICK_X + 4, py - 2.6, py + 2.6, z0 - 1, z1 + 1),          # pick window
            g.box_r(P.PICK_X + 6, P.PICK_X + 8, y - 2.0, y + 4.5, z0 - 1, z1 + 1),           # peel slot
            g.box_r(t0 - PT_SLIT, t1, yc - tw / 2 - PT_SLIT, yc + tw / 2 + PT_SLIT, z0 - 1, z1 + 1)]
    cp = cp.cut(g.compound(cuts))
    tongue = g.box_r(t0, t1 + 0.01, yc - tw / 2, yc + tw / 2, z0, z1)
    a, aw, ch = PT_TAB
    tab = _xz_poly([(t0, z0 + 0.01), (t0, zt + DET_Z), (t0 + a - ch, zt + DET_Z), (t0 + a, zt + DET_Z + ch),
                    (t0 + a, z0 + 0.01)], yc - aw / 2, yc + aw / 2)
    cp = cp.fuse([tongue, tab])
    for s in (-1, 1):                                                                       # rear hinge tabs
        cp = cp.fuse(g.box_r(591.0 - PLATE_T, 591.0, min(y + s * 5.5, y + s * 8.5), max(y + s * 5.5, y + s * 8.5),
                             zt + 13.3, z0 + 0.01))
    cp = g.drill(cp, "M2", [(532.5, y - 7.0, z1), (532.5, y + 7.0, z1)], depth=PLATE_T + 1, cbore=0)
    return cp.removeSplitter()


def _cover_plate_steel(y, zt):
    z0, z1 = zt + CH_TOP, zt + CH_TOP + 0.5
    py = y + POCKET_DY
    cp = g.box_r(530.0, 591.0, y - 9.0, y + 9.0, z0, z1)
    cuts = [g.box_r(P.PICK_X - 4, P.PICK_X + 4, py - 2.6, py + 2.6, z0 - 1, z1 + 1),          # pick window
            g.box_r(P.PICK_X + 6, P.PICK_X + 8, y - 2.0, y + 4.5, z0 - 1, z1 + 1)]           # peel slot
    # detent tongue: anchored at +X, tip at -X, 2 wide, 0.5 slit around it
    t0, t1 = D_HOOK, D_HOOK + TONGUE_L
    cuts.append(g.box_r(t0 - 0.5, t1, y + HOLE_DY - 1.5, y + HOLE_DY + 1.5, z0 - 1, z1 + 1))
    cp = cp.cut(g.compound(cuts))
    tongue = g.box_r(t0, t1 + 0.01, y + HOLE_DY - 1.0, y + HOLE_DY + 1.0, z0, z1)
    tab = g.box_r(t0, t0 + 0.5, y + HOLE_DY - 0.4, y + HOLE_DY + 0.4, zt + DET_Z, z0 + 0.01)
    cp = cp.fuse([tongue, tab])
    for s in (-1, 1):                                                                       # rear hinge tabs
        cp = cp.fuse(g.box_r(590.5, 591.0, min(y + s * 5.5, y + s * 8.5), max(y + s * 5.5, y + s * 8.5),
                             zt + 13.3, z0 + 0.01))
    cp = g.drill(cp, "M2", [(532.5, y - 7.0, z1), (532.5, y + 7.0, z1)], depth=2, cbore=0)
    return cp.removeSplitter()


def _servo(y, zt):
    xs = SERVO_X
    case = g.box_r(xs - 5.9, xs + 16.6, y - 6.0, y + 6.0, zt + ZF, zt + ZF + 22.7)
    tabs = g.box_r(xs - 10.75, xs + 21.45, y - 6.0, y + 6.0, zt + ZF + 4.3, zt + ZF + 6.8)
    tabs = g.drill(tabs, "M2", [(xs - 8.6, y, zt + ZF + 6.8), (xs + 19.2, y, zt + ZF + 6.8)], depth=4, cbore=0,
                   screw=6)
    spl = g.cyl(2.4, 3.0, (xs, y, zt + ZF - 3.0))
    return case.fuse([tabs, spl])


def _horn(y, zt, th):
    xs = SERVO_X
    hub = g.cyl(3.6, 3.6, (xs, y, zt + ZF - 4.5))
    arm = g.box_r(xs, xs + HORN_R + 2.5, y - 2.5, y + 2.5, zt + ZF - 4.5, zt + ZF - 2.9)
    arm = _rz(arm, th, (xs, y, 0))
    px, py = pin_xy(y, th)
    return hub.fuse(arm).cut(g.cyl(2.45, 3.1, (xs, y, zt + ZF - 3.0))).cut(g.cyl(1.0, 3, (px, py, zt + ZF - 5)))


def _pin(y, zt, th):
    px, py = pin_xy(y, th)
    return g.cyl(1.0, 18.0, (px, py, zt + 6.0))


def build_lane(y, th=None):
    """Returns a list of (suffix, shape, colour, mat, mass, bom, kind) and records screws in geom.
    th = horn angle (deg); default is the forward end (model pose)."""
    zt = P.TABLE_TOP_Z
    th = TH_FWD if th is None else th
    ztp = zt + TAPE_TOP
    out = []
    out.append(("Body", _body(y, zt), g.C_ORANGE, "PETG", None, "Feeder v2.1 lane body (printed PETG)", "print"))
    sl = _slider(y, zt)
    if th != TH_FWD:
        sl.translate(V(pin_xy(y, th)[0] - pin_xy(y, TH_FWD)[0], 0, 0))
    out.append(("Slider", sl, g.C_BLUE, "PETG", None, "Feeder v2.1 slider with flexure pawl (printed PETG)",
                "print"))
    if COVER_PLATE == "printed":
        out.append(("CoverPlate", _cover_plate(y, zt), g.C_ORANGE, "PETG", None,
                    "Feeder v2.1 cover plate 1.2 mm with detent tongue (printed PETG, upside down)", "print"))
    else:
        out.append(("CoverPlate", _cover_plate(y, zt), g.C_STEEL, "steel", None,
                "Feeder cover plate 0.5 mm 1.4310 spring steel, laser cut + 3 bends (detent tongue)", "make"))
    out.append(("Servo_SG90", _servo(y, zt), g.C_BLUE, None, 9.0, "Servo SG90 9 g, 180 deg, analog (tape advance)",
                "buy"))
    out.append(("Horn", _horn(y, zt, th), g.C_WHITE, None, 0.5, None, "buy"))
    out.append(("HornPin", _pin(y, zt, th), g.C_STEEL, None, 0.4, "Dowel pin ISO 8734 2 x 18 m6 (horn pin)", "buy"))

    # ---------------------------------------------------------------- peel drive (from the slider)
    dz = lift_dz(th)
    peg = _peg(y, zt)
    lif = _lifter(y, zt, dz)
    if th != TH_FWD:
        peg.translate(V(slider_dx(th), 0, 0))
    out.append(("SliderPeg", peg, g.C_ORANGE, "PETG", None, "Slider peg D3 x 8 (printed PETG, lying)", "print"))
    out.append(("Lifter", lif, g.C_BLUE, "PETG", None, "Feeder v2.1 peel lifter with flexure pawl (printed PETG)",
                "print"))
    rat = _ratchet(y, zt)
    out.append(("Ratchet", rat, g.C_WHITE, "PETG", None, "Feeder v2.1 ratchet 18T + hub (printed PETG)", "print"))
    out.append(("HoldPawl", _hold_pawl(y, zt), g.C_BLUE, "PETG", None, "Feeder v2.1 hold pawl (printed PETG)",
                "print"))
    shaft = pin_y(1.5, ROLL_X, y - 10.0, 20.0, zt + ROLL_Z)          # flat at the bottom, load is on top
    out.append(("RollerShaft", shaft, g.C_ORANGE, "PETG", None,
                "Roller axle D3 x 20, stationary (printed PETG, lying)", "print"))
    dbore = g.cyl(HUB_R, 8.0, (ROLL_X, y - 2.5, zt + ROLL_Z), (0, 1, 0)).cut(
        g.box_r(ROLL_X - 4, ROLL_X + 4, y - 3, y + 6, zt + ROLL_Z + HUB_FLAT, zt + ROLL_Z + 4))
    roll = g.cyl(ROLL_R, 6.0, (ROLL_X, y - 1.75, zt + ROLL_Z), (0, 1, 0)).cut(dbore)
    out.append(("DriveRoller", roll, g.C_DARK, "TPU", None, "Drive roller D14 x 6, D-bore (printed TPU 95A)",
                "print"))
    # pinch yoke, roller and axle (all printed), spring, snap-on cap
    yk = g.box_r(ROLL_X - 3.6, ROLL_X + 3.6, y - 6.4, y + 6.3, zt + 56.5, zt + 64.5)
    yk = yk.fuse(g.box_r(ROLL_X + 3.6, ROLL_X + 7.5, y - 2.0, y + 2.0, zt + 63.0, zt + 64.5))       # lift tab
    for s in (-1, 1):
        yk = yk.fuse(g.cyl(1.2, 0.9, (ROLL_X, y - 6.4 if s < 0 else y + 6.3, zt + 62.5), (0, s, 0)))
    yk = yk.cut(g.box_r(ROLL_X - 3.9, ROLL_X + 3.9, y + POCKET_DY - 1.65, y + POCKET_DY + 1.65, zt + 54.0,
                        zt + PINCH_Z + 3.9))
    yk = yk.cut(g.cyl(1.5, 12.5, (ROLL_X, y - 5.4, zt + PINCH_Z), (0, 1, 0)))                # press fit from +y
    yk = yk.cut(g.cyl(2.7, 2.1, (ROLL_X, y - 0.45, zt + 63.0)))                             # spring seat
    out.append(("PinchYoke", yk.removeSplitter(), g.C_ORANGE, "PETG", None, "Pinch yoke (printed PETG)", "print"))
    prl = g.tube(3.5, 1.6, 3.0, (ROLL_X, y + POCKET_DY - 1.5, zt + PINCH_Z), (0, 1, 0))
    out.append(("PinchRoller", prl, g.C_WHITE, "PETG", None, "Pinch roller D7 x 3, runs on its axle (printed PETG)",
                "print"))
    out.append(("PinchAxle", pin_y(1.5, ROLL_X, y - 4.4, 10.0, zt + PINCH_Z), g.C_ORANGE, "PETG", None,
                "Pinch axle D3 x 10 (printed PETG, lying)", "print"))
    out.append(("PinchSpring", g.tube(2.5, 2.1, CHEEK_TOP - 63.0, (ROLL_X, y - 0.45, zt + 63.0)), g.C_STEEL, None,
                0.1, "Compression spring OD 5 x 0.4 wire x L0 9, ~0.75 N/mm (pinch, 1.5 N)", "buy"))
    cap = g.box_r(CHEEK_X[0], CHEEK_X[1], y - BW, y + BW, zt + CHEEK_TOP, zt + CHEEK_TOP + 2.0)
    cap = cap.fuse(g.box_r(627.5, CHEEK_X[0] + 0.5, y - 8.5, y - 1.7, zt + CHEEK_TOP, zt + CHEEK_TOP + 2.0))  # lifter stop
    for sd, x0, x1 in CAP_SNAPS:                                    # snap legs 0.85 thick, lip 0.5 into the notch
        f = y + sd * BW
        leg = g.box_r(x0, x1, min(f - sd * 0.02, f - sd * 0.87), max(f - sd * 0.02, f - sd * 0.87),
                      zt + SNAP_Z, zt + CHEEK_TOP + 0.01)
        lip = g.box_r(x0, x1, min(f - sd * 0.8, f - sd * 1.4), max(f - sd * 0.8, f - sd * 1.4),
                      zt + SNAP_Z, zt + SNAP_Z + 0.9)
        cap = cap.fuse([leg, lip])
    out.append(("CheekCap", cap.removeSplitter(), g.C_ORANGE, "PETG", None,
                "Cheek cap, snap-on, with lifter stop (printed PETG)", "print"))

    # fasteners from below (tooling plate -> lane), thumb screws
    for x, yy in mount_points(y):
        g._SCREWS.append(g.screw_solid("M3", (x, yy, zt - P.TABLE_T), (0, 0, 1), 12, head_at=0))
    for s in (-7.0, 7.0):
        g._SCREWS.append(g.screw_solid("M2", (532.5, y + s, zt + CH_TOP + PLATE_T), (0, 0, -1), 6, head_at=0))

    # ---------------------------------------------------------------- cover tape path
    c0, c1 = y + COVER_Y[0], y + COVER_Y[1]
    zp = zt + CH_TOP + PLATE_T
    ct = [g.box_r(P.PICK_X + 8, X_OUT + 12, c0, c1, ztp, ztp + COVER_T),                # still on the tape
          g.box_r(P.PICK_X + 8 - COVER_T, P.PICK_X + 8, c0, c1, ztp + COVER_T, zp),       # up the peel slot
          g.box_r(P.PICK_X + 8 - COVER_T, 591.0, c0, c1, zp, zp + COVER_T),              # back on the plate
          g.box_r(591.0, ROD[0] - 1.5, c0, c1, zt + 16.9, zt + 16.9 + COVER_T),           # onto the tower foot
          g.box_r(ROD[0] - 1.5 - COVER_T, ROD[0] - 1.5, c0, c1, zt + 16.9, zt + ROD[1]),  # riser
          g.box_r(ROD[0], X_OUT + 12, c0, c1, zt + ROD[1] + 1.5, zt + ROD[1] + 1.5 + COVER_T)]   # to the nip, out
    arc = g.tube(1.5 + COVER_T, 1.5, c1 - c0, (ROD[0], c0, zt + ROD[1]), (0, 1, 0))
    arc = arc.common(g.box_r(ROD[0] - 2, ROD[0], c0, c1, zt + ROD[1], zt + ROD[1] + 2))
    out.append(("CoverTape", g.compound(ct + [arc]), (0.85, 0.85, 0.95), None, 0.0, None, "buy"))

    # ---------------------------------------------------------------- carrier tape (paper) with holes and parts
    tape = g.box_r(X_IN - 6, X_OUT + 12, y - 4.0, y + 4.0, zt + ZB, ztp)
    holes, pockets, parts = [], [], []
    xh = HOLE_C0 - PITCH * math.floor((HOLE_C0 - X_IN + 6) / PITCH)
    while xh < X_OUT + 12:
        holes.append(g.cyl(HOLE_R, 2, (xh, y + HOLE_DY, zt + ZB - 0.5)))
        xh += PITCH
    xx = P.PICK_X - PITCH * math.floor((P.PICK_X - X_IN + 5) / PITCH)
    while xx < X_OUT + 11:
        pockets.append(g.box_c(xx, y + POCKET_DY, ztp - 0.35, 1.6, 1.0, 0.71))
        if xx >= P.PICK_X - 0.1:
            parts.append(g.box_c(xx, y + POCKET_DY, ztp - 0.35, 1.4, 0.8, 0.6))
        xx += PITCH
    tape = tape.cut(g.compound(holes + pockets))
    out.append(("Tape", tape, g.C_TAPE, None, 0.0, None, "buy"))
    out.append(("TapeParts", g.compound(parts), g.C_DARK, None, 0.0, None, "buy"))
    return out


# ------------------------------------------------------------------ bank parts (one per feeder bank)
REEL_X, REEL_Z = 760.0, 95.0       # reel axle, frame X and Z (bench at Z 0)
REEL_D, REEL_W = 178.0, 12.0       # 7" reel for 8 mm tape
EXIT_SLOT_X = (508.0, 522.0)       # empty-tape slot in the tooling plate


def bank_y(lanes_y):
    return min(lanes_y), max(lanes_y)


def bin_feet(lanes_y):
    ya, yb = bank_y(lanes_y)
    return [(655.0, ya - 17.0), (655.0, yb + 17.0)]


def build_bank(lanes_y):
    """Exit chute, waste bin, reel rack. Returns (name, shape, colour, mat, mass, bom, kind, fasteners)."""
    zt = P.TABLE_TOP_Z
    ya, yb = bank_y(lanes_y)
    out = []

    # empty tape exit chute: per lane a curved 1.6 mm channel from the lane exit down through the plate slot
    c0, c1 = ya - 12.0, yb + 12.0
    xc, zc = X_IN, zt + ZB - 11.0
    blk = g.box_r(505.0, X_IN, c0, c1, zt, zt + 16.7)
    chans = []
    for ly in lanes_y:
        a0, a1 = ly - 4.5, ly + 4.5
        ring = g.tube(12.6, 11.0, a1 - a0, (xc, a0, zc), (0, 1, 0))
        ring = ring.common(g.box_r(xc - 13, xc, a0, a1, zc, zc + 13))
        chans.append(ring)
        chans.append(g.box_r(xc - 12.6, xc - 11.0, a0, a1, zt - 1, zc + 0.01))
        chans.append(g.box_r(xc - 0.5, xc + 1, a0, a1, zt + ZB, zt + 16.8))
    blk = blk.cut(g.compound(chans))
    blk = blk.cut(g.box_r(EXIT_SLOT_X[0] + 0.5, EXIT_SLOT_X[1] - 0.5, c0 - 1, c1 + 1, zt - 1, zt + 2.0)
                  .cut(g.box_r(0, 1000, ya - 30, yb + 30, zt + 2.0 - 0.01, zt + 2.0)))
    mid = [(ya + yb) / 2]
    ribs = [c0 + 5.0, c1 - 5.0] + mid
    pts = [(506.5, r, zt + 16.7) for r in ribs] + [(524.0, r, zt + 16.7) for r in ribs]
    blk = g.drill(blk, "M3", pts, depth=17.7, cbore=3, screw=20)
    out.append(("Feeder_ExitChute", blk.removeSplitter(), g.C_ORANGE, "PETG", None,
                "Empty-tape exit chute, 8 lanes (printed PETG)", "print", {"M3x20 SHCS (chute -> plate)": 6}))

    # waste bin for used cover tape, standing on two legs on the plate behind the lanes
    b0, b1 = ya - 22.0, yb + 22.0
    bx0, bx1, bz0, bz1 = 651.0, 689.0, zt + 46.0, zt + 74.0
    tray = g.box_r(bx0, bx1, b0, b1, bz0, bz1).cut(g.box_r(bx0 + 2, bx1 - 2, b0 + 2, b1 - 2, bz0 + 2, bz1 + 1))
    tray = tray.cut(g.box_r(bx0 - 1, bx0 + 3, b0 + 6, b1 - 6, zt + 52.0, bz1 + 1))              # low front lip
    feet = bin_feet(lanes_y)
    tray = g.drill(tray, "M3", [(x, yy, bz0 + 2) for x, yy in feet], depth=3, cbore=0)
    out.append(("Feeder_WasteBin", tray.removeSplitter(), g.C_ORANGE, "PETG", None,
                "Cover tape waste bin (printed PETG)", "print", {"M3x55 SHCS + washer (bin + leg -> plate)": 2}))
    for k, (x, yy) in enumerate(feet):
        leg = g.box_r(x - 4, x + 4, yy - 5, yy + 5, zt, bz0)
        leg = g.drill(leg, "M3", [(x, yy, bz0 + 2)], depth=48, cbore=0)
        g._SCREWS.append(g.screw_solid("M3", (x, yy, bz0 + 2), (0, 0, -1), 55, head_at=0))
        out.append(("Feeder_WasteBinLeg_%d" % (k + 1), leg, g.C_ORANGE, "PETG", None, "Waste bin leg (printed PETG)",
                    "print", None))

    # reel rack: free standing on the bench behind the machine
    r0, r1 = ya - 6.3 - 0.3, yb + 15.7
    sides = []
    for k, (s0, s1) in enumerate(((r0 - 8, r0), (r1, r1 + 8))):
        sp = g.box_r(REEL_X - 60, REEL_X + 60, s0, s1, 0, 8).fuse(
            g.box_r(REEL_X - 10, REEL_X + 10, s0, s1, 0, REEL_Z)).fuse(
            g.cyl(12, s1 - s0, (REEL_X, s0, REEL_Z), (0, 1, 0)))
        for zz in (REEL_Z, 20.0):
            sp = sp.cut(g.cyl(4.3, 20, (REEL_X, s0 - 1, zz), (0, 1, 0)))
        out.append(("ReelRack_Side_%d" % (k + 1), sp.removeSplitter(), g.C_ORANGE, "PETG", None,
                    "Reel rack side plate (printed PETG)", "print", None))
        sides.append((s0, s1))
    rod_l = sides[1][1] - sides[0][0] + 20
    for k, zz in enumerate((REEL_Z, 20.0)):
        out.append(("ReelRack_Rod_%d" % (k + 1), g.cyl(4.0, rod_l, (REEL_X, sides[0][0] - 10, zz), (0, 1, 0)),
                    g.C_STEEL, "steel", None, "Threaded rod M8 x %.0f + 2 nuts + 2 washers (reel rack)" % rod_l,
                    "buy", None))
    for i, ly in enumerate(lanes_y):
        hub = g.cyl(6.4, 12.6, (REEL_X, ly - 6.3, REEL_Z), (0, 1, 0)).fuse(
            g.cyl(11.0, 9.4, (REEL_X, ly + 6.3, REEL_Z), (0, 1, 0)))
        hub = hub.cut(g.cyl(4.2, 30, (REEL_X, ly - 10, REEL_Z), (0, 1, 0)))
        out.append(("ReelHub_%d" % (i + 1), hub, g.C_ORANGE, "PETG", None, "Reel hub / spacer (printed PETG)",
                    "print", None))
        reel = g.cyl(REEL_D / 2, 1.2, (REEL_X, ly - REEL_W / 2, REEL_Z), (0, 1, 0)).fuse(
            g.cyl(REEL_D / 2, 1.2, (REEL_X, ly + REEL_W / 2 - 1.2, REEL_Z), (0, 1, 0))).fuse(
            g.cyl(30.0, REEL_W, (REEL_X, ly - REEL_W / 2, REEL_Z), (0, 1, 0)))
        reel = reel.cut(g.cyl(6.5, 30, (REEL_X, ly - 10, REEL_Z), (0, 1, 0)))
        out.append(("Reel_%d" % (i + 1), reel, (0.20, 0.45, 0.80), None, 0.0, None, "buy", None))
    return out

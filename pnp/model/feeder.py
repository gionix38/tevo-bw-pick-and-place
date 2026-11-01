"""TBW-Feeder v3.0: motorised 8 mm tape lane (0816 principle), one SG90 servo per lane.

v3.0 is the robust / easy-to-print rework of v2.1 after the first article (see feeder/DESIGN.md, TRIZ notes):
  advance   the servo hangs upside down in the tower; a 13T gear sector on its spline drives a rack on the
            slider (the rack arm rises beside the tape), stroke 4.2 = 37 deg, linear in the angle. The pawl is now a RIGID printed lever on a 2 mm steel pin with a steel
            spring; it is pivoted below and behind its tooth, so the push load drives the tooth deeper
            (self-locking, no flexure). Feed 4.0 mm per stroke, half strokes give 2 mm.
  detent    the same pawl part, pivoted in the body two holes ahead of the feed pawl, blocks back-drag.
  peel      gears + bought one-way bearings instead of the flexure ratchet: a rack fixed to the slider turns a
            36T idler, the idler a 14T m1 pinion printed in one piece with its 6 mm shaft; a one-way needle
            bearing (HF0612) in the drive roller turns it on the feed stroke only. The pinch roller below it runs
            on a second HF0612 on a fixed printed axle and holds
            the cover tape taut on the retract. The nip (two O-rings 12 x 1.5, steel spring 1.5 N) slips the
            20 % surplus and limits the peel tension.
  cover     printed plate in segmented rails (bayonet: slide 6.8 mm toward the pick, lift off), screwed home
            by 2 x M2 countersunk screws through its upstand into the tower; no snaps, no magnets.
  build     the body is split at y = SPLIT_Y into a main body and a side plate. Every pocket opens to the split
            face, so both print flat on their outer face without supports (0.4 mm nozzle). All moving parts are
            laid in from the split side, then 3 x M3 close the lane. Shafts, axles and the guide bar are printed PETG;
            bought metal: servo, 2 x HF0612, springs, screws, inserts, O-rings.
  control   one servo cable per lane to the bank controller (Arduino Nano + IO shield), firmware
            ../feeder/firmware (settings in microseconds). OpenPnP feeds with M600 N<lane> F<mm>.
Geometry in world (frame) coordinates; lane centre line at y. Model pose: slider at the forward end.
"""
import math

import FreeCAD as App
import Part

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
GROOVE_Z = 13.0           # groove floor: 2.4 mm embossed pockets clear, 1.2 mm roof over the slider tunnel
PITCH = P.TAPE_POCKET_PITCH
HOLE_C0 = P.PICK_X + 2.0   # hole centre next to the pick pocket (EIA P2 = 2.0)

# ------------------------------------------------------------------ lane body (main body + side plate)
BW = 10.25                 # body half width (lane pitch 22 -> 1.5 mm gap)
X_IN = 526.0               # inner end (empty tape exit)
X_TOWER = 592.0            # start of the tall part
X_OUT = 653.0              # rear face (tape inlet), below HEAD_Z0
X_HEAD_OUT = 652.0         # rear face of the peel head (the waste bin starts at 653.5)
FLOOR = 5.0                # floor slab (main body, full width); tunnel floor
SPLIT_Y = -4.85            # side plate (y < SPLIT_Y, above the floor slab) / main body
TUN_TOP = 11.8             # slider tunnel roof (the roof ties the sprocket-side tape floor to the body)
TUN_N = (SPLIT_Y, 1.25)    # slider tunnel under the tape (open to the split face)
TUN_W = (SPLIT_Y, 8.9)     # wide tunnel (slider ear)
TUN_T = (SPLIT_Y, 0.8)     # tail tunnel (clear of the rear mount insert)
SLOT_Y = (-2.85, -0.45)    # hole-row slot from the tunnel up to the tape (pawls)
TOP_T = 36.0               # tower top around the servo
POST_X = (592.0, 601.0)    # tower front post (cover tape riser + guide bar)
POST_TOP = 52.0
CHEEK_X = (628.0, X_HEAD_OUT)
CHEEK_TOP = 66.0

# ------------------------------------------------------------------ advance
STROKE = 4.2               # 4.0 feed + 0.2 free travel
SG_N, SG_M = 13, 1.0       # servo gear (sector) on the spline, drives the rack on the slider
SG_R = SG_N * SG_M / 2     # 6.5: the rack pitch line runs at y + 6.5, beside the tape
ALPHA = math.degrees(STROKE / 2 / SG_R)
TH_FWD = 90.0 + ALPHA      # servo angle at the forward end (37 deg stroke, linear in the angle)
TH_RET = 90.0 - ALPHA
SERVO_X = 611.0            # servo output axis
ZF = 27.1                  # servo case face on the output side (facing down); top 49.8, under the cover tape
SERVO_BOSS = (5.9, 4.0)    # round boss around the output gear (radius, height) below the case face
SERVO_SPLINE = (2.4, 2.8)  # output spline (radius, length) below the boss
SG_Z = (18.3, ZF - SERVO_BOSS[1] - 0.3)   # servo gear: bottom (over the rack flange) .. under the boss
SG_SECTOR = 55.0           # teeth within +-55 deg of the rack side; elsewhere cut back to the hub
SG_HUB = 4.5
SLIDER_RACK = (SG_Z[0] - 0.1, SG_Z[1] - 0.2)   # z range of the rack teeth on the slider arm
EAR_X = (SERVO_X - 9.0, SERVO_X + 9.0)   # slider ear + rack arm along x (model pose)
NECK_L = 5.0               # the rack arm stands on 2 necks (short passages through the body: bridges < 10)
FEED_BLOCK_X = (EAR_X[0] - 0.3, EAR_X[1] + STROKE + 0.3)   # tape channel under the servo: side plate (the arm lays in)
TOOTH_W = 0.8              # pawl tooth width across the tape (y)
TOOTH_H = 0.75             # tooth height above the tape underside (hook face)
CHORD = math.sqrt(HOLE_R ** 2 - (TOOTH_W / 2) ** 2)    # hook face to hole centre at the tooth edge
W_HOOK = HOLE_C0 + 4 * PITCH - CHORD                    # feed pawl hook face at the forward end
D_HOOK = HOLE_C0 - CHORD + 0.15                         # detent hook face (0.15 play)
PAWL_L = 8.5               # hook face -> pivot
PAWL_PZ = 9.6              # pivot height above the table
PAWL_Y = (HOLE_DY - TOOTH_W / 2, HOLE_DY - TOOTH_W / 2 + 2.0)   # pawl plate, tooth flush with its -y face
PAWL_SX = 2.2              # spring position behind the hook face
PAWL_BAR_Z = 11.8          # underside of the pawl bar (spring seat)
PAWL_FLOOR = 7.4           # fork floor = up-stop for the pawl tail
PAWL_SPRING_Z0 = 6.3       # spring seat (installed length 5.5)
PAWL_PIN = (-4.5, 0.5)     # 2 x 5 dowel, y

# ------------------------------------------------------------------ cover plate (printed, bayonet rails)
PLATE_T = 1.2
PLATE_X = (533.0, 591.9)
PLATE_HW = 8.25            # full-thickness half width
TONGUE = (8.25, 9.25, 0.7)   # rail tongue |y| range and thickness
LIP_Y = (8.45, 10.25)
LIP_Z = (CH_TOP + 0.8, CH_TOP + 2.0)      # lip over the tongue (top 18.3)
RAIL_X = (534.5, 548.5, 562.5)            # lip segments, 6 long
RAIL_L = 6.0
SLIDE = 6.8                # plate travel toward -x to release the tongues
UPSTAND = (588.0, PLATE_X[1], -9.25, -1.8, CH_TOP + PLATE_T, 26.8)   # screw upstand on the plate (-y)
CP_SCREWS = ((-6.3, 19.9), (-6.3, 24.1))  # (y, z): M2 x 8 countersunk, axis x, upstand -> tower (side plate)
CSK = (2.0, 1.1)           # countersink radius at the face (DIN 965 M2 head 3.8), clearance radius
REAR_TONGUES = ((-8.0, -4.4), (4.4, 8.0))  # rear tongues into the post

# ------------------------------------------------------------------ peel (gears + one-way bearings)
NIP_Z = 50.94              # cover tape underside at the nip (horizontal run over the servo)
ROLL_X = 638.0
ROLL_R = 8.0               # O-ring OD 16 (2 x 12 x 1.5 on a D13 groove)
ROLL_Z = NIP_Z + COVER_T + ROLL_R
PINCH_R = ROLL_R           # same roller as the drive roller (O-rings): it holds the full nip force on the retract
PINCH_Z = NIP_Z - PINCH_R
ROLL_Y = (-6.0, 6.0)       # both rollers: 12 mm, the HF0612 length
OWB = (10.0, 6.0, 12.0)    # HF0612: OD, bore, length
PIN_N, PIN_M = 14, 1.0     # pinion
PIN_RP = PIN_N * PIN_M / 2
GEAR_Y = (-8.2, -6.4)      # gear plane: rack, idler, pinion (side plate pocket -8.4 .. split face)
PIN_Y = GEAR_Y
RACK_ADD = 0.8             # shortened rack addendum
SHAFT_Y = (-8.2, 10.15)    # D6 drive shaft, printed on the pinion (pinion -y face .. +y body face)
SHAFT_PIN = (1.45, -5.0)   # side plate journal pin into the shaft end: radius, +y end (from the pocket floor)
SHAFT_BORE = (1.65, -4.6)  # bore in the shaft end: radius, bottom (then a 45 deg tip)
PINCH_AXLE_Y = (-6.1, 7.9)  # D6 x 14 printed axle, pressed into the single +y yoke arm (the idler runs on the -y side)
YOKE_ARM_Y = 6.2, 8.6
YOKE_X = (633.8, 642.2)
YOKE_Z0 = NIP_Z - 2 * PINCH_R - 1.95   # bridge underside = spring top (bridge 1.6, 0.35 under the roller)
SPRING_Z0 = YOKE_Z0 - 7.0  # pinch spring seat (installed 7.0, L0 9)
ROD = (596.2, NIP_Z - 1.5)  # D2.9 printed guide bar with a head (its counterbore clears the post front)
ROD_Y = (SPLIT_Y, 8.4)     # the bar ends at 8.4, pushed into the post
ROD_HEAD = (2.9, 3.0)      # head radius, height (in the side plate counterbore)
RISER_Y = (-2.2, 4.7)      # cover tape riser in the post

# ------------------------------------------------------------------ peel drive (servo powered, gears only)
# A rack fixed to the slider (teeth up) turns a 36T idler, the idler turns the 14T pinion on the drive shaft.
# Rack -> idler -> pinion gives the winding direction; the idler size doesn't change the ratio (4.8 mm / stroke).
IDL_N = 36
IDL_R = IDL_N * PIN_M / 2
IDL_Z = 34.8               # idler axis height (its stub clears the servo tabs, axle behind the case)
IDL_X = ROLL_X - math.sqrt((IDL_R + PIN_RP) ** 2 - (ROLL_Z - IDL_Z) ** 2)
RACK_Z = IDL_Z - IDL_R     # rack pitch line
RACK_X = (624.9, 640.0)    # rack part along x (model pose)
RACK_PINS = ((628.5, 8.0), (636.5, 8.0))   # M2 x 6 screws: rack -> slider tail (x, z)
IDL_STUB = (2.5, -10.2)    # idler axle stub printed on the gear: radius, -y end (runs in a hole through the side plate)
SLIDER_END = 641.0
RACK_GAP_X = (624.6, 645.5)   # no side plate wall over the tape channel here (the rack passes it)
A_ROT0 = -90.0 + 180.0 / IDL_N              # an idler space at the bottom, a rack tooth under it
_PHI = math.degrees(math.atan2(ROLL_Z - IDL_Z, ROLL_X - IDL_X))
_DEL = (_PHI - A_ROT0) % (360.0 / IDL_N)    # idler tooth this far before the line of centres
PIN_ROT0 = _PHI + 180.0 + _DEL * IDL_R / PIN_RP + 180.0 / PIN_N   # the pinion space that meets it

SIDE_SCREWS = ((533.0, 10.0), (601.5, 25.0), (648.6, 9.5))   # (x, z): side plate -> body


def pin_y(r, x, y0, length, z):
    return g.cyl(r, length, (x, y0, z), (0, 1, 0))


LANE_FASTENERS = {
    "M3 heat-set insert (lane bottom + side plate joint)": 6,
    "M3x8 SHCS (tooling plate -> lane, from below)": 3,
    "M3x10 SHCS (side plate -> body)": 3,
    "M2x8 countersunk DIN 965 (cover plate upstand -> tower)": 2,
    "M2x6 SHCS (take-up rack -> slider)": 2,
    "M2x6 screw (servo gear on the spline, from the servo kit)": 1,
}


def pick_xy(y):
    return P.PICK_X, y + POCKET_DY


def mount_points(y):
    """Lane bottom insert positions (x, y) for the tooling plate screws."""
    return [(531.0, y + 6.5), (588.0, y - 7.0), (648.0, y + 3.0)]


def _neck_x():
    return EAR_X[0], EAR_X[1] - NECK_L


def slider_dx(th):
    """Slider displacement from the forward end (0 .. +STROKE, +x = retract): rack and pinion, linear."""
    return SG_R * math.radians(TH_FWD - th)


def idler_rot(s):
    """Idler rotation (deg about +y) for a slider travel s (+x = retract) from the forward end."""
    return -math.degrees(s / IDL_R)


def pinion_rot(s):
    """Pinion / drive shaft rotation (deg about +y) for a slider travel s."""
    return math.degrees(s / PIN_RP)


def peel_per_stroke(stroke):
    """Drive roller surface per slider stroke (mm)."""
    return stroke * ROLL_R / PIN_RP


def _xz_poly(pts, y0, y1):
    """Prism from an XZ polygon, extruded y0..y1."""
    s = g.poly_face(pts).extrude(V(0, 0, y1 - y0))
    s.rotate(V(), V(1, 0, 0), 90)       # local y -> z, local z -> -y
    s.translate(V(0, y1, 0))
    return s


def _yz_poly(pts, x0, x1):
    """Prism from a YZ polygon, extruded x0..x1."""
    w = Part.makePolygon([V(x0, yy, zz) for yy, zz in pts] + [V(x0, *pts[0])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


def _rz(shape, deg, c):
    s = shape.copy()
    s.rotate(V(*c), V(0, 0, 1), deg)
    return s


# ------------------------------------------------------------------ gears
def _gear_pts(n, m, cx, cz, rot0=0.0, backlash=0.1, add=1.0, ded=1.25, steps=6):
    """Involute spur gear outline in the XZ plane (angle 0 = +x), tooth k centred at rot0 + k * 360 / n."""
    rp = n * m / 2
    al = math.radians(20.0)
    rb, ra, rf = rp * math.cos(al), rp + add * m, rp - ded * m
    inv = lambda a: math.tan(a) - a                                        # noqa: E731
    psi = (math.pi * m / 2 - backlash) / (2 * rp) + inv(al)

    def half(r):
        return psi - inv(math.acos(min(1.0, rb / r)))
    r0 = max(rb, rf)
    rs = [r0 + (ra - r0) * i / steps for i in range(steps + 1)]
    pts = []
    for k in range(n):
        c = math.radians(rot0) + k * 2 * math.pi / n
        tooth = ([(rf, c - half(r0))] if rf < rb else []) + [(r, c - half(r)) for r in rs]
        tooth += [(r, c + half(r)) for r in reversed(rs)] + ([(rf, c + half(r0))] if rf < rb else [])
        nxt = c + 2 * math.pi / n - half(r0)
        a0 = c + half(r0)
        tooth += [(rf, a0 + (nxt - a0) * j / 3) for j in (1, 2)]
        pts += tooth
    return [(cx + r * math.cos(a), cz + r * math.sin(a)) for r, a in pts]


def _rack_teeth(x0, x1, z_pitch, y0, y1, backlash=0.1, m=PIN_M):
    """Rack teeth pointing +z along x, pitch line z_pitch; a tooth centred at IDL_X (model pose)."""
    t = math.tan(math.radians(20.0))
    s_ = math.pi * m / 2 - backlash
    zt_, zr_ = z_pitch + RACK_ADD * m, z_pitch - 1.25 * m
    ht, hr = s_ / 2 - RACK_ADD * m * t, s_ / 2 + 1.25 * m * t
    k0 = math.ceil((x0 + hr - IDL_X) / (math.pi * m))
    k1 = math.floor((x1 - hr - IDL_X) / (math.pi * m))
    return [_xz_poly([(xc - hr, zr_ - 0.01), (xc - ht, zt_), (xc + ht, zt_), (xc + hr, zr_ - 0.01)], y0, y1)
            for xc in (IDL_X + k * math.pi * m for k in range(k0, k1 + 1))]


def _xy_prism(pts, z0, z1):
    w = Part.makePolygon([V(x_, y_, z0) for x_, y_ in pts] + [V(pts[0][0], pts[0][1], z0)])
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def _rack_teeth_y(x0, x1, y_pitch, z0, z1, backlash=0.1, m=SG_M):
    """Rack teeth along x pointing -y (toward the servo gear), pitch line y_pitch. At the forward end a tooth sits
    under the gear space that faces the rack when the gear is at 90 deg, shifted by the slider travel to 90 deg."""
    t = math.tan(math.radians(20.0))
    s_ = math.pi * m / 2 - backlash
    yt, yr = y_pitch - RACK_ADD * m, y_pitch + 1.25 * m
    ht, hr = s_ / 2 - RACK_ADD * m * t, s_ / 2 + 1.25 * m * t
    xc0 = SERVO_X - slider_dx(90.0)
    k0 = math.ceil((x0 + hr - xc0) / (math.pi * m))
    k1 = math.floor((x1 - hr - xc0) / (math.pi * m))
    return [_xy_prism([(xc - hr, yr + 0.01), (xc - ht, yt), (xc + ht, yt), (xc + hr, yr + 0.01)], z0, z1)
            for xc in (xc0 + k * math.pi * m for k in range(k0, k1 + 1))]


# ------------------------------------------------------------------ pawl (feed and detent are the same part)
def _pawl(h, y, zt):
    """Rigid printed pawl, an XZ profile: tooth (hook face at x = h), bar under the tape, pivot boss at
    h + PAWL_L below the bar, tail behind the pivot (its underside on the fork floor is the up-stop).
    The tooth is flush with the -y face, so the part prints on that face."""
    hp = h + PAWL_L
    y0, y1 = y + PAWL_Y[0], y + PAWL_Y[1]
    bar = g.box_r(h, hp + 1.0, y0, y1, zt + PAWL_BAR_Z, zt + ZB - 0.1)
    boss = g.cyl(2.2, y1 - y0, (hp, y0, zt + PAWL_PZ), (0, 1, 0))
    web = g.box_r(hp - 2.2, hp + 1.0, y0, y1, zt + PAWL_PZ, zt + PAWL_BAR_Z + 0.01)
    tail = g.box_r(hp, hp + 3.2, y0, y1, zt + PAWL_FLOOR, zt + PAWL_PZ + 1.0)
    zb = zt + ZB - 0.1
    tooth = _xz_poly([(h, zb - 0.01), (h, zt + ZB + TOOTH_H), (h + 0.3, zt + ZB + TOOTH_H),
                      (h + 0.3 + TOOTH_H + 0.1, zb - 0.01)], y0, y0 + TOOTH_W)
    s = bar.fuse([boss, web, tail, tooth]).removeSplitter()
    return s.cut(g.cyl(1.05, 12, (hp, y - 6, zt + PAWL_PZ), (0, 1, 0)))


def _pawl_slot_x():
    """x range of the hole-row slot over the feed pawl (bar + stroke)."""
    return W_HOOK - 0.5, W_HOOK + PAWL_L + 1.5 + STROKE


def _pawl_housing(h, y, zt, open_front=0.4):
    """Cavity for a pawl (fork slot, spring bore) and its pin hole, as one cut tool."""
    hp = h + PAWL_L
    cuts = [g.box_r(h - open_front, hp + 3.6, y + SLOT_Y[0], y + SLOT_Y[1], zt + PAWL_FLOOR, zt + ZB + 0.1),
            g.cyl(1.65, ZB + 0.1 - PAWL_SPRING_Z0, (h + PAWL_SX, y + sum(PAWL_Y) / 2, zt + PAWL_SPRING_Z0))]
    return cuts


def _pawl_spring(h, y, zt):
    return g.tube(1.5, 1.2, PAWL_BAR_Z - PAWL_SPRING_Z0, (h + PAWL_SX, y + sum(PAWL_Y) / 2, zt + PAWL_SPRING_Z0))


def _pawl_pin(h, y, zt):
    """M2 x 5 set screw as the pawl pivot, threaded into the printed 1.6 holes of both walls."""
    return pin_y(1.0, h + PAWL_L, y + PAWL_PIN[0], PAWL_PIN[1] - PAWL_PIN[0], zt + PAWL_PZ)


# ------------------------------------------------------------------ body
_BODY = {}


def _body_full(y, zt):
    """The whole lane body (main body + side plate before the split), cached per lane."""
    key = (round(y, 3), round(zt, 3))
    if key not in _BODY:
        _BODY[key] = _body_cut(y, zt)
    return _BODY[key]


def _body_cut(y, zt):
    y0, y1 = y - BW, y + BW
    xs = SERVO_X
    low = g.box_r(X_IN, X_TOWER, y0, y1, zt, zt + CH_TOP)
    tower = g.box_r(X_TOWER, X_OUT, y0, y1, zt, zt + TOP_T)
    post = g.box_r(POST_X[0], POST_X[1], y0, y1, zt + TOP_T - 1, zt + POST_TOP)
    ch0, ch1 = CHEEK_X
    cheek_p = g.box_r(ch0, ch1, y + YOKE_ARM_Y[0], y1, zt + TOP_T - 1, zt + CHEEK_TOP)
    cheek_m = g.box_r(ch0, ch1, y0, y + SPLIT_Y, zt + TOP_T - 1, zt + CHEEK_TOP)
    lips = []
    for xk in RAIL_X:
        for sd in (-1, 1):
            a, b = sorted((y + sd * LIP_Y[0], y + sd * LIP_Y[1]))
            lips.append(g.box_r(xk, xk + RAIL_L, a, b, zt + CH_TOP - 0.01, zt + LIP_Z[1]))
    body = low.fuse([tower, post, cheek_p, cheek_m] + lips).removeSplitter()
    # the rear above the tower top ends at X_HEAD_OUT (waste bin)
    body = body.cut(g.box_r(X_HEAD_OUT, X_OUT + 1, y0 - 1, y1 + 1, zt + TOP_T, zt + 80))

    cuts = []
    # rail grooves under the lips (the plate tongues slide in)
    for xk in RAIL_X:
        for sd in (-1, 1):
            a, b = sorted((y + sd * LIP_Y[0], y + sd * (TONGUE[1] + 0.1)))
            cuts.append(g.box_r(xk - 1, xk + RAIL_L + 1, a, b, zt + CH_TOP - 0.1, zt + LIP_Z[0]))
    # tape channel (through), inlet flare, embossed pocket groove
    cuts.append(g.box_r(X_IN - 1, X_OUT + 1, y - CH_HW, y + CH_HW, zt + ZB, zt + CH_TOP))
    cuts.append(_xz_poly([(X_OUT - 4, zt + CH_TOP), (X_OUT + 1, zt + CH_TOP + 3), (X_OUT + 1, zt + CH_TOP)],
                         y - CH_HW - 1, y + CH_HW + 1))
    cuts.append(g.box_r(X_IN - 1, X_OUT + 1, y + GROOVE_Y[0], y + GROOVE_Y[1], zt + GROOVE_Z, zt + ZB + 0.1))
    # 45 deg on the sprocket-side edge of the groove: printed lying (+y down) it would be a 2.1 mm ledge;
    # the groove keeps its full width at the floor (embossed pockets)
    g0, d = y + GROOVE_Y[0], ZB - GROOVE_Z
    cuts.append(_yz_poly([(g0, zt + GROOVE_Z), (g0 + 0.01, zt + ZB + 0.1), (g0 - d - 0.1, zt + ZB + 0.1)],
                         X_IN - 1, X_OUT + 1))
    cuts.append(_yz_poly([(y + GROOVE_Y[1], zt + GROOVE_Z), (y + GROOVE_Y[1] + ZB - GROOVE_Z + 0.1, zt + ZB + 0.1),
                          (y + GROOVE_Y[1] - 0.01, zt + ZB + 0.1)], *FEED_BLOCK_X))   # +y edge, side plate block
    # the sprocket-side channel wall above the tape floor is side plate (_side_region); over the rack it would
    # have to pass through the rack when the side plate comes off, so there it is left out
    cuts.append(g.box_r(*RACK_GAP_X, y + SPLIT_Y, y - CH_HW + 0.01, zt + ZB, zt + CH_TOP + 0.1))
    # slider tunnel (open to the split face): narrow under the low section, ear, tail
    xt0 = W_HOOK - 1.8
    ear0, ear1 = EAR_X[0] - 0.3, EAR_X[1] + STROKE + 0.3
    tail1 = SLIDER_END + STROKE + 0.5
    cuts.append(g.box_r(xt0, ear0 + 0.01, y + TUN_N[0], y + TUN_N[1], zt + FLOOR, zt + TUN_TOP))
    cuts.append(g.box_r(ear0, ear1, y + TUN_W[0], y + TUN_W[1], zt + FLOOR, zt + TUN_TOP))
    cuts.append(g.box_r(ear1 - 0.01, tail1, y + TUN_T[0], y + TUN_T[1], zt + FLOOR, zt + TUN_TOP))
    cuts.append(g.box_r(*_pawl_slot_x(), y + SLOT_Y[0], y + SLOT_Y[1], zt + TUN_TOP - 0.1, zt + ZB + 0.1))
    # detent pawl housing (closed to the split face; the pin goes in from the split face)
    cuts += _pawl_housing(D_HOOK, y, zt, open_front=1.0)
    cuts.append(pin_y(0.8, D_HOOK + PAWL_L, y + SPLIT_Y, PAWL_PIN[1] - SPLIT_Y, zt + PAWL_PZ))   # M2 set screw pilot
    # rack arm passage beside the tape (+y), servo gear chamber over the tape, boss pocket, servo pocket with
    # the tab slot (the tabs are captured, no screws)
    for x0_ in _neck_x():                        # neck passages up from the ear tunnel
        cuts.append(g.box_r(x0_ - 0.3, x0_ + NECK_L + STROKE + 0.3, y + 5.5, y + 9.3, zt + TUN_TOP - 0.3,
                            zt + SG_Z[0] - 0.5))
    cuts.append(g.box_r(ear0, ear1, y + SPLIT_Y, y + 9.3, zt + SG_Z[0] - 0.9, zt + SLIDER_RACK[1] + 0.4))
    cuts.append(g.box_r(xs - SG_R - 1.4, xs + SG_R + 1.4, y + SPLIT_Y, y + 5.3, zt + SG_Z[0] - 0.3, zt + ZF + 0.1))
    cuts.append(g.box_r(xs - 6.2, xs + 6.2, y - 6.2, y + 6.2, zt + ZF - SERVO_BOSS[1] - 0.3, zt + ZF + 0.1))
    cuts.append(g.box_r(xs - 6.1, xs + 16.8, y - 6.2, y + 6.2, zt + ZF - 0.2, zt + 60))
    cuts.append(g.box_r(xs - 10.95, xs + 23.5, y - 6.2, y + 6.2, zt + ZF + 4.15, zt + ZF + 6.9))   # runs into the pinch pocket
    # cover tape riser (from the plate top) up the post, guide bar hole, plate tongue slots, cover screw pilots
    cuts.append(g.box_r(X_TOWER - 1, POST_X[0] + 5.5, y + RISER_Y[0], y + RISER_Y[1], zt + CH_TOP + PLATE_T,
                        zt + POST_TOP + 1))
    cuts.append(pin_y(1.5, ROD[0], y + SPLIT_Y, ROD_Y[1] - SPLIT_Y + 0.3, zt + ROD[1]))   # bar (push fit in the post)
    cuts.append(g.box_r(ROD[0], POST_X[1] + 1, y + SPLIT_Y, y + RISER_Y[1], zt + NIP_Z - 0.6, zt + POST_TOP + 1))
    for a, b in REAR_TONGUES:
        cuts.append(g.box_r(X_TOWER - 0.2, X_TOWER + 3.2, y + a - 0.2, y + b + 0.2, zt + CH_TOP, zt + CH_TOP + PLATE_T))
    for my, mz in CP_SCREWS:
        cuts.append(g.cyl(0.8, 6.5, (X_TOWER - 0.5, y + my, zt + mz), (1, 0, 0)))   # M2 pilot (self-tapping)
    # peel head: drive roller / pinion / pinch roller pockets, yoke grooves + bridge pocket, spring pocket,
    # tab slot through the rear, lifter pocket (side plate, open to the split face), shaft holes
    rc, pc = (ROLL_X, zt + ROLL_Z), (ROLL_X, zt + PINCH_Z)
    cuts.append(g.cyl(ROLL_R + 0.4, 8.4 + YOKE_ARM_Y[0], (rc[0], y - 8.4, rc[1]), (0, 1, 0)))
    for dz_ in (0.0, -3.2):                         # pinch roller pocket: the yoke opens 3 mm
        cuts.append(g.cyl(PINCH_R + 0.4, 12.4, (pc[0], y - 6.2, pc[1] + dz_), (0, 1, 0)))
    cuts.append(g.box_r(pc[0] - PINCH_R - 0.4, pc[0] + PINCH_R + 0.4, y - 6.2, y + 6.2, pc[1] - 3.2, pc[1]))
    cuts.append(g.box_r(pc[0] - PINCH_R - 0.4, pc[0] + PINCH_R + 0.4, y - 6.2, y + SPLIT_Y + 0.01, pc[1], rc[1]))   # no sliver at the nip
    ya0, ya1 = YOKE_ARM_Y
    cuts.append(g.box_r(YOKE_X[0] - 0.2, YOKE_X[1] + 0.2, y + ya0 - 0.01, y + ya1 + 0.2, zt + YOKE_Z0 - 3.2,
                        zt + PINCH_Z + 4.6))                         # single +y arm
    cuts.append(g.box_r(YOKE_X[0] - 0.4, YOKE_X[1] + 0.4, y - 6.2, y + ya1 + 0.2, zt + YOKE_Z0 - 3.2,
                        zt + YOKE_Z0 + 2.0))
    cuts.append(g.box_r(YOKE_X[1] - 0.1, X_OUT + 1, y + SPLIT_Y, y + 2.2, zt + YOKE_Z0 - 3.2, zt + YOKE_Z0 + 2.0))
    cuts.append(g.cyl(2.7, YOKE_Z0 - SPRING_Z0 + 0.1, (ROLL_X, y, zt + SPRING_Z0)))
    cuts.append(g.box_r(ROLL_X - 2.7, ROLL_X + 2.7, y + SPLIT_Y, y, zt + SPRING_Z0, zt + YOKE_Z0 + 0.1))   # lays in with the yoke
    cuts.append(pin_y(3.1, ROLL_X, y + GEAR_Y[0] - 0.2, BW - GEAR_Y[0] + 1.2, zt + ROLL_Z))   # shaft (side plate: pin)
    # gear train in the side plate (open to the split face): rack travel, idler, idler stub hole
    cuts.append(g.box_r(RACK_X[0] - 0.3, RACK_X[1] + STROKE + 0.3, y + GEAR_Y[0] - 0.2, y + SPLIT_Y + 0.01,
                        zt + FLOOR, zt + RACK_Z + RACK_ADD + 0.4))
    cuts.append(g.cyl(IDL_R + 1.4, SPLIT_Y + 0.01 - GEAR_Y[0] + 0.2, (IDL_X, y + GEAR_Y[0] - 0.2, zt + IDL_Z), (0, 1, 0)))
    cuts.append(pin_y(IDL_STUB[0] + 0.15, IDL_X, y - BW - 1, BW + 1 + GEAR_Y[0] - 0.19, zt + IDL_Z))   # idler stub hole
    # cover tape through the peel head (between the cheeks) and out at the rear
    cuts.append(g.box_r(ch0 - 1, X_OUT + 1, y - 2.2, y + 4.7, zt + NIP_Z - 1.0, zt + NIP_Z + 1.5))
    body = body.cut(g.compound(cuts))
    # guide bar (printed) and pawl pins (set screws) are separate
    return body.removeSplitter()


def _side_region(y, zt):
    """What of the full body belongs to the side plate: everything -y of SPLIT_Y above the floor slab, the
    tape floor strip beside the feed pawl slot (over the slot it would be a 15 mm bridge in the main body), the
    sprocket-side channel wall (a ledge in print) and the -y wall of the cover tape riser in the post."""
    return g.box_r(X_IN - 5, X_OUT + 5, y - BW - 1, y + SPLIT_Y, zt + FLOOR, zt + 100).fuse([
        g.box_r(*_pawl_slot_x(), y + SPLIT_Y - 0.01, y + SLOT_Y[0], zt + TUN_TOP - 0.2, zt + CH_TOP),
        g.box_r(*FEED_BLOCK_X, y + SPLIT_Y - 0.01, y + 5.5, zt + TUN_TOP, zt + SG_Z[0] - 0.9),
        g.box_r(X_IN - 5, RACK_GAP_X[0], y + SPLIT_Y - 0.01, y - CH_HW, zt + ZB, zt + CH_TOP),
        g.box_r(RACK_GAP_X[1], X_OUT + 5, y + SPLIT_Y - 0.01, y - CH_HW, zt + ZB, zt + CH_TOP),
        g.box_r(X_TOWER - 1, POST_X[0] + 6.5, y + SPLIT_Y - 0.01, y + RISER_Y[0], zt + CH_TOP + PLATE_T,
                zt + POST_TOP + 1),
        g.box_r(X_TOWER - 1, POST_X[0] + 7.3, y + SPLIT_Y - 0.01, y + RISER_Y[0], zt + ROD[1] - 4.0,
                zt + POST_TOP + 1)]).removeSplitter()


def _main_body(y, zt):
    full = _body_full(y, zt)
    body = full.cut(_side_region(y, zt)).removeSplitter()
    body = g.drill(body, "M3", [(x, yy, zt) for x, yy in mount_points(y)], d=(0, 0, 1), depth=5.5, insert=True)
    body = g.drill(body, "M3", [(x, y + SPLIT_Y, zt + z) for x, z in SIDE_SCREWS], d=(0, 1, 0), depth=5.0,
                   insert=True)
    return body.removeSplitter()


def _side_plate(y, zt):
    full = _body_full(y, zt)
    sp = full.common(_side_region(y, zt)).removeSplitter()
    # room for the rear mount insert's screw tip, screws with counterbored heads on the outer face
    x, yy = mount_points(y)[1]
    sp = sp.cut(g.cyl(2.0, 1.0, (x, yy, zt + FLOOR - 0.1)).fuse(g.box_r(x - 2, x + 2, yy, y + SPLIT_Y + 0.1, zt + FLOOR - 0.1,
                                                                        zt + FLOOR + 0.9)))
    sp = g.drill(sp, "M3", [(x, y - BW, zt + z) for x, z in SIDE_SCREWS], d=(0, 1, 0), depth=6.0, cbore=3.2,
                 screw=10)
    sp = g.drill(sp, "M3", [(ROD[0], y - BW, zt + ROD[1])], d=(0, 1, 0), depth=12.0, cbore=3.2)   # guide bar + head
    sp = sp.fuse(pin_y(SHAFT_PIN[0], ROLL_X, y + GEAR_Y[0] - 0.21, SHAFT_PIN[1] - GEAR_Y[0] + 0.21,
                       zt + ROLL_Z))   # journal for the -y end of the pinion shaft (prints upward)
    # 0.2 mm sacrificial layer at the bottom of each counterbore: the step prints as a bridge; pierce it
    sp = sp.fuse([pin_y(1.8, x, y - BW + 3.2, 0.2, zt + z) for x, z in SIDE_SCREWS])
    return sp.removeSplitter()


def _slider(y, zt):
    """Slider at the forward end: pawl fork at the front (pin + spring, closed by a front wall), ear with the rack
    arm that rises beside the tape (teeth toward -y, driven by the servo gear), tail with the 2 dowel holes for
    the take-up rack. Prints standing on its bottom: the rack teeth lie in the print plane."""
    w = W_HOOK
    zs0, zs1 = zt + FLOOR + 0.15, zt + TUN_TOP - 0.15
    ya, yb = y + TUN_N[0] + 0.15, y + TUN_N[1] - 0.15
    body = g.box_r(w - 1.1, EAR_X[0], ya, yb, zs0, zs1)          # 0.8 front wall closes the pawl fork
    ear = g.box_r(EAR_X[0], EAR_X[1], ya, y + TUN_W[1] - 0.2, zs0, zs1)
    ya_, yb_ = y + SG_R + 1.25 * SG_M, y + 9.1
    yf = y + SG_R - RACK_ADD * SG_M                 # flange under the teeth: they print on it, it bridges the necks
    arm = g.box_r(EAR_X[0], EAR_X[1], ya_, yb_, zt + SG_Z[0] - 0.6, zt + SLIDER_RACK[1]).fuse(
        [g.box_r(EAR_X[0], EAR_X[1], yf, yb_, zt + SG_Z[0] - 0.6, zt + SG_Z[0] - 0.09)] +
        [g.box_r(x0_, x0_ + NECK_L, yf, yb_, zs1 - 0.01, zt + SG_Z[0] - 0.59) for x0_ in _neck_x()])
    teeth = _rack_teeth_y(EAR_X[0], EAR_X[1], y + SG_R, zt + SLIDER_RACK[0], zt + SLIDER_RACK[1])
    tail = g.box_r(EAR_X[1] - 0.01, SLIDER_END, ya, y + TUN_T[1] - 0.15, zs0, zs1)
    s = body.fuse([ear, arm, tail] + teeth).removeSplitter()
    s = s.cut(g.compound(_pawl_housing(w, y, zt, open_front=0.3)))
    s = s.cut(pin_y(0.8, w + PAWL_L, y + SPLIT_Y, 8.0, zt + PAWL_PZ))     # M2 set screw pilot (self-tapping)
    s = s.cut(g.compound([pin_y(0.8, x, y + GEAR_Y[0], 8.0, zt + z) for x, z in RACK_PINS]))   # rack screws, pilot
    return s.removeSplitter()


def _rack(y, zt):
    """Printed rack, fixed to the slider tail by 2 x M2 x 6 screws (moves with it): m1 teeth up at RACK_Z under
    the idler, a web across the split gap to the slider. Prints on its -y face."""
    y0, y1 = y + GEAR_Y[0], y + GEAR_Y[1]
    zr = zt + RACK_Z - 1.25 * PIN_M
    back = g.box_r(RACK_X[0], RACK_X[1], y0, y1, zt + FLOOR + 0.3, zr)
    web = g.box_r(RACK_X[0] + 1.5, RACK_X[1] - 0.5, y0, y + SPLIT_Y + 0.1, zt + FLOOR + 0.3, zt + 10.5)
    s = back.fuse([web] + _rack_teeth(RACK_X[0], RACK_X[1], zt + RACK_Z, y0, y1)).removeSplitter()
    holes = [pin_y(1.2, x, y - BW, 8.0, zt + z).fuse(pin_y(2.05, x, y - BW, BW + GEAR_Y[0] + 2.1, zt + z))
             for x, z in RACK_PINS]                       # M2 clearance + head counterbore 2.1 deep
    return s.cut(g.compound(holes)).removeSplitter()


def _idler(y, zt, rot=0.0):
    """36T m1 idler with its axle stub printed on (-y side): the stub runs in a hole through the side plate.
    Laid in, it rests on the side of the servo (0.4 mm from the gear plane); the side plate's hole takes the stub
    on closing. Prints on its +y face, stub up."""
    pts = _gear_pts(IDL_N, PIN_M, IDL_X, zt + IDL_Z, A_ROT0)
    s = _xz_poly(pts, y + GEAR_Y[0], y + GEAR_Y[1])
    stub = pin_y(IDL_STUB[0], IDL_X, y + IDL_STUB[1], GEAR_Y[0] - IDL_STUB[1] + 0.01, zt + IDL_Z)
    s = s.fuse(stub).removeSplitter()
    if rot:
        s.rotate(V(IDL_X, y, zt + IDL_Z), V(0, 1, 0), rot)
    return s


def _pinion(y, zt, rot=0.0):
    """14T m1 pinion printed in one piece with the D6 drive shaft (no press fit to slip). The shaft carries the
    drive roller's HF0612 and runs in the body; its -y end runs on the side plate's journal pin. Prints gear
    down, shaft up."""
    pts = _gear_pts(PIN_N, PIN_M, ROLL_X, zt + ROLL_Z, PIN_ROT0)
    shaft = pin_y(OWB[1] / 2, ROLL_X, y + SHAFT_Y[0], SHAFT_Y[1] - SHAFT_Y[0], zt + ROLL_Z)
    s = _xz_poly(pts, y + PIN_Y[0], y + PIN_Y[1]).fuse(shaft)
    br, bz = SHAFT_BORE
    bore = pin_y(br, ROLL_X, y + SHAFT_Y[0] - 1, bz - SHAFT_Y[0] + 1, zt + ROLL_Z).fuse(
        g.cone(br, 0.01, br, (ROLL_X, y + bz, zt + ROLL_Z), (0, 1, 0)))
    s = s.cut(bore).removeSplitter()
    if rot:
        s.rotate(V(ROLL_X, y, zt + ROLL_Z), V(0, 1, 0), rot)
    return s


def _drive_roller(y, zt):
    """PETG roller body: housing for the HF0612 (one-way, drives on the feed stroke), two O-ring grooves.
    Prints on its -y end; the +y flank of each groove is 45 deg (no overhang)."""
    c = (ROLL_X, zt + ROLL_Z)
    r_hub, r_gr = 7.6, 6.5
    s = g.tube(r_hub, OWB[0] / 2, ROLL_Y[1] - ROLL_Y[0], (c[0], y + ROLL_Y[0], c[1]), (0, 1, 0))
    for gc in ORING_Y:
        a, b = gc - 0.8, gc + 0.8
        prof = [(r_gr, a), (r_gr, b), (r_hub + 0.01, b + (r_hub - r_gr) + 0.01), (r_hub + 0.01, a)]
        face = g.poly_face(prof)                        # local x = radius, local y = axial position
        ring = face.revolve(V(0, 0, 0), V(0, 1, 0), 360)
        ring.translate(V(c[0], y, c[1]))
        s = s.cut(ring)
    return s.removeSplitter()


ORING_Y = (-0.6, 2.9)      # O-ring groove centres (cover tape -1.4 .. 3.9)


def _orings(y, zt):
    rings = []
    for gc in ORING_Y:
        t = App.Placement(V(ROLL_X, y + gc, zt + ROLL_Z), App.Rotation(V(1, 0, 0), 90))
        tor = Part.makeTorus(6.5 + 0.75, 0.75)
        tor.Placement = t
        rings.append(tor)
    return g.compound(rings)


def _yoke(y, zt):
    ya0, ya1 = YOKE_ARM_Y
    x0, x1 = YOKE_X
    z0 = zt + YOKE_Z0
    arms = [g.box_r(x0, x1, y + ya0, y + ya1, z0, zt + PINCH_Z + 4.2)]      # single arm: the idler is at -y
    bridge = g.box_r(x0, x1, y - 6.0, y + ya1, z0, z0 + 1.6)
    tab = g.box_r(x1 - 0.01, X_OUT - 1.5, y - 2.0, y + 2.0, z0, z0 + 1.6)
    s = bridge.fuse(arms + [tab]).removeSplitter()
    return s.cut(pin_y(3.0, ROLL_X, y - BW, 2 * BW, zt + PINCH_Z))


def _cover_plate(y, zt):
    """PETG plate, 1.2 mm, prints right side up (the smooth bed side touches the tape). Pick window, peel
    slot, rail tongues at the edges, rear tongues into the post, upstand with 2 countersunk M2 holes."""
    z0, z1 = zt + CH_TOP, zt + CH_TOP + PLATE_T
    px0, px1 = PLATE_X
    py = y + POCKET_DY
    cp = g.box_r(px0, px1, y - PLATE_HW, y + PLATE_HW, z0, z1)
    parts = []
    for xk in RAIL_X:
        for sd in (-1, 1):
            a, b = sorted((y + sd * TONGUE[0] - sd * 0.01, y + sd * TONGUE[1]))
            parts.append(g.box_r(xk + 0.5, xk + RAIL_L - 0.5, a, b, z0, z0 + TONGUE[2]))
    for a, b in REAR_TONGUES:
        parts.append(g.box_r(px1 - 0.01, X_TOWER + 3.0, y + a, y + b, z0, z0 + 1.0))
    ux0, ux1, uy0, uy1, uz0, uz1 = UPSTAND
    parts.append(g.box_r(ux0, ux1, y + uy0, y + uy1, z1 - 0.01, zt + uz1))
    parts.append(g.box_r(ux0, ux1, y + uy0, y - PLATE_HW + 0.01, z0, z1))
    cp = cp.fuse(parts)
    cuts = [g.box_r(P.PICK_X - 4, P.PICK_X + 4, py - 2.6, py + 2.6, z0 - 1, z1 + 1),          # pick window
            g.box_r(P.PICK_X + 6, P.PICK_X + 8, y - 2.0, y + 4.5, z0 - 1, z1 + 1)]           # peel slot
    for my, mz in CP_SCREWS:
        c = (UPSTAND[0], y + my, zt + mz)
        cuts += [g.cyl(CSK[1], 6.0, (c[0] - 1, c[1], c[2]), (1, 0, 0)),
                 g.cyl(CSK[0], 1.0, (c[0] - 1, c[1], c[2]), (1, 0, 0)),
                 g.cone(CSK[0], CSK[1], CSK[0] - CSK[1], c, (1, 0, 0))]
    return cp.cut(g.compound(cuts)).removeSplitter()


def _servo(y, zt):
    xs = SERVO_X
    case = g.box_r(xs - 5.9, xs + 16.6, y - 6.0, y + 6.0, zt + ZF, zt + ZF + 22.7)
    tabs = g.box_r(xs - 10.75, xs + 21.45, y - 6.0, y + 6.0, zt + ZF + 4.2, zt + ZF + 6.7)   # tab top 18.5 from the base
    tabs = tabs.cut(g.compound([g.cyl(1.0, 4, (xs + dx, y, zt + ZF + 4)) for dx in (-8.6, 19.2)]))
    br, bh = SERVO_BOSS
    sr, sl = SERVO_SPLINE
    boss = g.cyl(br, bh, (xs, y, zt + ZF - bh))
    spl = g.cyl(sr, sl, (xs, y, zt + ZF - bh - sl))
    return case.fuse([tabs, boss, spl])


def _servo_gear(y, zt, th):
    """Printed 13T m1 gear sector on the servo spline (replaces horn and pin): pressed on the spline (the metal
    spline of an MG90S cuts its teeth into the bore), held by the servo screw from below. Teeth only within
    +-SG_SECTOR of the rack side, the rest is the hub, so it clears the idler on the -y side. Drawn with a
    space toward +y at 90 deg, turned to th."""
    xs = SERVO_X
    z0, z1 = zt + SG_Z[0], zt + SG_Z[1]
    pts = _gear_pts(SG_N, SG_M, xs, y, 90.0 + 180.0 / SG_N)
    gear = _xy_prism(pts, z0, z1)
    a0, a1 = math.radians(90 - SG_SECTOR), math.radians(90 + SG_SECTOR)
    wedge = _xy_prism([(xs, y)] + [(xs + 10 * math.cos(a0 + (a1 - a0) * k / 8), y + 10 * math.sin(a0 + (a1 - a0) * k / 8))
                                    for k in range(9)], z0 - 1, z1 + 1)
    sg = gear.common(wedge).fuse(g.cyl(SG_HUB, z1 - z0, (xs, y, z0))).removeSplitter()
    sr, sl = SERVO_SPLINE
    zs = zt + ZF - SERVO_BOSS[1] - sl
    cuts = [g.cyl(sr, z1 - zs + 1, (xs, y, zs)),                                   # spline bore
            g.cyl(1.1, zs - z0 + 1, (xs, y, z0 - 0.5)), g.cyl(2.1, 1.2 + 1, (xs, y, z0 - 1))]   # screw, head
    sg = sg.cut(g.compound(cuts)).removeSplitter()
    return _rz(sg, th - 90.0, (xs, y, 0))


def _servo_gear_screw(y, zt):
    return g.screw_solid("M2", (SERVO_X, y, zt + SG_Z[0]), (0, 0, 1), 5, head_at=1.2)


def build_lane(y, th=None):
    """Returns a list of (suffix, shape, colour, mat, mass, bom, kind) and records screws in geom.
    th = horn angle (deg); default is the forward end (model pose)."""
    zt = P.TABLE_TOP_Z
    th = TH_FWD if th is None else th
    ztp = zt + TAPE_TOP
    dx = slider_dx(th)

    def mv(s):
        if dx:
            s.translate(V(dx, 0, 0))
        return s
    out = []
    out.append(("Body", _main_body(y, zt), g.C_ORANGE, "PETG", None, "Feeder v3.0 main body (printed PETG)", "print"))
    out.append(("SidePlate", _side_plate(y, zt), g.C_ORANGE, "PETG", None, "Feeder v3.0 side plate (printed PETG)",
                "print"))
    out.append(("CoverPlate", _cover_plate(y, zt), g.C_ORANGE, "PETG", None,
                "Feeder v3.0 cover plate, bayonet rails (printed PETG)", "print"))
    out.append(("Slider", mv(_slider(y, zt)), g.C_BLUE, "PETG", None, "Feeder v3.0 slider (printed PETG)", "print"))
    out.append(("Pawl_1", mv(_pawl(W_HOOK, y, zt)), g.C_WHITE, "PETG", None,
                "Feeder v3.0 pawl, feed + detent (printed PETG)", "print"))
    out.append(("Pawl_2", _pawl(D_HOOK, y, zt), g.C_WHITE, "PETG", None,
                "Feeder v3.0 pawl, feed + detent (printed PETG)", "print"))
    for k, (h, moving) in enumerate(((W_HOOK, True), (D_HOOK, False))):
        pp, ps = _pawl_pin(h, y, zt), _pawl_spring(h, y, zt)
        if moving:
            pp, ps = mv(pp), mv(ps)
        out.append(("PawlPin_%d" % (k + 1), pp, g.C_STEEL, None, 0.1, "Set screw M2 x 5 (pawl pivots)", "buy"))
        out.append(("PawlSpring_%d" % (k + 1), ps, g.C_STEEL, None, 0.05,
                    "Compression spring OD 3 x 0.3 wire x L0 8, ~0.5 N/mm (pawls)", "buy"))
    out.append(("Servo_SG90", _servo(y, zt), g.C_BLUE, None, 9.0, "Servo MG90S (metal gears + spline, SG90 size), 180 deg (tape advance)",
                "buy"))
    out.append(("ServoGear", _servo_gear(y, zt, th), g.C_WHITE, "PETG", None,
                "Feeder v3.0 servo gear sector 13T m1 on the spline (printed PETG, replaces the horn)", "print"))
    g._SCREWS.append(_servo_gear_screw(y, zt))

    # ---------------------------------------------------------------- peel: rack, idler, pinion, rollers, yoke
    out.append(("Rack", mv(_rack(y, zt)), g.C_BLUE, "PETG", None, "Feeder v3.0 rack m1 on the slider (printed PETG)",
                "print"))
    for x, z in RACK_PINS:
        sc = g.screw_solid("M2", (x, y + GEAR_Y[0], zt + z), (0, 1, 0), 6, head_at=2.1)
        g._SCREWS.append(mv(sc))
    out.append(("Idler", _idler(y, zt, idler_rot(dx)), g.C_WHITE, "PETG", None,
                "Feeder v3.0 idler gear 36T m1 with axle stub (printed PETG)", "print"))
    out.append(("Pinion", _pinion(y, zt, pinion_rot(dx)), g.C_WHITE, "PETG", None,
                "Feeder v3.0 pinion 14T m1 with the D6 drive shaft, one part (printed PETG)", "print"))
    out.append(("DriveRoller", _drive_roller(y, zt), g.C_WHITE, "PETG", None,
                "Feeder v3.0 roller body, drive + pinch (printed PETG)", "print"))
    owb = [g.tube(OWB[0] / 2, OWB[1] / 2, OWB[2], (ROLL_X, y + ROLL_Y[0], zt + z), (0, 1, 0))
           for z in (ROLL_Z, PINCH_Z)]
    for k, s in enumerate(owb):
        out.append(("OneWay_%d" % (k + 1), s, g.C_STEEL, None, 2.5,
                    "One-way needle bearing HF0612 (6 x 10 x 12), drive roller + pinch roller", "buy"))
    rings = list(_orings(y, zt).Solids)
    for r_ in list(rings):
        r2 = r_.copy()
        r2.translate(V(0, 0, PINCH_Z - ROLL_Z))
        rings.append(r2)
    for k, ring in enumerate(rings):
        out.append(("ORing_%d" % (k + 1), ring, g.C_DARK, None, 0.1, "O-ring 12 x 1.5 NBR 70 (roller tyres)", "buy"))
    pr = _drive_roller(y, zt)
    pr.translate(V(0, 0, PINCH_Z - ROLL_Z))
    out.append(("PinchRoller", pr, g.C_WHITE, "PETG", None, "Feeder v3.0 roller body, drive + pinch (printed PETG)",
                "print"))
    out.append(("PinchAxle", pin_y(3.0, ROLL_X, y + PINCH_AXLE_Y[0], PINCH_AXLE_Y[1] - PINCH_AXLE_Y[0],
                                   zt + PINCH_Z), g.C_WHITE, "PETG", None,
                "Feeder v3.0 pinch axle D6 x 14, pressed into the yoke (printed PETG)", "print"))
    out.append(("PinchYoke", _yoke(y, zt), g.C_ORANGE, "PETG", None, "Feeder v3.0 pinch yoke (printed PETG)", "print"))
    out.append(("PinchSpring", g.tube(2.5, 2.1, YOKE_Z0 - SPRING_Z0, (ROLL_X, y, zt + SPRING_Z0)), g.C_STEEL, None,
                0.1, "Compression spring OD 5 x 0.4 wire x L0 9, ~0.75 N/mm (pinch, 1.5 N)", "buy"))
    hy = y - BW + 3.2 - ROD_HEAD[1]
    bar = pin_y(ROD_HEAD[0], ROD[0], hy, ROD_HEAD[1], zt + ROD[1]).fuse(
        pin_y(1.45, ROD[0], hy + ROD_HEAD[1] - 0.01, y + ROD_Y[1] - hy - ROD_HEAD[1] + 0.01, zt + ROD[1]))
    out.append(("GuideBar", bar.removeSplitter(), g.C_WHITE, "PETG", None,
                "Feeder v3.0 cover tape guide bar D2.9 with head, pushed into the post (printed PETG)", "print"))
    for my, mz in CP_SCREWS:                         # countersunk M2 x 8: upstand -> tower
        c = V(UPSTAND[0], y + my, zt + mz)
        head = g.cone(1.9, 1.0, 0.9, c, (1, 0, 0))
        g._SCREWS.append(head.fuse(g.cyl(0.95, 8.0, c, (1, 0, 0))))

    ins = [g.tube(2.0, 1.5, 4.0, (x, yy, zt), (0, 0, 1)) for x, yy in mount_points(y)]
    ins += [g.tube(2.0, 1.5, 4.0, (x, y + SPLIT_Y, zt + z), (0, 1, 0)) for x, z in SIDE_SCREWS]
    out.append(("Inserts", g.compound(ins), g.C_BRASS, None, 0.0, None, "buy"))

    # fasteners from below (tooling plate -> lane)
    for x, yy in mount_points(y):
        g._SCREWS.append(g.screw_solid("M3", (x, yy, zt - P.TABLE_T), (0, 0, 1), 8, head_at=3.2))

    # ---------------------------------------------------------------- cover tape path
    c0, c1 = y + COVER_Y[0], y + COVER_Y[1]
    zp = zt + CH_TOP + PLATE_T
    zn = zt + NIP_Z
    xr = ROD[0] - 1.5 - COVER_T
    ct = [g.box_r(P.PICK_X + 8, X_OUT + 12, c0, c1, ztp, ztp + COVER_T),                # still on the tape
          g.box_r(P.PICK_X + 8 - COVER_T, P.PICK_X + 8, c0, c1, ztp + COVER_T, zp),       # up the peel slot
          g.box_r(P.PICK_X + 8 - COVER_T, xr, c0, c1, zp, zp + COVER_T),                 # back on the plate
          g.box_r(xr, xr + COVER_T, c0, c1, zp, zt + ROD[1]),                           # riser
          g.box_r(ROD[0], X_OUT + 12, c0, c1, zn, zn + COVER_T)]                          # to the nip, out
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

    # waste bin for used cover tape, standing on two legs on the plate behind the lanes. The cover tape
    # leaves the nips at NIP_Z, over the low front lip.
    b0, b1 = ya - 22.0, yb + 22.0
    bx0, bx1, bz0, bz1 = X_HEAD_OUT + 1.5, 689.0, zt + 43.0, zt + 71.0
    tray = g.box_r(bx0, bx1, b0, b1, bz0, bz1).cut(g.box_r(bx0 + 2, bx1 - 2, b0 + 2, b1 - 2, bz0 + 2, bz1 + 1))
    tray = tray.cut(g.box_r(bx0 - 1, bx0 + 3, b0 + 6, b1 - 6, zt + NIP_Z - 1.5, bz1 + 1))       # low front lip
    feet = bin_feet(lanes_y)
    tray = g.drill(tray, "M3", [(x, yy, bz0 + 2) for x, yy in feet], depth=3, cbore=0)
    out.append(("Feeder_WasteBin", tray.removeSplitter(), g.C_ORANGE, "PETG", None,
                "Cover tape waste bin (printed PETG)", "print", {"M3x50 SHCS + washer (bin + leg -> plate)": 2}))
    for k, (x, yy) in enumerate(feet):
        leg = g.box_r(x - 4, x + 4, yy - 5, yy + 5, zt, bz0)
        leg = g.drill(leg, "M3", [(x, yy, bz0 + 2)], depth=48, cbore=0)
        g._SCREWS.append(g.screw_solid("M3", (x, yy, bz0 + 2), (0, 0, -1), 50, head_at=0))
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

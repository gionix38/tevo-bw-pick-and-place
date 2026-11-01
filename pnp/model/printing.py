"""Printed parts (rev E): print orientation, teardrop holes, bed placement for STL, printability numbers.

Every kind='print' Item goes through prepare(): the part gets a print 'up' direction (frame coordinates),
horizontal holes in that orientation get a 45 deg teardrop roof (no support, no sagging), and the STL is
written lying on the bed. analyse() gives bed contact, overhang and bridge areas for the report.
"""
import math

import FreeCAD as App
import Part

import params as P
from . import geom as g

V = App.Vector

# print 'up' direction in frame coordinates, by part name prefix (first match wins). The face opposite
# to 'up' goes on the bed. Parts not listed use the automatic choice (least overhang).
UP = (
    ("Corner_", (0, 0, 1)),            # foot on the bed, holes horizontal -> teardrops
    ("XIdler_Slider", (0, 0, 1)),
    ("Bridge_End", (1, 0, 0)),         # Y-Z profile on its side
    ("Head_Carriage", (1, 0, 0)),      # back face (MGN12H blocks) on the bed
    ("Head_BeltClamp", (0, 1, 0)),     # X-Z profile on its side
    ("XChain_TrayBracket", (1, 0, 0)),  # L profile lying on its side
    ("XChain_Arm", (0, 1, 0)),         # end plate on the bed
    ("PCB_SlideClamp", (0, 0, 1)),
    ("UpCam_Housing", (0, 0, 1)),      # floor on the bed, open top up
    ("Lane", None),                    # feeder lane parts: by suffix (LANE_UP)
    ("Feeder_ExitChute", (0, 1, 0)),   # on its end, channel profiles vertical
    ("Feeder_WasteBinLeg", (1, 0, 0)),  # lying on its side
    ("Feeder_WasteBin", (0, 0, 1)),    # open top up
    ("ReelRack_Side", (0, 1, 0)),      # flat on its side
    ("ReelHub", (0, -1, 0)),           # flange on the bed
)

TEAR_MIN_R = 2.6       # smaller horizontal holes bridge fine without a teardrop
OVERHANG_COS = 0.72    # facets steeper than ~44 deg from vertical count as overhang (teardrop roofs are 45)


# feeder v3.0: every lane part prints flat on a face, pockets open upward (no supports, 0.4 mm nozzle)
LANE_UP = {"Body": (0, -1, 0),          # +y outer face on the bed, split face up
           "SidePlate": (0, 1, 0),      # -y outer face on the bed, split face up
           "CoverPlate": (0, 0, 1),     # tape side on the bed (smooth), rail tongues on the bed
           "Slider": (0, 0, 1), "Pawl": (0, 1, 0), "Pinion": (0, 1, 0),
           "DriveRoller": (0, 1, 0), "PinchRoller": (0, 1, 0),
           "PinchYoke": (0, 0, 1),      # bridge on the bed, arms up
           "Crank": (0, 0, -1),         # servo side on the bed, pin boss up
           "Rack": (0, 1, 0), "Idler": (0, -1, 0),
           "PinchAxle": (0, 1, 0),      # upright: round all over for the HF0612 needles
           "GuideBar": (0, 1, 0),       # head on the bed
           "ServoGear": (0, 0, 1)}


def up_for(name, shape):
    if name.startswith("Lane"):
        up = LANE_UP.get(name.split("_", 1)[1].rstrip("_0123456789"))
        return V(*up) if up else auto_up(shape)
    for pre, up in UP:
        if name.startswith(pre):
            if up is not None:
                return V(*up)
            break
    return auto_up(shape)


def _rot_to_bed(up):
    return App.Rotation(V(*up) if not isinstance(up, App.Vector) else up, V(0, 0, 1))


def orient(shape, up):
    """Copy of the shape turned so that 'up' is +Z, lying on Z=0, centred on the bed origin."""
    s = shape.copy()
    s.Placement = App.Placement(V(), _rot_to_bed(up)).multiply(s.Placement)
    bb = s.BoundBox
    s.translate(V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, -bb.ZMin))
    return s


def analyse(shape, up):
    """Areas in mm2 with the part on the bed: contact, angled overhang, flat bridge/ceiling; size."""
    import MeshPart
    s = orient(shape, up)
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.1, AngularDeflection=0.35, Segments=True)
    skip = set()
    for i, f in enumerate(s.Faces):
        if i >= m.countSegments():
            break
        su = f.Surface
        if isinstance(su, (Part.Cylinder, Part.Cone)) and getattr(su, "Radius", 99) <= TEAR_MIN_R:
            skip.update(m.getSegment(i))
    contact = over = bridge = 0.0
    for k, fc in enumerate(m.Facets):
        nz = fc.Normal.z
        if nz > -OVERHANG_COS or k in skip:
            continue
        zs = [p[2] for p in fc.Points]
        if max(zs) < 0.05:
            contact += fc.Area
        elif nz < -0.985:
            bridge += fc.Area
        else:
            over += fc.Area
    bb = s.BoundBox
    return dict(contact=contact, overhang=over, bridge=bridge, size=(bb.XLength, bb.YLength, bb.ZLength))


def auto_up(shape):
    best = None
    for up in ((0, 0, 1), (0, 0, -1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
        a = analyse(shape, V(*up))
        score = a["overhang"] + 0.3 * a["bridge"] - 0.2 * a["contact"]
        if best is None or score < best[0]:
            best = (score, V(*up))
    return best[1]


def _axis_of(cyl_surface):
    ax = cyl_surface.Axis
    for k, e in enumerate((V(1, 0, 0), V(0, 1, 0), V(0, 0, 1))):
        if abs(abs(ax.dot(e)) - 1) < 1e-6:
            return k, e
    return None, None


def teardrops(shape, up):
    """Add a 45 deg roof over every horizontal (in print orientation) round hole of radius > TEAR_MIN_R."""
    up = V(*up) if not isinstance(up, App.Vector) else up
    tools = []
    done = set()
    for f in shape.Faces:
        su = f.Surface
        if not isinstance(su, Part.Cylinder) or su.Radius <= TEAR_MIN_R:
            continue
        k, ax = _axis_of(su)
        if ax is None or abs(ax.dot(up)) > 1e-6:
            continue                       # vertical hole in print orientation, or skewed
        r = su.Radius
        c = su.Center
        lo, hi = (f.BoundBox.XMin, f.BoundBox.XMax) if k == 0 else (
            (f.BoundBox.YMin, f.BoundBox.YMax) if k == 1 else (f.BoundBox.ZMin, f.BoundBox.ZMax))
        if hi - lo < 0.2:
            continue
        # the roof only matters if the face is a hole (material outside) and its arc covers the top
        c0 = V(c)
        c0[k] = (lo + hi) / 2
        top_in, top_out = c0 + up * (r - 0.15), c0 + up * (r + 0.15)
        if f.distToShape(Part.Vertex(c0 + up * r))[0] > 0.05:
            continue
        if not shape.isInside(top_out, 0.01, True) or shape.isInside(top_in, 0.01, True):
            continue
        key = (k, round(c0.x, 2), round(c0.y, 2), round(c0.z, 2), round(r, 2), round(lo, 2), round(hi, 2))
        if key in done:
            continue
        done.add(key)
        s = up.cross(ax)
        q = r * math.sqrt(0.5)
        a0 = V(c0)
        a0[k] = lo
        pts = [a0 + s * q + up * q, a0 + up * (r * math.sqrt(2)), a0 - s * q + up * q, a0, a0 + s * q + up * q]
        kite = Part.Face(Part.makePolygon(pts)).extrude(ax * (hi - lo))
        tools.append(kite)
    if not tools:
        return shape, 0
    out = shape.cut(Part.makeCompound(tools)).removeSplitter()
    if not out.isValid() or len(out.Solids) != len(shape.Solids):
        return shape, 0
    return out, len(tools)


def prepare(name, shape):
    """Return (shape with teardrops, print up vector, number of teardrops)."""
    up = up_for(name, shape)
    shp, n = teardrops(shape, up)
    return shp, up, n


BRIDGE_MAX = 10.0     # longest bridge (anchored at both ends) a 0.4 mm nozzle does cleanly in PETG
CANTILEVER_MAX = 1.0  # flat ceiling anchored on one side only (a ledge) that still prints without support
OVERHANG_MAX = 3.0    # mm2 of steeper-than-45 deg overhang tolerated per part (small facets)


def _ceiling(shape, f, h):
    """Classify the flat ceiling f at print height h: boundary segments (2D) with an 'anchored' flag (the
    neighbouring face reaches below h, i.e. material under the edge), then rays from sample points: a point
    is bridged if a ray hits anchored edges on both sides (span = both distances), otherwise it hangs from
    the nearest anchored edge (cantilever). Returns (worst bridge span, worst cantilever depth, where)."""
    segs = []
    for e in f.OuterWire.Edges:                    # holes in a bridge are spanned over, not edges of it
        anc = False
        for g2 in shape.ancestorsOfType(e, Part.Face):
            if not g2.isSame(f) and g2.BoundBox.ZMin < h - 0.05:
                anc = True
        pts = e.discretize(Distance=0.4) if e.Length > 0.4 else [e.Vertexes[0].Point, e.Vertexes[-1].Point]
        for a, b in zip(pts, pts[1:]):
            segs.append((a.x, a.y, b.x, b.y, anc))
    bb = f.BoundBox
    step = max(0.4, min(bb.XLength, bb.YLength) / 6.0, max(bb.XLength, bb.YLength) / 40.0)
    dirs = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 180, 30)]
    worst_b, worst_c, where = 0.0, 0.0, None

    def hit(px, py, dx, dy):
        best = None
        for x0, y0, x1, y1, anc in segs:
            ex, ey = x1 - x0, y1 - y0
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = ((x0 - px) * ey - (y0 - py) * ex) / den
            u = ((x0 - px) * dy - (y0 - py) * dx) / den
            if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9 and (best is None or t < best[0]):
                best = (t, anc)
        return best
    x = bb.XMin + step / 2
    while x < bb.XMax:
        y = bb.YMin + step / 2
        while y < bb.YMax:
            if f.isInside(V(x, y, h), 0.01, True):
                span, hang = None, None
                rays = [(hit(x, y, dx, dy), hit(x, y, -dx, -dy)) for dx, dy in dirs]
                if any(a is None or b is None for a, b in rays):
                    y += step
                    continue                  # on the boundary (a ray escapes): not a ceiling point
                for a, b in rays:
                    if a and b and a[1] and b[1]:
                        span = a[0] + b[0] if span is None else min(span, a[0] + b[0])
                    for r in (a, b):
                        if r and r[1]:
                            hang = r[0] if hang is None else min(hang, r[0])
                d = 99.0 if hang is None else hang
                if d <= CANTILEVER_MAX:
                    worst_c = max(worst_c, d)         # held by the edge next to it (a short ledge)
                elif span is not None:
                    if span > worst_b:
                        worst_b, where = span, (round(x, 1), round(y, 1), round(h, 1))
                elif d > worst_c:
                    worst_c, where = d, (round(x, 1), round(y, 1), round(h, 1))
            y += step
        x += step
    return worst_b, worst_c, where


def support_report(shape, up):
    """Support-free check in print orientation. Flat ceilings: worst bridge span and worst one-sided
    (cantilever) depth from _ceiling(); angled overhang area (faces steeper than ~44 deg from vertical, not
    flat, not a small horizontal hole); bed contact area. Returns a dict."""
    s = orient(shape, up)
    worst, cant, over, contact = 0.0, 0.0, 0.0, 0.0
    where = None
    for f in s.Faces:
        su = f.Surface
        bb = f.BoundBox
        if isinstance(su, Part.Plane):
            n = f.normalAt(*f.ParameterRange[0::2])
            if n.z > -OVERHANG_COS:
                continue
            if bb.ZMax < 0.05:
                contact += f.Area
            elif n.z < -0.985:
                b, c, w = _ceiling(s, f, bb.ZMin)
                if b > worst or c > max(cant, CANTILEVER_MAX):
                    where = w
                worst, cant = max(worst, b), max(cant, c)
            else:
                over += f.Area
            continue
        if isinstance(su, (Part.Cylinder, Part.Cone)) and getattr(su, "Radius", 99) <= TEAR_MIN_R:
            continue
        if bb.ZMax < 0.05:
            continue
        u0, u1, v0, v1 = f.ParameterRange
        k, bad = 8, 0
        for i in range(k):
            for j in range(k):
                u, v = u0 + (u1 - u0) * (i + 0.5) / k, v0 + (v1 - v0) * (j + 0.5) / k
                try:
                    if not f.isInside(f.valueAt(u, v), 0.01, True):
                        continue
                    if f.normalAt(u, v).z < -OVERHANG_COS:
                        bad += 1
                except Exception:
                    pass
        over += f.Area * bad / (k * k)
    return dict(bridge=worst, cantilever=cant, at=where, overhang=over, contact=contact)


def support_free(rep):
    return rep["bridge"] <= BRIDGE_MAX and rep["cantilever"] <= CANTILEVER_MAX and rep["overhang"] <= OVERHANG_MAX


def fits_bed(size):
    bed = sorted(P.PRINT_BED[:2])
    xy = sorted(size[:2])
    return xy[0] <= bed[0] and xy[1] <= bed[1] and size[2] <= P.PRINT_BED[2]


def up_label(up):
    names = {(0, 0, 1): "+Z up (as installed)", (0, 0, -1): "upside down", (1, 0, 0): "on the -X face",
             (-1, 0, 0): "on the +X face", (0, 1, 0): "on the -Y face", (0, -1, 0): "on the +Y face"}
    return names.get(tuple(int(round(c)) for c in up), str(tuple(up)))

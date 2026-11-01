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


LANE_UP = {"Body": (0, 0, 1), "Slider": (0, 1, 0), "DriveRoller": (0, 1, 0), "PinchYoke": (0, 0, -1),
           "CheekCap": (0, 0, -1), "Lifter": (0, 1, 0), "Ratchet": (0, 1, 0), "HoldPawl": (0, 1, 0),
           "CoverPlate": (0, 0, -1), "RollerShaft": (0, 0, 1), "PinchAxle": (0, 0, 1), "SliderPeg": (-1, 0, 0), "PinchRoller": (0, 1, 0)}


def up_for(name, shape):
    if name.startswith("Lane"):
        up = LANE_UP.get(name.split("_", 1)[1])
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


def fits_bed(size):
    bed = sorted(P.PRINT_BED[:2])
    xy = sorted(size[:2])
    return xy[0] <= bed[0] and xy[1] <= bed[1] and size[2] <= P.PRINT_BED[2]


def up_label(up):
    names = {(0, 0, 1): "+Z up (as installed)", (0, 0, -1): "upside down", (1, 0, 0): "on the -X face",
             (-1, 0, 0): "on the +X face", (0, 1, 0): "on the -Y face", (0, -1, 0): "on the +Y face"}
    return names.get(tuple(int(round(c)) for c in up), str(tuple(up)))

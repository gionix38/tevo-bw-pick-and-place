"""Geometry helpers: profiles, guides, motors, pulleys, belts, chains. Headless Part workbench only."""
import math

import FreeCAD as App
import Part

V = App.Vector

# ------------------------------------------------------------------ colours (RGB 0..1)
C_ALU_BLACK = (0.13, 0.13, 0.15)
C_ALU = (0.75, 0.76, 0.78)
C_STEEL = (0.62, 0.64, 0.67)
C_DARK = (0.08, 0.08, 0.09)
C_RED = (0.85, 0.18, 0.16)        # printed parts, Tevo red
C_ORANGE = (0.95, 0.50, 0.10)     # new printed PnP parts
C_BRASS = (0.80, 0.64, 0.25)
C_BELT = (0.06, 0.06, 0.06)
C_PCB = (0.05, 0.40, 0.18)
C_COPPER = (0.85, 0.55, 0.25)
C_TAPE = (0.92, 0.92, 0.88)
C_BLUE = (0.15, 0.35, 0.75)
C_WHITE = (0.95, 0.95, 0.95)
C_CHAIN = (0.12, 0.12, 0.12)
C_GLASS = (0.30, 0.50, 0.70)

# part colour scheme: every distinct made / printed part gets its own colour (same part in every lane alike)
PART_PALETTE = ((0.95, 0.50, 0.10), (0.20, 0.50, 0.88), (0.22, 0.68, 0.36), (0.88, 0.26, 0.30), (0.62, 0.42, 0.85),
                (0.97, 0.80, 0.18), (0.15, 0.72, 0.78), (0.90, 0.48, 0.68), (0.58, 0.78, 0.25), (0.62, 0.45, 0.30),
                (0.40, 0.52, 0.72), (0.98, 0.62, 0.50), (0.30, 0.82, 0.62), (0.80, 0.62, 0.95), (0.75, 0.75, 0.30),
                (0.25, 0.38, 0.60))


def part_key(name):
    """Name without lane / index decoration: Lane3_Body -> Body, ReelHub_5 -> ReelHub."""
    import re
    return re.sub(r"_\d+$", "", re.sub(r"^Lane\d+_", "", name))


def part_colors(entries):
    """entries: iterable of (name, kind, colour). Made and printed parts get a palette colour per part_key
    (assigned in sorted order, so a rebuild keeps them); bought / stock parts keep their own colour."""
    entries = list(entries)
    keys = sorted({part_key(n) for n, k, c in entries if k in ("make", "print")})
    pal = {k: PART_PALETTE[i % len(PART_PALETTE)] for i, k in enumerate(keys)}
    return {n: (pal[part_key(n)] if k in ("make", "print") else tuple(c)) for n, k, c in entries}

DENSITY = {"alu": 2.70, "steel": 7.85, "PETG": 1.27, "PLA": 1.24, "brass": 8.5, "FR4": 1.85, "rubber": 1.2, "TPU": 1.21}


def box(dx, dy, dz, x=0.0, y=0.0, z=0.0):
    return Part.makeBox(dx, dy, dz, V(x, y, z))


def box_c(cx, cy, cz, dx, dy, dz):
    """Box from centre and size."""
    return Part.makeBox(dx, dy, dz, V(cx - dx / 2, cy - dy / 2, cz - dz / 2))


def box_r(x0, x1, y0, y1, z0, z1):
    """Box from ranges."""
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, h, p=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCylinder(r, h, V(*p), V(*d))


def tube(ro, ri, h, p=(0, 0, 0), d=(0, 0, 1)):
    return cyl(ro, h, p, d).cut(cyl(ri, h + 2, tuple(V(*p) - V(*d).normalize()), d))


def cone(r1, r2, h, p=(0, 0, 0), d=(0, 0, 1)):
    return Part.makeCone(r1, r2, h, V(*p), V(*d))


def poly_face(pts):
    return Part.Face(Part.makePolygon([V(x, y, 0) for x, y in pts] + [V(*pts[0], 0)]))


# ------------------------------------------------------------------ aluminium profiles
def _slot(u, side, w, h):
    """V-slot cut polygon centred at coordinate u on one side of a w x h section."""
    prof = [(-3.1, -0.2), (-3.1, 1.8), (-5.5, 1.8), (-5.5, 4.3), (-2.9, 6.5),
            (2.9, 6.5), (5.5, 4.3), (5.5, 1.8), (3.1, 1.8), (3.1, -0.2)]
    if side == "bottom":
        pts = [(u + a, b) for a, b in prof]
    elif side == "top":
        pts = [(u + a, h - b) for a, b in prof]
    elif side == "left":
        pts = [(b, u + a) for a, b in prof]
    else:  # right
        pts = [(w - b, u + a) for a, b in prof]
    return poly_face(pts)


def vslot_section(w, h, skip_sides=()):
    """2D V-slot section w x h (multiples of 20) in the XY plane, origin at corner."""
    face = poly_face([(0, 0), (w, 0), (w, h), (0, h)])
    cuts = []
    for i in range(int(round(w / 20))):
        u = 10 + 20 * i
        for side in ("bottom", "top"):
            if side not in skip_sides:
                cuts.append(_slot(u, side, w, h))
    for j in range(int(round(h / 20))):
        v = 10 + 20 * j
        for side in ("left", "right"):
            if side not in skip_sides:
                cuts.append(_slot(v, side, w, h))
    for i in range(int(round(w / 20))):
        for j in range(int(round(h / 20))):
            cuts.append(Part.Face(Part.Wire(Part.makeCircle(2.1, V(10 + 20 * i, 10 + 20 * j, 0)))))
    for c in cuts:
        face = face.cut(c)
    return face


def cbeam_section(w=40.0, h=80.0, channel=(18.0, 62.0, 27.0)):
    """C-beam: channel opens on the left side (u = 0)."""
    face = vslot_section(w, h, skip_sides=("left",))
    v0, v1, depth = channel
    face = face.cut(poly_face([(-0.2, v0 + 4), (3, v0 + 4), (3, v0), (depth, v0),
                               (depth, v1), (3, v1), (3, v1 - 4), (-0.2, v1 - 4)]))
    for v in (10.0, h - 10.0):   # lip slots on the standard 10 mm grid (8 cut the corners off)
        face = face.cut(_slot(v, "left", w, h))
    return face


def extrude_section(face, length, place):
    """Extrude a section (XY plane) along +Z, then apply placement."""
    s = face.extrude(V(0, 0, length))
    s.Placement = place
    return s


def profile_along(section, length, axis, min_corner, flip_u=False):
    """Extrude a section (local XY) along world axis 'x', 'y' or 'z' and move it so that its
    bounding box starts at min_corner. Section local X -> the first remaining world axis,
    local Y -> world Z (or world Y for axis 'z'). flip_u mirrors the section's local X."""
    sec = section.mirror(V(0, 0, 0), V(1, 0, 0)) if flip_u else section
    s = sec.extrude(V(0, 0, length))
    if axis == "x":
        rot = App.Rotation(V(0, 1, 0), V(0, 0, 1), V(1, 0, 0), "ZXY")
    elif axis == "y":
        rot = App.Rotation(V(-1, 0, 0), V(0, 0, 1), V(0, 1, 0), "ZXY")
    else:
        rot = App.Rotation()
    s.Placement = App.Placement(V(), rot)
    bb = s.BoundBox
    s.translate(V(min_corner[0] - bb.XMin, min_corner[1] - bb.YMin, min_corner[2] - bb.ZMin))
    return s


# ------------------------------------------------------------------ linear guides
def mgn_rail(spec, length):
    """Rail along +X, mounting face on Z=0, centred on Y=0."""
    w, h = spec["rail_w"], spec["rail_h"]
    r = box(length, w, h, 0, -w / 2, 0)
    groove = box(length + 2, 1.6, 1.4, -1, -w / 2 - 0.4, h * 0.55)
    r = r.cut(groove).cut(groove.mirror(V(0, 0, 0), V(0, 1, 0)))
    pitch = spec.get("rail_pitch", 25.0)
    n = int(length // pitch)
    x0 = (length - (n - 1) * pitch) / 2
    for i in range(n):
        r = r.cut(cyl(3.0, 3.6, (x0 + i * pitch, 0, h - 3.5)))
    return r


def mgn_block(spec):
    """Block centred at origin in X/Y, sitting on a rail whose base is Z=0."""
    w, L, H, rh = spec["blk_w"], spec["blk_l"], spec["H"], spec["rail_h"]
    body = box(L * 0.78, w, H - 3, -L * 0.39, -w / 2, 3)
    caps = box(L, w * 0.92, H - 4.5, -L / 2, -w * 0.46, 3.5)
    b = body.fuse(caps)
    b = b.cut(box(L + 2, spec["rail_w"] + 1.2, rh + 0.6, -L / 2 - 1, -spec["rail_w"] / 2 - 0.6, 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = b.cut(cyl(1.3, 6, (sx * spec["hole_c"] / 2, sy * spec["hole_b"] / 2, H - 5)))
    return b.removeSplitter()


# ------------------------------------------------------------------ motors, pulleys
def nema(spec):
    """Stepper, face on Z=0, body towards -Z, shaft along +Z, axis through origin."""
    s, L = spec["size"], spec["length"]
    ch = s * 0.12
    pts = [(-s / 2 + ch, -s / 2), (s / 2 - ch, -s / 2), (s / 2, -s / 2 + ch), (s / 2, s / 2 - ch),
           (s / 2 - ch, s / 2), (-s / 2 + ch, s / 2), (-s / 2, s / 2 - ch), (-s / 2, -s / 2 + ch)]
    body = poly_face(pts).extrude(V(0, 0, L))
    body.translate(V(0, 0, -L))
    body = body.cut(box(s + 2, s + 2, 1.2, -s / 2 - 1, -s / 2 - 1, -L * 0.62)
                    .cut(cyl(s / 2 - 1.5, 2, (0, 0, -L * 0.62 - 0.5))))
    body = body.fuse(cyl(spec["boss"] / 2, 2, (0, 0, 0)))
    shaft = cyl(spec["shaft"] / 2, spec["shaft_len"], (0, 0, 2))
    return body.removeSplitter(), shaft


def gt2_pulley(teeth=20, width=9.0, bore=5.0, hub=8.0, flanged=True):
    """Pulley along +Z from Z=0 (hub first), axis at origin."""
    pd = teeth * 2.0 / math.pi
    hub_s = cyl(pd / 2 + 1.5, hub)
    toothed = cyl(pd / 2 - 0.38, width + 1, (0, 0, hub + (1 if flanged else 0)))
    p = hub_s.fuse(toothed)
    if flanged:
        p = p.fuse(cyl(pd / 2 + 2.5, 1, (0, 0, hub))).fuse(cyl(pd / 2 + 2.5, 1, (0, 0, hub + width + 1)))
    p = p.cut(cyl(bore / 2, hub + width + 4, (0, 0, -1)))
    return p.removeSplitter()


def idler(width=9.0, teeth=20):
    pd = teeth * 2.0 / math.pi
    p = cyl(pd / 2 - 0.4, width + 1).fuse(cyl(pd / 2 + 2.5, 1, (0, 0, -1))).fuse(cyl(pd / 2 + 2.5, 1, (0, 0, width + 1)))
    return p.cut(cyl(2.5, width + 6, (0, 0, -3)))


def belt_loop(c1, c2, r, width, t=1.4, normal=(0, 1, 0)):
    """Closed belt around two pulleys. c1/c2 are centres (Vectors) in a plane with given normal;
    the belt has its width along the normal starting at the centre plane - width/2."""
    c1, c2 = V(*c1), V(*c2)
    n = V(*normal).normalize()
    L = (c2 - c1).Length
    u = (c2 - c1).normalize()
    w = n.cross(u)
    def ring(rr):
        a = c1 + w * rr
        b = c2 + w * rr
        c = c2 - w * rr
        d = c1 - w * rr
        e1 = Part.LineSegment(a, b).toShape()
        e2 = Part.Arc(b, c2 + u * rr, c).toShape()
        e3 = Part.LineSegment(c, d).toShape()
        e4 = Part.Arc(d, c1 - u * rr, a).toShape()
        return Part.Face(Part.Wire([e1, e2, e3, e4]))
    f = ring(r + t).cut(ring(r))
    f.translate(n * (-width / 2))
    return f.extrude(n * width)


def drag_chain(p_fixed, p_moving, direction, up, radius, slack, link=(14.0, 10.0, 16.0), pitch=17.0):
    """Drag chain lying in the plane spanned by 'direction' and 'up'.
    Lower run starts at p_fixed and runs along +direction, bends 180 deg upward, upper run returns
    to p_moving (which is 2*radius above the lower run). Links are boxes (len, width, height).
    Returns a list of link shapes."""
    pf, pm = V(*p_fixed), V(*p_moving)
    d = V(*direction).normalize()
    up = V(*up).normalize()
    side = d.cross(up)
    lf = (pm - pf).dot(d)
    # constant chain length: loop position moves at half the speed of the moving end
    x_loop = lf / 2 + slack
    pts = []
    s = 0.0
    while s <= x_loop:
        pts.append((pf + d * s, d))
        s += pitch
    n_arc = max(4, int(math.pi * radius / pitch))
    c = pf + d * x_loop + up * radius
    for i in range(1, n_arc):
        a = -math.pi / 2 + math.pi * i / n_arc
        p = c + d * (radius * math.cos(a)) + up * (radius * math.sin(a))
        t = d * (-math.sin(a)) + up * math.cos(a)
        pts.append((p, t))
    s = x_loop
    while s >= lf - 1e-6:
        pts.append((pf + d * s + up * (2 * radius), -d))
        s -= pitch
    shapes = []
    L, W, H = link
    for p, t in pts:
        b = box(L, W, H, -L / 2, -W / 2, -H / 2)
        tn = t.normalize()
        nrm = tn.cross(side)
        rot = App.Rotation(tn, side, nrm, "ZXY")
        b.Placement = App.Placement(p, rot)
        shapes.append(b)
    return shapes


def compound(shapes):
    return Part.makeCompound([s for s in shapes if s is not None])


def microswitch():
    """Small endstop switch, 20 x 6.4 x 10 with lever, origin at body bottom-centre."""
    b = box_c(0, 0, 5, 20, 6.4, 10)
    lever = box(16, 4, 0.6, -6, -2, 10.5)
    return b.fuse(lever)


# ------------------------------------------------------------------ rounding and holes
CLEAR = {"M2": (2.4, 4.2, 2.0), "M2.5": (2.9, 5.0, 2.5), "M3": (3.4, 6.5, 3.2), "M4": (4.5, 8.0, 4.2),
         "M5": (5.5, 9.5, 5.2), "M6": (6.6, 11.0, 6.2), "M8": (8.6, 14.0, 8.2)}   # hole, cbore dia, cbore depth
INSERT = {"M2": 3.2, "M2.5": 3.6, "M3": 4.0, "M5": 6.4, "M6": 8.0}               # heat-set insert holes
TAP = {"M2": 1.6, "M2.5": 2.05, "M3": 2.5, "M4": 3.3, "M5": 4.2, "M6": 5.0}        # tap drill (metal parts)


def rbox(x0, x1, y0, y1, z0, z1, r, axis="z"):
    """Box with its four edges parallel to 'axis' rounded to radius r."""
    b = box_r(x0, x1, y0, y1, z0, z1)
    if r <= 0:
        return b
    a = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}[axis]
    edges = [e for e in b.Edges if abs(abs((e.Vertexes[1].Point - e.Vertexes[0].Point).normalize().dot(a)) - 1) < 1e-6]
    return b.makeFillet(r, edges)


def fillet_safe(shape, r, min_len=None):
    """Round the edges of a printed/solid part. Tries all straight edges, then smaller radii,
    then only the longer edges; returns the input if every attempt fails."""
    if r <= 0:
        return shape
    min_len = 3 * r if min_len is None else min_len
    lines = [e for e in shape.Edges if e.Curve.TypeId == "Part::GeomLine" and e.Length > min_len]
    for rr, sel in ((r, lines), (r * 0.6, lines), (r * 0.6, [e for e in lines if e.Length > 6 * r])):
        if not sel:
            continue
        try:
            f = shape.makeFillet(rr, sel)
            if f.isValid() and abs(f.Volume - shape.Volume) < 0.08 * shape.Volume:
                return f
        except Exception:
            pass
    return shape


def drill(shape, spec, pts, d=(0, 0, -1), depth=60.0, cbore=None, insert=False, tap=False, screw=None):
    """Cut fastener holes. pts are the hole entry points, d the drilling direction.
    cbore = counterbore depth (None = use the table value, 0 = plain hole)."""
    dv = V(*d).normalize()
    if insert:
        dia = INSERT[spec]
    elif tap:
        dia = TAP[spec]
    else:
        dia = CLEAR[spec][0]
    for p in pts:
        p = V(*p)
        shape = shape.cut(Part.makeCylinder(dia / 2, depth + 1, p - dv * 1.0, dv))
        if cbore is not None and cbore > 0 and not insert and not tap:
            shape = shape.cut(Part.makeCylinder(CLEAR[spec][1] / 2, cbore + 1, p - dv * 1.0, dv))
        if screw and not insert and not tap:
            _SCREWS.append(screw_solid(spec, p, dv, screw, head_at=(cbore or 0.0)))
    return shape


def nema_pattern(size):
    """Bolt pitch for a NEMA frame size (mm)."""
    return {42.3: 31.0, 35.0: 26.0, 28.0: 23.0, 20.0: 16.0}[size]


# ------------------------------------------------------------------ screws (modelled fasteners)
HEAD = {"M2": (3.8, 2.0), "M2.5": (4.5, 2.5), "M3": (5.5, 3.0), "M4": (7.0, 4.0), "M5": (8.5, 5.0),
        "M6": (10.0, 6.0), "M8": (13.0, 8.0)}          # socket head diameter, height
_SCREWS = []


def screw_solid(spec, p, d, length, head_at=0.0):
    """Socket head cap screw. p = hole entry, d = direction into the work, head bottom at p + d*head_at."""
    dv = V(*d).normalize()
    hd, hh = HEAD[spec]
    base = V(*p) + dv * head_at
    head = Part.makeCylinder(hd / 2, hh, base - dv * hh, dv)
    head = head.cut(Part.makeCylinder(hd * 0.22, hh * 0.6, base - dv * hh - dv * 0.01, dv))
    shank = Part.makeCylinder(CLEAR[spec][0] / 2 - 0.25, length, base, dv)
    return head.fuse(shank)


def take_screws():
    """Return (and clear) the screws recorded by drill(..., screw=L) since the last call."""
    global _SCREWS
    s, _SCREWS = _SCREWS, []
    return Part.makeCompound(s) if s else None


def slot(shape, spec, p, d, along, length, depth=20.0):
    """Cut a slotted clearance hole: centre p, drilling direction d, slot direction 'along'."""
    dv, av = V(*d).normalize(), V(*along).normalize()
    r = CLEAR[spec][0] / 2
    c = V(*p) - dv * 1.0
    s = Part.makeCylinder(r, depth + 1, c - av * (length / 2), dv).fuse(Part.makeCylinder(r, depth + 1, c + av * (length / 2), dv))
    w = dv.cross(av).normalize()
    b = Part.makeBox(length, 2 * r, depth + 1)
    b.Placement = App.Placement(c - av * (length / 2) - w * r, App.Rotation(av, w, dv, "ZXY"))
    return shape.cut(s.fuse(b))

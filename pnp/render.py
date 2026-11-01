"""Headless renderer: Part shapes -> Coin3D scene -> SoOffscreenRenderer -> PNG (via PIL).

No FreeCAD GUI is started. Faces are tessellated one by one so normals are smooth inside a face
and sharp across edges; edges are drawn as dark lines for a CAD look.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import FreeCADGui
FreeCADGui.setupWithoutGUI()
from pivy import coin  # noqa: E402

# view name -> (direction camera looks along, up vector, orthographic, focus)
VIEWS = {   # name -> (look direction, up, orthographic, focus tag, zoom)
    "iso":        ((-0.75, 1.0, -0.62), (0, 0, 1), False, None, 1.25),
    "iso_rear":   ((0.8, -0.9, -0.7), (0, 0, 1), False, None, 1.25),
    "front":      ((0, 1, 0), (0, 0, 1), True, None, 1.45),
    "top":        ((0, 0, -1), (0, 1, 0), True, None, 1.35),
    "side":       ((-1, 0, 0), (0, 0, 1), True, None, 1.45),
    "head":       ((-0.9, 0.55, -0.35), (0, 0, 1), False, "head", 1.0),
    "head_front": ((0.2, 1.0, -0.25), (0, 0, 1), False, "head", 0.9),
    "table":      ((-0.35, 0.75, -0.9), (0, 0, 1), False, "table", 1.05),
    "strip":      ((-0.75, 0.45, -0.75), (0, 0, 1), False, "strip", 1.0),
    "xdrive":     ((0.55, 0.75, -0.45), (0, 0, 1), False, "xdrive", 0.9),
    "ymotor":     ((-0.8, -0.6, -0.5), (0, 0, 1), False, "ymotor", 0.75),
    "yidler":     ((-0.7, 0.8, -0.5), (0, 0, 1), False, "yidler", 0.7),
    "xidler":     ((-0.6, 0.7, -0.6), (0, 0, 1), False, "xidler", 0.8),
    "bridgeend":  ((-0.7, 0.75, -0.4), (0, 0, 1), False, "bridgeend", 0.8),
    "tray":       ((0.6, -0.8, -0.4), (0, 0, 1), False, "tray", 0.7),
    "camera":     ((-0.8, 0.3, -0.25), (0, 0, 1), False, "camera", 0.55),
    "feeder":     ((-0.55, 0.8, -0.5), (0, 0, 1), False, "feeder", 1.0),
    "feeder_mech": ((-0.45, 0.85, -0.35), (0, 0, 1), False, None, 1.9),
}


def _face_mesh(face, tol):
    try:
        pts, tris = face.tessellate(tol)
    except Exception:
        return None
    if not tris:
        return None
    P = np.array([(p.x, p.y, p.z) for p in pts], dtype=np.float32)
    T = np.array(tris, dtype=np.int32)
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    fn = np.cross(b - a, c - a)
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, T[:, k], fn)
    ln = np.linalg.norm(N, axis=1, keepdims=True)
    ln[ln == 0] = 1
    return P, T, N / ln


def shape_node(shape, color, tol=0.25, edges=True, edge_color=(0.05, 0.05, 0.06), shininess=0.35, alpha=0.0):
    sep = coin.SoSeparator()
    mat = coin.SoMaterial()
    mat.diffuseColor.setValue(*color)
    mat.ambientColor.setValue(*[c * 0.9 for c in color])
    mat.specularColor.setValue(0.35, 0.35, 0.35)
    mat.shininess.setValue(shininess)
    mat.transparency.setValue(alpha)
    sep.addChild(mat)
    hints = coin.SoShapeHints()
    hints.vertexOrdering = coin.SoShapeHints.UNKNOWN_ORDERING   # two-sided lighting
    hints.shapeType = coin.SoShapeHints.UNKNOWN_SHAPE_TYPE
    sep.addChild(hints)
    Ps, Ns, Is = [], [], []
    off = 0
    bb = shape.BoundBox
    tol = max(tol, min(1.0, bb.DiagonalLength / 400.0))
    for f in shape.Faces:
        m = _face_mesh(f, tol)
        if m is None:
            continue
        P, T, N = m
        Ps.append(P)
        Ns.append(N)
        T = T + off
        Is.append(np.hstack([T, -np.ones((len(T), 1), dtype=np.int32)]).ravel())
        off += len(P)
    if Ps:
        coords = coin.SoCoordinate3()
        coords.point.setValues(0, off, np.vstack(Ps).tolist())
        norms = coin.SoNormal()
        norms.vector.setValues(0, off, np.vstack(Ns).tolist())
        nb = coin.SoNormalBinding()
        nb.value = coin.SoNormalBinding.PER_VERTEX_INDEXED
        sep.addChild(coords)
        sep.addChild(norms)
        sep.addChild(nb)
        po = coin.SoPolygonOffset()
        po.factor = 1.0
        po.units = 1.0
        sep.addChild(po)
        ifs = coin.SoIndexedFaceSet()
        idx = np.concatenate(Is).tolist()
        ifs.coordIndex.setValues(0, len(idx), idx)
        ifs.normalIndex.setValues(0, len(idx), idx)
        sep.addChild(ifs)
    if edges:
        esep = coin.SoSeparator()
        lm = coin.SoLightModel()
        lm.model = coin.SoLightModel.BASE_COLOR
        esep.addChild(lm)
        em = coin.SoBaseColor()
        em.rgb.setValue(*edge_color)
        esep.addChild(em)
        ds = coin.SoDrawStyle()
        ds.lineWidth = 1.0
        esep.addChild(ds)
        pts, counts = [], []
        for e in shape.Edges:
            try:
                d = e.discretize(Deflection=tol * 2)
            except Exception:
                continue
            if len(d) < 2:
                continue
            pts += [(p.x, p.y, p.z) for p in d]
            counts.append(len(d))
        if counts:
            c = coin.SoCoordinate3()
            c.point.setValues(0, len(pts), pts)
            ls = coin.SoLineSet()
            ls.numVertices.setValues(0, len(counts), counts)
            esep.addChild(c)
            esep.addChild(ls)
            sep.addChild(esep)
    return sep


def _lights(root):
    for d, i in (((-0.45, 0.55, -1.0), 0.85), ((0.9, 0.35, -0.45), 0.45), ((-0.2, -0.9, -0.2), 0.40),
                 ((0.3, 0.2, 1.0), 0.20)):
        l = coin.SoDirectionalLight()
        l.direction.setValue(*d)
        l.intensity = i
        root.addChild(l)


def _bg(w, h):
    top = np.array([236, 238, 242], dtype=np.float32)
    bot = np.array([196, 200, 208], dtype=np.float32)
    t = np.linspace(0, 1, h)[:, None]
    col = top * (1 - t) + bot * t
    img = np.repeat(col[:, None, :], w, axis=1).astype(np.uint8)
    return Image.fromarray(img, "RGB")


class Scene:
    def __init__(self, entries, edges=True):
        """entries: list of (name, shape, color, tags)."""
        self.entries = entries
        self.nodes = {}
        self.root = coin.SoSeparator()
        self.cam = None
        _lights(self.root)
        self.geom = coin.SoSeparator()
        self.root.addChild(self.geom)
        for name, shape, color, tags in entries:
            n = shape_node(shape, color, edges=edges and "noedge" not in tags,
                           alpha=0.78 if "ghost" in tags else 0.0, tol=0.08 if "fine" in tags else 0.25)
            self.nodes[name] = (n, tags)
            self.geom.addChild(n)

    def focus_node(self, tag):
        sep = coin.SoSeparator()
        for n, tags in self.nodes.values():
            if tag in tags or (tag == "machine" and "floor" not in tags):
                sep.addChild(n)
        return sep if sep.getNumChildren() else None

    def render(self, path, view="iso", size=(1600, 1000), ss=2, title=None, subtitle=None, zoom=1.0):
        d, up, ortho, focus, vzoom = VIEWS[view]
        zoom = zoom * vzoom
        W, H = size[0] * ss, size[1] * ss
        vp = coin.SbViewportRegion(W, H)
        cam = coin.SoOrthographicCamera() if ortho else coin.SoPerspectiveCamera()
        if not ortho:
            cam.heightAngle = math.radians(32)
        if self.cam is not None:
            self.root.removeChild(self.cam)
        self.root.insertChild(cam, 0)      # camera must be a direct child ahead of the geometry
        self.cam = cam
        dv = coin.SbVec3f(*d)
        dv.normalize()
        cam.pointAt(dv * 100.0, coin.SbVec3f(*up))
        target = self.focus_node(focus or "machine")
        cam.viewAll(target if target is not None else self.geom, vp, 1.0)
        if zoom != 1.0:
            if ortho:
                cam.height = cam.height.getValue() / zoom
            else:
                p = cam.position.getValue()
                fd = cam.focalDistance.getValue()
                cam.position = p + dv * (fd * (1 - 1 / zoom))
                cam.focalDistance = fd / zoom
        # parts outside the focus box must not be clipped by the near/far planes
        cam.nearDistance = 5.0
        cam.farDistance = 6000.0
        r = coin.SoOffscreenRenderer(vp)
        r.getGLRenderAction().setTransparencyType(coin.SoGLRenderAction.SORTED_OBJECT_BLEND)
        r.setComponents(coin.SoOffscreenRenderer.RGB_TRANSPARENCY)
        r.setBackgroundColor(coin.SbColor(1, 1, 1))
        if not r.render(self.root):
            raise RuntimeError("offscreen render failed")
        buf = r.getBuffer()
        img = Image.frombytes("RGBA", (W, H), bytes(buf)).transpose(Image.FLIP_TOP_BOTTOM)
        bg = _bg(W, H)
        bg.paste(img, (0, 0), img)
        out = bg.resize(size, Image.LANCZOS)
        if title or subtitle:
            dr = ImageDraw.Draw(out)
            try:
                f1 = ImageFont.truetype("arial.ttf", 26)
                f2 = ImageFont.truetype("arial.ttf", 16)
            except OSError:
                f1 = f2 = ImageFont.load_default()
            if title:
                dr.text((24, 18), title, fill=(25, 28, 34), font=f1)
            if subtitle:
                dr.text((24, 54), subtitle, fill=(70, 75, 85), font=f2)
        out.save(path)
        return path

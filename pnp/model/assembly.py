"""Collect all subsystems, apply a machine pose, and write the FreeCAD document."""
import FreeCAD as App

import params as P
from . import frame, xaxis, yaxis, head, tooling, services
from . import geom as g
from .item import Item

V = App.Vector

SYSTEM_ORDER = ("frame", "x_axis", "y_axis", "head", "table", "feeders", "magazine", "chains")


def static_items():
    """Everything except pose-dependent parts, at the reference pose (home)."""
    items = []
    items += frame.build()
    items += xaxis.build()
    items += yaxis.build()
    items += head.build()
    items += tooling.build_table()
    items += tooling.build_feeders()
    items += tooling.build_magazine()
    items += services.build_tray()
    names = [i.name for i in items]
    dup = {n for n in names if names.count(n) > 1}
    if dup:
        raise ValueError("duplicate item names: %s" % sorted(dup))
    return items


def clamp_pose(pose):
    d = P.derive()
    p = dict(X=0.0, Y=0.0, Z=0.0, C=0.0)
    p.update({k: float(v) for k, v in (pose or {}).items()})
    p["X"] = min(max(p["X"], 0.0), d["x_travel"])
    p["Y"] = min(max(p["Y"], 0.0), d["y_travel"])
    p["Z"] = min(max(p["Z"], P.Z_SOFT_MIN), 0.0)
    return p


def placement_for(move, pose):
    X, Y, Z, C = pose["X"], pose["Y"], pose["Z"], pose["C"]
    if move in ("fixed", "posed"):
        return App.Placement()
    if move == "bridge":
        return App.Placement(V(X, 0, 0), App.Rotation())
    if move == "carriage":
        return App.Placement(V(X, Y, 0), App.Rotation())
    if move == "zslide":
        return App.Placement(V(X, Y, Z), App.Rotation())
    if move == "rotor":
        n = head.nozzle_world_ref()
        return App.Placement(V(X, Y, Z), App.Rotation(V(0, 0, 1), C), V(n.x, n.y, 0))
    raise ValueError(move)


def posed_items(pose, items=None):
    """Return (items, shapes) with shapes moved to the pose. Items are reused, shapes are copies."""
    pose = clamp_pose(pose)
    items = list(items) if items is not None else static_items()
    items += services.build_chains(pose) + xaxis.build_belts(pose) + yaxis.build_belt(pose)
    shapes = []
    for it in items:
        s = it.shape.copy()
        pl = placement_for(it.move, pose)
        s.Placement = pl.multiply(s.Placement)
        shapes.append(s)
    return items, shapes


def machine_xy(pose):
    """Nozzle position in machine coordinates (TS section 4) and frame coordinates."""
    pose = clamp_pose(pose)
    n = head.nozzle_world_ref()
    frame_xyz = (n.x + pose["X"], n.y + pose["Y"], n.z + pose["Z"])
    return pose, frame_xyz


def make_document(pose, path=None, name="TEVO_BW_PnP"):
    """Create a FreeCAD document with one group per subsystem. Colours are stored in a PnpColor
    property (headless sessions have no view providers); out/apply_colors.FCMacro applies them."""
    pose = clamp_pose(pose)
    items, shapes = posed_items(pose)
    doc = App.newDocument(name)
    groups = {}
    for sysname in SYSTEM_ORDER:
        grp = doc.addObject("App::DocumentObjectGroup", sysname)
        groups[sysname] = grp
    pcol = g.part_colors((it.name, it.kind, it.color) for it in items)
    for it, s in zip(items, shapes):
        obj = doc.addObject("Part::Feature", it.name)
        obj.Shape = it.shape
        obj.Placement = placement_for(it.move, pose).multiply(obj.Placement) if it.move != "posed" else obj.Placement
        obj.addProperty("App::PropertyColor", "PnpColor", "PnP", "display colour")
        obj.PnpColor = tuple(it.color)
        obj.addProperty("App::PropertyColor", "PartColor", "PnP", "display colour, one per part (pnp gui default)")
        obj.PartColor = pcol[it.name]
        obj.addProperty("App::PropertyString", "MoveGroup", "PnP", "motion group")
        obj.MoveGroup = it.move
        obj.addProperty("App::PropertyString", "Kind", "PnP", "stock/buy/make/print")
        obj.Kind = it.kind
        obj.addProperty("App::PropertyFloat", "MassGram", "PnP", "mass estimate, g")
        obj.MassGram = float(it.mass)
        if it.bom:
            obj.addProperty("App::PropertyString", "BOM", "PnP", "BOM line")
            obj.BOM = it.bom
        grp = groups.get(it.system)
        if grp is None:
            grp = groups[it.system] = doc.addObject("App::DocumentObjectGroup", it.system)
        grp.addObject(obj)
    for o in doc.Objects:          # headless documents can store Visibility = false; force everything shown
        if hasattr(o, "Visibility"):
            o.Visibility = True
    sheet = doc.addObject("Spreadsheet::Sheet", "Pose")
    for r, k in enumerate(("X", "Y", "Z", "C"), start=1):
        sheet.set("A%d" % r, k)
        sheet.set("B%d" % r, str(pose[k]))
    doc.recompute()
    if path:
        doc.saveAs(path)
    return doc, items

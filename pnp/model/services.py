"""Services, rev C: drag chains (FR-5). The X chain tray is an Al angle on three separate printed
brackets bolted into the lower side slot of the rear C-beam (below the bridge belt clamp path).

The vacuum/valve panel and the electronics box are left out of the model for now (TS 7.4 and 8 still
apply; they return as their own module)."""
import FreeCAD as App

import params as P
from . import geom as g
from .item import Item

V = g.V

CHAIN_R = 25.0
CHAIN_LINK = (16.0, 14.0, 10.0)
X_CHAIN_Y = 609.0         # centre plane of the X chain behind the rear C-beam
X_CHAIN_FIX_X = 287.0
Y_CHAIN_DX = -12.0        # Y chain centre relative to the bridge centre
Y_CHAIN_FIX_Y = 280.0


TRAY_X = (40.0, 535.0)
TRAY_BRACKETS = (52.0, 287.0, 522.0)


def tray_bracket(x):
    """L bracket: plate on the rear C-beam outer face (M5 into the lower lip slot), arm out under the
    bridge belt clamp, upright to the tray."""
    d = P.derive()
    fw = d["frame_width"]
    zb = d["cb_z"][0]
    ztray = d["cb_z"][1]
    yt0 = fw + 24
    # rev E: one Y-Z profile 20 mm thick (plate, arm, upright, gusset) -> prints lying on its side
    plate = g.box_r(x - 10, x + 10, fw, fw + 5, zb, zb + 18)
    arm = g.box_r(x - 10, x + 10, fw, fw + 54, zb, zb + 8)
    up = g.box_r(x - 10, x + 10, yt0 + 14, yt0 + 22, zb, ztray)
    rib = g.Part.Face(g.Part.makePolygon([V(x - 10, y, z) for y, z in
                                          ((yt0 + 14, zb + 8), (yt0 - 6, zb + 8), (yt0 + 14, zb + 28),
                                           (yt0 + 14, zb + 8))])).extrude(V(20, 0, 0))
    br = plate.fuse(arm).fuse(up).fuse(rib).removeSplitter()
    br = g.drill(br, "M5", [(x, fw + 5, zb + 10)], d=(0, -1, 0), depth=6, cbore=0, screw=10)
    br = g.drill(br, "M3", [(x, yt0 + 18, ztray)], d=(0, 0, -1), depth=8, insert=True)
    return br


def build_tray():
    d = P.derive()
    fw = d["frame_width"]
    z = d["cb_z"][1]
    items = []
    tray = g.box_r(TRAY_X[0], TRAY_X[1], fw + 24, fw + 74, z, z + 2).fuse(
        g.box_r(TRAY_X[0], TRAY_X[1], fw + 72, fw + 74, z + 2, z + 18))
    g.take_screws()
    tray = g.drill(tray, "M3", [(x, fw + 42, z + 2) for x in TRAY_BRACKETS], depth=4, cbore=0, screw=8)
    items.append(Item("XChain_Tray", tray.removeSplitter(), g.C_ALU, "chains", mat="alu",
                      bom="X chain tray, Al angle 50x18x2, %.0f mm" % (TRAY_X[1] - TRAY_X[0]), kind="make"))
    for k, x in enumerate(TRAY_BRACKETS):
        items.append(Item("XChain_TrayBracket_%d" % (k + 1), tray_bracket(x), g.C_ORANGE, "chains", mat="PETG",
                          bom="X chain tray bracket (printed PETG)", kind="print",
                          fasteners={"M5x10 SHCS + M5 T-nut (C-beam lower slot)": 1,
                                     "M3x8 SHCS + heat-set insert (tray)": 1}))
    items.append(Item("Screws_XChainTray", g.take_screws(), (0.22, 0.22, 0.24), "chains", mass=0, check=False))
    return items


def build_chains(pose):
    """Drag chains at the given machine pose (frame coords, already posed)."""
    d = P.derive()
    bx = d["bx_min"] + pose["X"]
    cy = d["cy_min"] + pose["Y"]
    items = []
    H = CHAIN_LINK[2]
    zl = d["cb_z"][1] + 2 + H / 2
    fix_x = (d["bx_min"] + d["bx_max"]) / 2          # chain fixed at mid travel
    slack_x = (d["bx_max"] - fix_x) / 2 + 8
    links = g.drag_chain((fix_x, X_CHAIN_Y, zl), (bx, X_CHAIN_Y, zl + 2 * CHAIN_R), (1, 0, 0), (0, 0, 1),
                         CHAIN_R, slack_x, link=CHAIN_LINK)
    items.append(Item("XChain", g.compound(links), g.C_CHAIN, "chains", move="posed", mass=0,
                      bom="Drag chain 10x15 (stock), X run", kind="stock", check=False))
    xc = bx + Y_CHAIN_DX
    zb = d["bridge_z"][1] + H / 2
    slack_y = (d["cy_max"] - Y_CHAIN_FIX_Y) / 2 + 8
    links = g.drag_chain((xc, Y_CHAIN_FIX_Y, zb), (xc, cy, zb + 2 * CHAIN_R), (0, 1, 0), (0, 0, 1),
                         CHAIN_R, slack_y, link=CHAIN_LINK)
    items.append(Item("YChain", g.compound(links), g.C_CHAIN, "chains", move="posed", mass=0,
                      bom="Drag chain 10x15 (stock), Y run", kind="stock", check=False))
    return items

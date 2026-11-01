"""Fixed tooling (TS 7.5-7.8), rev B.

One aluminium tooling plate spans the PCB area and the tooling strip over the right end of the frame.
The strip lies right of the bridge travel (beam right face <= X 522) and inside the nozzle reach, so
the beam never passes over the tape lanes, the up camera or the magazine. Tapes run along X and feed
in from the right end; the magazine pockets run along Y.
"""
import math

import FreeCAD as App

import params as P
from . import geom as g
from .item import Item

V = g.V


def lane_y(i):
    return P.LANE0_Y + i * P.LANE_PITCH


def magazine_pockets():
    return [(P.MAGAZINE_X, P.MAGAZINE_Y0 + k * P.MAGAZINE_PITCH) for k in range(P.MAGAZINE_POCKETS)]


def feeder_points(i):
    """Pick pocket XY for lane i (0-based), frame coords."""
    from . import feeder
    return feeder.pick_xy(lane_y(i))


def build_table():
    d = P.derive()
    items = []
    zt = P.TABLE_TOP_Z
    zb = zt - P.TABLE_T
    ux, uy = P.UPCAM_XY
    plate = g.rbox(P.TABLE_X[0], P.TABLE_X[1], P.TABLE_Y[0], P.TABLE_Y[1], zb, zt, 10, axis="z")
    plate = plate.cut(g.cyl(12.5, 10, (ux, uy, zb - 1)))
    plate = plate.cut(g.cyl(14.5, 2.2, (ux, uy, zt - 2)))                          # window seat
    fast = {}
    plate = g.drill(plate, "M5", [(x, y, zb) for x, y in P.LEVEL_POINTS], d=(0, 0, 1), depth=8, tap=True)
    px, py = P.PCB_ORIGIN
    L, W, T = P.PCB_SIZE
    plate = plate.cut(g.cyl(1.5, 8, (px + 20, py - 1.5, zb - 1))).cut(g.cyl(1.5, 8, (px + L - 20, py - 1.5, zb - 1)))
    plate = g.drill(plate, "M3", [(px - 6, py + W / 2 + s, zt) for s in (-4, 4)], depth=8, tap=True)
    for s in (-20, 20):                                                             # clamp slots
        plate = plate.cut(g.box_r(px + L / 2 + s - 1.7, px + L / 2 + s + 1.7, py + W + 4, py + W + 30, zb - 1, zt + 1))
    from . import feeder
    lanes_y = [lane_y(i) for i in range(P.LANES)]
    lane_pts = [(x, yy, zb) for ly in lanes_y for x, yy in feeder.mount_points(ly)]
    plate = g.drill(plate, "M3", lane_pts, d=(0, 0, 1), depth=8, cbore=3.2)          # lanes bolt on from below
    ya, yb = feeder.bank_y(lanes_y)
    ex0, ex1 = feeder.EXIT_SLOT_X
    plate = plate.cut(g.rbox(ex0, ex1, ya - 10, yb + 10, zb - 1, zt + 1, 3, axis="z"))   # empty-tape exit slot
    bank_pts = [(506.5, r, zt) for r in (ya - 7.0, yb + 7.0, (ya + yb) / 2)]
    bank_pts += [(524.0, r, zt) for r in (ya - 7.0, yb + 7.0, (ya + yb) / 2)]
    bank_pts += [(x, yy, zt) for x, yy in feeder.bin_feet(lanes_y)]
    plate = g.drill(plate, "M3", bank_pts, depth=8, tap=True)
    mag = magazine_pockets()
    plate = g.drill(plate, "M5", [(P.MAGAZINE_X, mag[0][1] - 9), (P.MAGAZINE_X, mag[-1][1] + 11)], depth=8, tap=True)
    plate = g.drill(plate, "M3", [(ux + a * 20, uy + b * 20, zb) for a in (-1, 1) for b in (-1, 1)],
                    d=(0, 0, 1), depth=8, tap=True)
    items.append(Item("Tooling_Plate", plate, g.C_ALU, "table", mat="alu",
                      bom="Tooling plate Al 6 mm %.0f x %.0f, PCB area + tooling strip (one piece)" %
                          (P.TABLE_X[1] - P.TABLE_X[0], P.TABLE_Y[1] - P.TABLE_Y[0]), kind="make"))

    # 3-point support: one levelling screw on the left tie, two posts on the right tie bar
    ztie_l = d["cb_z"][1]
    ztie_r = d["cb_z"][0] + P.TIE_B[1]
    for k, (x, y) in enumerate(P.LEVEL_POINTS):
        z0 = ztie_l if x < 100 else ztie_r
        post = g.cyl(8, zb - 4 - z0, (x, y, z0)) if z0 < zb - 10 else None
        scr = g.cyl(2.5, zb - (zb - 4 if post else z0) + 6, (x, y, zb - 4 if post else z0)).fuse(
            g.cyl(4.6, 4, (x, y, zb - 4)).cut(g.cyl(2.5, 6, (x, y, zb - 5))))
        s = scr.fuse(post) if post else scr
        items.append(Item("Table_Support_%d" % (k + 1), s, g.C_STEEL, "table", mat="steel",
                          bom="Table support: M5 levelling screw + lock nut" + (" on Al post D16" if post else ""),
                          kind="buy", check=False, fasteners={"M5x12 SHCS + T-nut (support base)": 1}))

    # PCB + datums (TS 7.8)
    pcb = g.box_r(px, px + L, py, py + W, zt, zt + T)
    items.append(Item("PCB_demo", pcb, g.C_PCB, "table", mat="FR4", bom=None, check=True))
    pads, parts = [], []
    for i in range(10):
        for j in range(5):
            cx, cy = px + 25 + i * 11.0, py + 22 + j * 14.0
            for s in (-1, 1):
                pads.append(g.box_c(cx + s * 0.95, cy, zt + T + 0.02, 0.9, 1.3, 0.04))
            if (i + j) % 3 != 0:
                parts.append(g.box_c(cx, cy, zt + T + 0.45, 2.0, 1.25, 0.9))
    for fx, fy in ((px + 6, py + 6), (px + L - 6, py + 6), (px + 6, py + W - 6)):
        pads.append(g.cyl(0.5, 0.04, (fx, fy, zt + T)))
    items.append(Item("PCB_Pads_Fiducials", g.compound(pads), g.C_COPPER, "table", bom=None, check=False))
    items.append(Item("PCB_Placed_0805", g.compound(parts), g.C_DARK, "table", bom=None, check=False))
    for k, x in enumerate((px + 20, px + L - 20)):
        items.append(Item("Datum_Pin_%d" % (k + 1), g.cyl(1.5, 12, (x, py - 1.5, zb)), g.C_STEEL, "table",
                          mat="steel", bom="Datum pin 3 mm hardened, press fit", kind="buy", check=False))
    stop = g.rbox(px - 12, px, py + W / 2 - 8, py + W / 2 + 8, zt, zt + 5, 2, axis="z")
    g.take_screws()
    stop = g.drill(stop, "M3", [(px - 6, py + W / 2 + s, zt + 5) for s in (-4, 4)], depth=6, cbore=2, screw=8)
    stop = stop.fuse(g.cyl(1.5, 3, (px - 3, py + W / 2, zt + 2.5), (1, 0, 0)))
    items.append(Item("Datum_XStop_Plunger", stop, g.C_STEEL, "table", mat="steel",
                      bom="Spring plunger X stop block", kind="buy", fasteners={"M3x8 SHCS": 2}))
    for s in (-20, 20):
        g._SCREWS.append(g.screw_solid("M3", (px + L / 2 + s, py + W + 18, zt + 5), (0, 0, -1), 10, head_at=-0.5))
    clamp = g.rbox(px + L / 2 - 30, px + L / 2 + 30, py + W, py + W + 30, zt, zt + 5, 3, axis="z")
    clamp = clamp.fuse(g.rbox(px + L / 2 - 25, px + L / 2 + 25, py + W, py + W + 8, zt + 5, zt + 8, 2, axis="z"))
    for s in (-20, 20):
        clamp = clamp.cut(g.box_r(px + L / 2 + s - 1.7, px + L / 2 + s + 1.7, py + W + 10, py + W + 26, zt - 1, zt + 6))
    items.append(Item("PCB_SlideClamp", clamp.removeSplitter(), g.C_ORANGE, "table", mat="PETG",
                      bom="PCB slide clamp (printed PETG)", kind="print",
                      fasteners={"M3x10 SHCS + washer (clamp slots)": 2}))

    # up-looking camera: one printed housing hung under the plate (TS 7.6)
    from .head import CAM_BOARD
    hz0 = zb - 42
    hsg = g.rbox(ux - 24, ux + 24, uy - 24, uy + 24, hz0, zb, 6, axis="z")
    hsg = hsg.cut(g.rbox(ux - 21, ux + 21, uy - 21, uy + 21, hz0 + 3, zb + 1, 4, axis="z"))
    hsg = hsg.cut(g.box_r(ux + 18, ux + 25, uy - 6, uy + 6, hz0 + 3, hz0 + 12))      # USB exit
    for a in (-1, 1):
        for b in (-1, 1):
            hsg = hsg.fuse(g.cyl(3.5, 42, (ux + a * 20, uy + b * 20, hz0)))
    hsg = g.drill(hsg, "M3", [(ux + a * 20, uy + b * 20, hz0) for a in (-1, 1) for b in (-1, 1)],
                  d=(0, 0, 1), depth=44, cbore=0, screw=45)
    items.append(Item("UpCam_Housing", hsg.removeSplitter(), g.C_ORANGE, "table", mat="PETG",
                      bom="Up camera housing, one piece (printed PETG)", kind="print",
                      fasteners={"M3x45 SHCS (housing -> plate)": 4, "M2x6 screw (camera board)": 4}))
    items.append(Item("Screws_Table", g.take_screws(), (0.22, 0.22, 0.24), "table", mass=0, check=False))
    items.append(Item("UpCam_Board", g.box_c(ux, uy, hz0 + 6.8, 38, 38, 1.6), g.C_PCB, "table", mass=10,
                      bom=CAM_BOARD, kind="buy"))
    items.append(Item("UpCam_LensHolder", g.box_c(ux, uy, hz0 + 13.6, 14, 14, 12), g.C_DARK, "table", mass=4))
    items.append(Item("UpCam_Lens_M12", g.cyl(7, 17, (ux, uy, hz0 + 19.6)), g.C_DARK, "table", mass=8,
                      bom="M12 lens f = 6 mm, for 1/4\" sensor or larger, low distortion, with lock nut (up camera: "
                          "FOV ~21 x 13 mm at the hovering part, 0.017 mm/px)", kind="buy"))
    items.append(Item("UpCam_Window", g.cyl(14.3, 1.0, (ux, uy, zt - 2)), g.C_GLASS, "table", mass=1,
                      bom="Up camera cover glass D29", kind="buy", check=False))
    items.append(Item("UpCam_Backlight_Ring", g.tube(24, 15, 2.5, (ux, uy, zt)), g.C_WHITE, "table", mass=8,
                      bom="LED ring diffuse (up camera silhouette light)", kind="buy"))
    return items


FEEDER_NOCHECK = ("Tape", "TapeParts", "CoverTape", "ServoGear", "Inserts", "PinchSpring", "PinchAxle", 
                  "GuideBar", "ORing_1", "ORing_2", "OneWay_1", "OneWay_2", "PawlPin_1", "PawlPin_2",
                  "PawlSpring_1", "PawlSpring_2", "Pawl_1", "Pawl_2")


def build_feeders():
    """TBW-Feeder v3.0 lanes (model/feeder.py) + bank parts (exit chute, waste bin, reel rack)."""
    from . import feeder
    items = []
    for i in range(P.LANES):
        g.take_screws()
        parts = feeder.build_lane(lane_y(i))
        for suf, shp, col, mat, mass, bom, kind in parts:
            items.append(Item("Lane%d_%s" % (i + 1, suf), shp, col, "feeders", mat=mat, mass=mass, bom=bom,
                              kind=kind, fasteners=feeder.LANE_FASTENERS if suf == "Body" else None,
                              check=suf not in FEEDER_NOCHECK))
        items.append(Item("Screws_Lane%d" % (i + 1), g.take_screws(), (0.22, 0.22, 0.24), "feeders", mass=0,
                          check=False))
    g.take_screws()
    for name, shp, col, mat, mass, bom, kind, fast in feeder.build_bank([lane_y(i) for i in range(P.LANES)]):
        items.append(Item(name, shp, col, "feeders", mat=mat, mass=mass, bom=bom, kind=kind, fasteners=fast,
                          check=not name.startswith("Reel")))
    items.append(Item("Screws_FeederBank", g.take_screws(), (0.22, 0.22, 0.24), "feeders", mass=0, check=False))
    return items


def build_magazine():
    items = []
    zt = P.TABLE_TOP_Z
    pk = magazine_pockets()
    mx = P.MAGAZINE_X
    y0, y1 = pk[0][1] - 13, pk[-1][1] + 15
    bar = g.rbox(mx - 12, mx + 12, y0, y1, zt, zt + 12, 4, axis="z")
    bar = g.fillet_safe(bar, 1.0)
    for k, (x, y) in enumerate(pk):
        bar = bar.cut(g.cyl(4.6, 9, (x, y, zt + 4)))
        bar = bar.cut(g.box_r(x - 7, x + 7, y - 1.2, y + 1.2, zt + 8, zt + 13))       # twist-lock key slot
        for n in range(k + 1):                                                         # index marks 1..6
            bar = bar.cut(g.cyl(0.6, 1, (x - 10, y - 5 + n * 2.0, zt + 11.5)))
    g.take_screws()
    bar = g.drill(bar, "M5", [(mx, pk[0][1] - 9, zt + 12), (mx, pk[-1][1] + 11, zt + 12)], depth=14, cbore=5,
                  screw=16)
    items.append(Item("Screws_Magazine", g.take_screws(), (0.22, 0.22, 0.24), "magazine", mass=0, check=False))
    items.append(Item("Nozzle_Magazine_Bar", bar, g.C_ALU, "magazine", mat="alu",
                      bom="Nozzle magazine bar, Al 24x12, 6 pockets along Y", kind="make",
                      fasteners={"M5x16 SHCS (magazine -> plate)": 2, "M2x5 screw (leaf spring)": 2}))
    spring = g.box_r(mx + 9, mx + 9.4, y0 + 2, y1 - 2, zt + 12, zt + 14)
    items.append(Item("Magazine_LeafSpring", spring, g.C_STEEL, "magazine", mat="steel",
                      bom="Magazine retaining leaf spring", kind="buy", check=False))
    sizes = (0.45, 0.75, 1.1, 1.75, 0.75, 0.0)
    for k, (x, y) in enumerate(pk):
        if k == 1:
            continue  # tip 2 is on the head in the reference pose
        tip = g.cyl(2.2, 9, (x, y, zt + 4)).fuse(g.cyl(4.2, 3, (x, y, zt + 13))).fuse(g.cyl(1.6, 4, (x, y, zt + 16)))
        if sizes[k] > 0:
            tip = tip.cut(g.cyl(sizes[k] / 2, 30, (x, y, zt)))
        items.append(Item("Tip_%d" % (k + 1), tip, g.C_BRASS, "magazine", mass=1.5,
                          bom="Juki-compatible tip (set of 6, see TS 7.4)" if k == 0 else None, kind="buy",
                          check=False))
    return items

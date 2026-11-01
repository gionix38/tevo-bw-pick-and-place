"""Design parameters for the TEVO-BW pick-and-place conversion (TEVO-BW-PNP-TS-001 rev 1.1).

All lengths in mm, masses in g, angles in degrees.

Frame coordinates (used for modelling):
    origin = floor level, under the left end of the front C-beam, front face.
    +X along the C-beams (left -> right), +Y front -> rear, +Z up.
Machine coordinates (TS section 4, used by OpenPnP) are the same axes with the origin at the
nozzle home position; see MACHINE_ORIGIN below.

Values marked (WP0) are taken from the project model and must be replaced by measurements.
"""

# ---------------------------------------------------------------- stock members (TS section 3)
# Bounding sizes measured from the project STLs (C-Beam assembly.stl etc.).
CB_SECTION = (40.0, 80.0)      # C-beam: width (Y) x height (Z) once laid horizontal
CB_EXTR_LEN = 550.0            # C-beam extrusion length
CB_CAP = 12.0                  # end cap thickness -> 574 mm assembly (WP0)
CB_LEN = CB_EXTR_LEN + 2 * CB_CAP
CB_GAP = 480.0                 # inner gap between the C-beams, measured in the stock STEP (WP0)
#   Stock model: C-beams at X -30..10 and 490..530 -> 480 mm inner gap. The 20x80x500 top tie sits
#   on the C-beam ends, it does not fit between them, so it is cut to 480 (design note D1).
CB_CHANNEL = (18.0, 62.0, 27.0)  # C channel: v_from, v_to (height), depth

BASE_Z = 20.0                  # C-beam underside above the floor (corner blocks + rubber feet)
FOOT_H = 10.0                  # rubber foot height; corner blocks start at FOOT_H
#   rev B: the 20x80x210 legs are removed; the four printed corner blocks are the legs.
TIE_A = (20.0, 80.0, 480.0)    # 20x80x500 stock top tie, cut to the gap
TIE_B = (40.0, 20.0, 480.0)    # stock X gantry 20x40x485 bar, cut to the gap, at the bottom of the right end
#   The 40x80x550 used as the Y bridge is the stock bed-axis extrusion in the project model; the
#   stock X gantry is the 2 x 20x40x485 pair. TS 3 calls the 550 beam "the X beam" (design note D2).

BRIDGE_LEN = 550.0             # 40x80x550 stock X beam, now the Y bridge
BRIDGE_SECTION = (40.0, 80.0)  # width (X) x height (Z)
BRIDGE_RISER_H = 32.0          # riser between X blocks and bridge (clears tape bank under beam)
BRIDGE_PLATE = (54.0, 64.0, 8.0)   # bridge end foot on the X block: X, Y, thickness

# ---------------------------------------------------------------- linear guides
# MGN series: rail W, rail H, block W, block L (H type), total H (rail bottom -> block top)
MGN = {
    "MGN9":  dict(rail_w=9.0,  rail_h=6.5, blk_w=20.0, blk_l=39.9, H=10.0, rail_gpm=0.38, blk_g=26.0,
                  hole_b=15.0, hole_c=16.0, blk_screw="M3", rail_pitch=20.0, rail_screw="M3"),
    "MGN12": dict(rail_w=12.0, rail_h=8.0, blk_w=27.0, blk_l=45.4, H=13.0, rail_gpm=0.65, blk_g=37.0,
                  hole_b=20.0, hole_c=20.0, blk_screw="M3", rail_pitch=25.0, rail_screw="M3"),
}
X_RAIL = "MGN12"
X_RAIL_LEN = 550.0
X_BLOCKS_PER_RAIL = 1          # rev C: one MGN12H per bridge end (smaller bridge ends)
X_BLOCK_PITCH = 52.0           # only used with 2 blocks per rail
X_MAX_BEAM_FACE = 522.0        # soft limit: beam right face stays left of the tooling strip
Y_RAIL = "MGN12"
Y_RAIL_LEN = 500.0
Y_BLOCK_PITCH = 52.0
Z_RAIL = "MGN9"
Z_RAIL_LEN = 90.0
RAIL_END_MARGIN = 10.0         # TS 7.1 / 7.2: unused rail at each end

# ---------------------------------------------------------------- drives
GT2_PITCH = 2.0
PULLEY_TEETH = 20
X_BELT_W = 9.0
Y_BELT_W = 6.0                 # stock belt stays on the bridge
MICROSTEPS = 16
Z_MICROSTEPS = 4               # rev F: at 1/16 Z needs 1600 steps/mm -> 96k steps/s for PR-3 (60 mm/s), far over the
#                                8-bit board; 1/4 gives 400 steps/mm (2.5 um), 24k steps/s
FULL_STEPS = 200
Z_SCREW_LEAD = 2.0             # TR8x2
C_RATIO = 1.0
JACKSHAFT_D = 8.0
JACKSHAFT_X = -16.0            # jackshaft axis, frame X
DRIVE_Z = 60.0                 # X belt plane centre height (middle of the C channel)

# ---------------------------------------------------------------- head (TS 7.3)
Z_STROKE = 40.0                # screw travel; soft stops at 2 and 38
Z_USABLE = 35.0                # FR-11
Z_SOFT_MIN = -37.4             # firmware soft limit: PCB-top place height minus 1.0 mm of compliance
NOZZLE_TIP_HOME_Z = 152.0      # world Z of the tip at Z home (top switch)
HEAD_PLATE_T = 8.0             # one-piece printed head carriage (replaces mother plate + head plate)
HEAD_PLATE_MAT = "PETG"
Z_MOTOR = "NEMA8_LIN30"        # rev D: NEMA8 external linear stepper, integral 2 mm lead screw (FR-12)
C_MOTOR = "NEMA8_HOLLOW30"     # rev D: NEMA8 hollow shaft on the nozzle axis, direct drive, vacuum through
CAMERA_OFFSET = (2.0, 57.0)    # down camera axis relative to nozzle axis, machine X/Y (nominal)
MASS_BUDGET = 500.0            # FR-4
PRINT_FILL = 0.70              # printed parts: effective density factor (4 walls + ~40% infill)
PRINT_BED = (220.0, 220.0, 250.0)   # smallest common printer bed X, Y, Z (printed parts must fit)

MOTORS = {  # size, body length, mass (typical catalogue values)
    "NEMA17_40": dict(size=42.3, length=40.0, mass=280.0, boss=22.0, shaft=5.0, shaft_len=24.0),
    "NEMA17_23": dict(size=42.3, length=23.0, mass=150.0, boss=22.0, shaft=5.0, shaft_len=20.0),
    "NEMA14_20": dict(size=35.0, length=20.0, mass=110.0, boss=22.0, shaft=5.0, shaft_len=18.0),
    "NEMA11_32": dict(size=28.0, length=32.0, mass=110.0, boss=22.0, shaft=5.0, shaft_len=18.0),
    "NEMA8_HOLLOW30": dict(size=20.0, length=30.0, mass=60.0, boss=16.0, shaft=5.0, shaft_len=0.0,
                           torque=0.018, note="hollow shaft OD5/ID3, bearing runout <= 0.02 mm required (FR-14)"),
    "NEMA8_LIN30": dict(size=20.0, length=30.0, mass=60.0, boss=16.0, shaft=5.0, shaft_len=0.0,
                        torque=0.018, note="external linear, T5x2 screw 95 mm + flange nut"),
}

# ---------------------------------------------------------------- dynamics (PR-1..PR-4, PR-10), rev F
# Aluminium profiles are modelled with a solid core; their real mass comes from the catalogue (kg/m, typical
# for V-slot / C-beam, +-15 %). WP0 weighs the bridge beam.
PROFILE_KG_M = {"20x40": 0.80, "20x80": 1.50, "40x80": 2.40, "C40x80": 2.40}
BOARD_STEP_RATE = 40000.0      # steps/s per axis, MKS Gen (ATmega2560) + Marlin 2 without multi-stepping
PSU_V = 24.0                   # (WP0) 12 or 24 V; the torque check uses the matching pull-out curve
NEMA17_HOLD = 0.42             # N m, 40 mm stock motors (X, Y)
NEMA17_ROTOR = 5.4e-6          # kg m2
XJACK_INERTIA = 3.0e-6         # kg m2, 8 mm jackshaft 520 mm + 4 pulleys
RAIL_DRAG = 1.5                # N per MGN12H block with seals
# fraction of holding torque left at speed (typical 1.5 A hybrid stepper, chopper driver)
PULLOUT = {24.0: ((0, 1.0), (300, 0.80), (600, 0.60), (900, 0.45), (1200, 0.35), (1800, 0.25)),
           12.0: ((0, 1.0), (300, 0.65), (600, 0.40), (900, 0.25), (1200, 0.18), (1800, 0.10))}
TORQUE_SF = 2.0                # required margin: pull-out torque / needed torque
PR_V_XY = 400.0                # PR-1 mm/s
PR_A = {"X": 3000.0, "Y": 4000.0}   # PR-2 mm/s2
PR_V_Z = 60.0                  # PR-3 mm/s
Z_ACCEL = 1500.0               # mm/s2 used for the cycle estimate
Z_COMPLIANCE = 1.5             # N, nozzle compliance spring, only at contact (slide weight comes from the model)
SAFE_Z_MARGIN = 2.0            # mm, OpenPnP Safe Z: tip this far above the tallest tooling in reach
Z_SCREW_EFF = 0.35             # T5x2 trapezoidal screw + plastic nut
VISION_S = 0.25                # bottom vision settle + capture + process per part
VAC_S = 0.12                   # pick dwell + place dwell + blow-off
FEED_S = 0.55                  # TBW-Feeder 4 mm feed (3 servo moves x 180 ms)

# ---------------------------------------------------------------- table & tooling (TS 7.5-7.8)
TIE_TOP_Z = BASE_Z + CB_SECTION[1]          # top of the C-beams
TABLE_STANDOFF = 8.0
TABLE_T = 6.0
TABLE_TOP_Z = TIE_TOP_Z + TABLE_STANDOFF + TABLE_T
TABLE_X = (25.0, 660.0)        # one plate: PCB area + tooling strip over the right end
TABLE_Y = (58.0, 502.0)        # inside the bridge foot plates (Y -12..52 and 508..572)

PCB_SIZE = (160.0, 100.0, 1.6)
PCB_ORIGIN = (250.0, 250.0)    # datum corner (front-left) in frame XY
PCB_AREA = (200.0, 150.0)      # flatness area, TS 7.8

# rev B: all tooling sits in the strip right of the bridge's travel (beam right face <= X 522),
# so the beam never passes over it. Tapes run along X and feed in from the right end.
LANES = 8
LANE_PITCH = 22.0              # TS 7.7: 20-24, now along Y
LANE0_Y = 150.0                # centre of lane 1 (front)
FEEDER_X = (526.0, 653.0)      # TBW-Feeder footprint along X (inner end -> tape inlet)
PICK_X = 540.0                 # first open pocket (pick window)
FEEDER_H = 72.0                # lane height above table (tower, X > 592)
TAPE_POCKET_PITCH = 4.0

MAGAZINE_POCKETS = 6
MAGAZINE_PITCH = 18.0          # TS 7.5: >= 18
MAGAZINE_X = 548.0             # pocket centre line, frame X (pockets along Y)
MAGAZINE_Y0 = 377.0            # pocket 1

UPCAM_XY = (548.0, 338.0)      # up-looking camera axis, between tape bank and magazine
LEVEL_POINTS = ((26.0, 280.0), (538.0, 150.0), (538.0, 420.0))   # 3-point table support

# ---------------------------------------------------------------- motion envelope
BRIDGE_X_REF = None            # filled in derive()


def mgn(name):
    return MGN[name]


def derive():
    """Return a dict of derived numbers used by builders, report and checks."""
    d = {}
    xr = MGN[X_RAIL]
    yr = MGN[Y_RAIL]
    d["cb_front_y"] = (0.0, CB_SECTION[0])
    d["cb_rear_y"] = (CB_SECTION[0] + CB_GAP, 2 * CB_SECTION[0] + CB_GAP)
    d["frame_width"] = 2 * CB_SECTION[0] + CB_GAP
    d["cb_z"] = (BASE_Z, BASE_Z + CB_SECTION[1])
    d["x_rail_x"] = (CB_CAP, CB_CAP + X_RAIL_LEN)
    d["x_rail_top"] = d["cb_z"][1] + xr["rail_h"]
    d["x_block_top"] = d["cb_z"][1] + xr["H"]
    d["riser_top"] = d["x_block_top"] + BRIDGE_PLATE[2] + BRIDGE_RISER_H
    d["bridge_z"] = (d["riser_top"], d["riser_top"] + BRIDGE_SECTION[1])
    d["bridge_y"] = ((d["frame_width"] - BRIDGE_LEN) / 2, (d["frame_width"] + BRIDGE_LEN) / 2)
    # bridge (beam centre X) travel limits
    span = xr["blk_l"] + (X_BLOCK_PITCH if X_BLOCKS_PER_RAIL == 2 else 0.0)
    half_carriage = max(BRIDGE_PLATE[0], span) / 2
    d["bx_min"] = d["x_rail_x"][0] + RAIL_END_MARGIN + half_carriage
    d["bx_max"] = min(d["x_rail_x"][1] - RAIL_END_MARGIN - half_carriage,
                      X_MAX_BEAM_FACE - BRIDGE_SECTION[0] / 2)
    # Y rail on +X face of the bridge, centred in its height
    d["y_rail_x0"] = BRIDGE_SECTION[0] / 2           # relative to bridge centre X
    d["y_rail_zc"] = (d["bridge_z"][0] + d["bridge_z"][1]) / 2
    d["y_rail_y"] = (d["frame_width"] / 2 - Y_RAIL_LEN / 2, d["frame_width"] / 2 + Y_RAIL_LEN / 2)
    half_y = (Y_BLOCK_PITCH + yr["blk_l"]) / 2
    d["cy_min"] = d["y_rail_y"][0] + RAIL_END_MARGIN + half_y
    d["cy_max"] = d["y_rail_y"][1] - RAIL_END_MARGIN - half_y
    d["mother_x0"] = d["y_rail_x0"] + yr["H"]         # mother plate back face, rel. bridge centre
    d["mother_t"] = 0.0                               # rev B: no separate mother plate
    d["head_plate_x0"] = d["mother_x0"]
    d["nozzle_dx"] = d["head_plate_x0"] + HEAD_PLATE_T + 24.0   # nozzle axis rel. bridge centre X
    d["nozzle_x_min"] = d["bx_min"] + d["nozzle_dx"]
    d["nozzle_x_max"] = d["bx_max"] + d["nozzle_dx"]
    d["nozzle_y_min"] = d["cy_min"]
    d["nozzle_y_max"] = d["cy_max"]
    d["x_travel"] = d["bx_max"] - d["bx_min"]
    d["y_travel"] = d["cy_max"] - d["cy_min"]
    d["pcb_top_z"] = TABLE_TOP_Z + PCB_SIZE[2]
    d["tip_min_z"] = NOZZLE_TIP_HOME_Z - Z_STROKE
    # steps
    d["steps_xy"] = FULL_STEPS * MICROSTEPS / (PULLEY_TEETH * GT2_PITCH)
    d["steps_z"] = FULL_STEPS * Z_MICROSTEPS / Z_SCREW_LEAD
    d["steps_c"] = FULL_STEPS * MICROSTEPS * C_RATIO / 360.0
    d["pulley_pd"] = PULLEY_TEETH * GT2_PITCH / 3.141592653589793
    return d


# Machine origin (TS section 4): nozzle at home = X min, Y min, Z top.
def machine_origin():
    d = derive()
    return (d["nozzle_x_min"], d["nozzle_y_min"], NOZZLE_TIP_HOME_Z)

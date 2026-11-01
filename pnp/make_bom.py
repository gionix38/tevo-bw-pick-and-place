"""Purchasing BOM workbook: out/TEVO_BW_PnP_BOM.xlsx.

Combines the model BOM (out/bom.csv, written by `pnp build`, includes the 8 feeder lanes and the feeder bank) with
the parts the model does not contain: the vacuum circuit (TS 7.4), E-stop and pump switch (TS 8.2, 10), camera
USB cables, and the feeder controller (feeder/ELECTRONICS.md). Unit prices are left for the user to fill in.

    python make_bom.py
"""
import csv
import os

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "out", "bom.csv")
OUT = os.path.join(HERE, "out", "TEVO_BW_PnP_BOM.xlsx")

# parts the model does not draw: (system, item, qty, source / note)
EXTRA_BUY = [
    ("vacuum", "Diaphragm vacuum pump, 12 or 24 V (= printer PSU, check in WP0), >= -60 kPa, ~4-6 l/min", 1,
     "TS 7.4: -60 kPa in the nozzle line in < 100 ms"),
    ("vacuum", "Solenoid valve 2/2 normally closed, 12 or 24 V, M5 or 1/8\", small (pick + blow)", 2, "TS 7.4"),
    ("vacuum", "Vacuum switch, adjustable, set to about -40 kPa, NO/NC contact", 1, "TS 7.4, FR-8; to an endstop input"),
    ("vacuum", "Inline vacuum filter 10 um, 4 mm push-in", 1, "TS 7.4: between nozzle and valves"),
    ("vacuum", "Needle valve or orifice, 4 mm push-in (blow puff 10-30 kPa / line decay leak)", 1, "TS 7.4"),
    ("vacuum", "PU tube 4 mm OD / 2.5 mm ID, 3 m", 1, "TS 7.3: one run valve block -> swivel, service loop"),
    ("vacuum", "Push-in fittings 4 mm: 2 tees, 4 straight M5/1/8\", 2 elbows", 1, "set"),
    ("vacuum", "Muffler for the pump exhaust", 1, "TS 7.4"),
    ("electrical", "Flyback diode 1N4007 (one per valve coil)", 2, "TS 8.2"),
    ("electrical", "Pump switch + inline fuse holder and fuse", 1, "TS 8.2: pump on a manual fused switch"),
    ("electrical", "E-stop mushroom switch, NC, rated for the motor + valve supply", 1, "TS 10"),
    ("cameras", "USB 2.0 cable, high-flex (drag chain), 2 m, to the down camera", 1, "TS 8.4: cameras on the PC"),
    ("cameras", "USB 2.0 cable 1.5 m, to the up camera", 1, "TS 8.4"),
    ("feeder bank", "Arduino Nano (ATmega328P, CH340 or FT232)", 1, "feeder/ELECTRONICS.md"),
    ("feeder bank", "Nano IO shield (GVS header on every pin, external power terminal)", 1, "feeder/ELECTRONICS.md"),
    ("feeder bank", "5 V 4 A supply (e.g. Mean Well LRS-35-5) or 24->5 V 5 A buck module", 1,
     "feeder/ELECTRONICS.md"),
    ("feeder bank", "Electrolytic capacitor 1000 uF / 10 V", 1, "feeder/ELECTRONICS.md"),
    ("feeder bank", "Servo extension cable 3-pin, 300 mm", 8, "feeder/ELECTRONICS.md"),
    ("feeder bank", "USB cable for the Nano (mini or micro, to match)", 1, "feeder/ELECTRONICS.md"),
    ("consumables", "Thread locker, medium strength", 1, "FR-23: camera focus and screws"),
]

NOTES = {
    "Camera board OV9281": "Global shutter required (FR-20). OV9732 boards are rolling shutter and are not "
                           "accepted. Check the board's M2 hole spacing: the model assumes a 32 mm square.",
    "M12 lens f = 10 mm": "Down camera, sensor 70 mm above the PCB. 8 mm gives ~26 mm FOV, 12 mm ~14 mm.",
    "M12 lens f = 6 mm": "Up camera, part 46 mm above the sensor. Fits SOIC-16 with margin.",
}

ARIAL = "Arial"
HEAD_FILL = PatternFill("solid", start_color="1F3A5F")
INPUT_FILL = PatternFill("solid", start_color="FFFF00")
BAND_FILL = PatternFill("solid", start_color="EEF2F7")
THIN = Side(style="thin", color="C8CED8")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def read_model_bom():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    for r in rows:
        r["qty"] = int(float(r["qty"]))
        r["mass_g_total"] = float(r["mass_g_total"] or 0)
    return rows


def note_for(item):
    for k, v in NOTES.items():
        if item.startswith(k):
            return v
    return ""


def style_header(ws, row, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(name=ARIAL, bold=True, color="FFFFFF")
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        cell.border = BORDER


def body_font(cell, bold=False, color="000000"):
    cell.font = Font(name=ARIAL, bold=bold, color=color)
    cell.border = BORDER
    cell.alignment = Alignment(vertical="top", wrap_text=True)


def priced_sheet(wb, title, intro, rows, widths):
    """rows: [(system, item, qty, note)] -> columns System, Item, Qty, Unit price, Line total, Note."""
    ws = wb.create_sheet(title)
    ws["A1"] = title
    ws["A1"].font = Font(name=ARIAL, bold=True, size=14)
    ws["A2"] = intro
    ws["A2"].font = Font(name=ARIAL, italic=True, color="555555")
    hdr = ["System", "Item", "Qty", "Unit price", "Line total", "Note"]
    for i, h in enumerate(hdr, 1):
        ws.cell(row=4, column=i, value=h)
    style_header(ws, 4, len(hdr))
    r = 5
    for k, (system, item, qty, note) in enumerate(rows):
        vals = [system, item, qty, None, "=C%d*D%d" % (r, r), note]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v)
            body_font(cell, color="0000FF" if c == 3 else "000000")
            if k % 2:
                cell.fill = BAND_FILL
        ws.cell(row=r, column=4).fill = INPUT_FILL
        ws.cell(row=r, column=4).number_format = "#,##0.00"
        ws.cell(row=r, column=5).number_format = "#,##0.00;-#,##0.00;-"
        r += 1
    ws.cell(row=r, column=2, value="Total")
    ws.cell(row=r, column=5, value="=SUM(E5:E%d)" % (r - 1))
    for c in (2, 5):
        body_font(ws.cell(row=r, column=c), bold=True)
    ws.cell(row=r, column=5).number_format = "#,##0.00"
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A5"
    return ws, r


def main():
    model = read_model_bom()
    by_kind = {}
    for row in model:
        by_kind.setdefault(row["kind"], []).append(row)

    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"

    buy = [(r["systems"], r["item"], r["qty"], note_for(r["item"]) or r["note"]) for r in by_kind.get("buy", [])]
    buy += [(s, i, q, "not in the CAD model - " + n) for s, i, q, n in EXTRA_BUY]
    buy.sort(key=lambda t: (t[0], t[1]))
    ws_buy, tot_buy = priced_sheet(wb, "Buy", "Purchased parts for one machine with 8 feeder lanes. Enter unit prices "
                                   "in the yellow cells (your currency); totals update.", buy, [14, 70, 7, 12, 13, 60])
    for r in range(5, tot_buy):
        if ws_buy.cell(row=r, column=2).value.startswith("Camera board"):
            ws_buy.cell(row=r, column=2).comment = Comment(
                "OV9281: 1/4\" mono global shutter, 1280x800, 3 um pixels. Same optics as OV9732, but no rolling "
                "shutter. AR0144 (colour, global shutter, 1280x800) is an equivalent alternative.", "BOM")

    make = [(r["systems"], r["item"], r["qty"], r["note"]) for r in by_kind.get("make", [])]
    ws_make, tot_make = priced_sheet(wb, "Make", "Machined and laser-cut parts. STEP files: out/parts_step/ (machine), "
                                     "feeder/out/step/ (cover plate + flat DXF).", make, [14, 70, 7, 12, 13, 50])

    fast = [(r["systems"], r["item"], r["qty"], r["note"]) for r in by_kind.get("fastener", [])]
    ws_fast, tot_fast = priced_sheet(wb, "Fasteners", "Screws, nuts, inserts. Buy about 10 % spare of the small "
                                     "sizes.", fast, [14, 60, 7, 12, 13, 40])

    # printed parts: grams from the model (infill applied), no prices
    ws = wb.create_sheet("Print")
    ws["A1"] = "Print"
    ws["A1"].font = Font(name=ARIAL, bold=True, size=14)
    ws["A2"] = ("3D-printed parts. OrcaSlicer projects: out/TEVO_BW_PnP_machine_parts.3mf and "
                "feeder/out/TBW_Feeder_v3.0.3mf (one lane; print the lane plates 8 times).")
    ws["A2"].font = Font(name=ARIAL, italic=True, color="555555")
    for i, h in enumerate(["System", "Part", "Qty", "Material", "Mass total (g)", "Note"], 1):
        ws.cell(row=4, column=i, value=h)
    style_header(ws, 4, 6)
    r = 5
    for k, row in enumerate(sorted(by_kind.get("print", []), key=lambda x: (x["systems"], x["item"]))):
        mat = "TPU 95A" if "TPU" in row["item"] else "PETG"
        vals = [row["systems"], row["item"], row["qty"], mat, round(row["mass_g_total"], 1), row["note"]]
        for c, v in enumerate(vals, 1):
            cell = ws.cell(row=r, column=c, value=v)
            body_font(cell, color="0000FF" if c in (3, 5) else "000000")
            if k % 2:
                cell.fill = BAND_FILL
        ws.cell(row=r, column=5).number_format = "#,##0.0"
        r += 1
    last_print = r - 1
    ws.cell(row=r, column=2, value="Total PETG (g)")
    ws.cell(row=r, column=5, value='=SUMIF(D5:D%d,"PETG",E5:E%d)' % (last_print, last_print))
    ws.cell(row=r + 1, column=2, value="Total TPU (g)")
    ws.cell(row=r + 1, column=5, value='=SUMIF(D5:D%d,"TPU 95A",E5:E%d)' % (last_print, last_print))
    for rr in (r, r + 1):
        for c in (2, 5):
            body_font(ws.cell(row=rr, column=c), bold=True)
        ws.cell(row=rr, column=5).number_format = "#,##0"
    ws.cell(row=r, column=6, value="Model mass at 40 % infill; the slicer's estimate is the better number "
                                   "(machine plates ~1.24 kg).")
    body_font(ws.cell(row=r, column=6))
    print_petg, print_tpu = r, r + 1
    for i, w in enumerate([14, 70, 7, 10, 15, 50], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A5"

    # stock parts reused from the printer
    ws_s = wb.create_sheet("Reused")
    ws_s["A1"] = "Reused from the Tevo Black Widow"
    ws_s["A1"].font = Font(name=ARIAL, bold=True, size=14)
    for i, h in enumerate(["System", "Part", "Qty"], 1):
        ws_s.cell(row=3, column=i, value=h)
    style_header(ws_s, 3, 3)
    r = 4
    for row in by_kind.get("stock", []):
        for c, v in enumerate([row["systems"], row["item"], row["qty"]], 1):
            body_font(ws_s.cell(row=r, column=c, value=v))
        r += 1
    for i, w in enumerate([14, 70, 7], 1):
        ws_s.column_dimensions[get_column_letter(i)].width = w

    # summary
    s = summary
    s["A1"] = "TEVO-BW pick and place - bill of materials"
    s["A1"].font = Font(name=ARIAL, bold=True, size=16)
    s["A2"] = "One machine with 8 TBW-Feeder v3.0 lanes and one feeder bank. Generated by make_bom.py from the model."
    s["A2"].font = Font(name=ARIAL, italic=True, color="555555")
    for i, h in enumerate(["Sheet", "Lines", "Total cost", "Note"], 1):
        s.cell(row=4, column=i, value=h)
    style_header(s, 4, 4)
    lines = [("Buy", "=COUNTA(Buy!B5:B%d)" % (tot_buy - 1), "=Buy!E%d" % tot_buy, "purchased parts"),
             ("Make", "=COUNTA(Make!B5:B%d)" % (tot_make - 1), "=Make!E%d" % tot_make, "quote from a CNC / laser shop"),
             ("Fasteners", "=COUNTA(Fasteners!B5:B%d)" % (tot_fast - 1), "=Fasteners!E%d" % tot_fast, "")]
    r = 5
    for name, n, tot, note in lines:
        for c, v in enumerate([name, n, tot, note], 1):
            cell = s.cell(row=r, column=c, value=v)
            body_font(cell, color="008000" if c in (2, 3) else "000000")
        s.cell(row=r, column=3).number_format = "#,##0.00"
        r += 1
    s.cell(row=r, column=1, value="Total")
    s.cell(row=r, column=3, value="=SUM(C5:C%d)" % (r - 1))
    for c in (1, 3):
        body_font(s.cell(row=r, column=c), bold=True)
    s.cell(row=r, column=3).number_format = "#,##0.00"
    r += 2
    s.cell(row=r, column=1, value="Filament PETG (g)")
    s.cell(row=r, column=3, value="=Print!E%d" % print_petg)
    s.cell(row=r + 1, column=1, value="Filament TPU (g)")
    s.cell(row=r + 1, column=3, value="=Print!E%d" % print_tpu)
    for rr in (r, r + 1):
        body_font(s.cell(row=rr, column=1))
        body_font(s.cell(row=rr, column=3), color="008000")
        s.cell(row=rr, column=3).number_format = "#,##0"
    r += 3
    legend = [
        ("How to use", True),
        ("Yellow cells (Unit price on Buy, Make, Fasteners) are the only inputs: enter the price per piece in "
         "your currency, e.g. 2.50. Line totals and this summary update by themselves.", False),
        ("Blue numbers are quantities from the model; green numbers link to other sheets.", False),
        ("Rows marked 'not in the CAD model' come from the spec (TS 7.4, 8, 10) and feeder/ELECTRONICS.md.", False),
        ("Cameras: buy 2 x OV9281 global-shutter USB boards (not OV9732, which is rolling shutter), "
         "one M12 f = 10 mm lens (down) and one M12 f = 6 mm lens (up). Details in the Buy sheet notes.", False),
    ]
    for text, bold in legend:
        s.cell(row=r, column=1, value=text).font = Font(name=ARIAL, bold=bold)
        s.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        s.cell(row=r, column=1).alignment = Alignment(wrap_text=True, vertical="top")
        s.row_dimensions[r].height = 15 if bold else 30
        r += 1
    for i, w in enumerate([22, 10, 14, 60], 1):
        s.column_dimensions[get_column_letter(i)].width = w

    out = OUT
    try:
        wb.save(out)
    except PermissionError:                     # the workbook is open in Excel
        out = OUT.replace(".xlsx", "_new.xlsx")
        wb.save(out)
        print("NOTE: %s is open (locked); saved as %s" % (os.path.basename(OUT), os.path.basename(out)))
    print("wrote", out, "- buy %d, make %d, fasteners %d, print %d lines" % (
        tot_buy - 5, tot_make - 5, tot_fast - 5, last_print - 4))


if __name__ == "__main__":
    main()

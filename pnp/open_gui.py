"""Open out/pnp_machine.FCStd in the FreeCAD GUI with colours, and save the colours into the file.

    freecad.exe open_gui.py        (or: pnp gui)

PNP_FCSTD selects another file (e.g. feeder/out/tbw_feeder_lane.FCStd). PNP_COLORS = parts (default: one colour
per distinct part) or kind (printed parts orange, as in the renders).
"""
import os

import FreeCAD as App
import FreeCADGui as Gui

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
PATH = os.environ.get("PNP_FCSTD", os.path.join(HERE, "out", "pnp_machine.FCStd"))
PROP = "PnpColor" if os.environ.get("PNP_COLORS", "parts") == "kind" else "PartColor"

doc = App.openDocument(PATH)
for o in doc.Objects:
    vo = getattr(o, "ViewObject", None)
    if vo is None:
        continue
    try:
        o.Visibility = True
        vo.Visibility = True
    except Exception:
        pass
    src = PROP if hasattr(o, PROP) else "PnpColor"
    if not hasattr(o, src):
        continue
    c = tuple(getattr(o, src)[:3])
    try:
        vo.ShapeColor = c
    except Exception:
        pass
    try:
        vo.LineColor = (0.05, 0.05, 0.06)
        vo.PointColor = (0.05, 0.05, 0.06)
    except Exception:
        pass
doc.save()                       # colours are now stored in the FCStd (GuiDocument.xml)
Gui.activeDocument().activeView().viewIsometric()
Gui.SendMsgToActiveView("ViewFit")
App.Console.PrintMessage("PnP model opened with colours: %s\n" % PATH)

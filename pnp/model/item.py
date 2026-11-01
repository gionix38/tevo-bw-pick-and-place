"""Item: one solid in the machine model, with the metadata used by BOM, mass report, export and render."""
import params as P
from . import geom

# motion groups, outermost first. Each group inherits the motion of the ones before it.
MOVES = ("fixed", "bridge", "carriage", "zslide", "rotor")


class Item:
    def __init__(self, name, shape, color, system, move="fixed", mat=None, mass=None,
                 bom=None, qty=1, kind="part", printed=False, note="", check=True, fasteners=None):
        """
        name     unique object name (FreeCAD object label)
        shape    Part shape in frame coordinates at the reference pose (machine home)
        color    RGB 0..1
        system   subsystem label: frame, x_axis, y_axis, head, vacuum, table, feeders, magazine, ...
        move     motion group (see MOVES)
        mat      material key in geom.DENSITY, used when mass is None
        mass     mass override in g (purchased parts)
        bom      BOM line text; items with the same text are summed. None = not a BOM line
        qty      BOM quantity this item stands for
        kind     'stock' (reused), 'buy', 'make' (machined/plate), 'print' (3D printed)
        printed  export an STL for printing
        """
        self.name = name
        self.shape = shape
        self.color = color
        self.system = system
        self.move = move
        self.mat = mat
        self._mass = mass
        self.bom = bom
        self.qty = qty
        self.kind = kind
        self.printed = printed or kind == "print"
        self.note = note
        self.check = check   # include in interference checks
        self.fasteners = dict(fasteners or {})   # {'M3x10 SHCS': qty, ...}
        self.print_up = None
        self.teardrops = 0
        if self.kind == "print":
            # all printed parts are orange; holes get teardrops for the print orientation (printing.py)
            from . import printing
            self.color = geom.C_ORANGE
            self.shape, self.print_up, self.teardrops = printing.prepare(name, shape)

    @property
    def mass(self):
        if self._mass is not None:
            return self._mass
        if self.mat is None:
            return 0.0
        m = self.shape.Volume / 1000.0 * geom.DENSITY[self.mat]
        return m * P.PRINT_FILL if self.kind == "print" else m

    def __repr__(self):
        return "Item(%s, %s, %s)" % (self.name, self.system, self.move)

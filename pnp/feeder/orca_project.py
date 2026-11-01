"""Write an OrcaSlicer project (.3mf) with every printed feeder part, laid out on plates with per-part settings.

    python orca_project.py [template.3mf] [out.3mf]

The printer, process and filament settings come from a project saved by OrcaSlicer (the template, default: the
user's AD5M project in Documents, 0.4 mm nozzle). v3.0 prints in PETG only (build(add_tpu=True) still adds
Orca's TPU profile as filament 2 if a part needs it). Parts come from out/stl (run `feeder build` first). One
lane (first article) + the bank parts.
"""
import glob
import json
import os
import struct
import sys
import uuid
import zipfile
from xml.sax.saxutils import quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
STL = os.path.join(HERE, "out", "stl")
APP = os.path.join(os.environ.get("APPDATA", ""), "OrcaSlicer")
TPU_PROFILE = "Flashforge Generic TPU"
GAP = 6.0           # mm between parts on a plate
MARGIN = 10.0       # mm kept free at the bed edge

FINE = {"layer_height": "0.12", "sparse_infill_density": "100%", "wall_loops": "4"}
SOLID = {"sparse_infill_density": "100%", "wall_loops": "4"}
STRONG = {"wall_loops": "4", "sparse_infill_density": "40%", "sparse_infill_pattern": "gyroid"}
BANK = {"wall_loops": "3", "sparse_infill_density": "30%"}

# (plate name, [(stl, count, object settings, filament)]). v3.0: one material (PETG), one 0.4 mm nozzle, 0.20 mm
# layers everywhere, no supports; every part lies on the bed as exported.
PLATES = [
    ("Lane - main body (PETG 0.20, 4 walls, infill 40)", [("Body", 1, STRONG, 1)]),
    ("Lane - side plate, cover plate, yoke (PETG 0.20)", [("SidePlate", 1, STRONG, 1), ("CoverPlate", 1, SOLID, 1),
                                                         ("PinchYoke", 1, STRONG, 1)]),
    ("Lane - moving parts (PETG 0.20, solid)", [("Slider", 1, SOLID, 1), ("Pawl", 2, SOLID, 1), ("Rack", 1, SOLID, 1), ("Idler", 1, SOLID, 1),
                                                ("Pinion", 1, SOLID, 1), ("DriveRoller", 2, SOLID, 1),
                                                ("ServoGear", 1, SOLID, 1), ("PinchAxle", 1, SOLID, 1),
                                                ("GuideBar", 1, SOLID, 1)]),
    ("Test fit (optional) - HF0612 dummies, no clutch: for trial assembly only", [("TestFit_HF0612", 2, SOLID, 1)]),
    ("Bank - waste bin, rack side 1", [("Feeder_WasteBin", 1, {"sparse_infill_density": "20%"}, 1),
                                       ("ReelRack_Side", 1, dict(BANK, wall_loops="4"), 1)]),
    ("Bank - rack side 2, reel hubs", [("ReelRack_Side", 1, dict(BANK, wall_loops="4"), 1),
                                       ("ReelHub", 8, BANK, 1)]),
    ("Bank - exit chute, bin legs", [("Feeder_ExitChute", 1, BANK, 1),
                                     ("Feeder_WasteBinLeg", 2, {"sparse_infill_density": "20%"}, 1)]),
]

NO_COPY = {"name", "inherits", "from", "type", "version", "setting_id", "filament_id", "instantiation",
           "compatible_printers", "compatible_printers_condition", "compatible_prints",
           "compatible_prints_condition", "is_custom_defined", "filament_settings_id", "description"}


# ------------------------------------------------------------------ meshes
def read_stl(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[80:84])[0]
    if 84 + 50 * n != len(b):
        raise ValueError("binary STL expected: " + path)
    verts, index, tris = [], {}, []
    for i in range(n):
        v = struct.unpack("<12f", b[84 + 50 * i:84 + 50 * i + 48])
        t = []
        for j in (3, 6, 9):
            key = (round(v[j], 5), round(v[j + 1], 5), round(v[j + 2], 5))
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            t.append(index[key])
        if len(set(t)) == 3:
            tris.append(t)
    xs, ys, zs = zip(*verts)
    return verts, tris, (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


# ------------------------------------------------------------------ plates (OrcaSlicer PartPlateList layout)
def plate_cols(count):
    v = count ** 0.5
    r = round(v)
    return int(r + 1 if v > r else r)


def plate_origin(i, cols, w, d):
    return (i % cols) * w * 1.2, -(i // cols) * d * 1.2


def auto_plates(parts, w, d, prefix):
    """First-fit: [(stl, count, opts, filament)] -> plates [(name, items)], biggest parts first."""
    plates = []
    for part in sorted(parts, key=lambda p: -p[4]):
        name, count, opts, fil, _, sx, sy = part
        for k in range(count):
            for pl in plates:
                trial = pl + [(name, 1, opts, fil, sx, sy)]
                try:
                    pack([((it[0], i), it[4], it[5]) for i, it in enumerate(trial)], w, d)
                except ValueError:
                    continue
                pl.append(trial[-1])
                break
            else:
                plates.append([(name, 1, opts, fil, sx, sy)])
    out = []
    for i, pl in enumerate(plates):
        merged = {}
        for name, _, opts, fil, _, _ in pl:
            merged.setdefault(name, [name, 0, opts, fil])[1] += 1
        out.append(("%s %d" % (prefix, i + 1), [tuple(v) for v in merged.values()]))
    return out


def pack(items, w, d):
    """Shelf packing inside the bed (bed coordinates centred on 0). items: [(key, sx, sy)] -> {key: (cx, cy)}"""
    x0, y0 = -w / 2 + MARGIN, -d / 2 + MARGIN
    x1, y1 = w / 2 - MARGIN, d / 2 - MARGIN
    pos, x, y, shelf = {}, x0, y0, 0.0
    for key, sx, sy in sorted(items, key=lambda it: -it[2]):
        if x + sx > x1:
            x, y, shelf = x0, y + shelf + GAP, 0.0
        if y + sy > y1 or x + sx > x1:
            raise ValueError("does not fit on one plate: %s" % (key,))
        pos[key] = (x + sx / 2, y + sy / 2)
        x += sx + GAP
        shelf = max(shelf, sy)
    return pos


# ------------------------------------------------------------------ settings
def system_filament(name):
    found = {}
    for root, _, files in os.walk(os.path.join(APP, "system")):
        for f in files:
            if f.endswith(".json"):
                try:
                    d = json.load(open(os.path.join(root, f), encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if isinstance(d, dict) and d.get("name") and os.path.basename(root) == "filament":
                    found.setdefault(d["name"], d)

    def res(n):
        d = dict(found[n])
        base = res(d["inherits"]) if d.get("inherits") else {}
        base.update(d)
        return base
    return res(name)


def project_settings(template_cfg):
    cfg = json.loads(template_cfg)
    nf = len(cfg["filament_settings_id"])
    tpu = system_filament(TPU_PROFILE)
    for k, v in tpu.items():
        if k in NO_COPY or not isinstance(v, list) or k not in cfg or not isinstance(cfg[k], list):
            continue
        if len(cfg[k]) == nf and len(v) == 1:
            cfg[k] = cfg[k] + v
    cfg["filament_settings_id"] = cfg["filament_settings_id"] + [TPU_PROFILE]
    cfg["filament_colour"] = cfg.get("filament_colour", ["#FF8000"])[:nf] + ["#303030"]
    for k in ("inherits_group", "different_settings_to_system"):     # [process, filaments..., printer]
        if isinstance(cfg.get(k), list) and len(cfg[k]) == nf + 2:
            cfg[k] = cfg[k][:-1] + [TPU_PROFILE if k == "inherits_group" else ""] + cfg[k][-1:]
    n = nf + 1
    cfg["flush_volumes_matrix"] = ["0" if i == j else "280" for i in range(n) for j in range(n)]
    cfg["flush_volumes_vector"] = ["140"] * (2 * n)
    return cfg


# ------------------------------------------------------------------ 3MF
NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')


def object_model(oid, verts, tris):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<model unit="millimeter" xml:lang="en-US" %s>' % NS,
           ' <metadata name="BambuStudio:3mfVersion">1</metadata>', ' <resources>',
           '  <object id="%d" p:UUID="%s" type="model">' % (oid, uuid.uuid4()), '   <mesh>', '    <vertices>']
    out += ['     <vertex x="%.5f" y="%.5f" z="%.5f"/>' % v for v in verts]
    out += ['    </vertices>', '    <triangles>']
    out += ['     <triangle v1="%d" v2="%d" v3="%d"/>' % tuple(t) for t in tris]
    out += ['    </triangles>', '   </mesh>', '  </object>', ' </resources>', ' <build/>', '</model>', '']
    return "\n".join(out)


def build(template, out_path, plates=None, stl_dir=STL, title="TBW-Feeder v3.0 - one lane + bank parts",
          add_tpu=False):
    plates_in = PLATES if plates is None else plates
    zt = zipfile.ZipFile(template)
    raw = zt.read("Metadata/project_settings.config").decode("utf-8")
    cfg = project_settings(raw) if add_tpu else json.loads(raw)
    app = "OrcaSlicer"
    for line in zt.read("3D/3dmodel.model").decode("utf-8").splitlines():
        if 'name="Application"' in line:
            app = line.split(">")[1].split("<")[0]
    w = d = 220.0
    pa = cfg.get("printable_area")
    if pa:
        pts = [tuple(float(c) for c in p.split("x")) for p in pa]
        w = max(p[0] for p in pts) - min(p[0] for p in pts)
        d = max(p[1] for p in pts) - min(p[1] for p in pts)
    cols = plate_cols(len(plates_in))

    meshes = {}
    for _, items in plates_in:
        for name, *_ in items:
            if name not in meshes:
                meshes[name] = read_stl(os.path.join(stl_dir, name + ".stl"))

    objects, files, plates = [], {}, []
    oid = 0
    for pi, (pname, items) in enumerate(plates_in):
        boxes = []
        for name, count, opts, fil in items:
            bb = meshes[name][2]
            for k in range(count):
                boxes.append(((name, k), bb[3] - bb[0], bb[4] - bb[1]))
        pos = pack(boxes, w, d)
        ox, oy = plate_origin(pi, cols, w, d)
        inst = []
        for name, count, opts, fil in items:
            verts, tris, bb = meshes[name]
            for k in range(count):
                oid += 2
                cx, cy = pos[(name, k)]
                tx, ty = ox + cx, oy + cy                     # meshes are stored centred (as Orca writes them)
                tz = (bb[5] - bb[2]) / 2
                label = name + (" %d" % (k + 1) if count > 1 else "")
                fn = "3D/Objects/%s_%d.model" % (name, oid)
                c = ((bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, (bb[2] + bb[5]) / 2)
                files[fn] = object_model(oid - 1, [(v[0] - c[0], v[1] - c[1], v[2] - c[2]) for v in verts], tris)
                objects.append(dict(id=oid, mesh_id=oid - 1, file=fn, name=label, opts=opts, fil=fil,
                                    tx=tx, ty=ty, tz=tz, src=os.path.join(stl_dir, name + ".stl")))
                inst.append(oid)
        plates.append((pname, inst))

    model = ['<?xml version="1.0" encoding="UTF-8"?>', '<model unit="millimeter" xml:lang="en-US" %s>' % NS,
             ' <metadata name="Application">%s</metadata>' % app,
             ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
             ' <metadata name="Title">%s</metadata>' % title, ' <resources>']
    for o in objects:
        model += ['  <object id="%d" p:UUID="%s" type="model">' % (o["id"], uuid.uuid4()), '   <components>',
                  '    <component p:path="/%s" objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
                  % (o["file"], o["mesh_id"], uuid.uuid4()), '   </components>', '  </object>']
    model += [' </resources>', ' <build p:UUID="%s">' % uuid.uuid4()]
    for o in objects:
        model.append('  <item objectid="%d" p:UUID="%s" transform="1 0 0 0 1 0 0 0 1 %.4f %.4f %.4f" printable="1"/>'
                     % (o["id"], uuid.uuid4(), o["tx"], o["ty"], o["tz"]))
    model += [' </build>', '</model>', '']

    ms = ['<?xml version="1.0" encoding="UTF-8"?>', '<config>']
    for o in objects:
        ms.append('  <object id="%d">' % o["id"])
        ms.append('    <metadata key="name" value=%s/>' % quoteattr(o["name"]))
        ms.append('    <metadata key="extruder" value="%d"/>' % o["fil"])
        for k, v in o["opts"].items():
            ms.append('    <metadata key="%s" value=%s/>' % (k, quoteattr(v)))
        ms += ['    <part id="%d" subtype="normal_part">' % o["mesh_id"],
               '      <metadata key="name" value=%s/>' % quoteattr(o["name"]),
               '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
               '      <metadata key="source_file" value=%s/>' % quoteattr(o["src"]),
               '      <metadata key="source_object_id" value="0"/>',
               '      <metadata key="source_offset_x" value="0"/>', '      <metadata key="source_offset_y" value="0"/>',
               '      <metadata key="source_offset_z" value="%.4f"/>' % o["tz"],
               '      <metadata key="source_volume_id" value="0"/>',
               '      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" '
               'backwards_edges="0"/>', '    </part>', '  </object>']
    ident = 1000
    for pi, (pname, inst) in enumerate(plates):
        ms += ['  <plate>', '    <metadata key="plater_id" value="%d"/>' % (pi + 1),
               # any plate name makes the Orca CLI segfault (GUI-saved projects leave it empty): names are console-only
               '    <metadata key="plater_name" value=""/>',
               '    <metadata key="locked" value="false"/>',
               '    <metadata key="filament_map_mode" value="Auto For Flush"/>',
               '    <metadata key="filament_maps" value="%s"/>' % " ".join(["1"] * len(cfg["filament_settings_id"]))]
        for o in inst:
            ident += 1
            ms += ['    <model_instance>', '      <metadata key="object_id" value="%d"/>' % o,
                   '      <metadata key="instance_id" value="0"/>',
                   '      <metadata key="identify_id" value="%d"/>' % ident, '    </model_instance>']
        ms.append('  </plate>')
    ms += ['  <assemble>']
    for o in objects:
        ms.append('   <assemble_item object_id="%d" instance_id="0" transform="1 0 0 0 1 0 0 0 1 %.4f %.4f %.4f" '
                  'offset="0 0 0" />' % (o["id"], o["tx"], o["ty"], o["tz"]))
    ms += ['  </assemble>', '</config>', '']

    rels = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    rels += [' <Relationship Target="/%s" Id="rel-%d" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/'
             '3dmodel"/>' % (fn, i + 1) for i, fn in enumerate(files)]
    rels += ['</Relationships>', '']

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", zt.read("[Content_Types].xml"))
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships">\n <Relationship Target="/3D/3dmodel.model" '
                   'Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
                   '</Relationships>\n')
        z.writestr("3D/3dmodel.model", "\n".join(model))
        z.writestr("3D/_rels/3dmodel.model.rels", "\n".join(rels))
        for fn, txt in files.items():
            z.writestr(fn, txt)
        z.writestr("Metadata/project_settings.config", json.dumps(cfg, ensure_ascii=False, indent=4))
        z.writestr("Metadata/model_settings.config", "\n".join(ms))
        if "Metadata/slice_info.config" in zt.namelist():
            z.writestr("Metadata/slice_info.config", zt.read("Metadata/slice_info.config"))
    print("wrote", out_path, "-", len(objects), "objects on", len(plates), "plates")
    for pname, inst in plates:
        print("  %-45s %d parts" % (pname, len(inst)))


def default_template():
    docs = os.path.expanduser(r"~\Documents")
    c = sorted(glob.glob(os.path.join(docs, "**", "*.3mf"), recursive=True), key=os.path.getmtime, reverse=True)
    for p in c:
        try:
            cfg = json.loads(zipfile.ZipFile(p).read("Metadata/project_settings.config"))
        except (KeyError, ValueError, zipfile.BadZipFile):
            continue
        if "Adventurer 5M" in cfg.get("printer_model", ""):
            return p
    raise SystemExit("no AD5M project found in Documents; pass a template .3mf")


if __name__ == "__main__":
    tpl = sys.argv[1] if len(sys.argv) > 1 else default_template()
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "out", "TBW_Feeder_v3.0.3mf")
    build(tpl, out)

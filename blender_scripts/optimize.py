# Optimización para Quest: une las mallas estáticas (menos draw calls) y marca qué se hornea en el lightmap.
# Correr DESPUÉS de build_scene.py (idealmente con LOWPOLY = True).
import bpy, re

KEEP = re.compile(r"^(Wheel_Drum|Wheel_Lever_Pivot|Wheel_Bulb_.*|Wheel_Display|Wheel_Topper.*|Mole_\d+|Mallet_\d|Ball_\d|"
                  r"Gun_\d|Target_\d|Can_\d|Prize_.*|Nevera_Bisagra|Nevera_Lata_.*|Screen_\d|Scoreboard|Scoreboard_Big|"
                  r"Basket_Display|Mole_Display|Tragaticket_Pantalla|Hoop_Trigger|Basket_Aro|Mostrador_Tope|FLOOR|S_.*|"
                  r"Topo_Torre|Basket_Red_.*|Basket_Bandeja.*|Tiro_Repisa_Latas|REF_.*|Camera|XR_Rig_Origen|GameManager)$")

def kept(o):
    while o:
        if KEEP.match(o.name): return True
        o = o.parent
    return False

def kind(o):
    names = [m.name for m in o.data.materials if m]
    if any(n == "Vidrio" for n in names): return "vidrio"
    if names and all(n.startswith(("Neon_", "Bombillo", "Display_LED")) for n in names): return "neon"
    return "solido"

groups = {}
for o in list(bpy.data.objects):
    if o.type != "MESH" or kept(o) or o.children: continue
    key = (o.parent.name if o.parent else "", kind(o))
    groups.setdefault(key, []).append(o)

joined = []
for (parent, k), objs in groups.items():
    if len(objs) == 1:
        joined.append((objs[0], k)); continue
    act = objs[0]
    with bpy.context.temp_override(active_object=act, object=act, selected_objects=objs, selected_editable_objects=objs):
        bpy.ops.object.join()
    act.name = f"{parent or 'Escena'}_{k}_unido"
    joined.append((act, k))

# piezas móviles hechas de varias partes (topos, premios, pistolas, dianas, mazos): una sola malla por pieza
for rname in [o.name for o in bpy.data.objects]:
    root = bpy.data.objects.get(rname)
    if root is None or root.type != "EMPTY" or not re.match(r"^(Mole_\d+|Prize_.*|Gun_\d|Target_\d|Mallet_\d)$", root.name): continue
    parts = [c for c in root.children if c.type == "MESH" and not c.children]
    if len(parts) < 2: continue
    act = parts[0]
    with bpy.context.temp_override(active_object=act, object=act, selected_objects=parts, selected_editable_objects=parts):
        bpy.ops.object.join()
    act.name = root.name + "_malla"

def set_lm(o, v):
    try: o.NEEDLE_isLightmapped = v
    except Exception: o["NEEDLE_isLightmapped"] = v

# qué se hornea: lo estático y sólido (sí), lo que se mueve, neones y vidrio (no)
for o in bpy.data.objects:
    if o.type == "MESH":
        static_solid = (not kept(o) and kind(o) == "solido") or o.name == "FLOOR" or (o.name.startswith("S_") and kind(o) == "solido")
        set_lm(o, bool(static_solid))
    elif o.type == "LIGHT":
        set_lm(o, True)   # las luces quedan horneadas: no cuestan en tiempo real

meshes = [o for o in bpy.data.objects if o.type == "MESH" and not o.name.startswith("REF_")]
dg = bpy.context.evaluated_depsgraph_get()
tris = sum(sum(len(p.vertices) - 2 for p in o.evaluated_get(dg).data.polygons) for o in meshes)
dc = sum(max(1, len([m for m in o.data.materials if m])) for o in meshes)
RESUMEN = dict(mallas=len(meshes), triangulos=tris, drawcalls_aprox=dc,
               horneados=sum(1 for o in meshes if getattr(o, "NEEDLE_isLightmapped", o.get("NEEDLE_isLightmapped", False))))
print("OPTIMIZADO:", RESUMEN)

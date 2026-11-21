# Parte las mallas grandes de la escena en zonas (3 x 2) para que three.js no dibuje lo que queda fuera de la vista
# (frustum culling: es automático por objeto, pero una sola malla que ocupa todo el cuarto nunca se puede descartar).
# Conserva UVs, materiales y los datos del lightmap, así que no hay que volver a hornear.
import bpy, bmesh

COLS = [(-99, -2.0, "izq"), (-2.0, 2.0, "centro"), (2.0, 99, "der")]
ROWS = [(-99, 0.0, "frente"), (0.0, 99, "fondo")]

def split(obj):
    pieces = []
    mw = obj.matrix_world
    for (x0, x1, cn) in COLS:
        for (y0, y1, rn) in ROWS:
            me = obj.data
            sel = [p.index for p in me.polygons if x0 <= (mw @ p.center).x < x1 and y0 <= (mw @ p.center).y < y1]
            if not sel or len(sel) == len(me.polygons):
                continue
            bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
            keep = set(sel)
            # nueva malla con las caras de la zona
            new_bm = bm.copy(); new_bm.faces.ensure_lookup_table()
            bmesh.ops.delete(new_bm, geom=[f for f in new_bm.faces if f.index not in keep], context="FACES")
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in keep], context="FACES")
            nme = me.copy(); new_bm.to_mesh(nme); new_bm.free()
            bm.to_mesh(me); bm.free()
            no = obj.copy(); no.data = nme; no.name = f"{obj.name}_{cn}_{rn}"
            for c in obj.users_collection: c.objects.link(no)
            pieces.append(no)
    return pieces

made = []
for o in [o for o in bpy.data.objects if o.type == "MESH" and o.parent is None and o.name.startswith("Escena_") and o.name.endswith("_unido")]:
    made += split(o)
RESUMEN = {"piezas": [(p.name, len(p.data.polygons)) for p in made]}
print(RESUMEN)

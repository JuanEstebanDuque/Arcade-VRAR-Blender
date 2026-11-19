# Renders de revisión (no afectan la escena). Uso: exec(...) con VIEWS definido o por defecto.
import bpy, math, os
from mathutils import Vector
sc = bpy.context.scene
out = os.path.join(os.path.dirname(bpy.data.filepath), "renders")
os.makedirs(out, exist_ok=True)
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 75
try: sc.eevee.taa_render_samples = 16
except Exception: pass
DEFAULT = {
    "v_entrada": ((0, -4.6, 1.65), (0, 1.0, 1.5), 16),
    "v_maquinitas": ((0.2, 2.0, 1.6), (-1.5, 4.5, 1.4), 20),
    "v_rueda": ((0.6, -1.4, 1.7), (0, 1.0, 1.7), 22),
    "v_tiro": ((-2.4, 1.0, 1.6), (-5.5, 2.4, 1.4), 18),
    "v_basket": ((2.5, 1.2, 1.7), (5.5, 2.6, 1.6), 18),
    "v_topo": ((3.9, -1.0, 1.7), (5.3, -2.0, 0.9), 22),
    "v_premios": ((-3.4, -2.2, 1.5), (-5.6, -3.0, 1.2), 20),
}
views = globals().get("VIEWS") or DEFAULT
cd = bpy.data.cameras.new("PrevCam"); pc = bpy.data.objects.new("REF_PrevCam", cd); sc.collection.objects.link(pc)
old = sc.camera; sc.camera = pc
done = []
for name, (pos, tgt, lens) in views.items():
    pc.location = pos; cd.lens = lens
    pc.rotation_euler = (Vector(tgt) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, name + ".png")
    bpy.ops.render.render(write_still=True); done.append(name)
sc.camera = old
bpy.data.objects.remove(pc); bpy.data.cameras.remove(cd)

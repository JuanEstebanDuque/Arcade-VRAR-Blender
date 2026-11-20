# Importa los assets externos (MakerLab, imagen -> 3D) y los deja listos: una sola malla, centrada, con tamaño real.
import bpy, os, math
from mathutils import Vector

BASE = os.path.dirname(bpy.data.filepath)
EXT = os.path.join(BASE, "assets_externos")
# nombre del premio a reemplazar, archivo, tamaño objetivo (lado más largo, en metros, ANTES de la escala 1.35 del premio)
ASSETS = {
    "Rubik":  {"file": "rubikCube.glb", "prize_old": "Prize_80_Yoyo", "prize_new": "Prize_80_Rubik", "size": 0.12},
    "Trofeo": {"file": "Trophey.glb",  "prize_old": "Prize_1000_Trofeo", "prize_new": "Prize_1000_Trofeo", "size": 0.2},
}

def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

def import_asset(key):
    a = ASSETS[key]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(EXT, a["file"]))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    # aplicar transformaciones y unir en una sola malla
    for o in meshes:
        mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
    act = meshes[0]
    if len(meshes) > 1:
        with bpy.context.temp_override(active_object=act, object=act, selected_objects=meshes, selected_editable_objects=meshes):
            bpy.ops.object.join()
    for o in new:
        if o.name in bpy.data.objects and o != act and o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    me = act.data
    me.transform(act.matrix_world); act.matrix_world.identity()
    # centrar (base en z=0) y escalar al tamaño objetivo
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    size = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    s = a["size"] / size
    c = Vector(((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, min(zs)))
    for v in me.vertices: v.co = (v.co - c) * s
    me.update()
    act.name = f"EXT_{key}_original"
    return act

def place_in_prize(obj, key, scene_prize_scale=True):
    """Pone la malla dentro del premio (reemplaza las piezas viejas) y renombra el premio si hace falta."""
    a = ASSETS[key]
    p = bpy.data.objects.get(a["prize_old"]) or bpy.data.objects.get(a["prize_new"])
    for ch in list(p.children_recursive):
        if ch.type == "MESH": bpy.data.objects.remove(ch, do_unlink=True)
    for c in obj.users_collection: c.objects.unlink(obj)
    for c in p.users_collection: c.objects.link(obj)
    obj.parent = p; obj.matrix_parent_inverse.identity()
    obj.location = (0, 0, 0); obj.rotation_euler = (0, 0, math.radians(25 if key == "Rubik" else 0)); obj.scale = (1, 1, 1)
    p.name = a["prize_new"]
    return p

# ---------------- optimización y horneado ----------------
TEX = os.path.join(BASE, "textures")

def make_low(hi, target_tris):
    lo = hi.copy(); lo.data = hi.data.copy(); lo.name = hi.name.replace("_original", "_lowpoly")
    for c in hi.users_collection: c.objects.link(lo)
    ratio = max(0.0005, target_tris / max(1, tris(hi)))
    m = lo.modifiers.new("Decimate", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = ratio
    dg = bpy.context.evaluated_depsgraph_get()
    newme = bpy.data.meshes.new_from_object(lo.evaluated_get(dg))
    lo.modifiers.clear(); old = lo.data; lo.data = newme; bpy.data.meshes.remove(old)
    for p in lo.data.polygons: p.use_smooth = True
    return lo

def unwrap(lo):
    bpy.context.view_layer.objects.active = lo
    for o in bpy.context.selected_objects: o.select_set(False)
    lo.select_set(True)
    uv = lo.data.uv_layers.new(name="UV_Horneado"); lo.data.uv_layers.active = uv
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01)
    bpy.ops.object.mode_set(mode="OBJECT")
    # dejar solo el UV nuevo
    for l in list(lo.data.uv_layers):
        if l.name != "UV_Horneado": lo.data.uv_layers.remove(l)

def bake(hi, lo, key, res=1024):
    sc = bpy.context.scene
    old_engine = sc.render.engine
    sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"; sc.cycles.samples = 16
    imgs = {}
    for kind in ("color", "normal"):
        im = bpy.data.images.new(f"ext_{key.lower()}_{kind}", res, res, alpha=False)
        if kind == "normal": im.colorspace_settings.name = "Non-Color"
        imgs[kind] = im
    mat = bpy.data.materials.new(f"EXT_{key}_Horneado"); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
    lo.data.materials.clear(); lo.data.materials.append(mat)
    tex = {}
    for i, kind in enumerate(("color", "normal")):
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = imgs[kind]; n.location = (-600, 300 - i * 300); tex[kind] = n
    for o in bpy.context.selected_objects: o.select_set(False)
    hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    ext = max(lo.dimensions) * 0.02
    for kind, btype in (("color", "DIFFUSE"), ("normal", "NORMAL")):
        nt.nodes.active = tex[kind]
        kw = dict(type=btype, use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=0.0, margin=8)
        if btype == "DIFFUSE": kw["pass_filter"] = {"COLOR"}
        bpy.ops.object.bake(**kw)
        p = os.path.join(TEX, f"ext_{key.lower()}_{kind}.png")
        imgs[kind].filepath_raw = p; imgs[kind].file_format = "PNG"; imgs[kind].save()
    # material final: color + mapa de normales
    nt.links.new(tex["color"].outputs["Color"], bsdf.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-250, -150)
    nt.links.new(tex["normal"].outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    hb = hi.data.materials[0].node_tree.nodes.get("Principled BSDF") if hi.data.materials and hi.data.materials[0].use_nodes else None
    bsdf.inputs["Roughness"].default_value = hb.inputs["Roughness"].default_value if hb else 0.5
    bsdf.inputs["Metallic"].default_value = (hb.inputs["Metallic"].default_value if hb else 0.0)
    if key == "Trofeo": bsdf.inputs["Metallic"].default_value = 0.6; bsdf.inputs["Roughness"].default_value = 0.35
    sc.render.engine = old_engine
    return imgs

def rebake_keep_uv(key, target_tris, res=1024):
    """Versión para objetos con bordes y ranuras (cubo): conserva los UV y la textura de color originales
    (solo reducida a 1024 px) y hornea únicamente el mapa de normales. Así el color no se ensucia."""
    hi = import_asset(key)
    lo = make_low(hi, target_tris)
    src_img = None
    for n in hi.data.materials[0].node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image: src_img = n.image; break
    col = src_img.copy(); col.name = f"ext_{key.lower()}_color"; col.scale(res, res)
    col.filepath_raw = os.path.join(TEX, f"ext_{key.lower()}_color.png"); col.file_format = "PNG"; col.save()
    nrm = bpy.data.images.new(f"ext_{key.lower()}_normal", res, res, alpha=False); nrm.colorspace_settings.name = "Non-Color"
    mat = bpy.data.materials.new(f"EXT_{key}_Horneado"); mat.use_nodes = True
    nt = mat.node_tree; bsdf = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexImage"); tc.image = col; tc.location = (-600, 300)
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = nrm; tn.location = (-600, 0)
    lo.data.materials.clear(); lo.data.materials.append(mat)
    sc = bpy.context.scene; old = sc.render.engine
    sc.render.engine = "CYCLES"; sc.cycles.device = "GPU"; sc.cycles.samples = 16
    for o in bpy.context.selected_objects: o.select_set(False)
    hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
    nt.nodes.active = tn
    ext = max(lo.dimensions) * 0.02
    bpy.ops.object.bake(type="NORMAL", use_selected_to_active=True, cage_extrusion=ext, max_ray_distance=0.0, margin=16)
    nrm.filepath_raw = os.path.join(TEX, f"ext_{key.lower()}_normal.png"); nrm.file_format = "PNG"; nrm.save()
    sc.render.engine = old
    nt.links.new(tc.outputs["Color"], bsdf.inputs["Base Color"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-250, -150); nm.inputs["Strength"].default_value = 0.6
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.35
    return hi, lo

# Utilidades de modelado para la escena del arcade (se ejecuta dentro de Blender).
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Euler

PROJECT = os.path.dirname(bpy.data.filepath)
TEX = os.path.join(PROJECT, "textures")
R = math.radians

# ---------------- colecciones ----------------
def coll(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    p = parent or bpy.context.scene.collection
    if c.name not in [x.name for x in p.children]: p.children.link(c)
    return c

def link(o, col, parent=None, loc=None, rot=None):
    col.objects.link(o)
    if loc is not None: o.location = loc
    if rot is not None: o.rotation_euler = [R(a) for a in rot]
    if parent is not None: o.parent = parent
    return o

def empty(name, loc, col, rot=(0, 0, 0), parent=None, size=0.2):
    o = bpy.data.objects.new(name, None); o.empty_display_size = size
    return link(o, col, parent, loc, rot)

# ---------------- materiales ----------------
def _bsdf(m):
    m.use_nodes = True
    return m.node_tree.nodes.get("Principled BSDF")

def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    b = _bsdf(m)
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit is not None:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

_imgcache = {}
def img(file):
    if file in _imgcache: return _imgcache[file]
    path = os.path.join(TEX, file)
    im = bpy.data.images.load(path, check_existing=True)
    _imgcache[file] = im
    return im

def mat_img(name, file, rough=0.6, metal=0.0, emissive=0.0, alpha_clip=False, tint=None):
    """Material con textura. emissive>0 hace que la imagen brille (pantallas, letreros)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name)
    b = _bsdf(m); nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(file); t.location = (-500, 200)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emissive > 0:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emissive
    if alpha_clip:
        g = nt.nodes.new("ShaderNodeMath"); g.operation = "GREATER_THAN"; g.inputs[1].default_value = 0.5
        nt.links.new(t.outputs["Alpha"], g.inputs[0]); nt.links.new(g.outputs[0], b.inputs["Alpha"])
        try: m.surface_render_method = "DITHERED"
        except Exception: pass
    return m

# ---------------- mallas ----------------
def _finish(name, bm, mats, col, loc, rot, parent):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    return link(o, col, parent, loc, rot)

def _box_uv(bm, size, tile):
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for l in f.loops:
            co = l.vert.co
            if tile:
                u, v = co[a] / tile, co[b] / tile
            else:
                u = (co[a] / size[a]) + 0.5 if size[a] else 0
                v = (co[b] / size[b]) + 0.5 if size[b] else 0
                # que la imagen se lea derecha en las caras -X/+Y
                if (ax == 0 and n[0] < 0) or (ax == 1 and n[1] > 0): u = 1 - u
            l[uv].uv = (u, v)

def box(name, size, loc, m, col, rot=(0, 0, 0), parent=None, bevel=0.0, tile=None, face_mats=None):
    """Caja con UVs. bevel>0 redondea aristas. face_mats={'-y': mat, '+x': mat...} asigna materiales por cara."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    mats = [m]
    if face_mats:
        keys = {"+x": (0, 1), "-x": (0, -1), "+y": (1, 1), "-y": (1, -1), "+z": (2, 1), "-z": (2, -1)}
        for k, fm in face_mats.items():
            if fm not in mats: mats.append(fm)
            ax, sg = keys[k]
            for f in bm.faces:
                if f.normal[ax] * sg > 0.9: f.material_index = mats.index(fm)
    _box_uv(bm, size, tile)
    if bevel > 0:
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bevel, segments=2, affect="EDGES", profile=0.5)
    return _finish(name, bm, mats, col, loc, rot, parent)

def plane(name, w, h, loc, m, col, rot=(90, 0, 0), parent=None):
    """Plano con UV 0-1. Con rot=(90,0,0) queda vertical mirando a -Y."""
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((-w/2, -h/2, 0), (w/2, -h/2, 0), (w/2, h/2, 0), (-w/2, h/2, 0))]
    f = bm.faces.new(v); uv = bm.loops.layers.uv.verify()
    for l, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): l[uv].uv = c
    return _finish(name, bm, [m], col, loc, rot, parent)

def cyl(name, r, depth, loc, m, col, rot=(0, 0, 0), verts=24, parent=None, r2=None, cap_mat=None, smooth=True):
    bm = bmesh.new(); bm.loops.layers.uv.verify()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r if r2 is None else r2, depth=depth, calc_uvs=True)
    mats = [m]
    if cap_mat:
        mats.append(cap_mat)
        for f in bm.faces:
            if abs(f.normal.z) > 0.9: f.material_index = 1
    if smooth:
        for f in bm.faces:
            if abs(f.normal.z) < 0.9: f.smooth = True
    return _finish(name, bm, mats, col, loc, rot, parent)

def sphere(name, r, loc, m, col, parent=None, seg=24, rings=12, scale=(1, 1, 1), rot=(0, 0, 0)):
    bm = bmesh.new(); bm.loops.layers.uv.verify()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=r, calc_uvs=True)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    for f in bm.faces: f.smooth = True
    return _finish(name, bm, [m], col, loc, rot, parent)

def torus(name, R1, r, loc, m, col, rot=(0, 0, 0), parent=None, seg=32, mseg=10, arc=360):
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    full = arc >= 360
    nU = seg if full else seg + 1
    rows = []
    for i in range(nU):
        a = R(arc) * i / seg
        row = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            p = Vector(((R1 + r * math.cos(b)) * math.cos(a), (R1 + r * math.cos(b)) * math.sin(a), r * math.sin(b)))
            row.append(bm.verts.new(p))
        rows.append(row)
    for i in range(seg):
        i2 = (i + 1) % nU if full else i + 1
        for j in range(mseg):
            j2 = (j + 1) % mseg
            f = bm.faces.new((rows[i][j], rows[i2][j], rows[i2][j2], rows[i][j2])); f.smooth = True
    return _finish(name, bm, [m], col, loc, rot, parent)

def tube(name, pts, r, m, col, parent=None, loc=(0, 0, 0), cyclic=False, rot=(0,0,0)):
    """Tubo (neón, barandas, cables) que sigue una lista de puntos."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, q in zip(sp.points, pts): p.co = (*q, 1)
    sp.use_cyclic_u = cyclic
    cu.bevel_depth = r; cu.bevel_resolution = 2; cu.use_fill_caps = True
    tmp = bpy.data.objects.new(name + "_tmp", cu); col.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get(); ev = tmp.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev); me.materials.clear(); me.materials.append(m)
    bpy.data.objects.remove(tmp, do_unlink=True); bpy.data.curves.remove(cu)
    o = bpy.data.objects.new(name, me)
    return link(o, col, parent, loc, rot)

def extrude_profile(name, prof, width, col, body_mat, side_mat, loc, parent=None, rot=(0, 0, 0), uv_box=(1.0, 2.0)):
    """Extruye un perfil (lista de (y,z)) a lo ancho en X. Las caras laterales llevan side_mat con UV del perfil."""
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify()
    L = [bm.verts.new((-width/2, y, z)) for y, z in prof]
    Rr = [bm.verts.new((width/2, y, z)) for y, z in prof]
    fl = bm.faces.new(L[::-1]); fr = bm.faces.new(Rr)
    n = len(prof); quads = []
    for i in range(n):
        j = (i + 1) % n
        quads.append(bm.faces.new((L[i], L[j], Rr[j], Rr[i])))
    bm.normal_update()
    ys = [p[0] for p in prof]; zs = [p[1] for p in prof]
    y0, y1, z0, z1 = min(ys), max(ys), min(zs), max(zs)
    for f, flip in ((fl, True), (fr, False)):
        f.material_index = 1
        for l in f.loops:
            u = (l.vert.co.y - y0) / (y1 - y0); v = (l.vert.co.z - z0) / (z1 - z0)
            l[uv].uv = (1 - u if flip else u, v)
    acc = 0
    for f in quads:
        for l in f.loops:
            l[uv].uv = (l.vert.co.x + 0.5, (l.vert.co.y + l.vert.co.z))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return _finish(name, bm, [body_mat, side_mat], col, loc, rot, parent)

def wire_from(o, thickness=0.006):
    """Convierte una malla en red de alambre (para redes del basket)."""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.wireframe(bm, faces=bm.faces[:], thickness=thickness, offset=0, use_replace=True, use_boundary=True)
    bm.to_mesh(me); bm.free()
    return o

def text_mesh(name, body, loc, size, m, col, rot=(90, 0, 0), extrude=0.01, parent=None, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = align; cu.align_y = "CENTER"
    tmp = bpy.data.objects.new(name + "_tmp", cu); col.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg)); me.materials.clear(); me.materials.append(m)
    bpy.data.objects.remove(tmp, do_unlink=True); bpy.data.curves.remove(cu)
    o = bpy.data.objects.new(name, me)
    return link(o, col, parent, loc, rot)

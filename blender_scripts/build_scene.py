# Construye la escena base del Arcade (bloqueo con medidas reales, 1 unidad = 1 m).
# Convenciones de nombres que lee el código (web/src/scripts):
#   S_*        -> colisionador estático (piso, paredes, mostradores)
#   FLOOR      -> piso teletransportable
#   REF_*      -> referencias que se ocultan en la web
#   Screen_*   -> pantallas animadas por shader
#   Scoreboard -> marcador de tickets
import bpy, math

# ---------- limpieza ----------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
for m in list(bpy.data.meshes):
    if m.users == 0: bpy.data.meshes.remove(m)
for m in list(bpy.data.materials):
    if m.users == 0: bpy.data.materials.remove(m)

scene = bpy.context.scene
root = scene.collection

def coll(name):
    c = bpy.data.collections.new(name)
    root.children.link(c)
    return c

# ---------- materiales ----------
def mat(name, color, rough=0.6, metal=0.0, emit=None, strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m

M = {
 "wall":   mat("Pared_Oscura", (0.035, 0.03, 0.06), 0.85),
 "floor":  mat("Alfombra_Cosmica", (0.03, 0.02, 0.05), 0.95),
 "ceil":   mat("Techo", (0.02, 0.02, 0.03), 0.9),
 "wood":   mat("Madera_Mostrador", (0.25, 0.12, 0.06), 0.55),
 "black":  mat("Plastico_Negro", (0.02, 0.02, 0.02), 0.4),
 "chrome": mat("Cromo", (0.8, 0.8, 0.85), 0.2, 1.0),
 "white":  mat("Blanco", (0.85, 0.85, 0.85), 0.5),
 "red":    mat("Rojo", (0.7, 0.04, 0.05), 0.45),
 "yellow": mat("Amarillo", (0.9, 0.7, 0.05), 0.45),
 "teal":   mat("Turquesa", (0.02, 0.45, 0.5), 0.45),
 "purple": mat("Morado", (0.25, 0.05, 0.45), 0.45),
 "orange": mat("Naranja", (0.9, 0.3, 0.02), 0.5),
 "n_pink": mat("Neon_Magenta", (1, 0.1, 0.7), 0.3, 0, (1, 0.05, 0.6), 6),
 "n_cyan": mat("Neon_Cian", (0.1, 0.9, 1), 0.3, 0, (0.05, 0.8, 1), 6),
 "n_yel":  mat("Neon_Amarillo", (1, 0.85, 0.2), 0.3, 0, (1, 0.8, 0.1), 5),
 "n_purp": mat("Neon_Morado", (0.6, 0.2, 1), 0.3, 0, (0.55, 0.15, 1), 5),
 "screen": mat("Pantalla_Base", (0.01, 0.01, 0.02), 0.2, 0, (0.1, 0.1, 0.2), 1),
 "glass":  mat("Vidrio_Nevera", (0.6, 0.8, 0.9), 0.05, 0, (0.4, 0.7, 0.9), 0.6),
 "ref":    mat("Referencia", (0.9, 0.3, 0.1), 0.8),
}

# ---------- primitivas ----------
def box(name, size, loc, m, col, rot=(0, 0, 0), parent=None):
    sx, sy, sz = [s / 2 for s in size]
    v = [(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),(-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)]
    f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f); me.update()
    me.materials.append(m)
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    if parent: o.parent = parent
    return o

def cyl(name, r, depth, loc, m, col, rot=(0, 0, 0), verts=24, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=(0,0,0))
    o = bpy.context.active_object
    o.name = name; o.data.name = name
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o)
    o.data.materials.append(m)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    if parent: o.parent = parent
    return o

def sphere(name, r, loc, m, col, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=r, location=(0,0,0))
    o = bpy.context.active_object
    o.name = name; o.data.name = name
    for c in o.users_collection: c.objects.unlink(o)
    col.objects.link(o)
    o.data.materials.append(m)
    o.location = loc
    bpy.ops.object.shade_smooth()
    if parent: o.parent = parent
    return o

def empty(name, loc, col, rot=(0,0,0), parent=None):
    o = bpy.data.objects.new(name, None)
    col.objects.link(o)
    o.location = loc
    o.rotation_euler = [math.radians(a) for a in rot]
    o.empty_display_size = 0.3
    if parent: o.parent = parent
    return o

def text(name, body, loc, size, m, col, rot=(90, 0, 0), extrude=0.01, align='CENTER'):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.size = size; cu.extrude = extrude
    cu.align_x = align; cu.align_y = 'CENTER'
    o = bpy.data.objects.new(name + "_tmp", cu)
    col.objects.link(o)
    cu.materials.append(m)
    # convertir a malla para que exporte bien
    me = o.to_mesh().copy()
    mo = bpy.data.objects.new(name, me)
    col.objects.link(mo)
    mo.location = loc; mo.rotation_euler = [math.radians(a) for a in rot]
    bpy.data.objects.remove(o, do_unlink=True)
    return mo

# ======================================================
W, D, H = 12.0, 10.0, 3.6          # ancho (x), fondo (y), alto (z)
x0, x1, y0, y1 = -W/2, W/2, -D/2, D/2

# ---------- arquitectura ----------
C = coll("01_Arquitectura")
fl = box("FLOOR", (W, D, 0.1), (0, 0, -0.05), M["floor"], C)
box("S_Pared_Fondo", (W, 0.2, H), (0, y1 + 0.1, H/2), M["wall"], C)
box("S_Pared_Frente", (W, 0.2, H), (0, y0 - 0.1, H/2), M["wall"], C)
box("S_Pared_Izq", (0.2, D, H), (x0 - 0.1, 0, H/2), M["wall"], C)
box("S_Pared_Der", (0.2, D, H), (x1 + 0.1, 0, H/2), M["wall"], C)
box("Techo", (W, D, 0.1), (0, 0, H + 0.05), M["ceil"], C)
# zócalos neón (línea baja alrededor del cuarto)
for n, (s, l, mm) in {
    "Neon_Zocalo_Fondo": ((W, 0.03, 0.04), (0, y1 - 0.02, 0.15), M["n_pink"]),
    "Neon_Zocalo_Izq":   ((0.03, D, 0.04), (x0 + 0.02, 0, 0.15), M["n_cyan"]),
    "Neon_Zocalo_Der":   ((0.03, D, 0.04), (x1 - 0.02, 0, 0.15), M["n_cyan"]),
    "Neon_Techo_Fondo":  ((W, 0.03, 0.04), (0, y1 - 0.02, H - 0.15), M["n_purp"]),
    "Neon_Techo_Izq":    ((0.03, D, 0.04), (x0 + 0.02, 0, H - 0.15), M["n_pink"]),
    "Neon_Techo_Der":    ((0.03, D, 0.04), (x1 - 0.02, 0, H - 0.15), M["n_pink"]),
}.items():
    box(n, s, l, mm, C)
# franjas neón del techo (tipo arcade)
for i, x in enumerate((-3, 0, 3)):
    box(f"Neon_Techo_Franja_{i}", (0.06, D - 1.5, 0.03), (x, 0, H - 0.02), M["n_cyan"] if i != 1 else M["n_pink"], C)
# puerta de entrada (decorativa) en pared del frente
box("Puerta_Marco", (1.8, 0.08, 2.3), (0, y0 + 0.02, 1.15), M["chrome"], C)
box("Puerta_Vidrio", (1.6, 0.04, 2.15), (0, y0 + 0.05, 1.1), M["glass"], C)
text("Letrero_Nombre", "PIXEL 84", (0, y0 + 0.08, 2.85), 0.55, M["n_pink"], C, rot=(90, 0, 180))

# ---------- referencia humana 1.70 m ----------
R = coll("00_Referencia")
cyl("REF_Humano_1.70m", 0.22, 1.70, (-2.2, -1.5, 0.85), M["ref"], R, verts=12)

# ---------- recepción (pared izquierda, adelante) ----------
C = coll("02_Recepcion")
box("S_Mostrador", (0.6, 3.2, 1.05), (-4.6, -3.0, 0.525), M["wood"], C)
box("Mostrador_Tope", (0.7, 3.3, 0.04), (-4.6, -3.0, 1.07), M["black"], C)
box("Mostrador_Neon", (0.02, 3.2, 0.04), (-4.29, -3.0, 0.95), M["n_yel"], C)
# vitrina de premios contra la pared
box("S_Estanteria", (0.45, 3.0, 2.2), (-5.75, -3.0, 1.1), M["purple"], C)
for i, z in enumerate((0.55, 1.05, 1.55, 2.05)):
    box(f"Repisa_{i}", (0.5, 3.0, 0.03), (-5.55, -3.0, z), M["white"], C)
text("Letrero_Premios", "PREMIOS", (-5.95 + 0.42, -3.0, 2.55), 0.32, M["n_yel"], C, rot=(90, 0, 90))
# marcador de tickets de la recepción
box("Scoreboard_Marco", (0.06, 1.6, 0.6), (-4.6, -3.0, 1.9), M["black"], C)
box("Scoreboard", (0.02, 1.5, 0.5), (-4.56, -3.0, 1.9), M["screen"], C)
box("Scoreboard_Soporte", (0.06, 0.06, 0.8), (-4.6, -3.0, 1.45), M["chrome"], C)
# nevera de gaseosas
F = empty("Nevera", (-5.55, -0.7, 0), C)
box("S_Nevera_Cuerpo", (0.8, 0.75, 1.9), (0, 0, 0.95), M["red"], C, parent=F)
box("Nevera_Interior", (0.7, 0.6, 1.7), (0.03, 0, 0.95), M["white"], C, parent=F)
for i, z in enumerate((0.55, 1.0, 1.45)):
    box(f"Nevera_Repisa_{i}", (0.7, 0.6, 0.02), (0.03, 0, z), M["chrome"], C, parent=F)
hinge = empty("Nevera_Bisagra", (0.42, -0.36, 0.0), C, parent=F)
box("Fridge_Door", (0.04, 0.72, 1.86), (0, 0.36, 0.95), M["glass"], C, parent=hinge)
box("Fridge_Handle", (0.05, 0.03, 0.5), (0.05, 0.66, 1.1), M["chrome"], C, parent=hinge)

# ---------- rueda de la fortuna (centro) ----------
C = coll("03_Rueda")
WH = empty("Rueda", (0, 1.2, 0), C)
box("S_Rueda_Base", (1.6, 0.8, 0.25), (0, 0, 0.125), M["black"], C, parent=WH)
box("Rueda_Poste", (0.25, 0.25, 1.9), (0, 0.15, 1.15), M["chrome"], C, parent=WH)
disk = cyl("Wheel_Disk", 1.0, 0.08, (0, 0, 2.0), M["yellow"], C, rot=(90, 0, 0), verts=48, parent=WH)
cyl("Wheel_Rim", 1.05, 0.06, (0, 0.02, 2.0), M["n_pink"], C, rot=(90, 0, 0), verts=48, parent=WH)
box("Wheel_Pointer", (0.12, 0.06, 0.25), (0, -0.08, 3.12), M["n_cyan"], C, parent=WH)
# palanca grande horizontal al lado derecho
LV = empty("Wheel_Lever_Pivot", (1.0, 0.0, 1.15), C, parent=WH)
box("Lever_Base", (0.25, 0.25, 0.3), (0, 0, 0), M["black"], C, parent=LV)
box("Wheel_Lever", (0.7, 0.06, 0.06), (0.35, 0, 0.1), M["chrome"], C, parent=LV)
sphere("Wheel_Lever_Knob", 0.07, (0.72, 0, 0.1), M["red"], C, parent=LV)
box("S_Lever_Pedestal", (0.3, 0.3, 1.0), (1.0, 0.0, 0.5), M["purple"], C, parent=WH)

# ---------- galería de tiro (pared izquierda, atrás) ----------
C = coll("04_Tiro")
box("S_Tiro_Mostrador", (0.6, 3.4, 1.0), (-3.6, 2.4, 0.5), M["red"], C)
box("Tiro_Mostrador_Tope", (0.7, 3.5, 0.04), (-3.6, 2.4, 1.02), M["wood"], C)
box("Tiro_Cabina_Techo", (2.6, 3.6, 0.1), (-4.7, 2.4, 2.8), M["red"], C)
box("Tiro_Cabina_Toldo", (0.1, 3.6, 0.4), (-3.4, 2.4, 2.6), M["yellow"], C)
box("Tiro_Fondo", (0.05, 3.4, 2.2), (-5.95, 2.4, 1.6), M["teal"], C)
text("Letrero_Tiro", "TIRO AL BLANCO", (-3.33, 2.4, 2.6), 0.22, M["n_yel"], C, rot=(90, 0, 90))
for i in range(3):   # rieles de dianas
    box(f"Tiro_Riel_{i}", (0.05, 3.2, 0.04), (-5.85, 2.4, 1.2 + i * 0.5), M["chrome"], C)
GUNS = coll("04_Tiro_Pistolas")
for i, y in enumerate((1.8, 3.0)):
    g = empty(f"Gun_{i+1}", (-3.6, y, 1.09), GUNS, rot=(0, 0, 90))
    box(f"Gun_{i+1}_Body", (0.25, 0.05, 0.07), (0.05, 0, 0.03), M["n_cyan"] if i == 0 else M["n_pink"], GUNS, parent=g)
    box(f"Gun_{i+1}_Grip", (0.05, 0.045, 0.12), (-0.04, 0, -0.03), M["black"], GUNS, rot=(0, -15, 0), parent=g)
    empty(f"Gun_{i+1}_Muzzle", (0.18, 0, 0.03), GUNS, parent=g)

# ---------- golpea el topo (pared derecha, adelante) ----------
C = coll("05_Topo")
box("S_Topo_Mueble", (0.9, 1.2, 0.85), (5.2, -2.0, 0.425), M["orange"], C)
box("Topo_Tablero", (0.95, 1.25, 0.04), (5.2, -2.0, 0.87), M["black"], C)
box("Topo_Torre", (0.3, 1.2, 1.4), (5.8, -2.0, 1.55), M["orange"], C)
box("Topo_Pantalla", (0.02, 1.0, 0.45), (5.64, -2.0, 1.95), M["screen"], C)
text("Letrero_Topo", "GOLPEA EL TOPO", (5.63, -2.0, 2.4), 0.14, M["n_cyan"], C, rot=(90, 0, 270))
k = 0
for ix, dx in enumerate((-0.25, 0.0, 0.25)):
    for iy, dy in enumerate((-0.35, 0.0, 0.35)):
        k += 1
        cyl(f"Topo_Hueco_{k}", 0.1, 0.02, (5.2 + dx, -2.0 + dy, 0.885), M["black"], C, verts=16)
        cyl(f"Mole_{k}", 0.075, 0.16, (5.2 + dx, -2.0 + dy, 0.82), M["purple"], C, verts=16)

# ---------- mini basket (pared derecha, atrás) ----------
C = coll("06_Basket")
box("S_Basket_Rampa", (3.0, 1.4, 0.3), (4.4, 2.4, 0.5), M["teal"], C, rot=(0, -6, 0))
box("S_Basket_Lado_A", (3.0, 0.06, 1.0), (4.4, 1.7, 0.6), M["purple"], C)
box("S_Basket_Lado_B", (3.0, 0.06, 1.0), (4.4, 3.1, 0.6), M["purple"], C)
box("S_Basket_Tablero", (0.05, 1.2, 0.9), (5.85, 2.4, 2.3), M["white"], C)
box("Basket_Tablero_Neon", (0.02, 1.1, 0.04), (5.82, 2.4, 2.76), M["n_pink"], C)
cyl("Basket_Aro", 0.24, 0.02, (5.5, 2.4, 2.05), M["orange"], C, verts=24)
cyl("Hoop_Trigger", 0.2, 0.08, (5.5, 2.4, 1.95), M["n_cyan"], C, verts=16)
box("Basket_Bandeja", (0.4, 1.3, 0.12), (3.0, 2.4, 0.95), M["black"], C)
for i in range(4):
    sphere(f"Ball_{i+1}", 0.12, (3.0, 1.95 + i * 0.3, 1.13), M["orange"], C)
text("Letrero_Basket", "MINI BASKET", (5.82, 2.4, 3.0), 0.2, M["n_yel"], C, rot=(90, 0, 270))

# ---------- maquinitas decorativas (pared del fondo) ----------
C = coll("07_Maquinitas")
def cabinet(i, x, color, neon):
    p = empty(f"Arcade_{i}", (x, 4.45, 0), C)
    box(f"Arcade_{i}_Base", (0.75, 0.8, 1.0), (0, 0, 0.5), color, C, parent=p)
    box(f"Arcade_{i}_Cuerpo", (0.75, 0.55, 0.85), (0, 0.12, 1.42), color, C, parent=p)
    box(f"Arcade_{i}_Panel", (0.75, 0.35, 0.06), (0, -0.25, 1.02), M["black"], C, rot=(-15, 0, 0), parent=p)
    box(f"Screen_{i}", (0.55, 0.02, 0.45), (0, -0.16, 1.45), M["screen"], C, rot=(-8, 0, 0), parent=p)
    box(f"Arcade_{i}_Marquesina", (0.75, 0.35, 0.22), (0, 0.0, 1.98), neon, C, parent=p)
    sphere(f"Arcade_{i}_Joystick", 0.035, (-0.15, -0.28, 1.12), M["red"], C, parent=p)
    for b in range(3):
        cyl(f"Arcade_{i}_Boton_{b}", 0.025, 0.02, (0.05 + b * 0.08, -0.27, 1.07), M["yellow"], C, rot=(-15, 0, 0), verts=12, parent=p)
    return p
cols = [(M["purple"], M["n_pink"]), (M["teal"], M["n_yel"]), (M["red"], M["n_cyan"]), (M["black"], M["n_purp"]), (M["purple"], M["n_cyan"])]
for i, x in enumerate((-3.6, -2.4, -1.2, 1.2, 2.4)):
    cabinet(i + 1, x, *cols[i])
# máquina moderna de carreras (toque actual)
RC = empty("Carreras_Moderna", (3.9, 4.2, 0), C)
box("Carreras_Asiento", (0.6, 0.7, 0.5), (0, -0.3, 0.25), M["black"], C, parent=RC)
box("Carreras_Respaldo", (0.6, 0.12, 0.6), (0, -0.62, 0.75), M["black"], C, parent=RC)
box("Carreras_Cuerpo", (1.0, 0.6, 1.5), (0, 0.45, 0.75), M["white"], C, parent=RC)
box("Screen_6", (0.9, 0.02, 0.55), (0, 0.14, 1.25), M["screen"], C, parent=RC)
cyl("Carreras_Timon", 0.17, 0.03, (0, 0.05, 0.85), M["black"], C, rot=(70, 0, 0), parent=RC)
box("Carreras_LED", (1.02, 0.62, 0.03), (0, 0.45, 1.52), M["n_cyan"], C, parent=RC)
# máquina de baile (toque actual)
DM = empty("Baile_Moderna", (0, 4.3, 0), C)
box("Baile_Pantalla_Cuerpo", (1.0, 0.4, 2.1), (0, 0.35, 1.05), M["black"], C, parent=DM)
box("Screen_7", (0.85, 0.02, 0.6), (0, 0.14, 1.6), M["screen"], C, parent=DM)
box("Baile_Piso", (1.0, 1.0, 0.12), (0, -0.4, 0.06), M["chrome"], C, parent=DM)
for j, (dx, dy, nm) in enumerate(((-0.3, -0.4, "n_pink"), (0.3, -0.4, "n_cyan"), (0, -0.1, "n_yel"), (0, -0.7, "n_purp"))):
    box(f"Baile_Flecha_{j}", (0.25, 0.25, 0.02), (dx, dy, 0.13), M[nm], C, parent=DM)
# mural synthwave y marcador grande
box("Mural_Synthwave", (7.0, 0.02, 1.2), (0, y1 - 0.01, 2.85), M["screen"], C)
box("Scoreboard_Grande_Marco", (2.0, 0.06, 0.7), (-4.6, y1 - 0.04, 2.6), M["black"], C)
box("Scoreboard_Big", (1.9, 0.02, 0.6), (-4.6, y1 - 0.08, 2.6), M["screen"], C)

# ---------- luces (la luz principal sale de los neones emisivos) ----------
L = coll("08_Luces")
def light(name, kind, loc, color, energy, size=0.5):
    ld = bpy.data.lights.new(name, kind)
    ld.color = color; ld.energy = energy
    if kind == 'AREA': ld.size = size
    o = bpy.data.objects.new(name, ld)
    L.objects.link(o); o.location = loc
    return o
light("Luz_Techo_Centro", 'AREA', (0, 0, H - 0.1), (0.85, 0.75, 1.0), 400, 4)
light("Luz_Rosa_Izq", 'POINT', (-4, 2.4, 2.6), (1, 0.3, 0.8), 150)
light("Luz_Cian_Der", 'POINT', (4.5, 0, 2.6), (0.3, 0.9, 1), 150)
light("Luz_Recepcion", 'POINT', (-4.2, -3.0, 2.8), (1, 0.85, 0.6), 120)

# ---------- cámara: punto de inicio del jugador (entrada) ----------
cam_data = bpy.data.cameras.new("Camera")
cam = bpy.data.objects.new("Camera", cam_data)
root.objects.link(cam)
cam.location = (0, -3.8, 1.6)
cam.rotation_euler = (math.radians(90), 0, 0)   # mirando hacia +Y (hacia el fondo)
cam_data.lens = 18
scene.camera = cam

# ---------- XR ----------
X = empty("XR_Rig_Origen", (0, -3.8, 0), root)
G = empty("GameManager", (0, 0, 0), root)

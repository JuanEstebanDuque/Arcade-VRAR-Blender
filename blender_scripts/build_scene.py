# PIXEL 84 — construye toda la escena del arcade con detalle (1 unidad = 1 m).
# Uso en Blender: exec(open(ruta_de_este_archivo).read())  -> BORRA la escena actual y la rehace.
# Convenciones de nombres que lee el código web (web/src/scripts/arcade): ver README.md
import bpy, math, os, sys
_dir = os.path.join(os.path.dirname(bpy.data.filepath), "blender_scripts")
exec(open(os.path.join(_dir, "lib.py"), encoding="utf8").read())

# ---------------- limpieza ----------------
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
for blk in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights, bpy.data.cameras, bpy.data.images):
    for x in list(blk):
        if x.users == 0: blk.remove(x)
_imgcache.clear()

# ---------------- materiales base ----------------
M = dict(
 floor = mat_img("Alfombra_Cosmica", "carpet.png", rough=0.95),
 wall  = mat_img("Pared_Paneles", "wall.png", rough=0.85),
 ceil  = mat("Techo", (0.02, 0.015, 0.03), 0.9),
 black = mat("Plastico_Negro", (0.015, 0.015, 0.02), 0.35),
 rubber= mat("Goma_Negra", (0.03, 0.03, 0.03), 0.9),
 chrome= mat("Cromo", (0.85, 0.85, 0.9), 0.15, 1.0),
 gold  = mat("Dorado", (1.0, 0.7, 0.2), 0.25, 1.0),
 white = mat("Blanco", (0.9, 0.9, 0.9), 0.4),
 wood  = mat("Madera", (0.32, 0.16, 0.07), 0.5),
 red   = mat("Rojo", (0.75, 0.03, 0.06), 0.35),
 yellow= mat("Amarillo", (0.95, 0.72, 0.05), 0.4),
 teal  = mat("Turquesa", (0.02, 0.45, 0.55), 0.4),
 purple= mat("Morado", (0.28, 0.05, 0.5), 0.4),
 orange= mat("Naranja", (0.95, 0.35, 0.03), 0.45),
 blue  = mat("Azul", (0.03, 0.15, 0.7), 0.4),
 green = mat("Verde", (0.05, 0.6, 0.2), 0.4),
 brown = mat("Cafe_Topo", (0.4, 0.22, 0.1), 0.7),
 skin  = mat("Hocico", (0.85, 0.65, 0.45), 0.7),
 pink  = mat("Rosa", (1.0, 0.35, 0.6), 0.5),
 n_pink= mat("Neon_Magenta", (1, 0.1, 0.7), 0.3, 0, (1, 0.05, 0.6), 8),
 n_cyan= mat("Neon_Cian", (0.1, 0.9, 1), 0.3, 0, (0.05, 0.8, 1), 8),
 n_yel = mat("Neon_Amarillo", (1, 0.85, 0.2), 0.3, 0, (1, 0.8, 0.1), 6),
 n_purp= mat("Neon_Morado", (0.6, 0.2, 1), 0.3, 0, (0.55, 0.15, 1), 6),
 n_grn = mat("Neon_Verde", (0.2, 1, 0.4), 0.3, 0, (0.1, 1, 0.3), 6),
 n_red = mat("Neon_Rojo", (1, 0.1, 0.1), 0.3, 0, (1, 0.05, 0.05), 6),
 bulb  = mat("Bombillo", (1, 0.9, 0.6), 0.2, 0, (1, 0.85, 0.5), 10),
 led   = mat("Display_LED", (0.01, 0.01, 0.015), 0.2, 0, (0.03, 0.0, 0.05), 1),
 eye   = mat("Ojo_Blanco", (0.95, 0.95, 0.95), 0.3),
 mirror= mat("Espejo_Disco", (0.9, 0.9, 0.95), 0.05, 1.0),
 ref   = mat("Referencia", (0.9, 0.3, 0.1), 0.8),
)
glass = bpy.data.materials.new("Vidrio"); b = _bsdf(glass)
b.inputs["Base Color"].default_value = (0.6, 0.85, 1, 1); b.inputs["Roughness"].default_value = 0.05
b.inputs["Alpha"].default_value = 0.22
try: glass.surface_render_method = "BLENDED"
except Exception: pass
M["glass"] = glass

W, D, H = 12.0, 10.0, 3.6
x0, x1, y0, y1 = -W/2, W/2, -D/2, D/2

# =====================================================================
# ARQUITECTURA
# =====================================================================
C = coll("01_Arquitectura")
box("FLOOR", (W, D, 0.1), (0, 0, -0.05), M["floor"], C, tile=2.5)
box("S_Pared_Fondo", (W, 0.2, H), (0, y1 + 0.1, H/2), M["wall"], C, tile=2.0)
box("S_Pared_Frente", (W, 0.2, H), (0, y0 - 0.1, H/2), M["wall"], C, tile=2.0)
box("S_Pared_Izq", (0.2, D, H), (x0 - 0.1, 0, H/2), M["wall"], C, tile=2.0)
box("S_Pared_Der", (0.2, D, H), (x1 + 0.1, 0, H/2), M["wall"], C, tile=2.0)
box("Techo", (W, D, 0.1), (0, 0, H + 0.05), M["ceil"], C)
# zócalos y cornisas de neón
for nm, pts, m in (
    ("Neon_Zocalo_Fondo", [(x0+0.05, y1-0.03, 0.12), (x1-0.05, y1-0.03, 0.12)], M["n_pink"]),
    ("Neon_Zocalo_Izq",   [(x0+0.03, y0+0.05, 0.12), (x0+0.03, y1-0.05, 0.12)], M["n_cyan"]),
    ("Neon_Zocalo_Der",   [(x1-0.03, y0+0.05, 0.12), (x1-0.03, y1-0.05, 0.12)], M["n_cyan"]),
    ("Neon_Cornisa",      [(x0+0.03, y0+0.03, H-0.12), (x1-0.03, y0+0.03, H-0.12), (x1-0.03, y1-0.03, H-0.12), (x0+0.03, y1-0.03, H-0.12)], M["n_purp"]),
):
    tube(nm, pts, 0.012, m, C, cyclic=(nm == "Neon_Cornisa"))
# franjas del techo en zigzag (muy ochentero)
for i, x in enumerate((-3.0, 0.0, 3.0)):
    pts = [(x + (0.25 if k % 2 else -0.25), -4.0 + k * 0.8, H - 0.03) for k in range(11)]
    tube(f"Neon_Techo_Zigzag_{i}", pts, 0.015, M["n_cyan"] if i != 1 else M["n_pink"], C)
# focos de techo
for i, (x, y) in enumerate(((-3, -2.5), (3, -2.5), (-3, 2.5), (3, 2.5), (0, -3.6))):
    cyl(f"Foco_{i}", 0.09, 0.12, (x, y, H - 0.06), M["black"], C, cap_mat=M["bulb"], verts=16)
# bola disco
sphere("Bola_Disco", 0.26, (0, -1.6, H - 0.55), M["mirror"], C, seg=16, rings=10)
for f in bpy.data.objects["Bola_Disco"].data.polygons: f.use_smooth = False
cyl("Bola_Disco_Cadena", 0.006, 0.3, (0, -1.6, H - 0.15), M["chrome"], C, verts=6)

# puerta de entrada
P = empty("Puerta", (0, y0 + 0.02, 0), C)
box("Puerta_Marco", (1.9, 0.08, 2.35), (0, 0, 1.175), M["chrome"], C, parent=P, bevel=0.01)
box("Puerta_Vidrio_Izq", (0.86, 0.03, 2.15), (-0.44, -0.0, 1.1), M["glass"], C, parent=P)
box("Puerta_Vidrio_Der", (0.86, 0.03, 2.15), (0.44, -0.0, 1.1), M["glass"], C, parent=P)
box("Puerta_Division", (0.04, 0.06, 2.2), (0, 0.01, 1.1), M["chrome"], C, parent=P)
for s in (-1, 1): cyl(f"Puerta_Barra_{s}", 0.018, 0.6, (s * 0.44, 0.07, 1.05), M["chrome"], C, rot=(0, 90, 0), parent=P, verts=12)
text_mesh("Letrero_Nombre", "PIXEL 84", (0, y0 + 0.06, 2.95), 0.55, M["n_pink"], C, rot=(90, 0, 180), extrude=0.03)
tube("Letrero_Nombre_Marco", [(-1.7, y0+0.05, 2.6), (1.7, y0+0.05, 2.6), (1.7, y0+0.05, 3.3), (-1.7, y0+0.05, 3.3)], 0.012, M["n_cyan"], C, cyclic=True)
text_mesh("Letrero_Abierto", "ABIERTO", (0.0, y0 + 0.07, 2.42), 0.14, M["n_grn"], C, rot=(90, 0, 180), extrude=0.01)

# pósters con marco
for i, (pos, rot) in enumerate((
    ((-2.6, y0 + 0.02, 1.6), (90, 0, 180)), ((2.6, y0 + 0.02, 1.6), (90, 0, 180)),
    ((x1 - 0.02, -0.4, 1.6), (90, 0, 90 + 180)), ((x1 - 0.02, -4.0, 1.6), (90, 0, -90))), 1):
    pm = mat_img(f"Poster_{i}", f"poster{i}.png", rough=0.5, emissive=0.25)
    pl = plane(f"Poster_{i}", 0.6, 0.9, pos, pm, C, rot=rot)
    fr = plane(f"Poster_{i}_Marco", 0.68, 0.98, pos, M["black"], C, rot=rot)
    # el marco va 1 cm detrás del póster
    n = pl.matrix_world.to_3x3() @ Vector((0, 0, 1)) if False else None
P3 = bpy.data.objects
for i in range(1, 5):
    p = P3[f"Poster_{i}"]; fr = P3[f"Poster_{i}_Marco"]
    bpy.context.view_layer.update()
    nrm = p.matrix_world.to_3x3() @ Vector((0, 0, 1))
    p.location = p.location + nrm * 0.012
mural = mat_img("Mural_Synthwave", "mural.png", rough=0.6, emissive=0.6)
plane("Mural_Synthwave", 6.4, 1.6, (0, y1 - 0.02, 2.75), mural, C, rot=(90, 0, 180))

# referencia humana (se oculta en la web)
Rc = coll("00_Referencia")
cyl("REF_Humano_1.70m", 0.22, 1.70, (-2.2, -1.6, 0.85), M["ref"], Rc, verts=12)

# =====================================================================
# MAQUINITAS (pared del fondo)
# =====================================================================
C = coll("07_Maquinitas")
PROF = [(-0.38, 0.0), (-0.38, 0.92), (-0.56, 0.98), (-0.56, 1.04), (-0.30, 1.10), (-0.22, 1.72),
        (-0.31, 1.74), (-0.31, 2.02), (0.40, 2.02), (0.40, 0.0)]
BODY = [M["purple"], M["teal"], M["red"], M["blue"], M["purple"]]
NEON = [M["n_cyan"], M["n_yel"], M["n_cyan"], M["n_pink"], M["n_yel"]]

def cabinet(i, x, y=4.45, rotz=0):
    p = empty(f"Arcade_{i}", (x, y, 0), C, rot=(0, 0, rotz))
    side = mat_img(f"Arte_Lateral_{i}", f"cab{i}_side.png", rough=0.45)
    extrude_profile(f"Arcade_{i}_Cuerpo", PROF, 0.76, C, BODY[i-1], side, (0, 0, 0), parent=p)
    for s in (-1, 1):
        tube(f"Arcade_{i}_Moldura_{'I' if s<0 else 'D'}", [(s * 0.385, py, pz) for py, pz in PROF], 0.009, NEON[i-1], C, parent=p, cyclic=True)
    tilt = math.degrees(math.atan2(0.08, 0.62))
    mid = Vector((0, -0.26, 1.41)); nrm = Vector((0, -math.cos(R(tilt)), math.sin(R(tilt))))
    box(f"Arcade_{i}_Bisel", (0.68, 0.05, 0.58), mid + nrm * 0.0, M["black"], C, rot=(-tilt, 0, 0), parent=p, bevel=0.012)
    scr = mat_img(f"Pantalla_{i}", f"cab{i}_screen.png", rough=0.1, emissive=1.8)
    plane(f"Screen_{i}", 0.54, 0.405, mid + nrm * 0.027, scr, C, rot=(90 - tilt, 0, 0), parent=p)
    box(f"Arcade_{i}_Vidrio", (0.6, 0.006, 0.46), mid + nrm * 0.032, M["glass"], C, rot=(-tilt, 0, 0), parent=p)
    mq = mat_img(f"Marquesina_{i}", f"cab{i}_marquee.png", rough=0.3, emissive=2.2)
    plane(f"Arcade_{i}_Marquesina", 0.74, 0.25, (0, -0.312, 1.88), mq, C, parent=p)
    box(f"Arcade_{i}_Parlante", (0.7, 0.06, 0.03), (0, -0.33, 1.75), M["black"], C, parent=p)
    # panel de control
    pt = 13.0
    panel = mat_img(f"Panel_{i}", f"cab{i}_panel.png", rough=0.4)
    plane(f"Arcade_{i}_Panel", 0.74, 0.26, (0, -0.43, 1.074), panel, C, rot=(pt, 0, 0), parent=p)
    zc = lambda yy: 1.04 + 0.06 * ((yy + 0.56) / 0.26) + 0.004
    cyl(f"Arcade_{i}_Joy_Base", 0.035, 0.012, (-0.2, -0.46, zc(-0.46)), M["black"], C, rot=(pt, 0, 0), parent=p, verts=16)
    cyl(f"Arcade_{i}_Joy_Palo", 0.007, 0.08, (-0.2, -0.465, zc(-0.46) + 0.04), M["chrome"], C, rot=(pt, 0, 0), parent=p, verts=8)
    sphere(f"Arcade_{i}_Joy_Bola", 0.024, (-0.2, -0.475, zc(-0.46) + 0.085), M["red"], C, parent=p, seg=12, rings=8)
    for k, bm in enumerate((M["n_red"], M["n_yel"], M["n_cyan"], M["n_grn"])):
        bx = 0.0 + (k % 2) * 0.075 + (k // 2) * 0.035; by = -0.47 + (k // 2) * 0.07
        cyl(f"Arcade_{i}_Boton_{k}", 0.021, 0.018, (bx, by, zc(by) + 0.006), bm, C, rot=(pt, 0, 0), parent=p, verts=16)
    for k in range(2):
        cyl(f"Arcade_{i}_Start_{k}", 0.012, 0.012, (0.22 + k * 0.06, -0.36, zc(-0.36) + 0.004), M["white"], C, rot=(pt, 0, 0), parent=p, verts=12)
    door = mat_img("Puerta_Monedas", "coin_door.png", rough=0.4, emissive=0.15)
    plane(f"Arcade_{i}_Monedero", 0.28, 0.28, (0, -0.386, 0.5), door, C, parent=p)
    box(f"Arcade_{i}_Zocalo", (0.77, 0.02, 0.08), (0, -0.39, 0.04), M["chrome"], C, parent=p)
    return p

for i, x in enumerate((-3.0, -2.1, -1.2, 1.2, 2.1), 1):
    cabinet(i, x)
# taburetes
for i, x in enumerate((-2.55, -1.2, 1.65)):
    cyl(f"Taburete_{i}_Asiento", 0.18, 0.07, (x, 3.6, 0.68), M["red"], C, cap_mat=M["red"], verts=20)
    torus(f"Taburete_{i}_Borde", 0.18, 0.02, (x, 3.6, 0.68), M["chrome"], C, mseg=8)
    cyl(f"Taburete_{i}_Poste", 0.025, 0.62, (x, 3.6, 0.33), M["chrome"], C, verts=10)
    cyl(f"Taburete_{i}_Base", 0.2, 0.03, (x, 3.6, 0.015), M["chrome"], C, verts=20)
    torus(f"Taburete_{i}_Aro", 0.16, 0.01, (x, 3.6, 0.3), M["chrome"], C, mseg=6)

# --- máquina de carreras moderna ---
RC = empty("Carreras_Moderna", (3.4, 4.2, 0), C)
box("Carreras_Plataforma", (1.1, 1.5, 0.12), (0, -0.25, 0.06), M["black"], C, parent=RC, bevel=0.02)
tube("Carreras_LED_Piso", [(-0.56, -1.0, 0.13), (0.56, -1.0, 0.13), (0.56, 0.5, 0.13), (-0.56, 0.5, 0.13)], 0.01, M["n_cyan"], C, parent=RC, cyclic=True)
box("Carreras_Asiento", (0.5, 0.5, 0.14), (0, -0.62, 0.5), M["black"], C, parent=RC, bevel=0.05)
box("Carreras_Respaldo", (0.5, 0.14, 0.7), (0, -0.88, 0.85), M["black"], C, parent=RC, rot=(-12, 0, 0), bevel=0.05)
for s in (-1, 1):
    box(f"Carreras_Lateral_{s}", (0.06, 0.5, 0.2), (s * 0.25, -0.65, 0.6), M["red"], C, parent=RC, bevel=0.025)
    box(f"Carreras_Hombro_{s}", (0.07, 0.12, 0.4), (s * 0.26, -0.9, 1.0), M["red"], C, parent=RC, rot=(-12, 0, 0), bevel=0.03)
box("Carreras_Base_Asiento", (0.4, 0.4, 0.38), (0, -0.62, 0.31), M["chrome"], C, parent=RC)
prof_rc = [(-0.25, 0.0), (-0.25, 0.75), (-0.35, 0.8), (-0.12, 1.0), (-0.05, 1.85), (0.45, 1.85), (0.45, 0.0)]
extrude_profile("Carreras_Cuerpo", prof_rc, 1.0, C, M["white"], M["black"], (0, 0.15, 0), parent=RC)
for s in (-1, 1):
    tube(f"Carreras_LED_{s}", [(s * 0.505, py + 0.15, pz) for py, pz in prof_rc], 0.012, M["n_cyan"], C, parent=RC, cyclic=True)
road = mat_img("Pantalla_Carreras", "mural.png", rough=0.1, emissive=1.6)
box("Carreras_Bisel", (0.92, 0.05, 0.62), (0, 0.06, 1.42), M["black"], C, parent=RC, rot=(-5, 0, 0), bevel=0.015)
plane("Screen_6", 0.86, 0.55, (0, 0.03, 1.42), road, C, rot=(85, 0, 0), parent=RC)
cyl("Carreras_Columna", 0.03, 0.3, (0, -0.15, 0.95), M["black"], C, rot=(60, 0, 0), parent=RC, verts=10)
torus("Carreras_Timon", 0.17, 0.022, (0, -0.28, 1.04), M["black"], C, rot=(-30 + 90, 0, 0), parent=RC, mseg=8)
cyl("Carreras_Timon_Centro", 0.05, 0.04, (0, -0.27, 1.04), M["red"], C, rot=(60, 0, 0), parent=RC, verts=12)
for s in (-1, 1): box(f"Carreras_Pedal_{s}", (0.08, 0.14, 0.02), (s * 0.1, -0.18, 0.2), M["chrome"], C, parent=RC, rot=(35, 0, 0))
text_mesh("Carreras_Titulo", "TURBO 84", (0, -0.21, 1.93), 0.13, M["n_cyan"], C, rot=(90, 0, 0), parent=RC, extrude=0.01)

# --- máquina de baile moderna ---
DM = empty("Baile_Moderna", (0, 4.35, 0), C)
box("Baile_Plataforma", (1.2, 1.2, 0.14), (0, -0.55, 0.07), M["chrome"], C, parent=DM, bevel=0.02)
arrows = [((0, -0.2), 0, M["n_pink"]), ((0, -0.9), 180, M["n_cyan"]), ((-0.35, -0.55), 90, M["n_yel"]), ((0.35, -0.55), -90, M["n_grn"])]
for k, ((ax, ay), r, m) in enumerate(arrows):
    o = cyl(f"Baile_Flecha_{k}", 0.13, 0.02, (ax, ay, 0.15), m, C, rot=(0, 0, r + 90), parent=DM, verts=3, smooth=False)
    box(f"Baile_Cuadro_{k}", (0.3, 0.3, 0.01), (ax, ay, 0.142), M["black"], C, parent=DM)
tube("Baile_Baranda", [(-0.55, -0.0, 0.14), (-0.55, 0.05, 0.95), (0.55, 0.05, 0.95), (0.55, 0.0, 0.14)], 0.02, M["chrome"], C, parent=DM)
box("Baile_Cuerpo", (1.0, 0.45, 2.25), (0, 0.3, 1.125), M["black"], C, parent=DM, bevel=0.03)
box("Baile_Bisel", (0.86, 0.04, 0.68), (0, 0.06, 1.55), M["black"], C, parent=DM, bevel=0.015)
plane("Screen_7", 0.8, 0.6, (0, 0.035, 1.55), mat_img("Pantalla_Baile", "cab5_screen.png", rough=0.1, emissive=1.8), C, parent=DM)
for s in (-1, 1):
    cyl(f"Baile_Parlante_{s}", 0.13, 0.04, (s * 0.32, 0.07, 0.8), M["rubber"], C, rot=(90, 0, 0), parent=DM, verts=20)
    torus(f"Baile_Parlante_Aro_{s}", 0.13, 0.012, (s * 0.32, 0.05, 0.8), M["n_purp"], C, rot=(90, 0, 0), parent=DM, mseg=6)
    tube(f"Baile_LED_{s}", [(s * 0.51, 0.08, 0.1), (s * 0.51, 0.08, 2.2)], 0.012, M["n_pink"], C, parent=DM)
text_mesh("Baile_Titulo", "DANCE ZONE", (0, 0.07, 2.08), 0.13, M["n_yel"], C, rot=(90, 0, 0), parent=DM, extrude=0.01)

# =====================================================================
# RUEDA CÓSMICA (centro) — tambor que gira al empujar la palanca
# =====================================================================
C = coll("03_Rueda")
WH = empty("Rueda", (0, 1.0, 0), C)
side = mat_img("Rueda_Lateral", "wheel_side.png", rough=0.45)
front = mat_img("Rueda_Frente", "wheel_front.png", rough=0.4, emissive=0.5)
box("S_Rueda_Base", (1.3, 1.0, 0.95), (0, 0, 0.475), M["purple"], C, parent=WH, bevel=0.03, face_mats={"-y": front})
for s in (-1, 1):
    box(f"Rueda_Lado_{s}", (0.08, 1.0, 1.55), (s * 0.62, 0, 1.72), M["purple"], C, parent=WH, bevel=0.02,
        face_mats={("+x" if s > 0 else "-x"): side})
    # bombillos que se encienden en secuencia (el código los anima)
    for k in range(9):
        sphere(f"Wheel_Bulb_{'D' if s > 0 else 'I'}_{k}", 0.022, (s * 0.62, -0.52, 1.05 + k * 0.17), M["bulb"], C, parent=WH, seg=10, rings=6)
box("Rueda_Fondo", (1.24, 0.06, 1.55), (0, 0.47, 1.72), M["black"], C, parent=WH)
box("Rueda_Tapa", (1.36, 1.06, 0.08), (0, 0, 2.5), M["purple"], C, parent=WH, bevel=0.02)
box("Rueda_Repisa", (1.24, 0.25, 0.06), (0, -0.38, 0.98), M["black"], C, parent=WH)
# tambor: eje en X, textura con 12 segmentos (u = a lo largo del eje, v = ángulo)
import bmesh as _bm
bm = _bm.new(); uvl = bm.loops.layers.uv.verify()
NSEG, NA, RAD, LEN = 12, (36 if LOWPOLY else 72), 0.5, 1.08
rings = []
for i in range(NA + 1):
    a = 2 * math.pi * i / NA
    rings.append([bm.verts.new((sx * LEN / 2, -RAD * math.cos(a), RAD * math.sin(a))) for sx in (-1, 1)])
for i in range(NA):
    f = bm.faces.new((rings[i][0], rings[i][1], rings[i+1][1], rings[i+1][0])); f.smooth = True
    for l in f.loops:
        idx = 0 if l.vert in (rings[i][0], rings[i+1][0]) else 1
        k = i if l.vert in rings[i] else i + 1
        l[uvl].uv = (idx, k / NA)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
drum_mat = mat_img("Rueda_Tambor", "wheel_drum.png", rough=0.35, emissive=0.35)
_finish("Wheel_Drum", bm, [drum_mat], C, (0, 0.0, 1.72), (0, 0, 0), WH)
for s in (-1, 1):
    cyl(f"Wheel_Tapa_{s}", RAD + 0.02, 0.03, (s * (LEN/2 + 0.015), 0, 1.72), M["chrome"], C, rot=(0, 90, 0), parent=WH, verts=48)
cyl("Rueda_Eje", 0.03, 1.22, (0, 0, 1.72), M["chrome"], C, rot=(0, 90, 0), parent=WH, verts=12)
# marco neón de la ventana y línea ganadora
tube("Rueda_Marco_Neon", [(-0.57, -0.53, 1.02), (-0.57, -0.53, 2.3), (-0.3, -0.53, 2.44), (0.3, -0.53, 2.44), (0.57, -0.53, 2.3), (0.57, -0.53, 1.02)], 0.016, M["n_pink"], C, parent=WH)
for s in (-1, 1):
    o = cyl(f"Wheel_Pointer_{s}", 0.07, 0.04, (s * 0.53, -0.47, 1.72), M["n_yel"], C, rot=(90, 0, 90 * s), parent=WH, verts=3, smooth=False)
box("Wheel_Display", (0.8, 0.07, 0.2), (0, -0.49, 2.62), M["led"], C, parent=WH, bevel=0.01)
box("Rueda_Display_Marco", (0.86, 0.06, 0.26), (0, -0.46, 2.62), M["chrome"], C, parent=WH, bevel=0.01)
top = mat_img("Rueda_Topper", "wheel_topper.png", rough=0.4, emissive=0.9, alpha_clip=True)
plane("Wheel_Topper", 1.3, 0.89, (0, -0.2, 3.1), top, C, parent=WH)
plane("Wheel_Topper_Atras", 1.3, 0.89, (0, -0.19, 3.1), top, C, rot=(90, 0, 180), parent=WH)
cyl("Rueda_Topper_Soporte", 0.03, 0.4, (0, -0.15, 2.72), M["chrome"], C, parent=WH, verts=10)
# palanca horizontal grande (pivote en X): empujar hacia abajo hace girar el tambor
LV = empty("Wheel_Lever_Pivot", (0, -0.52, 1.0), C, parent=WH)
for s in (-1, 1):
    box(f"Wheel_Lever_Brazo_{s}", (0.04, 0.38, 0.05), (s * 0.4, -0.19, 0.05), M["chrome"], C, parent=LV, bevel=0.01)
    box(f"Rueda_Palanca_Soporte_{s}", (0.1, 0.12, 0.2), (s * 0.4, 0.02, -0.02), M["black"], C, parent=LV, bevel=0.02)
cyl("Wheel_Lever", 0.03, 0.84, (0, -0.38, 0.06), M["chrome"], C, rot=(0, 90, 0), parent=LV, verts=16)
cyl("Wheel_Lever_Grip", 0.042, 0.55, (0, -0.38, 0.06), M["red"], C, rot=(0, 90, 0), parent=LV, verts=16)
plane("Rueda_Monedero", 0.24, 0.24, (0.45, -0.505, 0.45), mat_img("Puerta_Monedas", "coin_door.png"), C, parent=WH)
box("Rueda_Salida_Tickets", (0.16, 0.06, 0.05), (-0.45, -0.52, 0.55), M["black"], C, parent=WH)
tk = mat_img("Ticket", "ticket.png", rough=0.6)
plane("Rueda_Ticket_Tira", 0.06, 0.16, (-0.45, -0.552, 0.45), tk, C, rot=(90, 0, 0), parent=WH)
cyl("S_Rueda_Pata", 0.05, 0.02, (0, 0, 0.01), M["black"], C, parent=WH)

# =====================================================================
# GALERÍA DE TIRO (pared izquierda, atrás)
# =====================================================================
C = coll("04_Tiro")
sign = mat_img("Tiro_Letrero", "gallery_sign.png", rough=0.4, emissive=0.8)
back = mat_img("Tiro_Fondo_Ciudad", "gallery_back.png", rough=0.7, emissive=0.5)
GY0, GY1 = 0.5, 3.8; GYC = (GY0 + GY1) / 2; GL = GY1 - GY0
box("S_Tiro_Mostrador", (0.55, GL - 0.1, 1.0), (-3.6, GYC, 0.5), M["red"], C, bevel=0.02, face_mats={"+x": sign})
box("Tiro_Mostrador_Tope", (0.68, GL, 0.05), (-3.6, GYC, 1.025), M["wood"], C, bevel=0.01)
for yy in (GY0, GY1):
    box(f"Tiro_Poste_{yy}", (0.18, 0.18, 2.95), (-3.42, yy, 1.475), M["yellow"], C, bevel=0.03)
    box(f"Tiro_Pared_{yy}", (2.4, 0.08, 2.95), (-4.7, yy, 1.475), M["purple"], C)
box("Tiro_Cabecera", (0.2, GL + 0.18, 0.5), (-3.42, GYC, 2.7), M["red"], C, bevel=0.02, face_mats={"+x": sign})
box("Tiro_Techo", (2.6, GL + 0.18, 0.06), (-4.7, GYC, 2.95), M["red"], C)
for k in range(15):   # bombillos de feria en la cabecera
    sphere(f"Tiro_Bombillo_{k}", 0.03, (-3.31, GY0 + 0.15 + k * (GL - 0.3) / 14, 2.98), M["bulb"], C, seg=10, rings=6)
# banderines
pts = [(-3.3, GY0 + k * GL / 20, 2.42 - 0.08 * math.sin(math.pi * (k % 10) / 10)) for k in range(21)]
tube("Tiro_Cuerda", pts, 0.004, M["black"], C)
for k in range(20):
    px, py, pz = pts[k]
    o = cyl(f"Tiro_Banderin_{k}", 0.06, 0.01, (px, py + GL / 40, pz - 0.05), [M["yellow"], M["n_pink"], M["teal"], M["red"]][k % 4], C, rot=(0, 90, 0), verts=3, smooth=False)
    o.rotation_euler = (R(-90), R(90), 0)
plane("Tiro_Fondo", GL - 0.1, 1.85, (-5.96, GYC, 1.55), back, C, rot=(90, 0, -90 + 180))
for k, z in enumerate((1.25, 1.85)):
    cyl(f"Tiro_Riel_{k}", 0.018, GL - 0.2, (-5.55, GYC, z), M["chrome"], C, rot=(90, 0, 0), verts=10)
tgt = mat_img("Diana", "target.png", rough=0.5, emissive=0.3, alpha_clip=True)
k = 0
for z in (1.25, 1.85):
    for j in range(4):
        k += 1
        yy = GY0 + 0.45 + j * (GL - 0.9) / 3 + (0.25 if z > 1.5 else 0)
        yy = min(yy, GY1 - 0.35)
        tg = empty(f"Target_{k}", (-5.5, yy, z + 0.2), C)
        plane(f"Target_{k}_Cara", 0.26, 0.26, (0.014, 0, 0), tgt, C, rot=(90, 0, 90), parent=tg)
        cyl(f"Target_{k}_Disco", 0.128, 0.025, (0, 0, 0), M["white"], C, rot=(0, 90, 0), parent=tg, verts=24)
        box(f"Target_{k}_Soporte", (0.03, 0.03, 0.2), (-5.52, yy, z + 0.06), M["chrome"], C)
# latas para tumbar
box("Tiro_Repisa_Latas", (0.4, 1.0, 0.04), (-5.6, GY1 - 0.6, 0.95), M["wood"], C)
box("Tiro_Repisa_Pata", (0.3, 0.8, 0.93), (-5.65, GY1 - 0.6, 0.465), M["purple"], C)
canm = mat_img("Lata_Burbu", "can_burbu.png", rough=0.3, metal=0.3)
k = 0
for row, n in enumerate((3, 2, 1)):
    for j in range(n):
        k += 1
        cyl(f"Can_{k}", 0.04, 0.12, (-5.6, GY1 - 0.6 + (j - (n - 1) / 2) * 0.09, 1.03 + row * 0.122), canm, C, verts=16, cap_mat=M["chrome"])
# pistolas (agarrables)
GN = coll("04_Tiro_Pistolas", C)
for i, (yy, acc) in enumerate(((GYC - 0.7, M["n_cyan"]), (GYC + 0.7, M["n_pink"])), 1):
    g = empty(f"Gun_{i}", (-3.62, yy, 1.1), GN, rot=(0, 0, 180))
    box(f"Gun_{i}_Cuerpo", (0.2, 0.045, 0.07), (0.0, 0, 0.03), M["black"], GN, parent=g, bevel=0.012)
    cyl(f"Gun_{i}_Canon", 0.016, 0.2, (0.18, 0, 0.045), M["chrome"], GN, rot=(0, 90, 0), parent=g, verts=12)
    cyl(f"Gun_{i}_Boca", 0.022, 0.03, (0.28, 0, 0.045), acc, GN, rot=(0, 90, 0), parent=g, verts=12)
    box(f"Gun_{i}_Mira", (0.02, 0.008, 0.02), (0.24, 0, 0.075), M["black"], GN, parent=g)
    box(f"Gun_{i}_Mango", (0.05, 0.04, 0.13), (-0.06, 0, -0.04), M["rubber"], GN, rot=(0, -18, 0), parent=g, bevel=0.012)
    torus(f"Gun_{i}_Guarda", 0.03, 0.005, (0.005, 0, -0.015), M["black"], GN, rot=(90, 0, 0), parent=g, mseg=6, arc=200)
    box(f"Gun_{i}_Gatillo", (0.01, 0.01, 0.03), (0.005, 0, -0.02), M["red"], GN, parent=g)
    box(f"Gun_{i}_Franja", (0.18, 0.047, 0.01), (0.0, 0, 0.055), acc, GN, parent=g)
    empty(f"Gun_{i}_Muzzle", (0.3, 0, 0.045), GN, parent=g, size=0.03)
    box(f"Gun_{i}_Base", (0.3, 0.14, 0.02), (-3.62 + 0.0, yy, 1.06), M["rubber"], C)

# =====================================================================
# GOLPEA EL TOPO (pared derecha, adelante)
# =====================================================================
C = coll("05_Topo")
moleart = mat_img("Topo_Arte", "mole_side.png", rough=0.45, emissive=0.3)
MX, MY = 5.2, -2.0
box("S_Topo_Mueble", (0.95, 1.25, 0.82), (MX, MY, 0.41), M["orange"], C, bevel=0.03, face_mats={"-x": mat_img("Topo_Frente", "mole_front.png", rough=0.4, emissive=0.3)})
box("Topo_Tablero", (1.0, 1.3, 0.05), (MX, MY, 0.845), M["yellow"], C, bevel=0.015)
tube("Topo_Bumper", [(MX - 0.5, MY - 0.65, 0.87), (MX - 0.5, MY + 0.65, 0.87)], 0.03, M["rubber"], C)
box("Topo_Torre", (0.32, 1.25, 1.45), (MX + 0.33, MY, 1.57), M["orange"], C, bevel=0.03, face_mats={"-x": moleart})
box("Mole_Display", (0.05, 0.6, 0.16), (MX + 0.15, MY, 2.38), M["led"], C, bevel=0.01)
for s in (-1, 1):
    tube(f"Topo_LED_{s}", [(MX + 0.16, MY + s * 0.63, 0.88), (MX + 0.16, MY + s * 0.63, 2.3)], 0.012, M["n_yel"], C)
k = 0
for ix, dx in enumerate((-0.27, 0.0, 0.27)):
    for iy, dy in enumerate((-0.36, 0.0, 0.36)):
        k += 1
        hx, hy = MX - 0.06 + dx * 0.9, MY + dy
        torus(f"Topo_Hueco_{k}", 0.085, 0.018, (hx, hy, 0.872), M["black"], C, mseg=8)
        cyl(f"Topo_Hueco_Fondo_{k}", 0.08, 0.01, (hx, hy, 0.86), M["rubber"], C, verts=16)
        mg = empty(f"Mole_{k}", (hx, hy, 0.86), C)
        cyl(f"Mole_{k}_Cuerpo", 0.062, 0.12, (0, 0, 0.0), M["brown"], C, parent=mg, verts=16)
        sphere(f"Mole_{k}_Cabeza", 0.064, (0, 0, 0.06), M["brown"], C, parent=mg, seg=16, rings=8)
        sphere(f"Mole_{k}_Hocico", 0.032, (-0.05, 0, 0.045), M["skin"], C, parent=mg, seg=10, rings=6)
        sphere(f"Mole_{k}_Nariz", 0.013, (-0.08, 0, 0.06), M["pink"], C, parent=mg, seg=8, rings=4)
        for s in (-1, 1):
            sphere(f"Mole_{k}_Ojo_{s}", 0.014, (-0.05, s * 0.022, 0.09), M["eye"], C, parent=mg, seg=8, rings=4)
            sphere(f"Mole_{k}_Pupila_{s}", 0.007, (-0.062, s * 0.022, 0.092), M["black"], C, parent=mg, seg=6, rings=4)
        sphere(f"Mole_{k}_Casco", 0.068, (0, 0, 0.085), M["yellow"], C, parent=mg, seg=12, rings=6, scale=(1, 1, 0.55))
        cyl(f"Mole_{k}_Lampara", 0.015, 0.01, (-0.045, 0, 0.115), M["bulb"], C, rot=(0, -60, 0), parent=mg, verts=8)
for i, s in enumerate((-1, 1), 1):
    mt = empty(f"Mallet_{i}", (MX - 0.42, MY + s * 0.55, 0.92), C, rot=(0, 0, 90))
    cyl(f"Mallet_{i}_Mango", 0.018, 0.32, (0, 0, 0.0), M["yellow"], C, rot=(0, 90, 0), parent=mt, verts=10)
    cyl(f"Mallet_{i}_Cabeza", 0.06, 0.14, (0.18, 0, 0.0), M["red"] if i == 1 else M["blue"], C, parent=mt, verts=16)
    box(f"Topo_Soporte_Mazo_{i}", (0.12, 0.06, 0.05), (MX - 0.42, MY + s * 0.55, 0.875), M["black"], C)

# =====================================================================
# MINI BASKET (pared derecha, atrás) — el jugador lanza mirando hacia +X
# =====================================================================
C = coll("06_Basket")
bart = mat_img("Basket_Lateral", "basket_side.png", rough=0.45, emissive=0.35)
board = mat_img("Basket_Tablero", "backboard.png", rough=0.3, emissive=0.2)
ball = mat_img("Balon", "basketball.png", rough=0.7)
BX0, BX1, BY = 3.35, 5.85, 2.4; BL = BX1 - BX0; BXC = (BX0 + BX1) / 2
box("S_Basket_Base", (BL, 1.1, 0.85), (BXC, BY, 0.425), M["blue"], C, bevel=0.02, face_mats={"-y": bart, "+y": bart})
ang = math.degrees(math.atan2(0.25, BL))
box("S_Basket_Rampa", (BL, 1.1, 0.06), (BXC, BY, 0.98), M["wood"], C, rot=(0, -ang, 0), tile=0.5)
box("S_Basket_Frente", (0.08, 1.1, 1.05), (BX0, BY, 0.525), M["blue"], C, bevel=0.02)
box("Basket_Bandeja", (0.35, 1.0, 0.04), (BX0 - 0.15, BY, 1.0), M["black"], C)
box("Basket_Bandeja_Borde", (0.04, 1.0, 0.08), (BX0 - 0.33, BY, 1.04), M["chrome"], C)
for s in (-1, 1):
    box(f"S_Basket_Lado_{s}", (BL, 0.04, 0.25), (BXC, BY + s * 0.55, 1.15), M["purple"], C)
for (xx, s) in ((BX0 + 0.05, -1), (BX0 + 0.05, 1), (BX1 - 0.05, -1), (BX1 - 0.05, 1)):
    cyl(f"Basket_Poste_{xx:.1f}_{s}", 0.022, 1.65, (xx, BY + s * 0.55, 1.8), M["chrome"], C, verts=10)
for s in (-1, 1):
    tube(f"Basket_Riel_{s}", [(BX0 + 0.05, BY + s * 0.55, 2.62), (BX1 - 0.05, BY + s * 0.55, 2.62)], 0.018, M["chrome"], C)
    # red lateral de alambre
    bm = _bm.new()
    bmesh.ops.create_grid(bm, x_segments=(12 if LOWPOLY else 22), y_segments=(7 if LOWPOLY else 12), size=0.5)
    bmesh.ops.scale(bm, vec=Vector((BL - 0.6, 1.45, 1)), verts=bm.verts)
    nm = _finish(f"Basket_Red_{s}", bm, [M["black"]], C, (BXC + 0.3, BY + s * 0.55, 1.9), (90, 0, 0), None)
    wire_from(nm, 0.004)
tube("Basket_Riel_Arriba", [(BX1 - 0.05, BY - 0.55, 2.62), (BX1 - 0.05, BY + 0.55, 2.62)], 0.018, M["chrome"], C)
box("S_Basket_Tablero", (0.05, 1.05, 0.78), (BX1 - 0.1, BY, 2.2), M["white"], C, bevel=0.01, face_mats={"-x": board})
box("Basket_Brazo_Aro", (0.2, 0.06, 0.04), (BX1 - 0.22, BY, 1.98), M["chrome"], C)
torus("Basket_Aro", 0.2, 0.013, (BX1 - 0.42, BY, 1.98), M["orange"], C, mseg=8)
bm = _bm.new()
bmesh.ops.create_cone(bm, cap_ends=False, segments=(10 if LOWPOLY else 14), radius1=0.13, radius2=0.2, depth=0.3)
bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.1], cuts=(2 if LOWPOLY else 3), use_grid_fill=False)
net = _finish("Basket_Net", bm, [M["white"]], C, (BX1 - 0.42, BY, 1.83), (0, 0, 0), None)
wire_from(net, 0.005)
cyl("Hoop_Trigger", 0.15, 0.06, (BX1 - 0.42, BY, 1.86), M["n_cyan"], C, verts=12)
box("Basket_Display", (0.05, 0.7, 0.18), (BX1 - 0.12, BY, 2.75), M["led"], C, bevel=0.01)
tube("Basket_Arco_Neon", [(BX1 - 0.1, BY - 0.52 + 1.04 * k / 12, 2.6 + 0.35 * math.sin(math.pi * k / 12)) for k in range(13)], 0.015, M["n_pink"], C)
for i in range(4):
    sphere(f"Ball_{i+1}", 0.12, (BX0 - 0.14, BY - 0.36 + i * 0.24, 1.14), ball, C, seg=24, rings=12)

# =====================================================================
# RECEPCIÓN, PREMIOS Y NEVERA (pared izquierda, adelante)
# =====================================================================
C = coll("02_Recepcion")
cfront = mat_img("Recepcion_Frente", "counter_front.png", rough=0.45, emissive=0.4)
box("S_Mostrador", (0.6, 3.2, 1.0), (-4.6, -3.0, 0.5), M["purple"], C, bevel=0.02, face_mats={"+x": cfront})
box("Mostrador_Tope", (0.75, 3.35, 0.05), (-4.62, -3.0, 1.025), M["black"], C, bevel=0.015)
tube("Mostrador_Neon", [(-4.28, -4.6, 0.08), (-4.28, -1.4, 0.08)], 0.012, M["n_yel"], C)
tube("Mostrador_Neon_Alto", [(-4.24, -4.65, 1.03), (-4.24, -1.35, 1.03)], 0.01, M["n_cyan"], C)
# caja registradora
CR = empty("Caja_Registradora", (-4.65, -4.1, 1.05), C, rot=(0, 0, 90))
box("Caja_Base", (0.38, 0.32, 0.12), (0, 0, 0.06), M["black"], C, parent=CR, bevel=0.015)
box("Caja_Teclado", (0.34, 0.18, 0.05), (0, -0.05, 0.14), M["white"], C, parent=CR, rot=(15, 0, 0), bevel=0.01)
box("Caja_Pantalla", (0.2, 0.04, 0.1), (0, 0.1, 0.23), M["led"], C, parent=CR, rot=(-10, 0, 0))
# máquina comedora de tickets
TM = empty("Tragaticket", (-4.65, -1.75, 1.05), C, rot=(0, 0, 90))
box("Tragaticket_Cuerpo", (0.34, 0.3, 0.45), (0, 0, 0.225), M["red"], C, parent=TM, bevel=0.03)
box("Tragaticket_Boca", (0.2, 0.02, 0.03), (0, -0.155, 0.3), M["black"], C, parent=TM)
box("Tragaticket_Pantalla", (0.22, 0.02, 0.09), (0, -0.155, 0.39), M["led"], C, parent=TM)
plane("Tragaticket_Ticket", 0.06, 0.14, (0, -0.17, 0.24), tk, C, parent=TM, rot=(60, 0, 0))
text_mesh("Tragaticket_Texto", "TRAGA TICKETS", (0, -0.156, 0.12), 0.035, M["n_yel"], C, parent=TM, extrude=0.003)
cyl("Campana_Base", 0.06, 0.01, (-4.55, -2.5, 1.06), M["black"], C, verts=16)
sphere("Campana", 0.05, (-4.55, -2.5, 1.065), M["gold"], C, seg=16, rings=8, scale=(1, 1, 0.8))
cyl("Rollo_Tickets", 0.09, 0.07, (-4.7, -3.35, 1.14), tk, C, rot=(90, 0, 0), verts=20, cap_mat=M["pink"])
# marcador de recepción
box("Scoreboard_Marco", (0.08, 1.4, 0.55), (-4.5, -3.0, 2.95), M["chrome"], C, bevel=0.015)
box("Scoreboard", (0.04, 1.3, 0.45), (-4.45, -3.0, 2.95), M["led"], C)
for yy in (-3.6, -2.4):
    cyl(f"Scoreboard_Cadena_{yy}", 0.006, 0.4, (-4.5, yy, 3.42), M["chrome"], C, verts=6)
# estantería de premios
box("S_Estanteria", (0.05, 3.0, 2.3), (-5.96, -3.0, 1.15), M["black"], C)
for yy in (-4.5, -1.5):
    box(f"Estanteria_Lado_{yy}", (0.45, 0.05, 2.3), (-5.76, yy, 1.15), M["purple"], C, bevel=0.01)
box("Estanteria_Techo", (0.47, 3.05, 0.05), (-5.76, -3.0, 2.3), M["purple"], C, bevel=0.01)
for k, z in enumerate((0.5, 1.0, 1.5, 2.0)):
    box(f"Repisa_{k}", (0.42, 2.9, 0.025), (-5.73, -3.0, z), M["white"], C)
    tube(f"Repisa_Neon_{k}", [(-5.51, -4.45, z + 0.015), (-5.51, -1.55, z + 0.015)], 0.006, [M["n_pink"], M["n_cyan"]][k % 2], C)
text_mesh("Letrero_Premios", "PREMIOS", (-5.5, -3.0, 2.55), 0.3, M["n_yel"], C, rot=(90, 0, 90), extrude=0.02)

def tag(v, x, y, z):
    plane(f"Precio_{v}_{y:.2f}", 0.12, 0.06, (x, y, z), mat_img(f"Precio_{v}", f"price_{v}.png", rough=0.5, emissive=0.3), C, rot=(90, 0, 90))

def prize(name, cost, x, y, z, builder):
    p = empty(f"Prize_{cost}_{name}", (x, y, z), C)
    builder(p)
    p.scale = (1.35, 1.35, 1.35)
    tag(cost, -5.5, y, z - 0.03)
    return p

def b_rubik(p):
    rb = mat_img("Rubik", "rubik.png", rough=0.3)
    box("Rubik_Cubo", (0.12, 0.12, 0.12), (0, 0, 0.06), rb, C, parent=p, rot=(0, 0, 20), bevel=0.008)
def b_oso(p):
    t = M["teal"]
    sphere("Oso_Cuerpo", 0.1, (0, 0, 0.1), t, C, parent=p, scale=(1, 1, 1.1))
    sphere("Oso_Cabeza", 0.08, (0, 0, 0.25), t, C, parent=p)
    for s in (-1, 1):
        sphere(f"Oso_Oreja_{s}", 0.03, (0, s * 0.06, 0.32), t, C, parent=p, seg=10, rings=6)
        sphere(f"Oso_Ojo_{s}", 0.012, (0.07, s * 0.03, 0.27), M["black"], C, parent=p, seg=8, rings=4)
        sphere(f"Oso_Brazo_{s}", 0.035, (0.03, s * 0.1, 0.13), t, C, parent=p, seg=10, rings=6, scale=(1, 1, 1.5))
    sphere("Oso_Hocico", 0.03, (0.07, 0, 0.23), M["white"], C, parent=p, seg=10, rings=6)
    sphere("Oso_Corazon", 0.035, (0.09, 0, 0.1), M["n_pink"], C, parent=p, seg=10, rings=6, scale=(0.4, 1, 1))
def b_yoyo(p):
    for s in (-1, 1): cyl(f"Yoyo_Lado_{s}", 0.05, 0.018, (0, s * 0.014, 0.05), M["n_grn"], C, rot=(90, 0, 0), parent=p, verts=20)
    cyl("Yoyo_Eje", 0.012, 0.02, (0, 0, 0.05), M["white"], C, rot=(90, 0, 0), parent=p, verts=8)
def b_pato(p):
    y = M["yellow"]
    sphere("Pato_Cuerpo", 0.07, (0, 0, 0.06), y, C, parent=p, scale=(1.3, 1, 0.8))
    sphere("Pato_Cabeza", 0.045, (0.06, 0, 0.13), y, C, parent=p)
    cyl("Pato_Pico", 0.02, 0.04, (0.11, 0, 0.125), M["orange"], C, rot=(0, 90, 0), parent=p, r2=0.005, verts=10)
    for s in (-1, 1): sphere(f"Pato_Ojo_{s}", 0.009, (0.09, s * 0.025, 0.145), M["black"], C, parent=p, seg=6, rings=4)
def b_cohete(p):
    cyl("Cohete_Cuerpo", 0.04, 0.2, (0, 0, 0.12), M["white"], C, parent=p, verts=16)
    cyl("Cohete_Punta", 0.04, 0.08, (0, 0, 0.26), M["red"], C, parent=p, r2=0.0, verts=16)
    cyl("Cohete_Ventana", 0.018, 0.01, (0.04, 0, 0.15), M["n_cyan"], C, rot=(0, 90, 0), parent=p, verts=12)
    for k in range(3):
        o = box(f"Cohete_Aleta_{k}", (0.06, 0.008, 0.06), (0, 0, 0.04), M["red"], C, parent=p, rot=(0, 0, k * 120))
        o.location = (0.045 * math.cos(R(k * 120)), 0.045 * math.sin(R(k * 120)), 0.04)
def b_lapiz(p):
    cyl("Lapiz_Cuerpo", 0.025, 0.3, (0, 0, 0.17), M["yellow"], C, parent=p, verts=6, smooth=False, rot=(0, 0, 0))
    cyl("Lapiz_Punta", 0.025, 0.05, (0, 0, 0.345), M["skin"], C, parent=p, verts=6, r2=0.004, smooth=False)
    cyl("Lapiz_Borrador", 0.025, 0.03, (0, 0, 0.005), M["pink"], C, parent=p, verts=12)
    p.rotation_euler = (R(-12), 0, 0)
def b_gafas(p):
    for s in (-1, 1): torus(f"Gafas_Lente_{s}", 0.035, 0.007, (0.0, s * 0.045, 0.05), M["n_pink"], C, rot=(0, 90, 0), parent=p, mseg=6, seg=20)
    cyl("Gafas_Puente", 0.005, 0.03, (0, 0, 0.055), M["n_pink"], C, rot=(90, 0, 0), parent=p, verts=6)
def b_trofeo(p):
    g = M["gold"]
    box("Trofeo_Base", (0.12, 0.12, 0.05), (0, 0, 0.025), M["black"], C, parent=p, bevel=0.006)
    cyl("Trofeo_Pie", 0.015, 0.08, (0, 0, 0.09), g, C, parent=p, verts=10)
    cyl("Trofeo_Copa", 0.07, 0.12, (0, 0, 0.19), g, C, parent=p, r2=0.035, verts=20, rot=(180, 0, 0))
    for s in (-1, 1): torus(f"Trofeo_Asa_{s}", 0.035, 0.007, (0, s * 0.075, 0.2), g, C, rot=(90, 0, 0), parent=p, mseg=6, seg=16)
def b_consola(p):
    box("Consola_Cuerpo", (0.03, 0.11, 0.17), (0, 0, 0.09), M["purple"], C, parent=p, bevel=0.012)
    plane("Consola_Pantalla", 0.08, 0.065, (0.016, 0, 0.12), mat_img("Pantalla_Consola", "cab1_screen.png", emissive=1.2), C, rot=(90, 0, 90), parent=p)
    cyl("Consola_Cruz", 0.012, 0.01, (0.017, -0.03, 0.05), M["black"], C, rot=(0, 90, 0), parent=p, verts=4, smooth=False)
    for k in range(2): cyl(f"Consola_Boton_{k}", 0.008, 0.01, (0.017, 0.02 + k * 0.02, 0.05 + k * 0.01), M["n_red"], C, rot=(0, 90, 0), parent=p, verts=10)
    p.rotation_euler = (0, R(-10), 0)
def b_saturnino(p):
    sphere("Saturnino_Planeta", 0.09, (0, 0, 0.1), M["orange"], C, parent=p)
    torus("Saturnino_Anillo", 0.13, 0.012, (0, 0, 0.1), M["n_cyan"], C, rot=(15, 0, 0), parent=p, mseg=6)
    for s in (-1, 1): sphere(f"Saturnino_Ojo_{s}", 0.015, (0.08, s * 0.03, 0.12), M["black"], C, parent=p, seg=8, rings=4)
def b_dado(p):
    box("Dado_Cubo", (0.1, 0.1, 0.1), (0, 0, 0.05), M["white"], C, parent=p, bevel=0.012, rot=(0, 0, 15))
    for (yy, zz) in ((-0.025, 0.075), (0, 0.05), (0.025, 0.025)):
        sphere(f"Dado_Punto_{yy}", 0.009, (0.05, yy, zz), M["black"], C, parent=p, seg=8, rings=4)
def b_balon(p):
    sphere("Balon_Premio", 0.08, (0, 0, 0.08), ball, C, parent=p)

PRIZES = [  # (nombre, costo, constructor) — de barato (abajo) a caro (arriba)
    ("Rubik", 50, b_rubik), ("Lapiz", 50, b_lapiz), ("Dado", 50, b_dado),
    ("Yoyo", 80, b_yoyo), ("Gafas", 80, b_gafas), ("Pato", 120, b_pato),
    ("Cohete", 200, b_cohete), ("Balon", 200, b_balon), ("Oso", 300, b_oso),
    ("Saturnino", 500, b_saturnino), ("Consola", 750, b_consola), ("Trofeo", 1000, b_trofeo),
]
for idx, (nm, cost, fn) in enumerate(PRIZES):
    shelf = idx // 3; slot = idx % 3
    prize(nm, cost, -5.68, -4.0 + slot * 1.0, 0.513 + shelf * 0.5, fn)

# --- nevera ---
NV = empty("Nevera", (-5.55, -0.65, 0), C)
box("S_Nevera_Cuerpo", (0.08, 0.78, 1.95), (-0.36, 0, 0.975), M["red"], C, parent=NV, bevel=0.02)
for yy in (-0.35, 0.35):
    box(f"S_Nevera_Lado_{yy}", (0.8, 0.08, 1.95), (0, yy, 0.975), M["red"], C, parent=NV, bevel=0.02)
box("Nevera_Techo", (0.8, 0.78, 0.2), (0, 0, 1.85), M["red"], C, parent=NV, bevel=0.02)
box("Nevera_Piso", (0.8, 0.78, 0.15), (0, 0, 0.075), M["red"], C, parent=NV, bevel=0.02)
box("Nevera_Interior", (0.02, 0.62, 1.6), (-0.31, 0, 0.95), mat("Nevera_Luz", (0.85, 0.95, 1.0), 0.3, 0, (0.6, 0.85, 1.0), 1.2), C, parent=NV)
plane("Nevera_Letrero", 0.76, 0.19, (0.402, 0, 1.85), mat_img("Nevera_Letrero", "fridge_header.png", emissive=1.5), C, rot=(90, 0, 90), parent=NV)
lima = mat_img("Lata_Lima", "can_lima.png", rough=0.3, metal=0.3)
for k, z in enumerate((0.35, 0.75, 1.15, 1.55)):
    box(f"Nevera_Repisa_{k}", (0.62, 0.62, 0.015), (0.08, 0, z), M["chrome"], C, parent=NV)
    for j in range(5):
        for r in range(1 if LOWPOLY else 2):
            cyl(f"Nevera_Lata_{k}_{j}_{r}", 0.032, 0.12, (0.0 + r * 0.12 + 0.12, -0.24 + j * 0.12, z + 0.068),
                canm if (j + k) % 2 == 0 else lima, C, parent=NV, verts=12, cap_mat=None if LOWPOLY else M["chrome"])
HG = empty("Nevera_Bisagra", (0.41, -0.38, 0), C, parent=NV)
box("Fridge_Door", (0.03, 0.74, 1.78), (0.0, 0.37, 0.98), M["glass"], C, parent=HG)
for nm, pts in (("Puerta_Marco_Nevera", [(0.0, 0.01, 0.09), (0.0, 0.73, 0.09), (0.0, 0.73, 1.87), (0.0, 0.01, 1.87)]),):
    tube(nm, pts, 0.018, M["red"], C, parent=HG, cyclic=True)
cyl("Fridge_Handle", 0.015, 0.55, (0.05, 0.66, 1.1), M["chrome"], C, parent=HG, verts=10)

# --- máquina de cambio junto a la puerta ---
CM = empty("Maquina_Cambio", (1.9, -4.7, 0), C)
box("Cambio_Cuerpo", (0.6, 0.45, 1.6), (0, 0, 0.8), M["yellow"], C, parent=CM, bevel=0.03)
plane("Cambio_Monedero", 0.3, 0.3, (0, -0.226, 1.0), mat_img("Puerta_Monedas", "coin_door.png"), C, parent=CM)
text_mesh("Cambio_Texto", "FICHAS", (0, -0.23, 1.38), 0.1, M["red"], C, parent=CM, extrude=0.008)
box("Cambio_Bandeja", (0.3, 0.1, 0.08), (0, -0.25, 0.45), M["chrome"], C, parent=CM)
CB = empty("Caneca", (-1.4, -4.6, 0), C)
cyl("Caneca_Cuerpo", 0.2, 0.7, (0, 0, 0.35), M["teal"], C, parent=CB, verts=20, r2=0.22)
torus("Caneca_Borde", 0.22, 0.015, (0, 0, 0.7), M["chrome"], C, parent=CB, mseg=6)

# marcador grande en la pared del fondo
C = coll("01_Arquitectura")
box("Scoreboard_Grande_Marco", (1.9, 0.06, 0.62), (4.6, y1 - 0.04, 2.85), M["chrome"], C, bevel=0.015)
box("Scoreboard_Big", (1.8, 0.04, 0.52), (4.6, y1 - 0.08, 2.85), M["led"], C)

# =====================================================================
# LUCES, CÁMARA, XR
# =====================================================================
L = coll("08_Luces")
def light(name, kind, loc, color, energy, size=0.5, rot=None):
    ld = bpy.data.lights.new(name, kind); ld.color = color; ld.energy = energy
    if kind == "AREA": ld.size = size
    o = bpy.data.objects.new(name, ld); L.objects.link(o); o.location = loc
    if rot: o.rotation_euler = [R(a) for a in rot]
    return o
light("Luz_Techo_Centro", "AREA", (0, 0, H - 0.1), (0.85, 0.75, 1.0), 350, 5)
light("Luz_Rosa_Izq", "POINT", (-4, 2.2, 2.6), (1, 0.35, 0.8), 140)
light("Luz_Cian_Der", "POINT", (4.4, 0.2, 2.6), (0.3, 0.9, 1), 140)
light("Luz_Recepcion", "POINT", (-4.0, -3.0, 2.8), (1, 0.85, 0.65), 140)
light("Luz_Maquinitas", "AREA", (0, 3.2, 3.3), (0.8, 0.5, 1.0), 150, 3)
light("Luz_Nevera", "POINT", (-5.4, -0.65, 1.2), (0.7, 0.9, 1.0), 25)
light("Luz_Rueda", "SPOT", (0, -1.5, 3.4), (1, 0.9, 0.7), 250, rot=(40, 0, 0))

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
bpy.context.scene.collection.objects.link(cam)
cam.location = (0, -3.8, 1.6); cam.rotation_euler = (R(90), 0, 0); cam.data.lens = 18
bpy.context.scene.camera = cam
X = empty("XR_Rig_Origen", (0, -3.8, 0), bpy.context.scene.collection)
G = empty("GameManager", (0, 0, 0), bpy.context.scene.collection)

# componentes de Needle (se pierden al borrar la escena, así que se vuelven a poner)
try:
    cu = [m for k, m in sys.modules.items() if k.endswith("component_utils") and "Needle" in k][0]
    k = cu.addComponentToObject(G, "WebXR"); c = getattr(G, k)
    c.createARButton = False; c.createSendToQuestButton = True; c.useDefaultControls = True
    c.showControllerModels = True; c.showHandModels = True
    cu.addComponentToObject(X, "XRRig")
except Exception as e:
    print("No se pudieron agregar componentes de Needle:", e)
print("ESCENA LISTA:", len(bpy.data.objects), "objetos")

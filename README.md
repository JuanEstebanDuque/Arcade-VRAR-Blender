# PIXEL 84 — Arcade VR (Parcial 3 VR-AR)

## Estructura
- `Arcade.blend` — escena en Blender (1 unidad = 1 m). Al guardar (Ctrl+S) se exporta sola a `web/assets/scene.glb`.
- `blender_scripts/build_scene.py` — genera el bloqueo del cuarto desde cero. OJO: borra todo lo que haya en la escena.
- `web/` — proyecto Needle Engine. Las interacciones están en `web/src/scripts/arcade/`.

## Convenciones de nombres (el código las lee, no las cambien sin avisar)
| Prefijo / nombre | Qué hace en la web |
|---|---|
| `S_*` | Colisionador estático (paredes, mostradores, muebles) |
| `FLOOR` | Piso: colisionador y único sitio donde se puede teletransportar |
| `REF_*` | Se oculta en la web (referencia humana de 1,70 m) |
| `Scoreboard`, `Scoreboard_Big` | Marcadores LED de tickets |
| `Screen_*` | Pantallas de maquinitas (animación por shader, pendiente) |
| `Mole_1..9` | Topos |
| `Ball_*`, `Hoop_Trigger` | Basket |
| `Wheel_Disk`, `Wheel_Lever_Pivot` | Rueda y palanca |
| `Gun_*`, `Gun_*_Muzzle` | Pistolas de la galería de tiro |
| `Nevera_Bisagra`, `Fridge_Door` | Nevera |

## Probar
- En el PC: https://localhost:3000 (aceptar el aviso de certificado). Tecla **T** = +10 tickets, **R** = reiniciar.
- En el Quest: misma red WiFi, abrir https://<IP-del-PC>:3000 en el navegador del Quest y aceptar el aviso.

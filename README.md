# PIXEL 84 — Arcade VR (Parcial 3 VR-AR)

Arcade ochentero en Realidad Virtual hecho con Blender + Needle Engine (WebXR).

## Estructura
- `Arcade.blend`: escena en Blender (1 unidad = 1 m). Al guardar (Ctrl+S) se exporta sola a `web/assets/scene.glb`.
- `blender_scripts/build_scene.py`: genera **toda** la escena desde cero. Usa `lib.py` (utilidades de modelado). OJO: borra lo que haya en la escena antes de construir.
- `blender_scripts/gen_textures.py`: genera todas las texturas originales de `textures/` (personajes, pósters, alfombra, ruleta, dianas, etc.). Se corre con Python + Pillow.
- `blender_scripts/build_scene_v1_boceto.py`: versión inicial (boceto) de la escena, para comparar el antes y el después.
- `blender_scripts/render_previews.py`: renders de revisión que quedan en `renders/`.
- `textures/`: texturas originales (sin derechos de terceros).
- `web/`: proyecto Needle Engine. La lógica está en `web/src/scripts/arcade/`.

## Convenciones de nombres (el código las lee: no los cambien sin avisar)
| Nombre en Blender | Qué hace en la web |
|---|---|
| `S_*` | Colisionador estático (paredes, mostradores, muebles) |
| `FLOOR` | Piso: colisionador y único sitio donde se puede teletransportar |
| `REF_*` | Se oculta en la web (referencia humana de 1,70 m) |
| `Scoreboard`, `Scoreboard_Big` | Marcadores LED de tickets |
| `Screen_*` | Pantallas de las maquinitas |
| `Wheel_Drum`, `Wheel_Lever_Pivot`, `Wheel_Lever_Grip`, `Wheel_Display`, `Wheel_Bulb_*` | Rueda Cósmica (funciona) |
| `Mole_1..9`, `Mallet_1..2`, `Mole_Display` | Golpea el topo |
| `Ball_1..4`, `Hoop_Trigger`, `Basket_Display` | Mini basket |
| `Gun_1..2`, `Gun_*_Muzzle`, `Target_1..8`, `Can_1..6` | Galería de tiro |
| `Prize_<costo>_<nombre>` | Premios de la vitrina |
| `Nevera_Bisagra`, `Fridge_Door` | Nevera |

## Probar
- En el PC: https://localhost:3000 (aceptar el aviso de certificado). Tecla **T** = +10 tickets, **R** = reiniciar. Clic en la palanca de la rueda = girar.
- En el Quest: misma red WiFi, abrir `https://<IP-del-PC>:3000` en el navegador del Quest y aceptar el aviso.

## Estado
- [x] Escena detallada, sistema de tickets persistente, teletransporte
- [x] Rueda Cósmica (palanca arrastrable), topo, galería de tiro, nevera, canje de premios, maquinitas jugables
- [x] Caminar en PC (WASD + arrastrar para mirar) y agarrar/usar/soltar en PC y VR
- [ ] Ajustar el lanzamiento del balón en el basket
- [ ] Optimización (unir mallas estáticas + luz horneada) para 72 FPS en Quest

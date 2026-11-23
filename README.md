# PIXEL 84 — Arcade VR (Parcial 3 VR-AR)

Arcade ochentero en Realidad Virtual hecho con Blender + Needle Engine (WebXR).

- **Jugar (PC o Meta Quest):** https://pixel84-arcade-1nxw5w1z5iy2-1uqoc0.needle.run/
- **Equipo:** Juan Esteban Duque Taborda (arte 3D y escena) · Sebastián Escobar Marín (integración y publicación)

## Estructura
- `Arcade.blend`: escena en Blender (1 unidad = 1 m). Al guardar (Ctrl+S) se exporta sola a `web/assets/scene.glb`.
- `blender_scripts/build_scene.py`: genera **toda** la escena desde cero. Usa `lib.py` (utilidades de modelado). OJO: borra lo que haya en la escena antes de construir.
- `blender_scripts/gen_textures.py`: genera todas las texturas originales de `textures/` (personajes, pósters, alfombra, ruleta, dianas, etc.). Se corre con Python + Pillow.
- `blender_scripts/build_scene_v1_boceto.py`: versión inicial (boceto) de la escena, para comparar el antes y el después.
- `blender_scripts/optimize.py`: une las mallas estáticas y marca qué se hornea. Para regenerar la versión optimizada en Blender: `LOWPOLY = True`, correr `build_scene.py`, luego `optimize.py` y hornear el lightmap desde el panel de Needle.
- `Arcade_sin_optimizar.blend`: copia de la escena con detalle antes de optimizar.
- `blender_scripts/render_previews.py`: renders de revisión que quedan en `renders/`.
- `textures/`: texturas originales (sin derechos de terceros).
- `web/`: proyecto Needle Engine. La lógica está en `web/src/scripts/arcade/`.
- `Images/`: material del Behance (capturas de los juegos, horneado, optimización, videos antes/después y video del profe en el visor).
- `Images/behance/`: video POV de 2 min, clips y GIF de las interacciones, QR, portada e imágenes de referencia del caso de estudio.

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
- [x] Mini basket con física (lanzamiento con ayuda de puntería)
- [x] Optimización: modo low-poly, mallas estáticas unidas y luz horneada (lightmap 2048). Ver `renders/optimizacion/`
- [x] Ajustes tras la prueba en Quest: pistolas y mazos orientados con el control, menos caída de FPS al disparar, escena dividida en 6 zonas para no dibujar lo que no se ve
- [x] Contador de tickets fijo (PC y VR), carteles "¡TÓCALA!" en las maquinitas y pantalla de bienvenida bloqueante de 10 s
- [x] Premios canjeados van directo a la mano (PC y VR) y se pueden girar (PC: clic derecho + arrastrar / rueda; VR: joystick)
- [x] Publicado en Needle Cloud

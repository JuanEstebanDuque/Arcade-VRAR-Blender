import { Context } from "@needle-tools/engine";
import { Box3, CanvasTexture, DoubleSide, Mesh, MeshBasicMaterial, Object3D, PlaneGeometry, SRGBColorSpace, Vector3 } from "three";

/** Cartel plano con texto (se dibuja una sola vez). */
function sign(lines: { t: string; c: string; s: number }[], w: number, h: number, px = 512) {
    const canvas = document.createElement("canvas"); canvas.width = px; canvas.height = Math.round(px * h / w);
    const g = canvas.getContext("2d")!;
    g.fillStyle = "rgba(10,0,30,0.88)"; g.fillRect(0, 0, canvas.width, canvas.height);
    g.strokeStyle = "#ff3cac"; g.lineWidth = 8; g.strokeRect(4, 4, canvas.width - 8, canvas.height - 8);
    g.textAlign = "center"; g.textBaseline = "middle";
    const total = lines.reduce((a, l) => a + l.s * 1.25, 0); let y = (canvas.height - total) / 2;
    for (const l of lines) { g.font = `bold ${l.s}px sans-serif`; g.fillStyle = l.c; y += l.s * 0.625; g.fillText(l.t, canvas.width / 2, y); y += l.s * 0.625; }
    const tex = new CanvasTexture(canvas); tex.colorSpace = SRGBColorSpace;
    return new Mesh(new PlaneGeometry(w, h), new MeshBasicMaterial({ map: tex, toneMapped: false, side: DoubleSide }));
}

/** Carteles "¡TÓCALA!" encima de las maquinitas (la bienvenida ahora es la pantalla de inicio). */
export function placeSigns(ctx: Context, byName: Map<string, Object3D>) {
    const center = new Vector3(0, 1.6, 0);
    const lookAtRoom = (m: Mesh, at: Vector3) => { m.position.copy(at); m.lookAt(new Vector3(center.x, at.y, center.z)); };
    for (const n of ["Arcade_1", "Arcade_2", "Arcade_3", "Arcade_4", "Arcade_5", "Carreras_Moderna", "Baile_Moderna"]) {
        const o = byName.get(n); if (!o) continue;
        const b = new Box3().setFromObject(o); const c = b.getCenter(new Vector3());
        const m = sign([{ t: "¡TÓCALA!", c: "#ffd728", s: 64 }, { t: "minijuego · 2 a 8 tickets", c: "#ffffff", s: 34 }], 0.62, 0.22);
        // al frente y arriba de la máquina, mirando al salón
        const toRoom = center.clone().sub(c).setY(0).normalize();
        lookAtRoom(m, new Vector3(c.x, b.max.y + 0.16, c.z).add(toRoom.multiplyScalar(0.25)));
        ctx.scene.add(m);
    }
}

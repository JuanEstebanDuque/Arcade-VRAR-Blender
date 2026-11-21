import { Context } from "@needle-tools/engine";
import { CanvasTexture, Mesh, MeshBasicMaterial, PlaneGeometry, Quaternion, SRGBColorSpace, Vector3 } from "three";
import { Tickets } from "./tickets";
import { inXR } from "./state";

/**
 * Contador de tickets siempre visible.
 * PC: recuadro fijo arriba a la derecha. VR: pequeño panel arriba a la derecha de la vista.
 * Muestra "+N" un momento cada vez que ganas tickets.
 */
export class TicketHud {
    private el: HTMLDivElement;
    private canvas = document.createElement("canvas");
    private tex: CanvasTexture;
    private panel: Mesh;
    private gain = 0; private gainTime = 0; private dirty = true;

    constructor(private ctx: Context) {
        const d = document.createElement("div");
        d.style.cssText = "position:fixed;right:14px;top:14px;z-index:50;padding:10px 16px;border-radius:12px;" +
            "background:rgba(10,0,30,.78);color:#fff;font:700 15px/1.3 'Courier New',monospace;pointer-events:none;" +
            "border:1px solid #00e5ff;box-shadow:0 0 12px #00e5ff66;text-align:right";
        document.body.appendChild(d); this.el = d;
        this.canvas.width = 256; this.canvas.height = 96;
        this.tex = new CanvasTexture(this.canvas); this.tex.colorSpace = SRGBColorSpace;
        this.panel = new Mesh(new PlaneGeometry(0.16, 0.06), new MeshBasicMaterial({ map: this.tex, transparent: true, toneMapped: false, depthTest: false }));
        this.panel.renderOrder = 999; this.panel.visible = false; this.panel.frustumCulled = false;
        ctx.scene.add(this.panel);
        Tickets.onChange((_v, delta) => { if (delta > 0) { this.gain = delta; this.gainTime = 1.6; } this.dirty = true; });
    }

    private draw() {
        const v = Tickets.value;
        const plus = this.gainTime > 0 ? `<span style="color:#3cff7a">+${this.gain} </span>` : "";
        this.el.innerHTML = `<span style="color:#00e5ff;font-size:12px">TUS TICKETS</span><br>${plus}<span style="color:#ff3cac;font-size:24px">${v}</span>` +
            `<br><span style="color:#ffd728;font-size:11px">Canjéalos en PREMIOS</span>`;
        const g = this.canvas.getContext("2d")!;
        g.clearRect(0, 0, 256, 96);
        g.fillStyle = "rgba(10,0,30,0.8)"; g.fillRect(0, 0, 256, 96);
        g.strokeStyle = "#00e5ff"; g.lineWidth = 4; g.strokeRect(2, 2, 252, 92);
        g.textAlign = "right"; g.fillStyle = "#00e5ff"; g.font = "bold 20px monospace"; g.fillText("TICKETS", 240, 28);
        g.fillStyle = "#ff3cac"; g.font = "bold 44px monospace"; g.fillText(String(v), 240, 76);
        if (this.gainTime > 0) { g.textAlign = "left"; g.fillStyle = "#3cff7a"; g.font = "bold 28px monospace"; g.fillText(`+${this.gain}`, 14, 70); }
        this.tex.needsUpdate = true;
    }

    update() {
        const dt = this.ctx.time.deltaTime;
        if (this.gainTime > 0) { this.gainTime -= dt; if (this.gainTime <= 0) this.dirty = true; }
        if (this.dirty) { this.dirty = false; this.draw(); }
        const xr = inXR(this.ctx);
        this.el.style.display = xr ? "none" : "block";
        this.panel.visible = xr;
        if (xr) {
            const cam = this.ctx.mainCamera!;
            const q = cam.getWorldQuaternion(new Quaternion());
            this.panel.position.copy(cam.getWorldPosition(new Vector3()).add(new Vector3(0.17, 0.11, -0.55).applyQuaternion(q)));
            this.panel.quaternion.copy(q);
        }
    }
}

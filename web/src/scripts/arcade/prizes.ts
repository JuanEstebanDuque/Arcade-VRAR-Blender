import { Behaviour, BoxCollider, Context, NeedleXRController, PointerEventData, Rigidbody, destroy } from "@needle-tools/engine";
import { Box3, BoxGeometry, Mesh, MeshBasicMaterial, Object3D, Vector3 } from "three";
import { Hands } from "./hand";
import { LedDisplay } from "./screens";
import { Tickets } from "./tickets";
import { sfx } from "./sfx";
import { inXR, isDeskClick, setCursor, Intro } from "./state";

const KEY = "pixel84_prizes";

class PrizeClick extends Behaviour {
    shop!: PrizeShop; key = ""; cost = 0; copy = false;
    onPointerEnter() { if (this.copy) return; if (!inXR(this.context)) setCursor(true); this.shop.hover(this, true); }
    onPointerExit() { setCursor(false); this.shop.hover(this, false); }
    onPointerClick(e: PointerEventData) {
        if (Intro.blocking) return;
        if (this.copy) return;
        if (e.mode === "screen" && !isDeskClick(this.context, e.mode)) return;
        const origin = (e.event as any)?.origin;
        this.shop.buy(this, origin instanceof NeedleXRController ? origin : undefined);
    }
}

/** Vitrina de premios: clic en un premio para canjearlo con tickets. Lo que ganas queda en el mostrador (y se guarda). */
export class PrizeShop {
    prizes = new Map<string, { obj: Object3D; comp: PrizeClick; baseScale: number; basePos: Vector3; anim: number; shake: number; hover: boolean }>();
    won: string[] = [];
    display?: LedDisplay;
    slotBase = new Vector3(); slotAxis = new Vector3(0, 0, 1);
    constructor(private ctx: Context, byName: Map<string, Object3D>) {
        byName.forEach((o, n) => {
            const m = /^Prize_(\d+)_(.+)$/.exec(n); if (!m) return;
            const comp = o.addComponent(PrizeClick); comp.shop = this; comp.cost = +m[1]; comp.key = n;
            this.prizes.set(n, { obj: o, comp, baseScale: o.scale.x, basePos: o.position.clone(), anim: 0, shake: 0, hover: false });
        });
        const top = byName.get("Mostrador_Tope");
        if (top) {
            const b = new Box3().setFromObject(top);
            const size = b.getSize(new Vector3());
            this.slotAxis = size.z > size.x ? new Vector3(0, 0, 1) : new Vector3(1, 0, 0);
            const across = size.z > size.x ? new Vector3(1, 0, 0) : new Vector3(0, 0, 1);
            const c = b.getCenter(new Vector3());
            // fila de premios ganados en el borde del mostrador que da al salón
            const edge = c.clone().add(across.clone().multiplyScalar((size.z > size.x ? size.x : size.z) / 2 - 0.12));
            const len = Math.max(size.x, size.z);
            this.slotBase = edge.add(this.slotAxis.clone().multiplyScalar(-len / 2 + 0.6)).setY(b.max.y);
        }
        const d = byName.get("Tragaticket_Pantalla");
        if (d) { this.display = new LedDisplay(d, 256, 96); this.showBalance(); }
        Tickets.onChange(() => this.showBalance());
        try { this.won = JSON.parse(localStorage.getItem(KEY) || "[]"); } catch { this.won = []; }
        this.won.forEach((n, i) => this.placeCopy(n, i));
        window.addEventListener("keydown", e => { if (e.key === "r" || e.key === "R") this.resetWon(); });
    }

    private showBalance() { this.display?.set(String(Tickets.value), "#ffd728", "TICKETS"); }

    hover(c: PrizeClick, on: boolean) { const p = this.prizes.get(c.key); if (p) p.hover = on; }

    buy(c: PrizeClick, ctrl?: NeedleXRController) {
        const p = this.prizes.get(c.key); if (!p) return;
        if (Tickets.spend(c.cost)) {
            sfx.win(); p.anim = 1;
            this.won.push(c.key);
            try { localStorage.setItem(KEY, JSON.stringify(this.won)); } catch { }
            this.placeCopy(c.key, this.won.length - 1, true, ctrl);
            this.display?.set("¡GRACIAS!", "#00ff88", `-${c.cost}`);
            setTimeout(() => this.showBalance(), 1500);
        } else {
            sfx.buzz(); p.shake = 0.5;
            this.display?.set(`FALTAN ${c.cost - Tickets.value}`, "#ff3c3c", "TICKETS");
            setTimeout(() => this.showBalance(), 1600);
        }
    }

    private copies: Object3D[] = [];
    /** Copia SOLO lo visual del premio (sin componentes), para que no quede ligada al de la vitrina. */
    private cloneVisual(src: Object3D): Object3D {
        const o = (src as Mesh).isMesh ? new Mesh((src as Mesh).geometry, (src as Mesh).material) : new Object3D();
        o.position.copy(src.position); o.quaternion.copy(src.quaternion); o.scale.copy(src.scale);
        for (const ch of src.children) o.add(this.cloneVisual(ch));
        return o;
    }

    /** El premio ganado aparece directo en la mano (PC y VR). Si lo sueltas cae al piso y lo puedes volver a agarrar. */
    private placeCopy(name: string, i: number, toHand = false, ctrl?: NeedleXRController) {
        const p = this.prizes.get(name); if (!p) return;
        const visual = this.cloneVisual(p.obj);
        visual.position.set(0, 0, 0);
        visual.scale.setScalar(p.baseScale * 0.85);
        this.ctx.scene.add(visual); visual.updateMatrixWorld(true);
        const bb = new Box3().setFromObject(visual);
        const size = bb.getSize(new Vector3()), center = bb.getCenter(new Vector3());
        visual.removeFromParent();
        // raíz con cuerpo físico (caja del tamaño del premio); lo visual va adentro, centrado
        const body = new Object3D(); body.name = "Ganado_" + name;
        body.add(visual); visual.position.sub(center);
        // si no va a la mano (premios guardados de antes o en VR), aparece frente al mostrador y cae al piso
        const front = this.slotBase.clone().add(new Vector3(0.7 + (i % 3) * 0.25, 0.4, 0)).add(this.slotAxis.clone().multiplyScalar((i % 5) * 0.3));
        body.position.copy(front);
        this.ctx.scene.add(body);
        body.addComponent(BoxCollider, { size: new Vector3(Math.max(size.x, 0.05), Math.max(size.y, 0.05), Math.max(size.z, 0.05)), center: new Vector3() } as any);
        const rb = body.addComponent(Rigidbody, { mass: 0.4 } as any);
        const g = Hands.register(body, {
            rb,
            desk: { pos: [0.2, -0.2, -0.5], rot: [0, 0, 0] },
            // en VR va en la palma, un poco adelante del control
            hold: { pos: [0, 0.01, -0.07 - Math.max(size.x, size.y, size.z) * 0.4], rot: [0, 0, 0] },
            spin: true,
            // clic con el premio en la mano: lo lanza suavemente hacia donde apuntas
            onUse: (_h, ray) => Hands.release(g, ray.direction.clone().multiplyScalar(2.2).add(new Vector3(0, 1.2, 0))),
        });
        if (toHand) { if (this.ctx.isInXR) Hands.grabXR(g, ctrl); else Hands.grab(g, { kind: "desk" }); }
        this.copies.push(body);
    }

    private resetWon() {
        this.won = []; try { localStorage.removeItem(KEY); } catch { }
        this.copies.forEach(c => { Hands.items = Hands.items.filter(g => g.obj !== c); destroy(c); }); this.copies = [];
    }

    update() {
        const dt = this.ctx.time.deltaTime; const t = this.ctx.time.time;
        this.prizes.forEach(p => {
            let s = p.baseScale;
            if (p.anim > 0) { p.anim = Math.max(0, p.anim - dt * 1.2); s *= 1 + Math.sin(p.anim * Math.PI) * 0.4; p.obj.rotation.y += dt * 12 * p.anim; }
            p.obj.scale.setScalar(s);
            p.obj.position.copy(p.basePos);
            if (p.shake > 0) { p.shake -= dt; p.obj.position.z += Math.sin(t * 60) * 0.02 * (p.shake / 0.5); }
            if (p.anim > 0) p.obj.position.y += Math.sin(p.anim * Math.PI) * 0.12;
        });
    }
}

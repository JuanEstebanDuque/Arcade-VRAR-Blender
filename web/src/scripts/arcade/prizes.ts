import { Behaviour, BoxCollider, Context, PointerEventData, Rigidbody, destroy } from "@needle-tools/engine";
import { Box3, BoxGeometry, Mesh, MeshBasicMaterial, Object3D, Vector3 } from "three";
import { Hands } from "./hand";
import { LedDisplay } from "./screens";
import { Tickets } from "./tickets";
import { sfx } from "./sfx";
import { inXR, isDeskClick, setCursor } from "./state";

const KEY = "pixel84_prizes";

class PrizeClick extends Behaviour {
    shop!: PrizeShop; key = ""; cost = 0; copy = false;
    onPointerEnter() { if (this.copy) return; if (!inXR(this.context)) setCursor(true); this.shop.hover(this, true); }
    onPointerExit() { setCursor(false); this.shop.hover(this, false); }
    onPointerClick(e: PointerEventData) {
        if (this.copy) return;
        if (e.mode === "screen" && !isDeskClick(this.context, e.mode)) return;
        this.shop.buy(this);
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

    buy(c: PrizeClick) {
        const p = this.prizes.get(c.key); if (!p) return;
        if (Tickets.spend(c.cost)) {
            sfx.win(); p.anim = 1;
            this.won.push(c.key);
            try { localStorage.setItem(KEY, JSON.stringify(this.won)); } catch { }
            this.placeCopy(c.key, this.won.length - 1);
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

    /** El premio ganado aparece sobre el mostrador, con física: se apoya bien y se puede agarrar como un balón. */
    private placeCopy(name: string, i: number) {
        const p = this.prizes.get(name); if (!p) return;
        const visual = this.cloneVisual(p.obj);
        visual.position.set(0, 0, 0);
        visual.scale.setScalar(p.baseScale * 0.85);
        this.ctx.scene.add(visual); visual.updateMatrixWorld(true);
        const bb = new Box3().setFromObject(visual);
        const size = bb.getSize(new Vector3()), center = bb.getCenter(new Vector3());
        visual.removeFromParent();
        // caja invisible que hace de cuerpo físico; lo visual va adentro, centrado
        const body = new Mesh(new BoxGeometry(Math.max(size.x, 0.04), Math.max(size.y, 0.04), Math.max(size.z, 0.04)),
            new MeshBasicMaterial({ visible: false }));
        body.name = "Ganado_" + name;
        body.add(visual); visual.position.sub(center);
        const col = i % 6, row = Math.floor(i / 6);
        const pos = this.slotBase.clone().add(this.slotAxis.clone().multiplyScalar(col * 0.32));
        pos.add(new Vector3(-row * 0.22, size.y / 2 + 0.02, 0));
        body.position.copy(pos);
        this.ctx.scene.add(body);
        BoxCollider.add(body, { rigidbody: true });
        const rb = body.getComponent(Rigidbody)!;
        rb.mass = 0.4;
        Hands.register(body, {
            rb,
            desk: { pos: [0.2, -0.2, -0.5], rot: [0, 0, 0] },
            // clic con el premio en la mano: lo lanza suavemente hacia donde apuntas
            onUse: (_h, ray) => { const g = Hands.desk; if (g) Hands.release(g, ray.direction.clone().multiplyScalar(2.2).add(new Vector3(0, 1.2, 0))); },
        });
        this.copies.push(body);
    }

    private resetWon() {
        this.won = []; try { localStorage.removeItem(KEY); } catch { }
        this.copies.forEach(c => { Hands.items = Hands.items.filter(g => g.obj !== c); destroy(c); }); this.copies = [];
    }

    update() {
        const dt = this.ctx.time.deltaTime; const t = this.ctx.time.time;
        this.prizes.forEach(p => {
            let s = p.baseScale * (p.hover ? 1.12 : 1);
            if (p.anim > 0) { p.anim = Math.max(0, p.anim - dt * 1.2); s *= 1 + Math.sin(p.anim * Math.PI) * 0.4; p.obj.rotation.y += dt * 12 * p.anim; }
            p.obj.scale.setScalar(s);
            p.obj.position.copy(p.basePos);
            if (p.shake > 0) { p.shake -= dt; p.obj.position.z += Math.sin(t * 60) * 0.02 * (p.shake / 0.5); }
            if (p.anim > 0) p.obj.position.y += Math.sin(p.anim * Math.PI) * 0.12;
        });
    }
}

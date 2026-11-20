import { Behaviour, Context, PointerEventData } from "@needle-tools/engine";
import { Object3D, Quaternion, Ray, Vector3, Euler } from "three";
import { Hands, Grabbable } from "./hand";
import { LedDisplay } from "./screens";
import { Tickets } from "./tickets";
import { sfx } from "./sfx";
import { isDeskClick, inXR, setCursor } from "./state";
import { raySphere, worldPos } from "./util";

const ROUND = 30;      // segundos por partida
const DROP = 0.17;     // cuánto se esconde el topo

type Mole = { obj: Object3D; head: Object3D; baseY: number; up: number; state: "down" | "up" | "hit"; timer: number; squash: number };

class MoleClick extends Behaviour {
    game!: MoleGame; index = -1;
    onPointerEnter() { if (!inXR(this.context)) setCursor(true); }
    onPointerExit() { setCursor(false); }
    onPointerClick(e: PointerEventData) {
        if (!isDeskClick(this.context, e.mode) && e.mode === "screen") return;
        if (this.index < 0) this.game.start(); else this.game.whack(this.index);
    }
}

/** Golpea el topo: 30 segundos, cada topo golpeado = 2 tickets, bono al final. */
export class MoleGame {
    moles: Mole[] = [];
    mallets: Grabbable[] = [];
    display?: LedDisplay;
    active = false; time = 0; score = 0; spawn = 0; attract = 0;
    private prevHands = new Map<any, Vector3>();

    constructor(private ctx: Context, byName: Map<string, Object3D>) {
        for (let k = 1; k <= 9; k++) {
            const o = byName.get("Mole_" + k); const head = byName.get(`Mole_${k}_Cabeza`);
            if (!o || !head) continue;
            const m: Mole = { obj: o, head, baseY: o.position.y, up: 0, state: "down", timer: 0, squash: 0 };
            this.moles.push(m);
            const c = o.addComponent(MoleClick); c.game = this; c.index = this.moles.length - 1;
        }
        for (const n of ["Topo_Torre", "Mole_Display"]) {
            const o = byName.get(n); if (o) { const c = o.addComponent(MoleClick); c.game = this; c.index = -1; }
        }
        const d = byName.get("Mole_Display");
        if (d) { this.display = new LedDisplay(d); this.display.set("GOLPEA", "#ffd728", "TOCA UN TOPO PARA JUGAR"); }
        for (let i = 1; i <= 2; i++) {
            const mt = byName.get("Mallet_" + i); if (!mt) continue;
            const g = Hands.register(mt, {
                returnHome: true,
                desk: { pos: [0.28, -0.3, -0.55], rot: [0, 90, 0] },
                hold: { pos: [0, 0, -0.04], rot: [0, 90, 0] },
                onUse: (_h, ray) => this.deskSwing(g, ray),
            });
            this.mallets.push(g);
        }
    }

    start() {
        if (this.active) return;
        this.active = true; this.time = ROUND; this.score = 0; this.spawn = 0.5;
        sfx.coin();
        this.display?.set(`${ROUND}`, "#ff3cac", "PUNTOS: 0");
    }

    whack(i: number) {
        const m = this.moles[i];
        if (!this.active) { if (m.state === "up") this.start(); else this.start(); return; }
        if (m.state !== "up") return;
        m.state = "hit"; m.timer = 0.35; m.squash = 1;
        this.score++;
        Tickets.add(2);
        sfx.hit();
    }

    /** En PC: clic con el mazo en la mano = martillazo hacia donde apunta el mouse. */
    private swing = 0; private swingG?: Grabbable;
    private deskSwing(g: Grabbable, ray: Ray) {
        this.swing = 0.25; this.swingG = g;
        let best = -1, bt = 1e9;
        this.moles.forEach((m, i) => {
            const t = raySphere(ray.origin, ray.direction, worldPos(m.head), 0.1);
            if (t !== null && t < bt) { bt = t; best = i; }
        });
        if (best >= 0) this.whack(best); else sfx.door();
    }

    update() {
        const dt = this.ctx.time.deltaTime;
        if (this.active) {
            this.time -= dt;
            this.spawn -= dt;
            if (this.spawn <= 0) {
                const free = this.moles.filter(m => m.state === "down" && m.up < 0.05);
                if (free.length) { const m = free[Math.floor(Math.random() * free.length)]; m.state = "up"; m.timer = 0.9 + Math.random() * 0.8; sfx.pop(); }
                this.spawn = Math.max(0.35, 0.95 - (ROUND - this.time) * 0.018) * (0.7 + Math.random() * 0.6);
            }
            this.display?.set(`${Math.ceil(Math.max(0, this.time))}`, "#ff3cac", `PUNTOS: ${this.score}`);
            if (this.time <= 0) this.finish();
        } else {
            // modo atracción: de vez en cuando se asoma uno para invitar a jugar
            this.attract -= dt;
            if (this.attract <= 0) {
                const m = this.moles[Math.floor(Math.random() * this.moles.length)];
                if (m && m.state === "down") { m.state = "up"; m.timer = 0.9; }
                this.attract = 2.5 + Math.random() * 2;
            }
        }
        for (const m of this.moles) {
            if (m.state === "up") { m.timer -= dt; if (m.timer <= 0) m.state = "down"; }
            if (m.state === "hit") { m.timer -= dt; if (m.timer <= 0) m.state = "down"; }
            const target = m.state === "up" ? 1 : 0;
            const speed = m.state === "hit" ? 14 : 9;
            m.up += (target - m.up) * Math.min(1, dt * speed);
            m.squash = Math.max(0, m.squash - dt * 3);
            m.obj.position.y = m.baseY - DROP * (1 - m.up);
            m.obj.scale.set(1 + 0.25 * m.squash, 1 - 0.4 * m.squash, 1 + 0.25 * m.squash);
        }
        // animación del martillazo en PC
        if (this.swing > 0 && this.swingG && this.swingG.holder?.kind === "desk") {
            this.swing = Math.max(0, this.swing - dt);
            const k = Math.sin((1 - this.swing / 0.25) * Math.PI);
            this.swingG.obj.worldQuaternion = this.swingG.obj.worldQuaternion.multiply(new Quaternion().setFromEuler(new Euler(0, 0, -k * 1.1)));
        }
        if (inXR(this.ctx)) this.xrHits();
    }

    /** En VR: golpear con el mazo (o la mano) moviéndolo hacia abajo sobre un topo. */
    private xrHits() {
        const xr = this.ctx.xr; if (!xr) return;
        const dt = Math.max(1e-3, this.ctx.time.deltaTime);
        const hitters: { key: any; p: Vector3 }[] = [];
        for (const c of xr.controllers) hitters.push({ key: c, p: c.gripWorldPosition.clone() });
        for (const g of this.mallets) if (g.holder) {
            const head = g.obj.children.find(ch => ch.name.endsWith("_Cabeza"));
            if (head) hitters.push({ key: g, p: worldPos(head) });
        }
        for (const h of hitters) {
            const prev = this.prevHands.get(h.key); this.prevHands.set(h.key, h.p);
            if (!prev) continue;
            const vy = (h.p.y - prev.y) / dt;
            if (vy > -0.6) continue;
            this.moles.forEach((m, i) => { if (m.state === "up" && h.p.distanceTo(worldPos(m.head)) < 0.11) this.whack(i); });
            if (!this.active) this.moles.forEach(m => { if (h.p.distanceTo(worldPos(m.head)) < 0.11) this.start(); });
        }
    }

    private finish() {
        this.active = false;
        const bonus = this.score >= 20 ? 30 : this.score >= 12 ? 15 : 0;
        if (bonus) { Tickets.add(bonus); sfx.win(); } else sfx.buzz();
        this.display?.set(`FIN: ${this.score}`, "#00ff88", bonus ? `BONO +${bonus} TICKETS` : "TOCA PARA JUGAR OTRA VEZ");
        this.moles.forEach(m => { if (m.state !== "hit") m.state = "down"; });
    }
}

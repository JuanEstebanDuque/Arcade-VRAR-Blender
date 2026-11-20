import { Behaviour, Context, NeedleXREventArgs, PointerEventData } from "@needle-tools/engine";
import { Color, Material, Mesh, MeshStandardMaterial, Object3D, Vector3 } from "three";
import { LedDisplay } from "./screens";
import { Tickets } from "./tickets";
import { sfx } from "./sfx";
import { Desk, inXR, setCursor } from "./state";

// Deben coincidir con blender_scripts/gen_textures.py (textura wheel_drum.png, de arriba hacia abajo)
const SEGMENTS = [10, 25, 5, 50, 10, 100, 20, 5, 250, 15, 30, 500];
// Probabilidad relativa de cada segmento: los premios grandes salen poco
const WEIGHTS  = [20, 10, 20, 8, 20, 5, 14, 20, 2, 15, 12, 1];
const TAU = Math.PI * 2;

function pickSegment(): number {
    const total = WEIGHTS.reduce((a, b) => a + b, 0);
    let r = Math.random() * total;
    for (let i = 0; i < WEIGHTS.length; i++) { r -= WEIGHTS[i]; if (r <= 0) return i; }
    return 0;
}

/**
 * Rueda Cósmica: al bajar la palanca (clic, gatillo apuntando o empujándola con la mano en VR)
 * el tambor gira, se detiene en un número y suma esos tickets.
 * Va en el objeto Wheel_Lever_Pivot; los clics en la palanca suben hasta aquí.
 */
export class WheelGame extends Behaviour {
    drum!: Object3D;
    grip!: Object3D;
    display?: LedDisplay;
    bulbs: Mesh[] = [];

    private spinning = false;
    private t = 0;
    private duration = 4.5;
    private from = 0;
    private to = 0;
    private lastSeg = -1;
    private target = 0;
    private lever = 0;          // 0 arriba, 1 abajo
    private leverAnim = 0;      // tiempo restante de la animación de la palanca
    private chase = 0;
    private prevHand = new Map<any, Vector3>();

    setup(drum: Object3D, grip: Object3D, display: Object3D | undefined, bulbs: Mesh[]) {
        this.drum = drum; this.grip = grip; this.bulbs = bulbs;
        if (display) { this.display = new LedDisplay(display); this.display.set("¡GIRA!", "#ffd728", "EMPUJA LA PALANCA"); }
        // cada bombillo con su propio material para poder prenderlos por separado
        for (const b of bulbs) b.material = (b.material as Material).clone();
    }

    // ----- PC: arrastrar la palanca hacia abajo (o clic rápido) -----
    private dragging = false; private dragStart = 0; private dragMoved = false; private dragVal = 0;
    // ----- VR: agarrar la palanca con el botón de agarre y bajarla -----
    private xrCtrl: any = null; private xrBaseY = 0; private xrVal = 0;

    onPointerEnter() { if (!inXR(this.context)) setCursor(true); }
    onPointerExit() { setCursor(false); }
    onPointerDown(e: PointerEventData) {
        if (e.mode !== "screen" || inXR(this.context)) return;
        this.dragging = true; this.dragMoved = false; this.dragVal = 0;
        this.dragStart = this.context.input.mousePosition.y;
        Desk.captured = true;
    }
    /** En VR, apuntar con el rayo y apretar el gatillo también la baja. */
    onPointerClick(e: PointerEventData) { if (e.mode !== "screen") this.pull(); }

    /** En VR: empujar la palanca hacia abajo con la mano o el control. */
    onUpdateXR(args: NeedleXREventArgs) {
        if (!this.grip) return;
        const gp = this.grip.getWorldPosition(new Vector3());
        for (const c of args.xr.controllers) {
            const p = c.gripWorldPosition.clone();
            const prev = this.prevHand.get(c);
            this.prevHand.set(c, p);
            if (!prev) continue;
            const vy = (p.y - prev.y) / Math.max(1e-3, this.context.time.deltaTime);
            if (p.distanceTo(gp) < 0.18 && vy < -0.6) this.pull();
            const sq = c.getButton("xr-standard-squeeze");
            if (!this.xrCtrl && sq?.isDown && p.distanceTo(gp) < 0.22) { this.xrCtrl = c; this.xrBaseY = p.y; }
            if (this.xrCtrl === c) {
                if (sq?.pressed) {
                    this.xrVal = Math.max(0, Math.min(1, (this.xrBaseY - p.y) / 0.25));
                    if (this.xrVal >= 0.95) this.pull();
                } else { this.xrCtrl = null; this.xrVal = 0; }
            }
        }
    }

    pull() {
        if (this.spinning) return;
        sfx.coin();
        this.leverAnim = 0.6;
        this.spinning = true;
        this.t = 0;
        this.target = pickSegment();
        // ángulo para que el centro del segmento quede frente al puntero
        const n = SEGMENTS.length;
        const centerV = 1 - (this.target + 0.5) / n;
        const aim = centerV * TAU;
        const cur = this.drum.rotation.x;
        let delta = (aim - cur) % TAU; if (delta < 0) delta += TAU;
        this.from = cur;
        this.to = cur + delta + TAU * (4 + Math.floor(Math.random() * 2));
        this.duration = 4 + Math.random() * 1.5;
    }

    private segmentAtFront(angle: number): number {
        const n = SEGMENTS.length;
        let v = (angle / TAU) % 1; if (v < 0) v += 1;
        return Math.min(n - 1, Math.floor((1 - v) * n));
    }

    update() {
        const dt = this.context.time.deltaTime;
        // palanca: baja rápido y vuelve sola
        if (this.leverAnim > 0) {
            this.leverAnim = Math.max(0, this.leverAnim - dt);
            const k = this.leverAnim / 0.6;
            this.lever = k > 0.6 ? 1 : k / 0.6;
        } else this.lever = 0;
        if (this.dragging) {
            const input = this.context.input;
            if (input.getPointerPressed(0)) {
                const dy = Math.abs(input.mousePosition.y - this.dragStart);
                if (dy > 4) this.dragMoved = true;
                this.dragVal = Math.min(1, dy / 140);
                if (this.dragVal >= 0.95) this.pull();
            } else {
                this.dragging = false; Desk.captured = false;
                if (!this.dragMoved) this.pull();
                this.dragVal = 0;
            }
        }
        this.gameObject.rotation.x = Math.max(this.lever, this.dragVal, this.xrVal) * 0.65;

        if (this.spinning) {
            this.t += dt;
            const k = Math.min(1, this.t / this.duration);
            const ease = 1 - Math.pow(1 - k, 3);
            this.drum.rotation.x = this.from + (this.to - this.from) * ease;
            const seg = this.segmentAtFront(this.drum.rotation.x);
            if (seg !== this.lastSeg) {
                this.lastSeg = seg; sfx.tick();
                this.display?.set(String(SEGMENTS[seg]), "#ff3cac", "GIRANDO...");
            }
            if (k >= 1) {
                this.spinning = false;
                this.drum.rotation.x = this.to % TAU;
                const win = SEGMENTS[this.target];
                Tickets.add(win);
                if (win >= 100) sfx.win(); else sfx.pop();
                this.display?.set(`+${win}`, win >= 100 ? "#ffd728" : "#00ff88", win >= 250 ? "¡JACKPOT!" : "TICKETS");
            }
        }

        // luces que corren alrededor (más rápido mientras gira)
        this.chase += dt * (this.spinning ? 14 : 3);
        const on = Math.floor(this.chase);
        this.bulbs.forEach((b, i) => {
            const m = b.material as MeshStandardMaterial;
            const lit = (i + on) % 3 === 0;
            m.emissiveIntensity = lit ? 10 : 0.6;
        });
    }
}

export function setupWheel(byName: Map<string, Object3D>) {
    const pivot = byName.get("Wheel_Lever_Pivot");
    const drum = byName.get("Wheel_Drum");
    const grip = byName.get("Wheel_Lever_Grip");
    if (!pivot || !drum || !grip) { console.warn("[Arcade] Falta la rueda en la escena"); return; }
    const bulbs: Mesh[] = [];
    byName.forEach((o, n) => { if (n.startsWith("Wheel_Bulb_") && (o as Mesh).isMesh) bulbs.push(o as Mesh); });
    bulbs.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
    const game = pivot.addComponent(WheelGame);
    game.setup(drum, grip, byName.get("Wheel_Display"), bulbs);
}

import { CanvasTexture, MeshBasicMaterial, Object3D, SRGBColorSpace } from "three";
import { makeScreenPlane } from "./screens";
import { sfx } from "./sfx";

const STORAGE_KEY = "pixel84_tickets";

type Listener = (value: number, delta: number) => void;

/**
 * Moneda del arcade. Guarda los tickets en el navegador (localStorage),
 * así que siguen ahí cuando vuelves a entrar: el "mundo persistente" del módulo.
 */
class TicketManagerImpl {
    private _value = 0;
    private _shown = 0;          // valor que se muestra (sube de a poco, como un contador real)
    private listeners: Listener[] = [];
    private boards: { canvas: HTMLCanvasElement; tex: CanvasTexture; label: string; grid?: HTMLCanvasElement }[] = [];
    private flash = 0;
    private acc = 0; private tick = 0; private dirty = false;

    constructor() {
        try {
            const v = parseInt(localStorage.getItem(STORAGE_KEY) || "0");
            if (!isNaN(v)) { this._value = v; this._shown = v; }
        } catch { /* storage no disponible: empezamos en 0 */ }
    }

    get value() { return this._value; }

    add(amount: number) {
        if (amount <= 0) return;
        this._value += amount;
        this.save();
        this.flash = 1;
        this.listeners.forEach(l => l(this._value, amount));
    }

    /** Devuelve false si no alcanza. */
    spend(amount: number): boolean {
        if (amount > this._value) return false;
        this._value -= amount;
        this._shown = this._value;
        this.save();
        this.redraw();
        this.listeners.forEach(l => l(this._value, -amount));
        return true;
    }

    reset() { this._value = 0; this._shown = 0; this.save(); this.redraw(); }

    onChange(l: Listener) { this.listeners.push(l); }

    private save() {
        try { localStorage.setItem(STORAGE_KEY, String(this._value)); } catch { }
    }

    /** Convierte un objeto de Blender en un marcador LED. */
    attachBoard(obj: Object3D, label = "TICKETS") {
        const canvas = document.createElement("canvas");
        canvas.width = 768; canvas.height = 256;
        const tex = new CanvasTexture(canvas);
        tex.colorSpace = SRGBColorSpace;
        const mat = new MeshBasicMaterial({ map: tex, toneMapped: false });
        makeScreenPlane(obj, mat, 0.96);
        // la rejilla de LEDs se pinta una sola vez y luego se copia
        const grid = document.createElement("canvas"); grid.width = canvas.width; grid.height = canvas.height;
        const gg = grid.getContext("2d")!; gg.fillStyle = "rgba(255,255,255,0.03)";
        for (let x = 0; x < grid.width; x += 8) for (let y = 0; y < grid.height; y += 8) gg.fillRect(x, y, 5, 5);
        this.boards.push({ canvas, tex, label, grid });
        this.redraw();
    }

    /** Llamar cada frame. */
    update(dt: number) {
        // el contador sube de a poco, pero el dibujo del marcador se actualiza máximo ~8 veces por segundo
        // (redibujar el canvas y subirlo a la GPU cada frame era lo que bajaba los FPS en VR)
        this.acc += dt;
        if (this._shown < this._value) {
            const step = Math.max(1, Math.round((this._value - this._shown) * dt * 8));
            this._shown = Math.min(this._value, this._shown + step);
            this.tick += dt; if (this.tick > 0.09) { this.tick = 0; sfx.ticket(); }
            this.dirty = true;
        } else if (this.flash > 0) {
            this.flash = Math.max(0, this.flash - dt * 1.5);
            this.dirty = true;
        }
        if (this.dirty && this.acc > 0.125) { this.acc = 0; this.dirty = false; this.redraw(); }
    }

    private redraw() {
        for (const b of this.boards) {
            const g = b.canvas.getContext("2d")!;
            const w = b.canvas.width, h = b.canvas.height;
            g.fillStyle = "#07020f"; g.fillRect(0, 0, w, h);
            // rejilla tipo LED
            if (b.grid) g.drawImage(b.grid, 0, 0);
            g.textAlign = "center"; g.textBaseline = "middle";
            g.font = "bold 46px 'Courier New', monospace";
            g.lineWidth = 10; g.strokeStyle = "rgba(0,229,255,0.25)"; g.strokeText(b.label, w / 2, 48);
            g.fillStyle = "#00e5ff"; g.fillText(b.label, w / 2, 48);
            const pink = this.flash > 0 ? `rgb(255,${Math.round(60 + 195 * this.flash)},${Math.round(172 + 83 * this.flash)})` : "#ff3cac";
            g.font = "bold 150px 'Courier New', monospace";
            const txt = String(this._shown).padStart(5, "0");
            g.lineWidth = 16; g.strokeStyle = "rgba(255,60,172,0.25)"; g.strokeText(txt, w / 2, 160);
            g.fillStyle = pink; g.fillText(txt, w / 2, 160);
            b.tex.needsUpdate = true;
        }
    }
}

export const Tickets = new TicketManagerImpl();

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
    private boards: { canvas: HTMLCanvasElement; tex: CanvasTexture; label: string }[] = [];
    private flash = 0;

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
        this.boards.push({ canvas, tex, label });
        this.redraw();
    }

    /** Llamar cada frame. */
    update(dt: number) {
        if (this._shown < this._value) {
            // sube 1 ticket cada ~30 ms, más rápido si la diferencia es grande
            const step = Math.max(1, Math.round((this._value - this._shown) * dt * 6));
            this._shown = Math.min(this._value, this._shown + step);
            sfx.ticket();
            this.redraw();
        } else if (this.flash > 0) {
            this.flash = Math.max(0, this.flash - dt * 1.5);
            this.redraw();
        }
    }

    private redraw() {
        for (const b of this.boards) {
            const g = b.canvas.getContext("2d")!;
            const w = b.canvas.width, h = b.canvas.height;
            g.fillStyle = "#07020f"; g.fillRect(0, 0, w, h);
            // rejilla tipo LED
            g.fillStyle = "rgba(255,255,255,0.03)";
            for (let x = 0; x < w; x += 8) for (let y = 0; y < h; y += 8) g.fillRect(x, y, 5, 5);
            g.textAlign = "center"; g.textBaseline = "middle";
            g.shadowColor = "#00e5ff"; g.shadowBlur = 18;
            g.fillStyle = "#00e5ff";
            g.font = "bold 46px 'Courier New', monospace";
            g.fillText(b.label, w / 2, 48);
            const pink = this.flash > 0 ? `rgb(255,${Math.round(60 + 195 * this.flash)},${Math.round(172 + 83 * this.flash)})` : "#ff3cac";
            g.shadowColor = "#ff3cac"; g.shadowBlur = 30;
            g.fillStyle = pink;
            g.font = "bold 150px 'Courier New', monospace";
            g.fillText(String(this._shown).padStart(5, "0"), w / 2, 160);
            b.tex.needsUpdate = true;
        }
    }
}

export const Tickets = new TicketManagerImpl();

import { Behaviour, Context, PointerEventData } from "@needle-tools/engine";
import { CanvasTexture, Material, Mesh, MeshBasicMaterial, Object3D, SRGBColorSpace } from "three";
import { Tickets } from "./tickets";
import { sfx, chiptune } from "./sfx";
import { inXR, isDeskClick, setCursor, Intro } from "./state";

type Style = "shooter" | "runner" | "racer" | "dance";
const SONGS: number[][] = [
    [523, 659, 784, 659, 523, 0, 392, 0, 523, 659, 784, 1046, 784, 0, 659, 0],
    [392, 0, 392, 523, 0, 523, 659, 587, 523, 0, 440, 494, 523, 0, 0, 0],
    [330, 330, 0, 330, 0, 262, 330, 0, 392, 0, 0, 0, 196, 0, 0, 0],
    [659, 587, 523, 587, 659, 659, 659, 0, 587, 587, 587, 0, 659, 784, 784, 0],
];

class CabClick extends Behaviour {
    cab!: Cabinet;
    onPointerEnter() { if (!inXR(this.context)) setCursor(true); }
    onPointerExit() { setCursor(false); }
    onPointerClick(e: PointerEventData) {
        if (Intro.blocking) return;
        if (e.mode === "screen" && !isDeskClick(this.context, e.mode)) return;
        this.cab.play();
    }
}

/** Maquinita: al tocarla se "juega" una partida corta en su pantalla y da unos pocos tickets. */
class Cabinet {
    canvas = document.createElement("canvas");
    tex: CanvasTexture; mat: MeshBasicMaterial;
    original: Material | Material[];
    playing = 0; over = 0; win = 0; acc = 0; t = 0;
    sprites: { x: number; y: number; v: number; c: string }[] = [];
    constructor(private ctx: Context, public root: Object3D, public screen: Mesh, public style: Style, public color: string, public song: number[]) {
        this.canvas.width = 256; this.canvas.height = 192;
        this.tex = new CanvasTexture(this.canvas); this.tex.colorSpace = SRGBColorSpace;
        this.mat = new MeshBasicMaterial({ map: this.tex, toneMapped: false });
        this.original = screen.material;
        const c = root.addComponent(CabClick); c.cab = this;
    }
    play() {
        if (this.playing > 0 || this.over > 0) return;
        sfx.coin();
        this.playing = 8; this.t = 0; this.sprites = [];
        this.screen.material = this.mat;
        const len = chiptune(this.song);
        setTimeout(() => { if (this.playing > 0) chiptune(this.song); }, len * 1000);
    }
    update(dt: number) {
        if (this.playing <= 0 && this.over <= 0) return;
        this.t += dt;
        if (this.playing > 0) {
            this.playing -= dt;
            if (this.playing <= 0) {
                this.win = 2 + Math.floor(Math.random() * 7);
                Tickets.add(this.win); sfx.win();
                this.over = 2;
            }
        } else {
            this.over -= dt;
            if (this.over <= 0) { this.screen.material = this.original; return; }
        }
        this.acc += dt; if (this.acc < 1 / 12) return; this.acc = 0;   // 12 fps para no pesar en el Quest
        this.draw();
    }
    private draw() {
        const g = this.canvas.getContext("2d")!; const W = 256, H = 192; const t = this.t;
        g.fillStyle = "#05030f"; g.fillRect(0, 0, W, H);
        if (this.over > 0) {
            g.textAlign = "center"; g.fillStyle = "#ff3cac"; g.font = "bold 30px monospace"; g.fillText("GAME OVER", W / 2, 80);
            g.fillStyle = "#ffd728"; g.font = "bold 24px monospace"; g.fillText(`+${this.win} TICKETS`, W / 2, 125);
            return;
        }
        if (this.style === "racer") {
            g.fillStyle = "#2a0050"; g.fillRect(0, 0, W, 80);
            g.fillStyle = "#ffcc33"; g.beginPath(); g.arc(W / 2, 80, 30, Math.PI, 0); g.fill();
            for (let i = 0; i < 12; i++) {
                const k = ((i / 12) + t * 0.8) % 1; const y = 80 + k * k * 112;
                g.fillStyle = i % 2 ? "#ff3cac" : "#00e5ff"; g.fillRect(W / 2 - 10 - k * 120, y, 4 + k * 10, 3 + k * 6); g.fillRect(W / 2 + 6 + k * 120, y, 4 + k * 10, 3 + k * 6);
            }
            g.fillStyle = "#ff3c3c"; g.fillRect(W / 2 - 18 + Math.sin(t * 2) * 30, 160, 36, 18);
        } else if (this.style === "dance") {
            const cols = ["#ff3cac", "#00e5ff", "#ffd728", "#3cff7a"];
            for (let i = 0; i < 4; i++) { g.strokeStyle = cols[i]; g.lineWidth = 3; g.strokeRect(40 + i * 48, 20, 36, 36); }
            for (let i = 0; i < 10; i++) {
                const lane = (i * 7) % 4; const y = 192 - ((t * 90 + i * 40) % 220);
                g.fillStyle = cols[lane]; g.beginPath(); g.moveTo(58 + lane * 48, y); g.lineTo(40 + lane * 48, y + 30); g.lineTo(76 + lane * 48, y + 30); g.fill();
            }
        } else {
            for (let i = 0; i < 40; i++) { const y = (i * 37 + t * (this.style === "runner" ? 0 : 60)) % H; const x = (i * 71 + (this.style === "runner" ? -t * 80 : 0)) % W; g.fillStyle = "#ffffff55"; g.fillRect((x + W) % W, y, 2, 2); }
            if (this.style === "runner") {
                g.fillStyle = "#3a1a6a"; g.fillRect(0, 150, W, 42);
                for (let i = 0; i < 4; i++) { const x = (W - ((t * 120 + i * 90) % (W + 40))); g.fillStyle = "#ff3cac"; g.fillRect(x, 130, 18, 20); }
                const jump = Math.abs(Math.sin(t * 4)) * 40;
                g.fillStyle = this.color; g.beginPath(); g.arc(60, 138 - jump, 12, 0, Math.PI * 2); g.fill();
            } else {
                const px = W / 2 + Math.sin(t * 2.3) * 80;
                g.fillStyle = this.color; g.beginPath(); g.moveTo(px, 160); g.lineTo(px - 12, 180); g.lineTo(px + 12, 180); g.fill();
                for (let r = 0; r < 3; r++) for (let c = 0; c < 6; c++) {
                    const x = 30 + c * 36 + Math.sin(t * 1.5) * 20, y = 30 + r * 24;
                    if ((c + r + Math.floor(t * 2)) % 7 === 0) continue;
                    g.fillStyle = ["#ff3cac", "#00e5ff", "#3cff7a"][r]; g.fillRect(x, y, 20, 12);
                }
                g.fillStyle = "#ffd728"; for (let i = 0; i < 3; i++) g.fillRect(px - 1, 150 - ((t * 300 + i * 50) % 130), 2, 8);
            }
        }
        g.fillStyle = "#ffffff"; g.font = "bold 14px monospace"; g.textAlign = "left";
        g.fillText(`SCORE ${String(Math.floor(this.t * 137)).padStart(5, "0")}`, 8, 16);
        for (let y = 0; y < H; y += 3) { g.fillStyle = "rgba(0,0,0,0.25)"; g.fillRect(0, y, W, 1); }
        this.tex.needsUpdate = true;
    }
}

export class Cabinets {
    list: Cabinet[] = [];
    constructor(private ctx: Context, byName: Map<string, Object3D>) {
        const defs: [string, string, Style, string][] = [
            ["Arcade_1", "Screen_1", "shooter", "#ff9a28"], ["Arcade_2", "Screen_2", "runner", "#50f05a"],
            ["Arcade_3", "Screen_3", "shooter", "#c8c8dc"], ["Arcade_4", "Screen_4", "runner", "#ffd728"],
            ["Arcade_5", "Screen_5", "shooter", "#e646c8"], ["Carreras_Moderna", "Screen_6", "racer", "#ff3c3c"],
            ["Baile_Moderna", "Screen_7", "dance", "#ff3cac"],
        ];
        defs.forEach(([r, s, st, col], i) => {
            const root = byName.get(r); const screen = byName.get(s) as Mesh | undefined;
            if (root && screen && screen.isMesh) this.list.push(new Cabinet(ctx, root, screen, st, col, SONGS[i % SONGS.length]));
        });
    }
    update() { const dt = this.ctx.time.deltaTime; this.list.forEach(c => c.update(dt)); }
}

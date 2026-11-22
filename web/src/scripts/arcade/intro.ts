import { Context, findObjectOfType, XRControllerMovement } from "@needle-tools/engine";
import { CanvasTexture, Group, Mesh, MeshBasicMaterial, PlaneGeometry, Quaternion, SRGBColorSpace, Vector3 } from "three";
import { Desk, Intro, inXR } from "./state";

const DURATION = 10;   // segundos antes de quitarse sola

const GAMES: [string, string][] = [
    ["RUEDA CÓSMICA", "Baja la palanca y gana hasta 500"],
    ["TIRO AL BLANCO", "Agarra una pistola y dispara"],
    ["TOPO", "Agarra un mazo y golpea"],
    ["MINI BASKET", "Lanza el balón al aro"],
    ["MAQUINITAS", "Tócalas: minijuego de 2 a 8"],
];

/**
 * Pantalla de inicio que explica la experiencia. Bloquea moverse e interactuar
 * hasta que pasen 10 s o la persona pulse algo.
 * PC: recuadro grande en el centro de la pantalla. VR: panel frente a los ojos (aparece al entrar a VR).
 */
export class IntroScreen {
    private overlay?: HTMLDivElement;
    private bar?: HTMLDivElement;
    private left = 0;
    private mode: "none" | "desk" | "xr" = "none";
    private releaseAt = 0;           // sigue bloqueando un instante tras quitarla (para que ese clic no cuente)
    private shownInXR = false;
    private wasXR = false;
    private panel: Group;
    private vrBar: Mesh;
    private onKey = (e: Event) => { if (this.mode === "desk") { e.stopPropagation(); this.dismiss(); } };

    constructor(private ctx: Context) {
        this.panel = this.buildPanel();
        this.vrBar = this.panel.getObjectByName("intro_bar") as Mesh;
        ctx.scene.add(this.panel);
        if (inXR(ctx)) this.showXR(); else this.showDesk();
    }

    // ---------- PC ----------
    private showDesk() {
        const o = document.createElement("div");
        o.style.cssText = "position:fixed;inset:0;z-index:100000;display:flex;align-items:center;justify-content:center;" +
            "background:rgba(5,0,20,.72);backdrop-filter:blur(3px);cursor:pointer;font-family:'Courier New',monospace";
        const rows = GAMES.map(([t, d]) =>
            `<div style="display:flex;justify-content:space-between;gap:24px;padding:6px 0;border-bottom:1px dashed #ffffff22">` +
            `<span style="color:#ffd728;font-weight:700">${t}</span><span style="color:#fff">${d}</span></div>`).join("");
        o.innerHTML =
            `<div style="width:min(720px,90vw);padding:32px 40px 24px;border-radius:18px;background:#0a001ef0;` +
            `border:3px solid #ff3cac;box-shadow:0 0 40px #ff3cac88, inset 0 0 30px #00e5ff22;text-align:center">` +
            `<div style="color:#00e5ff;font-size:clamp(26px,4vw,44px);font-weight:900;letter-spacing:2px;text-shadow:0 0 12px #00e5ff">BIENVENIDO A PIXEL 84</div>` +
            `<div style="color:#fff;font-size:18px;margin:10px 0 18px">Juega para ganar tickets:</div>` +
            `<div style="text-align:left;font-size:16px">${rows}</div>` +
            `<div style="color:#3cff7a;font-size:19px;font-weight:700;margin:20px 0 6px">Canjea tus tickets por premios en el mostrador</div>` +
            `<div style="color:#bbb;font-size:13px;margin-bottom:18px">Tu total de tickets siempre está arriba a la derecha · Gira tus premios con clic derecho o la rueda</div>` +
            `<div style="height:8px;border-radius:4px;background:#ffffff1a;overflow:hidden"><div id="intro-bar" style="height:100%;width:100%;background:linear-gradient(90deg,#ff3cac,#00e5ff)"></div></div>` +
            `<div style="color:#ffd728;font-size:14px;margin-top:12px">Pulsa cualquier tecla o haz clic para empezar</div></div>`;
        document.body.appendChild(o);
        this.overlay = o; this.bar = o.querySelector("#intro-bar") as HTMLDivElement;
        // el clic no debe llegar al juego
        for (const ev of ["pointerdown", "pointerup", "click", "wheel", "contextmenu"])
            o.addEventListener(ev, e => { e.stopPropagation(); e.preventDefault(); if (ev === "click" || ev === "wheel") this.dismiss(); });
        window.addEventListener("keydown", this.onKey, true);
        this.start("desk");
    }

    // ---------- VR ----------
    private buildPanel() {
        const W = 1024, H = 640;
        const c = document.createElement("canvas"); c.width = W; c.height = H;
        const g = c.getContext("2d")!;
        g.fillStyle = "rgba(10,0,30,0.94)"; g.fillRect(0, 0, W, H);
        g.strokeStyle = "#ff3cac"; g.lineWidth = 10; g.strokeRect(5, 5, W - 10, H - 10);
        g.textAlign = "center"; g.textBaseline = "middle";
        g.fillStyle = "#00e5ff"; g.font = "900 60px sans-serif"; g.fillText("BIENVENIDO A PIXEL 84", W / 2, 70);
        g.fillStyle = "#fff"; g.font = "bold 32px sans-serif"; g.fillText("Juega para ganar tickets:", W / 2, 135);
        GAMES.forEach(([t, d], i) => {
            const y = 195 + i * 56;
            g.textAlign = "left"; g.fillStyle = "#ffd728"; g.font = "bold 32px sans-serif"; g.fillText(t, 70, y);
            g.textAlign = "right"; g.fillStyle = "#fff"; g.font = "28px sans-serif"; g.fillText(d, W - 70, y);
        });
        g.textAlign = "center";
        g.fillStyle = "#3cff7a"; g.font = "bold 34px sans-serif"; g.fillText("Canjea tus tickets en el mostrador de PREMIOS", W / 2, 488);
        g.fillStyle = "#bbbbbb"; g.font = "24px sans-serif"; g.fillText("Gira tus premios con el joystick · Suéltalos con el grip", W / 2, 535);
        g.fillStyle = "#ffd728"; g.font = "bold 28px sans-serif"; g.fillText("Aprieta cualquier botón del control para empezar", W / 2, 600);
        const tex = new CanvasTexture(c); tex.colorSpace = SRGBColorSpace;
        const mat = (o: object) => new MeshBasicMaterial({ toneMapped: false, depthTest: false, transparent: true, ...o });
        const grp = new Group();
        const w = 0.8, h = w * H / W;
        const bg = new Mesh(new PlaneGeometry(w, h), mat({ map: tex }));
        // barra del tiempo (se encoge escalando, sin redibujar la textura)
        const track = new Mesh(new PlaneGeometry(w * 0.86, 0.012), mat({ color: 0x332244 }));
        const bar = new Mesh(new PlaneGeometry(w * 0.86, 0.012), mat({ color: 0x00e5ff }));
        bar.name = "intro_bar";
        const by = -h / 2 + h * (95 / H);
        track.position.set(0, by, 0.001); bar.position.set(0, by, 0.002);
        for (const [i, m] of [bg, track, bar].entries()) { m.renderOrder = 1000 + i; m.frustumCulled = false; grp.add(m); }
        grp.visible = false;
        return grp;
    }

    private showXR() {
        this.shownInXR = true;
        this.panel.visible = true;
        this.placePanel(1);
        const mov = findObjectOfType(XRControllerMovement, this.ctx); if (mov) mov.enabled = false;
        this.start("xr");
    }

    private placePanel(k: number) {
        const cam = this.ctx.mainCamera; if (!cam) return;
        const q = cam.getWorldQuaternion(new Quaternion());
        const target = cam.getWorldPosition(new Vector3()).add(new Vector3(0, -0.05, -1.0).applyQuaternion(q));
        this.panel.position.lerp(target, k);
        this.panel.quaternion.slerp(q, k);
    }

    // ---------- común ----------
    private start(mode: "desk" | "xr") {
        this.mode = mode; this.left = DURATION; Intro.blocking = true;
    }

    private dismiss() {
        if (this.mode === "none") return;
        if (this.mode === "desk") {
            this.overlay?.remove(); this.overlay = undefined;
            window.removeEventListener("keydown", this.onKey, true);
        } else {
            this.panel.visible = false;
            const mov = findObjectOfType(XRControllerMovement, this.ctx); if (mov) mov.enabled = true;
        }
        this.mode = "none";
        Desk.usedFrame = this.ctx.time.frameCount;
        this.releaseAt = this.ctx.time.time + 0.35;
    }

    update() {
        const ctx = this.ctx; const xr = inXR(ctx);
        // al entrar a VR por primera vez, mostrar la explicación allá también
        if (xr && !this.wasXR) {
            if (this.mode === "desk") this.dismiss();
            if (!this.shownInXR) this.showXR();
        }
        if (!xr && this.wasXR && this.mode === "xr") this.dismiss();
        this.wasXR = xr;

        if (this.mode === "none") {
            if (Intro.blocking && ctx.time.time >= this.releaseAt) Intro.blocking = false;
            return;
        }
        this.left -= Math.min(0.1, ctx.time.deltaTime);   // el primer frame trae el tiempo de carga
        const k = Math.max(0, this.left / DURATION);
        if (this.mode === "desk" && this.bar) this.bar.style.width = `${k * 100}%`;
        if (this.mode === "xr") {
            this.vrBar.scale.x = Math.max(0.001, k);
            this.vrBar.position.x = -(1 - k) * (0.8 * 0.86) / 2;
            this.placePanel(0.08);   // sigue suave la mirada para no perderlo
            // cualquier botón (tras medio segundo, para no quitarlo con el clic de entrar a VR)
            if (DURATION - this.left > 0.5 && ctx.xr) {
                for (const c of ctx.xr.controllers) {
                    const any = ["xr-standard-trigger", "xr-standard-squeeze", "a-button", "b-button", "x-button", "y-button", "pinch"]
                        .some(b => c.getButton(b as any)?.isDown);
                    if (any) { this.dismiss(); return; }
                }
            }
        }
        if (this.left <= 0) this.dismiss();
    }
}

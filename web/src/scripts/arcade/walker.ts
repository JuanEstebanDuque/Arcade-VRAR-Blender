import { Context, OrbitControls, findObjectOfType } from "@needle-tools/engine";
import { Box3, Euler, Object3D, Quaternion, Vector3 } from "three";
import { Desk, inXR, Intro } from "./state";

/**
 * Caminar en el PC (sin visor): WASD / flechas para moverse, arrastrar con el mouse para mirar.
 * En VR no hace nada: ahí manda el visor y el teletransporte.
 */
export class DesktopWalker {
    private yaw = 0;
    private pitch = 0;
    private pos = new Vector3();
    private obstacles: Box3[] = [];
    private bounds = new Box3();
    private hud?: HTMLDivElement;
    private moved = 0;
    private lookX = 0; private lookY = 0; private hudHidden = false;
    private ready = false;

    constructor(private ctx: Context, obstacleRoots: Object3D[], roomBounds: Box3) {
        const orbit = findObjectOfType(OrbitControls, ctx);
        if (orbit) orbit.enabled = false;
        const cam = ctx.mainCamera;
        if (!cam) return;
        const f = new Vector3(0, 0, -1).applyQuaternion(cam.getWorldQuaternion(new Quaternion()));
        this.yaw = Math.atan2(-f.x, -f.z);
        this.pitch = 0;
        cam.getWorldPosition(this.pos);
        this.pos.y = 1.6;
        for (const o of obstacleRoots) {
            const b = new Box3().setFromObject(o);
            if (!b.isEmpty() && b.max.y > 0.3 && b.min.y < 1.8) this.obstacles.push(b.expandByScalar(0.25));
        }
        this.bounds.copy(roomBounds).expandByScalar(-0.35);
        const el = ctx.domElement;
        el.addEventListener("contextmenu", e => e.preventDefault());
        // usamos eventos del navegador (no el sondeo por frame) para que un clic rápido nunca se confunda con arrastrar
        window.addEventListener("pointerdown", () => { Desk.dragged = false; this.moved = 0; }, true);
        window.addEventListener("pointermove", e => {
            if (!e.buttons || inXR(this.ctx)) return;
            this.moved += Math.abs(e.movementX) + Math.abs(e.movementY);
            if (this.moved > 6) Desk.dragged = true;
            if (Desk.dragged && !Desk.captured) { this.lookX -= e.movementX * 0.0045; this.lookY -= e.movementY * 0.0045; }
        }, true);
        window.addEventListener("pointerup", () => { setTimeout(() => { Desk.captured = false; }, 0); }, true);
        window.addEventListener("keydown", e => { if ((e.key === "h" || e.key === "H") && this.hud) this.hudHidden = !this.hudHidden; });
        this.makeHud();
        this.ready = true;
    }

    private makeHud() {
        const d = document.createElement("div");
        d.style.cssText = "position:fixed;left:12px;bottom:12px;z-index:50;padding:10px 14px;border-radius:10px;" +
            "background:rgba(10,0,30,.72);color:#fff;font:600 13px/1.45 system-ui,sans-serif;pointer-events:none;" +
            "border:1px solid #ff3cac;box-shadow:0 0 12px #ff3cac66";
        d.innerHTML = "<b style='color:#00e5ff'>PIXEL 84</b><br>WASD / flechas: caminar · Shift: correr<br>" +
            "Arrastrar el mouse: mirar<br>Clic: usar / agarrar · Clic con algo en la mano: lanzar, disparar, golpear<br>" +
            "Q: soltar lo que tienes · Arrastra la palanca de la rueda hacia abajo<br><span style='opacity:.7'>H: ocultar esta ayuda</span>";
        document.body.appendChild(d);
        this.hud = d;
    }

    /** Para pruebas automáticas: poner la cámara en un punto (x, z) mirando con yaw/pitch en radianes. */
    setPose(x: number, z: number, yaw: number, pitch = 0) { this.pos.set(x, 1.6, z); this.yaw = yaw; this.pitch = pitch; }

    update() {
        if (!this.ready) return;
        const ctx = this.ctx; const input = ctx.input;
        if (this.hud) this.hud.style.display = inXR(ctx) || this.hudHidden ? "none" : "block";
        if (inXR(ctx)) return;
        const cam = ctx.mainCamera; if (!cam) return;
        const dt = Math.min(0.05, ctx.time.deltaTime);

        // mirar: lo maneja onPointerMove (eventos del navegador)
        if (Intro.blocking) { this.lookX = 0; this.lookY = 0; }
        this.yaw += this.lookX; this.pitch = Math.max(-1.2, Math.min(1.2, this.pitch + this.lookY));
        this.lookX = 0; this.lookY = 0;

        // caminar
        const k = (c: string) => input.isKeyPressed(c);
        let fx = 0, fz = 0;
        if (k("w") || k("W") || k("ArrowUp")) fz += 1;
        if (k("s") || k("S") || k("ArrowDown")) fz -= 1;
        if (k("a") || k("A") || k("ArrowLeft")) fx -= 1;
        if (k("d") || k("D") || k("ArrowRight")) fx += 1;
        if (Intro.blocking) { fx = 0; fz = 0; }
        if (fx || fz) {
            const speed = (k("Shift") ? 3.6 : 2.0) * dt;
            const len = Math.hypot(fx, fz);
            const fwd = new Vector3(-Math.sin(this.yaw), 0, -Math.cos(this.yaw));
            const right = new Vector3(Math.cos(this.yaw), 0, -Math.sin(this.yaw));
            const step = fwd.multiplyScalar(fz / len * speed).add(right.multiplyScalar(fx / len * speed));
            this.tryMove(step.x, 0); this.tryMove(0, step.z);
        }
        cam.worldPosition = this.pos;
        cam.worldQuaternion = new Quaternion().setFromEuler(new Euler(this.pitch, this.yaw, 0, "YXZ"));
    }

    private tryMove(dx: number, dz: number) {
        const nx = this.pos.x + dx, nz = this.pos.z + dz;
        if (nx < this.bounds.min.x || nx > this.bounds.max.x || nz < this.bounds.min.z || nz > this.bounds.max.z) return;
        for (const b of this.obstacles) {
            const inside = nx > b.min.x && nx < b.max.x && nz > b.min.z && nz < b.max.z;
            const wasInside = this.pos.x > b.min.x && this.pos.x < b.max.x && this.pos.z > b.min.z && this.pos.z < b.max.z;
            if (inside && !wasInside) return;
        }
        this.pos.x = nx; this.pos.z = nz;
    }
}

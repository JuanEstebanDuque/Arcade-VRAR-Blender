import { Behaviour, Context, findObjectOfType, NeedleXRController, XRControllerMovement, PointerEventData, Rigidbody } from "@needle-tools/engine";
import { Box3, Euler, Matrix4, Object3D, Quaternion, Ray, Raycaster, Vector2, Vector3 } from "three";
import { Desk, inXR, Intro, isDeskClick, setCursor } from "./state";

export type Holder = { kind: "desk" } | { kind: "xr"; ctrl: NeedleXRController };
type Pose = { pos: [number, number, number]; rot: [number, number, number] };

export interface GrabOptions {
    /** si tiene Rigidbody se puede lanzar (al soltarlo sigue con la velocidad de la mano) */
    rb?: Rigidbody;
    /** pose en la mano en VR. Si se omite, se agarra "como esté". aim=true: sigue el rayo del control (pistolas) */
    hold?: Pose & { aim?: boolean; forward?: number };
    /** pose relativa a la cámara en PC */
    desk?: Pose;
    /** al soltarlo vuelve solo a su sitio */
    returnHome?: boolean;
    canGrab?: () => boolean;
    onGrab?: (h: Holder) => void;
    /** se llama al soltar; puede cambiar la velocidad (ayuda de puntería) */
    onRelease?: (vel: Vector3, h: Holder) => void;
    /** gatillo en VR / clic en PC mientras se sostiene */
    onUse?: (h: Holder, ray: Ray) => void;
    /** se puede girar en la mano: PC = clic derecho + arrastrar y rueda; VR = joystick del control que lo sostiene */
    spin?: boolean;
}

const D2R = Math.PI / 180;
const qFrom = (r: [number, number, number]) => new Quaternion().setFromEuler(new Euler(r[0] * D2R, r[1] * D2R, r[2] * D2R));

export class Grabbable {
    holder: Holder | null = null;
    homePos = new Vector3();
    homeQuat = new Quaternion();
    centerLocal = new Vector3();
    radius = 0.1;
    rel = new Matrix4();          // pose relativa a la mano al agarrar "como esté"
    returning = 0;
    pendingVel: Vector3 | null = null; pendingFrames = 0;
    history: { p: Vector3; t: number }[] = [];
    /** giro extra que la persona le da al objeto en la mano */
    spin = new Quaternion();
    /** VR: agarrado sin apretar el grip (p. ej. al canjear un premio): no se suelta hasta apretar y soltar el grip */
    sticky = false;
    grabTime = 0;
    constructor(public obj: Object3D, public opt: GrabOptions) {
        obj.updateWorldMatrix(true, true);
        obj.getWorldPosition(this.homePos); obj.getWorldQuaternion(this.homeQuat);
        const b = new Box3().setFromObject(obj);
        const c = new Vector3(); b.getCenter(c);
        this.radius = Math.max(0.05, b.getSize(new Vector3()).length() / 2);
        this.centerLocal.copy(obj.worldToLocal(c.clone()));
    }
    worldCenter() { return this.obj.localToWorld(this.centerLocal.clone()); }
    goHome() {
        this.obj.worldPosition = this.homePos; this.obj.worldQuaternion = this.homeQuat;
        if (this.opt.rb) { this.opt.rb.teleport(this.homePos); this.opt.rb.resetVelocities(); }
    }
}

/** Clic en PC sobre un objeto agarrable = tomarlo en la mano. */
class Pickable extends Behaviour {
    g!: Grabbable;
    onPointerEnter() { if (!inXR(this.context)) setCursor(true); }
    onPointerExit() { setCursor(false); }
    onPointerClick(e: PointerEventData) {
        if (!isDeskClick(this.context, e.mode)) return;
        if (Hands.desk) return;                 // con algo en la mano, el clic es "usar"
        if (this.g.opt.canGrab && !this.g.opt.canGrab()) return;
        Hands.grab(this.g, { kind: "desk" });
        e.use();
    }
}

class HandsImpl {
    ctx!: Context;
    items: Grabbable[] = [];
    desk: Grabbable | null = null;
    private xrHeld = new Map<NeedleXRController, Grabbable>();
    private raycaster = new Raycaster();

    private rotating = false;
    private mov?: XRControllerMovement | null;

    init(ctx: Context) {
        this.ctx = ctx;
        window.addEventListener("keydown", e => { if ((e.key === "q" || e.key === "Q") && this.desk) this.release(this.desk); });
        // PC: clic derecho + arrastrar gira lo que tienes en la mano (en todos los ejes); la rueda lo gira sobre sí mismo
        window.addEventListener("pointerdown", e => {
            if (e.button === 2 && this.desk?.opt.spin && !inXR(ctx)) { this.rotating = true; Desk.captured = true; }
        }, true);
        window.addEventListener("pointermove", e => {
            if (!this.rotating || !this.desk) return;
            if (!(e.buttons & 2)) { this.rotating = false; return; }
            Desk.captured = true;
            this.spinBy(this.desk, e.movementY * 0.012, e.movementX * 0.012, 0);
        }, true);
        window.addEventListener("pointerup", e => {
            if (e.button !== 2) return;
            // que el clic derecho no cuente como "usar" ni como clic en otra cosa
            Desk.usedFrame = ctx.time.frameCount + 1;
            this.rotating = false;
        }, true);
        window.addEventListener("wheel", e => {
            if (!this.desk?.opt.spin || inXR(ctx)) return;
            this.spinBy(this.desk, 0, 0, Math.sign(e.deltaY) * 0.25);
        }, { passive: true });
    }

    /** Gira el objeto en la mano: ángulos en el marco de la cámara (PC) o del control (VR). */
    private spinBy(g: Grabbable, ax: number, ay: number, az: number) {
        const d = new Quaternion().setFromEuler(new Euler(ax, ay, az, "XYZ"));
        g.spin.premultiply(d);
    }

    register(obj: Object3D, opt: GrabOptions): Grabbable {
        const g = new Grabbable(obj, opt);
        this.items.push(g);
        const p = obj.addComponent(Pickable); p.g = g;
        return g;
    }

    isHeld(g: Grabbable) { return !!g.holder; }

    /** VR: poner un objeto directo en la mano del control (sin apretar el grip). */
    grabXR(g: Grabbable, ctrl?: NeedleXRController) {
        const ctrls = this.ctx.xr?.controllers ?? [];
        let c = ctrl && ctrls.includes(ctrl) ? ctrl : undefined;
        if (!c) c = ctrls.find(k => k.getButton("xr-standard-trigger")?.pressed) ?? ctrls.find(k => k.side === "right") ?? ctrls[0];
        if (!c) return false;
        const old = this.xrHeld.get(c); if (old) this.release(old);
        this.grab(g, { kind: "xr", ctrl: c });
        g.sticky = true;
        this.poseInHand(g, c);
        return true;
    }

    grab(g: Grabbable, h: Holder) {
        if (g.holder) this.release(g, new Vector3());
        g.holder = h; g.returning = 0; g.history = []; g.pendingFrames = 0;
        g.spin.identity(); g.grabTime = this.ctx.time.time; g.sticky = false;
        if (g.opt.rb) { g.opt.rb.isKinematic = true; g.opt.rb.resetVelocities(); }
        if (h.kind === "desk") { if (this.desk && this.desk !== g) this.release(this.desk); this.desk = g; Desk.usedFrame = this.ctx.time.frameCount; }
        else {
            this.xrHeld.set(h.ctrl, g);
            const grip = new Matrix4().compose(h.ctrl.gripWorldPosition, h.ctrl.gripWorldQuaternion, new Vector3(1, 1, 1));
            g.obj.updateWorldMatrix(true, false);
            g.rel.copy(grip.invert()).multiply(g.obj.matrixWorld);
        }
        g.opt.onGrab?.(h);
    }

    /** Suelta. vel = velocidad de lanzamiento (si se omite, la de la mano). */
    release(g: Grabbable, vel?: Vector3) {
        const h = g.holder; if (!h) return;
        g.holder = null;
        if (h.kind === "desk") { if (this.desk === g) this.desk = null; Desk.usedFrame = this.ctx.time.frameCount; }
        else this.xrHeld.delete(h.ctrl);
        const v = vel ? vel.clone() : this.handVelocity(g);
        if (g.opt.rb) {
            g.opt.onRelease?.(v, h);
            g.opt.rb.isKinematic = false;
            g.opt.rb.teleport(g.obj.getWorldPosition(new Vector3()));
            g.opt.rb.setVelocity(v.x, v.y, v.z);
            g.opt.rb.setAngularVelocity((Math.random() - .5) * 6, (Math.random() - .5) * 6, (Math.random() - .5) * 6);
            // el cambio de cinemático a dinámico se aplica en el siguiente paso de física: repetir la velocidad unos frames
            g.pendingVel = v.clone(); g.pendingFrames = 3;
        } else {
            g.opt.onRelease?.(v, h);
            if (g.opt.returnHome) g.returning = 0.0001;
        }
    }

    private handVelocity(g: Grabbable) {
        const hs = g.history; if (hs.length < 2) return new Vector3();
        const a = hs[0], b = hs[hs.length - 1];
        const dt = Math.max(1e-3, b.t - a.t);
        return b.p.clone().sub(a.p).divideScalar(dt);
    }

    /** Rayo desde la cámara por donde está el mouse (PC). */
    mouseRay(): Ray {
        const ctx = this.ctx;
        const rc = ctx.input.mousePositionRC;
        this.raycaster.setFromCamera(new Vector2(rc.x, rc.y), ctx.mainCamera!);
        return this.raycaster.ray.clone();
    }

    update() {
        const ctx = this.ctx; if (!ctx) return;
        const t = ctx.time.time;
        const xr = inXR(ctx);
        if (xr && this.desk) this.release(this.desk);

        // ----- PC -----
        if (!xr && this.desk) {
            const g = this.desk; const cam = ctx.mainCamera!;
            const d = g.opt.desk ?? { pos: [0.25, -0.25, -0.55], rot: [0, 0, 0] };
            const cq = cam.getWorldQuaternion(new Quaternion());
            const cp = cam.getWorldPosition(new Vector3());
            g.obj.worldQuaternion = cq.clone().multiply(g.spin).multiply(qFrom(d.rot));
            g.obj.worldPosition = cp.add(new Vector3(...d.pos).applyQuaternion(cq));
            if (g.opt.rb) g.opt.rb.teleport(g.obj.worldPosition);
            this.track(g, t);
            // clic = usar
            if (ctx.input.getPointerUp(0) && !Desk.dragged && ctx.time.frameCount - Desk.usedFrame > 2) {
                Desk.usedFrame = ctx.time.frameCount;
                g.opt.onUse?.({ kind: "desk" }, this.mouseRay());
            }
        }

        // ----- VR -----
        const session = ctx.xr;
        if (xr && session) {
            for (const c of session.controllers) {
                const sq = c.getButton("xr-standard-squeeze") ?? c.getButton("pinch" as any);
                const tr = c.getButton("xr-standard-trigger");
                const held = this.xrHeld.get(c);
                if (!held && sq?.isDown) {
                    const gp = c.gripWorldPosition;
                    let best: Grabbable | null = null, bd = 1e9;
                    for (const g of this.items) {
                        if (g.holder || (g.opt.canGrab && !g.opt.canGrab())) continue;
                        const dist = g.worldCenter().distanceTo(gp) - Math.min(g.radius, 0.15);
                        if (dist < 0.1 && dist < bd) { bd = dist; best = g; }
                    }
                    if (best) this.grab(best, { kind: "xr", ctrl: c });
                } else if (held) {
                    this.poseInHand(held, c);
                    this.track(held, t);
                    if (held.opt.spin) {
                        // joystick: girar lo que tienes (con la muñeca se completa el tercer eje)
                        const st = c.getStick("xr-standard-thumbstick" as any);
                        const dt = ctx.time.deltaTime * 3;
                        if (st && (Math.abs(st.x) > 0.15 || Math.abs(st.y) > 0.15)) this.spinBy(held, -st.y * dt, st.x * dt, 0);
                    }
                    if (tr?.isDown && t - held.grabTime > 0.4) {
                        const ray = new Ray(c.rayWorldPosition.clone(), this.aimDir(c));
                        held.opt.onUse?.({ kind: "xr", ctrl: c }, ray);
                    }
                    if (held.sticky) { if (sq?.pressed) held.sticky = false; }
                    else if (sq?.isUp || (sq && !sq.pressed)) this.release(held);
                }
            }
        }

        // con un premio en la mano en VR, el joystick gira el premio en vez de teletransportar
        if (this.mov === undefined) this.mov = findObjectOfType(XRControllerMovement, ctx);
        if (this.mov && xr) {
            let spinning = false; this.xrHeld.forEach(g => { if (g.opt.spin) spinning = true; });
            const want = !spinning && !Intro.blocking;
            if (this.mov.enabled !== want) this.mov.enabled = want;
        }

        // ----- velocidad de lanzamiento pendiente -----
        for (const g of this.items) {
            if (!g.pendingVel || g.pendingFrames <= 0 || g.holder || !g.opt.rb) continue;
            if (g.opt.rb.isKinematic) g.opt.rb.isKinematic = false;
            if (g.pendingFrames === 3) g.opt.rb.setVelocity(g.pendingVel.x, g.pendingVel.y, g.pendingVel.z);
            else { const cur = g.opt.rb.getVelocity(); if (cur.length() < g.pendingVel.length() * 0.5) g.opt.rb.setVelocity(g.pendingVel.x, g.pendingVel.y, g.pendingVel.z); }
            g.pendingFrames--;
        }

        // ----- volver a casa -----
        for (const g of this.items) {
            if (g.holder || !g.returning) continue;
            g.returning += ctx.time.deltaTime / 0.5;
            const k = Math.min(1, g.returning);
            const p = g.obj.getWorldPosition(new Vector3()).lerp(g.homePos, k);
            const q = g.obj.getWorldQuaternion(new Quaternion()).slerp(g.homeQuat, k);
            g.obj.worldPosition = p; g.obj.worldQuaternion = q;
            if (k >= 1) g.returning = 0;
        }
    }

    /** Dirección hacia donde apunta el control (la misma del rayo láser). */
    private aimDir(c: NeedleXRController) {
        const r = c.ray; return r ? r.direction.clone().normalize() : new Vector3(0, 0, -1).applyQuaternion(c.rayWorldQuaternion);
    }

    private poseInHand(g: Grabbable, c: NeedleXRController) {
        const h = g.opt.hold;
        if (h && h.aim) {
            // la pieza se arma con su eje +X hacia donde apunta el control y +Y hacia arriba del control
            const fwd = this.aimDir(c);
            let up = new Vector3(0, 1, 0).applyQuaternion(c.gripWorldQuaternion);
            const side = new Vector3().crossVectors(fwd, up);
            if (side.lengthSq() < 1e-4) side.set(1, 0, 0);
            side.normalize(); up = new Vector3().crossVectors(side, fwd).normalize();
            // columnas: X = adelante, Y = arriba, Z = X × Y
            const m = new Matrix4().makeBasis(fwd, up, new Vector3().crossVectors(fwd, up).normalize());
            g.obj.worldQuaternion = new Quaternion().setFromRotationMatrix(m);
            g.obj.worldPosition = c.gripWorldPosition.clone().add(fwd.clone().multiplyScalar(h.forward ?? 0.05));
        } else if (h) {
            const q = c.gripWorldQuaternion.clone().multiply(g.spin).multiply(qFrom(h.rot));
            g.obj.worldQuaternion = q;
            g.obj.worldPosition = c.gripWorldPosition.clone().add(new Vector3(...h.pos).applyQuaternion(c.gripWorldQuaternion));
        } else {
            const grip = new Matrix4().compose(c.gripWorldPosition, c.gripWorldQuaternion, new Vector3(1, 1, 1));
            const mm = grip.multiply(g.rel);
            const p = new Vector3(), q = new Quaternion(), s2 = new Vector3();
            mm.decompose(p, q, s2);
            g.obj.worldPosition = p; g.obj.worldQuaternion = q;
        }
        if (g.opt.rb) g.opt.rb.teleport(g.obj.worldPosition);
    }

    private track(g: Grabbable, t: number) {
        g.history.push({ p: g.obj.getWorldPosition(new Vector3()), t });
        while (g.history.length > 6) g.history.shift();
    }
}

export const Hands = new HandsImpl();

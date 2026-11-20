import { Context, Rigidbody, SphereCollider, CollisionDetectionMode } from "@needle-tools/engine";
import { Object3D, Ray, Vector3 } from "three";
import { Hands, Holder, Grabbable } from "./hand";
import { LedDisplay } from "./screens";
import { Tickets } from "./tickets";
import { sfx } from "./sfx";
import { invisibleWall, worldPos } from "./util";

const G = new Vector3(0, -9.81, 0);

function ballistic(from: Vector3, to: Vector3, T: number) {
    return to.clone().sub(from).sub(G.clone().multiplyScalar(0.5 * T * T)).divideScalar(T);
}

/** Mini basket: agarrar un balón y lanzarlo. Cada canasta = 10 tickets. */
export class Basket {
    balls: { g: Grabbable; prevY: number; idle: number }[] = [];
    hoop = new Vector3();
    display?: LedDisplay;
    score = 0;
    constructor(private ctx: Context, byName: Map<string, Object3D>) {
        const aro = byName.get("Basket_Aro");
        if (!aro) return;
        this.hoop = worldPos(aro);
        const disp = byName.get("Basket_Display");
        if (disp) { this.display = new LedDisplay(disp); this.display.set("¡ENCESTA!", "#ff8a1e", "10 TICKETS X CANASTA"); }
        // bandeja y redes laterales con colisión
        for (const n of ["Basket_Bandeja", "Basket_Bandeja_Borde", "Basket_Red_-1", "Basket_Red_1"]) {
            const o = byName.get(n); if (o) invisibleWall(ctx, o, 0.08);
        }
        for (let i = 1; i <= 4; i++) {
            const b = byName.get("Ball_" + i); if (!b) continue;
            b.addComponent(SphereCollider, { radius: 0.12 } as any);
            const rb = b.addComponent(Rigidbody, { mass: 0.6, collisionDetectionMode: CollisionDetectionMode.Continuous } as any);
            const g = Hands.register(b, {
                rb,
                desk: { pos: [0.18, -0.22, -0.5], rot: [0, 0, 0] },
                onUse: (_h, ray) => this.deskThrow(g, ray),
                onRelease: (v, h) => { if (h.kind === "xr") this.assist(g, v); },
            });
            this.balls.push({ g, prevY: worldPos(b).y, idle: 0 });
        }
    }

    /** En PC: lanzar hacia donde apunta el mouse. Si apuntas al aro, te ayuda un poco (no siempre entra). */
    private deskThrow(g: Grabbable, ray: Ray) {
        const from = worldPos(g.obj);
        const toHoop = this.hoop.clone().sub(from);
        const ang = ray.direction.angleTo(toHoop.clone().normalize());
        let v: Vector3;
        if (ang < 0.45) {
            const err = Math.sqrt(Math.random()) * 0.17, a = Math.random() * Math.PI * 2;
            const target = this.hoop.clone().add(new Vector3(Math.cos(a) * err, 0.02, Math.sin(a) * err));
            const T = Math.min(1.3, Math.max(0.75, toHoop.length() * 0.28 + 0.45));
            v = ballistic(from, target, T);
        } else {
            v = ray.direction.clone().multiplyScalar(6.5).add(new Vector3(0, 2.2, 0));
        }
        Hands.release(g, v);
    }

    /** En VR: si el lanzamiento va más o menos hacia el aro, lo corrige un poco. */
    private assist(g: Grabbable, v: Vector3) {
        const from = worldPos(g.obj);
        const toHoop = this.hoop.clone().sub(from);
        if (v.length() < 1.2 || v.clone().setY(0).angleTo(toHoop.clone().setY(0)) > 0.5) return;
        const T = Math.min(1.2, Math.max(0.6, toHoop.length() / Math.max(2.5, v.length())));
        v.lerp(ballistic(from, this.hoop.clone().add(new Vector3(0, 0.02, 0)), T), 0.55);
    }

    update() {
        const dt = this.ctx.time.deltaTime;
        for (const b of this.balls) {
            const p = worldPos(b.g.obj);
            if (!b.g.holder) {
                const dx = p.x - this.hoop.x, dz = p.z - this.hoop.z;
                if (b.prevY > this.hoop.y && p.y <= this.hoop.y && Math.hypot(dx, dz) < 0.17) this.basket();
                // si se va lejos o se queda quieto fuera de la bandeja: vuelve
                b.idle += dt;
                const far = p.distanceTo(b.g.homePos) > 0.5;
                if (p.y < -0.5 || p.distanceTo(this.hoop) > 9 || (far && b.idle > 7)) { b.g.goHome(); b.idle = 0; }
                if (!far) b.idle = 0;
            } else b.idle = 0;
            b.prevY = p.y;
        }
    }

    private basket() {
        this.score++;
        Tickets.add(10);
        sfx.win();
        this.display?.set(`¡CANASTA!`, "#00ff88", `TOTAL: ${this.score}`);
    }
}

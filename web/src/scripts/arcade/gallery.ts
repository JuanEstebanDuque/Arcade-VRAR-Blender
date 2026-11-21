import { BoxCollider, Context, Rigidbody } from "@needle-tools/engine";
import { BufferGeometry, Line, LineBasicMaterial, Mesh, Object3D, Quaternion, Ray, Vector3, Euler } from "three";
import { Hands, Grabbable, Holder } from "./hand";
import { Tickets } from "./tickets";
import { sfx } from "./sfx";
import { raySphere, staticCollider, worldPos } from "./util";

type Target = { obj: Object3D; base: Vector3; baseQ: Quaternion; axis: Vector3; phase: number; down: number; flip: number; sign: number };
type Can = { obj: Object3D; rb: Rigidbody; home: Vector3; homeQ: Quaternion; hit: boolean };

/** Galería de tiro: agarra una pistola y dispara. Diana = 10 tickets, lata = 5. */
export class Gallery {
    targets: Target[] = [];
    cans: Can[] = [];
    guns: Grabbable[] = [];
    resetCans = 0;
    t = 0;
    private tracer: Line;
    private tracerTime = 0;
    private recoil = new Map<Grabbable, number>();

    constructor(private ctx: Context, byName: Map<string, Object3D>) {
        const counter = byName.get("S_Tiro_Mostrador");
        const counterPos = counter ? worldPos(counter) : new Vector3();
        const t1 = byName.get("Target_1"), t4 = byName.get("Target_4");
        const axis = t1 && t4 ? worldPos(t4).sub(worldPos(t1)).setY(0).normalize() : new Vector3(0, 0, 1);
        for (let k = 1; k <= 8; k++) {
            const o = byName.get("Target_" + k); if (!o) continue;
            const base = o.position.clone();
            const away = worldPos(o).sub(counterPos).setY(0).normalize();
            const top = new Vector3(0, 1, 0).applyQuaternion(new Quaternion().setFromAxisAngle(axis, Math.PI / 2));
            const sign = top.dot(away) >= 0 ? 1 : -1;
            this.targets.push({ obj: o, base, baseQ: o.quaternion.clone(), axis, phase: k > 4 ? Math.PI : 0, down: 0, flip: 0, sign });
        }
        const shelf = byName.get("Tiro_Repisa_Latas"); if (shelf) staticCollider(shelf);
        for (let k = 1; k <= 6; k++) {
            const o = byName.get("Can_" + k) as Mesh | undefined; if (!o) continue;
            const col = BoxCollider.add(o, { rigidbody: true });
            const rb = o.getComponent(Rigidbody)!;
            rb.isKinematic = true;
            this.cans.push({ obj: o, rb, home: worldPos(o), homeQ: o.getWorldQuaternion(new Quaternion()), hit: false });
        }
        for (let i = 1; i <= 2; i++) {
            const gun = byName.get("Gun_" + i); const muzzle = byName.get(`Gun_${i}_Muzzle`);
            if (!gun || !muzzle) continue;
            const g = Hands.register(gun, {
                returnHome: true,
                hold: { pos: [0, 0, 0], rot: [0, 0, 0], aim: true, forward: 0.04 },
                desk: { pos: [0.22, -0.2, -0.45], rot: [0, 90, 0] },
                onUse: (h, ray) => this.shoot(g, muzzle, h, ray),
            });
            this.guns.push(g);
        }
        this.tracer = new Line(new BufferGeometry().setFromPoints([new Vector3(), new Vector3()]),
            new LineBasicMaterial({ color: 0xff3cac, transparent: true, opacity: 0.9 }));
        // se deja visible el primer segundo (de largo cero) para que el shader se compile al cargar y no al primer disparo
        this.tracer.visible = true; this.tracer.frustumCulled = false; this.tracerTime = 1.0;
        ctx.scene.add(this.tracer);
    }

    private shoot(g: Grabbable, muzzle: Object3D, h: Holder, ray: Ray) {
        sfx.shoot();
        this.recoil.set(g, 0.12);
        const origin = h.kind === "desk" ? ray.origin : worldPos(muzzle);
        const dir = ray.direction.clone().normalize();
        let bestT = 12; let hit: { kind: "t"; t: Target } | { kind: "c"; c: Can } | null = null;
        for (const t of this.targets) {
            if (t.down > 0) continue;
            const d = raySphere(origin, dir, worldPos(t.obj), 0.14);
            if (d !== null && d < bestT) { bestT = d; hit = { kind: "t", t }; }
        }
        for (const c of this.cans) {
            if (c.hit) continue;
            const d = raySphere(origin, dir, worldPos(c.obj), 0.065);
            if (d !== null && d < bestT) { bestT = d; hit = { kind: "c", c }; }
        }
        const end = origin.clone().add(dir.clone().multiplyScalar(bestT));
        const pos = this.tracer.geometry.attributes.position as any;
        const m = worldPos(muzzle);
        pos.setXYZ(0, m.x, m.y, m.z); pos.setXYZ(1, end.x, end.y, end.z); pos.needsUpdate = true;
        this.tracer.visible = true; this.tracerTime = 0.08;
        if (!hit) return;
        if (hit.kind === "t") {
            hit.t.down = 2.5; sfx.hit(); Tickets.add(10);
        } else {
            const c = hit.c; c.hit = true;
            c.rb.isKinematic = false;
            c.rb.setVelocity(dir.x * 3, 1.5 + dir.y * 3, dir.z * 3);
            c.rb.setAngularVelocity(Math.random() * 8, Math.random() * 8, Math.random() * 8);
            sfx.pop(); Tickets.add(5);
            if (!this.resetCans) this.resetCans = 6;
        }
    }

    update() {
        const dt = this.ctx.time.deltaTime; this.t += dt;
        for (const t of this.targets) {
            // se mueven por el riel; la fila de arriba en sentido contrario
            const off = Math.sin(this.t * 0.9 + t.phase) * 0.22;
            t.obj.position.copy(t.base).add(t.axis.clone().multiplyScalar(off));
            if (t.down > 0) { t.down -= dt; t.flip = Math.min(1, t.flip + dt * 8); }
            else t.flip = Math.max(0, t.flip - dt * 3);
            t.obj.quaternion.copy(new Quaternion().setFromAxisAngle(t.axis, t.sign * t.flip * Math.PI / 2).multiply(t.baseQ));
        }
        if (this.resetCans > 0) {
            this.resetCans -= dt;
            if (this.resetCans <= 0 || this.cans.every(c => c.hit) && this.resetCans < 4.5) {
                this.resetCans = 0;
                for (const c of this.cans) {
                    c.hit = false; c.rb.isKinematic = true; c.rb.resetVelocities();
                    c.obj.worldPosition = c.home; c.obj.worldQuaternion = c.homeQ; c.rb.teleport(c.home);
                }
            }
        }
        if (this.tracerTime > 0) { this.tracerTime -= dt; if (this.tracerTime <= 0) this.tracer.visible = false; }
        // retroceso al disparar
        this.recoil.forEach((r, g) => {
            if (r <= 0 || !g.holder) return;
            this.recoil.set(g, r - dt);
            const k = Math.sin((r / 0.12) * Math.PI) * 0.25;
            g.obj.worldQuaternion = g.obj.worldQuaternion.multiply(new Quaternion().setFromEuler(new Euler(0, 0, k)));
        });
    }
}

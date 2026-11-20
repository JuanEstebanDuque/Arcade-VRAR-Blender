import { Behaviour, Context, PointerEventData } from "@needle-tools/engine";
import { Object3D, Vector3 } from "three";
import { Hands, Grabbable } from "./hand";
import { sfx } from "./sfx";
import { inXR, isDeskClick, setCursor } from "./state";
import { worldPos } from "./util";

class DoorClick extends Behaviour {
    fridge!: Fridge;
    onPointerEnter() { if (!inXR(this.context)) setCursor(true); }
    onPointerExit() { setCursor(false); }
    onPointerClick(e: PointerEventData) {
        if (e.mode === "screen" && !isDeskClick(this.context, e.mode)) return;
        this.fridge.toggle();
    }
}

/** Nevera: abrir/cerrar la puerta y tomarse una gaseosa. */
export class Fridge {
    hinge?: Object3D;
    handle?: Object3D;
    open = false;
    angle = 0;
    cans: { g: Grabbable; gone: number }[] = [];

    constructor(private ctx: Context, byName: Map<string, Object3D>) {
        this.hinge = byName.get("Nevera_Bisagra");
        this.handle = byName.get("Fridge_Handle");
        if (this.hinge) { const c = this.hinge.addComponent(DoorClick); c.fridge = this; }
        byName.forEach((o, n) => {
            if (!n.startsWith("Nevera_Lata_")) return;
            const g = Hands.register(o, {
                returnHome: true,
                canGrab: () => this.open,
                desk: { pos: [0.2, -0.22, -0.45], rot: [0, 0, 0] },
                onUse: () => this.drink(g),
            });
            this.cans.push({ g, gone: 0 });
        });
    }

    toggle() { this.open = !this.open; sfx.door(); }

    private drink(g: Grabbable) {
        // glu glu
        sfx.pop(); setTimeout(() => sfx.pop(), 140); setTimeout(() => sfx.pop(), 280);
        Hands.release(g);
        g.returning = 0;
        g.goHome();
        g.obj.visible = false;
        const c = this.cans.find(x => x.g === g); if (c) c.gone = 6;
    }

    update() {
        const dt = this.ctx.time.deltaTime;
        const target = this.open ? -1.6 : 0;
        this.angle += (target - this.angle) * Math.min(1, dt * 6);
        if (this.hinge) this.hinge.rotation.y = this.angle;
        for (const c of this.cans) if (c.gone > 0) { c.gone -= dt; if (c.gone <= 0) c.g.obj.visible = true; }
        // en VR: apretar el botón de agarre cerca de la manija abre/cierra
        const xr = this.ctx.xr;
        if (inXR(this.ctx) && xr && this.handle) {
            const hp = worldPos(this.handle);
            for (const ctrl of xr.controllers) {
                const sq = ctrl.getButton("xr-standard-squeeze");
                if (sq?.isDown && ctrl.gripWorldPosition.distanceTo(hp) < 0.18) this.toggle();
            }
        }
    }
}

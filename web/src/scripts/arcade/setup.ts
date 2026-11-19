import { onStart, onUpdate, findObjectOfType, WebXR, XRControllerMovement, TeleportTarget, BoxCollider, Context } from "@needle-tools/engine";
import { Mesh, Object3D } from "three";
import { Tickets } from "./tickets";
import { setupWheel } from "./wheel";
import { MeshBasicMaterial } from "three";

/**
 * Punto de entrada del arcade. Recorre la escena exportada desde Blender y,
 * según el nombre de cada objeto, le agrega su comportamiento.
 *   S_*        colisionador estático
 *   FLOOR      piso: colisionador + destino de teletransporte
 *   REF_*      se oculta (referencias de escala)
 *   Scoreboard / Scoreboard_Big   marcadores de tickets
 */
export function setupArcade() {
    onStart(ctx => {
        const byName = new Map<string, Object3D>();
        ctx.scene.traverse(o => byName.set(o.name, o));

        ctx.scene.traverse(o => {
            if (o.name.startsWith("REF_")) o.visible = false;
            if (o.name.startsWith("S_") && (o as Mesh).isMesh) BoxCollider.add(o as Mesh);
        });

        // Piso: colisionador y único lugar donde se puede teletransportar
        const floor = byName.get("FLOOR");
        if (floor) {
            BoxCollider.add(floor as Mesh);
            floor.addComponent(TeleportTarget);
        }

        setupLocomotion(ctx);

        // Volúmenes de detección: invisibles pero activos
        for (const n of ["Hoop_Trigger"]) {
            const o = byName.get(n) as Mesh | undefined;
            if (o) o.material = new MeshBasicMaterial({ visible: false });
        }

        // Juegos
        setupWheel(byName);

        // Marcadores
        const s1 = byName.get("Scoreboard"); if (s1) Tickets.attachBoard(s1, "TUS TICKETS");
        const s2 = byName.get("Scoreboard_Big"); if (s2) Tickets.attachBoard(s2, "TICKETS");

        // Atajos para probar en el computador: T = +10 tickets, R = reiniciar
        window.addEventListener("keydown", e => {
            if (e.key === "t" || e.key === "T") Tickets.add(10);
            if (e.key === "r" || e.key === "R") Tickets.reset();
        });
        (window as any).tickets = Tickets;
    });

    onUpdate(ctx => Tickets.update(ctx.time.deltaTime));
}

/** Solo teletransporte (sin caminar con joystick) para evitar mareo. */
function setupLocomotion(ctx: Context) {
    const webxr = findObjectOfType(WebXR, ctx);
    if (!webxr) { console.warn("[Arcade] No hay componente WebXR en la escena"); return; }
    let mov = webxr.gameObject.getComponent(XRControllerMovement);
    if (!mov) mov = webxr.gameObject.addComponent(XRControllerMovement);
    mov.movementSpeed = 0;        // sin desplazamiento continuo
    mov.useTeleport = true;
    mov.useTeleportTarget = true; // solo se puede caer en el piso, no encima de mesas
    mov.useTeleportFade = true;
    mov.rotationStep = 30;        // giro por pasos con el joystick derecho
    mov.showRays = true;
}

import { onStart, onUpdate, findObjectOfType, WebXR, XRControllerMovement, TeleportTarget, BoxCollider, Context } from "@needle-tools/engine";
import { Mesh, Object3D } from "three";
import { Tickets } from "./tickets";
import { setupWheel } from "./wheel";
import { Hands } from "./hand";
import { DesktopWalker } from "./walker";
import { Basket } from "./basket";
import { MoleGame } from "./mole";
import { Gallery } from "./gallery";
import { Fridge } from "./fridge";
import { PrizeShop } from "./prizes";
import { Cabinets } from "./cabinets";
import { staticCollider } from "./util";
import { Box3 } from "three";
import { MeshBasicMaterial } from "three";

/**
 * Punto de entrada del arcade. Recorre la escena exportada desde Blender y,
 * según el nombre de cada objeto, le agrega su comportamiento.
 *   S_*        colisionador estático
 *   FLOOR      piso: colisionador + destino de teletransporte
 *   REF_*      se oculta (referencias de escala)
 *   Scoreboard / Scoreboard_Big   marcadores de tickets
 */
let walker: DesktopWalker | undefined;
const games: { update(): void }[] = [];

export function setupArcade() {
    onStart(ctx => {
        const byName = new Map<string, Object3D>();
        ctx.scene.traverse(o => byName.set(o.name, o));

        ctx.scene.traverse(o => {
            if (o.name.startsWith("REF_")) o.visible = false;
            if (o.name.startsWith("S_")) staticCollider(o);
        });

        // Piso: colisionador y único lugar donde se puede teletransportar
        const floor = byName.get("FLOOR");
        if (floor) {
            BoxCollider.add(floor as Mesh);
            floor.addComponent(TeleportTarget);
        }

        setupLocomotion(ctx);

        // El tope del mostrador también choca (ahí se apoyan los premios ganados)
        const tope = byName.get("Mostrador_Tope"); if (tope) staticCollider(tope);

        // Volúmenes de detección: invisibles pero activos
        for (const n of ["Hoop_Trigger"]) {
            const o = byName.get(n) as Mesh | undefined;
            if (o) o.material = new MeshBasicMaterial({ visible: false });
        }

        // Juegos
        Hands.init(ctx);
        setupWheel(byName);
        games.push(new Basket(ctx, byName), new MoleGame(ctx, byName), new Gallery(ctx, byName),
            new Fridge(ctx, byName), new PrizeShop(ctx, byName), new Cabinets(ctx, byName));

        // Caminar en PC: chocar con muebles y máquinas
        const roots: Object3D[] = [];
        byName.forEach((o, n) => {
            if (/^(S_(?!Pared)|Arcade_\d$|Carreras_Moderna$|Baile_Moderna$|Rueda$|Nevera$|Maquina_Cambio$|Caneca$)/.test(n)) roots.push(o);
        });
        const room = floor ? new Box3().setFromObject(floor) : new Box3();
        walker = new DesktopWalker(ctx, roots, room);
        (window as any).__arcade = { walker, hands: Hands, games, tickets: Tickets, byName };

        // Marcadores
        const s1 = byName.get("Scoreboard"); if (s1) Tickets.attachBoard(s1, "TUS TICKETS");
        const s2 = byName.get("Scoreboard_Big"); if (s2) Tickets.attachBoard(s2, "TICKETS");

        // Atajos para probar en el computador: T = +10 tickets, R = reiniciar
        window.addEventListener("keydown", e => {
            if (e.key === "t" || e.key === "T") Tickets.add(10);
            if (e.key === "r" || e.key === "R") Tickets.reset();   // también borra los premios ganados
        });
        (window as any).tickets = Tickets;
    });

    onUpdate(ctx => {
        Tickets.update(ctx.time.deltaTime);
        walker?.update();
        Hands.update();
        for (const g of games) g.update();
    });
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

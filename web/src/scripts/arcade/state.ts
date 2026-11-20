import { Context } from "@needle-tools/engine";

/** Estado compartido de la entrada en PC (para distinguir clic de arrastrar). */
export const Desk = {
    /** el botón del mouse se movió más de unos píxeles desde que se presionó */
    dragged: false,
    /** un objeto (p. ej. la palanca) tomó el control del arrastre: no girar la cámara */
    captured: false,
    /** frame en el que la mano usó/soltó algo con un clic (para no agarrar otra cosa en el mismo clic) */
    usedFrame: -10,
};

export function inXR(ctx: Context) { return !!ctx.isInXR; }

/** ¿Este evento de clic viene del mouse en PC y no fue un arrastre? */
export function isDeskClick(ctx: Context, mode: string) {
    return !inXR(ctx) && mode === "screen" && !Desk.dragged && ctx.time.frameCount - Desk.usedFrame > 2;
}

export function setCursor(pointer: boolean) {
    document.body.style.cursor = pointer ? "pointer" : "";
}


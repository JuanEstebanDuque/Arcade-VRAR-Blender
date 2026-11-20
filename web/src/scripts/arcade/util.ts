import { BoxCollider, Context } from "@needle-tools/engine";
import { Box3, BoxGeometry, Mesh, MeshBasicMaterial, Object3D, Vector3 } from "three";

const HIDDEN = new MeshBasicMaterial({ visible: false });

/** Pared invisible con colisionador a partir de la caja (en mundo) de un objeto. minThick evita que la pelota atraviese redes delgadas. */
export function invisibleWall(ctx: Context, src: Object3D, minThick = 0.08) {
    const b = new Box3().setFromObject(src);
    const size = b.getSize(new Vector3()); const c = b.getCenter(new Vector3());
    size.set(Math.max(size.x, minThick), Math.max(size.y, minThick), Math.max(size.z, minThick));
    const m = new Mesh(new BoxGeometry(size.x, size.y, size.z), HIDDEN);
    m.position.copy(c); ctx.scene.add(m);
    BoxCollider.add(m);
    return m;
}

/** Colisionador para objetos de Blender (si el objeto tiene varios materiales, three lo vuelve un grupo de mallas). */
export function staticCollider(o: Object3D) {
    if ((o as Mesh).isMesh) { BoxCollider.add(o as Mesh); return; }
    o.children.forEach(ch => { if ((ch as Mesh).isMesh) BoxCollider.add(ch as Mesh); });
}

export function worldPos(o: Object3D) { return o.getWorldPosition(new Vector3()); }

/** Distancia de un punto a un rayo y parámetro t (para impactos de disparo). */
export function raySphere(origin: Vector3, dir: Vector3, center: Vector3, r: number): number | null {
    const oc = origin.clone().sub(center);
    const b = oc.dot(dir); const c = oc.lengthSq() - r * r;
    const h = b * b - c; if (h < 0) return null;
    const t = -b - Math.sqrt(h);
    return t > 0 ? t : null;
}

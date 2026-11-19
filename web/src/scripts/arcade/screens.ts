import { Mesh, Object3D, PlaneGeometry, Vector3, Box3, Material } from "three";

const ROOM_CENTER = new Vector3(0, 1.6, 0);

/**
 * Crea un plano (con UVs) pegado a la cara de un objeto "pantalla" que mira hacia el centro del cuarto.
 * Los cubos que vienen de Blender no tienen UVs; este plano sí, así que podemos ponerle texturas o shaders.
 */
export function makeScreenPlane(obj: Object3D, material: Material, inset = 0.92): Mesh | null {
    const mesh = obj as Mesh;
    if (!mesh.geometry) return null;
    mesh.geometry.computeBoundingBox();
    const bb = mesh.geometry.boundingBox as Box3;
    const size = new Vector3(); bb.getSize(size);
    const center = new Vector3(); bb.getCenter(center);

    // eje más delgado = normal de la pantalla
    const axes: ("x" | "y" | "z")[] = ["x", "y", "z"];
    axes.sort((a, b) => size[a] - size[b]);
    const thin = axes[0];
    const others = axes.slice(1) as ("x" | "y" | "z")[];

    // escoger la cara que mira al centro del cuarto
    obj.updateWorldMatrix(true, false);
    const n = new Vector3(); n[thin] = 1;
    const worldN = n.clone().transformDirection(obj.matrixWorld);
    const worldPos = obj.getWorldPosition(new Vector3());
    const toCenter = ROOM_CENTER.clone().sub(worldPos);
    const sign = worldN.dot(toCenter) >= 0 ? 1 : -1;

    // ancho/alto: el eje más vertical en mundo es el alto
    const upLocal = new Vector3(0, 1, 0).transformDirection(obj.matrixWorld.clone().invert());
    let hAxis = others[0], wAxis = others[1];
    if (Math.abs(upLocal[others[1]]) > Math.abs(upLocal[others[0]])) { hAxis = others[1]; wAxis = others[0]; }

    const plane = new Mesh(new PlaneGeometry(size[wAxis] * inset, size[hAxis] * inset), material);
    plane.name = obj.name + "_Plane";

    // orientar el plano: su +Z = normal, su +Y = alto
    const zDir = n.clone().multiplyScalar(sign);
    const yDir = new Vector3(); yDir[hAxis] = Math.sign(upLocal[hAxis]) || 1;
    const xDir = new Vector3().crossVectors(yDir, zDir);
    const m = plane.matrix;
    m.makeBasis(xDir, yDir, zDir);
    plane.quaternion.setFromRotationMatrix(m);
    plane.position.copy(center);
    plane.position[thin] += sign * (size[thin] / 2 + 0.002);
    obj.add(plane);
    return plane;
}

import { CanvasTexture, MeshBasicMaterial, SRGBColorSpace } from "three";

/** Pantalla LED de texto (marcadores de cada juego). */
export class LedDisplay {
    private canvas = document.createElement("canvas");
    private tex: CanvasTexture;
    constructor(obj: Object3D, w = 512, h = 128) {
        this.canvas.width = w; this.canvas.height = h;
        this.tex = new CanvasTexture(this.canvas);
        this.tex.colorSpace = SRGBColorSpace;
        makeScreenPlane(obj, new MeshBasicMaterial({ map: this.tex, toneMapped: false }), 0.94);
    }
    set(text: string, color = "#ff3cac", sub?: string) {
        const g = this.canvas.getContext("2d")!; const w = this.canvas.width, h = this.canvas.height;
        g.fillStyle = "#07020f"; g.fillRect(0, 0, w, h);
        g.fillStyle = "rgba(255,255,255,0.035)";
        for (let x = 0; x < w; x += 6) for (let y = 0; y < h; y += 6) g.fillRect(x, y, 4, 4);
        g.textAlign = "center"; g.textBaseline = "middle";
        g.shadowColor = color; g.shadowBlur = 16; g.fillStyle = color;
        const size = sub ? h * 0.5 : h * 0.68;
        g.font = `bold ${size}px 'Courier New', monospace`;
        g.fillText(text, w / 2, sub ? h * 0.4 : h / 2);
        if (sub) {
            g.shadowColor = "#00e5ff"; g.fillStyle = "#00e5ff";
            g.font = `bold ${h * 0.26}px 'Courier New', monospace`;
            g.fillText(sub, w / 2, h * 0.82);
        }
        this.tex.needsUpdate = true;
    }
}

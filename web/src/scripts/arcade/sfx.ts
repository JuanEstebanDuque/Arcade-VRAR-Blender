// Sonidos sintetizados con WebAudio: originales, sin archivos ni derechos de autor.
let ctx: AudioContext | null = null;

function ac(): AudioContext | null {
    try {
        if (!ctx) ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
        if (ctx.state === "suspended") ctx.resume();
        return ctx;
    } catch { return null; }
}

function tone(freq: number, dur: number, type: OscillatorType = "square", vol = 0.08, slideTo?: number, delay = 0) {
    const a = ac(); if (!a) return;
    const t = a.currentTime + delay;
    const o = a.createOscillator();
    const g = a.createGain();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t + dur);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(a.destination);
    o.start(t); o.stop(t + dur + 0.02);
}

/** Melodía 8-bit corta (notas en Hz, 0 = silencio). */
export function chiptune(notes: number[], step = 0.14, vol = 0.035) {
    notes.forEach((f, i) => { if (f) tone(f, step * 0.9, "square", vol, undefined, i * step); });
    return notes.length * step;
}

export const sfx = {
    ticket: () => tone(1320, 0.06, "square", 0.05),
    win: () => { [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.12, "square", 0.07, undefined, i * 0.09)); },
    hit: () => tone(220, 0.12, "triangle", 0.15, 90),
    pop: () => tone(500, 0.08, "sine", 0.1, 900),
    tick: () => tone(1800, 0.02, "square", 0.03),
    shoot: () => tone(900, 0.15, "sawtooth", 0.06, 120),
    buzz: () => tone(110, 0.3, "sawtooth", 0.08),
    coin: () => { tone(988, 0.08, "square", 0.06); tone(1319, 0.25, "square", 0.06, undefined, 0.08); },
    door: () => tone(160, 0.25, "triangle", 0.08, 220),
};

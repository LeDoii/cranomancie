"use strict";
/* Living room: the painted candle flames were removed from the picture (see remove_flames.py); this draws animated flames at the same places and a
   flickering candlelight over the room. A canvas (half of the master resolution) sits in the room layer, so it follows zoom and pan with the picture.
   Drawn with mix-blend-mode: screen, which adds light to the painting. Paused when the tab is hidden; off by default for prefers-reduced-motion. */

const AMBIANCE_FLAMES = [   // master picture coordinates (3584 x 1536): wick x, wick y, flame height, flame half width, phase
  { x: 1388, y: 692, h: 26, w: 6, p: 0.3 }, { x: 1427, y: 659, h: 30, w: 7, p: 1.9 }, { x: 1463, y: 683, h: 27, w: 6, p: 3.4 },
  { x: 2094, y: 689, h: 26, w: 7, p: 5.1 }, { x: 2130, y: 661, h: 30, w: 7, p: 2.6 }, { x: 2160, y: 689, h: 28, w: 7, p: 4.2 }, { x: 2189, y: 693, h: 30, w: 7, p: 0.9 },
  { x: 2762, y: 567, h: 34, w: 9, p: 3.9 },
];
const AMBIANCE_SCALE = 0.5;       // canvas pixels per master pixel
const AMBIANCE_FPS = 30;

function ambianceNoise(t, seed) {   // smooth pseudo-random value in about [-1, 1]
  return 0.5 * Math.sin(t * 2.3 + seed) + 0.3 * Math.sin(t * 3.9 + seed * 1.7 + 1.3) + 0.2 * Math.sin(t * 7.1 + seed * 2.9 + 0.4);
}

function drawFlame(ctx, f, t) {
  const s = AMBIANCE_SCALE, sway = ambianceNoise(t, f.p) * 0.55 + ambianceNoise(t * 0.4, f.p + 9) * 0.35;      // lean left / right
  const hs = 1 + 0.10 * ambianceNoise(t * 1.6, f.p + 4), ws = 1 - 0.07 * ambianceNoise(t * 1.6, f.p + 4);
  const x = f.x * s, y = f.y * s, H = f.h * s * hs, W = f.w * s * ws, tip = x + sway * H * 0.32;
  const shape = (k, wk) => {
    const w = W * wk, h = H * k, tx = x + (tip - x) * k;
    ctx.beginPath();
    ctx.moveTo(x, y + 1 * s);
    ctx.bezierCurveTo(x - w * 1.25, y - h * 0.18, x - w * 0.55 + (tx - x) * 0.35, y - h * 0.72, tx, y - h);
    ctx.bezierCurveTo(x + w * 0.55 + (tx - x) * 0.35, y - h * 0.72, x + w * 1.25, y - h * 0.18, x, y + 1 * s);
    ctx.closePath();
  };
  ctx.fillStyle = "rgba(255,150,45,0.62)"; shape(1.08, 1.55); ctx.fill();
  ctx.fillStyle = "rgba(255,215,115,0.85)"; shape(0.86, 1.08); ctx.fill();
  ctx.fillStyle = "rgba(255,250,232,0.97)"; shape(0.56, 0.62); ctx.fill();
  ctx.fillStyle = "rgba(120,150,255,0.22)"; ctx.beginPath(); ctx.arc(x, y - 1.0 * s, 1.1 * s, 0, 7); ctx.fill();   // the blue base of a real flame
}

function glow(ctx, x, y, radius, alpha, rgb) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, radius);
  g.addColorStop(0, `rgba(${rgb},${alpha})`); g.addColorStop(0.45, `rgba(${rgb},${alpha * 0.38})`); g.addColorStop(1, `rgba(${rgb},0)`);
  ctx.fillStyle = g; ctx.fillRect(x - radius, y - radius, radius * 2, radius * 2);
}

function initAmbiance(box, getEnabled) {
  const W = Math.round(3584 * AMBIANCE_SCALE), H = Math.round(1536 * AMBIANCE_SCALE);
  const canvas = document.createElement("canvas"); canvas.className = "ambiance"; canvas.width = W; canvas.height = H; canvas.setAttribute("aria-hidden", "true");
  box.prepend(canvas);
  const ctx = canvas.getContext("2d");
  let raf = 0, last = 0, running = false;
  const draw = (t) => {
    ctx.clearRect(0, 0, W, H);
    const wind = ambianceNoise(t * 0.25, 2.1);                                    // a slow draught that moves all the flames a little together
    let mx = 0, my = 0;
    for (const f of AMBIANCE_FLAMES) {
      const flick = 0.5 + 0.5 * (ambianceNoise(t * 1.3, f.p) * 0.6 + ambianceNoise(t * 5.3, f.p + 3) * 0.4);   // 0..1
      const x = f.x * AMBIANCE_SCALE, y = (f.y - f.h * 0.55) * AMBIANCE_SCALE;
      glow(ctx, x, y, 300 * AMBIANCE_SCALE * (0.92 + 0.12 * flick), 0.12 + 0.07 * flick, "255,160,60");        // pool of light around the flame
      glow(ctx, x, y, 90 * AMBIANCE_SCALE, 0.10 + 0.08 * flick, "255,225,150");                               // bright halo close to it
      mx += x; my += y;
    }
    mx /= AMBIANCE_FLAMES.length; my /= AMBIANCE_FLAMES.length;
    glow(ctx, mx + wind * 40, my, 1500 * AMBIANCE_SCALE, 0.035 + 0.012 * ambianceNoise(t * 0.9, 5.5), "255,150,50");  // the whole room breathes
    for (const f of AMBIANCE_FLAMES) drawFlame(ctx, { ...f, p: f.p }, t + wind * 0.2);
  };
  const frame = (now) => {
    raf = requestAnimationFrame(frame);
    if (now - last < 1000 / AMBIANCE_FPS) return;
    last = now;
    draw(now / 1000);
  };
  const start = () => { if (!running) { running = true; canvas.style.display = ""; raf = requestAnimationFrame(frame); } };
  const stop = () => { running = false; cancelAnimationFrame(raf); ctx.clearRect(0, 0, W, H); canvas.style.display = "none"; };
  const apply = () => (getEnabled() && !document.hidden ? start() : stop());
  document.addEventListener("visibilitychange", apply);
  apply();
  return { apply, draw, show: () => { canvas.style.display = ""; } };   // draw/show: one still frame (tests, hidden tabs)
}

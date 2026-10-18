"use strict";
/* Reading card of CRANOMANCIE 2000: drawn on a canvas (1240 x 1754 = A5 at 150 dpi), exported as PNG or as a one-page PDF.
   Four templates, chosen by the number of favourable signs (3, 2, 1, 0). Everything is drawn here: no library, no image file. */

const CARD = { W: 1240, H: 1754 };
const CARD_TEMPLATES = {
  3: { name: "Présage très favorable", emblem: "sun", paper: ["#F1E4BE", "#E4D1A0"], ink: "#2E2415", accent: "#8A6A12", border: "#B88A1E",
       good: "#3F7A33", bad: "#9A3B2D", sub: "Les signes s’accordent." },
  2: { name: "Présage favorable", emblem: "star", paper: ["#EFE3C6", "#E0D0A8"], ink: "#2E2718", accent: "#6F6A24", border: "#9C7A2C",
       good: "#3F7A33", bad: "#9A3B2D", sub: "Un point de vigilance demeure." },
  1: { name: "Présage mitigé", emblem: "moon", paper: ["#E4E0D2", "#D2CDBB"], ink: "#272A2E", accent: "#4A5D72", border: "#6B7B8E",
       good: "#3F7A33", bad: "#9A3B2D", sub: "Un appui, deux signes de prudence." },
  0: { name: "Avertissement", emblem: "skull", paper: ["#CDBFA2", "#B3A17F"], ink: "#1E1712", accent: "#7A2A22", border: "#7A2A22",
       good: "#3F7A33", bad: "#8E2A20", sub: "Le crâne parle avec gravité." },
};

function cardFontsReady() {
  return Promise.all([document.fonts.load('60px "Italiana"'), document.fonts.load('30px "Crimson Pro"'), document.fonts.load('italic 30px "Crimson Pro"'),
    document.fonts.load('22px "Geist Mono"')]).catch(() => {});
}

function seeded(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

function wrapLines(ctx, text, maxWidth, maxLines) {
  const words = text.split(/\s+/), lines = []; let cur = "";
  for (const w of words) {
    const test = cur ? cur + " " + w : w;
    if (ctx.measureText(test).width <= maxWidth || !cur) cur = test; else { lines.push(cur); cur = w; }
  }
  if (cur) lines.push(cur);
  if (maxLines && lines.length > maxLines) { lines.length = maxLines; lines[maxLines - 1] = lines[maxLines - 1].replace(/[\s,;:.]*$/, "") + "…"; }
  return lines;
}

function drawEmblem(ctx, kind, cx, cy, r, color, ink) {
  ctx.save(); ctx.translate(cx, cy); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 5; ctx.lineCap = "round"; ctx.lineJoin = "round";
  if (kind === "sun") {
    ctx.beginPath(); ctx.arc(0, 0, r * 0.42, 0, 7); ctx.fill();
    for (let i = 0; i < 16; i++) { const a = i * Math.PI / 8, long = i % 2 === 0; ctx.beginPath();
      ctx.moveTo(Math.cos(a) * r * 0.58, Math.sin(a) * r * 0.58); ctx.lineTo(Math.cos(a) * r * (long ? 1 : 0.8), Math.sin(a) * r * (long ? 1 : 0.8)); ctx.stroke(); }
  } else if (kind === "star") {
    ctx.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rad = i % 2 ? r * 0.42 : r; ctx.lineTo(Math.cos(a) * rad, Math.sin(a) * rad); }
    ctx.closePath(); ctx.fill(); ctx.beginPath(); ctx.arc(0, 0, r * 1.12, 0, 7); ctx.lineWidth = 3; ctx.stroke();
  } else if (kind === "moon") {
    ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.lineWidth = 4; ctx.stroke();
    ctx.beginPath(); ctx.arc(0, 0, r * 0.8, Math.PI / 2, -Math.PI / 2, false); ctx.arc(r * 0.28, 0, r * 0.72, -Math.PI / 2 + 0.55, Math.PI / 2 - 0.55, true); ctx.closePath(); ctx.fill();
  } else {  // skull
    ctx.beginPath(); ctx.moveTo(-r * 0.62, r * 0.12); ctx.bezierCurveTo(-r * 0.7, -r * 0.95, r * 0.7, -r * 0.95, r * 0.62, r * 0.12);
    ctx.lineTo(r * 0.4, r * 0.34); ctx.lineTo(r * 0.4, r * 0.7); ctx.lineTo(-r * 0.4, r * 0.7); ctx.lineTo(-r * 0.4, r * 0.34); ctx.closePath(); ctx.fill();
    ctx.fillStyle = ink; ctx.beginPath(); ctx.ellipse(-r * 0.27, -r * 0.05, r * 0.18, r * 0.22, 0, 0, 7); ctx.ellipse(r * 0.27, -r * 0.05, r * 0.18, r * 0.22, 0, 0, 7); ctx.fill();
    ctx.beginPath(); ctx.moveTo(0, r * 0.12); ctx.lineTo(-r * 0.08, r * 0.3); ctx.lineTo(r * 0.08, r * 0.3); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = ink; ctx.lineWidth = 4; for (const x of [-0.2, 0, 0.2]) { ctx.beginPath(); ctx.moveTo(r * x, r * 0.48); ctx.lineTo(r * x, r * 0.7); ctx.stroke(); }
  }
  ctx.restore();
}

function drawCorner(ctx, x, y, sx, sy, color) {
  ctx.save(); ctx.translate(x, y); ctx.scale(sx, sy); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 4; ctx.lineCap = "round";
  ctx.beginPath(); ctx.moveTo(0, 90); ctx.lineTo(0, 22); ctx.quadraticCurveTo(0, 0, 22, 0); ctx.lineTo(90, 0); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(14, 70); ctx.lineTo(14, 30); ctx.quadraticCurveTo(14, 14, 30, 14); ctx.lineTo(70, 14); ctx.lineWidth = 2; ctx.stroke();
  ctx.beginPath(); ctx.arc(30, 30, 7, 0, 7); ctx.fill(); ctx.restore();
}

function drawCard(canvas, info) {
  const { W, H } = CARD, tpl = CARD_TEMPLATES[info.favorableCount];
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext("2d"), rnd = seeded(7 + info.favorableCount);
  // parchment
  const g = ctx.createLinearGradient(0, 0, W * 0.4, H); g.addColorStop(0, tpl.paper[0]); g.addColorStop(1, tpl.paper[1]);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 90; i++) { const x = rnd() * W, y = rnd() * H, r = 30 + rnd() * 160; const s = ctx.createRadialGradient(x, y, 0, x, y, r);
    s.addColorStop(0, `rgba(120,90,40,${0.035 + rnd() * 0.04})`); s.addColorStop(1, "rgba(120,90,40,0)"); ctx.fillStyle = s; ctx.fillRect(x - r, y - r, r * 2, r * 2); }
  for (let i = 0; i < 700; i++) { ctx.fillStyle = `rgba(80,55,20,${0.04 + rnd() * 0.08})`; ctx.fillRect(rnd() * W, rnd() * H, 1 + rnd() * 2, 1 + rnd() * 2); }
  const v = ctx.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.78); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, info.favorableCount === 0 ? "rgba(40,20,10,.38)" : "rgba(70,45,15,.22)");
  ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
  // frame
  ctx.strokeStyle = tpl.border; ctx.lineWidth = 7; ctx.strokeRect(46, 46, W - 92, H - 92); ctx.lineWidth = 2; ctx.strokeRect(68, 68, W - 136, H - 136);
  drawCorner(ctx, 58, 58, 1, 1, tpl.border); drawCorner(ctx, W - 58, 58, -1, 1, tpl.border); drawCorner(ctx, 58, H - 58, 1, -1, tpl.border); drawCorner(ctx, W - 58, H - 58, -1, -1, tpl.border);
  ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
  // head
  ctx.fillStyle = tpl.accent; ctx.font = '26px "Geist Mono", monospace'; ctx.letterSpacing = "10px"; ctx.fillText("CRANOMANCIE", W / 2 + 5, 150); ctx.letterSpacing = "0px";
  drawEmblem(ctx, tpl.emblem, W / 2, 262, 74, tpl.accent, tpl.paper[1]);
  ctx.fillStyle = tpl.ink; ctx.font = '84px "Italiana", serif'; ctx.fillText(tpl.name, W / 2, 446);
  ctx.strokeStyle = tpl.border; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(W / 2 - 220, 478); ctx.quadraticCurveTo(W / 2, 462, W / 2 + 220, 478); ctx.stroke();
  ctx.fillStyle = tpl.ink; ctx.globalAlpha = 0.8; ctx.font = 'italic 34px "Crimson Pro", serif'; ctx.fillText("Lecture du crâne de", W / 2, 540); ctx.globalAlpha = 1;
  let size = 76; ctx.font = `${size}px "Italiana", serif`; while (ctx.measureText(info.name).width > W - 280 && size > 36) { size -= 2; ctx.font = `${size}px "Italiana", serif`; }
  ctx.fillStyle = tpl.accent; ctx.fillText(info.name, W / 2, 618);
  ctx.fillStyle = tpl.ink; ctx.globalAlpha = 0.6; ctx.font = '24px "Geist Mono", monospace'; ctx.fillText(info.date, W / 2, 664); ctx.globalAlpha = 1;
  // the three signs
  let y = 725;
  info.readings.forEach((r, i) => {
    const colour = r.favorable ? tpl.good : tpl.bad;
    ctx.textAlign = "left"; ctx.fillStyle = tpl.accent; ctx.font = '25px "Geist Mono", monospace'; ctx.letterSpacing = "3px";
    ctx.fillText(`${r.axisLabel.toUpperCase()} · ${r.axisName.toUpperCase()}`, 130, y + 20); ctx.letterSpacing = "0px";
    // polarity pill
    const label = r.favorable ? "FAVORABLE" : "DÉFAVORABLE"; ctx.font = 'bold 22px "Geist Mono", monospace'; const pw = ctx.measureText(label).width + 40;
    ctx.fillStyle = colour; ctx.beginPath(); ctx.roundRect(W - 130 - pw, y - 6, pw, 38, 19); ctx.fill();
    ctx.fillStyle = "#FBF5E4"; ctx.textAlign = "center"; ctx.fillText(label, W - 130 - pw / 2, y + 20);
    ctx.textAlign = "left"; ctx.fillStyle = tpl.ink; let s2 = 54; ctx.font = `${s2}px "Italiana", serif`;
    while (ctx.measureText(r.sign).width > W - 260 && s2 > 34) { s2 -= 2; ctx.font = `${s2}px "Italiana", serif`; }
    ctx.fillText(r.sign, 130, y + 84);
    ctx.fillStyle = tpl.ink; ctx.font = '39px "Crimson Pro", serif';
    wrapLines(ctx, r.meaning.replace(/\.$/, "") + ".", W - 260, 3).forEach((ln, k) => ctx.fillText(ln, 130, y + 142 + k * 46));
    if (i < 2) { ctx.strokeStyle = tpl.border; ctx.globalAlpha = 0.55; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(130, y + 252); ctx.lineTo(W - 130, y + 252); ctx.stroke(); ctx.globalAlpha = 1; }
    y += 280;
  });
  // verdict
  ctx.textAlign = "center"; ctx.fillStyle = tpl.accent; ctx.font = 'italic 38px "Crimson Pro", serif';
  wrapLines(ctx, info.tone, W - 300, 3).forEach((ln, k) => ctx.fillText(ln, W / 2, 1566 + k * 46));
  ctx.fillStyle = tpl.ink; ctx.globalAlpha = 0.55; ctx.font = '21px "Geist Mono", monospace'; ctx.fillText("Cranomancie · d’après Oswald Bald", W / 2, 1702); ctx.globalAlpha = 1;
  return canvas;
}

function dataUrlToBytes(url) { const b = atob(url.split(",")[1]), a = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; }

/* A one-page A5 PDF holding the card as a JPEG (DCTDecode): no PDF library needed. */
function cardPdfBytes(canvas) {
  const jpeg = dataUrlToBytes(canvas.toDataURL("image/jpeg", 0.93)), enc = new TextEncoder();
  const pageW = 419.53, pageH = 595.28, parts = [], offsets = [];
  let length = 0;
  const push = (data) => { const b = typeof data === "string" ? enc.encode(data) : data; parts.push(b); length += b.length; };
  const obj = (n, body) => { offsets[n] = length; push(`${n} 0 obj\n${body}\nendobj\n`); };
  push("%PDF-1.4\n%âãÏÓ\n");
  obj(1, "<< /Type /Catalog /Pages 2 0 R >>");
  obj(2, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>");
  obj(3, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageW} ${pageH}] /Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>`);
  const content = `q ${pageW} 0 0 ${pageH} 0 0 cm /Im0 Do Q`;
  obj(4, `<< /Length ${content.length} >>\nstream\n${content}\nendstream`);
  offsets[5] = length;
  push(`5 0 obj\n<< /Type /XObject /Subtype /Image /Width ${canvas.width} /Height ${canvas.height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpeg.length} >>\nstream\n`);
  push(jpeg); push("\nendstream\nendobj\n");
  const xref = length;
  let table = "xref\n0 6\n0000000000 65535 f \n";
  for (let n = 1; n <= 5; n++) table += String(offsets[n]).padStart(10, "0") + " 00000 n \n";
  push(table + `trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
  const out = new Uint8Array(length); let p = 0; for (const b of parts) { out.set(b, p); p += b.length; } return out;
}

function downloadBlob(blob, filename) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = filename; document.body.append(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
}

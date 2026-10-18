"use strict";
/* CRANOMANCIE 2000, web version: same behaviour as the desktop app (reading.py, reading_view.py, library.py).
   Content is invented (Oswald Bald's guide). Edits to signs are kept in this browser only (localStorage). */

const DATA = window.CRANO_DATA;
const AXES = DATA.axes;
const ORIGINAL = JSON.parse(JSON.stringify(AXES));
const FIELDS = ["sign", "sign_art", "fav", "unf"];
const STORE_KEY = "cranomancie_custom_signs_v1";
let OVERRIDES = {};

// ---------------------------------------------------------------- reading logic (port of reading.py)
const lowerFirst = (s) => s.slice(0, 1).toLowerCase() + s.slice(1);

function parseRoll(text) {
  const t = String(text).trim();
  if (!/^[+-]?\d+$/.test(t)) throw new Error("Jet : entrez un nombre entre 1 et 20.");
  const v = parseInt(t, 10);
  if (v < 1 || v > 20) throw new Error("Jet : le jet doit être entre 1 et 20.");
  return v;
}
const randInt = (lo, hi) => lo + Math.floor(Math.random() * (hi - lo + 1));
function rollPolarity() { const value = randInt(1, 20); return { value, favorable: value % 2 === 0 }; }
const getSign = (ai, roll) => AXES[ai].signs[roll - 1];

function readAxis(ai, roll, favorable, polarityValue = null) {
  const axis = AXES[ai], sign = getSign(ai, roll);
  const meaning = lowerFirst(favorable ? sign.fav : sign.unf);
  const polarity = favorable ? "favorable" : "défavorable";
  return {
    axis: axis.label, index: ai, roll, sign, favorable, polarity_value: polarityValue,
    meaning: favorable ? sign.fav : sign.unf,
    phrase: `${axis.spoken}, je vois ${sign.sign_art} : signe ${polarity}, ${meaning}.`,
    me_phrase: `${axis.me} ${sign.sign_art} : signe ${polarity}, ${meaning}.`,
  };
}
function detailLine(r) {
  const polarity = r.favorable ? "favorable" : "défavorable";
  return `${r.axis} : ${lowerFirst(r.sign.sign)}, ${polarity}, ${lowerFirst(r.meaning)}.`;
}
const tone = (rs) => DATA.synthesis[String(rs.filter((r) => r.favorable).length)];
const synthesize = (rs) => [tone(rs), ...rs.map(detailLine)].join(" ");
const synthesizeMe = (spoken) => DATA.me_synthesis_prefix + lowerFirst(spoken);
function conclusionItems(rs) {
  const t = tone(rs);
  const items = [{ display: t, favorable: null, spoken: t, me: DATA.me_synthesis_prefix + lowerFirst(t) }];
  for (const r of rs) {
    items.push({ display: `${r.axis} : ${lowerFirst(r.sign.sign)}, ${lowerFirst(r.meaning)}.`, favorable: r.favorable,
      spoken: detailLine(r), me: "précise : " + detailLine(r) });
  }
  return items;
}

// ---------------------------------------------------------------- user edits (port of the overrides)
function applyOverride(ai, n) {
  const sign = AXES[ai].signs[n - 1];
  for (const k of FIELDS) sign[k] = ORIGINAL[ai].signs[n - 1][k];
  Object.assign(sign, (OVERRIDES[AXES[ai].id] || {})[String(n)] || {});
}
function loadOverrides() {
  let stored = {};
  try { stored = JSON.parse(localStorage.getItem(STORE_KEY) || "{}"); } catch (e) { stored = {}; }
  OVERRIDES = {};
  AXES.forEach((axis, ai) => {
    const per = stored && typeof stored === "object" ? stored[axis.id] || {} : {};
    for (const [nText, fields] of Object.entries(per)) {
      const n = parseInt(nText, 10);
      if (!(n >= 1 && n <= 20) || typeof fields !== "object" || !fields) continue;
      const clean = {};
      for (const k of FIELDS) if (typeof fields[k] === "string" && fields[k].trim()) clean[k] = fields[k];
      if (Object.keys(clean).length) { (OVERRIDES[axis.id] ||= {})[String(n)] = clean; applyOverride(ai, n); }
    }
  });
}
function writeOverrides() {
  try { localStorage.setItem(STORE_KEY, JSON.stringify(OVERRIDES)); } catch (e) { toast("Enregistrement impossible dans ce navigateur"); }
}
const isCustomized = (ai, n) => !!Object.keys((OVERRIDES[AXES[ai].id] || {})[String(n)] || {}).length;

const ARTICLES = { ligne: "une", deux: "", cicatrice: "une", grain: "un", bosse: "une", creux: "un", taches: "des", veine: "une",
  peau: "une", petite: "une", petit: "un", grand: "un", pli: "un", coupure: "une", tache: "une", double: "une", marque: "une",
  trace: "une", "crâne": "un", front: "un", sommet: "un", nuque: "une", "arrière": "l'", tempes: "des", arcades: "des",
  contour: "un", profil: "un" };
function withArticle(sign) {
  const s = sign.trim(), lowered = lowerFirst(s), first = (s.split(/\s+/)[0] || "").toLowerCase();
  if (!(first in ARTICLES)) return lowered;
  const art = ARTICLES[first];
  return art === "l'" ? "l'" + lowered : art ? `${art} ${lowered}` : lowered;
}
function saveSign(ai, n, sign, art, fav, unf) {
  [sign, art, fav, unf] = [sign, art, fav, unf].map((v) => v.trim());
  if (!(sign && fav && unf)) throw new Error("Le nom et les deux définitions ne peuvent pas être vides.");
  art = art || withArticle(sign);
  const original = ORIGINAL[ai].signs[n - 1], changed = {};
  for (const [k, v] of [["sign", sign], ["sign_art", art], ["fav", fav], ["unf", unf]]) if (v !== original[k]) changed[k] = v;
  const id = AXES[ai].id;
  if (Object.keys(changed).length) (OVERRIDES[id] ||= {})[String(n)] = changed; else if (OVERRIDES[id]) delete OVERRIDES[id][String(n)];
  applyOverride(ai, n); writeOverrides();
}
function resetSign(ai, n) {
  const id = AXES[ai].id;
  if (OVERRIDES[id]) delete OVERRIDES[id][String(n)];
  applyOverride(ai, n); writeOverrides();
}

// ---------------------------------------------------------------- small helpers
const $ = (sel, root = document) => root.querySelector(sel);
function el(tag, attrs = {}, ...kids) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v; else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (v === true) node.setAttribute(k, ""); else if (v !== false && v != null) node.setAttribute(k, v);
  }
  for (const kid of kids) node.append(kid);
  return node;
}
let toastTimer;
function toast(text) {
  const t = $("#toast"); t.textContent = text; t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove("show"), 1400);
}
async function copyRaw(text) {
  try { await navigator.clipboard.writeText(text); }
  catch (e) {
    const ta = el("textarea", { style: "position:fixed;opacity:0" }); ta.value = text; document.body.append(ta); ta.select();
    try { document.execCommand("copy"); } finally { ta.remove(); }
  }
  toast("Copié");
}
const state = { me: true, manual: false, view: "reading", axes: AXES.map(() => ({ rollText: "", polText: "", roll: null, polarity: null, result: null, error: "" })), synthesis: "" };
function copyText(spoken, me) { copyRaw(state.me && me != null ? "/me " + me : spoken); }

// ---------------------------------------------------------------- reading view
const panels = [];
function numberField(caption, get, set, onChange) {
  const input = el("input", { class: "num", inputmode: "numeric", maxlength: 3, autocomplete: "off", "aria-label": caption });
  const step = (d) => {
    let v = parseInt(get().trim(), 10);
    if (Number.isNaN(v)) v = d > 0 ? 0 : 21;
    set(String(Math.max(1, Math.min(20, v + d)))); input.value = get(); onChange();
  };
  input.addEventListener("input", () => { set(input.value); onChange(); });
  input.addEventListener("keydown", (e) => {
    const d = { ArrowUp: 1, ArrowRight: 1, ArrowDown: -1, ArrowLeft: -1 }[e.key];
    if (d) { e.preventDefault(); step(d); }
  });
  input.addEventListener("wheel", (e) => { if (document.activeElement === input) { e.preventDefault(); step(e.deltaY < 0 ? 1 : -1); } }, { passive: false });
  const root = el("div", { class: "field" }, el("span", { class: "label" }, caption), el("div", { class: "row" }, input,
    el("div", { class: "arrows" }, el("button", { type: "button", "aria-label": "Plus", onclick: () => step(1) }, "▲"),
      el("button", { type: "button", "aria-label": "Moins", onclick: () => step(-1) }, "▼")),
    el("button", { type: "button", class: "dice", title: "Tirer au hasard", onclick: () => { set(String(randInt(1, 20))); input.value = get(); onChange(); } }, "🎲")));
  return { root, input, sync: () => { input.value = get(); } };
}

function buildPanel(ai) {
  const axis = AXES[ai], st = state.axes[ai], p = { ai };
  p.rollField = numberField("Jet (1-20)", () => st.rollText, (v) => { st.rollText = v; }, refresh);
  p.polField = numberField("Polarité (/roll 1-20 du 2e joueur)", () => st.polText, (v) => { st.polText = v; }, refresh);
  p.polBtn = el("button", { type: "button", class: "btn", onclick: () => { if (st.roll) { st.polarity = rollPolarity(); refresh(); } } }, "🎲 Lancer la polarité");
  p.sign = el("div", { class: "sign-label", role: "button", tabindex: 0, onclick: () => { if (st.roll) openSign(ai, st.roll); },
    onkeydown: (e) => { if (e.key === "Enter" && st.roll) openSign(ai, st.roll); } });
  p.observe = el("p", { class: "observe" });
  p.polLabel = el("div", { class: "pol-label" });
  p.phrase = el("p", { class: "phrase" });
  p.copy = el("button", { type: "button", class: "btn", disabled: true, onclick: () => { if (st.result) copyText(st.result.phrase, st.result.me_phrase); } }, "Copier la phrase");
  p.error = el("p", { class: "error" });
  p.polBox = el("div", {}, p.polBtn, p.polField.root);
  p.root = el("article", { class: "axis panel" },
    el("span", { class: "caption" }, axis.label.toUpperCase()), el("h2", {}, axis.nom), el("p", { class: "question" }, axis.question),
    p.rollField.root, p.sign, p.observe, p.polBox, p.polLabel, p.phrase,
    el("div", { class: "btn-row" }, p.copy, el("button", { type: "button", class: "btn", onclick: () => { randomizeFull(ai); refresh(); } }, "Aléatoire")), p.error);
  return p;
}

function randomizeFull(ai) {
  const st = state.axes[ai];
  st.roll = randInt(1, 20); st.rollText = String(st.roll); st.polarity = rollPolarity();
  if (state.manual) st.polText = String(st.polarity.value);
  panels[ai].rollField.sync(); panels[ai].polField.sync();
}

function evaluate(ai) {
  const st = state.axes[ai]; st.error = "";
  const text = st.rollText.trim();
  if (!text) return clearAxis(ai);
  let roll;
  try { roll = parseRoll(text); } catch (e) { return clearAxis(ai, e.message); }
  if (roll !== st.roll) { st.polarity = null; st.polText = ""; }  // a new roll invalidates the previous polarity
  st.roll = roll;
  if (state.manual) {
    st.polarity = null;
    const pt = st.polText.trim();
    if (pt) { try { const v = parseRoll(pt); st.polarity = { value: v, favorable: v % 2 === 0 }; } catch (e) { st.error = e.message.replace("Jet", "Polarité"); } }
  }
  if (!st.polarity) st.result = null;
  else st.result = readAxis(ai, roll, st.polarity.favorable, st.polarity.value);
}
function clearAxis(ai, message = "") {
  const st = state.axes[ai];
  Object.assign(st, { roll: null, polarity: null, polText: "", result: null, error: message });
}

function renderAxis(ai) {
  const st = state.axes[ai], p = panels[ai];
  p.polField.sync();
  p.polBtn.hidden = state.manual; p.polField.root.hidden = !state.manual;
  p.polBtn.disabled = !st.roll;
  p.sign.textContent = st.roll ? getSign(ai, st.roll).sign : "";
  p.observe.textContent = st.roll ? AXES[ai].observe : "";
  p.polBtn.textContent = st.polarity ? "🎲 Relancer la polarité" : "🎲 Lancer la polarité";
  p.error.textContent = st.error;
  if (st.result) {
    const fav = st.result.favorable;
    p.polLabel.textContent = `Polarité : ${st.polarity.value} (${fav ? "pair" : "impair"}) → ${fav ? "FAVORABLE" : "DÉFAVORABLE"}`;
    p.polLabel.className = "pol-label " + (fav ? "good" : "bad");
    p.phrase.textContent = state.me ? "l'individu " + st.result.me_phrase : st.result.phrase;
    p.copy.disabled = false;
  } else {
    p.polLabel.textContent = ""; p.polLabel.className = "pol-label"; p.phrase.textContent = ""; p.copy.disabled = true;
  }
}

function renderConclusion() {
  const done = state.axes.map((a) => a.result).filter(Boolean);
  const rows = $("#concl-rows"), big = $("#big-rows");
  rows.replaceChildren(); big.replaceChildren();
  const complete = done.length === 3;
  $("#concl-actions").hidden = !complete; $("#btn-big").hidden = !complete;
  if (!complete) {
    state.synthesis = "";
    rows.append(el("div", { class: "concl-row" }, el("div", { class: "txt" }, "Entrez les trois jets, puis lancez la polarité de chaque axe.")));
    closeBig(); return;
  }
  state.synthesis = synthesize(done);
  for (const item of conclusionItems(done)) {
    const cls = item.favorable === null ? "" : item.favorable ? "good" : "bad";
    const text = state.me ? "l'individu " + item.me : item.display;
    const make = () => el("div", { class: "concl-row" }, el("div", { class: "txt " + cls }, text),
      el("button", { type: "button", class: "btn", onclick: () => copyText(item.spoken, item.me) }, "Copier"));
    rows.append(make()); big.append(make());
  }
}

function refresh() {
  AXES.forEach((_, ai) => evaluate(ai));
  AXES.forEach((_, ai) => renderAxis(ai));
  renderConclusion();
}
function openBig() { if (!$("#btn-big").hidden) $("#big").hidden = false; }
function closeBig() { $("#big").hidden = true; }

// ---------------------------------------------------------------- library view
let selected = null, editing = false;
const sel = { search: "" };
const norm = (t) => t.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
function matches(axis, sign, query) {
  const hay = norm([axis.label, sign.sign, sign.fav, sign.unf].join(" "));
  return norm(query).split(/\s+/).filter(Boolean).every((w) => (/^\d+$/.test(w) ? parseInt(w, 10) === sign.n : hay.includes(w)));
}
function populate() {
  const grid = $("#signs-grid"); grid.replaceChildren(); let total = 0;
  AXES.forEach((axis, ai) => {
    const col = el("div", { class: "signs-col" }, el("h3", {}, `${axis.label.toUpperCase()} · ${axis.nom}`));
    for (const sign of axis.signs) {
      if (!matches(axis, sign, sel.search)) continue;
      total++;
      const row = el("button", { type: "button", class: "sign-row", "data-a": ai, "data-n": sign.n,
        onclick: () => showDetail(ai, sign.n) }, `${String(sign.n).padStart(2, " ")}  ${sign.sign}${isCustomized(ai, sign.n) ? "  ✎" : ""}`);
      if (selected && selected[0] === ai && selected[1] === sign.n) row.classList.add("sel");
      col.append(row);
    }
    grid.append(col);
  });
  $("#count").textContent = `${total} / 60`;
}
function openSign(ai, roll) {
  setView("signs");
  if (sel.search) { sel.search = ""; $("#search").value = ""; }
  showDetail(ai, roll);
}
function showDetail(ai, n) {
  if (editing) editing = false;
  selected = [ai, n];
  populate(); renderDrawer();
  const row = $(`.sign-row[data-a="${ai}"][data-n="${n}"]`);
  if (row) row.scrollIntoView({ block: "nearest" });
}
function closeDetail() { editing = false; selected = null; $("#drawer").hidden = true; populate(); }
function renderDrawer() {
  const d = $("#drawer"); d.replaceChildren();
  if (!selected) { d.hidden = true; return; }
  d.hidden = false;
  const [ai, n] = selected, axis = AXES[ai], sign = getSign(ai, n), custom = isCustomized(ai, n);
  d.append(el("div", { class: "dhead" },
    el("h2", {}, `${axis.label} n°${n} : ${sign.sign}${custom ? "  ✎ personnalisé" : ""}`),
    el("button", { type: "button", class: "btn small", onclick: closeDetail }, "Fermer ✕")));
  if (editing) return renderForm(d, ai, n, sign);
  const actions = el("div", { class: "actions" }, el("button", { type: "button", class: "btn small", onclick: () => { editing = true; renderDrawer(); } }, "✎ Modifier"));
  if (custom) actions.append(el("button", { type: "button", class: "btn small", onclick: () => {
    if (confirm("Remettre ce signe à sa version d'origine ?\nVos modifications seront perdues.")) { resetSign(ai, n); afterEdit(); } } }, "↺ Réinitialiser"));
  d.append(actions, el("h4", { class: "caption" }, `${axis.label.toUpperCase()} · ${axis.nom}`), el("p", { class: "m" }, axis.observe + "."));
  for (const fav of [true, false]) {
    const r = readAxis(ai, n, fav);
    d.append(el("h4", { class: fav ? "good" : "bad" }, fav ? "FAVORABLE (jet de polarité pair)" : "DÉFAVORABLE (jet de polarité impair)"),
      el("p", { class: "def" }, fav ? sign.fav : sign.unf),
      el("p", { class: "m" }, "Phrase : " + r.phrase), el("p", { class: "m" }, "/me : " + r.me_phrase));
  }
  d.append(el("p", { class: "m", style: "margin-top:12px" }, "Définitions inventées (Cranomancie d'Oswald Bald)." + (custom ? " Ce signe a été modifié par vous." : "")));
}
function renderForm(d, ai, n, sign) {
  const name = el("input", { value: sign.sign }), art = el("input", { value: sign.sign_art });
  const fav = el("textarea", { rows: 3 }, sign.fav), unf = el("textarea", { rows: 3 }, sign.unf);
  const save = () => {
    let newName = name.value.trim(), newArt = art.value.trim();
    if (newName !== sign.sign && newArt === sign.sign_art) newArt = withArticle(newName);
    try { saveSign(ai, n, newName, newArt, fav.value, unf.value); } catch (e) { alert(e.message); return; }
    editing = false; afterEdit();
  };
  d.append(el("label", { class: "cap" }, "NOM DU SIGNE", name),
    el("label", { class: "cap" }, "DANS LA PHRASE (« je vois … »)", el("small", {}, "Se remplit tout seul si vous changez le nom et laissez ce champ tel quel."), art),
    el("label", { class: "cap" }, "FAVORABLE (jet de polarité pair)", fav),
    el("label", { class: "cap" }, "DÉFAVORABLE (jet de polarité impair)", unf),
    el("div", { class: "actions", style: "margin-top:12px" }, el("button", { type: "button", class: "btn small", style: "background:var(--warm);color:var(--bg)", onclick: save }, "Enregistrer"),
      el("button", { type: "button", class: "btn small", onclick: () => { editing = false; renderDrawer(); } }, "Annuler")));
  name.focus();
}
function afterEdit() { populate(); renderDrawer(); refresh(); }

function arrowMove(dx, dy) {
  const rows = [...document.querySelectorAll(".sign-row")].map((r) => [+r.dataset.a, +r.dataset.n]);
  if (!rows.length) return;
  let target;
  if (!selected || !rows.some(([a, n]) => a === selected[0] && n === selected[1])) target = rows[0];
  else {
    const [col, n] = selected;
    if (dy) {
      const column = rows.filter(([a]) => a === col).map(([, m]) => m);
      target = [col, column[Math.max(0, Math.min(column.length - 1, column.indexOf(n) + dy))]];
    } else {
      const other = rows.filter(([a]) => a === col + dx).map(([, m]) => m);
      target = other.length ? [col + dx, other.reduce((best, m) => (Math.abs(m - n) < Math.abs(best - n) ? m : best))] : selected;
    }
  }
  showDetail(...target);
}

// ---------------------------------------------------------------- views, title, wiring
function setView(name) {
  state.view = name;
  $("#view-reading").hidden = name !== "reading"; $("#view-signs").hidden = name !== "signs";
  $("#tab-reading").classList.toggle("active", name === "reading"); $("#tab-signs").classList.toggle("active", name === "signs");
  if (name === "signs") populate();
}

/* Retro arcade title: bold monospace rendered small, thresholded, scaled up as pixels with an amber glow and scanlines. */
async function drawTitle() {
  const canvas = $("#title"), text = DATA.meta.title;
  try { await document.fonts.load('700 20px "Geist Mono"'); } catch (e) { /* fallback font */ }
  const rows = 22, small = document.createElement("canvas"), sc = small.getContext("2d", { willReadFrequently: true });
  sc.font = `800 ${rows * 0.72}px "Geist Mono", Consolas, monospace`;
  const w = Math.ceil(sc.measureText(text).width) + 6;
  small.width = w; small.height = rows;
  sc.font = `800 ${rows * 0.72}px "Geist Mono", Consolas, monospace`; sc.textBaseline = "middle"; sc.fillStyle = "#fff";
  sc.fillText(text, 3, rows / 2 + 1);
  const px = sc.getImageData(0, 0, w, rows).data;
  const f = Math.max(3, Math.min(5, Math.floor(Math.min(window.innerWidth - 24, 1000) / w)));
  canvas.width = w * f; canvas.height = rows * f;
  const c = canvas.getContext("2d");
  const lit = [];
  for (let y = 0; y < rows; y++) for (let x = 0; x < w; x++) if (px[(y * w + x) * 4 + 3] > 110) lit.push([x, y]);
  c.shadowColor = "rgba(180,90,0,.95)"; c.shadowBlur = f * 2.2; c.fillStyle = "#FFBE46";
  for (const [x, y] of lit) c.fillRect(x * f, y * f, f, f);
  c.shadowBlur = 0;
  for (const [x, y] of lit) c.fillRect(x * f, y * f, f, f);
  c.globalCompositeOperation = "source-atop"; c.fillStyle = "rgba(0,0,0,.35)";
  for (let y = 0; y < canvas.height; y += Math.max(3, Math.round(f * .75))) c.fillRect(0, y, canvas.width, Math.max(1, Math.round(f / 4)));
}

// ---------------------------------------------------------------- background music (off by default, very low volume)
function initMusic() {
  const audio = $("#bgm"), button = $("#btn-music"), vol = $("#vol");
  const VOL_KEY = "cranomancie_music_volume_v1", DEFAULT = 20;           // percent: deliberately very quiet
  let saved = parseInt(localStorage.getItem(VOL_KEY) || String(DEFAULT), 10);
  if (!(saved >= 0 && saved <= 100)) saved = DEFAULT;
  vol.value = saved;
  const apply = () => { audio.volume = Math.pow(vol.value / 100, 1.5) * 0.5; };   // curved: fine control at low levels, default is about -40 dBFS
  const refresh = () => {
    const on = !audio.paused;
    button.textContent = (on ? "🔊" : "🔇") + " Musique"; button.setAttribute("aria-pressed", String(on));
  };
  apply(); refresh();
  button.addEventListener("click", async () => {
    if (audio.paused) { try { await audio.play(); } catch (e) { toast("Lecture impossible dans ce navigateur"); } } else audio.pause();
    refresh();
  });
  vol.addEventListener("input", () => { apply(); try { localStorage.setItem(VOL_KEY, vol.value); } catch (e) { /* private mode */ } });
}

// ---------------------------------------------------------------- hide the whole interface: only the room (and this button) stay
// With the interface hidden the room can be explored: wheel = zoom around the cursor, drag = move, double-click = reset.
function initHud() {
  const button = $("#btn-hud"), room = $(".room");
  const view = { z: 1, x: 0, y: 0 }, MAX_ZOOM = 5;
  window.__roomView = view;   // read by the secret overlay
  // Pan limits: the picture itself must keep covering the screen. On a screen that is narrower (or taller) than the room picture, part of the
  // room is cropped at zoom 1 and the pan range is not empty, so the hidden part can be reached by dragging.
  const range = (axis) => {
    const b = roomBox(), start = axis === "x" ? b.left : b.top, length = axis === "x" ? b.w : b.h, port = axis === "x" ? innerWidth : innerHeight;
    let hi = -view.z * start, lo = port - view.z * (start + length);
    if (lo > hi) { hi = 0; lo = port * (1 - view.z); }            // the picture is smaller than the screen on this axis: keep the old limits
    return [lo, hi];
  };
  const clamp = () => {
    view.z = Math.max(1, Math.min(MAX_ZOOM, view.z));
    const [xlo, xhi] = range("x"), [ylo, yhi] = range("y");
    view.x = Math.min(xhi, Math.max(xlo, view.x));
    view.y = Math.min(yhi, Math.max(ylo, view.y));
  };
  const canPan = () => { const [xlo, xhi] = range("x"), [ylo, yhi] = range("y"); return xhi - xlo > 1 || yhi - ylo > 1; };
  // The room element is the picture itself (not the screen): it can be larger than the screen, so dragging shows the cropped parts.
  const layoutRoom = () => {
    const b = roomBox();
    Object.assign(room.style, { inset: "auto", left: b.left + "px", top: b.top + "px", width: b.w + "px", height: b.h + "px", backgroundSize: "100% 100%", backgroundPosition: "0 0",
      transformOrigin: `${-b.left}px ${-b.top}px` });                // the zoom origin stays the top-left corner of the screen
  };
  layoutRoom();
  const paint = (smooth) => {
    room.style.transition = smooth ? "transform .12s ease-out" : "none";
    room.style.transform = view.z === 1 && !view.x && !view.y ? "" : `translate(${view.x}px, ${view.y}px) scale(${view.z})`;
    const layer = document.querySelector(".hotlayer"); if (layer) { layer.style.transition = room.style.transition; layer.style.transform = room.style.transform; }
  };
  const reset = () => { Object.assign(view, { z: 1, x: 0, y: 0 }); paint(true); };
  const off = () => document.body.classList.contains("hud-off");
  const set = (hidden) => {
    document.body.classList.toggle("hud-off", hidden); button.setAttribute("aria-pressed", String(hidden));
    button.textContent = hidden ? "👁 Afficher l’interface" : "👁 Masquer l’interface";
    if (!hidden) reset();
  };
  button.addEventListener("click", () => set(!off()));
  document.addEventListener("keydown", (e) => {
    const t = e.target;
    if (e.ctrlKey || e.metaKey || e.altKey || t.tagName === "INPUT" || t.tagName === "TEXTAREA") return;
    if (e.key.toLowerCase() === "h") set(!off());
    else if (off() && (e.key === "0" || e.key === "Escape")) reset();
    else if (off() && e.key.startsWith("Arrow")) {                                   // arrow keys also move around the room
      const step = 90, d = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] }[e.key];
      view.x += d[0]; view.y += d[1]; clamp(); paint(true); e.preventDefault();
    }
  });
  document.addEventListener("wheel", (e) => {
    if (!off() || e.target.closest?.("#btn-hud")) return;
    e.preventDefault();
    const old = view.z, next = Math.max(1, Math.min(MAX_ZOOM, old * Math.exp(-e.deltaY * 0.0015)));
    view.x = e.clientX - (e.clientX - view.x) * next / old;       // keep the point under the cursor fixed
    view.y = e.clientY - (e.clientY - view.y) * next / old;
    view.z = next; clamp(); paint(true);
  }, { passive: false });
  let drag = null;
  document.addEventListener("pointerdown", (e) => {
    if (!off() || e.button !== 0 || e.target.closest?.("#btn-hud") || !canPan()) return;
    drag = { x: e.clientX - view.x, y: e.clientY - view.y }; document.body.classList.add("panning");
  });
  document.addEventListener("pointermove", (e) => {
    if (!drag) return;
    view.x = e.clientX - drag.x; view.y = e.clientY - drag.y; clamp(); paint(false);
  });
  const stop = () => { drag = null; document.body.classList.remove("panning"); };
  document.addEventListener("pointerup", stop); document.addEventListener("pointercancel", stop);
  document.addEventListener("dblclick", (e) => { if (off() && !e.target.closest?.("#btn-hud")) reset(); });
  window.addEventListener("resize", () => { layoutRoom(); if (off()) { clamp(); paint(false); } });
}

// ---------------------------------------------------------------- settings popover (format, polarity, music)
function initSettings() {
  const button = $("#btn-settings"), panel = $("#settings-panel");
  const set = (open) => { panel.hidden = !open; button.setAttribute("aria-expanded", String(open)); button.classList.toggle("tab", false); button.style.background = open ? "var(--warm)" : ""; button.style.color = open ? "var(--bg)" : ""; };
  button.addEventListener("click", (e) => { e.stopPropagation(); set(panel.hidden); });
  document.addEventListener("click", (e) => { if (!panel.hidden && !e.target.closest?.("#settings-panel")) set(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) { set(false); e.stopImmediatePropagation(); } }, true);
}

// ---------------------------------------------------------------- server calendar (wiki.elixirrp.fr/fr/calendrier)
// A server year lasts 28 real days (4 weeks, starting on a Sunday with "janvier"); the year 2057 began on Sunday 28 June 2026.
// Month lengths in real days: 2 3 2 | 2 3 2 | 2 3 2 | 2 3 2 (Jan..Dec). The wiki table (2057 -> 2062, 28 Jun -> 12 Dec 2026) lists month + year only.
const SERVER_MONTHS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
const SERVER_MONTH_DAYS = [2, 3, 2, 2, 3, 2, 2, 3, 2, 2, 3, 2];   // sums to 28
function serverDate(date = new Date()) {
  const day = Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()), start = Date.UTC(2026, 5, 28);
  const n = Math.floor((day - start) / 86400000), cycle = Math.floor(n / 28), p = ((n % 28) + 28) % 28;
  let month = 0, left = p;
  while (left >= SERVER_MONTH_DAYS[month]) { left -= SERVER_MONTH_DAYS[month]; month++; }
  return { year: 2057 + cycle, month, monthName: SERVER_MONTHS[month], label: SERVER_MONTHS[month][0].toUpperCase() + SERVER_MONTHS[month].slice(1) + " " + (2057 + cycle) };
}

// ---------------------------------------------------------------- reading card export (PNG / PDF)
function cardInfo(name) {
  const done = state.axes.map((a) => a.result);
  return {
    name: name || "…", favorableCount: done.filter((r) => r.favorable).length, tone: tone(done),
    date: serverDate().label,
    readings: done.map((r, i) => ({ axisLabel: AXES[i].label, axisName: AXES[i].nom, sign: r.sign.sign, favorable: r.favorable, meaning: r.meaning })),
  };
}
// ---------------------------------------------------------------- direct link: postimg.cc through a small relay (relay/worker.js), after an explicit confirmation
// The relay keeps the postimg API key secret. Set RELAY_URL once the worker is deployed (see relay/README_RELAY.md); while empty, the button stays hidden.
const RELAY_URL = "https://cranomancie-relay.ledoii.workers.dev";
async function uploadViaRelay(blob, filename) {
  const response = await fetch(`${RELAY_URL}?name=${encodeURIComponent(filename.replace(/\.png$/i, ""))}`, { method: "POST", headers: { "Content-Type": "image/png" }, body: blob });
  let data = {}; try { data = await response.json(); } catch (e) { /* not JSON */ }
  if (!response.ok || !/^https:\/\/i\.postimg\.cc\/\S+$/.test(data.url || "")) throw new Error(data.error || (response.ok ? "réponse inattendue du relais" : `le relais a répondu ${response.status}`));
  return data.url;
}
function initDirectLink(getName, slug) {
  const btn = $("#export-link"), box = $("#linkbox"), confirmBox = $("#linkbox-confirm"), status = $("#linkbox-status"), done = $("#linkbox-done");
  const show = (which) => { box.hidden = which === null; confirmBox.hidden = which !== "confirm"; status.hidden = which !== "status"; done.hidden = which !== "done"; };
  if (!RELAY_URL) btn.hidden = true;                                   // no relay configured: no button
  btn.addEventListener("click", () => { if (getName()) show("confirm"); });
  $("#link-cancel").addEventListener("click", () => show(null));
  $("#link-send").addEventListener("click", async () => {
    const who = getName(); if (!who) return;
    status.textContent = "Envoi en cours…"; status.className = ""; show("status");
    try {
      await cardFontsReady();
      const canvas = drawCard(document.createElement("canvas"), cardInfo(who));
      const blob = await new Promise((r) => canvas.toBlob(r, "image/png"));
      const url = await uploadViaRelay(blob, `cranomancie_${slug(who)}.png`);
      $("#link-url").value = url; show("done"); $("#link-url").select();
    } catch (e) {
      status.innerHTML = ""; const p = el("p", { class: "err" }, `Envoi impossible : ${e.message}. Exportez le PNG et utilisez img.elixirrp.fr.`);
      status.append(p, el("div", { class: "actions" }, el("button", { type: "button", class: "btn", onclick: () => show("confirm") }, "Réessayer"), el("button", { type: "button", class: "btn", onclick: () => show(null) }, "Fermer")));
      status.hidden = false;
    }
  });
  $("#link-copy").addEventListener("click", () => copyRaw($("#link-url").value));
  return { reset: () => show(null), enable: (on) => { btn.disabled = !on; if (!on) show(null); } };
}

function initExport() {
  const modal = $("#export-modal"), name = $("#export-name"), go = $("#export-go"), preview = $("#card-preview");
  const slug = (t) => t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "carte";
  const link = initDirectLink(() => name.value.trim(), slug);
  const copyBtn = $("#export-copy");
  const setNamed = (on) => { go.disabled = !on; copyBtn.disabled = !on; link.enable(on); };
  copyBtn.addEventListener("click", async () => {
    const who = name.value.trim(); if (!who) return;
    if (!navigator.clipboard || typeof ClipboardItem === "undefined") { toast("Copie d’image non prise en charge par ce navigateur : utilisez l’export PNG"); return; }
    try {
      await cardFontsReady();
      const canvas = drawCard(document.createElement("canvas"), cardInfo(who));
      const blob = new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("PNG vide"))), "image/png"));
      await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);   // the promise keeps the user gesture valid (Safari)
      toast("Image copiée dans le presse-papiers");
    } catch (e) { toast("Copie impossible : " + (e.message || "refusée par le navigateur") + ". Utilisez l’export PNG."); }
  });
  let timer;
  const redraw = () => { clearTimeout(timer); timer = setTimeout(async () => { await cardFontsReady(); drawCard(preview, cardInfo(name.value.trim())); }, 60); };
  const open = async () => {
    if (state.axes.some((a) => !a.result)) return;
    $("#export-tpl").textContent = CARD_TEMPLATES[cardInfo("").favorableCount].name;
    modal.hidden = false; setNamed(!!name.value.trim()); await cardFontsReady(); drawCard(preview, cardInfo(name.value.trim())); name.focus();
  };
  const close = () => { modal.hidden = true; link.reset(); };
  $("#btn-export").addEventListener("click", open);
  $("#export-close").addEventListener("click", close); $("#export-cancel").addEventListener("click", close);
  modal.addEventListener("click", (e) => { if (e.target === modal) close(); });
  name.addEventListener("input", () => { setNamed(!!name.value.trim()); redraw(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !modal.hidden) { close(); e.stopImmediatePropagation(); } }, true);
  $("#export-form").addEventListener("submit", async (e) => {
    e.preventDefault(); const who = name.value.trim(); if (!who) return;
    await cardFontsReady();
    const canvas = drawCard(document.createElement("canvas"), cardInfo(who)), format = document.querySelector('input[name="export-format"]:checked').value;
    const file = `cranomancie_${slug(who)}`;
    if (format === "png") canvas.toBlob((b) => { downloadBlob(b, file + ".png"); toast("Carte PNG exportée"); }, "image/png");
    else { downloadBlob(new Blob([cardPdfBytes(canvas)], { type: "application/pdf" }), file + ".pdf"); toast("Carte PDF exportée"); }
    close();
  });
  window.__card = { cardInfo, slug, cardPdfBytes, drawCard, serverDate, uploadViaRelay };   // handy for tests
}

// ---------------------------------------------------------------- secret: nine invisible spots of the room, any order; at the end a short scene plays in one painting
// Spot coordinates are in pixels of the 3584 x 1536 master picture of the room (the page shows it scaled, centred, bottom aligned).
const ROOM_W = 3584, ROOM_H = 1536;
const SECRET_SPOTS = [
  { id: "zaza", shape: "ellipse", x: 1190, y: 735, rx: 100, ry: 130 },
  { id: "diane", shape: "rect", x: 2048, y: 186, w: 193, h: 205 },
  { id: "lorcan", shape: "rect", x: 939, y: 190, w: 161, h: 190 },
  { id: "sitwell", shape: "rect", x: 2976, y: 176, w: 330, h: 672 },
  { id: "bust1", shape: "ellipse", x: 835, y: 650, rx: 90, ry: 150 },
  { id: "bust2", shape: "ellipse", x: 1064, y: 655, rx: 85, ry: 135 },
  { id: "bust3", shape: "ellipse", x: 2282, y: 655, rx: 85, ry: 125 },
  { id: "bust4", shape: "ellipse", x: 2495, y: 660, rx: 95, ry: 135 },
  { id: "bust5", shape: "ellipse", x: 2695, y: 660, rx: 95, ry: 140 },
];
const SECRET_STAGE = { x: 2334, y: 201, w: 157, h: 201 };   // the canvas of the portrait to the right of Diane's
const SECRET_SPRITE = { x: 2314, y: 195, size: 200 };       // where the 256 px animation sits relative to that canvas
const SECRET_PLAY_MS = 7000;
const LIVING_PORTRAIT = { x: 1181, y: 217, w: 112, h: 143 };       // canvas of the frame to the right of Lorcan's: "Absolute Viktor" appears there with the secret only (av.webp)

// the only hint of the secret: a soft note for every validated spot, rising along an A dorian scale (A3 ... E5), a small chord on the ninth
const SECRET_NOTES = [220, 261.63, 293.66, 329.63, 392, 440, 523.25, 587.33, 659.25];
let secretAudio = null;
function secretNote(step, last) {
  try {
    secretAudio = secretAudio || new (window.AudioContext || window.webkitAudioContext)();
    const ctx = secretAudio; if (ctx.state === "suspended") ctx.resume();
    const t0 = ctx.currentTime + 0.02, freqs = last ? [SECRET_NOTES[step], SECRET_NOTES[step] * 1.5, SECRET_NOTES[step] * 2] : [SECRET_NOTES[step]];
    const master = ctx.createGain(); master.gain.value = 0.07; master.connect(ctx.destination);   // very quiet, whatever the music setting
    const echo = ctx.createDelay(); echo.delayTime.value = 0.27; const fb = ctx.createGain(); fb.gain.value = 0.35; echo.connect(fb); fb.connect(echo); echo.connect(master);
    freqs.forEach((f, i) => {
      const osc = ctx.createOscillator(), g = ctx.createGain(); osc.type = "triangle"; osc.frequency.value = f;
      const start = t0 + i * (last ? 0.09 : 0), len = last ? 1.6 : 1.0;
      g.gain.setValueAtTime(0, start); g.gain.linearRampToValueAtTime(1, start + 0.015); g.gain.exponentialRampToValueAtTime(0.0008, start + len);
      osc.connect(g); g.connect(master); g.connect(echo); osc.start(start); osc.stop(start + len + 0.05);
    });
  } catch (e) { /* no audio available: the secret still works */ }
}

function roomBox() {
  const aspect = ROOM_W / ROOM_H, vw = innerWidth, vh = innerHeight;
  const tall = matchMedia("(max-aspect-ratio: 4/3)").matches;          // same rule as the stylesheet: cover on tall screens
  const h = tall ? Math.max(vh, vw / aspect) : vh, w = h * aspect;
  return { left: (vw - w) / 2, top: vh - h, w, h };
}

function initSecret() {
  const found = new Set(); let playing = false, down = null;
  const layer = el("div", { class: "hotlayer", "aria-hidden": "true" }), box = el("div", { class: "hotbox" });
  layer.append(box); document.body.append(layer);
  const place = () => { const b = roomBox(); Object.assign(box.style, { left: b.left + "px", top: b.top + "px", width: b.w + "px", height: b.h + "px" }); };
  place(); window.addEventListener("resize", place);
  const pct = (v, total) => (v / total * 100) + "%";
  const stage = el("div", { class: "stage" });
  Object.assign(stage.style, { left: pct(SECRET_STAGE.x, ROOM_W), top: pct(SECRET_STAGE.y, ROOM_H), width: pct(SECRET_STAGE.w, ROOM_W), height: pct(SECRET_STAGE.h, ROOM_H) });
  box.append(stage);
  const living = el("div", { class: "living" }, el("img", { src: "av.webp", alt: "", draggable: "false" }));
  Object.assign(living.style, { left: pct(LIVING_PORTRAIT.x, ROOM_W), top: pct(LIVING_PORTRAIT.y, ROOM_H), width: pct(LIVING_PORTRAIT.w, ROOM_W), height: pct(LIVING_PORTRAIT.h, ROOM_H) });
  box.append(living);
  if (new URLSearchParams(location.search).get("secret") === "show") {   // developer view: outlines of the spots
    for (const s of SECRET_SPOTS) {
      const d = el("div", { class: "spot-debug" }), w = s.shape === "ellipse" ? s.rx * 2 : s.w, h = s.shape === "ellipse" ? s.ry * 2 : s.h;
      const x = s.shape === "ellipse" ? s.x - s.rx : s.x, y = s.shape === "ellipse" ? s.y - s.ry : s.y;
      Object.assign(d.style, { left: pct(x, ROOM_W), top: pct(y, ROOM_H), width: pct(w, ROOM_W), height: pct(h, ROOM_H), borderRadius: s.shape === "ellipse" ? "50%" : "4px" });
      box.append(d);
    }
  }
  const hit = (clientX, clientY) => {
    const view = window.__roomView || { z: 1, x: 0, y: 0 }, b = roomBox();
    const px = ((clientX - view.x) / view.z - b.left) / b.w * ROOM_W, py = ((clientY - view.y) / view.z - b.top) / b.h * ROOM_H;
    return SECRET_SPOTS.find((s) => s.shape === "ellipse" ? ((px - s.x) / s.rx) ** 2 + ((py - s.y) / s.ry) ** 2 <= 1 : px >= s.x && px <= s.x + s.w && py >= s.y && py <= s.y + s.h);
  };
  const play = () => {
    playing = true; stage.replaceChildren(); living.classList.add("on");
    const back = el("div", { class: "stage-bg" }), sprite = el("img", { class: "stage-sprite", alt: "", src: "fx.webp?" + Date.now() });
    Object.assign(sprite.style, { left: pct(SECRET_SPRITE.x - SECRET_STAGE.x, SECRET_STAGE.w), top: pct(SECRET_SPRITE.y - SECRET_STAGE.y, SECRET_STAGE.h),
      width: pct(SECRET_SPRITE.size, SECRET_STAGE.w), height: pct(SECRET_SPRITE.size, SECRET_STAGE.h) });
    stage.append(back, sprite); requestAnimationFrame(() => stage.classList.add("on"));
    setTimeout(() => { stage.classList.remove("on"); living.classList.remove("on"); setTimeout(() => { stage.replaceChildren(); playing = false; found.clear(); }, 1200); }, SECRET_PLAY_MS);
  };
  document.addEventListener("pointerdown", (e) => { down = { x: e.clientX, y: e.clientY }; });
  document.addEventListener("click", (e) => {
    if (!document.body.classList.contains("hud-off") || playing || document.querySelector(".modal:not([hidden]), .big:not([hidden])")) return;   // only with the interface hidden
    if (e.target.closest?.("button, a, input, textarea, label, select, header, footer, .panel, .settings-panel, .toast, .modal, .big")) return;
    if (down && Math.hypot(e.clientX - down.x, e.clientY - down.y) > 6) return;        // a drag (pan), not a click
    const spot = hit(e.clientX, e.clientY);
    if (!spot) return;
    if (found.has(spot.id)) return;                                                     // already validated: no note
    found.add(spot.id);
    secretNote(found.size - 1, found.size === SECRET_SPOTS.length);
    if (found.size === SECRET_SPOTS.length) play();
  });
  window.__secret = { found, hit, roomBox, play, spots: SECRET_SPOTS };
}

function init() {
  loadOverrides();
  $("#version").textContent = "Version web v" + window.CRANO_VERSION;
  const holder = $("#axes");
  AXES.forEach((_, ai) => { panels.push(buildPanel(ai)); holder.append(panels[ai].root); });
  $("#opt-me").addEventListener("change", (e) => { state.me = e.target.checked; refresh(); });
  $("#opt-manual").addEventListener("change", (e) => {
    state.manual = e.target.checked; state.axes.forEach((a) => { a.polarity = null; a.polText = ""; }); refresh();
  });
  $("#btn-random-all").addEventListener("click", () => { AXES.forEach((_, ai) => randomizeFull(ai)); refresh(); setView("reading"); });
  $("#tab-reading").addEventListener("click", () => setView("reading"));
  $("#tab-signs").addEventListener("click", () => setView("signs"));
  $("#btn-copy-all").addEventListener("click", () => copyText(state.synthesis, synthesizeMe(state.synthesis)));
  $("#btn-reset").addEventListener("click", () => { state.axes.forEach((a) => Object.assign(a, { rollText: "", polText: "", roll: null, polarity: null, result: null, error: "" })); panels.forEach((p) => { p.rollField.sync(); }); refresh(); });
  $("#btn-big").addEventListener("click", openBig);
  $("#btn-big-close").addEventListener("click", closeBig);
  $("#search").addEventListener("input", (e) => { sel.search = e.target.value; populate(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { if (!$("#big").hidden) closeBig(); else if (state.view === "signs") { if (editing) { editing = false; renderDrawer(); } else closeDetail(); } return; }
    const step = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[e.key];
    if (!step || state.view !== "signs" || editing) return;
    const t = e.target;
    if ((t.tagName === "INPUT" && t.id !== "search") || t.tagName === "TEXTAREA") return;
    e.preventDefault(); arrowMove(...step);
  });
  initMusic();
  initSettings();
  initExport();
  initHud();
  initSecret();
  {   // animated room: on by default, the choice is remembered
    const KEY = "cranomancie_room_anim_v1", box = document.querySelector(".hotbox"), toggle = $("#opt-anim");
    const stored = localStorage.getItem(KEY);
    toggle.checked = stored === null ? true : stored === "1";      // on by default (Windows reports "reduced motion" when its own animations are off): the switch turns it off
    const ambiance = initAmbiance(box, () => toggle.checked);
    window.__ambiance = ambiance;
    toggle.addEventListener("change", () => { try { localStorage.setItem(KEY, toggle.checked ? "1" : "0"); } catch (e) { /* private mode */ } ambiance.apply(); });
  }
  refresh(); drawTitle();
  let resizeTimer; window.addEventListener("resize", () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(drawTitle, 200); });
}
init();

// Kod Bilimi Atölyesi: arayüz denetleyicisi.
// İş akışı mantığı (düğüm, bağlantı, tür denetimi, sıra, çalıştırma, açıklama) DOM'suz
// src/workflows/engine.js'tedir; burada yalnızca çizim ve etkileşim var. Algoritmalar
// kopyalanmaz: katalog, atomları ve molekülü doğrudan ../src/ altından içe aktarır.
import { createCatalog, TYPES, SAMPLES, parsePatternList } from '../src/workflows/catalog.js';
import {
  createWorkflow, addNode, removeNode, removeEdge, connect, canConnect, validateWorkflow,
  serializeWorkflow, deserializeWorkflow, explainWorkflow,
} from '../src/workflows/engine.js';
import { PACKAGES, packageById } from '../src/workflows/packages.js';
import { init as initRunner, runWorkflowRemote, raceRemote, runnerMode } from './runner.js';

const catalog = createCatalog();
const NODE_W = 190, HEAD = 38, PAD = 6, ROW = 22, FOOT = 24, GRID = 10;
const TYPE_ORDER = ['Source.File', 'FASTA.Entry', 'Pattern.Set', 'Sequence.Match', 'Finding'];

const state = {
  wf: createWorkflow({ name: 'Yeni iş akışı' }),
  sel: null,          // { kind: 'node', id } | { kind: 'edge', edge }
  run: null,          // son çalıştırmanın sonucu (runSerialized çıktısı)
  live: {},           // çalışırken düğüm durumları
  running: false,
  dirty: false,       // son çalıştırmadan sonra iş akışı değişti mi?
  zoom: 1,
  pkg: null,
  armed: null,        // klavye / tıklama ile bağlantı: { node, port, side }
  race: null,
  tab: 'bulgular',
  explain: null,
};

// ------------------------------------------------------------------ küçük yardımcılar
const $ = (id) => document.getElementById(id);
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs ?? {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k === 'text') el.textContent = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'style' && typeof v === 'object') Object.assign(el.style, v);
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) el.append(kid.nodeType ? kid : String(kid));
  return el;
}
const svgNS = 'http://www.w3.org/2000/svg';
function s(tag, attrs = {}) {
  const el = document.createElementNS(svgNS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
  return el;
}
const nf = (x, d = 1) => Number(x).toLocaleString('tr-TR', { maximumFractionDigits: d, minimumFractionDigits: 0 });
const fmtMs = (ms) => (ms == null ? '' : ms < 1 ? `${nf(ms, 3)} ms` : ms < 100 ? `${nf(ms, 1)} ms` : `${nf(Math.round(ms), 0)} ms`);
const catClass = (c) => 'cat-' + c.replace(/ /g, '-');
const tyClass = (t) => 'ty-' + t;
const compOf = (node) => catalog.get(node.type);
const nodeById = (id) => state.wf.nodes.find((n) => n.id === id);

let toastTimer = null;
function toast(msg, kind = 'info') {
  const t = $('toast');
  t.textContent = msg;
  t.className = 'toast' + (kind === 'err' ? ' err' : '');
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), kind === 'err' ? 6500 : 3200);
}

function nodeHeight(comp) {
  return HEAD + PAD * 2 + Math.max(1, comp.inputs.length, comp.outputs.length) * ROW + FOOT;
}
function portPos(node, side, name) {
  const comp = compOf(node);
  const list = side === 'out' ? comp.outputs : comp.inputs;
  const i = Math.max(0, list.findIndex((p) => p.name === name));
  return { x: node.x + (side === 'out' ? NODE_W : 0), y: node.y + HEAD + PAD + i * ROW + ROW / 2 };
}

/** İş akışı değişti: çalıştırma sonucu bayatladı. */
function changed({ structure = true } = {}) {
  if (state.run) state.dirty = true;
  state.explain = null;
  if (structure) renderCanvas();
  renderProps();
  setBadge();
  if (state.tab === 'aciklama') renderResults();
}

// ------------------------------------------------------------------ kenar çubuğu
function renderPackages() {
  const ul = $('paketler');
  ul.replaceChildren(...PACKAGES.map((p) => h('li', {},
    h('button', { type: 'button', 'aria-current': state.pkg === p.id ? 'true' : 'false', onclick: () => loadPackage(p.id), title: p.summary },
      h('span', { class: 'hash', 'aria-hidden': 'true', text: '#' }), p.channel))));
}

function renderPalette() {
  const q = $('ara').value.trim().toLocaleLowerCase('tr-TR');
  const box = $('palet');
  box.replaceChildren();
  let shown = 0;
  for (const cat of catalog.categories) {
    const items = [...catalog.values()].filter((c) => c.category === cat).filter((c) => {
      if (!q) return true;
      return [c.title, c.subtitle, c.badge, c.category, c.help, c.type, ...c.inputs.map((p) => p.type), ...c.outputs.map((p) => p.type)]
        .filter(Boolean).join(' ').toLocaleLowerCase('tr-TR').includes(q);
    });
    if (!items.length) continue;
    shown += items.length;
    const det = h('details', { class: 'cat', open: true },
      h('summary', {}, cat, h('span', { class: 'count', text: String(items.length) })),
      ...items.map((c) => h('button', {
        type: 'button', class: 'pal-item', draggable: 'true', 'data-type': c.type,
        title: `${c.help ?? ''}\nGiriş: ${c.inputs.map((p) => p.type).join(', ') || '—'} · Çıkış: ${c.outputs.map((p) => p.type).join(', ') || '—'}`,
        'aria-label': `${c.title} ekle (${c.category})`,
        onclick: () => addFromPalette(c.type),
        ondragstart: (e) => {
          e.dataTransfer.setData('application/x-kba-type', c.type);
          e.dataTransfer.setData('text/plain', c.type);
          e.dataTransfer.effectAllowed = 'copy';
        },
      }, h('span', { class: 'ico', 'aria-hidden': 'true', text: c.icon ?? '•' }), h('span', { class: 't', text: c.title }), h('span', { class: 'b', text: c.badge ?? c.subtitle ?? (c.outputs[0]?.type ?? '') }))));
    box.append(det);
  }
  $('ara-bos').hidden = shown > 0;
}

function openSide(open) {
  $('side').classList.toggle('open', open);
  $('scrim').hidden = !open;
  $('side-ac').setAttribute('aria-expanded', String(open));
  if (open) $('ara').focus();
}
const isMobile = () => matchMedia('(max-width: 760px)').matches;

function freeSpot() {
  const sc = $('tuval');
  const z = state.zoom;
  let x = Math.round((sc.scrollLeft / z + 40) / GRID) * GRID;
  let y = Math.round((sc.scrollTop / z + 40) / GRID) * GRID;
  for (let tries = 0; tries < 60; tries++) {
    const hit = state.wf.nodes.some((n) => Math.abs(n.x - x) < NODE_W + 10 && Math.abs(n.y - y) < 100);
    if (!hit) break;
    y += 110;
    if (tries % 4 === 3) { x += NODE_W + 40; y = Math.round((sc.scrollTop / z + 40) / GRID) * GRID; }
  }
  return { x, y };
}

function addFromPalette(type, at = null) {
  const pos = at ?? freeSpot();
  const node = addNode(state.wf, catalog, type, pos);
  state.sel = { kind: 'node', id: node.id };
  changed();
  if (isMobile()) openSide(false);
  focusNode(node.id);
  toast(`"${compOf(node).title}" eklendi. Uçlarına tıklayarak bağlayın.`);
}

function focusNode(id) {
  requestAnimationFrame(() => document.querySelector(`.node[data-id="${CSS.escape(id)}"]`)?.focus({ preventScroll: false }));
}

// ------------------------------------------------------------------ tuval
function boardSize() {
  let w = 0, hgt = 0;
  for (const n of state.wf.nodes) {
    w = Math.max(w, n.x + NODE_W);
    hgt = Math.max(hgt, n.y + nodeHeight(compOf(n)));
  }
  return { cw: w + 30, ch: hgt + 30, w: Math.max(w + 400, 1400), h: Math.max(hgt + 300, 900) };
}

function applyZoom() {
  const { w, h: hh } = boardSize();
  const board = $('board');
  board.style.width = `${w}px`;
  board.style.height = `${hh}px`;
  board.style.transform = `scale(${state.zoom})`;
  const sizer = board.parentElement;
  sizer.style.width = `${w * state.zoom}px`;
  sizer.style.height = `${hh * state.zoom}px`;
  $('kablolar').setAttribute('width', w);
  $('kablolar').setAttribute('height', hh);
  $('olcek').textContent = `${Math.round(state.zoom * 100)}%`;
}

function setZoom(z) {
  state.zoom = Math.min(1.6, Math.max(0.4, Math.round(z * 100) / 100));
  applyZoom();
}

function fit() {
  const sc = $('tuval');
  const { cw, ch } = boardSize();
  if (!state.wf.nodes.length) return setZoom(1);
  const z = Math.min(1, (sc.clientWidth - 16) / cw, Math.max(0.55, (sc.clientHeight - 16) / ch));
  setZoom(Math.max(isMobile() ? 0.7 : 0.45, z)); // telefonda okunur kalsın; tuval kaydırılır
  sc.scrollTo({ left: 0, top: 0 });
}

function nodeFooter(node) {
  const r = state.live[node.id] ?? (state.run && !state.dirty ? state.run.nodes[node.id] : null);
  if (r) {
    if (r.status === 'çalışıyor') return 'çalışıyor…';
    if (r.status === 'bitti') return `${fmtMs(r.ms)} · ${r.summary ?? r.info?.summary ?? ''}`;
    return `${r.status}: ${r.error ?? ''}`;
  }
  const c = compOf(node);
  const p = node.params ?? {};
  switch (node.type) {
    case 'kaynak.ornek': return SAMPLES[p.sample]?.title ?? p.sample;
    case 'kaynak.kod': case 'kaynak.log': case 'kaynak.fasta': return `${p.path} · ${String(p.text ?? '').length} karakter`;
    case 'kaynak.dosyalar': return `${(p.files ?? []).length} dosya`;
    case 'desen.ozel': return `${parsePatternList(p.patterns).length} desen${p.ignoreCase ? ' · ignoreCase' : ''}`;
    case 'molekul.ExactMatch': return `strateji: ${p.strategy}`;
    case 'cikti.jsonl': return p.filename;
    default: return c.badge ?? c.subtitle ?? '';
  }
}

function renderCanvas() {
  const layer = $('dugumler');
  layer.replaceChildren();
  for (const node of state.wf.nodes) layer.append(nodeEl(node));
  applyZoom();
  renderWires();
}

function nodeEl(node) {
  const comp = compOf(node);
  const selected = state.sel?.kind === 'node' && state.sel.id === node.id;
  const r = state.live[node.id] ?? (state.run && !state.dirty ? state.run.nodes[node.id] : null);
  const el = h('div', {
    class: `node ${catClass(comp.category)}${selected ? ' sel' : ''}`, tabindex: '0', role: 'group',
    'data-id': node.id, 'data-status': r?.status ?? null, 'data-gate': r?.info?.gate ?? null,
    'aria-label': `${comp.title} kutusu (${comp.category}). Ok tuşları taşır, Delete siler.`,
    style: { left: `${node.x}px`, top: `${node.y}px`, height: `${nodeHeight(comp)}px` },
  });
  const head = h('div', { class: 'node-head' },
    h('span', { class: 'node-ico', 'aria-hidden': 'true', text: comp.icon ?? '•' }),
    h('div', { style: { minWidth: '0' } }, h('div', { class: 'node-cat', text: comp.category }), h('div', { class: 'node-title', text: comp.title })));
  el.append(head);
  const rows = h('div', { class: 'node-rows', style: { height: `${PAD * 2 + Math.max(1, comp.inputs.length, comp.outputs.length) * ROW}px` } });
  const n = Math.max(comp.inputs.length, comp.outputs.length);
  for (let i = 0; i < n; i++) {
    rows.append(h('div', { class: 'node-row', style: { top: `${PAD + i * ROW}px` } },
      comp.inputs[i] ? h('span', { text: comp.inputs[i].label ?? comp.inputs[i].name }) : h('span'),
      comp.outputs[i] ? h('span', { class: 'out', text: comp.outputs[i].label ?? comp.outputs[i].name }) : null));
  }
  el.append(rows);
  for (const [side, list] of [['in', comp.inputs], ['out', comp.outputs]]) {
    list.forEach((p, i) => {
      const armed = state.armed && state.armed.node === node.id && state.armed.port === p.name && state.armed.side === side;
      let okTarget = false;
      if (state.armed && state.armed.side !== side && state.armed.node !== node.id) {
        const a = { node: state.armed.node, port: state.armed.port };
        const b = { node: node.id, port: p.name };
        okTarget = (side === 'in' ? canConnect(state.wf, catalog, a, b) : canConnect(state.wf, catalog, b, a)).ok;
      }
      const btn = h('button', {
        type: 'button', class: `port ${side} ${tyClass(p.type)}${armed ? ' armed' : ''}${okTarget ? ' ok-target' : ''}`,
        style: { top: `${HEAD + PAD + i * ROW + ROW / 2 - 7}px` },
        'data-node': node.id, 'data-port': p.name, 'data-side': side, 'data-type': p.type,
        title: `${side === 'in' ? 'Giriş' : 'Çıkış'}: ${p.label ?? p.name} (${p.type}${p.multi ? ', birden çok bağlantı alır' : ''})`,
        'aria-label': `${comp.title}: ${side === 'in' ? 'giriş' : 'çıkış'} ${p.label ?? p.name}, tür ${p.type}`,
      });
      wirePort(btn);
      el.append(btn);
    });
  }
  el.append(h('div', { class: 'node-foot' }, h('i', { class: 'st', 'aria-hidden': 'true' }), h('span', { text: nodeFooter(node) })));
  wireNode(el, head, node);
  return el;
}

function edgePath(a, b) {
  const dx = Math.max(40, Math.abs(b.x - a.x) / 2);
  return `M ${a.x} ${a.y} C ${a.x + dx} ${a.y}, ${b.x - dx} ${b.y}, ${b.x} ${b.y}`;
}

function renderWires() {
  const svg = $('kablolar');
  svg.replaceChildren();
  for (const e of state.wf.edges) {
    const a = nodeById(e.from.node), b = nodeById(e.to.node);
    if (!a || !b) continue;
    const type = compOf(a).outputs.find((p) => p.name === e.from.port)?.type ?? '';
    const d = edgePath(portPos(a, 'out', e.from.port), portPos(b, 'in', e.to.port));
    const sel = state.sel?.kind === 'edge' && sameEdge(state.sel.edge, e);
    svg.append(s('path', { d, class: `w ${tyClass(type)}${sel ? ' sel' : ''}` }));
    const hit = s('path', { d, class: 'hit' });
    const title = s('title');
    title.textContent = `${compOf(a).title} → ${compOf(b).title} (${type}). Tıklayıp Delete ile silin.`;
    hit.append(title);
    hit.addEventListener('pointerdown', (ev) => {
      ev.stopPropagation();
      state.sel = { kind: 'edge', edge: e };
      renderWires();
      renderProps();
      renderCanvasSelection();
    });
    svg.append(hit);
  }
  if (drag.temp) svg.append(drag.temp);
}
const sameEdge = (a, b) => a.from.node === b.from.node && a.from.port === b.from.port && a.to.node === b.to.node && a.to.port === b.to.port;

function renderCanvasSelection() {
  for (const el of document.querySelectorAll('.node')) {
    el.classList.toggle('sel', state.sel?.kind === 'node' && state.sel.id === el.dataset.id);
  }
}

function select(sel) {
  state.sel = sel;
  renderCanvasSelection();
  renderWires();
  renderProps();
}

// --- kutu taşıma (fare / dokunma / klavye)
function wireNode(el, head, node) {
  el.addEventListener('focus', () => {
    if (!(state.sel?.kind === 'node' && state.sel.id === node.id)) select({ kind: 'node', id: node.id });
  });
  el.addEventListener('keydown', (e) => {
    if (e.target !== el) return;
    const step = e.shiftKey ? 50 : GRID;
    const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    if (moves[e.key]) {
      e.preventDefault();
      node.x = Math.max(0, node.x + moves[e.key][0]);
      node.y = Math.max(0, node.y + moves[e.key][1]);
      el.style.left = `${node.x}px`;
      el.style.top = `${node.y}px`;
      renderWires();
      applyZoom();
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      e.preventDefault();
      deleteSelection();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      $('props').focus();
    }
  });
  head.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    el.focus({ preventScroll: true });
    select({ kind: 'node', id: node.id });
    const start = { x: e.clientX, y: e.clientY, nx: node.x, ny: node.y };
    head.setPointerCapture(e.pointerId);
    const move = (ev) => {
      node.x = Math.max(0, Math.round((start.nx + (ev.clientX - start.x) / state.zoom) / GRID) * GRID);
      node.y = Math.max(0, Math.round((start.ny + (ev.clientY - start.y) / state.zoom) / GRID) * GRID);
      el.style.left = `${node.x}px`;
      el.style.top = `${node.y}px`;
      renderWires();
    };
    const up = () => {
      head.removeEventListener('pointermove', move);
      head.removeEventListener('pointerup', up);
      head.removeEventListener('pointercancel', up);
      applyZoom();
    };
    head.addEventListener('pointermove', move);
    head.addEventListener('pointerup', up);
    head.addEventListener('pointercancel', up);
  });
}

// --- bağlantı kurma: uçtan sürükle-bırak, ya da iki uca sırayla tıkla / Enter
const drag = { temp: null };
function boardPoint(ev) {
  const r = $('board').getBoundingClientRect();
  return { x: (ev.clientX - r.left) / state.zoom, y: (ev.clientY - r.top) / state.zoom };
}

function wirePort(btn) {
  const me = () => ({ node: btn.dataset.node, port: btn.dataset.port, side: btn.dataset.side });
  btn.addEventListener('click', (e) => {
    if (e.detail === 0) activatePort(me(), btn); // klavye (Enter / Boşluk)
  });
  btn.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();
    const from = me();
    const node = nodeById(from.node);
    const p0 = portPos(node, from.side, from.port);
    const start = { x: e.clientX, y: e.clientY };
    let moved = false;
    btn.setPointerCapture(e.pointerId);
    const move = (ev) => {
      if (!moved && Math.hypot(ev.clientX - start.x, ev.clientY - start.y) < 5) return;
      moved = true;
      const p = boardPoint(ev);
      const d = from.side === 'out' ? edgePath(p0, p) : edgePath(p, p0);
      if (!drag.temp) drag.temp = s('path', { class: 'temp' });
      drag.temp.setAttribute('d', d);
      if (!drag.temp.isConnected) $('kablolar').append(drag.temp);
    };
    const up = (ev) => {
      btn.removeEventListener('pointermove', move);
      btn.removeEventListener('pointerup', up);
      btn.removeEventListener('pointercancel', up);
      drag.temp?.remove();
      drag.temp = null;
      if (!moved) return activatePort(from, btn);
      const target = document.elementFromPoint(ev.clientX, ev.clientY)?.closest('.port');
      if (!target || target === btn) return;
      tryConnect(from, { node: target.dataset.node, port: target.dataset.port, side: target.dataset.side }, btn, target);
    };
    btn.addEventListener('pointermove', move);
    btn.addEventListener('pointerup', up);
    btn.addEventListener('pointercancel', up);
  });
}

function activatePort(p, btn) {
  if (state.armed && state.armed.side !== p.side && state.armed.node !== p.node) {
    const other = document.querySelector(`.port[data-node="${CSS.escape(state.armed.node)}"][data-port="${CSS.escape(state.armed.port)}"][data-side="${state.armed.side}"]`);
    const a = state.armed;
    state.armed = null;
    tryConnect(a, p, other, btn);
    return;
  }
  if (state.armed && state.armed.node === p.node && state.armed.port === p.port && state.armed.side === p.side) {
    disarm();
    return;
  }
  state.armed = p;
  const comp = compOf(nodeById(p.node));
  const port = (p.side === 'out' ? comp.outputs : comp.inputs).find((x) => x.name === p.port);
  const hint = $('baglanti-ipucu');
  hint.textContent = `${comp.title} → ${port.label ?? port.name} (${port.type}) seçildi: şimdi bir ${p.side === 'out' ? 'giriş' : 'çıkış'} ucuna tıklayın ya da Tab ile gidip Enter'a basın. Esc: vazgeç.`;
  hint.hidden = false;
  renderCanvas();
  document.querySelector(`.port[data-node="${CSS.escape(p.node)}"][data-port="${CSS.escape(p.port)}"][data-side="${p.side}"]`)?.focus();
}

function disarm() {
  state.armed = null;
  $('baglanti-ipucu').hidden = true;
  renderCanvas();
}

function tryConnect(a, b, elA, elB) {
  state.armed = null;
  $('baglanti-ipucu').hidden = true;
  if (a.side === b.side) {
    toast('İki ucun biri çıkış, diğeri giriş olmalı.', 'err');
    renderCanvas();
    return false;
  }
  const from = a.side === 'out' ? a : b;
  const to = a.side === 'out' ? b : a;
  const r = canConnect(state.wf, catalog, { node: from.node, port: from.port }, { node: to.node, port: to.port });
  if (!r.ok) {
    renderCanvas();
    for (const el of [elA, elB]) {
      const fresh = el && document.querySelector(`.port[data-node="${CSS.escape(el.dataset.node)}"][data-port="${CSS.escape(el.dataset.port)}"][data-side="${el.dataset.side}"]`);
      fresh?.classList.add('reject');
    }
    toast(`Bağlantı reddedildi. ${r.reason}`, 'err');
    return false;
  }
  connect(state.wf, catalog, { node: from.node, port: from.port }, { node: to.node, port: to.port });
  changed();
  toast(`Bağlandı: ${compOf(nodeById(from.node)).title} → ${compOf(nodeById(to.node)).title}`);
  return true;
}

function deleteSelection() {
  if (!state.sel) return;
  if (state.sel.kind === 'node') {
    const title = compOf(nodeById(state.sel.id))?.title;
    removeNode(state.wf, state.sel.id);
    toast(`"${title}" silindi.`);
  } else {
    removeEdge(state.wf, state.sel.edge);
    toast('Bağlantı silindi.');
  }
  state.sel = null;
  changed();
  $('tuval').focus();
}

// ------------------------------------------------------------------ özellikler paneli
function chip(type) {
  return h('span', { class: 'chip', title: TYPES[type] ?? '' }, h('i', { class: tyClass(type) }), type);
}

function paramField(node, p) {
  const id = `p-${node.id}-${p.key}`;
  const val = node.params[p.key];
  const set = (v, rerender = false) => {
    node.params[p.key] = v;
    changed({ structure: false });
    const foot = document.querySelector(`.node[data-id="${CSS.escape(node.id)}"] .node-foot span`);
    if (foot) foot.textContent = nodeFooter(node);
    if (rerender) renderProps();
  };
  if (p.kind === 'bool') {
    return h('div', { class: 'field' }, h('label', { class: 'check' },
      h('input', { type: 'checkbox', id, checked: Boolean(val), onchange: (e) => set(e.target.checked) }), p.label));
  }
  if (p.kind === 'select') {
    const sel = h('select', { id, onchange: (e) => set(e.target.value, true) }, ...p.options.map((o) => h('option', { value: o.value, selected: o.value === val, text: o.label })));
    return h('div', { class: 'field' }, h('label', { class: 'l', for: id, text: p.label }), sel);
  }
  if (p.kind === 'textarea') {
    const ta = h('textarea', { id, rows: '6', spellcheck: 'false', oninput: (e) => set(e.target.value) });
    ta.value = val ?? '';
    const extra = p.upload ? h('input', {
      type: 'file', 'aria-label': `${p.label}: dosyadan yükle`,
      onchange: async (e) => {
        const f = e.target.files[0];
        if (!f) return;
        ta.value = await f.text();
        node.params.path = f.name;
        set(ta.value, true);
      },
    }) : null;
    return h('div', { class: 'field' }, h('label', { class: 'l', for: id, text: p.label }), ta, extra);
  }
  if (p.kind === 'files') {
    const list = val ?? [];
    return h('div', { class: 'field' },
      h('label', { class: 'l', for: id, text: p.label }),
      h('input', {
        id, type: 'file', multiple: true,
        onchange: async (e) => {
          const files = [...e.target.files];
          const read = await Promise.all(files.map(async (f) => ({ path: f.webkitRelativePath || f.name, text: await f.text() })));
          set([...(node.params.files ?? []), ...read], true);
          toast(`${read.length} dosya yüklendi (tarayıcıdan çıkmaz).`);
        },
      }),
      list.length ? h('ul', { class: 'conn-list', style: { marginTop: '6px' } }, ...list.map((f, i) => h('li', {},
        h('span', { class: 'mono', text: `${f.path} · ${nf(f.text.length, 0)} karakter` }),
        h('button', { type: 'button', onclick: () => set(list.filter((_, j) => j !== i), true), 'aria-label': `${f.path} dosyasını çıkar`, text: 'çıkar' })))) : h('p', { class: 'sub', text: 'Henüz dosya yok.' }));
  }
  const inp = h('input', { id, type: 'text', oninput: (e) => set(e.target.value), autocomplete: 'off' });
  inp.value = val ?? '';
  return h('div', { class: 'field' }, h('label', { class: 'l', for: id, text: p.label }), inp);
}

function connectionsOf(node) {
  const comp = compOf(node);
  const items = state.wf.edges.filter((e) => e.from.node === node.id || e.to.node === node.id).map((e) => {
    const other = e.from.node === node.id ? nodeById(e.to.node) : nodeById(e.from.node);
    const dir = e.from.node === node.id ? `→ ${compOf(other).title} (${e.to.port})` : `← ${compOf(other).title} (${e.from.port})`;
    return h('li', {}, h('span', { text: dir }), h('button', { type: 'button', text: 'sil', 'aria-label': `Bağlantıyı sil: ${dir}`, onclick: () => { removeEdge(state.wf, e); changed(); } }));
  });
  // Klavyeyle bağlantı: bu kutunun bir çıkışından uyumlu bir girişe
  const options = [];
  for (const out of comp.outputs) {
    for (const other of state.wf.nodes) {
      if (other.id === node.id) continue;
      for (const inp of compOf(other).inputs) {
        if (canConnect(state.wf, catalog, { node: node.id, port: out.name }, { node: other.id, port: inp.name }).ok) {
          options.push({ value: JSON.stringify([out.name, other.id, inp.name]), label: `${out.label ?? out.name} → ${compOf(other).title} · ${inp.label ?? inp.name}` });
        }
      }
    }
  }
  const sel = h('select', { id: 'bagla-sec', 'aria-label': 'Bağlanacak giriş' }, ...options.map((o) => h('option', { value: o.value, text: o.label })));
  return h('div', {},
    items.length ? h('ul', { class: 'conn-list' }, ...items) : h('p', { class: 'sub', text: 'Bağlantı yok.' }),
    comp.outputs.length ? h('div', { class: 'field', style: { marginTop: '8px' } },
      h('label', { class: 'l', for: 'bagla-sec', text: 'Klavyeyle bağla (uyumlu girişler)' }),
      options.length ? h('div', { class: 'row' }, sel, h('button', {
        type: 'button', text: 'Bağla',
        onclick: () => {
          const [port, target, tport] = JSON.parse(sel.value);
          tryConnect({ node: node.id, port, side: 'out' }, { node: target, port: tport, side: 'in' });
        },
      })) : h('p', { class: 'sub', text: 'Tuvalde bu kutunun çıkışını alabilecek boş bir giriş yok.' })) : null);
}

function recordView(node, rec, info) {
  const est = Object.entries(rec.estimates ?? {});
  const ok = est.filter(([, e]) => e.applicable).sort((a, b) => a[1].ms - b[1].ms);
  const na = est.filter(([, e]) => !e.applicable);
  const max = Math.max(...ok.map(([, e]) => e.ms), 1e-9);
  const sh = rec.shape ?? {};
  return h('div', {},
    h('h3', { text: 'Karar kaydı (record)' }),
    h('p', {}, 'Seçilen atom: ', h('b', { text: rec.selected }), rec.requested !== 'auto' ? ` (istenen: ${rec.requested})` : ''),
    h('dl', { class: 'kv' },
      ...[['n (ilk kayıt)', sh.n], ['σ', sh.sigma], ['σe (etkin)', sh.sigmaEff], ['k', sh.k], ['mMin / mMax', `${sh.mMin} / ${sh.mMax}`], ['mMean', sh.mMean], ['örneklendi', sh.sampled ? 'evet (64 × 256 karakter)' : 'hayır (tam sayım)']]
        .flatMap(([k, v]) => [h('dt', { text: k }), h('dd', { text: String(v) })])),
    h('h3', { text: 'Atomların tahmini süresi' }),
    h('div', { class: 'bars', role: 'list' }, ...ok.map(([name, e]) => h('div', { class: `bar${name === rec.selected ? ' selected' : ''}`, role: 'listitem', title: `${name}: ${e.ms} ms (tahmin)` },
      h('span', { class: 'n', text: name.replace('Search', '') }),
      h('span', { class: 'track' }, h('span', { class: 'fill', style: { width: `${(e.ms / max) * 100}%` } })),
      h('span', { class: 'v', text: `${nf(e.ms, 3)} ms` }))),
    ...na.map(([name, e]) => h('div', { class: 'bar na', role: 'listitem' }, h('span', { class: 'n', text: name.replace('Search', '') }), h('span', { class: 'sub', text: `uygun değil: ${e.reason}` }), h('span')))),
    h('h3', { text: 'Neden' }),
    h('p', { class: 'why', text: rec.why }),
    info?.searchMs != null ? h('p', { class: 'sub', text: `Karar + arama bu tarayıcıda ${fmtMs(info.searchMs)} sürdü; ${nf(info.count, 0)} eşleşme.` }) : null);
}

function renderProps() {
  const box = $('props');
  box.replaceChildren();
  const sel = state.sel;
  if (sel?.kind === 'edge') {
    const a = nodeById(sel.edge.from.node), b = nodeById(sel.edge.to.node);
    const type = compOf(a).outputs.find((p) => p.name === sel.edge.from.port)?.type;
    box.append(h('h2', { text: 'Bağlantı' }),
      h('p', {}, `${compOf(a).title} · ${sel.edge.from.port} → ${compOf(b).title} · ${sel.edge.to.port}`),
      h('p', {}, chip(type)),
      h('button', { type: 'button', class: 'danger', text: 'Bağlantıyı sil', onclick: deleteSelection }));
    return;
  }
  if (sel?.kind === 'node' && nodeById(sel.id)) {
    const node = nodeById(sel.id);
    const comp = compOf(node);
    const r = state.run && !state.dirty ? state.run.nodes[node.id] : null;
    box.append(
      h('h2', {}, h('span', { class: catClass(comp.category), 'aria-hidden': 'true' }, h('span', { class: 'node-ico', text: comp.icon ?? '•' })), comp.title),
      h('p', { class: 'sub', text: `${comp.category} · kimlik: ${node.id}${comp.subtitle ? ' · ' + comp.subtitle : ''}` }),
      comp.help ? h('p', { class: 'note', text: comp.help }) : null);
    if (comp.manifest) {
      const m = comp.manifest;
      box.append(h('h3', { text: 'Manifest' }), h('dl', { class: 'kv' },
        ...[['name', m.name], ['kind', m.kind], ['task', m.task], ['version', m.version], ['kaynak', (m.references ?? []).join('; ') || '—']].flatMap(([k, v]) => [h('dt', { text: k }), h('dd', { text: v })])));
    }
    if (comp.params?.length) {
      box.append(h('h3', { text: 'Ayarlar' }), ...comp.params.map((p) => paramField(node, p)));
    }
    box.append(h('h3', { text: 'Uçlar' }), h('ul', { class: 'ports-list' },
      ...comp.inputs.map((p) => h('li', {}, h('span', { text: `giriş: ${p.label ?? p.name}${p.multi ? ' (çoklu)' : ''}` }), chip(p.type))),
      ...comp.outputs.map((p) => h('li', {}, h('span', { text: `çıkış: ${p.label ?? p.name}` }), chip(p.type)))));
    box.append(h('h3', { text: 'Bağlantılar' }), connectionsOf(node));
    if (r) {
      box.append(h('h3', { text: 'Son çalıştırma' }), h('p', { class: r.status === 'bitti' ? 'sub' : 'problems' },
        `${r.status} · ${fmtMs(r.ms)}${r.info?.summary ? ' · ' + r.info.summary : ''}${r.error ? ' · ' + r.error : ''}`));
      if (r.info?.record) box.append(recordView(node, r.info.record, r.info));
    } else if (node.type === 'molekul.ExactMatch') {
      box.append(h('h3', { text: 'Karar kaydı (record)' }), h('p', { class: 'sub', text: 'İş akışını çalıştırınca burada veri şekli, her atomun tahmini süresi, seçilen atom ve nedeni görünür.' }));
    }
    if (node.type === 'molekul.ExactMatch' || node.type.startsWith('atom.')) {
      box.append(h('div', { class: 'row', style: { marginTop: '10px' } },
        h('button', { type: 'button', id: 'yaristir', disabled: !r || r.status !== 'bitti' || state.running, onclick: () => race(node.id), text: 'Atomları yarıştır' })),
        h('p', { class: 'sub', style: { marginTop: '6px' }, text: 'Aynı girdide bütün atomları bu tarayıcıda ölçer (ısınma + 5 tekrarın medyanı) ve molekülün tahminiyle yan yana koyar. Gösterim amaçlıdır; rapordaki sayılar Node ölçümleridir.' }));
    }
    box.append(h('div', { class: 'row', style: { marginTop: '14px' } }, h('button', { type: 'button', class: 'danger', text: 'Kutuyu sil', onclick: deleteSelection })));
    return;
  }
  // Seçim yok: iş akışının genel durumu
  const problems = validateWorkflow(state.wf, catalog);
  box.append(
    h('h2', { text: 'İş akışı' }),
    packageInfo(),
    h('p', { class: 'sub', text: `${state.wf.nodes.length} kutu, ${state.wf.edges.length} bağlantı · çalıştırma: ${runnerMode() === 'worker' ? 'Web Worker (arayüz donmaz)' : runnerMode()}` }),
    problems.length ? h('div', {}, h('h3', { text: 'Çalıştırmadan önce' }), h('ul', { class: 'problems' }, ...problems.map((p) => h('li', { text: p.message })))) : h('p', { class: 'note', text: state.wf.nodes.length ? 'İş akışı çalıştırılmaya hazır.' : 'Soldan bir hazır paket seçin ya da bileşenleri tuvale sürükleyin.' }),
    h('h3', { text: 'Uç türleri' }),
    h('div', { class: 'legend' }, ...TYPE_ORDER.map(chip)),
    h('p', { class: 'sub', style: { marginTop: '6px' }, text: 'Yalnızca aynı türdeki uçlar bağlanır; uyumsuz bağlantı nedeniyle birlikte reddedilir.' }),
    h('h3', { text: 'Klavye' }),
    h('ul', { class: 'shortcuts' },
      h('li', {}, 'Bileşen listesinde ', h('span', { class: 'kbd', text: 'Enter' }), ': tuvale ekler'),
      h('li', {}, 'Kutuda ', h('span', { class: 'kbd', text: '← ↑ → ↓' }), ' taşır (', h('span', { class: 'kbd', text: 'Shift' }), ' ile 50 px), ', h('span', { class: 'kbd', text: 'Delete' }), ' siler'),
      h('li', {}, 'Bir uçta ', h('span', { class: 'kbd', text: 'Enter' }), ', sonra karşı uçta ', h('span', { class: 'kbd', text: 'Enter' }), ': bağlar; ', h('span', { class: 'kbd', text: 'Esc' }), ' vazgeçer'),
      h('li', {}, h('span', { class: 'kbd', text: 'Ctrl' }), ' + ', h('span', { class: 'kbd', text: 'Enter' }), ': çalıştırır')));
}

// ------------------------------------------------------------------ çalıştırma ve sonuçlar
function findingTotal(run) {
  return state.wf.nodes.filter((n) => n.type === 'uyarlayici.bulgu').reduce((sum, n) => sum + (run.nodes[n.id]?.info?.count ?? 0), 0);
}

function setBadge(text, kind) {
  const b = $('durum');
  if (text) {
    b.textContent = text;
    b.dataset.state = kind;
    return;
  }
  if (state.running) { b.textContent = 'çalışıyor…'; b.dataset.state = 'running'; return; }
  if (!state.run) { b.textContent = 'çalışmadı'; b.dataset.state = 'idle'; return; }
  if (state.dirty) { b.textContent = 'çalışmadı (değişiklik var)'; b.dataset.state = 'idle'; return; }
  const run = state.run;
  if (!run.ok) {
    const first = run.problems?.[0]?.message ?? Object.values(run.nodes).find((r) => r.status === 'hata')?.error ?? 'bilinmeyen hata';
    b.textContent = `hata: ${first}`;
    b.dataset.state = 'error';
    return;
  }
  const n = findingTotal(run);
  const gate = Object.values(run.nodes).some((r) => r.info?.gate === 'kaldı');
  b.textContent = `bitti: ${nf(n, 0)} bulgu, ${fmtMs(run.totalMs)}${gate ? ' · kapı kaldı' : ''}`;
  b.dataset.state = gate ? 'gate' : 'done';
}

async function run() {
  if (state.running) return;
  disarm();
  const problems = validateWorkflow(state.wf, catalog);
  if (problems.length) {
    state.run = { ok: false, problems, nodes: {}, totalMs: 0 };
    state.dirty = false;
    setBadge();
    state.sel = null;
    renderProps();
    toast(`Çalıştırılamadı: ${problems[0].message}`, 'err');
    return;
  }
  state.running = true;
  state.live = {};
  state.race = null;
  setBadge();
  renderCanvas();
  const data = serializeWorkflow(state.wf);
  try {
    const res = await runWorkflowRemote(data, (p) => {
      state.live[p.node] = p;
      const el = document.querySelector(`.node[data-id="${CSS.escape(p.node)}"]`);
      if (el) {
        el.dataset.status = p.status;
        el.querySelector('.node-foot span').textContent = p.status === 'çalışıyor' ? 'çalışıyor…' : `${fmtMs(p.ms)} · ${p.summary ?? p.error ?? ''}`;
      }
    });
    state.run = res;
    state.dirty = JSON.stringify(serializeWorkflow(state.wf)) !== JSON.stringify(data);
  } catch (err) {
    state.run = { ok: false, problems: [{ message: err.message }], nodes: {}, totalMs: 0 };
  } finally {
    state.running = false;
    state.live = {};
  }
  setBadge();
  renderCanvas();
  renderProps();
  renderResults();
  if (!state.run.ok) toast($('durum').textContent, 'err');
}

async function race(nodeId) {
  const btn = $('yaristir');
  if (btn) { btn.disabled = true; btn.textContent = 'Ölçülüyor…'; }
  setTab('yaris');
  $('panel-yaris').replaceChildren(h('p', { class: 'empty', text: 'Atomlar bu tarayıcıda ölçülüyor (Web Worker içinde; arayüz donmaz)…' }));
  try {
    state.race = { node: nodeId, ...(await raceRemote(nodeId, 5)) };
  } catch (err) {
    state.race = { error: err.message };
  }
  renderResults();
  renderProps();
}

function previewCell(pv) {
  if (!pv) return h('td', { class: 'pv' });
  return h('td', { class: 'pv', title: pv.before + pv.hit + pv.after }, pv.before, h('mark', { text: pv.hit }), pv.after);
}

function renderResults() {
  const run = state.run && !state.dirty ? state.run : null;
  const nodesOf = (type) => state.wf.nodes.filter((n) => n.type === type && run?.nodes[n.id]?.status === 'bitti');
  // Bulgular
  const pb = $('panel-bulgular');
  pb.replaceChildren();
  const tables = nodesOf('cikti.tablo');
  if (!run) pb.append(h('p', { class: 'empty', text: state.dirty ? 'İş akışı değişti; sonuçları görmek için yeniden çalıştırın.' : 'Henüz çalıştırılmadı. Soldan bir hazır paket seçin ya da kutuları bağlayıp "Tarayıcıda çalıştır"a basın.' }));
  else if (!tables.length) pb.append(h('p', { class: 'empty', text: 'Bu iş akışında "Bulgu tablosu" kutusu yok; sayılar Özet sekmesinde.' }));
  for (const n of tables) {
    const list = run.nodes[n.id].info.findings ?? [];
    const LIMIT = 500;
    pb.append(h('h4', { text: `Bulgu tablosu (${n.id}) · ${nf(list.length, 0)} bulgu${list.length > LIMIT ? ` · ilk ${LIMIT} gösteriliyor` : ''}` }),
      list.length ? h('table', { class: 'findings' },
        h('thead', {}, h('tr', {}, h('th', { text: 'dosya:satır:sütun' }), h('th', { text: 'desen' }), h('th', { text: 'satır' }))),
        h('tbody', {}, ...list.slice(0, LIMIT).map((f) => h('tr', {},
          h('td', { class: 'loc', text: `${f.file}:${f.line}:${f.column}` }), h('td', { class: 'mono', text: f.pattern }), previewCell(f.preview))))) : h('p', { class: 'empty', text: 'Bulgu yok.' }));
  }
  // Özet
  const po = $('panel-ozet');
  po.replaceChildren();
  if (!run) po.append(h('p', { class: 'empty', text: 'Özet, çalıştırmadan sonra burada görünür.' }));
  else {
    const counters = h('div', { class: 'counters' },
      h('div', { class: 'counter' }, h('b', { text: nf(findingTotal(run), 0) }), h('span', { text: 'toplam bulgu' })),
      h('div', { class: 'counter' }, h('b', { text: fmtMs(run.totalMs) }), h('span', { text: 'toplam süre (veri yükleme dahil)' })),
      ...nodesOf('cikti.kapi').map((n) => {
        const g = run.nodes[n.id].info;
        return h('div', { class: `counter ${g.gate === 'kaldı' ? 'bad' : 'good'}` }, h('b', { text: g.gate === 'kaldı' ? 'KALDI' : 'GEÇTİ' }), h('span', { text: g.gate === 'kaldı' ? `kapı: ${g.count} bulgu → çıkış kodu 1` : 'kapı: bulgu yok → çıkış kodu 0' }));
      }),
      ...state.wf.nodes.filter((n) => n.type === 'molekul.ExactMatch' && run.nodes[n.id]?.info?.record).map((n) => h('div', { class: 'counter' }, h('b', { style: { fontSize: '16px' }, text: run.nodes[n.id].info.record.selected.replace('Search', '') }), h('span', { text: `molekülün seçimi (${n.id})` }))));
    po.append(counters);
    const cols = h('div', { class: 'cols' });
    for (const n of nodesOf('cikti.ozet')) {
      const info = run.nodes[n.id].info;
      const max = Math.max(1, ...info.byPattern.map((x) => x[1]));
      cols.append(h('div', {},
        h('h4', { text: `Özet (${n.id}) · ${nf(info.total, 0)} bulgu` }),
        h('div', { class: 'bars' }, ...info.byPattern.map(([pat, c]) => h('div', { class: 'bar' }, h('span', { class: 'n mono', text: pat }), h('span', { class: 'track' }, h('span', { class: 'fill', style: { width: `${(c / max) * 100}%`, background: 'var(--t-find)' } })), h('span', { class: 'v', text: nf(c, 0) })))),
        info.byFile.length > 1 ? h('details', {}, h('summary', { text: `Dosyalara göre (ilk ${info.byFile.length})` }), h('ul', { class: 'conn-list' }, ...info.byFile.map(([f, c]) => h('li', {}, h('span', { class: 'mono', text: f }), h('b', { text: String(c) }))))) : null));
    }
    for (const n of nodesOf('cikti.jsonl')) {
      const info = run.nodes[n.id].info;
      cols.append(h('div', {}, h('h4', { text: `JSONL (${n.id})` }),
        h('p', { class: 'sub', text: `${info.summary} Biçim: ios scan --json ile aynı.` }),
        h('button', { type: 'button', text: `${info.filename} indir`, onclick: () => download(info.filename, info.jsonl, 'application/x-ndjson') })));
    }
    po.append(cols);
  }
  // Açıklama
  const pa = $('panel-aciklama');
  pa.replaceChildren(state.explain ? h('pre', { class: 'explain', text: state.explain }) : h('p', { class: 'empty', text: '"Açıkla" düğmesi iş akışını düz Türkçe cümlelerle anlatır (kurala dayalı; yapay zekâ servisi kullanılmaz).' }));
  // Yarış
  const py = $('panel-yaris');
  py.replaceChildren();
  const rc = state.race;
  if (!rc) py.append(h('p', { class: 'empty', text: 'Bir ExactMatch ya da atom kutusunu seçip özellikler panelindeki "Atomları yarıştır" düğmesine basın (önce iş akışını çalıştırın).' }));
  else if (rc.error) py.append(h('p', { class: 'problems', text: rc.error }));
  else {
    const rows = [...rc.rows].sort((a, b) => a.ms - b.ms);
    const maxMs = Math.max(...rows.map((r) => r.ms), ...rows.map((r) => r.estimatedMs ?? 0));
    py.append(
      h('p', { class: 'note', text: `Tarayıcı ölçümü gösterim amaçlıdır; rapordaki sayılar Node ölçümleridir (bench/results). Girdi (${rc.node}): ${nf(rc.records, 0)} kayıt, ${nf(rc.chars, 0)} karakter, ${rc.patterns} desen; her atom ısınma + ${rc.reps} tekrarın medyanı, dönüşümlü sırayla. En hızlı: ${rc.fastest}; molekülün seçimi: ${rc.selected}${rc.fastest === rc.selected ? ' (aynı)' : ''}.` }),
      h('table', { class: 'race' },
        h('thead', {}, h('tr', {}, h('th', { text: 'Atom' }), h('th', { text: 'ölçülen (medyan)' }), h('th', {}), h('th', { text: 'molekülün tahmini' }), h('th', {}), h('th', { text: 'not' }))),
        h('tbody', {}, ...rows.map((r) => h('tr', { class: r.name === rc.selected ? 'sel' : '' },
          h('td', { text: r.name }),
          h('td', { class: 'num', text: fmtMs(r.ms) }),
          h('td', {}, h('div', { class: 'track' }, h('div', { class: 'fill', style: { width: `${(r.ms / maxMs) * 100}%` } }))),
          h('td', { class: 'num', text: r.estimatedMs == null ? '—' : fmtMs(r.estimatedMs) }),
          h('td', {}, r.estimatedMs == null ? null : h('div', { class: 'track' }, h('div', { class: 'fill est', style: { width: `${(r.estimatedMs / maxMs) * 100}%` } }))),
          h('td', { text: [r.name === rc.fastest ? 'en hızlı' : '', r.name === rc.selected ? 'molekülün seçimi' : '', r.applicable ? '' : `uygun değil: ${r.reason}`].filter(Boolean).join(' · ') }))))),
      h('p', { class: 'sub', style: { marginTop: '6px' }, text: 'Tahminler kalibrasyon makinesine göredir (bench/results/calibration.json); tarayıcı ve makine farklı olduğu için mutlak değerler değil, sıralama karşılaştırılmalıdır.' }));
  }
}

function setTab(name) {
  state.tab = name;
  for (const t of ['bulgular', 'ozet', 'aciklama', 'yaris']) {
    $(`sekme-${t}`).setAttribute('aria-selected', String(t === name));
    $(`sekme-${t}`).tabIndex = t === name ? 0 : -1;
    $(`panel-${t}`).hidden = t !== name;
  }
  $('sonuclar').classList.remove('collapsed');
  $('sonuc-katla').setAttribute('aria-expanded', 'true');
}

// ------------------------------------------------------------------ yükleme, dışa/içe aktarma, paylaşım
function setWorkflow(wf, { pkg = null } = {}) {
  state.wf = wf;
  state.sel = null;
  state.run = null;
  state.dirty = false;
  state.race = null;
  state.explain = null;
  state.pkg = pkg;
  $('wf-ad').value = wf.name;
  $('wf-hedef').value = wf.target;
  renderPackages();
  renderCanvas();
  fit();
  renderProps();
  renderResults();
  setBadge();
}

const EXPECTED_LABELS = { bulgu: 'molekül dalı', bulgu_atom: 'tek atom dalı', tek_bulgu: 'tek desen dalı', cok_bulgu: '16 desen dalı' };
function packageInfo() {
  const p = state.pkg && packageById(state.pkg);
  if (!p) return null;
  const keys = Object.keys(p.expected);
  const expected = keys.length === 1 ? `${nf(p.expected[keys[0]], 0)} bulgu` : keys.map((k) => `${EXPECTED_LABELS[k] ?? k}: ${nf(p.expected[k], 0)}`).join(' · ');
  return h('section', { class: 'pkg', 'aria-label': 'Hazır paket' },
    h('h3', { text: `Paket: # ${p.channel}` }),
    h('p', { text: p.summary }),
    h('p', {}, h('b', { text: 'Beklenen sonuç: ' }), expected),
    h('details', {}, h('summary', { text: 'Aynı işi yapan komut satırı' }), ...p.cli.map((c) => h('code', { class: 'cmd', text: c }))));
}

function loadPackage(id) {
  const p = packageById(id);
  if (!p) return toast(`Bilinmeyen paket: ${id}`, 'err');
  setWorkflow(deserializeWorkflow(p.build(), catalog), { pkg: id });
  history.replaceState(null, '', `#paket=${encodeURIComponent(id)}`);
  if (isMobile()) openSide(false);
  toast(`Paket açıldı: ${p.channel}. "Tarayıcıda çalıştır"a basın.`);
}

function download(name, text, type = 'application/json') {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = h('a', { href: url, download: name });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const slug = (s) => s.toLocaleLowerCase('tr-TR').replace(/[ıİ]/g, 'i').replace(/ğ/g, 'g').replace(/ü/g, 'u').replace(/ş/g, 's').replace(/ö/g, 'o').replace(/ç/g, 'c').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'is-akisi';

function b64urlEncode(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = '';
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function b64urlDecode(s) {
  const bin = atob(s.replace(/-/g, '+').replace(/_/g, '/'));
  return new TextDecoder().decode(Uint8Array.from(bin, (c) => c.charCodeAt(0)));
}

function loadFromHash() {
  const hash = location.hash.slice(1);
  const params = new URLSearchParams(hash);
  try {
    if (params.has('wf')) {
      const wf = deserializeWorkflow(JSON.parse(b64urlDecode(params.get('wf'))), catalog);
      setWorkflow(wf);
      toast('Bağlantıdaki iş akışı yüklendi.');
      return true;
    }
    if (params.has('paket') && packageById(params.get('paket'))) {
      loadPackage(params.get('paket'));
      return true;
    }
  } catch (err) {
    toast(`Bağlantıdaki iş akışı okunamadı: ${err.message}`, 'err');
  }
  return false;
}

async function share() {
  const json = JSON.stringify(serializeWorkflow(state.wf));
  const url = `${location.href.split('#')[0]}#wf=${b64urlEncode(json)}`;
  history.replaceState(null, '', url);
  if (url.length > 60000) toast('Bağlantı çok uzun (yüklenen dosya içerikleri de içinde). Bunun yerine "Dışa aktar" ile JSON paylaşın.', 'err');
  try {
    await navigator.clipboard.writeText(url);
    toast(`Bağlantı panoya kopyalandı (${nf(url.length, 0)} karakter).`);
  } catch {
    toast('Bağlantı adres çubuğuna yazıldı; oradan kopyalayın.');
  }
}

function applyTheme(t) {
  if (t) document.documentElement.dataset.theme = t;
  try { localStorage.setItem('kba-tema', t); } catch { /* özel pencere: tercih saklanmaz */ }
}

// ------------------------------------------------------------------ olaylar
function bind() {
  $('ara').addEventListener('input', renderPalette);
  $('side-ac').addEventListener('click', () => openSide(true));
  $('side-kapat').addEventListener('click', () => openSide(false));
  $('scrim').addEventListener('click', () => openSide(false));
  $('calistir').addEventListener('click', run);
  $('acikla').addEventListener('click', () => {
    state.explain = explainWorkflow(state.wf, catalog, state.run && !state.dirty ? state.run : null);
    setTab('aciklama');
    renderResults();
  });
  $('disa').addEventListener('click', () => {
    download(`${slug(state.wf.name)}.json`, JSON.stringify(serializeWorkflow(state.wf), null, 2) + '\n');
    toast('İş akışı JSON olarak indirildi.');
  });
  $('ice').addEventListener('click', () => $('ice-dosya').click());
  $('ice-dosya').addEventListener('change', async (e) => {
    const f = e.target.files[0];
    e.target.value = '';
    if (!f) return;
    try {
      const wf = deserializeWorkflow(JSON.parse(await f.text()), catalog);
      setWorkflow(wf);
      history.replaceState(null, '', location.pathname + location.search);
      toast(`"${wf.name}" içe aktarıldı: ${wf.nodes.length} kutu, ${wf.edges.length} bağlantı.`);
    } catch (err) {
      toast(`İçe aktarılamadı: ${err.message}`, 'err');
    }
  });
  $('paylas').addEventListener('click', share);
  $('tema').addEventListener('click', () => {
    const dark = getComputedStyle(document.documentElement).colorScheme.includes('dark');
    applyTheme(dark ? 'light' : 'dark');
  });
  $('wf-ad').addEventListener('input', (e) => { state.wf.name = e.target.value; changed({ structure: false }); });
  $('wf-hedef').addEventListener('input', (e) => { state.wf.target = e.target.value; changed({ structure: false }); });
  $('yaklas').addEventListener('click', () => setZoom(state.zoom + 0.1));
  $('uzaklas').addEventListener('click', () => setZoom(state.zoom - 0.1));
  $('sigdir').addEventListener('click', fit);
  $('temizle').addEventListener('click', () => {
    if (state.wf.nodes.length && !confirm('Tuvaldeki bütün kutular silinsin mi?')) return;
    setWorkflow(createWorkflow({ name: 'Yeni iş akışı' }));
    history.replaceState(null, '', location.pathname + location.search);
  });
  $('sonuc-katla').addEventListener('click', () => {
    const c = $('sonuclar').classList.toggle('collapsed');
    $('sonuc-katla').setAttribute('aria-expanded', String(!c));
    $('sonuc-katla').textContent = c ? '▴' : '▾';
  });
  const tabs = ['bulgular', 'ozet', 'aciklama', 'yaris'];
  for (const t of tabs) {
    $(`sekme-${t}`).addEventListener('click', () => setTab(t));
    $(`sekme-${t}`).addEventListener('keydown', (e) => {
      const i = tabs.indexOf(t);
      const j = e.key === 'ArrowRight' ? (i + 1) % tabs.length : e.key === 'ArrowLeft' ? (i + tabs.length - 1) % tabs.length : -1;
      if (j >= 0) { setTab(tabs[j]); $(`sekme-${tabs[j]}`).focus(); }
    });
  }
  // Tuvale bırakma (paletten sürükle-bırak)
  const board = $('board');
  const sc = $('tuval');
  sc.addEventListener('dragover', (e) => {
    if (![...e.dataTransfer.types].includes('application/x-kba-type')) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    board.classList.add('drop');
  });
  sc.addEventListener('dragleave', () => board.classList.remove('drop'));
  sc.addEventListener('drop', (e) => {
    const type = e.dataTransfer.getData('application/x-kba-type');
    board.classList.remove('drop');
    if (!type || !catalog.get(type)) return;
    e.preventDefault();
    const p = boardPoint(e);
    addFromPalette(type, { x: Math.max(0, Math.round((p.x - NODE_W / 2) / GRID) * GRID), y: Math.max(0, Math.round((p.y - 19) / GRID) * GRID) });
  });
  sc.addEventListener('pointerdown', (e) => {
    if (e.target === sc || e.target === board || e.target.id === 'dugumler' || e.target.id === 'kablolar') {
      if (state.armed) disarm();
      if (state.sel) select(null);
    }
  });
  document.addEventListener('keydown', (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName ?? '');
    if (e.key === 'Escape') {
      if (state.armed) disarm();
      else if ($('side').classList.contains('open')) openSide(false);
      else if (state.sel && !typing) select(null);
    } else if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      run();
    } else if (!typing && (e.key === 'Delete' || e.key === 'Backspace') && state.sel?.kind === 'edge') {
      e.preventDefault();
      deleteSelection();
    }
  });
  window.addEventListener('hashchange', loadFromHash);
  window.addEventListener('resize', () => applyZoom());
}

// ------------------------------------------------------------------ başlat
bind();
renderPalette();
renderPackages();
if (!loadFromHash()) loadPackage(PACKAGES[0].id);
setTab('bulgular');
initRunner().then(() => { if (!state.sel) renderProps(); });
// Testler ve hata ayıklama için (arayüzün kendisi kullanmaz)
window.__atolye = { state, catalog, serialize: () => serializeWorkflow(state.wf) };

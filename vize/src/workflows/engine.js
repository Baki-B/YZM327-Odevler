// İş akışı motoru (workflow engine): kutular (düğüm), bağlantılar, tür denetimi,
// topolojik sıra ve çalıştırma. DOM'a, dosya sistemine ve ağa dokunmaz; aynı modül
// tarayıcıda (web/, Web Worker içinde) ve Node'da (testler) çalışır.
//
// Sözlük:
//   bileşen (component)  kataloğdaki tanım: girişleri, çıkışları, ayarları, run() işlevi
//   düğüm (node)         iş akışındaki bir kutu: { id, type, params, x, y }
//   uç (port)            bir düğümün adlandırılmış girişi ya da çıkışı; her ucun bir türü var
//   bağlantı (edge)      { from: { node, port }, to: { node, port } }
//
// Uç türleri IoS veri türlerine benzetildi: Source.File, FASTA.Entry, Pattern.Set,
// Sequence.Match, Finding. Bağlantı yalnızca aynı türdeki uçlar arasında kurulabilir.

export const FORMAT = 'kod-bilimi-atolyesi/workflow';
export const FORMAT_VERSION = 1;

/** Boş bir iş akışı. */
export function createWorkflow({ name = 'Adsız iş akışı', target = '', nodes = [], edges = [] } = {}) {
  return { name, target, nodes: nodes.map((n) => ({ ...n, params: { ...(n.params ?? {}) } })), edges: edges.map(cloneEdge) };
}

function cloneEdge(e) {
  return { from: { node: e.from.node, port: e.from.port }, to: { node: e.to.node, port: e.to.port } };
}

/** Kataloğu (bileşen listesi) tür adına göre arar. */
export function componentOf(catalog, type) {
  const c = catalog.get(type);
  if (!c) throw new Error(`Bilinmeyen bileşen türü: ${type}`);
  return c;
}

/** Varsayılan ayarlarla yeni bir düğüm ekler; düğümü döndürür. */
export function addNode(wf, catalog, type, { id, x = 0, y = 0, params = {} } = {}) {
  const comp = componentOf(catalog, type);
  const defaults = {};
  for (const p of comp.params ?? []) defaults[p.key] = structuredCloneSafe(p.default);
  const node = { id: id ?? nextId(wf, comp.idPrefix ?? 'n'), type, x, y, params: { ...defaults, ...params } };
  if (wf.nodes.some((n) => n.id === node.id)) throw new Error(`Bu kimlikte bir düğüm zaten var: ${node.id}`);
  wf.nodes.push(node);
  return node;
}

function structuredCloneSafe(v) {
  return v === undefined ? undefined : JSON.parse(JSON.stringify(v));
}

function nextId(wf, prefix) {
  let i = 1;
  const used = new Set(wf.nodes.map((n) => n.id));
  while (used.has(`${prefix}${i}`)) i++;
  return `${prefix}${i}`;
}

/** Düğümü ve ona bağlı bütün bağlantıları siler. */
export function removeNode(wf, id) {
  wf.nodes = wf.nodes.filter((n) => n.id !== id);
  wf.edges = wf.edges.filter((e) => e.from.node !== id && e.to.node !== id);
}

export function removeEdge(wf, edge) {
  wf.edges = wf.edges.filter((e) => !sameEdge(e, edge));
}

function sameEdge(a, b) {
  return a.from.node === b.from.node && a.from.port === b.from.port && a.to.node === b.to.node && a.to.port === b.to.port;
}

function nodeOf(wf, id) {
  return wf.nodes.find((n) => n.id === id);
}

function portOf(comp, side, name) {
  return (side === 'out' ? comp.outputs : comp.inputs).find((p) => p.name === name);
}

/**
 * Bir bağlantı kurulabilir mi? { ok: true } ya da { ok: false, reason } döner.
 * Nedenler kullanıcıya gösterilecek Türkçe cümlelerdir.
 */
export function canConnect(wf, catalog, from, to) {
  const a = nodeOf(wf, from.node);
  const b = nodeOf(wf, to.node);
  if (!a || !b) return { ok: false, reason: 'Bağlantının ucundaki kutu bulunamadı.' };
  if (a.id === b.id) return { ok: false, reason: 'Bir kutu kendine bağlanamaz.' };
  const ca = componentOf(catalog, a.type);
  const cb = componentOf(catalog, b.type);
  const out = portOf(ca, 'out', from.port);
  const inp = portOf(cb, 'in', to.port);
  if (!out) return { ok: false, reason: `"${ca.title}" kutusunun "${from.port}" adlı bir çıkışı yok.` };
  if (!inp) return { ok: false, reason: `"${cb.title}" kutusunun "${to.port}" adlı bir girişi yok.` };
  if (out.type !== inp.type) {
    return {
      ok: false,
      reason: `Tür uyuşmuyor: "${ca.title}" ${out.type} üretiyor, "${cb.title}" kutusunun "${inp.label ?? inp.name}" girişi ${inp.type} bekliyor.` +
        (HINTS[`${out.type}→${inp.type}`] ? ' ' + HINTS[`${out.type}→${inp.type}`] : ''),
    };
  }
  if (wf.edges.some((e) => sameEdge(e, { from, to }))) return { ok: false, reason: 'Bu bağlantı zaten var.' };
  if (!inp.multi && wf.edges.some((e) => e.to.node === to.node && e.to.port === to.port)) {
    return { ok: false, reason: `"${cb.title}" kutusunun "${inp.label ?? inp.name}" girişi yalnızca bir bağlantı alır; önce eskisini silin.` };
  }
  if (reaches(wf, b.id, a.id)) return { ok: false, reason: 'Bu bağlantı bir döngü oluşturur; iş akışı döngüsüz olmalı.' };
  return { ok: true };
}

// Sık yapılan yanlış bağlantılar için ipuçları.
const HINTS = {
  'Source.File→FASTA.Entry': 'Araya bir uyarlayıcı koyun: "Kaynak → FASTA.Entry" ya da "FASTA okuyucu".',
  'Sequence.Match→Finding': 'Araya "Eşleşme → Bulgu" uyarlayıcısını koyun.',
  'Source.File→Pattern.Set': 'Desenler bir desen kümesi kutusundan gelmeli.',
  'FASTA.Entry→Pattern.Set': 'Desenler bir desen kümesi kutusundan gelmeli.',
};

/** from düğümünden to düğümüne bir yol var mı? (döngü denetimi) */
function reaches(wf, from, to) {
  const seen = new Set();
  const stack = [from];
  while (stack.length) {
    const id = stack.pop();
    if (id === to) return true;
    if (seen.has(id)) continue;
    seen.add(id);
    for (const e of wf.edges) if (e.from.node === id) stack.push(e.to.node);
  }
  return false;
}

/** Bağlantı ekler; kurulamıyorsa nedeniyle birlikte hata fırlatır. */
export function connect(wf, catalog, from, to) {
  const r = canConnect(wf, catalog, from, to);
  if (!r.ok) {
    const err = new Error(r.reason);
    err.code = 'BAGLANTI_REDDEDILDI';
    throw err;
  }
  const edge = cloneEdge({ from, to });
  wf.edges.push(edge);
  return edge;
}

/**
 * Topolojik sıra (Kahn algoritması): her düğüm, girdilerini üreten bütün düğümlerden
 * sonra gelir. Eşit durumda düğümlerin listedeki sırası korunur (deterministik).
 */
export function topologicalOrder(wf) {
  const indeg = new Map(wf.nodes.map((n) => [n.id, 0]));
  for (const e of wf.edges) if (indeg.has(e.to.node)) indeg.set(e.to.node, indeg.get(e.to.node) + 1);
  const order = [];
  const done = new Set();
  while (order.length < wf.nodes.length) {
    const next = wf.nodes.find((n) => !done.has(n.id) && indeg.get(n.id) === 0);
    if (!next) throw new Error('İş akışında döngü var; topolojik sıra kurulamadı.');
    order.push(next);
    done.add(next.id);
    for (const e of wf.edges) if (e.from.node === next.id) indeg.set(e.to.node, indeg.get(e.to.node) - 1);
  }
  return order;
}

/**
 * Çalıştırmadan önceki denetim: bilinmeyen tür, bozuk bağlantı, tür uyuşmazlığı,
 * eksik zorunlu giriş, döngü. Sorun listesi döner (boşsa iş akışı çalıştırılabilir).
 */
export function validateWorkflow(wf, catalog) {
  const problems = [];
  for (const n of wf.nodes) {
    if (!catalog.get(n.type)) problems.push({ node: n.id, message: `Bilinmeyen bileşen türü: ${n.type}` });
  }
  if (problems.length) return problems;
  for (const e of wf.edges) {
    const a = nodeOf(wf, e.from.node);
    const b = nodeOf(wf, e.to.node);
    if (!a || !b) { problems.push({ message: 'Var olmayan bir kutuya bağlantı var.' }); continue; }
    const out = portOf(componentOf(catalog, a.type), 'out', e.from.port);
    const inp = portOf(componentOf(catalog, b.type), 'in', e.to.port);
    if (!out || !inp) problems.push({ node: b.id, message: 'Var olmayan bir uca bağlantı var.' });
    else if (out.type !== inp.type) problems.push({ node: b.id, message: `Tür uyuşmuyor: ${out.type} → ${inp.type}` });
  }
  for (const n of wf.nodes) {
    const comp = componentOf(catalog, n.type);
    for (const p of comp.inputs) {
      const count = wf.edges.filter((e) => e.to.node === n.id && e.to.port === p.name).length;
      if (count === 0 && !p.optional) problems.push({ node: n.id, message: `"${comp.title}": "${p.label ?? p.name}" girişi (${p.type}) bağlı değil.` });
      if (count > 1 && !p.multi) problems.push({ node: n.id, message: `"${comp.title}": "${p.label ?? p.name}" girişine birden çok bağlantı var.` });
    }
  }
  try {
    topologicalOrder(wf);
  } catch (err) {
    problems.push({ message: err.message });
  }
  return problems;
}

/**
 * İş akışını çalıştırır. Düğümler topolojik sırayla, birer birer çalışır; her düğümün
 * run(inputs, params, ctx) işlevi çıkış adı → değer nesnesi döndürür (ya da Promise).
 * Bir düğüm hata verirse ona bağlı düğümler "atlandı" olur, diğerleri çalışmaya devam eder.
 *
 * @param ctx { now(): ms, loadSample(name), onNode(id, durum), yieldEvery } — hepsi isteğe bağlı
 * @returns {{ ok, problems, order, nodes: { [id]: { status, ms, outputs, info, error } } }}
 */
export async function runWorkflow(wf, catalog, ctx = {}) {
  const problems = validateWorkflow(wf, catalog);
  if (problems.length) return { ok: false, problems, order: [], nodes: {} };
  const now = ctx.now ?? (() => Date.now());
  const order = topologicalOrder(wf);
  const results = {};
  for (const node of order) {
    const comp = componentOf(catalog, node.type);
    const incoming = wf.edges.filter((e) => e.to.node === node.id);
    const failedParent = incoming.find((e) => results[e.from.node]?.status !== 'bitti');
    if (failedParent) {
      results[node.id] = { status: 'atlandı', ms: 0, outputs: {}, info: null, error: `Önceki kutu (${failedParent.from.node}) tamamlanamadı.` };
      ctx.onNode?.(node.id, results[node.id]);
      continue;
    }
    const inputs = {};
    for (const p of comp.inputs) {
      const vals = incoming.filter((e) => e.to.port === p.name).map((e) => results[e.from.node].outputs[e.from.port]);
      inputs[p.name] = p.multi ? vals : vals[0];
    }
    ctx.onNode?.(node.id, { status: 'çalışıyor' });
    const t0 = now();
    try {
      const info = {};
      const outputs = (await comp.run(inputs, node.params ?? {}, { ...ctx, info, node })) ?? {};
      results[node.id] = { status: 'bitti', ms: now() - t0, outputs, info, error: null };
    } catch (err) {
      results[node.id] = { status: 'hata', ms: now() - t0, outputs: {}, info: null, error: err?.message ?? String(err) };
    }
    ctx.onNode?.(node.id, results[node.id]);
    // Uzun iş akışında arayüze (ya da işçi iş parçacığının ileti kuyruğuna) nefes aldır.
    if (ctx.yieldEvery !== 0) await new Promise((r) => setTimeout(r, 0));
  }
  const ok = Object.values(results).every((r) => r.status === 'bitti');
  return { ok, problems: [], order: order.map((n) => n.id), nodes: results };
}

/** JSON'a çevirme (dışa aktarma). Konumlar ve ayarlar dahil. */
export function serializeWorkflow(wf) {
  return {
    format: FORMAT,
    version: FORMAT_VERSION,
    name: wf.name,
    target: wf.target,
    nodes: wf.nodes.map((n) => ({ id: n.id, type: n.type, x: Math.round(n.x ?? 0), y: Math.round(n.y ?? 0), params: n.params ?? {} })),
    edges: wf.edges.map(cloneEdge),
  };
}

/** JSON'dan geri kurma (içe aktarma). Bozuk ya da yabancı dosyayı nedeniyle reddeder. */
export function deserializeWorkflow(data, catalog) {
  if (!data || typeof data !== 'object') throw new Error('İş akışı dosyası bir JSON nesnesi olmalı.');
  if (data.format !== FORMAT) throw new Error(`Bu dosya bir atölye iş akışı değil (format: ${data.format ?? 'yok'}).`);
  if (data.version !== FORMAT_VERSION) throw new Error(`Desteklenmeyen sürüm: ${data.version}`);
  if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) throw new Error('nodes ve edges dizi olmalı.');
  const wf = createWorkflow({ name: String(data.name ?? 'Adsız iş akışı'), target: String(data.target ?? '') });
  for (const n of data.nodes) {
    if (typeof n?.id !== 'string' || typeof n?.type !== 'string') throw new Error('Her düğümün id ve type alanı olmalı.');
    addNode(wf, catalog, n.type, { id: n.id, x: Number(n.x) || 0, y: Number(n.y) || 0, params: n.params ?? {} });
  }
  for (const e of data.edges) connect(wf, catalog, e.from, e.to);
  return wf;
}

/**
 * İş akışını düz Türkçe cümlelerle anlatır. Kurala dayalıdır: her bileşenin
 * describe(params) cümlesi topolojik sırayla, bağlantılarla birleştirilir.
 * (Yapay zekâ servisi kullanılmaz; aynı iş akışı her zaman aynı metni verir.)
 */
export function explainWorkflow(wf, catalog, run = null) {
  const lines = [];
  const problems = validateWorkflow(wf, catalog);
  lines.push(`"${wf.name}" iş akışında ${wf.nodes.length} kutu ve ${wf.edges.length} bağlantı var.`);
  if (wf.target) lines.push(`Hedef: ${wf.target}`);
  if (problems.length) {
    lines.push(`Çalıştırmadan önce düzeltilmesi gereken ${problems.length} sorun var:`);
    for (const p of problems) lines.push(`  • ${p.message}`);
    return lines.join('\n');
  }
  const order = topologicalOrder(wf);
  const titleOf = (id) => componentOf(catalog, nodeOf(wf, id).type).title;
  let step = 1;
  for (const node of order) {
    const comp = componentOf(catalog, node.type);
    const from = wf.edges.filter((e) => e.to.node === node.id).map((e) => `"${titleOf(e.from.node)}"`);
    const what = comp.describe ? comp.describe(node.params ?? {}) : comp.title;
    const src = from.length ? ` ${[...new Set(from)].join(' ve ')} kutusundan gelen veriyle` : '';
    let s = `${step++}. "${comp.title}"${src}: ${what}`;
    const r = run?.nodes?.[node.id];
    if (r?.status === 'bitti' && r.info?.summary) s += ` Sonuç: ${r.info.summary}`;
    else if (r?.status === 'hata') s += ` Hata: ${r.error}`;
    lines.push(s);
  }
  return lines.join('\n');
}

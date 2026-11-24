const DATA_URL = 'data/long_march_events.json';
const REFERENCES_URL = 'data/references.json';
const CATALOG_PAGE_SIZE = 36;

let museumData = null;
let referencesData = [];
let selectedPersonId = '';
let martyrFilter = 'all';
let personTypeFilter = 'all';
let personQuery = '';
let catalogModule = 'persons';
let catalogQuery = '';
let catalogEvidence = 'all';
let catalogSourceId = '';
let catalogPageLimit = CATALOG_PAGE_SIZE;
let archiveTab = 'all';
let archiveQuery = '';

document.addEventListener('DOMContentLoaded', initMuseum);

async function initMuseum() {
  try {
    const [res, refRes] = await Promise.all([
      fetch(`${DATA_URL}?v=${Date.now()}`, { cache: 'no-store' }),
      fetch(`${REFERENCES_URL}?v=${Date.now()}`, { cache: 'no-store' }).catch(() => null),
    ]);
    if (!res.ok) throw new Error(`数据加载失败：${res.status}`);
    museumData = await res.json();
    if (refRes && refRes.ok) {
      const refJson = await refRes.json();
      referencesData = refJson.references || [];
    }
    if (!referencesData.length) referencesData = museumData.sources || [];
    selectedPersonId = getDefaultPersonId();
    // 主题入口页 ?person=<id> / ?force=<id> / ?source=<id> 深链支持
    const qs = new URLSearchParams(window.location.search);
    const personParam = qs.get('person');
    const forceParam = qs.get('force');
    const sourceParam = qs.get('source');
    if (personParam && museumData.persons.some(p => p.id === personParam)) selectedPersonId = personParam;
    if (forceParam) {
      const subj = getSubject(forceParam);
      catalogModule = 'events';
      catalogQuery = subj?.shortName || subj?.name || forceParam;
    }
    if (sourceParam && museumData.sources.some(s => s.id === sourceParam)) {
      catalogModule = 'events';
      catalogSourceId = sourceParam;
    }
    applyHeroVisual();
    renderMetrics();
    renderHallNav();
    renderCuratorialLanes();
    renderRouteExhibit();
    renderModuleCatalog();
    renderMartyrWall();
    renderPersonBrowser();
    renderCostLedger();
    renderTurningPoints();
    renderPlaces();
    renderArchive();
    renderMethod();
    renderMemorial();
    bindImageFallbacks();
    bindImageLightbox();
    bindNavHighlight();
    document.getElementById('museum-loading')?.classList.add('hidden');
  } catch (err) {
    console.error(err);
    const loading = document.getElementById('museum-loading');
    if (loading) loading.textContent = err.message || String(err);
  }
}

function renderMetrics() {
  setText('metric-events', museumData.events.length);
  setText('metric-persons', museumData.persons.length);
  setText('metric-martyrs', museumData.persons.filter(p => p.personType === '烈士').length);
  setText('metric-costs', getCostEvents().length);
}

function renderHallNav() {
  const nav = document.getElementById('hall-nav');
  if (!nav) return;
  const halls = [];
  museumData.museum.halls.forEach(hall => {
    halls.push(hall);
    if (hall.id === 'route') halls.push({ id: 'catalog', title: '资料总目录' });
  });
  // 反馈(2026-05-28)：追加「新长征」视角入口
  halls.push({ id: 'new-longmarch', title: '新长征' });
  nav.innerHTML = halls.map(h => `<a href="#${escapeAttr(h.id)}">${escapeHTML(h.title)}</a>`).join('');
}

function renderCuratorialLanes() {
  const box = document.getElementById('curatorial-lanes');
  if (!box) return;
  const lanes = [
    { title: '明线', value: `${museumData.events.length} 条史实`, body: '路线、战役、会议、渡河与会师，把长征写成一条不断转向的行进史。', href: '#route' },
    { title: '人物透镜', value: `${museumData.persons.length} 个档案`, body: '把目光从“部队”收回到“人”：每个名字都有自己的抉择、伤痛与坚持。', href: '#persons' },
    { title: '暗线', value: `${getCostEvents().length} 条代价记录`, body: '后卫牺牲、战斗减员、家属离散与雪山草地，共同构成胜利背后的沉重底色。', href: '#costs' },
    { title: '证据层', value: `${museumData.sources.length} 条来源`, body: '史料出处被完整保留，让纪念不止于叙述，也经得起回看与考证。', href: '#archive' },
  ];
  box.innerHTML = lanes.map(lane => `<a class="lane-card" href="${escapeAttr(lane.href)}">
    <span>${escapeHTML(lane.title)}</span>
    <strong>${escapeHTML(lane.value)}</strong>
    <p>${escapeHTML(lane.body)}</p>
  </a>`).join('');
}

function renderRouteExhibit() {
  const exhibit = getExhibit('ex_route_map');
  const box = document.getElementById('route-exhibit');
  if (!box || !exhibit) return;
  const visual = getVisual('exhibit', exhibit.id);
  box.innerHTML = `
    <p class="eyebrow">red-map</p>
    <h3>${escapeHTML(exhibit.title)}</h3>
    <p>${escapeHTML(exhibit.summary)}</p>
    ${imageFigure(visual, 'panel-image')}
    <div class="tag-row">${exhibit.relatedEventIds.map(id => `<span>${escapeHTML(getEvent(id)?.location?.name || id)}</span>`).join('')}</div>
    <a class="panel-action" href="${escapeAttr(exhibit.actionHref || 'map.html')}">${escapeHTML(exhibit.actionLabel || '打开地图')}</a>`;
}

function renderModuleCatalog() {
  const tabs = document.getElementById('catalog-tabs');
  const search = document.getElementById('catalog-search');
  if (!tabs || !search) return;
  const modules = getCatalogModules();
  tabs.innerHTML = modules.map(module => `<button class="${module.id === catalogModule ? 'active' : ''}" data-catalog-module="${escapeAttr(module.id)}">
    <span>${escapeHTML(module.label)}</span><strong>${escapeHTML(module.count)}</strong>
  </button>`).join('');
  tabs.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    catalogModule = btn.dataset.catalogModule || 'persons';
    catalogPageLimit = CATALOG_PAGE_SIZE;
    if (catalogModule !== 'events') catalogSourceId = '';
    renderModuleCatalog();
  }));
  search.value = catalogQuery;
  search.oninput = () => {
    catalogQuery = search.value.trim();
    catalogPageLimit = CATALOG_PAGE_SIZE;
    renderCatalogContent();
  };
  renderEvidenceFilter();
  renderTopicFilter();
  renderCatalogContent();
  loadVariantGroups();
}

function renderEvidenceFilter() {
  const box = document.getElementById('catalog-evidence');
  if (!box) return;
  // 证据分级仅在事件模块显示
  if (catalogModule !== 'events') { box.innerHTML = ''; return; }
  const opts = [
    { key: 'all', label: '全部证据' },
    { key: 'high', label: '权威史实' },
    { key: 'medium', label: '一手见闻' },
    { key: 'low', label: '线索待证' },
  ];
  box.innerHTML = opts.map(o => `<button class="${catalogEvidence === o.key ? 'active' : ''}" data-evidence="${o.key}">${escapeHTML(o.label)}</button>`).join('');
  box.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    catalogEvidence = btn.dataset.evidence;
    catalogPageLimit = CATALOG_PAGE_SIZE;
    renderEvidenceFilter();
    renderCatalogContent();
  }));
}

// 语义化主题筛选（适配 8 大标准类型 + 4 大分层）
let catalogTopic = 'all';
const TOPIC_FILTERS = [
  { key: 'all', label: '全部主题', match: null },
  { key: 'battle', label: '战斗交锋', match: e => e.type === '战斗' },
  { key: 'decision', label: '战略决策', match: e => e.type === '决策' },
  { key: 'hazard', label: '渡险克难', match: e => e.type === '渡险' },
  { key: 'meeting', label: '会师汇流', match: e => e.type === '会师' },
  { key: 'sacrifice', label: '牺牲代价', match: e => e.type === '牺牲' },
  { key: 'people', label: '民生与民族', match: e => e.type === '民生' },
  { key: 'dashi', label: '逐日行军纪要', match: e => String(e.id || '').startsWith('dashi_') || e.type === '行军' },
  { key: 'hist', label: '史料与传播', match: e => e.type === '史料' || e.layer === 'historiography' || e.layer === 'theme_stat' },
];

function renderTopicFilter() {
  const box = document.getElementById('catalog-topic');
  if (!box) return;
  if (catalogModule !== 'events') { box.innerHTML = ''; return; }
  box.innerHTML = TOPIC_FILTERS.map(t => {
    const n = t.match ? (museumData.events || []).filter(t.match).length : null;
    const label = t.match ? `${t.label} ${n}` : t.label;
    return `<button class="${catalogTopic === t.key ? 'active' : ''}" data-topic="${t.key}">${escapeHTML(label)}</button>`;
  }).join('');
  box.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    catalogTopic = btn.dataset.topic;
    catalogPageLimit = CATALOG_PAGE_SIZE;
    renderTopicFilter();
    renderCatalogContent();
  }));
}

function renderCatalogSourceBanner() {
  const banner = document.getElementById('catalog-source-banner');
  if (!banner) return;
  if (catalogModule !== 'events' || !catalogSourceId) {
    banner.classList.add('hidden');
    banner.innerHTML = '';
    return;
  }
  const src = getSource(catalogSourceId);
  const title = src ? `${src.title}${src.year ? ` (${src.year})` : ''}` : catalogSourceId;
  banner.classList.remove('hidden');
  banner.innerHTML = `<span>正在按来源反查：<strong>${escapeHTML(title)}</strong>${src?.citedDetail ? ` · ${escapeHTML(src.citedDetail)}` : ''}</span><button type="button" id="clear-source-filter">清除来源筛选</button>`;
  document.getElementById('clear-source-filter')?.addEventListener('click', () => {
    catalogSourceId = '';
    catalogPageLimit = CATALOG_PAGE_SIZE;
    renderCatalogContent();
  });
}

function renderCatalogContent() {
  const stats = document.getElementById('catalog-stats');
  const grid = document.getElementById('catalog-grid');
  const pager = document.getElementById('catalog-pager');
  if (!stats || !grid) return;
  renderCatalogSourceBanner();
  const items = getCatalogItems(catalogModule);
  const shown = filterCatalogItems(items);
  const visible = shown.slice(0, catalogPageLimit);
  stats.innerHTML = catalogStats(items, shown);
  grid.innerHTML = visible.length ? visible.map(item => catalogCard(item)).join('') : `<div class="catalog-empty">没有匹配的资料模块</div>`;
  if (pager) {
    const remaining = shown.length - visible.length;
    if (remaining > 0) {
      pager.innerHTML = `<span>已显示 ${visible.length} / ${shown.length} 项</span><button type="button" id="catalog-load-more">加载更多（剩余 ${remaining}）</button><button type="button" id="catalog-show-all">全部展开</button>`;
      document.getElementById('catalog-load-more')?.addEventListener('click', () => {
        catalogPageLimit += CATALOG_PAGE_SIZE;
        renderCatalogContent();
      });
      document.getElementById('catalog-show-all')?.addEventListener('click', () => {
        catalogPageLimit = shown.length;
        renderCatalogContent();
      });
    } else {
      pager.innerHTML = shown.length > CATALOG_PAGE_SIZE ? `<span>已展示全部 ${shown.length} 项</span>` : '';
    }
  }
  bindCatalogCards();
  bindVariantBadges(grid);
  bindImageFallbacks();
}

function getCatalogModules() {
  return [
    { id: 'persons', label: '人物', count: museumData.persons.length },
    { id: 'places', label: '地点', count: getPlaceModules().length },
    { id: 'events', label: '事件', count: museumData.events.length },
    { id: 'forces', label: '部队', count: museumData.subjects.filter(s => s.type === 'force').length },
  ];
}

function getCatalogItems(moduleId) {
  if (moduleId === 'places') return getPlaceModules();
  if (moduleId === 'events') return getEventModules();
  if (moduleId === 'forces') return getForceModules();
  return getPersonModules();
}

function getPersonModules() {
  return museumData.persons.map(person => {
    const subject = getSubject(person.forceId);
    const links = getPersonEvents(person.id);
    return {
      kind: 'persons',
      id: person.id,
      title: person.name,
      subtitle: person.personType || '人物',
      body: person.summary || '',
      accent: subject?.color || '#bd2427',
      chips: [subject?.shortName, person.hometown, personLifespan(person), `${links.length} 个关联事件`].filter(Boolean),
      tags: person.themeTags || [],
      searchText: [person.name, person.nameEn, person.personType, person.hometown, subject?.name, subject?.shortName, person.summary, ...(person.themeTags || [])].join(' '),
      visual: getVisual('person', person.id),
      person,
    };
  });
}

function getPlaceModules() {
  const places = new Map();
  museumData.events.forEach(event => {
    const name = event.location?.name;
    if (!name) return;
    if (!places.has(name)) {
      places.set(name, { kind: 'places', id: name, title: name, events: [], forceIds: new Set(), types: new Set(), coordinates: event.location?.coordinates || [] });
    }
    const place = places.get(name);
    place.events.push(event);
    if (event.forceId) place.forceIds.add(event.forceId);
    if (event.type) place.types.add(event.type);
  });
  return [...places.values()].map(place => {
    const events = place.events.sort(compareEvents);
    const subjects = [...place.forceIds].map(id => getSubject(id)?.shortName || id);
    const titles = events.slice(0, 3).map(event => event.title);
    place.body = titles.join(' / ');
    place.chips = [`${events.length} 个事件`, dateRange(events), ...subjects.slice(0, 2)].filter(Boolean);
    place.tags = [...place.types].slice(0, 4);
    place.searchText = [place.title, place.body, ...subjects, ...place.tags, ...events.map(event => event.title)].join(' ');
    return place;
  }).sort((a, b) => compareEvents(a.events[0], b.events[0]) || a.title.localeCompare(b.title, 'zh-CN'));
}

function getEventModules() {
  return [...museumData.events].sort(compareEvents).map(event => {
    const subject = getSubject(event.forceId);
    return {
      kind: 'events',
      id: event.id,
      title: event.title,
      subtitle: event.type || '事件',
      body: event.description || '',
      accent: subject?.color || '#bd2427',
      chips: [formatDate(event.date), event.location?.name, subject?.shortName, event.certainty].filter(Boolean),
      tags: [event.type, ...(event.participants || []).slice(0, 3)].filter(Boolean),
      searchText: [event.title, event.description, event.type, event.location?.name, subject?.name, subject?.shortName, ...(event.participants || [])].join(' '),
      event,
    };
  });
}

function getForceModules() {
  return museumData.subjects.filter(subject => subject.type === 'force').map(subject => {
    const events = museumData.events.filter(event => event.forceId === subject.id).sort(compareEvents);
    const persons = museumData.persons.filter(person => person.forceId === subject.id);
    const subUnits = splitList(subject.subUnits);
    return {
      kind: 'forces',
      id: subject.id,
      title: subject.shortName || subject.name,
      subtitle: subject.isEnemy ? '对手态势' : '部队',
      body: subject.description || '',
      accent: subject.color || '#bd2427',
      chips: [`${events.length} 个事件`, `${persons.length} 个人物`, dateRange(events)].filter(Boolean),
      tags: subUnits.slice(0, 6),
      searchText: [subject.name, subject.shortName, subject.leader, subject.description, ...subUnits, ...events.map(event => event.title), ...persons.map(person => person.name)].join(' '),
      subject,
      events,
      persons,
    };
  }).sort((a, b) => Number(a.subject.sort || 999) - Number(b.subject.sort || 999));
}

function filterCatalogItems(items) {
  const query = normalizeCatalogQuery(catalogQuery);
  let out = items;
  if (catalogModule === 'events' && catalogSourceId) {
    out = out.filter(item => item.event && Array.isArray(item.event.sourceIds) && item.event.sourceIds.includes(catalogSourceId));
  }
  if (catalogModule === 'events' && catalogEvidence && catalogEvidence !== 'all') {
    out = out.filter(item => item.event && String(item.event.certainty).toLowerCase() === catalogEvidence);
  }
  if (catalogModule === 'events' && catalogTopic && catalogTopic !== 'all') {
    const t = TOPIC_FILTERS.find(x => x.key === catalogTopic);
    if (t && t.match) {
      out = out.filter(item => item.event && t.match(item.event));
    }
  }
  if (!query) return out;
  return out.filter(item => normalizeCatalogQuery(item.searchText).includes(query));
}

function catalogStats(items, shown) {
  const module = getCatalogModules().find(item => item.id === catalogModule);
  const labels = {
    persons: ['人物总数', '当前显示', '已关联事件'],
    places: ['地点总数', '当前显示', '覆盖事件'],
    events: ['事件总数', '当前显示', '涉及部队'],
    forces: ['部队总数', '当前显示', '关联人物'],
  };
  const label = labels[catalogModule] || labels.persons;
  const thirdValue = catalogModule === 'persons'
    ? museumData.personEvents.length
    : catalogModule === 'places'
      ? shown.reduce((sum, item) => sum + item.events.length, 0)
      : catalogModule === 'events'
        ? new Set(shown.map(item => item.event.forceId).filter(Boolean)).size
        : shown.reduce((sum, item) => sum + item.persons.length, 0);
  return [
    [label[0], items.length],
    [label[1], shown.length],
    [label[2], thirdValue],
  ].map(([name, value]) => `<span><strong>${escapeHTML(value)}</strong>${escapeHTML(name)}</span>`).join('');
}

function catalogCard(item) {
  if (item.kind === 'events') return eventCatalogCard(item);
  if (item.kind === 'forces') return forceCatalogCard(item);
  if (item.kind === 'places') return placeCatalogCard(item);
  return personCatalogCard(item);
}

function personCatalogCard(item) {
  const visual = item.visual ? imageFigure(item.visual, 'module-portrait') : '';
  return `<article class="catalog-card" tabindex="0" data-catalog-person="${escapeAttr(item.id)}" style="--accent:${escapeAttr(item.accent)}">
    ${visual}
    <div class="module-kicker"><span>${escapeHTML(item.subtitle)}</span><strong>${escapeHTML(item.chips[item.chips.length - 1] || '')}</strong></div>
    <h3>${escapeHTML(item.title)}</h3>
    <p>${escapeHTML(item.body)}</p>
    ${moduleMeta(item.chips.slice(0, 3))}
    ${moduleTags(item.tags)}
  </article>`;
}

function placeCatalogCard(item) {
  const firstEvent = item.events[0];
  return `<article class="catalog-card" style="--accent:#365f88">
    <div class="module-kicker"><span>地点</span><strong>${escapeHTML(item.chips[0] || '')}</strong></div>
    <h3>${escapeHTML(item.title)}</h3>
    <p>${escapeHTML(item.body)}</p>
    ${moduleMeta(item.chips.slice(1))}
    ${moduleTags(item.tags)}
    ${firstEvent ? `<a class="module-action" href="map.html#event=${encodeURIComponent(firstEvent.id)}">地图定位</a>` : ''}
  </article>`;
}

function extractEventCitation(event) {
  const notes = String(event?.notes || '').trim();
  if (!notes) return '';
  const m = notes.match(/据《[^》]+》[^；。\n]{0,44}/);
  if (m) return m[0];
  const m2 = notes.match(/《红军长征记》[^；。\n]{0,36}/);
  return m2 ? m2[0] : '';
}

function datePrecisionBadge(prec) {
  const labels = { month: '仅知月份', range: '时间区间', approx: '约略时间' };
  const label = labels[String(prec || '').toLowerCase()];
  return label ? `<span class="evidence-badge ev-approx">${escapeHTML(label)}</span>` : '';
}

function layerBadge(layer) {
  const labels = { spark_march: '延伸星火', theme_stat: '专题/统计', historiography: '文献传播史' };
  const label = labels[layer];
  return label ? `<span class="layer-badge">${escapeHTML(label)}</span>` : '';
}

function eventProvenanceHtml(event) {
  const sids = Array.isArray(event?.sourceIds) ? event.sourceIds : [];
  if (!sids.length) return '';
  const hint = extractEventCitation(event);
  const pills = sids.slice(0, 3).map(id => {
    const src = getSource(id);
    const label = src ? `${src.mediaType === '专著' ? '书·' : src.sourceType === 'game_text' ? '线索·' : ''}${src.title}` : id;
    return `<button type="button" class="card-source-pill" data-filter-source="${escapeAttr(id)}" title="点击按此来源反查全部事件">${escapeHTML(label.slice(0, 26))}${label.length > 26 ? '…' : ''}</button>`;
  }).join('');
  return `<div class="card-provenance">
    ${hint ? `<div class="card-cite-hint">${escapeHTML(hint)}</div>` : ''}
    <div class="card-source-pills">${pills}</div>
  </div>`;
}

function eventCatalogCard(item) {
  const ev = item.event;
  return `<article class="catalog-card" style="--accent:${escapeAttr(item.accent)}">
    <div class="module-kicker"><span>${escapeHTML(item.subtitle)}</span><strong>${escapeHTML(formatDate(ev.date))}</strong></div>
    <h3>${escapeHTML(item.title)}</h3>
    <p>${escapeHTML(item.body)}</p>
    ${moduleMeta(item.chips.slice(1, 3))}
    <div class="card-badge-row">
      ${evidenceBadge(ev.certainty)}
      ${datePrecisionBadge(ev.datePrecision)}
      ${layerBadge(ev.layer)}
      ${variantBadge(item.id)}
    </div>
    ${eventProvenanceHtml(ev)}
    ${moduleTags(item.tags)}
    <a class="module-action" href="map.html#event=${encodeURIComponent(item.id)}">地图查看</a>
  </article>`;
}

function forceCatalogCard(item) {
  return `<article class="catalog-card force-card" style="--accent:${escapeAttr(item.accent)}">
    <div class="module-kicker"><span>${escapeHTML(item.subtitle)}</span><strong>${escapeHTML(item.chips[0] || '')}</strong></div>
    <h3>${escapeHTML(item.title)}</h3>
    <p>${escapeHTML(item.body)}</p>
    ${moduleMeta([item.subject.leader, ...item.chips.slice(1)].filter(Boolean))}
    ${moduleTags(item.tags)}
    <button class="module-action" type="button" data-catalog-force="${escapeAttr(item.id)}">相关事件</button>
  </article>`;
}

// 证据分层徽章：把英文 certainty 翻译成观众能懂的中文语义。
// 只做呈现，不改变任何数据或史料优先级判断。
const EVIDENCE_META = {
  high:       { label: '权威史实', cls: 'ev-high',       title: '有权威来源支撑的史实' },
  medium:     { label: '一手见闻', cls: 'ev-medium',     title: '亲历者/一手记述，细节存异' },
  low:        { label: '线索待证', cls: 'ev-low',        title: '游戏文本等候选线索，尚无独立权威来源' },
  month:      { label: '仅知月份', cls: 'ev-approx',     title: '日期只能确定到月份' },
  range:      { label: '时间区间', cls: 'ev-approx',     title: '事件发生在一个时间段内' },
  approximate:{ label: '约略时间', cls: 'ev-approx',     title: '时间为约略值' },
  '口径有差异': { label: '口径有差异', cls: 'ev-approx', title: '不同来源记载口径不同' },
};
function evidenceBadge(certainty) {
  const key = String(certainty || '').toLowerCase();
  const meta = EVIDENCE_META[key] || { label: certainty || '未标注', cls: 'ev-unknown', title: '版权/证据状态未标注' };
  return `<span class="evidence-badge ${meta.cls}" title="${escapeAttr(meta.title)}">${escapeHTML(meta.label)}</span>`;
}

// 口径差异：同一史实在不同来源里记载不同（人数/里程/战果等）。
// 这些差异被有意保留，不强行合并 —— 观众需要看到"有几种说法、各自依据什么"。
let variantGroups = [];
let variantIndex = new Map();

function loadVariantGroups() {
  if (variantGroups.length) return;
  fetch('data/variant_groups.json', { cache: 'no-store' })
    .then(r => r.ok ? r.json() : { groups: [] })
    .then(data => {
      variantGroups = data.groups || [];
      variantIndex = new Map();
      variantGroups.forEach(g => (g.variants || []).forEach(v => variantIndex.set(v.eventId, g)));
      renderCatalogContent();
    })
    .catch(() => { variantGroups = []; });
}

function variantBadge(eventId) {
  const g = variantIndex.get(eventId);
  if (!g) return '';
  const n = g.variants.length;
  const certs = (g.certaintyKinds || []).join(' / ');
  return `<button type="button" class="variant-badge" data-variant-group="${escapeAttr(g.key)}"
    title="同一史实存在 ${n} 种来源记载：${escapeAttr(certs)}">${n} 种记载</button>`;
}

function variantPanelHtml(groupKey) {
  const g = variantGroups.find(x => x.key === groupKey);
  if (!g) return '';
  const rows = g.variants.map(v => {
    const ev = (museumData.events || []).find(e => e.id === v.eventId);
    const srcs = (v.sourceIds || []).map(s => {
      const src = (museumData.sources || []).find(x => x.id === s);
      return src ? `<a href="${escapeAttr(src.url || '#')}" target="_blank" rel="noopener">${escapeHTML(src.title || s)}</a>` : escapeHTML(s);
    }).join(' · ');
    return `<li class="variant-item">
      <div class="variant-head">${evidenceBadge(v.certainty)}<strong>${escapeHTML(v.label)}</strong></div>
      <h5>${escapeHTML(v.title)}</h5>
      <p>${escapeHTML(v.summary || '')}</p>
      ${ev ? `<a class="variant-link" href="map.html#event=${encodeURIComponent(v.eventId)}">在地图中查看</a>` : ''}
      ${srcs ? `<div class="variant-sources">${srcs}</div>` : ''}
    </li>`;
  }).join('');
  return `<div class="variant-panel" id="variant-panel" data-variant-panel="${escapeAttr(g.key)}">
    <div class="variant-panel-head">
      <strong>同一史实的 ${g.variants.length} 种来源记载</strong>
      <button type="button" class="variant-close" data-variant-close>收起</button>
    </div>
    <p class="variant-note">各来源记载在人数、里程或战果等细节上存在差异。本馆不做强行合并，以保留原始来源的独立说法。</p>
    <ul class="variant-list">${rows}</ul>
  </div>`;
}

function bindVariantBadges(root) {
  root.querySelectorAll('[data-variant-group]').forEach(btn => {
    btn.addEventListener('click', ev => {
      ev.preventDefault();
      ev.stopPropagation();
      const key = btn.getAttribute('data-variant-group');
      const existing = document.querySelector(`[data-variant-panel="${CSS.escape(key)}"]`);
      if (existing) { existing.remove(); return; }
      document.querySelectorAll('[data-variant-panel]').forEach(p => p.remove());
      const holder = btn.closest('.catalog-card') || btn.parentElement;
      if (holder) holder.insertAdjacentHTML('beforeend', variantPanelHtml(key));
      document.querySelectorAll('[data-variant-close]').forEach(c => {
        c.addEventListener('click', () => document.querySelectorAll('[data-variant-panel]').forEach(p => p.remove()));
      });
    });
  });
}

function moduleMeta(values) {
  const shown = values.filter(Boolean).slice(0, 4);
  return shown.length ? `<div class="module-meta">${shown.map(value => `<span>${escapeHTML(value)}</span>`).join('')}</div>` : '';
}

function moduleTags(values) {
  const shown = values.filter(Boolean).slice(0, 6);
  return shown.length ? `<div class="tag-row">${shown.map(tag => `<span>${escapeHTML(tag)}</span>`).join('')}</div>` : '';
}

function bindCatalogCards() {
  document.querySelectorAll('[data-catalog-person]').forEach(card => {
    const jump = () => jumpToPerson(card.dataset.catalogPerson);
    card.addEventListener('click', jump);
    card.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        jump();
      }
    });
  });
  document.querySelectorAll('[data-catalog-force]').forEach(button => {
    button.addEventListener('click', event => {
      event.stopPropagation();
      const subject = getSubject(button.dataset.catalogForce);
      catalogModule = 'events';
      catalogSourceId = '';
      catalogPageLimit = CATALOG_PAGE_SIZE;
      catalogQuery = subject?.shortName || subject?.name || button.dataset.catalogForce || '';
      renderModuleCatalog();
      document.getElementById('catalog')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  document.querySelectorAll('[data-filter-source]').forEach(button => {
    button.addEventListener('click', event => {
      event.stopPropagation();
      jumpToSourceEvents(button.dataset.filterSource);
    });
  });
}

function jumpToSourceEvents(sourceId) {
  if (!sourceId) return;
  catalogModule = 'events';
  catalogSourceId = sourceId;
  catalogEvidence = 'all';
  catalogTopic = 'all';
  catalogQuery = '';
  catalogPageLimit = CATALOG_PAGE_SIZE;
  renderModuleCatalog();
  document.getElementById('catalog')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderMartyrWall() {
  const filters = document.getElementById('martyr-filters');
  const wall = document.getElementById('portrait-wall');
  if (!filters || !wall) return;
  const martyrs = museumData.persons.filter(p => p.personType === '烈士');
  const forceIds = ['all', ...new Set(martyrs.map(p => p.forceId).filter(Boolean))];
  filters.innerHTML = forceIds.map(id => `<button class="${id === martyrFilter ? 'active' : ''}" data-filter="${escapeAttr(id)}">${escapeHTML(id === 'all' ? '全部' : getSubject(id)?.shortName || id)}</button>`).join('');
  filters.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => { martyrFilter = btn.dataset.filter; renderMartyrWall(); bindImageFallbacks(); }));
  const shown = martyrFilter === 'all' ? martyrs : martyrs.filter(p => p.forceId === martyrFilter);
  wall.innerHTML = shown.map(person => portraitCard(person)).join('');
  wall.querySelectorAll('[data-person-jump]').forEach(card => card.addEventListener('click', () => {
    jumpToPerson(card.dataset.personJump);
  }));
}

function portraitCard(person) {
  const visual = getVisual('person', person.id);
  return `<article class="portrait-card" data-person-jump="${escapeAttr(person.id)}">
    ${visual ? imageFigure(visual, 'portrait-image') : `<div class="portrait-face">${escapeHTML(person.name.slice(0, 1))}</div>`}
    <h3>${escapeHTML(person.name)}</h3>
    <p>${escapeHTML(person.summary)}</p>
    <div class="tag-row">${(person.themeTags || []).slice(0, 4).map(tag => `<span>${escapeHTML(tag)}</span>`).join('')}</div>
  </article>`;
}

function renderPersonBrowser() {
  const list = document.getElementById('person-list');
  if (!list) return;
  const searchInput = document.getElementById('person-search');
  if (searchInput && !searchInput.dataset.bound) {
    searchInput.dataset.bound = '1';
    searchInput.addEventListener('input', () => {
      personQuery = searchInput.value.trim();
      renderPersonBrowser();
      bindImageFallbacks();
    });
  }
  renderPersonTypeFilters();
  const persons = getFilteredPersons();
  if (persons.length && !persons.some(person => person.id === selectedPersonId)) selectedPersonId = persons[0].id;
  list.innerHTML = persons.length
    ? persons.map(person => `<button class="${person.id === selectedPersonId ? 'active' : ''}" data-person-id="${escapeAttr(person.id)}">
        <span>${escapeHTML(person.name)}</span><small>${escapeHTML(person.personType || '人物')}</small>
      </button>`).join('')
    : `<div class="catalog-empty">无匹配人物</div>`;
  list.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => { selectedPersonId = btn.dataset.personId; renderPersonBrowser(); renderPersonDetail(); bindImageFallbacks(); }));
  renderPersonDetail();
}

function renderPersonTypeFilters() {
  const box = document.getElementById('person-type-filters');
  if (!box) return;
  const types = ['all', ...new Set(museumData.persons.map(p => p.personType || '人物'))];
  box.innerHTML = types.map(type => `<button class="${type === personTypeFilter ? 'active' : ''}" data-person-type="${escapeAttr(type)}">${escapeHTML(type === 'all' ? '全部角色' : type)}</button>`).join('');
  box.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
    personTypeFilter = btn.dataset.personType;
    renderPersonBrowser();
    bindImageFallbacks();
  }));
}

function renderPersonDetail() {
  const detail = document.getElementById('person-detail');
  const person = getPerson(selectedPersonId);
  if (!detail || !person) return;
  const links = getPersonEvents(person.id)
    .map(rel => ({ rel, event: getEvent(rel.eventId) }))
    .filter(item => item.event)
    .sort((a, b) => compareEvents(a.event, b.event) || Number(a.rel.sort || 0) - Number(b.rel.sort || 0));
  const visual = getVisual('person', person.id);
  const subject = getSubject(person.forceId);
  const sourceItems = (person.sourceIds || []).map(id => getSource(id)).filter(Boolean);
  const meta = [
    ['身份', person.personType || '人物'],
    ['生卒', personLifespan(person)],
    ['籍贯', person.hometown],
    ['所属', subject?.shortName || subject?.name],
    ['关联事件', `${links.length} 个`],
    ['考证层级', EVIDENCE_META[String(person.certainty || 'medium').toLowerCase()]?.label || '一手见闻'],
  ].filter(([, value]) => value);
  detail.innerHTML = `
    <div class="person-head">
      ${visual ? imageFigure(visual, 'person-visual') : `<div class="person-seal">${escapeHTML(person.name.slice(0, 1))}</div>`}
      <div>
        <p class="eyebrow">${escapeHTML(person.personType || '人物')} · ${escapeHTML(subject?.shortName || '')}</p>
        <h3>${escapeHTML(person.name)}</h3>
        <p>${escapeHTML(person.summary)}</p>
      </div>
    </div>
    <div class="person-meta-grid">${meta.map(([label, value]) => `<div><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong></div>`).join('')}</div>
    <div class="tag-row">${(person.themeTags || []).map(tag => `<span>${escapeHTML(tag)}</span>`).join('')}</div>
    ${sourceItems.length ? `<div class="person-source-list"><h4>资料来源</h4>${sourceItems.map(source => `<a href="${escapeAttr(source.url || '#')}" target="_blank" rel="noopener noreferrer">${escapeHTML(source.title)}</a>`).join('')}</div>` : ''}
    <div class="timeline">${links.map(item => timelineItem(item.event, item.rel)).join('')}</div>`;
}

function timelineItem(event, rel) {
  return `<div class="timeline-item">
    <div class="timeline-date">${escapeHTML(formatDate(event.date))}</div>
    <div>
      <h4>${escapeHTML(event.title)} ${evidenceBadge(event.certainty)}</h4>
      <p>${escapeHTML(rel.note || event.description || '')}</p>
      <a href="map.html#event=${encodeURIComponent(event.id)}">在路线地图中查看</a>
    </div>
  </div>`;
}

function renderCostLedger() {
  const grid = document.getElementById('cost-grid');
  const ledger = document.getElementById('cost-ledger');
  if (!grid || !ledger) return;
  const costEvents = getCostEvents();
  const martyrCount = museumData.persons.filter(p => p.personType === '烈士').length;
  const explicitLosses = museumData.events.reduce((sum, event) => sum + Number(event.metrics?.redLosses || 0), 0);
  const lenses = [
    { label: '牺牲档案', value: martyrCount, body: '把牺牲从数字还原为姓名，让断后的身影与未竟的人生重新被看见。' },
    { label: '代价记录', value: costEvents.length, body: '这些记录呈现了失血、离散、饥寒与险阻，是长征必须承担的真实重量。' },
    { label: '可量化损失', value: explicitLosses ? `${formatNumber(explicitLosses)}+` : '待补', body: '只统计已经进入结构化字段的损失口径，避免把估算写成定论。' },
    { label: '待考证铭牌', value: museumData.persons.filter(p => !getVisual('person', p.id)).length, body: '没有可靠公开肖像时保留铭牌，让缺席本身成为历史叙述的一部分。' },
  ];
  grid.innerHTML = lenses.map(item => `<article class="cost-stat">
    <span>${escapeHTML(item.label)}</span>
    <strong>${escapeHTML(item.value)}</strong>
    <p>${escapeHTML(item.body)}</p>
  </article>`).join('');
  ledger.innerHTML = costEvents.slice(0, 12).map(event => `<article class="ledger-row">
    <div class="ledger-date">${escapeHTML(formatDate(event.date))}</div>
    <div>
      <h3>${escapeHTML(event.title)}</h3>
      <p>${escapeHTML(event.description)}</p>
      <div class="tile-meta"><span>${escapeHTML(event.type)}</span><span>${escapeHTML(getSubject(event.forceId)?.shortName || '')}</span>${event.metrics?.redLosses ? `<span>损失 ${escapeHTML(formatNumber(event.metrics.redLosses))}</span>` : ''}</div>
    </div>
  </article>`).join('');
}

function renderTurningPoints() {
  const box = document.getElementById('turning-events');
  const exhibit = getExhibit('ex_turning_points');
  if (!box || !exhibit) return;
  box.innerHTML = exhibit.relatedEventIds.map(id => eventTile(getEvent(id))).join('');
}

function renderPlaces() {
  const box = document.getElementById('place-grid');
  if (!box) return;
  const memoryKeywords = ['纪念馆', '纪念碑', '陵园', '旧址', '会址', '将台堡', '会宁', '于都', '遵义', '泸定', '吴起', '哈达铺', '腊子口'];
  const places = getPlaceModules()
    .map(place => ({
      ...place,
      firstEvent: place.events[0],
      score: place.events.length * 10 + place.events.filter(e => Number(e.importance || 0) >= 4).length * 6 + (memoryKeywords.some(k => place.title.includes(k)) ? 12 : 0),
    }))
    .sort((a, b) => b.score - a.score || compareEvents(a.firstEvent, b.firstEvent));
  box.innerHTML = places.slice(0, 24).map(place => placeTile(place.firstEvent, place)).join('');
}

function renderArchive() {
  renderArchiveSummary();
  renderArchiveControls();
  renderReferenceList();
  const box = document.getElementById('archive-grid');
  if (!box) return;
  box.innerHTML = museumData.museum.artifacts.map(artifact => `<article class="archive-tile">
    <h3>${escapeHTML(artifact.title)}</h3>
    <p>${escapeHTML(artifact.summary)}</p>
    <div class="tile-meta"><span>${escapeHTML(artifact.artifactType || 'archive')}</span>${evidenceBadge(artifact.certainty || 'medium')}</div>
  </article>`).join('');
}

function renderArchiveSummary() {
  const box = document.getElementById('archive-summary');
  if (!box) return;
  const events = museumData.events || [];
  const total = Math.max(1, events.length);
  const hi = events.filter(e => e.certainty === 'high').length;
  const med = events.filter(e => e.certainty === 'medium').length;
  const low = events.filter(e => e.certainty === 'low').length;
  const books = referencesData.filter(r => r.mediaType === '专著' || r.mediaType === '档案').length;
  const webs = referencesData.filter(r => r.mediaType === '网页').length;
  box.innerHTML = `
    <div class="archive-kpi-row">
      <div class="archive-kpi"><strong>${referencesData.length}</strong><span>登记文献与来源总数</span></div>
      <div class="archive-kpi"><strong>${books}</strong><span>核心专著与原刊文献</span></div>
      <div class="archive-kpi"><strong>${webs}</strong><span>权威党史军史官网</span></div>
      <div class="archive-kpi"><strong>${Math.round(((hi + med) / total) * 100)}%</strong><span>权威+一手核实占比（${hi + med}/${events.length}）</span></div>
    </div>
    <div class="evidence-bar-wrap">
      <div class="evidence-bar" aria-label="事件证据分层分布">
        <div class="evidence-bar-high" style="width:${((hi / total) * 100).toFixed(1)}%" title="权威史实 ${hi} 条"></div>
        <div class="evidence-bar-med" style="width:${((med / total) * 100).toFixed(1)}%" title="一手见闻 ${med} 条"></div>
        <div class="evidence-bar-low" style="width:${((low / total) * 100).toFixed(1)}%" title="线索待证 ${low} 条"></div>
      </div>
      <div class="evidence-bar-legend">
        <span>🟢 权威史实 ${hi} 条 · 🔵 一手见闻 ${med} 条 · 🟠 线索待证 ${low} 条</span>
        <a class="ref-ext-link" href="REFERENCES.md" target="_blank" rel="noopener">查看完整 GB/T 7714 参考书目文档 ↗</a>
      </div>
    </div>`;
}

function renderArchiveControls() {
  const tabs = document.getElementById('archive-tabs');
  const search = document.getElementById('archive-search');
  if (tabs) {
    const booksCnt = referencesData.filter(r => r.mediaType === '专著' || r.mediaType === '档案').length;
    const websCnt = referencesData.filter(r => r.mediaType === '网页').length;
    const clueCnt = referencesData.filter(r => r.sourceType === 'game_text' || r.mediaType === '数据库').length;
    const opts = [
      { key: 'all', label: `全部来源 (${referencesData.length})` },
      { key: 'book', label: `核心专著 (${booksCnt})` },
      { key: 'web', label: `权威官网 (${websCnt})` },
      { key: 'clue', label: `候选线索 (${clueCnt})` },
    ];
    tabs.innerHTML = opts.map(o => `<button type="button" class="${archiveTab === o.key ? 'active' : ''}" data-archive-tab="${o.key}">${escapeHTML(o.label)}</button>`).join('');
    tabs.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {
      archiveTab = btn.dataset.archiveTab || 'all';
      renderArchiveControls();
      renderReferenceList();
    }));
  }
  if (search && !search.dataset.bound) {
    search.dataset.bound = '1';
    search.addEventListener('input', () => {
      archiveQuery = search.value.trim();
      renderReferenceList();
    });
  }
}

function renderReferenceList() {
  const box = document.getElementById('reference-list');
  if (!box) return;
  const q = normalizeCatalogQuery(archiveQuery);
  const eventCountBySrc = new Map();
  (museumData.events || []).forEach(e => (e.sourceIds || []).forEach(sid => {
    eventCountBySrc.set(sid, (eventCountBySrc.get(sid) || 0) + 1);
  }));
  let list = [...referencesData];
  if (archiveTab === 'book') list = list.filter(r => r.mediaType === '专著' || r.mediaType === '档案');
  else if (archiveTab === 'web') list = list.filter(r => r.mediaType === '网页');
  else if (archiveTab === 'clue') list = list.filter(r => r.sourceType === 'game_text' || r.mediaType === '数据库');
  if (q) {
    list = list.filter(r => normalizeCatalogQuery([r.title, r.author, r.publisher, r.citedDetail, r.note, r.year].join(' ')).includes(q));
  }
  list.sort((a, b) => (eventCountBySrc.get(b.id) || 0) - (eventCountBySrc.get(a.id) || 0) || Number(b.usageCount || 0) - Number(a.usageCount || 0));
  if (!list.length) {
    box.innerHTML = `<div class="catalog-empty">没有匹配的参考书目</div>`;
    return;
  }
  box.innerHTML = list.map(r => {
    const evCnt = eventCountBySrc.get(r.id) || 0;
    const cls = r.mediaType === '专著' ? 'ref-book' : r.sourceType === 'game_text' ? 'ref-clue' : '';
    const kindLabel = r.mediaType === '专著' ? '专著 / 原始文献' : r.sourceType === 'game_text' ? '候选线索数据库' : '权威机构网页';
    const metaBits = [r.author, r.publisher, r.year, r.edition].filter(Boolean).join(' · ');
    const isHttp = r.url && /^https?:\/\//.test(r.url);
    return `<article class="ref-card ${cls}">
      <div class="ref-card-head"><span>${escapeHTML(kindLabel)}</span><strong>引用 ${evCnt} 条事件</strong></div>
      <h4>${escapeHTML(r.title)}</h4>
      ${metaBits ? `<div class="ref-card-meta">${escapeHTML(metaBits)}</div>` : ''}
      ${r.citedDetail ? `<div class="ref-card-cited">具体引用：${escapeHTML(r.citedDetail)}</div>` : ''}
      ${r.note ? `<div class="ref-card-meta">${escapeHTML(r.note)}</div>` : ''}
      <div class="ref-card-actions">
        ${evCnt ? `<button type="button" class="ref-btn" data-ref-events="${escapeAttr(r.id)}">反查 ${evCnt} 条关联事件</button>` : ''}
        ${isHttp ? `<a class="ref-ext-link" href="${escapeAttr(r.url)}" target="_blank" rel="noopener noreferrer">原文链接 ↗</a>` : ''}
      </div>
    </article>`;
  }).join('');
  box.querySelectorAll('[data-ref-events]').forEach(btn => {
    btn.addEventListener('click', () => jumpToSourceEvents(btn.dataset.refEvents));
  });
}

function renderMethod() {
  const box = document.getElementById('method-grid');
  if (!box) return;
  const steps = [
    ['研究材料', '事件、人物、地点、来源先进入表格，保留口径和可信度。'],
    ['证据分层', '卡片上的徽章标明依据层级：绿色「权威史实」有权威来源；蓝色「一手见闻」是亲历者记述、细节或有出入；橙色「线索待证」尚无独立权威来源，仅作线索保留。'],
    ['策展文本', '把史实材料改写为展板标题、导言、图注和人物经验层。'],
    ['叙事结构', '分为路线明线、人物透镜、牺牲暗线、地点记忆和资料层。'],
    ['视觉语言', '地图是材料，肖像是证据，铭牌显示资料缺失，不做无依据复原。'],
    ['原型实现', '先固定路线展板和人物页，再扩展到英烈墙与代价台账。'],
    ['测试复盘', '每次生成 JSON 后校验来源、引用、语法和浏览器渲染。'],
  ];
  box.innerHTML = steps.map((step, idx) => `<article class="method-step">
    <span>${String(idx + 1).padStart(2, '0')}</span>
    <h3>${escapeHTML(step[0])}</h3>
    <p>${escapeHTML(step[1])}</p>
  </article>`).join('');
}

function renderMemorial() {
  const box = document.getElementById('memorial-panel');
  const exhibit = getExhibit('ex_memorial_path');
  if (!box || !exhibit) return;
  const visual = getVisual('exhibit', exhibit.id);
  box.innerHTML = `<h3>${escapeHTML(exhibit.title)}</h3><p>${escapeHTML(exhibit.summary)}</p>${imageFigure(visual, 'panel-image')}<div class="tag-row"><span>路线</span><span>英烈</span><span>人物</span><span>地点</span><span>档案</span></div><a class="panel-action" href="#top">${escapeHTML(exhibit.actionLabel || '返回')}</a>`;
}

function eventTile(event) {
  if (!event) return '';
  const visual = getVisual('event', event.id);
  return `<article class="event-tile">${imageFigure(visual, 'tile-image')}<h3>${escapeHTML(event.title)}</h3><p>${escapeHTML(event.description)}</p><div class="tile-meta"><span>${escapeHTML(event.date)}</span><span>${escapeHTML(event.type)}</span><span>${escapeHTML(getSubject(event.forceId)?.shortName || '')}</span>${evidenceBadge(event.certainty)}</div></article>`;
}

function placeTile(event, place) {
  if (!event || !place) return '';
  const visual = getVisual('event', event.id);
  return `<article class="place-tile">${imageFigure(visual, 'tile-image')}<h3>${escapeHTML(place.title)}</h3><p>${escapeHTML(place.body)}</p><div class="tile-meta"><span>${escapeHTML(place.chips?.[0] || '')}</span><span>${escapeHTML(place.chips?.[1] || '')}</span></div></article>`;
}

function applyHeroVisual() {
  const visual = getVisual('hero', 'museum');
  if (!visual?.imageUrl) return;
  const imageUrl = new URL(visual.imageUrl, window.location.href).href;
  document.documentElement.style.setProperty('--museum-hero-image', `url("${cssUrl(imageUrl)}")`);
}

function imageFigure(visual, className = 'museum-image') {
  if (!visual?.imageUrl) return '';
  const title = visual.title || visual.alt || '图片资料';
  const eager = className === 'panel-image' || className === 'person-visual';
  const loadingMode = eager ? 'eager' : 'lazy';
  const fetchPriority = eager ? 'high' : 'low';
  const caption = [
    visual.imagePageUrl ? `<a href="${escapeAttr(visual.imagePageUrl)}" target="_blank" rel="noopener noreferrer">${escapeHTML(title)}</a>` : escapeHTML(title),
    visual.credit ? `<span>${escapeHTML(visual.credit)}</span>` : '',
    visual.license ? `<span>${escapeHTML(visual.license)}</span>` : ''
  ].filter(Boolean).join('');
  return `<figure class="museum-image ${escapeAttr(className)}" data-fallback="${escapeAttr(title)}">
    <img src="${escapeAttr(visual.imageUrl)}" alt="${escapeAttr(visual.alt || title)}" loading="${loadingMode}" decoding="async" fetchpriority="${fetchPriority}" referrerpolicy="no-referrer">
    <figcaption>${caption}</figcaption>
  </figure>`;
}

function bindImageFallbacks() {
  document.querySelectorAll('.museum-image img').forEach(img => {
    img.addEventListener('error', () => img.closest('.museum-image')?.classList.add('image-failed'), { once: true });
  });
}

function bindImageLightbox() {
  const box = document.getElementById('image-lightbox');
  const image = document.getElementById('lightbox-image');
  const caption = document.getElementById('lightbox-caption');
  const closeButton = document.getElementById('lightbox-close');
  if (!box || !image || !caption || !closeButton) return;

  const close = () => {
    box.classList.remove('active');
    box.setAttribute('aria-hidden', 'true');
    image.removeAttribute('src');
    image.removeAttribute('alt');
    caption.textContent = '';
  };

  closeButton.onclick = close;
  box.onclick = event => {
    if (event.target === box) close();
  };

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && box.classList.contains('active')) close();
  });

  document.querySelectorAll('.museum-image img').forEach(img => {
    img.addEventListener('click', event => {
      const target = event.currentTarget;
      const figure = target.closest('.museum-image');
      if (!figure || figure.classList.contains('image-failed')) return;
      image.src = target.getAttribute('src') || '';
      image.alt = target.getAttribute('alt') || '';
      caption.textContent = target.getAttribute('alt') || '';
      box.classList.add('active');
      box.setAttribute('aria-hidden', 'false');
    });
  });
}

function bindNavHighlight() {
  const links = [...document.querySelectorAll('.hall-nav a')];
  const targets = links.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === `#${entry.target.id}`));
    });
  }, { rootMargin: '-35% 0px -55% 0px', threshold: 0 });
  targets.forEach(t => obs.observe(t));
}

function getExhibit(id) { return museumData.museum.exhibits.find(e => e.id === id); }
function getPerson(id) { return museumData.persons.find(p => p.id === id); }
function getEvent(id) { return museumData.events.find(e => e.id === id); }
function getSubject(id) { return museumData.subjects.find(s => s.id === id); }
function getSource(id) { return museumData.sources.find(s => s.id === id); }
function getPersonEvents(personId) { return museumData.personEvents.filter(rel => rel.personId === personId); }
function getVisual(targetType, targetId) { return (museumData.museum.visualAssets || []).find(v => v.targetType === targetType && v.targetId === targetId); }
function getFilteredPersons() {
  let list = personTypeFilter === 'all' ? museumData.persons : museumData.persons.filter(p => (p.personType || '人物') === personTypeFilter);
  const q = normalizeCatalogQuery(personQuery);
  if (!q) return list;
  return list.filter(p => {
    const subj = getSubject(p.forceId);
    return normalizeCatalogQuery([p.name, p.nameEn, p.personType, p.hometown, subj?.name, subj?.shortName, p.summary].join(' ')).includes(q);
  });
}
function getCostEvents() {
  return museumData.events.filter(event => {
    const text = `${event.type || ''}${event.title || ''}${event.description || ''}${event.casualties || ''}`;
    return event.type === '牺牲' || Boolean(event.metrics?.redLosses) || /牺牲|损失|锐减|惨重|托孤|雪山|草地/.test(text);
  });
}
function getDefaultPersonId() {
  const visualPersonIds = new Set((museumData.museum.visualAssets || []).filter(v => v.targetType === 'person').map(v => v.targetId));
  return museumData.persons?.find(p => visualPersonIds.has(p.id))?.id || museumData.persons?.[0]?.id || '';
}
function jumpToPerson(personId) {
  if (!personId) return;
  selectedPersonId = personId;
  personTypeFilter = 'all';
  renderPersonBrowser();
  bindImageFallbacks();
  document.getElementById('persons')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function compareEvents(a, b) {
  return new Date(a?.date || 0) - new Date(b?.date || 0) || Number(a?.sequence || 0) - Number(b?.sequence || 0);
}
function dateRange(events) {
  if (!events?.length) return '';
  const sorted = [...events].sort(compareEvents);
  const start = formatDate(sorted[0].date);
  const end = formatDate(sorted[sorted.length - 1].date);
  return start === end ? start : `${start} 至 ${end}`;
}
function personLifespan(person) {
  if (person.birthDate && person.deathDate) return `${person.birthDate} - ${person.deathDate}`;
  return person.birthDate || person.deathDate || '';
}
function splitList(value) {
  return String(value || '').split(/[;；,，、]/).map(item => item.trim()).filter(Boolean);
}
function normalizeCatalogQuery(value) {
  return String(value || '').toLocaleLowerCase('zh-CN').replace(/\s+/g, '');
}
function setText(id, value) { const el = document.getElementById(id); if (el) el.textContent = value; }
function formatDate(dateStr) { const d = new Date(dateStr); return Number.isNaN(d.getTime()) ? dateStr : `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`; }
function formatNumber(value) { return Number(value || 0).toLocaleString('zh-CN'); }
function cssUrl(value) { return String(value ?? '').replaceAll('\\', '\\\\').replaceAll('"', '\\"'); }
function escapeHTML(value) { return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;'); }
function escapeAttr(value) { return escapeHTML(value).replaceAll('`','&#096;'); }

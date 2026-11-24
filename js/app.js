/**
 * 红军长征星火路线 v5
 * - 数据源：data/long_march_events.json
 * - 播放：全局时间顺序
 * - 连线：只连接同一部队/路线
 * - 色彩：按部队统一，不再按事件类型染色
 * - 点位：取消内部文字，减少地图噪音；最新点位更大且置顶
 * - 特效：会师、牺牲、七律诗句、敌军围堵触发叙事横幅
 */

const DATA_URL = 'data/long_march_events.json';
const TILE_URL = 'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}';

let map = null;
let marchData = null;
let allNormalizedEvents = [];
let sortedEvents = [];
let currentSortedIndex = 0;
let activeForces = new Set();
let scopeMode = 'core';        // 'core' (核心长征 1934-36) | 'all' (全域星火+专题+文献史)
let evidenceMode = 'verified'; // 'verified' (权威+一手) | 'high' (仅权威) | 'all' (全部含待证线索)
let highlightedPerson = '';
let sourceById = new Map();
let variantIndex = new Map();
let playTimer = null;
let playSpeed = 1;
let currentZoom = 5;
let currentLang = 'zh';
let effectLayer = null;
let meetingFlagLayer = null;

const markerById = new Map();
const routeByKey = new Map();
const labelByKey = new Map();

const EVENT_TYPE_MAP = {
  '战斗': '战斗', '战役': '战斗', '围堵': '战斗', '追堵': '战斗', '封锁': '战斗', '空袭': '战斗', '突围': '战斗', '起义': '战斗',
  '行军': '行军', '转进': '行军', '转移': '行军', '整编': '行军', '根据': '行军', '根据地': '行军', '启程': '行军', '出发': '行军', '到达': '行军', '胜利': '行军', '总结': '行军', '行动': '行军',
  '决策': '决策', '会议': '决策', '分歧': '决策', '转折': '决策',
  '渡险': '渡险', '渡河': '渡险', '险阻': '渡险', '自然险阻': '渡险', '雪山': '渡险', '草地': '渡险',
  '会师': '会师',
  '牺牲': '牺牲', '被俘': '牺牲',
  '民生': '民生', '民族': '民生', '民族工作': '民生', '生活': '民生', '医疗': '民生', '诞生': '民生', '出生': '民生',
  '史料': '史料', '里程': '史料', '传播': '史料', '其他': '行军'
};

const TYPE_LABELS_EN = {
  '战斗':'Battle','行军':'March','决策':'Decision','渡险':'Crossing / Hazard',
  '会师':'Convergence','牺牲':'Sacrifice','民生':'People & Unity','史料':'Historiography'
};

const UI = {
  zh: {
    appTitle: '红军长征星火路线',
    subtitle: '多路红军星火铺开 · 突破围追堵截 · 最终大会师',
    routes: '路线', all: '全选', clear: '清空', speed: '速度', editor: '本地数据编辑',
    statsTitle: '动态统计', joinedLabel: '参征人数', lossLabel: '损失人数', victoryLabel: '胜利记录', enemyLabel: '歼俘敌', distanceLabel: '里程推进', durationLabel: '历时',
    statsNote: '统计为史实口径与点位累积结合：参征/损失为约数，歼俘敌只汇总有明确数字的条目。',
    detail: '事件详情', time: '时间', force: '路线', type: '类型', place: '地点', result: '结果', casualties: '损失', participants: '人物 / 群体',
    loading: '正在加载长征数据...', langBtn: 'English', days: '天', li: '里', approx: '约',
    meetingKicker: '会师', meetingSubtitle: '分散的星火汇流，长征胜利向前推进。',
    sacrificeKicker: '牺牲', sacrificeSubtitle: '以生命守护队伍前行，壮烈不应被路线遮蔽。',
    enemyKicker: '围堵', enemySubtitle: '敌军围追堵截形成压迫，红军在夹缝中机动突围。',
    poemKicker: '七律·长征', poemSubtitle: '诗句在这里落到山川、河流与行军现场。',
    scopeCore: '核心长征 1934–36', scopeAll: '全域星火',
    evVerified: '权威+一手', evHigh: '仅权威', evAll: '含待证线索',
    sourcesTitle: '来源考证', archiveLink: '参考书目 ↗'
  },
  en: {
    appTitle: 'Long March Spark Map',
    subtitle: 'Routes spread out, broke encirclement, and converged in the northwest',
    routes: 'Routes', all: 'All', clear: 'Clear', speed: 'Speed', editor: 'Local Data Editor',
    statsTitle: 'Dynamic Stats', joinedLabel: 'Participants', lossLabel: 'Losses', victoryLabel: 'Victory nodes', enemyLabel: 'Enemy defeated', distanceLabel: 'Mileage', durationLabel: 'Elapsed',
    statsNote: 'Figures combine historical conventions and event-level accumulation. Losses and participants are approximate; enemy defeated only includes nodes with explicit figures.',
    detail: 'Event Details', time: 'Time', force: 'Route', type: 'Type', place: 'Place', result: 'Result', casualties: 'Losses', participants: 'People / groups',
    loading: 'Loading Long March data...', langBtn: '中文', days: 'days', li: 'li', approx: 'approx.',
    meetingKicker: 'Convergence', meetingSubtitle: 'Scattered sparks converge, pushing the Long March toward victory.',
    sacrificeKicker: 'Sacrifice', sacrificeSubtitle: 'Lives were given so the columns could continue.',
    enemyKicker: 'Encirclement', enemySubtitle: 'Pursuit and blockade pressed from all sides; mobility became survival.',
    poemKicker: 'Qilu · Long March', poemSubtitle: 'A poetic line meets the actual mountains and rivers on the route.',
    scopeCore: 'Core 1934–36', scopeAll: 'All Sparks',
    evVerified: 'Verified', evHigh: 'Authoritative', evAll: 'All + Clues',
    sourcesTitle: 'Sources & Provenance', archiveLink: 'Bibliography ↗'
  }
};

const TITLE_EN_FALLBACK = {
  '中央红军主力开始战略转移': 'The Central Red Army begins its strategic transfer',
  '中央红军渡过于都河': 'The Central Red Army crosses the Yudu River',
  '湘江战役开始': 'The Xiang River Campaign begins',
  '陈树湘壮烈牺牲，红三十四师成为“绝命后卫”': 'Chen Shuxiang sacrifices himself; the 34th Division becomes the rear guard',
  '遵义会议召开': 'The Zunyi Meeting is held',
  '巧渡金沙江开始': 'The Jinsha River crossing begins',
  '刘伯承与小叶丹彝海结盟': 'Liu Bocheng and Xiao Yedan form the Yihai alliance',
  '飞夺泸定桥': 'The assault on Luding Bridge',
  '红一、红四方面军前锋在达维会师': 'The First and Fourth Front Army vanguards meet at Dawei',
  '中央红军到达吴起镇': 'The Central Red Army reaches Wuqi',
  '红四方面军与红一方面军会宁会师': 'The Fourth and First Front Armies meet at Huining',
  '红二方面军到达将台堡，三大主力会师完成': 'The Second Front Army reaches Jiangtaibao, completing the convergence'
};

function t(key) { return (UI[currentLang] && UI[currentLang][key]) || UI.zh[key] || key; }

document.addEventListener('DOMContentLoaded', initApp);

async function initApp() {
  try {
    currentLang = document.body?.dataset?.lang === 'en' ? 'en' : 'zh';
    document.documentElement.lang = currentLang === 'en' ? 'en' : 'zh-CN';
    marchData = await loadDataFromFile();
    await loadVariantGroupsForMap();
    prepareData();
    initMap();
    initMapFilters();
    initForcePanel();
    initMemorialLayer();
    initTimeline();
    bindPanelClose();
    bindLanguageToggle();
    applyLanguage();
    applyHashEvent();
    bindHashNavigation();
    renderCurrentState(true);
    hideLoading();
  } catch (err) {
    console.error(err);
    showLoadingError(err);
  }
}

async function loadDataFromFile() {
  const res = await fetch(`${DATA_URL}?v=${Date.now()}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`数据文件加载失败：${res.status} ${res.statusText}`);
  return await res.json();
}

async function loadVariantGroupsForMap() {
  try {
    const res = await fetch(`data/variant_groups.json?v=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) return;
    const payload = await res.json();
    variantIndex = new Map();
    (payload.groups || []).forEach(g => (g.variants || []).forEach(v => variantIndex.set(v.eventId, g)));
  } catch (_) {
    variantIndex = new Map();
  }
}

function prepareData() {
  if (!marchData || !Array.isArray(marchData.subjects) || !Array.isArray(marchData.events)) throw new Error('数据格式错误：必须包含 subjects 与 events。');
  sourceById = new Map((marchData.sources || []).map(s => [s.id, s]));
  marchData.subjects.forEach(s => { if (s.id === 'enemy_kmt' || s.id === 'enemy_japan') s.isEnemy = true; });
  const forceIds = new Set(marchData.subjects.filter(s => s.type === 'force').map(s => s.id));
  const seen = new Set();
  marchData.events = marchData.events.filter(e => {
    if (!e || !e.id || !e.date || !e.forceId || !e.location || !Array.isArray(e.location.coordinates)) return false;
    if (!forceIds.has(e.forceId)) return false;
    const key = `${e.date}|${e.forceId}|${e.title}|${e.location.name}`;
    if (seen.has(e.id) || seen.has(key)) return false;
    seen.add(e.id); seen.add(key);
    e.type = normalizeType(e.type);
    e.layer = e.layer || 'march';
    e.datePrecision = e.datePrecision || 'day';
    return true;
  });
  allNormalizedEvents = [...marchData.events].sort((a,b) => new Date(a.date) - new Date(b.date) || Number(a.sequence || 0) - Number(b.sequence || 0) || String(a.id).localeCompare(String(b.id),'zh-CN'));
  activeForces = new Set(marchData.subjects.filter(s => s.type === 'force').map(s => s.id));
  rebuildVisibleEvents(null);
}

function eventPassesFilters(e) {
  if (scopeMode === 'core' && (e.layer || 'march') !== 'march') return false;
  const cert = String(e.certainty || 'medium').toLowerCase();
  if (evidenceMode === 'high' && cert !== 'high') return false;
  if (evidenceMode === 'verified' && cert === 'low') return false;
  return true;
}

function rebuildVisibleEvents(anchorEventId = null) {
  const prevId = anchorEventId || sortedEvents[currentSortedIndex]?.id || null;
  sortedEvents = allNormalizedEvents.filter(eventPassesFilters);
  if (!sortedEvents.length) sortedEvents = [...allNormalizedEvents];
  sortedEvents.forEach((e, idx) => { e._globalOrder = idx + 1; });
  if (prevId) {
    const idx = sortedEvents.findIndex(e => e.id === prevId);
    currentSortedIndex = idx >= 0 ? idx : Math.min(currentSortedIndex, Math.max(0, sortedEvents.length - 1));
  } else {
    currentSortedIndex = Math.max(0, sortedEvents.length - 1);
  }
  const slider = document.getElementById('timeline-slider');
  if (slider) {
    slider.min = 0;
    slider.max = Math.max(sortedEvents.length - 1, 0);
    slider.value = currentSortedIndex;
  }
  updateTimelineLabels();
  updateFilterSummary();
}

function initMapFilters() {
  const box = document.getElementById('map-filter-box');
  if (!box) return;
  box.querySelectorAll('[data-scope]').forEach(btn => {
    btn.addEventListener('click', () => {
      const next = btn.dataset.scope || 'core';
      if (next === scopeMode) return;
      scopeMode = next;
      syncMapFilterButtons();
      rebuildVisibleEvents();
      renderCurrentState(false);
    });
  });
  box.querySelectorAll('[data-evidence]').forEach(btn => {
    btn.addEventListener('click', () => {
      const next = btn.dataset.evidence || 'verified';
      if (next === evidenceMode) return;
      evidenceMode = next;
      syncMapFilterButtons();
      rebuildVisibleEvents();
      renderCurrentState(false);
    });
  });
  syncMapFilterButtons();
}

function syncMapFilterButtons() {
  document.querySelectorAll('#map-filter-box [data-scope]').forEach(btn => btn.classList.toggle('active', btn.dataset.scope === scopeMode));
  document.querySelectorAll('#map-filter-box [data-evidence]').forEach(btn => btn.classList.toggle('active', btn.dataset.evidence === evidenceMode));
  updateFilterSummary();
}

function updateFilterSummary() {
  const el = document.getElementById('map-filter-summary');
  if (!el) return;
  const hiddenLow = evidenceMode === 'verified'
    ? allNormalizedEvents.filter(e => (scopeMode === 'all' || e.layer === 'march') && e.certainty === 'low').length
    : 0;
  const countText = currentLang === 'en'
    ? `${sortedEvents.length} / ${allNormalizedEvents.length} nodes${hiddenLow ? ` (${hiddenLow} clues hidden)` : ''}`
    : `当前 ${sortedEvents.length} / ${allNormalizedEvents.length} 节点${hiddenLow ? `（已滤 ${hiddenLow} 条待证线索）` : ''}`;
  const hlHtml = highlightedPerson
    ? `<button type="button" class="person-hl-clear" id="clear-person-hl">${escapeHTML(highlightedPerson)} ×</button>`
    : '';
  el.innerHTML = `<span>${escapeHTML(countText)}</span>${hlHtml}`;
  document.getElementById('clear-person-hl')?.addEventListener('click', () => {
    highlightedPerson = '';
    updateFilterSummary();
    refreshAllMarkerIcons();
    updateEventPanel(sortedEvents[currentSortedIndex]);
  });
}

function normalizeType(type) {
  const raw = String(type || '其他').trim();
  const mapped = EVENT_TYPE_MAP[raw] || raw;
  return mapped.length === 2 ? mapped : (EVENT_TYPE_MAP[mapped] || mapped.slice(0, 2));
}

function initMap() {
  map = L.map('map', { center:[32.6,106.5], zoom:5, minZoom:4, maxZoom:10, zoomControl:false, attributionControl:true, scrollWheelZoom:true });
  L.tileLayer(TILE_URL, { attribution:'&copy; 高德地图 / AutoNavi（中文底图）', subdomains:['1','2','3','4'], maxZoom:18 }).addTo(map);
  map.setMaxBounds(L.latLngBounds([18,94],[43,125]));
  L.control.zoom({ position:'bottomright' }).addTo(map);
  map.on('zoomend', () => { currentZoom = map.getZoom(); renderCurrentState(false); });
}

function initForcePanel() {
  const container = document.getElementById('force-list');
  container.innerHTML = '';
  const toolbar = document.createElement('div');
  toolbar.className = 'force-toolbar';
  toolbar.innerHTML = `<button type="button" id="select-all-forces"></button><button type="button" id="clear-all-forces"></button>`;
  container.appendChild(toolbar);
  const forces = getForcesSorted();
  // 反馈(2026-05-28)：路线按「红军主线 / 星星之火 / 敌军」视角分组显示
  const groupOrder = ['红军主线', '星星之火', '敌军'];
  const groupI18n = {
    '红军主线': { zh: '红军主线', en: 'Main Red Armies' },
    '星星之火': { zh: '星星之火', en: 'Sparks' },
    '敌军': { zh: '敌军', en: 'Opposing Forces' }
  };
  const grouped = new Map();
  forces.forEach(force => {
    const g = force.group || (force.isEnemy ? '敌军' : '红军主线');
    if (!grouped.has(g)) grouped.set(g, []);
    grouped.get(g).push(force);
  });
  const orderedGroups = [...groupOrder.filter(g => grouped.has(g)), ...[...grouped.keys()].filter(g => !groupOrder.includes(g))];
  orderedGroups.forEach(groupName => {
    const header = document.createElement('div');
    header.className = `force-group-heading${groupName === '敌军' ? ' force-group-enemy' : ''}`;
    const label = groupI18n[groupName] || { zh: groupName, en: groupName };
    header.innerHTML = `<span class="force-group-title" data-group-zh="${escapeAttr(label.zh)}" data-group-en="${escapeAttr(label.en)}">${escapeHTML(label.zh)}</span><span class="force-group-count">${grouped.get(groupName).length}</span>`;
    container.appendChild(header);
    grouped.get(groupName).forEach(force => {
      const item = document.createElement('div');
      item.className = `force-item active ${force.isEnemy ? 'force-enemy' : ''}`;
      item.dataset.forceId = force.id;
      item.innerHTML = `
        <div class="force-color" style="background:${escapeAttr(force.color || '#777')}"></div>
        <div class="force-info">
          <div class="force-name"></div>
          <div class="force-short"></div>
          <div class="force-subunits"></div>
        </div>
        <span class="force-switch" aria-hidden="true"></span>`;
      item.addEventListener('click', ev => { ev.preventDefault(); toggleForce(force.id); });
      container.appendChild(item);
    });
  });
  document.getElementById('select-all-forces').addEventListener('click', ev => { ev.stopPropagation(); getForcesSorted().forEach(f => activeForces.add(f.id)); syncForcePanel(); renderCurrentState(false); });
  document.getElementById('clear-all-forces').addEventListener('click', ev => { ev.stopPropagation(); activeForces.clear(); syncForcePanel(); renderCurrentState(false); });
  syncForcePanel();
}
function getForcesSorted() { return marchData.subjects.filter(s => s.type === 'force').sort((a,b) => (a.isEnemy === b.isEnemy ? Number(a.sort || 999) - Number(b.sort || 999) : (a.isEnemy ? 1 : -1))); }
function toggleForce(forceId) { activeForces.has(forceId) ? activeForces.delete(forceId) : activeForces.add(forceId); syncForcePanel(); renderCurrentState(false); }
function syncForcePanel() {
  document.querySelectorAll('.force-item').forEach(item => {
    const force = getSubject(item.dataset.forceId) || {};
    item.classList.toggle('active', activeForces.has(force.id));
    const switcher = item.querySelector('.force-switch'); if (switcher) switcher.textContent = activeForces.has(force.id) ? '●' : '○';
    const name = item.querySelector('.force-name'); if (name) name.textContent = getSubjectName(force);
    const desc = item.querySelector('.force-short'); if (desc) desc.textContent = currentLang === 'zh' ? (force.leader || '') : (force.leaderEn || force.descriptionEn || '');
    const sub = item.querySelector('.force-subunits'); if (sub) renderSubUnits(sub, force);
  });
  document.querySelectorAll('.force-group-title').forEach(el => { el.textContent = currentLang === 'en' ? (el.dataset.groupEn || el.textContent) : (el.dataset.groupZh || el.textContent); });
  const selectAll = document.getElementById('select-all-forces'); if (selectAll) selectAll.textContent = t('all');
  const clearAll = document.getElementById('clear-all-forces'); if (clearAll) clearAll.textContent = t('clear');
}
function renderSubUnits(container, force) {
  const raw = currentLang === 'en' ? (force.subUnitsEn || '') : (force.subUnits || '');
  const units = String(raw || '').split(/[;；|｜]/).map(s => s.trim()).filter(Boolean);
  container.innerHTML = units.map(u => `<span class="subunit-chip">${escapeHTML(u)}</span>`).join('');
}

function initTimeline() {
  const slider = document.getElementById('timeline-slider');
  slider.min = 0; slider.max = Math.max(sortedEvents.length - 1, 0); slider.value = currentSortedIndex;
  document.getElementById('prev-btn').addEventListener('click', () => stepTimeline(-1));
  document.getElementById('next-btn').addEventListener('click', () => stepTimeline(1));
  document.getElementById('play-btn').addEventListener('click', togglePlay);
  document.getElementById('speed-select').addEventListener('change', ev => { playSpeed = Number(ev.target.value) || 1; if (playTimer) { stopPlay(); startPlay(); } });
  slider.addEventListener('input', ev => { currentSortedIndex = Number(ev.target.value); renderCurrentState(true); });
  updateTimelineLabels();
}
function updateTimelineLabels() {
  const labels = document.querySelector('.timeline-labels');
  if (!labels || !sortedEvents.length) return;
  labels.innerHTML = `<span>${formatDateZh(sortedEvents[0].date)}</span><span>${formatDateZh(sortedEvents[sortedEvents.length - 1].date)}</span>`;
}
function bindPanelClose() { document.getElementById('panel-close')?.addEventListener('click', () => document.getElementById('event-panel').classList.remove('show')); }
function bindLanguageToggle() {
  const btn = document.getElementById('lang-toggle');
  if (!btn) return;
  btn.addEventListener('click', () => {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    document.documentElement.lang = currentLang === 'zh' ? 'zh-CN' : 'en';
    applyLanguage(); syncForcePanel(); refreshAllMarkerIcons(); updateTimelineDisplay(); updateStats(); updateEventPanel(sortedEvents[currentSortedIndex]); updateSpecialEffects(sortedEvents[currentSortedIndex]);
  });
}
function bindHashNavigation() {
  window.addEventListener('hashchange', () => {
    if (applyHashEvent()) renderCurrentState(true);
  });
}
function applyHashEvent() {
  const raw = window.location.hash.replace(/^#/, '');
  if (!raw || !allNormalizedEvents.length) return false;
  const params = new URLSearchParams(raw);
  const eventId = params.get('event');
  const placeName = params.get('place');
  let target = null;
  if (eventId) {
    target = allNormalizedEvents.find(e => e.id === eventId);
  } else if (placeName) {
    target = sortedEvents.find(e => (e.location?.name || '').includes(placeName))
      || allNormalizedEvents.find(e => (e.location?.name || '').includes(placeName));
  }
  if (!target) return false;
  // 若目标事件在当前滤镜之外，自动放宽模式确保可达
  let changed = false;
  if (scopeMode === 'core' && (target.layer || 'march') !== 'march') { scopeMode = 'all'; changed = true; }
  if (evidenceMode === 'high' && target.certainty !== 'high') { evidenceMode = target.certainty === 'low' ? 'all' : 'verified'; changed = true; }
  else if (evidenceMode === 'verified' && target.certainty === 'low') { evidenceMode = 'all'; changed = true; }
  if (changed) { syncMapFilterButtons(); rebuildVisibleEvents(target.id); }
  const idx = sortedEvents.findIndex(e => e.id === target.id);
  if (idx < 0) return false;
  currentSortedIndex = idx;
  return true;
}
function applyLanguage() { document.querySelectorAll('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n)); document.title = t('appTitle'); const btn = document.getElementById('lang-toggle'); if (btn) btn.textContent = t('langBtn'); updateTimelineLabels(); updateFilterSummary(); }
function stepTimeline(delta) { const next = Math.max(0, Math.min(sortedEvents.length - 1, currentSortedIndex + delta)); if (next !== currentSortedIndex) { currentSortedIndex = next; renderCurrentState(true); } }
function togglePlay() { playTimer ? stopPlay() : startPlay(); }
function getPlaybackDelay(event) {
  const base = Math.max(1200, 2600 / playSpeed);
  return event?.type === '会师' ? Math.max(base + 2200, 4400) : base;
}
function startPlay() {
  if (currentSortedIndex >= sortedEvents.length - 1) {
    currentSortedIndex = 0;
    renderCurrentState(true);
  }
  document.getElementById('play-btn').textContent = '⏸';
  scheduleNextStep();
}
function scheduleNextStep() {
  if (playTimer) window.clearTimeout(playTimer);
  playTimer = window.setTimeout(() => {
    if (currentSortedIndex >= sortedEvents.length - 1) { stopPlay(); return; }
    currentSortedIndex += 1;
    renderCurrentState(true);
    scheduleNextStep();
  }, getPlaybackDelay(sortedEvents[currentSortedIndex]));
}
function stopPlay() { if (playTimer) window.clearTimeout(playTimer); playTimer = null; document.getElementById('play-btn').textContent = '▶'; }

function renderCurrentState(panToCurrent = true) {
  if (!map || !sortedEvents.length) return;
  const displayed = sortedEvents.slice(0, currentSortedIndex + 1);
  const activeDisplayed = displayed.filter(e => activeForces.has(e.forceId));
  const latestByForce = getLatestEventByForce(activeDisplayed);
  reconcileRoutes(activeDisplayed);
  reconcileMarkers(activeDisplayed, latestByForce);
  reconcileLabels(activeDisplayed, latestByForce);
  updateTimelineDisplay(); updateStats(activeDisplayed, displayed); updateEventPanel(sortedEvents[currentSortedIndex]); updateSpecialEffects(sortedEvents[currentSortedIndex]);
  const currentEvent = sortedEvents[currentSortedIndex];
  if (panToCurrent && currentEvent && activeForces.has(currentEvent.forceId) && currentEvent.location?.coordinates) map.panTo(currentEvent.location.coordinates, { animate:true, duration:.55 });
}
function getLatestEventByForce(events) { const latest = new Map(); events.forEach(e => { const old = latest.get(e.forceId); if (!old || e._globalOrder > old._globalOrder) latest.set(e.forceId, e); }); return latest; }

function isRouteLayerEvent(event) {
  const layer = event?.layer || 'march';
  return layer === 'march' || layer === 'spark_march';
}

function reconcileRoutes(events) {
  const wanted = new Set();
  const routeEvents = events.filter(isRouteLayerEvent);
  const byForce = groupBy(routeEvents, e => e.forceId);
  Object.entries(byForce).forEach(([forceId, forceEvents]) => {
    const force = getSubject(forceId); if (!force || forceEvents.length < 2) return;
    const sorted = [...forceEvents].sort(sortEventAscending);
    for (let i=1; i<sorted.length; i++) {
      const prev = sorted[i-1], curr = sorted[i];
      const key = `${prev.id}__${curr.id}`; wanted.add(key);
      const isHeadSegment = i === sorted.length - 1;
      const opts = getRouteOptions(force, isHeadSegment);
      if (!routeByKey.has(key)) {
        const line = L.polyline([prev.location.coordinates, curr.location.coordinates], opts).addTo(map);
        let decorator = null;
        if (L.polylineDecorator) decorator = L.polylineDecorator(line, { patterns:[{ offset:'74%', repeat:0, symbol:L.Symbol.arrowHead({ pixelSize: force.isEnemy ? 6 : 9, polygon:false, pathOptions:{ color:opts.color, weight:force.isEnemy ? 1 : 2, opacity: force.isEnemy ? .35 : .72 } }) }] }).addTo(map);
        routeByKey.set(key, { line, decorator });
      } else {
        routeByKey.get(key).line.setStyle(opts);
      }
    }
  });
  for (const [key, rec] of [...routeByKey.entries()]) if (!wanted.has(key)) { map.removeLayer(rec.line); if (rec.decorator) map.removeLayer(rec.decorator); routeByKey.delete(key); }
}
function getRouteOptions(force, isHeadSegment=false) {
  if (force?.isEnemy) {
    return { color:'#777', weight: isHeadSegment ? 3.4 : 2, opacity: isHeadSegment ? .52 : .24, dashArray:'9 9', lineCap:'round', lineJoin:'round', className:'route-enemy' };
  }
  return { color: force?.color || '#333', weight: isHeadSegment ? 7 : Math.max(2.4, currentZoom >= 6 ? 3.6 : 2.8), opacity: isHeadSegment ? .96 : .62, lineCap:'round', lineJoin:'round', className: isHeadSegment ? 'route-head' : 'route-normal' };
}

function reconcileMarkers(events, latestByForce) {
  const wanted = new Set(events.map(e => e.id));
  const coordCounter = new Map();
  events.forEach(event => {
    const coords = event.location.coordinates;
    const coordKey = `${coords[0].toFixed(3)},${coords[1].toFixed(3)}`;
    const count = coordCounter.get(coordKey) || 0; coordCounter.set(coordKey, count + 1);
    const adjusted = offsetCoordinates(coords, count);
    const status = markerStatus(event, latestByForce);
    const force = getSubject(event.forceId) || {};
    if (!markerById.has(event.id)) {
      const marker = L.marker(adjusted, { icon:makeEventIcon(event, force, status), zIndexOffset:status.zIndex }).addTo(map).bindPopup(getPopupHTML(event, force), { className:'mono-popup' });
      marker.on('click', () => { currentSortedIndex = event._globalOrder - 1; renderCurrentState(false); marker.openPopup(); });
      markerById.set(event.id, { marker, statusKey:status.key });
    } else {
      const rec = markerById.get(event.id);
      rec.marker.setLatLng(adjusted); rec.marker.setZIndexOffset(status.zIndex);
      if (rec.statusKey !== status.key) { rec.marker.setIcon(makeEventIcon(event, force, status)); rec.statusKey = status.key; }
      rec.marker.setPopupContent(getPopupHTML(event, force));
    }
  });
  for (const [id, rec] of [...markerById.entries()]) if (!wanted.has(id)) { map.removeLayer(rec.marker); markerById.delete(id); }
}

function reconcileLabels(events, latestByForce) {
  const candidates = [];
  const used = new Set();
  events.forEach(event => {
    if (!shouldShowLocationLabel(event, latestByForce)) return;
    const force = getSubject(event.forceId) || {};
    const text = getLocationLabelText(event);
    const coords = event.location?.coordinates;
    if (!text || !coords) return;
    const key = `${event.date}|${event.type}|${text}|${coords[0].toFixed(2)}|${coords[1].toFixed(2)}`;
    if (used.has(key)) return;
    used.add(key);
    candidates.push({ key, event, force, text, coords });
  });

  const wanted = new Set(candidates.map(c => c.key));
  const placements = computeMeetingLabelPlacements(candidates, events);

  candidates.forEach(c => {
    const placement = placements.get(c.key);
    if (!placement) return;
    const color = c.force.isEnemy ? '#777' : (c.force.color || '#555');
    const cls = ['location-label', 'location-label-meeting', c.force.isEnemy ? 'location-label-enemy' : ''].join(' ');
    const html = `<div class="${cls}" style="--label-color:${escapeAttr(color)};width:${placement.w}px"><span>${escapeHTML(c.text)}</span></div>`;
    const icon = L.divIcon({ className:'location-label-wrapper', html, iconSize:[placement.w, placement.h], iconAnchor:[placement.w / 2, placement.h / 2] });
    const labelLatLng = map.unproject(L.point(placement.x, placement.y), map.getZoom());
    const leaderLatLng = map.unproject(L.point(placement.x, placement.y + placement.h * 0.12), map.getZoom());
    const lineOpts = { color, weight:1.4, opacity:.45, dashArray:'3 5', lineCap:'round', interactive:false, className:'meeting-label-leader' };

    if (!labelByKey.has(c.key)) {
      const marker = L.marker(labelLatLng, { icon, interactive:false, zIndexOffset: 9300 }).addTo(map);
      const leader = L.polyline([c.coords, leaderLatLng], lineOpts).addTo(map);
      labelByKey.set(c.key, { marker, leader, html, x:placement.x, y:placement.y });
    } else {
      const rec = labelByKey.get(c.key);
      rec.marker.setLatLng(labelLatLng);
      if (rec.leader) rec.leader.setLatLngs([c.coords, leaderLatLng]).setStyle(lineOpts);
      if (rec.html !== html) { rec.marker.setIcon(icon); rec.html = html; }
    }
  });

  for (const [key, rec] of [...labelByKey.entries()]) {
    if (!wanted.has(key)) {
      if (rec.leader) map.removeLayer(rec.leader);
      map.removeLayer(rec.marker);
      labelByKey.delete(key);
    }
  }
}

function computeMeetingLabelPlacements(candidates, visibleEvents) {
  const placements = new Map();
  if (!map || !candidates.length) return placements;
  const viewport = map.getSize();
  const usedRects = [];
  const routeSegments = buildScreenRouteSegments(visibleEvents);
  const defaultOffsets = [
    [92, -58], [-108, -58], [94, 52], [-112, 52],
    [140, -10], [-156, -10], [18, -104], [18, 96],
    [150, 58], [-166, 58], [150, -82], [-166, -82]
  ];

  candidates.forEach((c, idx) => {
    const base = map.project(c.coords, map.getZoom());
    const textLen = [...String(c.text || '')].length;
    // v21: convergence labels must show the full place name; do not let the
    // Huining / Jiangtaibao labels be clipped or ellipsized.
    const w = Math.min(260, Math.max(116, textLen * (currentLang === 'en' ? 8.2 : 15.0) + 34));
    const h = 34;
    let best = null;
    let bestScore = Infinity;
    const text = `${c.text || ''}${c.event?.title || ''}${c.event?.location?.name || ''}`;
    let offsets = defaultOffsets;
    // Keep the final two convergence labels close to the nodes but on opposite sides:
    // Huining/Gansu to the left, Jiangtaibao/Ningxia to the right.
    if (/会宁|Huining/i.test(text)) offsets = [[-116, -42], [-118, 42], [-150, -6], [-90, -76], [-90, 72], ...defaultOffsets];
    if (/将台堡|西吉|Jiangtaibao|Xiji/i.test(text)) offsets = [[116, -42], [118, 42], [150, -6], [90, -76], [90, 72], ...defaultOffsets];

    offsets.forEach((off, offIdx) => {
      const dx = off[0] + (idx % 2) * 8;
      const dy = off[1] + (idx % 2) * 6;
      const center = L.point(base.x + dx, base.y + dy);
      const rect = rectFromCenter(center, w, h, 8);
      let score = Math.abs(dx) * 0.08 + Math.abs(dy) * 0.08 + offIdx;
      if (!rectWithinViewport(rect, viewport, 12)) score += 10000;
      usedRects.forEach(r => { if (rectsOverlap(rect, r, 14)) score += 6000; });
      routeSegments.forEach(seg => { if (segmentIntersectsRect(seg, rect)) score += 950; });
      if (pointInRect(base, expandRect(rect, 16))) score += 8000;
      if (score < bestScore) { bestScore = score; best = { x:center.x, y:center.y, w, h, rect }; }
    });

    if (!best) {
      const fallback = L.point(base.x + 140 + idx * 10, base.y - 90 - idx * 8);
      best = { x:fallback.x, y:fallback.y, w, h, rect:rectFromCenter(fallback, w, h, 8) };
    }
    usedRects.push(best.rect);
    placements.set(c.key, best);
  });
  return placements;
}

function buildScreenRouteSegments(events) {
  const segments = [];
  const byForce = groupBy(events.filter(e => e.location?.coordinates), e => e.forceId);
  Object.values(byForce).forEach(forceEvents => {
    const sorted = [...forceEvents].sort(sortEventAscending);
    for (let i = 1; i < sorted.length; i++) {
      segments.push({
        a: map.project(sorted[i - 1].location.coordinates, map.getZoom()),
        b: map.project(sorted[i].location.coordinates, map.getZoom())
      });
    }
  });
  return segments;
}

function rectFromCenter(center, w, h, pad=0) {
  return { left:center.x - w/2 - pad, right:center.x + w/2 + pad, top:center.y - h/2 - pad, bottom:center.y + h/2 + pad };
}
function expandRect(r, pad) { return { left:r.left-pad, right:r.right+pad, top:r.top-pad, bottom:r.bottom+pad }; }
function rectWithinViewport(r, size, margin=0) { return r.left >= margin && r.top >= margin && r.right <= size.x - margin && r.bottom <= size.y - margin; }
function rectsOverlap(a, b, margin=0) { return !(a.right + margin < b.left || a.left - margin > b.right || a.bottom + margin < b.top || a.top - margin > b.bottom); }
function pointInRect(p, r) { return p.x >= r.left && p.x <= r.right && p.y >= r.top && p.y <= r.bottom; }
function segmentIntersectsRect(seg, rect) {
  const r = expandRect(rect, 3);
  if (pointInRect(seg.a, r) || pointInRect(seg.b, r)) return true;
  const edges = [
    [{x:r.left,y:r.top},{x:r.right,y:r.top}], [{x:r.right,y:r.top},{x:r.right,y:r.bottom}],
    [{x:r.right,y:r.bottom},{x:r.left,y:r.bottom}], [{x:r.left,y:r.bottom},{x:r.left,y:r.top}]
  ];
  return edges.some(edge => segmentsIntersect(seg.a, seg.b, edge[0], edge[1]));
}
function segmentsIntersect(p1, p2, p3, p4) {
  const d1 = direction(p3, p4, p1), d2 = direction(p3, p4, p2), d3 = direction(p1, p2, p3), d4 = direction(p1, p2, p4);
  return ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0));
}
function direction(a, b, c) { return (c.x - a.x) * (b.y - a.y) - (b.x - a.x) * (c.y - a.y); }

function shouldShowLocationLabel(event, latestByForce) {
  // Only keep place labels for the final convergence nodes.
  // Intermediate place boxes are intentionally suppressed to keep the route map clean.
  if (event.type !== '会师') return false;
  const text = `${event.title || ''}${event.location?.name || ''}`;
  return /(会宁|将台堡|三大主力|大会师|会师完成|长征胜利)/.test(text);
}

function getLocationLabelText(event) {
  const name = getLocationName(event).replace(/一带|地区|区域|流域/g, '').trim();
  if (!name) return '';
  if (event.type === '会师') return `${name}会师`;
  return name.length > 12 ? name.slice(0, 12) : name;
}
function markerStatus(event, latestByForce) {
  const current = event.id === sortedEvents[currentSortedIndex].id;
  const latest = latestByForce.get(event.forceId)?.id === event.id;
  const meeting = event.type === '会师';
  const sacrifice = event.type === '牺牲';
  const enemy = getSubject(event.forceId)?.isEnemy;
  const poem = Boolean(event.poem);
  const nonRoute = !isRouteLayerEvent(event);
  const personHl = Boolean(highlightedPerson && Array.isArray(event.participants) && event.participants.includes(highlightedPerson));
  const key = [current?'current':'', latest?'latest':'', meeting?'meeting':'', sacrifice?'sacrifice':'', enemy?'enemy':'', poem?'poem':'', nonRoute?'nr':'', personHl?'phl':'', currentLang, currentZoom].join('|');
  const zIndex = personHl ? 9800 : enemy ? 500 : current ? 10000 : latest ? 8500 : meeting ? 7600 : sacrifice ? 7300 : poem ? 7000 : 1000 + event._globalOrder;
  return { current, latest, meeting, sacrifice, enemy, poem, nonRoute, personHl, key, zIndex };
}
function refreshAllMarkerIcons() { markerById.forEach(rec => rec.statusKey = 'refresh'); renderCurrentState(false); }
function makeEventIcon(event, force, status) {
  const size = getMarkerSize(status);
  const color = status.enemy ? '#777' : (force.color || '#555');
  const cls = ['event-marker', status.current?'event-marker-current':'', status.latest?'event-marker-latest':'', status.meeting?'event-marker-meeting':'', status.sacrifice?'event-marker-sacrifice':'', status.enemy?'event-marker-enemy':'', status.poem?'event-marker-poem':'', status.nonRoute?'event-marker-nonroute':'', status.personHl?'event-marker-person-hl':''].join(' ');
  const html = `<div class="marker-shell ${cls}" style="width:${size}px;height:${size}px;--marker-color:${escapeAttr(color)}"><div class="marker-core"></div></div>`;
  return L.divIcon({ className:'event-marker-wrapper', html, iconSize:[size,size], iconAnchor:[size/2,size/2] });
}
function getMarkerSize(status) {
  let base = status.enemy ? 8 : 9;
  if (status.latest) base = status.enemy ? 16 : 20;
  if (status.current && status.latest) base = Math.max(base, status.enemy ? 18 : 22);
  const scale = 1 + (currentZoom - 5) * .055;
  return Math.max(7, Math.min(28, base * scale));
}

function updateSpecialEffects(event) {
  if (effectLayer) { map.removeLayer(effectLayer); effectLayer = null; }
  if (meetingFlagLayer) { map.removeLayer(meetingFlagLayer); meetingFlagLayer = null; }
  const banner = document.getElementById('narrative-banner'); if (banner) banner.classList.add('hidden');
  if (!event || !activeForces.has(event.forceId)) return;
  const force = getSubject(event.forceId) || {};
  let show = false, kicker = '', title = getEventTitle(event), subtitle = '', radius = 50000, color = force.color || '#555';
  if (event.poem) {
    show = true; kicker = t('poemKicker');
    title = currentLang === 'zh' ? `${event.poem.line}｜${event.poem.title || getEventTitle(event)}` : (event.poem.titleEn || getEventTitle(event));
    subtitle = currentLang === 'zh' ? (event.poem.text || t('poemSubtitle')) : (event.poem.textEn || t('poemSubtitle'));
    radius = 72000;
  } else if (event.type === '会师') { show = true; kicker = t('meetingKicker'); subtitle = t('meetingSubtitle'); radius = 76000; }
  else if (event.type === '牺牲') { show = true; kicker = t('sacrificeKicker'); subtitle = t('sacrificeSubtitle'); radius = 52000; }
  else if (force.isEnemy && ['战斗','追堵','封锁','围堵','空袭'].includes(event.type)) { show = true; kicker = t('enemyKicker'); subtitle = t('enemySubtitle'); radius = 56000; color = '#777'; }
  if (show && event.location?.coordinates) {
    effectLayer = L.circle(event.location.coordinates, { radius, color, weight:event.type === '会师' ? 3 : 2, fillColor:color, fillOpacity:event.poem ? .08 : .06, opacity:.62, className:'event-effect-circle' }).addTo(map);
    if (event.type === '会师') showMeetingFlag(event);
    if (banner) {
      document.getElementById('banner-kicker').textContent = kicker;
      document.getElementById('banner-title').textContent = title;
      document.getElementById('banner-subtitle').textContent = subtitle;
      banner.classList.remove('hidden');
      window.clearTimeout(updateSpecialEffects._timer);
      updateSpecialEffects._timer = window.setTimeout(() => banner.classList.add('hidden'), event.poem ? 7800 : (event.type === '会师' ? 4200 : 5000));
    }
  }
}
function showMeetingFlag(event) {
  if (!event.location?.coordinates) return;
  const html = `<div class="meeting-flag">🚩</div>`;
  const icon = L.divIcon({ className:'meeting-flag-wrapper', html, iconSize:[44,44], iconAnchor:[16,38] });
  meetingFlagLayer = L.marker(event.location.coordinates, { icon, interactive:false, zIndexOffset: 12000 }).addTo(map);
  window.clearTimeout(showMeetingFlag._timer);
  showMeetingFlag._timer = window.setTimeout(() => {
    if (meetingFlagLayer) { map.removeLayer(meetingFlagLayer); meetingFlagLayer = null; }
  }, 4300);
}

function offsetCoordinates(coords, count) { if (count === 0) return coords; const angle = (count * 47) * Math.PI / 180; const radius = .022 + Math.floor(count / 6) * .012; return [coords[0] + Math.sin(angle) * radius, coords[1] + Math.cos(angle) * radius]; }

function updateTimelineDisplay() { const event = sortedEvents[currentSortedIndex]; if (!event) return; document.getElementById('timeline-slider').value = currentSortedIndex; document.getElementById('current-date').textContent = getDisplayDate(event); document.getElementById('current-event-title').textContent = getEventTitle(event); }
function getEvidenceBadgeHTML(certainty) {
  const c = String(certainty || 'medium').toLowerCase();
  const mapZh = { high: ['权威史实', 'map-ev-high'], medium: ['一手见闻', 'map-ev-medium'], low: ['线索待证', 'map-ev-low'] };
  const mapEn = { high: ['Authoritative', 'map-ev-high'], medium: ['Firsthand', 'map-ev-medium'], low: ['Unverified clue', 'map-ev-low'] };
  const [label, cls] = (currentLang === 'en' ? mapEn : mapZh)[c] || [c, 'map-ev-medium'];
  return `<span class="map-ev-badge ${cls}">${escapeHTML(label)}</span>`;
}

function getPrecisionBadgeHTML(prec) {
  const p = String(prec || 'day').toLowerCase();
  if (p === 'day') return '';
  const labels = currentLang === 'en'
    ? { month: 'Month-level', range: 'Date range', approx: 'Approximate' }
    : { month: '仅知月份', range: '时间区间', approx: '约略日期' };
  return labels[p] ? `<span class="map-ev-badge map-ev-prec">${escapeHTML(labels[p])}</span>` : '';
}

function getLayerBadgeHTML(layer) {
  if (!layer || layer === 'march') return '';
  const labels = currentLang === 'en'
    ? { spark_march: 'Extended Spark', theme_stat: 'Thematic / Stat', historiography: 'Historiography' }
    : { spark_march: '延伸星火', theme_stat: '专题/统计', historiography: '文献传播史' };
  return labels[layer] ? `<span class="map-ev-badge map-ev-layer">${escapeHTML(labels[layer])}</span>` : '';
}

function extractCitationHint(event) {
  const notes = String(event?.notes || '').trim();
  if (!notes) return '';
  const m = notes.match(/据《[^》]+》[^；。\n]{0,42}/);
  if (m) return m[0];
  const m2 = notes.match(/《红军长征记》[^；。\n]{0,36}/);
  return m2 ? m2[0] : '';
}

function renderEventSourcesHTML(event) {
  const sids = Array.isArray(event?.sourceIds) ? event.sourceIds : [];
  if (!sids.length) return '';
  const hint = extractCitationHint(event);
  const pills = sids.map(id => {
    const src = sourceById.get(id);
    if (!src) return `<span class="source-pill">${escapeHTML(id)}</span>`;
    const kind = src.mediaType === '专著' ? '书' : src.sourceType === 'game_text' ? '线索' : '网';
    const year = src.year ? ` (${src.year})` : '';
    const label = `${src.title}${year}`;
    const href = src.url && /^https?:\/\//.test(src.url) ? src.url : `museum.html?source=${encodeURIComponent(id)}#catalog`;
    const targetAttr = /^https?:\/\//.test(href) ? ' target="_blank" rel="noopener noreferrer"' : '';
    return `<a class="source-pill" href="${escapeAttr(href)}"${targetAttr} title="${escapeAttr(src.publisher || src.title)}"><span class="source-pill-kind">[${kind}]</span><span>${escapeHTML(label)}</span></a>`;
  }).join('');
  return `<div class="event-sources-box">
    <div class="event-sources-head">
      <h4>${escapeHTML(t('sourcesTitle'))}</h4>
      <a href="museum.html#archive" target="_blank" rel="noopener">${escapeHTML(t('archiveLink'))}</a>
    </div>
    ${hint ? `<div class="event-citation-loc">${escapeHTML(hint)}</div>` : ''}
    <div class="source-pill-list">${pills}</div>
  </div>`;
}

function renderMapVariantHTML(event) {
  const g = variantIndex.get(event.id);
  if (!g || !Array.isArray(g.variants) || g.variants.length < 2) return '';
  const items = g.variants.map(v => `<li>
    ${getEvidenceBadgeHTML(v.certainty)} <span>${escapeHTML(v.label || '')}</span>
    <strong>${escapeHTML(v.title || '')}</strong>
    <div>${escapeHTML((v.summary || '').slice(0, 120))}${(v.summary || '').length > 120 ? '…' : ''}</div>
  </li>`).join('');
  return `<div class="map-variant-box">
    <button type="button" class="map-variant-toggle" id="map-variant-toggle">⚖ 同一史实有 ${g.variants.length} 种来源记载（点击展开对比）</button>
    <ul class="map-variant-list hidden" id="map-variant-list">${items}</ul>
  </div>`;
}

function updateEventPanel(event) {
  if (!event) return;
  const panel = document.getElementById('event-panel');
  const title = document.getElementById('panel-title');
  const content = document.getElementById('panel-content');
  const force = getSubject(event.forceId) || {};

  title.textContent = getEventTitle(event);
  content.innerHTML = `
    <div class="event-badges-row">
      ${getEvidenceBadgeHTML(event.certainty)}
      ${getPrecisionBadgeHTML(event.datePrecision)}
      ${getLayerBadgeHTML(event.layer)}
    </div>
    <div class="event-meta event-meta-compact event-meta-grid-2x2">
      <div class="event-meta-item"><span class="event-meta-label">${t('time')}</span><span class="event-meta-value">${escapeHTML(getDisplayDate(event))}</span></div>
      <div class="event-meta-item"><span class="event-meta-label">${t('force')}</span><span class="event-meta-value"><span class="force-dot" style="background:${escapeAttr(force.color || '#777')}"></span>${escapeHTML(getSubjectName(force))}</span></div>
      <div class="event-meta-item"><span class="event-meta-label">${t('type')}</span><span class="event-meta-value"><span class="event-type-badge" style="background:${escapeAttr(force.color || '#757575')}">${escapeHTML(getTypeLabel(event.type))}</span></span></div>
      <div class="event-meta-item"><span class="event-meta-label">${t('place')}</span><span class="event-meta-value">${escapeHTML(getLocationName(event))}</span></div>
    </div>
    <div class="event-description">${escapeHTML(getEventDescription(event))}</div>
    ${Array.isArray(event.participants) && event.participants.length ? `<div class="event-participants"><h4>${t('participants')}</h4><div class="participant-tags">${event.participants.map(p => `<span class="participant-tag clickable${highlightedPerson === p ? ' active' : ''}" data-person-hl="${escapeAttr(p)}" title="点击在地图上高亮该人物轨迹">${escapeHTML(p)}</span>`).join('')}</div></div>` : ''}
    ${renderEventSourcesHTML(event)}
    ${renderMapVariantHTML(event)}`;
  content.querySelectorAll('[data-person-hl]').forEach(tag => {
    tag.addEventListener('click', () => {
      const name = tag.dataset.personHl || '';
      highlightedPerson = highlightedPerson === name ? '' : name;
      updateFilterSummary();
      refreshAllMarkerIcons();
      updateEventPanel(event);
    });
  });
  document.getElementById('map-variant-toggle')?.addEventListener('click', () => {
    document.getElementById('map-variant-list')?.classList.toggle('hidden');
  });
  panel.classList.add('show');
}
function getPopupHTML(event, force) {
  const firstSrc = (event.sourceIds || []).map(id => sourceById.get(id)?.title).filter(Boolean)[0] || '';
  return `<div class="popup-card"><h4 style="color:${escapeAttr(force.isEnemy ? '#777' : (force.color || '#555'))}">${escapeHTML(getEventTitle(event))}</h4><p>${getEvidenceBadgeHTML(event.certainty)} ${escapeHTML(getDisplayDate(event))}｜${escapeHTML(getSubjectName(force))}｜${escapeHTML(getTypeLabel(event.type))}</p><p>${escapeHTML(getLocationName(event))}</p><p class="popup-desc">${escapeHTML(getEventDescription(event)).slice(0,105)}${getEventDescription(event).length > 105 ? '……' : ''}</p>${firstSrc ? `<p style="font-size:11px;color:#6e6658;margin-top:5px;">出处：${escapeHTML(firstSrc)}</p>` : ''}</div>`;
}

function updateStats(activeDisplayedEvents = null, allDisplayedEvents = null) {
  if (!sortedEvents.length) return;
  if (!allDisplayedEvents) allDisplayedEvents = sortedEvents.slice(0, currentSortedIndex + 1);
  if (!activeDisplayedEvents) activeDisplayedEvents = allDisplayedEvents.filter(e => activeForces.has(e.forceId));
  const redDisplayed = allDisplayedEvents.filter(e => !getSubject(e.forceId)?.isEnemy);
  const redActive = activeDisplayedEvents.filter(e => !getSubject(e.forceId)?.isEnemy);
  const statsModel = marchData.statsModel || {};
  const startDate = new Date(statsModel.startDate || sortedEvents[0].date);
  const endDate = new Date(statsModel.endDate || sortedEvents[sortedEvents.length-1].date);
  const currentDate = new Date(sortedEvents[currentSortedIndex].date);
  const totalDays = Math.max(1, Math.round((endDate - startDate) / 86400000) + 1);
  const elapsedDays = Math.max(1, Math.round((currentDate - startDate) / 86400000) + 1);
  const progress = Math.max(0, Math.min(1, elapsedDays / totalDays));

  const joinedFromEvents = sumMetric(redDisplayed, 'redJoined');
  const joined = Math.min(statsModel.overallParticipantsApprox || 200000, Math.max(joinedFromEvents, Math.round((statsModel.overallParticipantsApprox || 200000) * progress * .72)));
  const knownLosses = sumMetric(redDisplayed, 'redLosses');
  const finalLoss = statsModel.overallLossesApprox || 150000;
  const losses = Math.min(finalLoss, Math.max(knownLosses, Math.round(finalLoss * Math.pow(progress, 1.18))));
  const enemyDefeated = sumMetric(redDisplayed, 'enemyDefeated');
  const victories = redDisplayed.filter(e => e.metrics?.victory || (['战役','战斗','突围'].includes(e.type) && /胜|捷|攻克|突破|歼|击退|打开|跳出/.test(`${e.title || ''}${e.result || ''}`))).length;
  const distance = estimateDistanceLi(redDisplayed, currentDate);

  setText('stat-joined', currentLang === 'zh' ? `${t('approx')}${formatWan(joined)}` : `~${formatNumber(joined)}`);
  setText('stat-loss', currentLang === 'zh' ? `${t('approx')}${formatWan(losses)}` : `~${formatNumber(losses)}`);
  setText('stat-victory', `${victories}`);
  setText('stat-enemy', enemyDefeated ? (currentLang === 'zh' ? `${t('approx')}${formatNumber(enemyDefeated)}` : `~${formatNumber(enemyDefeated)}`) : '—');
  setText('stat-distance', currentLang === 'zh' ? `${formatNumber(distance)}${t('li')}` : `${formatNumber(distance)} ${t('li')}`);
  setText('stat-duration', currentLang === 'zh' ? `${elapsedDays}${t('days')}` : `${elapsedDays} ${t('days')}`);
  setText('joined-label', t('joinedLabel')); setText('loss-label', t('lossLabel')); setText('victory-label', t('victoryLabel')); setText('enemy-label', t('enemyLabel')); setText('distance-label', t('distanceLabel')); setText('duration-label', t('durationLabel'));
  setText('stats-note', t('statsNote'));
}
function sumMetric(events, key) { return events.reduce((sum, e) => sum + Number(e.metrics?.[key] || 0), 0); }
function estimateDistanceLi(redDisplayed, currentDate) {
  const explicit = Math.max(0, ...redDisplayed.map(e => Number(e.metrics?.distanceLi || 0)));
  const centralStart = new Date('1934-10-10');
  const centralEnd = new Date('1935-10-19');
  const final = marchData.statsModel?.centralDistanceLi || 25000;
  if (currentDate >= centralEnd) return final;
  if (currentDate <= centralStart) return Math.max(0, explicit);
  const p = Math.max(0, Math.min(1, (currentDate - centralStart) / (centralEnd - centralStart)));
  return Math.max(explicit, Math.round(final * p));
}
function setText(id, value) { const el = document.getElementById(id); if (el) el.textContent = value; }

function getEventTitle(event) { return currentLang === 'en' ? (event.titleEn || TITLE_EN_FALLBACK[event.title] || event.title) : event.title; }
function getEventDescription(event) { return currentLang === 'en' ? (event.descriptionEn || event.description || '') : (event.description || ''); }
function getSubjectName(force) { if (!force) return ''; return currentLang === 'en' ? (force.shortNameEn || force.nameEn || force.shortName || force.name || force.id) : (force.shortName || force.name || force.id); }
function getLocationName(event) { return currentLang === 'en' ? (event.location?.nameEn || event.location?.name || '') : (event.location?.name || ''); }
function getTypeLabel(type) { return currentLang === 'en' ? (TYPE_LABELS_EN[type] || type) : type; }
function getDisplayDate(event) { return currentLang === 'en' ? formatDateEn(event.date) : formatDateCompact(event.date); }
function getSubject(id) { return marchData.subjects.find(s => s.id === id); }
function groupBy(items, fn) { return items.reduce((acc, item) => { const key = fn(item); (acc[key] ||= []).push(item); return acc; }, {}); }
function sortEventAscending(a,b) { return new Date(a.date) - new Date(b.date) || Number(a.sequence || 0) - Number(b.sequence || 0) || (a._globalOrder || 0) - (b._globalOrder || 0); }
function formatDateZh(dateStr) { const d = parseDate(dateStr); return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`; }
function formatDateCompact(dateStr) { const d = parseDate(dateStr); return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`; }
function formatDateEn(dateStr) { const d = parseDate(dateStr); return d.toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric' }); }
function parseDate(dateStr) { const m = String(dateStr || '').match(/^(\d{4})-(\d{2})-(\d{2})$/); if (m) return new Date(Number(m[1]), Number(m[2])-1, Number(m[3])); return new Date(dateStr); }
function formatWan(n) { n = Math.round(Number(n) || 0); return n >= 10000 ? `${(n/10000).toFixed(n >= 100000 ? 0 : 1)}万` : formatNumber(n); }
function formatNumber(n) { return Math.round(Number(n) || 0).toLocaleString(currentLang === 'zh' ? 'zh-CN' : 'en-US'); }
function escapeHTML(value) { return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;'); }
function escapeAttr(value) { return escapeHTML(value).replaceAll('`','&#096;'); }
function hideLoading() { document.getElementById('loading')?.classList.add('hidden'); }
function showLoadingError(err) { const loading = document.getElementById('loading'); if (!loading) return; loading.innerHTML = `<div class="loading-error"><h2>数据加载失败</h2><p>${escapeHTML(err.message || err)}</p><p>请使用项目根目录的 <code>start_server.bat</code> 启动。</p></div>`; }

/* ===== 烈士纪念设施图层（数据自主 GeoJSON，无外部 API key）===== */
let memorialLayer = null;
let memorialData = null;
let memorialVisible = false;

async function initMemorialLayer() {
  const btn = document.getElementById('memorial-toggle');
  if (!btn) return;
  try {
    const res = await fetch('data/memorial_sites.geojson?t=' + Date.now(), { cache: 'no-store' });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    memorialData = await res.json();
  } catch (err) {
    btn.disabled = true;
    btn.textContent = '◈ 纪念设施数据缺失';
    return;
  }
  btn.addEventListener('click', ev => {
    ev.preventDefault();
    memorialVisible = !memorialVisible;
    btn.setAttribute('aria-pressed', String(memorialVisible));
    btn.classList.toggle('active', memorialVisible);
    if (memorialVisible) showMemorialLayer(); else hideMemorialLayer();
  });
}

function showMemorialLayer() {
  if (!map || !memorialData) return;
  if (memorialLayer) { hideMemorialLayer(); }
  memorialLayer = L.layerGroup().addTo(map);
  (memorialData.features || []).forEach(f => {
    const p = f.properties || {};
    const c = f.geometry?.coordinates || [];
    if (c.length < 2) return;
    const [lng, lat] = c;
    const marker = L.circleMarker([lat, lng], {
      radius: 6,
      color: '#7f1618',
      weight: 2,
      fillColor: '#bd2427',
      fillOpacity: 0.85
    });
    const name = currentLang === 'en' ? (p.nameEn || p.name) : p.name;
    const lines = [
      `<strong>${escapeHTML(name)}</strong>`,
      `<div class="memorial-pop-loc">${escapeHTML(currentLang === 'en' ? (p.location || '') : (p.location || ''))}</div>`,
      `<div class="memorial-pop-meta">${escapeHTML(p.nationalList || '')} · ${escapeHTML(p.related || '')}</div>`,
      `<div class="memorial-pop-note">${escapeHTML(p.precision || '')}</div>`
    ];
    marker.bindPopup(lines.join(''), { maxWidth: 260 });
    marker.bindTooltip(escapeHTML(name), { direction: 'top', offset: [0, -6] });
    marker.addTo(memorialLayer);
  });
}

function hideMemorialLayer() {
  if (memorialLayer && map) { map.removeLayer(memorialLayer); memorialLayer = null; }
}

window.marchMap = {
  data: () => marchData,
  sortedEvents: () => sortedEvents,
  allEvents: () => allNormalizedEvents,
  scopeMode: () => scopeMode,
  evidenceMode: () => evidenceMode,
  setScope: mode => { scopeMode = mode; syncMapFilterButtons(); rebuildVisibleEvents(); renderCurrentState(false); },
  setEvidence: mode => { evidenceMode = mode; syncMapFilterButtons(); rebuildVisibleEvents(); renderCurrentState(false); },
  showEvent: index => { currentSortedIndex = Math.max(0, Math.min(sortedEvents.length - 1, Number(index) || 0)); renderCurrentState(true); },
  activeForces: () => [...activeForces],
  memorialSites: () => memorialData
};



/**
 * 红军长征星火路线 v5
 * - 数据源：data/long_march_events.json
 * - 播放：全局时间顺序
 * - 连线：只连接同一部队/路线
 * - 色彩：按部队统一，不再按事件类型染色
 * - 节点：取消内部文字，减少地图噪音；最新节点更大且置顶
 * - 特效：会师、牺牲、七律诗句、敌军围堵触发叙事横幅
 */

const DATA_URL = 'data/long_march_events.json';
const TILE_URL = 'https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=7&x={x}&y={y}&z={z}';

let map = null;
let marchData = null;
let sortedEvents = [];
let currentSortedIndex = 0;
let activeForces = new Set();
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
  '出发': '启程', '启程': '启程', '到达': '到达', '战役': '战役', '战斗': '战斗',
  '会议': '会议', '会师': '会师', '牺牲': '牺牲', '出生': '诞生', '诞生': '诞生',
  '民族工作': '民族', '民族': '民族', '根据地': '根据', '根据': '根据',
  '渡河': '渡河', '转移': '转进', '行军': '行军', '转进': '转进',
  '整编': '整编', '自然险阻': '险阻', '险阻': '险阻', '雪山': '雪山', '草地': '草地',
  '分歧': '分歧', '转折': '转折', '决策': '决策', '总结': '胜利', '胜利': '胜利',
  '生活': '生活', '追堵': '追堵', '封锁': '封锁', '空袭': '空袭', '围堵': '围堵',
  '突围': '突围', '其他': '其他'
};

const TYPE_LABELS_EN = {
  '启程':'Start','到达':'Arrive','战役':'Campaign','战斗':'Battle','会议':'Meeting','会师':'Meet',
  '牺牲':'Sacrifice','诞生':'Birth','民族':'Alliance','根据':'Base','渡河':'River','转进':'March',
  '行军':'March','整编':'Reorg','险阻':'Hazard','雪山':'Snow','草地':'Grassland','分歧':'Split',
  '转折':'Turn','决策':'Decision','胜利':'Victory','生活':'Life','追堵':'Pursuit','封锁':'Blockade',
  '空袭':'Air raid','围堵':'Encircle','突围':'Breakout','其他':'Other'
};

const UI = {
  zh: {
    appTitle: '红军长征星火路线',
    subtitle: '多路红军星火铺开 · 突破围追堵截 · 最终大会师',
    routes: '路线', all: '全选', clear: '清空', speed: '速度', editor: '本地数据编辑',
    statsTitle: '动态统计', joinedLabel: '参征人数', lossLabel: '损失人数', victoryLabel: '胜利节点', enemyLabel: '歼俘敌', distanceLabel: '里程推进', durationLabel: '历时',
    statsNote: '统计为史实口径与节点累积结合：参征/损失为约数，歼俘敌只汇总有明确数字的节点。',
    detail: '事件详情', time: '时间', force: '路线', type: '类型', place: '地点', result: '结果', casualties: '损失', participants: '人物 / 群体',
    loading: '正在加载长征数据...', langBtn: 'English', days: '天', li: '里', approx: '约',
    meetingKicker: '会师', meetingSubtitle: '分散的星火汇流，长征胜利向前推进。',
    sacrificeKicker: '牺牲', sacrificeSubtitle: '以生命守护队伍前行，壮烈不应被路线遮蔽。',
    enemyKicker: '围堵', enemySubtitle: '敌军围追堵截形成压迫，红军在夹缝中机动突围。',
    poemKicker: '七律·长征', poemSubtitle: '诗句在这里落到山川、河流与行军现场。'
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
    poemKicker: 'Qilu · Long March', poemSubtitle: 'A poetic line meets the actual mountains and rivers on the route.'
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
    prepareData();
    initMap();
    initForcePanel();
    initTimeline();
    bindPanelClose();
    bindLanguageToggle();
    applyLanguage();
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

function prepareData() {
  if (!marchData || !Array.isArray(marchData.subjects) || !Array.isArray(marchData.events)) throw new Error('数据格式错误：必须包含 subjects 与 events。');
  marchData.subjects.forEach(s => { if (s.id === 'enemy_kmt') s.isEnemy = true; });
  const forceIds = new Set(marchData.subjects.filter(s => s.type === 'force').map(s => s.id));
  const seen = new Set();
  marchData.events = marchData.events.filter(e => {
    if (!e || !e.id || !e.date || !e.forceId || !e.location || !Array.isArray(e.location.coordinates)) return false;
    if (!forceIds.has(e.forceId)) return false;
    const key = `${e.date}|${e.forceId}|${e.title}|${e.location.name}`;
    if (seen.has(e.id) || seen.has(key)) return false;
    seen.add(e.id); seen.add(key);
    e.type = normalizeType(e.type);
    return true;
  });
  sortedEvents = [...marchData.events].sort((a,b) => new Date(a.date) - new Date(b.date) || Number(a.sequence || 0) - Number(b.sequence || 0) || String(a.id).localeCompare(String(b.id),'zh-CN'));
  sortedEvents.forEach((e, idx) => e._globalOrder = idx + 1);
  activeForces = new Set(marchData.subjects.filter(s => s.type === 'force').map(s => s.id));
  currentSortedIndex = 0;
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
  getForcesSorted().forEach(force => {
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
function applyLanguage() { document.querySelectorAll('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n)); document.title = t('appTitle'); const btn = document.getElementById('lang-toggle'); if (btn) btn.textContent = t('langBtn'); updateTimelineLabels(); }
function stepTimeline(delta) { const next = Math.max(0, Math.min(sortedEvents.length - 1, currentSortedIndex + delta)); if (next !== currentSortedIndex) { currentSortedIndex = next; renderCurrentState(true); } }
function togglePlay() { playTimer ? stopPlay() : startPlay(); }
function getPlaybackDelay(event) {
  const base = Math.max(1200, 2600 / playSpeed);
  return event?.type === '会师' ? Math.max(base + 2200, 4400) : base;
}
function startPlay() {
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

function reconcileRoutes(events) {
  const wanted = new Set();
  const byForce = groupBy(events, e => e.forceId);
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
  candidates.forEach((c, idx) => {
    const color = c.force.isEnemy ? '#777' : (c.force.color || '#555');
    const cls = ['location-label', c.event.type === '会师' ? 'location-label-meeting' : '', c.event.poem ? 'location-label-poem' : '', c.force.isEnemy ? 'location-label-enemy' : ''].join(' ');
    const html = `<div class="${cls}" style="--label-color:${escapeAttr(color)}"><span>${escapeHTML(c.text)}</span></div>`;
    const icon = L.divIcon({ className:'location-label-wrapper', html, iconSize:null, iconAnchor:[-10, 28] });
    const adjusted = offsetCoordinates(c.coords, idx % 4);
    if (!labelByKey.has(c.key)) {
      const marker = L.marker(adjusted, { icon, interactive:false, zIndexOffset: c.event.type === '会师' ? 9000 : 6200 }).addTo(map);
      labelByKey.set(c.key, { marker, html });
    } else {
      const rec = labelByKey.get(c.key);
      rec.marker.setLatLng(adjusted);
      if (rec.html !== html) { rec.marker.setIcon(icon); rec.html = html; }
    }
  });
  for (const [key, rec] of [...labelByKey.entries()]) {
    if (!wanted.has(key)) { map.removeLayer(rec.marker); labelByKey.delete(key); }
  }
}

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
  const key = [current?'current':'', latest?'latest':'', meeting?'meeting':'', sacrifice?'sacrifice':'', enemy?'enemy':'', poem?'poem':'', currentLang, currentZoom].join('|');
  const zIndex = enemy ? 500 : current ? 10000 : latest ? 8500 : meeting ? 7600 : sacrifice ? 7300 : poem ? 7000 : 1000 + event._globalOrder;
  return { current, latest, meeting, sacrifice, enemy, poem, key, zIndex };
}
function refreshAllMarkerIcons() { markerById.forEach(rec => rec.statusKey = 'refresh'); renderCurrentState(false); }
function makeEventIcon(event, force, status) {
  const size = getMarkerSize(status);
  const color = status.enemy ? '#777' : (force.color || '#555');
  const cls = ['event-marker', status.current?'event-marker-current':'', status.latest?'event-marker-latest':'', status.meeting?'event-marker-meeting':'', status.sacrifice?'event-marker-sacrifice':'', status.enemy?'event-marker-enemy':'', status.poem?'event-marker-poem':''].join(' ');
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
  else if (force.isEnemy && ['追堵','封锁','围堵','空袭'].includes(event.type)) { show = true; kicker = t('enemyKicker'); subtitle = t('enemySubtitle'); radius = 56000; color = '#777'; }
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
  const html = `<div class="meeting-flag"><div class="flag-pole"></div><div class="flag-cloth">★</div></div>`;
  const icon = L.divIcon({ className:'meeting-flag-wrapper', html, iconSize:[56,72], iconAnchor:[12,66] });
  meetingFlagLayer = L.marker(event.location.coordinates, { icon, interactive:false, zIndexOffset: 12000 }).addTo(map);
  window.clearTimeout(showMeetingFlag._timer);
  showMeetingFlag._timer = window.setTimeout(() => {
    if (meetingFlagLayer) { map.removeLayer(meetingFlagLayer); meetingFlagLayer = null; }
  }, 4300);
}

function offsetCoordinates(coords, count) { if (count === 0) return coords; const angle = (count * 47) * Math.PI / 180; const radius = .022 + Math.floor(count / 6) * .012; return [coords[0] + Math.sin(angle) * radius, coords[1] + Math.cos(angle) * radius]; }

function updateTimelineDisplay() { const event = sortedEvents[currentSortedIndex]; if (!event) return; document.getElementById('timeline-slider').value = currentSortedIndex; document.getElementById('current-date').textContent = getDisplayDate(event); document.getElementById('current-event-title').textContent = getEventTitle(event); }
function updateEventPanel(event) {
  if (!event) return;
  const panel = document.getElementById('event-panel');
  const title = document.getElementById('panel-title');
  const content = document.getElementById('panel-content');
  const force = getSubject(event.forceId) || {};
  title.textContent = getEventTitle(event);
  content.innerHTML = `
    <div class="event-meta">
      <div class="event-meta-item"><span class="event-meta-label">${t('time')}</span><span class="event-meta-value">${escapeHTML(getDisplayDate(event))}</span></div>
      <div class="event-meta-item"><span class="event-meta-label">${t('force')}</span><span class="event-meta-value"><span class="force-dot" style="background:${escapeAttr(force.color || '#777')}"></span>${escapeHTML(getSubjectName(force))}</span></div>
      <div class="event-meta-item"><span class="event-meta-label">${t('type')}</span><span class="event-meta-value"><span class="event-type-badge" style="background:${escapeAttr(force.color || '#757575')}">${escapeHTML(getTypeLabel(event.type))}</span></span></div>
      <div class="event-meta-item"><span class="event-meta-label">${t('place')}</span><span class="event-meta-value">${escapeHTML(getLocationName(event))}</span></div>
      ${event.result ? `<div class="event-meta-item"><span class="event-meta-label">${t('result')}</span><span class="event-meta-value">${escapeHTML(event.result)}</span></div>` : ''}
      ${event.casualties ? `<div class="event-meta-item"><span class="event-meta-label">${t('casualties')}</span><span class="event-meta-value">${escapeHTML(event.casualties)}</span></div>` : ''}
    </div>
    ${event.poem ? `<div class="poem-card"><div class="poem-line">${escapeHTML(event.poem.line || '')}</div><div class="poem-title">${escapeHTML(event.poem.title || '')}</div><div class="poem-text">${escapeHTML(event.poem.text || '')}</div></div>` : ''}
    <div class="event-description">${escapeHTML(getEventDescription(event))}</div>
    ${Array.isArray(event.participants) && event.participants.length ? `<div class="event-participants"><h4>${t('participants')}</h4><div class="participant-tags">${event.participants.map(p => `<span class="participant-tag">${escapeHTML(p)}</span>`).join('')}</div></div>` : ''}`;
  panel.classList.add('show');
}
function getPopupHTML(event, force) { return `<div class="popup-card"><h4 style="color:${escapeAttr(force.isEnemy ? '#777' : (force.color || '#555'))}">${escapeHTML(getEventTitle(event))}</h4><p>${escapeHTML(getDisplayDate(event))}｜${escapeHTML(getSubjectName(force))}｜${escapeHTML(getTypeLabel(event.type))}</p><p>${escapeHTML(getLocationName(event))}</p><p class="popup-desc">${escapeHTML(getEventDescription(event)).slice(0,105)}${getEventDescription(event).length > 105 ? '……' : ''}</p></div>`; }

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
function getDisplayDate(event) { return currentLang === 'en' ? formatDateEn(event.date) : formatDateZh(event.date); }
function getSubject(id) { return marchData.subjects.find(s => s.id === id); }
function groupBy(items, fn) { return items.reduce((acc, item) => { const key = fn(item); (acc[key] ||= []).push(item); return acc; }, {}); }
function sortEventAscending(a,b) { return new Date(a.date) - new Date(b.date) || Number(a.sequence || 0) - Number(b.sequence || 0) || (a._globalOrder || 0) - (b._globalOrder || 0); }
function formatDateZh(dateStr) { const d = parseDate(dateStr); return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`; }
function formatDateEn(dateStr) { const d = parseDate(dateStr); return d.toLocaleDateString('en-US', { year:'numeric', month:'short', day:'numeric' }); }
function parseDate(dateStr) { const m = String(dateStr || '').match(/^(\d{4})-(\d{2})-(\d{2})$/); if (m) return new Date(Number(m[1]), Number(m[2])-1, Number(m[3])); return new Date(dateStr); }
function formatWan(n) { n = Math.round(Number(n) || 0); return n >= 10000 ? `${(n/10000).toFixed(n >= 100000 ? 0 : 1)}万` : formatNumber(n); }
function formatNumber(n) { return Math.round(Number(n) || 0).toLocaleString(currentLang === 'zh' ? 'zh-CN' : 'en-US'); }
function escapeHTML(value) { return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;'); }
function escapeAttr(value) { return escapeHTML(value).replaceAll('`','&#096;'); }
function hideLoading() { document.getElementById('loading')?.classList.add('hidden'); }
function showLoadingError(err) { const loading = document.getElementById('loading'); if (!loading) return; loading.innerHTML = `<div class="loading-error"><h2>数据加载失败</h2><p>${escapeHTML(err.message || err)}</p><p>请使用项目根目录的 <code>start_server.bat</code> 启动。</p></div>`; }

window.marchMap = { data: () => marchData, sortedEvents: () => sortedEvents, showEvent: index => { currentSortedIndex = Math.max(0, Math.min(sortedEvents.length - 1, Number(index) || 0)); renderCurrentState(true); }, activeForces: () => [...activeForces] };

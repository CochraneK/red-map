const DATA_URL = 'data/long_march_events.json';

let museumData = null;
let selectedPersonId = '';
let martyrFilter = 'all';
let personTypeFilter = 'all';
let catalogModule = 'persons';
let catalogQuery = '';

document.addEventListener('DOMContentLoaded', initMuseum);

async function initMuseum() {
  try {
    const res = await fetch(`${DATA_URL}?v=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`数据加载失败：${res.status}`);
    museumData = await res.json();
    selectedPersonId = getDefaultPersonId();
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
    <a class="panel-action" href="${escapeAttr(exhibit.actionHref || 'index.html')}">${escapeHTML(exhibit.actionLabel || '打开地图')}</a>`;
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
    renderModuleCatalog();
  }));
  search.value = catalogQuery;
  search.oninput = () => {
    catalogQuery = search.value.trim();
    renderCatalogContent();
  };
  renderCatalogContent();
}

function renderCatalogContent() {
  const stats = document.getElementById('catalog-stats');
  const grid = document.getElementById('catalog-grid');
  if (!stats || !grid) return;
  const items = getCatalogItems(catalogModule);
  const shown = filterCatalogItems(items);
  stats.innerHTML = catalogStats(items, shown);
  grid.innerHTML = shown.length ? shown.map(item => catalogCard(item)).join('') : `<div class="catalog-empty">没有匹配的资料模块</div>`;
  bindCatalogCards();
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
  if (!query) return items;
  return items.filter(item => normalizeCatalogQuery(item.searchText).includes(query));
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
    ${firstEvent ? `<a class="module-action" href="index.html#event=${encodeURIComponent(firstEvent.id)}">地图定位</a>` : ''}
  </article>`;
}

function eventCatalogCard(item) {
  return `<article class="catalog-card" style="--accent:${escapeAttr(item.accent)}">
    <div class="module-kicker"><span>${escapeHTML(item.subtitle)}</span><strong>${escapeHTML(formatDate(item.event.date))}</strong></div>
    <h3>${escapeHTML(item.title)}</h3>
    <p>${escapeHTML(item.body)}</p>
    ${moduleMeta(item.chips.slice(1))}
    ${moduleTags(item.tags)}
    <a class="module-action" href="index.html#event=${encodeURIComponent(item.id)}">地图查看</a>
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
      catalogQuery = subject?.shortName || subject?.name || button.dataset.catalogForce || '';
      renderModuleCatalog();
      document.getElementById('catalog')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
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
  renderPersonTypeFilters();
  const persons = getFilteredPersons();
  if (!persons.some(person => person.id === selectedPersonId)) selectedPersonId = persons[0]?.id || museumData.persons[0]?.id || '';
  list.innerHTML = persons.map(person => `<button class="${person.id === selectedPersonId ? 'active' : ''}" data-person-id="${escapeAttr(person.id)}">
    <span>${escapeHTML(person.name)}</span><small>${escapeHTML(person.personType || '人物')}</small>
  </button>`).join('');
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
    ['可信度', person.certainty || 'medium'],
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
      <h4>${escapeHTML(event.title)}</h4>
      <p>${escapeHTML(rel.note || event.description || '')}</p>
      <a href="index.html#event=${encodeURIComponent(event.id)}">在路线地图中查看</a>
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
  const box = document.getElementById('archive-grid');
  if (!box) return;
  box.innerHTML = museumData.museum.artifacts.map(artifact => `<article class="archive-tile">
    <h3>${escapeHTML(artifact.title)}</h3>
    <p>${escapeHTML(artifact.summary)}</p>
    <div class="tile-meta"><span>${escapeHTML(artifact.artifactType || 'archive')}</span><span>${escapeHTML(artifact.certainty || 'medium')}</span></div>
  </article>`).join('');
}

function renderMethod() {
  const box = document.getElementById('method-grid');
  if (!box) return;
  const steps = [
    ['研究材料', '事件、人物、地点、来源先进入表格，保留口径和可信度。'],
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
  return `<article class="event-tile">${imageFigure(visual, 'tile-image')}<h3>${escapeHTML(event.title)}</h3><p>${escapeHTML(event.description)}</p><div class="tile-meta"><span>${escapeHTML(event.date)}</span><span>${escapeHTML(event.type)}</span><span>${escapeHTML(getSubject(event.forceId)?.shortName || '')}</span></div></article>`;
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
function getFilteredPersons() { return personTypeFilter === 'all' ? museumData.persons : museumData.persons.filter(p => (p.personType || '人物') === personTypeFilter); }
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

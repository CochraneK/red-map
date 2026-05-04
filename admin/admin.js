const DATA_URL = '../data/long_march_events.json';
const EVENT_TYPES = ['启程','到达','战役','战斗','会议','会师','牺牲','诞生','民族','根据','渡河','转进','行军','整编','险阻','雪山','草地','分歧','转折','决策','胜利','生活','追堵','封锁','空袭','围堵','突围','其他'];
let marchData = null;
let currentPage = 1;
let pageSize = 14;
let currentSubjectTab = 'all';

document.addEventListener('DOMContentLoaded', initAdmin);

async function initAdmin() {
  marchData = await loadData();
  normalizeData();
  bindNavigation(); bindFilters(); bindPagination(); bindModals(); bindImportExport();
  populateSelects(); renderEventsTable(); renderSubjectsGrid();
}
async function loadData() { const res = await fetch(`${DATA_URL}?v=${Date.now()}`, {cache:'no-store'}); if (!res.ok) throw new Error(`无法加载数据文件：${res.status}`); return await res.json(); }
function normalizeData() { marchData.subjects ||= []; marchData.events ||= []; marchData.sources ||= []; dedupeEvents(); sortData(); }
function sortData() { marchData.subjects.sort((a,b)=>(Number(a.sort||999)-Number(b.sort||999)) || String(a.id).localeCompare(String(b.id))); marchData.events.sort((a,b)=> new Date(a.date)-new Date(b.date) || Number(a.sequence||0)-Number(b.sequence||0) || String(a.id).localeCompare(String(b.id))); }
function dedupeEvents() { const seen = new Set(); marchData.events = marchData.events.filter(e => { const key = e.id || `${e.date}|${e.forceId}|${e.title}|${e.location?.name}`; if (seen.has(key)) return false; seen.add(key); return true; }); }

function bindNavigation() { document.querySelectorAll('.nav-item').forEach(item => item.addEventListener('click', ev => { ev.preventDefault(); const section = item.dataset.section; document.querySelectorAll('.nav-item').forEach(i=>i.classList.remove('active')); document.querySelectorAll('.content-section').forEach(s=>s.classList.remove('active')); item.classList.add('active'); document.getElementById(`${section}-section`)?.classList.add('active'); })); }
function bindFilters() { ['sort-select','filter-subject','filter-type','search-input'].forEach(id => document.getElementById(id)?.addEventListener('input', () => { currentPage = 1; renderEventsTable(); })); document.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', () => { currentSubjectTab = btn.dataset.type; document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); renderSubjectsGrid(); })); }
function bindPagination() { document.getElementById('prev-page')?.addEventListener('click', () => { currentPage = Math.max(1, currentPage-1); renderEventsTable(); }); document.getElementById('next-page')?.addEventListener('click', () => { const total = Math.max(1, Math.ceil(getFilteredEvents().length / pageSize)); currentPage = Math.min(total, currentPage+1); renderEventsTable(); }); document.getElementById('page-jump-btn')?.addEventListener('click', () => { const total = Math.max(1, Math.ceil(getFilteredEvents().length / pageSize)); currentPage = Math.max(1, Math.min(total, Number(document.getElementById('page-jump-input').value || 1))); renderEventsTable(); }); }
function bindModals() { document.getElementById('add-event-btn')?.addEventListener('click', () => openEventModal()); document.getElementById('save-event-btn')?.addEventListener('click', saveEventFromForm); document.getElementById('add-subject-btn')?.addEventListener('click', () => openSubjectModal()); document.getElementById('save-subject-btn')?.addEventListener('click', saveSubjectFromForm); document.querySelectorAll('.modal-close,.modal-cancel').forEach(btn => btn.addEventListener('click', closeModals)); document.querySelectorAll('.modal').forEach(modal => modal.addEventListener('click', ev => { if (ev.target === modal) closeModals(); })); }
function bindImportExport() { document.getElementById('export-json-btn')?.addEventListener('click', exportJSON); document.getElementById('export-csv-btn')?.addEventListener('click', exportCSV); document.getElementById('import-file')?.addEventListener('change', importJSONFile); document.getElementById('import-paste-btn')?.addEventListener('click', importPastedRows); }

function populateSelects() {
  const subjects = getForceSubjects();
  ['filter-subject','event-subject'].forEach(id => { const select = document.getElementById(id); if (!select) return; const first = id === 'filter-subject' ? '<option value="">全部主体</option>' : ''; select.innerHTML = first + subjects.map(s => `<option value="${escapeAttr(s.id)}">${escapeHTML(s.shortName || s.name || s.id)}（${escapeHTML(s.id)}）</option>`).join(''); });
  ['filter-type','event-type'].forEach(id => { const select = document.getElementById(id); if (!select) return; const first = id === 'filter-type' ? '<option value="">全部类型</option>' : ''; select.innerHTML = first + EVENT_TYPES.map(t => `<option value="${escapeAttr(t)}">${escapeHTML(t)}</option>`).join(''); });
}
function getForceSubjects() { return marchData.subjects.filter(s => s.type === 'force').sort((a,b)=>(Number(a.sort||999)-Number(b.sort||999)) || String(a.id).localeCompare(String(b.id))); }
function getSubject(id) { return marchData.subjects.find(s => s.id === id); }

function getFilteredEvents() {
  const subject = document.getElementById('filter-subject')?.value || '';
  const type = document.getElementById('filter-type')?.value || '';
  const q = (document.getElementById('search-input')?.value || '').trim().toLowerCase();
  const sort = document.getElementById('sort-select')?.value || 'date-asc';
  let rows = marchData.events.filter(e => {
    if (subject && e.forceId !== subject) return false;
    if (type && e.type !== type) return false;
    if (q) { const text = `${e.title||''} ${e.description||''} ${e.location?.name||''} ${(e.participants||[]).join(' ')}`.toLowerCase(); if (!text.includes(q)) return false; }
    return true;
  });
  rows.sort((a,b) => { if (sort === 'date-desc') return new Date(b.date) - new Date(a.date); if (sort === 'importance-desc') return Number(b.importance||0) - Number(a.importance||0); if (sort === 'title-asc') return String(a.title||'').localeCompare(String(b.title||''),'zh-CN'); return new Date(a.date)-new Date(b.date) || Number(a.sequence||0)-Number(b.sequence||0); });
  return rows;
}
function renderEventsTable() {
  const tbody = document.getElementById('events-tbody'); if (!tbody) return;
  const rows = getFilteredEvents(); const totalPages = Math.max(1, Math.ceil(rows.length / pageSize)); currentPage = Math.min(currentPage, totalPages);
  const pageRows = rows.slice((currentPage-1)*pageSize, currentPage*pageSize);
  tbody.innerHTML = pageRows.map(e => {
    const s = getSubject(e.forceId) || {};
    const desc = (e.description || '').slice(0, 62);
    return `<tr>
      <td><span class="date-cell">${escapeHTML(formatYYYYMMDD(e.date))}</span></td>
      <td><span class="force-pill"><span class="force-dot" style="background:${escapeAttr(s.color || '#777')}"></span>${escapeHTML(s.shortName || s.name || e.forceId)}</span></td>
      <td><span class="type-badge">${escapeHTML(e.type || '')}</span></td>
      <td class="title-cell"><strong>${escapeHTML(e.title || '')}</strong><small>${escapeHTML(desc)}${(e.description || '').length > 62 ? '…' : ''}</small></td>
      <td class="place-cell">${escapeHTML(e.location?.name || '')}</td>
      <td>${escapeHTML(e.importance || '')}</td>
      <td><div class="action-cell"><button class="btn btn-sm btn-secondary" onclick="openEventModal('${escapeAttr(e.id)}')">编辑</button><button class="btn btn-sm btn-danger" onclick="deleteEvent('${escapeAttr(e.id)}')">删除</button></div></td>
    </tr>`;
  }).join('');
  document.getElementById('page-info').textContent = `第 ${currentPage} 页 / 共 ${totalPages} 页，共 ${rows.length} 条`;
  document.getElementById('page-jump-input').value = currentPage;
}

function renderSubjectsGrid() {
  const grid = document.getElementById('subjects-grid'); if (!grid) return;
  let subjects = marchData.subjects; if (currentSubjectTab !== 'all') subjects = subjects.filter(s => s.type === currentSubjectTab); subjects = [...subjects].sort((a,b)=>(Number(a.sort||999)-Number(b.sort||999)) || String(a.id).localeCompare(String(b.id)));
  grid.innerHTML = subjects.map(s => { const eventCount = marchData.events.filter(e => e.forceId === s.id || e.subjectId === s.id).length; return `<div class="subject-card">
    <div class="subject-card-header"><div class="subject-title"><span class="subject-color" style="background:${escapeAttr(s.color || '#777')}"></span><h3>${escapeHTML(s.name || '')}</h3></div><div class="subject-actions"><button class="btn btn-sm btn-secondary" onclick="openSubjectModal('${escapeAttr(s.id)}')">编辑</button><button class="btn btn-sm btn-danger" onclick="deleteSubject('${escapeAttr(s.id)}')">删除</button></div></div>
    <p><strong>ID：</strong>${escapeHTML(s.id)}　<strong>简称：</strong>${escapeHTML(s.shortName || '')}</p>
    <p><strong>类型：</strong>${escapeHTML(s.type || '')}　<strong>事件：</strong>${eventCount}</p>
    ${s.leader ? `<p><strong>人物：</strong>${escapeHTML(s.leader)}</p>` : ''}
    ${s.subUnits ? `<div class="subject-subunits">${splitList(s.subUnits).map(u => `<span>${escapeHTML(u)}</span>`).join('')}</div>` : ''}
    ${s.description ? `<p>${escapeHTML(s.description)}</p>` : ''}
  </div>`; }).join('');
}

function openEventModal(eventId = '') {
  const e = eventId ? marchData.events.find(x => x.id === eventId) : null;
  document.getElementById('event-modal-title').textContent = e ? '编辑事件' : '添加事件';
  setVal('event-id', e?.id || ''); setVal('event-date', e?.date ? formatYYYYMMDD(e.date) : ''); setVal('event-subject', e?.forceId || getForceSubjects()[0]?.id || ''); setVal('event-type', e?.type || '其他'); setVal('event-importance', e?.importance || 3); setVal('event-title', e?.title || ''); setVal('event-description', e?.description || ''); setVal('location-name', e?.location?.name || ''); setVal('location-lat', e?.location?.coordinates?.[0] ?? ''); setVal('location-lng', e?.location?.coordinates?.[1] ?? ''); setVal('event-participants', Array.isArray(e?.participants) ? e.participants.join('; ') : ''); setVal('event-result', e?.result || ''); setVal('event-casualties', e?.casualties || ''); setVal('metric-joined', e?.metrics?.redJoined || ''); setVal('metric-loss', e?.metrics?.redLosses || ''); setVal('metric-enemy', e?.metrics?.enemyDefeated || ''); setVal('metric-distance', e?.metrics?.distanceLi || ''); setVal('poem-line', e?.poem?.line || ''); setVal('poem-title', e?.poem?.title || ''); setVal('poem-text', e?.poem?.text || '');
  document.getElementById('event-modal').classList.add('show');
}
function saveEventFromForm() {
  let date; try { date = normalizeDateInput(getVal('event-date')); } catch (err) { alert(err.message); return; }
  const id = getVal('event-id') || makeEventId(date, getVal('event-subject'));
  const metrics = {}; addNumMetric(metrics,'redJoined','metric-joined'); addNumMetric(metrics,'redLosses','metric-loss'); addNumMetric(metrics,'enemyDefeated','metric-enemy'); addNumMetric(metrics,'distanceLi','metric-distance');
  const poemLine = getVal('poem-line'); const poem = poemLine ? { line: poemLine, title: getVal('poem-title'), text: getVal('poem-text') } : undefined;
  const ev = { id, date, displayDate: date, sequence: sequenceFromDate(date), forceId: getVal('event-subject'), type: getVal('event-type'), title: getVal('event-title').trim(), description: getVal('event-description').trim(), location: { name: getVal('location-name').trim(), coordinates: [Number(getVal('location-lat')), Number(getVal('location-lng'))] }, participants: splitList(getVal('event-participants')), importance: Number(getVal('event-importance') || 3), sourceIds: [], certainty: 'medium' };
  if (getVal('event-result')) ev.result = getVal('event-result'); if (getVal('event-casualties')) ev.casualties = getVal('event-casualties'); if (Object.keys(metrics).length) ev.metrics = metrics; if (poem) ev.poem = poem;
  if (!ev.forceId || !ev.title || !ev.location.name || !Number.isFinite(ev.location.coordinates[0]) || !Number.isFinite(ev.location.coordinates[1])) return alert('请完整填写主体、标题、地点、经纬度。');
  const idx = marchData.events.findIndex(x => x.id === id); if (idx >= 0) marchData.events[idx] = { ...marchData.events[idx], ...ev }; else marchData.events.push(ev);
  dedupeEvents(); sortData(); populateSelects(); renderEventsTable(); renderSubjectsGrid(); closeModals(); alert('已更新到当前浏览器内存。请导出 JSON 并替换 data/long_march_events.json。');
}
function deleteEvent(id) { if (!confirm('确认删除该事件？')) return; marchData.events = marchData.events.filter(e => e.id !== id); renderEventsTable(); renderSubjectsGrid(); }

function openSubjectModal(subjectId = '') {
  const s = subjectId ? getSubject(subjectId) : null;
  document.getElementById('subject-modal-title').textContent = s ? '编辑主体' : '添加主体';
  setVal('subject-original-id', s?.id || ''); setVal('subject-id', s?.id || ''); setVal('subject-type', s?.type || 'force'); setVal('subject-name', s?.name || ''); setVal('subject-short-name', s?.shortName || ''); setVal('subject-color', s?.color || '#d73027'); setVal('subject-sort', s?.sort || 99); setVal('subject-leader', s?.leader || ''); setVal('subject-subunits', s?.subUnits || ''); setVal('subject-subunits-en', s?.subUnitsEn || ''); setVal('subject-description', s?.description || ''); document.getElementById('subject-is-enemy').checked = Boolean(s?.isEnemy);
  document.getElementById('subject-modal').classList.add('show');
}
function saveSubjectFromForm() {
  const originalId = getVal('subject-original-id'); const id = getVal('subject-id').trim();
  if (!id || !/^[A-Za-z0-9_\-]+$/.test(id)) return alert('主体ID只能包含字母、数字、下划线或短横线。');
  if (!getVal('subject-name').trim()) return alert('请填写主体名称。');
  if (id !== originalId && marchData.subjects.some(s => s.id === id)) return alert('主体ID已存在。');
  const subject = { id, type: getVal('subject-type'), name: getVal('subject-name').trim(), shortName: getVal('subject-short-name').trim(), color: getVal('subject-color'), leader: getVal('subject-leader').trim(), subUnits: getVal('subject-subunits').trim(), subUnitsEn: getVal('subject-subunits-en').trim(), sort: Number(getVal('subject-sort') || 99), description: getVal('subject-description').trim() };
  if (document.getElementById('subject-is-enemy').checked) subject.isEnemy = true;
  const idx = marchData.subjects.findIndex(s => s.id === originalId);
  if (idx >= 0) marchData.subjects[idx] = { ...marchData.subjects[idx], ...subject }; else marchData.subjects.push(subject);
  if (originalId && originalId !== id) marchData.events.forEach(e => { if (e.forceId === originalId) e.forceId = id; });
  sortData(); populateSelects(); renderSubjectsGrid(); renderEventsTable(); closeModals(); alert('主体已更新，并已联动事件主体ID。请导出 JSON 后替换数据文件。');
}
function deleteSubject(id) { const count = marchData.events.filter(e => e.forceId === id || e.subjectId === id).length; if (count) return alert(`该主体仍关联 ${count} 条事件，不能删除。请先迁移或删除事件。`); if (!confirm('确认删除主体？')) return; marchData.subjects = marchData.subjects.filter(s => s.id !== id); populateSelects(); renderSubjectsGrid(); }

function closeModals() { document.querySelectorAll('.modal').forEach(m => m.classList.remove('show')); }
function exportJSON() { dedupeEvents(); sortData(); downloadFile('long_march_events.json', JSON.stringify(marchData, null, 2), 'application/json;charset=utf-8'); }
function exportCSV() { const headers = ['id','date','forceId','type','title','location','lat','lng','participants','importance','result','casualties','redJoined','redLosses','enemyDefeated','distanceLi','poemLine','poemTitle','poemText','description']; const lines = [headers.join(',')]; marchData.events.forEach(e => { const row = [e.id, formatYYYYMMDD(e.date), e.forceId, e.type, e.title, e.location?.name || '', e.location?.coordinates?.[0] ?? '', e.location?.coordinates?.[1] ?? '', (e.participants||[]).join('; '), e.importance || '', e.result || '', e.casualties || '', e.metrics?.redJoined || '', e.metrics?.redLosses || '', e.metrics?.enemyDefeated || '', e.metrics?.distanceLi || '', e.poem?.line || '', e.poem?.title || '', e.poem?.text || '', e.description || ''].map(csvEscape); lines.push(row.join(',')); }); downloadFile('long_march_events.csv', lines.join('\n'), 'text/csv;charset=utf-8'); }
function importJSONFile(ev) { const file = ev.target.files?.[0]; if (!file) return; const reader = new FileReader(); reader.onload = () => { try { const parsed = JSON.parse(reader.result); if (!Array.isArray(parsed.events) || !Array.isArray(parsed.subjects)) throw new Error('JSON 必须包含 subjects 和 events。'); marchData = parsed; normalizeData(); populateSelects(); renderEventsTable(); renderSubjectsGrid(); alert('已导入到当前浏览器内存。'); } catch (err) { alert(`导入失败：${err.message}`); } }; reader.readAsText(file, 'utf-8'); }
function importPastedRows() { const text = document.getElementById('import-textarea').value.trim(); if (!text) return alert('请粘贴数据。'); let imported = 0; parseDelimited(text).forEach(row => { if (row.length < 7) return; const [dateRaw, forceId, type, title, locationName, lat, lng, description='', participants=''] = row; let date; try { date = normalizeDateInput(dateRaw); } catch { return; } if (!forceId || !title) return; marchData.events.push({ id: makeEventId(date, forceId), date, displayDate: date, forceId, type: type || '其他', title, description, location:{ name: locationName, coordinates:[Number(lat), Number(lng)] }, participants: splitList(participants), importance:3, sourceIds:[], certainty:'medium' }); imported += 1; }); dedupeEvents(); sortData(); populateSelects(); renderEventsTable(); renderSubjectsGrid(); alert(`已导入 ${imported} 条到当前内存。`); }

function normalizeDateInput(value) { const raw = String(value || '').trim(); const digits = raw.replace(/\D/g, ''); let y,m,d; if (/^\d{8}$/.test(digits)) { y=digits.slice(0,4); m=digits.slice(4,6); d=digits.slice(6,8); } else { const match = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/); if (!match) throw new Error('日期请使用 YYYYMMDD，例如 19350115。'); y=match[1]; m=match[2].padStart(2,'0'); d=match[3].padStart(2,'0'); } const date = new Date(Number(y), Number(m)-1, Number(d)); if (date.getFullYear()!=Number(y) || date.getMonth()+1!=Number(m) || date.getDate()!=Number(d)) throw new Error('日期不存在，请检查。'); return `${y}-${m}-${d}`; }
function formatYYYYMMDD(date) { return String(date || '').replace(/-/g, ''); }
function sequenceFromDate(date) { return Number(formatYYYYMMDD(date).slice(4)); }
function addNumMetric(metrics, key, id) { const v = getVal(id); if (v !== '' && Number.isFinite(Number(v))) metrics[key] = Number(v); }
function setVal(id, value) { const el = document.getElementById(id); if (el) el.value = value ?? ''; }
function getVal(id) { return document.getElementById(id)?.value ?? ''; }
function makeEventId(date='', force='evt') { const d = formatYYYYMMDD(date || new Date().toISOString().slice(0,10)); return `evt_${d}_${String(force||'force').replace(/[^A-Za-z0-9_]/g,'_')}_${Math.random().toString(16).slice(2,7)}`; }
function splitList(value) { return String(value || '').split(/[，,;；|｜]/).map(s=>s.trim()).filter(Boolean); }
function parseDelimited(text) { return text.split(/\r?\n/).map(parseCSVLine); }
function parseCSVLine(line) { const out=[]; let cur='', quote=false; for (let i=0;i<line.length;i++){ const ch=line[i]; if(ch==='"'){ if(quote && line[i+1]==='"'){ cur+='"'; i++; } else quote=!quote; } else if((ch===',' || ch==='\t') && !quote){ out.push(cur.trim()); cur=''; } else cur+=ch; } out.push(cur.trim()); return out; }
function csvEscape(value) { const str = String(value ?? ''); return /[",\n\r]/.test(str) ? `"${str.replaceAll('"','""')}"` : str; }
function downloadFile(filename, content, mime) { const blob = new Blob([content], {type:mime}); const url = URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=filename; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); }
function escapeHTML(value) { return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;'); }
function escapeAttr(value) { return escapeHTML(value).replaceAll('`','&#096;'); }

window.openEventModal = openEventModal;
window.deleteEvent = deleteEvent;
window.openSubjectModal = openSubjectModal;
window.deleteSubject = deleteSubject;

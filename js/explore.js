/* 长征星火 · 主题入口页（数据驱动，无构建步骤） */
(function () {
  'use strict';
  var DATA_URL = 'data/long_march_events.json';
  var data = null;

  var PERSON_PICK = [
    'dongzhengtang', 'yangjingyu', 'zhaoyiman', 'fengbaiju', 'zengsheng',
    'liuzhidan', 'xiezichang', 'xiaoyedan', 'maozedong', 'zhouenlai',
    'zhude', 'xuhaidong', 'zhangqiqiu', 'yangkeming', 'wangzuoyao'
  ];
  var PLACE_PICK = [
    '贵州遵义', '甘肃会宁', '江西于都', '四川小金两河口', '四川松潘毛儿盖',
    '四川若尔盖包座', '云南皎平渡', '甘肃宕昌哈达铺', '湖南大庸/张家界', '陕西安定一带'
  ];
  var EVENT_PICK = [
    'rf_19341010_ruijin', 'en_19341010_encirclement',
    'ev_wxyj_19370120', 'ev_dkb_19400223', 'ev_qy_193304', 'ev_dj_19431202'
  ];

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[c];
    });
  }

  function fetchData() {
    return fetch(DATA_URL + '?v=' + Date.now(), { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
  }

  function linkPerson(id) { return 'museum.html?person=' + encodeURIComponent(id) + '#persons'; }
  function linkForce(id) { return 'museum.html#catalog'; }
  function linkPlace(name) { return 'map.html#event-' + encodeURIComponent(name); }
  function linkEvent(id) { return 'map.html#event=' + encodeURIComponent(id); }

  function card(opts) {
    return '<a class="ex-card" href="' + esc(opts.href) + '" style="--accent:' + esc(opts.color || '#bd2427') + '">' +
      '<span class="ex-card-kicker">' + esc(opts.kicker || '') + '</span>' +
      '<strong class="ex-card-title">' + esc(opts.title) + '</strong>' +
      '<span class="ex-card-desc">' + esc(opts.desc || '') + '</span>' +
      '<span class="ex-card-cta">' + esc(opts.cta || '进入 →') + '</span>' +
      '</a>';
  }

  function personCount(id) {
    var n = 0;
    (data.personEvents || []).forEach(function (r) { if (r.personId === id) n++; });
    return n;
  }

  function renderPersons() {
    var box = document.getElementById('grid-persons');
    var list = PERSON_PICK.map(function (id) {
      return (data.persons || []).find(function (p) { return p.id === id; });
    }).filter(Boolean);
    if (!list.length) list = (data.persons || []).slice(0, 12);
    box.innerHTML = list.map(function (p) {
      var n = personCount(p.id);
      return card({
        href: linkPerson(p.id),
        kicker: p.forceId ? (getForceName(p.forceId) || '人物') : '人物',
        title: p.name,
        desc: (p.summary || '').slice(0, 46) + (n ? ' · ' + n + ' 个事件' : ''),
        color: p.portrait ? '#8b0000' : '#bd2427'
      });
    }).join('');
  }

  function getForceName(id) {
    var f = (data.subjects || []).find(function (s) { return s.id === id; });
    return f ? f.name : '';
  }

  function renderForces() {
    var box = document.getElementById('grid-forces');
    var forces = (data.subjects || []).filter(function (s) { return s.type === 'force'; });
    var groups = { '红军主线': [], '星星之火': [], '敌军': [] };
    forces.forEach(function (f) {
      var g = f.group || (f.isEnemy ? '敌军' : '红军主线');
      (groups[g] || (groups[g] = [])).push(f);
    });
    var order = ['红军主线', '星星之火', '敌军'];
    var html = '';
    order.forEach(function (g) {
      (groups[g] || []).forEach(function (f) {
        var cnt = (data.events || []).filter(function (e) { return e.forceId === f.id; }).length;
        html += card({
          href: linkForce(f.id),
          kicker: g + (f.isEnemy ? ' · 叙事层' : ''),
          title: f.name,
          desc: (f.subUnits || f.description || '').slice(0, 44) + (cnt ? ' · ' + cnt + ' 节点' : ' · 框架待补'),
          color: f.color || '#777'
        });
      });
    });
    box.innerHTML = html;
  }

  function renderPlaces() {
    var box = document.getElementById('grid-places');
    var byName = {};
    (data.events || []).forEach(function (e) {
      var n = e.location && e.location.name;
      if (!n) return;
      (byName[n] || (byName[n] = [])).push(e);
    });
    var list = PLACE_PICK.map(function (n) { return { name: n, events: byName[n] || [] }; })
      .filter(function (x) { return x.events.length; });
    if (!list.length) {
      list = Object.keys(byName).sort(function (a, b) { return byName[b].length - byName[a].length; })
        .slice(0, 10).map(function (n) { return { name: n, events: byName[n] }; });
    }
    box.innerHTML = list.map(function (x) {
      var dates = x.events.map(function (e) { return e.date; }).sort();
      return card({
        href: linkPlace(x.name),
        kicker: x.events.length + ' 个事件',
        title: x.name,
        desc: dates.length ? (dates[0] + ' — ' + dates[dates.length - 1]) : '地点档案',
        color: '#2f5e49'
      });
    }).join('');
  }

  function renderEvents() {
    var box = document.getElementById('grid-events');
    var list = EVENT_PICK.map(function (id) {
      return (data.events || []).find(function (e) { return e.id === id; });
    }).filter(Boolean);
    if (!list.length) {
      list = (data.events || []).slice().sort(function (a, b) { return (b.importance || 0) - (a.importance || 0); }).slice(0, 6);
    }
    box.innerHTML = list.map(function (e) {
      return card({
        href: linkEvent(e.id),
        kicker: (e.date || '').replace(/-/g, '.') + ' · ' + (e.type || ''),
        title: e.title || e.id,
        desc: (e.description || '').slice(0, 46),
        color: e.certainty === 'high' ? '#bd2427' : '#7b7b7b'
      });
    }).join('');
  }

  fetchData().then(function (d) {
    data = d;
    renderPersons(); renderForces(); renderPlaces(); renderEvents();
  }).catch(function (err) {
    document.querySelectorAll('.ex-grid').forEach(function (el) {
      el.innerHTML = '<p class="ex-error">数据加载失败：' + esc(err.message) + '。请用 start_server.bat 启动本地服务。</p>';
    });
  });
})();

import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';

const DATA_URL = 'data/long_march_events.json';
const container = document.getElementById('immersive-scene');
const loading = document.getElementById('immersive-loading');
const focusPanel = document.getElementById('focus-panel');
const focusMeta = document.getElementById('focus-meta');
const focusAction = document.getElementById('focus-action');
const indexStrip = document.getElementById('immersive-index');
const walkCurrent = document.getElementById('walk-current');

const boardSpacing = 26;
const boardStartZ = -10;

let data;
let renderer;
let scene;
let camera;
let raycaster;
let pointer = new THREE.Vector2();
let pointerTarget = new THREE.Vector2();
let cameraTarget = new THREE.Vector3(0, 5.4, 10);
let lookTarget = new THREE.Vector3(0, 5, -10);
let currentBoardIndex = 0;
let boards = [];
let boardMeshes = [];
let interactiveGroups = [];
let floatingObjects = [];
let hoveredBoard = null;
let routeGroup;
let modeLayer;
let portraitOverlay;
let bounds;
let wheelLock = false;
let textureLoader;
const textureCache = new Map();

init();

async function init() {
  try {
    const res = await fetch(`${DATA_URL}?v=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`数据加载失败：${res.status}`);
    data = await res.json();
    boards = createBoardData();
    setupScene();
    buildMuseum();
    bindUI();
    goToBoard(0, true);
    animate();
    loading?.classList.add('hidden');
  } catch (err) {
    console.error(err);
    if (loading) loading.textContent = err.message || String(err);
  }
}

function createBoardData() {
  const steamEvents = data.events.filter(event => (event.sourceIds || []).includes('src_steam_longmarch_1934_1936')).length;
  const martyrs = data.persons.filter(person => person.personType === '烈士').length;
  const places = getPlaces().length;
  return [
    {
      id: 'route',
      mode: 'overview',
      title: '长征星火路线',
      subtitle: `${data.events.length} 条事件记录 / 多路红军路线`,
      body: '第一展板保留原 red-map 路线逻辑，作为整座数字博物馆的总入口。',
      href: 'museum.html#route',
      action: '进入路线展板',
      accent: '#d33134',
    },
    {
      id: 'catalog',
      mode: 'catalog',
      title: '资料总目录',
      subtitle: '人物、地点、事件、部队四类模块',
      body: '把游戏文本线索、公开资料和人工表格统一组织为可搜索的资料目录。',
      href: 'museum.html#catalog',
      action: '进入资料目录',
      accent: '#d7a752',
    },
    {
      id: 'events',
      mode: 'events',
      title: '事件星图',
      subtitle: `${steamEvents} 条补充事件线索`,
      body: '事件按时间和地点进入路线，补充材料会保留来源标记，方便后续校订。',
      href: 'museum.html#catalog',
      action: '查看事件模块',
      accent: '#5884b9',
    },
    {
      id: 'persons',
      mode: 'persons',
      title: '人物生命线',
      subtitle: `${data.persons.length} 个人物 / ${data.personEvents.length} 条关联`,
      body: '人物不是附录，而是进入长征叙事的透镜：每个名字都连接到一段具体史实。',
      href: 'museum.html#persons',
      action: '进入人物时间线',
      accent: '#4c8a65',
    },
    {
      id: 'places',
      mode: 'places',
      title: '地点档案',
      subtitle: `${places} 个地点聚合`,
      body: '每个地点都从路线坐标中聚合出来，显示事件密度、时间跨度和相关部队。',
      href: 'museum.html#places',
      action: '进入地点档案',
      accent: '#5d88bd',
    },
    {
      id: 'martyrs',
      mode: 'martyrs',
      title: '牺牲者纪念墙',
      subtitle: `${martyrs} 位烈士档案`,
      body: '牺牲不是抽象统计，而是姓名、部队、地点和时间共同形成的纪念结构。',
      href: 'museum.html#martyrs',
      action: '进入英烈墙',
      accent: '#d33134',
    },
    {
      id: 'archive',
      mode: 'archive',
      title: '来源与策展方法',
      subtitle: `${data.sources.length} 条来源 / 来源标记`,
      body: '外部文本只作为研究线索，进入正式展览前需要继续进行史实和版权复核。',
      href: 'museum.html#archive',
      action: '查看资料层',
      accent: '#b9863d',
    },
  ];
}

function setupScene() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x070909);
  scene.fog = new THREE.FogExp2(0x070909, 0.012);

  const width = container.clientWidth || window.innerWidth;
  const height = container.clientHeight || window.innerHeight;
  camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 260);
  camera.position.set(0, 5.6, 10);
  camera.lookAt(0, 5, -10);

  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.setSize(width, height);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);
  portraitOverlay = document.createElement('div');
  portraitOverlay.className = 'portrait-cloud-overlay';
  container.parentElement.appendChild(portraitOverlay);

  raycaster = new THREE.Raycaster();
  textureLoader = new THREE.TextureLoader();
  textureLoader.setCrossOrigin('anonymous');

  scene.add(new THREE.HemisphereLight(0xfff2df, 0x1d2628, 1.05));
  const key = new THREE.SpotLight(0xffc46c, 1500, 120, Math.PI / 5.2, 0.42, 1.1);
  key.position.set(-16, 22, 18);
  key.castShadow = true;
  scene.add(key);
  const red = new THREE.PointLight(0xd33134, 240, 80);
  red.position.set(18, 8, -42);
  scene.add(red);
  const blue = new THREE.PointLight(0x5e95d3, 180, 90);
  blue.position.set(-22, 7, -86);
  scene.add(blue);

  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', onPointerMove);
  window.addEventListener('touchmove', onTouchMove, { passive: true });
  window.addEventListener('click', onClick);
  window.addEventListener('wheel', onWheel, { passive: true });
  window.addEventListener('keydown', onKeyDown);
}

function buildMuseum() {
  bounds = getCoordinateBounds(data.events);
  buildCorridor();
  buildBoards();
  buildRouteTable();
  modeLayer = new THREE.Group();
  scene.add(modeLayer);
}

function buildCorridor() {
  const length = boards.length * boardSpacing + 38;
  const centerZ = boardStartZ - (length / 2) + 14;
  const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0x151816,
    roughness: 0.68,
    metalness: 0.1,
  });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(38, length, 16, 42), floorMaterial);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -0.04, centerZ);
  floor.receiveShadow = true;
  scene.add(floor);

  const grid = new THREE.GridHelper(length, 46, 0x8a2b2d, 0x303c38);
  grid.rotation.y = Math.PI / 2;
  grid.position.set(0, 0.02, centerZ);
  grid.material.transparent = true;
  grid.material.opacity = 0.2;
  scene.add(grid);

  const wallMaterial = new THREE.MeshStandardMaterial({
    color: 0x101514,
    roughness: 0.86,
    metalness: 0.05,
    transparent: true,
    opacity: 0.94,
  });
  const left = new THREE.Mesh(new THREE.PlaneGeometry(length, 18), wallMaterial);
  left.rotation.y = Math.PI / 2;
  left.position.set(-19, 8.8, centerZ);
  scene.add(left);
  const right = new THREE.Mesh(new THREE.PlaneGeometry(length, 18), wallMaterial.clone());
  right.rotation.y = -Math.PI / 2;
  right.position.set(19, 8.8, centerZ);
  scene.add(right);

  const ceiling = new THREE.Mesh(
    new THREE.PlaneGeometry(38, length),
    new THREE.MeshStandardMaterial({ color: 0x0d1110, roughness: 0.9, transparent: true, opacity: 0.72 })
  );
  ceiling.rotation.x = Math.PI / 2;
  ceiling.position.set(0, 17.8, centerZ);
  scene.add(ceiling);

  boards.forEach((board, index) => {
    const z = boardZ(index);
    const light = new THREE.PointLight(new THREE.Color(board.accent), 95, 25);
    light.position.set(index % 2 ? 8 : -8, 7.4, z + 1);
    scene.add(light);
    const marker = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.08, 2.8, 18),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(board.accent), transparent: true, opacity: 0.74 })
    );
    marker.rotation.x = Math.PI / 2;
    marker.position.set(0, 0.09, z + 7);
    scene.add(marker);
  });
}

function buildBoards() {
  boards.forEach((board, index) => {
    const x = index % 2 ? 5.2 : -5.2;
    const z = boardZ(index);
    board.x = x;
    board.z = z;

    const group = new THREE.Group();
    group.position.set(x, 6.3, z);
    group.rotation.y = index % 2 ? -0.1 : 0.1;
    group.userData = { board, href: board.href };

    const frame = new THREE.Mesh(
      new THREE.BoxGeometry(13.7, 7.5, 0.34),
      new THREE.MeshStandardMaterial({
        color: 0x171615,
        roughness: 0.5,
        metalness: 0.22,
        emissive: new THREE.Color(board.accent),
        emissiveIntensity: 0.05,
      })
    );
    frame.castShadow = true;
    group.add(frame);

    const panel = makeTextPlane(board.title, `${board.subtitle}\n${board.body}`, board.accent, 1200, 680);
    panel.position.z = 0.2;
    panel.scale.set(1.55, 1.55, 1);
    group.add(panel);

    const plinth = new THREE.Mesh(
      new THREE.BoxGeometry(15.4, 0.36, 2),
      new THREE.MeshStandardMaterial({ color: 0x262019, roughness: 0.5, metalness: 0.18 })
    );
    plinth.position.set(0, -4.05, 0.18);
    group.add(plinth);

    const number = makeTextPlane(String(index + 1).padStart(2, '0'), board.action, board.accent, 420, 260);
    number.scale.set(0.62, 0.62, 1);
    number.position.set(-5.8, -3.7, 0.42);
    group.add(number);

    markInteractive(group, board);
    scene.add(group);
    boardMeshes.push(group);
    interactiveGroups.push(group);
  });
}

function buildRouteTable() {
  routeGroup = new THREE.Group();
  routeGroup.position.set(0, 0.34, boardZ(0) + 2.5);
  routeGroup.scale.set(0.42, 0.42, 0.42);
  scene.add(routeGroup);

  const eventsByForce = new Map();
  data.events.forEach(event => {
    if (!event.location?.coordinates?.length) return;
    if (!eventsByForce.has(event.forceId)) eventsByForce.set(event.forceId, []);
    eventsByForce.get(event.forceId).push(event);
  });

  [...eventsByForce.entries()].forEach(([forceId, events], index) => {
    events.sort(compareEvents);
    const subject = getSubject(forceId);
    const color = new THREE.Color(subject?.color || '#bd2427');
    const points = events.map((event, i) => {
      const pos = eventPosition(event);
      pos.y = 0.25 + index * 0.08 + Math.sin(i * 0.65) * 0.05;
      return pos;
    });
    if (points.length < 2) return;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(points),
      new THREE.LineBasicMaterial({ color, transparent: true, opacity: forceId === 'enemy_kmt' ? 0.18 : 0.78 })
    );
    routeGroup.add(line);
  });

  const starGeometry = new THREE.SphereGeometry(0.18, 12, 8);
  data.events.filter(event => Number(event.importance || 0) >= 4).slice(0, 120).forEach(event => {
    const color = new THREE.Color(getSubject(event.forceId)?.color || '#bd2427');
    const star = new THREE.Mesh(
      starGeometry,
      new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.7, roughness: 0.35 })
    );
    star.position.copy(eventPosition(event));
    star.position.y = 0.9;
    routeGroup.add(star);
  });
}

function buildSideMemorials() {
  const personWallZ = boardZ(3);
  const people = data.persons.slice(0, 24);
  people.forEach((person, index) => {
    const side = index % 2 ? 1 : -1;
    const row = Math.floor(index / 2);
    const plaque = makeTextPlane(person.name, `${person.personType || '人物'} / ${getSubject(person.forceId)?.shortName || ''}`, side > 0 ? '#4c8a65' : '#d7a752', 560, 230);
    plaque.scale.set(0.86, 0.86, 1);
    plaque.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;
    plaque.position.set(side * 18.65, 13.8 - row * 1.85, personWallZ + 8 - row * 0.28);
    scene.add(plaque);
  });

  const placeWallZ = boardZ(4);
  getPlaces().sort((a, b) => b.events.length - a.events.length).slice(0, 18).forEach((place, index) => {
    const side = index % 2 ? 1 : -1;
    const row = Math.floor(index / 2);
    const plaque = makeTextPlane(place.name, `${place.events.length} 个事件`, '#5d88bd', 560, 220);
    plaque.scale.set(0.82, 0.82, 1);
    plaque.rotation.y = side > 0 ? -Math.PI / 2 : Math.PI / 2;
    plaque.position.set(side * 18.65, 13.6 - row * 1.7, placeWallZ + 8 - row * 0.24);
    scene.add(plaque);
  });
}

function setModeVisualization(board) {
  clearModeLayer();
  if (!modeLayer) return;
  if (board.id === 'events') {
    buildEventPanelCloud(board);
  }
  if (board.id === 'persons' || board.id === 'martyrs') {
    buildPortraitCloud(board);
  }
}

function clearModeLayer() {
  if (!modeLayer) return;
  interactiveGroups = interactiveGroups.filter(group => !group.userData.dynamicLayer);
  floatingObjects = [];
  if (portraitOverlay) {
    portraitOverlay.className = 'portrait-cloud-overlay';
    portraitOverlay.innerHTML = '';
  }
  while (modeLayer.children.length) {
    const child = modeLayer.children.pop();
    disposeObject(child);
  }
}

function disposeObject(object) {
  object.traverse(child => {
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      const materials = Array.isArray(child.material) ? child.material : [child.material];
      materials.forEach(material => {
        if (material.map && !material.userData?.cachedTexture) material.map.dispose();
        material.dispose();
      });
    }
  });
}

function addDynamicGroup(group, board, href = board.href) {
  group.userData.dynamicLayer = true;
  group.userData.board = board;
  group.userData.href = href;
  group.traverse(child => {
    child.userData.board = board;
    child.userData.href = href;
  });
  modeLayer.add(group);
  interactiveGroups.push(group);
  return group;
}

function buildEventPanelCloud(board) {
  const events = getEventPanelItems();
  const anchorZ = board.z || boardZ(2);
  const columns = [-8.4, -2.8, 2.8, 8.4];
  events.forEach((event, index) => {
    const column = index % columns.length;
    const row = Math.floor(index / columns.length);
    const group = new THREE.Group();
    const accent = getSubject(event.forceId)?.color || board.accent;
    const title = `${event.date || ''}  ${event.title || ''}`;
    const subtitle = `${event.type || '事件'} / ${event.location?.name || ''}\n${shortText(event.description || '', 36)}`;
    const card = makeTextPlane(title, subtitle, accent, 720, 430);
    card.scale.set(0.46, 0.46, 1);
    group.add(card);
    group.position.set(columns[column], 3.2 + row * 2.45, anchorZ + 5.8 - row * 0.7);
    group.rotation.y = -columns[column] * 0.012;
    group.userData.float = {
      origin: group.position.clone(),
      phase: index * 0.85,
      speed: 0.12,
      sway: 0.025,
      lift: 0.045,
    };
    floatingObjects.push(group);
    addDynamicGroup(group, board, 'museum.html#catalog');
  });
}

function getEventPanelItems() {
  const priorityTypes = new Set(['会议', '战役', '会师', '牺牲', '渡河']);
  return data.events
    .filter(event => priorityTypes.has(event.type) || Number(event.importance || 0) >= 4)
    .sort((a, b) => Number(b.importance || 0) - Number(a.importance || 0) || compareEvents(a, b))
    .slice(0, 8)
    .sort(compareEvents);
}

function buildPortraitCloud(board) {
  const people = getPortraitPeople(board.id);
  const rand = seededRandom(board.id === 'martyrs' ? 193610 : 193501);
  const anchorZ = board.z || boardZ(board.id === 'martyrs' ? 5 : 3);
  const href = board.id === 'martyrs' ? 'museum.html#martyrs' : 'museum.html#persons';
  people.forEach((person, index) => {
    const visual = getVisual('person', person.id);
    const card = createPortraitCard(person, visual, board.accent);
    const columns = [-7.6, -3.8, 0, 3.8, 7.6];
    const col = index % columns.length;
    const row = Math.floor(index / columns.length);
    const x = columns[col] + (rand() - 0.5) * 0.28;
    const y = 3.15 + row * 3.15 + (rand() - 0.5) * 0.16;
    const z = anchorZ + 5.2 - row * 0.55;
    const scale = 0.78 + rand() * 0.16;
    card.position.set(x, y, z);
    card.scale.setScalar(scale);
    card.rotation.y = -x * 0.018;
    card.userData.float = {
      origin: card.position.clone(),
      phase: rand() * Math.PI * 2,
      speed: 0.09 + rand() * 0.04,
      sway: 0.035,
      lift: 0.05,
    };
    floatingObjects.push(card);
    addDynamicGroup(card, board, href);
  });
}

function renderPortraitOverlay(people, board) {
  if (!portraitOverlay) return;
  const rand = seededRandom(board.id === 'martyrs' ? 193611 : 193502);
  const portraits = people
    .map(person => ({ person, visual: getVisual('person', person.id) }))
    .filter(item => item.visual?.imageUrl || board.id === 'martyrs')
    .slice(0, board.id === 'martyrs' ? 10 : 14);
  portraitOverlay.classList.add('active', board.id === 'martyrs' ? 'martyr-cloud' : 'person-cloud');
  portraitOverlay.innerHTML = portraits.map(({ person, visual }, index) => {
    const x = 20 + rand() * 60;
    const y = 18 + rand() * 54;
    const size = board.id === 'martyrs' ? 84 + rand() * 30 : 78 + rand() * 36;
    const dx = -10 + rand() * 20;
    const dy = -8 + rand() * 16;
    const rot = -4 + rand() * 8;
    const duration = 10 + rand() * 6;
    const delay = -rand() * duration;
    const style = `--x:${x.toFixed(2)}%;--y:${y.toFixed(2)}%;--size:${size.toFixed(1)}px;--dx:${dx.toFixed(1)}px;--dy:${dy.toFixed(1)}px;--rot:${rot.toFixed(2)}deg;--duration:${duration.toFixed(2)}s;--delay:${delay.toFixed(2)}s;`;
    const img = visual?.imageUrl
      ? `<img src="${escapeAttr(visual.imageUrl)}" alt="${escapeAttr(visual.alt || person.name)}" loading="lazy" referrerpolicy="no-referrer">`
      : `<strong>${escapeHTML(String(person.name || '?').slice(0, 1))}</strong>`;
    return `<figure class="floating-portrait" style="${style}">
      ${img}
      <figcaption>${escapeHTML(person.name || '')}</figcaption>
    </figure>`;
  }).join('');
}

function getPortraitPeople(boardId) {
  const visualIds = new Set((data.museum?.visualAssets || []).filter(visual => visual.targetType === 'person' && visual.imageUrl).map(visual => visual.targetId));
  const people = boardId === 'martyrs'
    ? data.persons.filter(person => person.personType === '烈士')
    : data.persons;
  return [...people]
    .sort((a, b) => Number(visualIds.has(b.id)) - Number(visualIds.has(a.id)) || Number(a.sort || 9999) - Number(b.sort || 9999))
    .slice(0, boardId === 'martyrs' ? 10 : 10);
}

function createPortraitCard(person, visual, accent) {
  const group = new THREE.Group();
  const subject = getSubject(person.forceId);
  const frame = new THREE.Mesh(
    new THREE.BoxGeometry(2.35, 3.12, 0.16),
    new THREE.MeshStandardMaterial({
      color: 0x171615,
      roughness: 0.54,
      metalness: 0.18,
      emissive: new THREE.Color(accent),
      emissiveIntensity: 0.08,
    })
  );
  group.add(frame);

  const material = new THREE.MeshBasicMaterial({
    map: makePortraitTexture(person, accent),
    color: 0xffffff,
    transparent: true,
    side: THREE.DoubleSide,
  });
  const image = new THREE.Mesh(new THREE.PlaneGeometry(1.86, 2.18), material);
  image.position.set(0, 0.34, 0.11);
  group.add(image);

  if (visual?.imageUrl && isTextureSafe(visual.imageUrl)) {
    loadTexture(visual.imageUrl, texture => {
      material.map = texture;
      material.userData.cachedTexture = true;
      material.needsUpdate = true;
    });
  }

  const label = makeTextPlane(person.name, `${person.personType || '人物'} / ${subject?.shortName || ''}`, accent, 420, 150);
  label.scale.set(0.45, 0.45, 1);
  label.position.set(0, -1.24, 0.13);
  group.add(label);
  return group;
}

function isTextureSafe(url) {
  return /^(docs\/|\.\/|\/)/.test(url);
}

function makePortraitTexture(person, accent) {
  const canvas = document.createElement('canvas');
  canvas.width = 520;
  canvas.height = 640;
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  gradient.addColorStop(0, '#26211b');
  gradient.addColorStop(1, '#0d1110');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = accent;
  ctx.lineWidth = 12;
  ctx.strokeRect(22, 22, canvas.width - 44, canvas.height - 44);
  ctx.fillStyle = accent;
  ctx.globalAlpha = 0.2;
  ctx.beginPath();
  ctx.arc(canvas.width / 2, 246, 150, 0, Math.PI * 2);
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.fillStyle = '#fff8ef';
  ctx.font = '900 150px "Microsoft YaHei", sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(String(person.name || '?').slice(0, 1), canvas.width / 2, 246);
  ctx.font = '900 46px "Microsoft YaHei", sans-serif';
  ctx.fillText(person.name || '', canvas.width / 2, 500);
  ctx.font = '700 24px "Microsoft YaHei", sans-serif';
  ctx.fillStyle = 'rgba(255, 248, 239, 0.72)';
  ctx.fillText(person.personType || '人物', canvas.width / 2, 548);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function loadTexture(url, onLoad) {
  if (textureCache.has(url)) {
    onLoad(textureCache.get(url));
    return;
  }
  textureLoader.load(
    url,
    texture => {
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.anisotropy = 4;
      textureCache.set(url, texture);
      onLoad(texture);
    },
    undefined,
    () => {}
  );
}

function seededRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value += 0x6D2B79F5;
    let t = value;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shortText(text, length) {
  const value = String(text || '').replace(/\s+/g, '');
  return value.length > length ? `${value.slice(0, length)}...` : value;
}

function markInteractive(group, board) {
  group.userData.href = board.href;
  group.userData.board = board;
  group.traverse(child => {
    child.userData.board = board;
    child.userData.href = board.href;
  });
}

function makeTextPlane(title, subtitle, accent = '#d7a752', width = 900, height = 480) {
  const texture = makeTextTexture(title, subtitle, accent, width, height);
  const material = new THREE.MeshStandardMaterial({
    map: texture,
    transparent: true,
    roughness: 0.62,
    metalness: 0.08,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(width / 150, height / 150), material);
  mesh.castShadow = true;
  return mesh;
}

function makeTextTexture(title, subtitle, accent, width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = 'rgba(20, 20, 18, 0.96)';
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = 'rgba(255, 248, 239, 0.22)';
  ctx.lineWidth = 5;
  ctx.strokeRect(12, 12, width - 24, height - 24);
  ctx.fillStyle = accent;
  ctx.fillRect(0, 0, width, 16);
  ctx.fillStyle = '#fff8ef';
  ctx.font = `900 ${Math.max(46, Math.floor(width / 12))}px "Microsoft YaHei", sans-serif`;
  wrapText(ctx, title, 42, height * 0.32, width - 84, Math.floor(width / 10));
  ctx.fillStyle = 'rgba(255, 248, 239, 0.72)';
  ctx.font = `700 ${Math.max(26, Math.floor(width / 28))}px "Microsoft YaHei", sans-serif`;
  wrapText(ctx, subtitle || '', 46, height * 0.62, width - 92, Math.floor(width / 24));
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 4;
  return texture;
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  String(text || '').split('\n').forEach((paragraph, paragraphIndex) => {
    if (paragraphIndex) y += lineHeight * 0.75;
    let line = '';
    [...paragraph].forEach(char => {
      const next = line + char;
      if (ctx.measureText(next).width > maxWidth && line) {
        ctx.fillText(line, x, y);
        line = char;
        y += lineHeight;
      } else {
        line = next;
      }
    });
    if (line) {
      ctx.fillText(line, x, y);
      y += lineHeight;
    }
  });
}

function bindUI() {
  document.querySelectorAll('[data-mode]').forEach(button => {
    button.addEventListener('click', () => {
      const index = boards.findIndex(board => board.mode === button.dataset.mode);
      goToBoard(index >= 0 ? index : 0);
    });
  });
  document.querySelectorAll('[data-walk]').forEach(button => {
    button.addEventListener('click', () => {
      goToBoard(currentBoardIndex + (button.dataset.walk === 'next' ? 1 : -1));
    });
  });
  renderIndex();
}

function renderIndex() {
  indexStrip.innerHTML = boards.map((board, index) => `<button type="button" data-board-index="${index}">
    <strong>${escapeHTML(board.title)}</strong>
    <span>${escapeHTML(board.subtitle)}</span>
  </button>`).join('');
  indexStrip.querySelectorAll('button').forEach(button => {
    button.addEventListener('click', () => goToBoard(Number(button.dataset.boardIndex || 0)));
  });
}

function goToBoard(index, immediate = false) {
  currentBoardIndex = Math.max(0, Math.min(boards.length - 1, index));
  const board = boards[currentBoardIndex];
  const x = board.x || 0;
  const z = board.z || boardZ(currentBoardIndex);
  cameraTarget.set(x * 0.36, 5.3, z + 14.5);
  lookTarget.set(x, 5.65, z - 0.2);
  if (immediate) {
    camera.position.copy(cameraTarget);
    camera.lookAt(lookTarget);
  }
  document.querySelectorAll('[data-mode]').forEach(button => {
    button.classList.toggle('active', button.dataset.mode === board.mode || (board.id === 'catalog' && button.dataset.mode === 'overview'));
  });
  indexStrip.querySelectorAll('button').forEach((button, buttonIndex) => {
    button.classList.toggle('active', buttonIndex === currentBoardIndex);
  });
  if (walkCurrent) walkCurrent.textContent = `${String(currentBoardIndex + 1).padStart(2, '0')} / ${String(boards.length).padStart(2, '0')}`;
  setFocus(board);
  setModeVisualization(board);
}

function setFocus(board) {
  focusPanel.querySelector('h1').textContent = board.title;
  focusPanel.querySelector('p:not(.eyebrow)').textContent = board.body;
  focusMeta.innerHTML = [board.subtitle, '点击 3D 看板进入模块'].map(item => `<span>${escapeHTML(item)}</span>`).join('');
  focusAction.href = board.href;
  focusAction.textContent = board.action;
}

function animate(time = 0) {
  requestAnimationFrame(animate);
  const t = time * 0.001;
  pointer.lerp(pointerTarget, 0.05);
  const parallax = new THREE.Vector3(pointer.x * 0.45, pointer.y * 0.2, Math.sin(t * 0.28) * 0.12);
  camera.position.lerp(cameraTarget.clone().add(parallax), 0.05);
  const look = lookTarget.clone().add(new THREE.Vector3(pointer.x * 0.28, pointer.y * 0.16, 0));
  camera.lookAt(look);
  boardMeshes.forEach((group, index) => {
    const desired = group === hoveredBoard ? 1.04 : 1;
    const current = group.scale.x;
    const next = current + (desired - current) * 0.12;
    group.scale.setScalar(next);
    group.position.y = 6.3 + Math.sin(t * 0.55 + index) * 0.018;
  });
  floatingObjects.forEach((group, index) => {
    const float = group.userData.float;
    if (!float) return;
    group.position.x = float.origin.x + Math.sin(t * float.speed + float.phase) * float.sway;
    group.position.y = float.origin.y + Math.sin(t * float.speed * 1.35 + float.phase * 0.7) * float.lift;
    group.position.z = float.origin.z + Math.cos(t * float.speed + index) * float.sway * 0.52;
    group.lookAt(camera.position);
  });
  if (routeGroup) routeGroup.rotation.y = Math.sin(t * 0.18) * 0.04;
  renderer.render(scene, camera);
}

function onPointerMove(event) {
  pointerTarget.x = (event.clientX / window.innerWidth - 0.5) * 2;
  pointerTarget.y = -(event.clientY / window.innerHeight - 0.5) * 2;
  raycast(event.clientX, event.clientY);
}

function onTouchMove(event) {
  const touch = event.touches[0];
  if (!touch) return;
  pointerTarget.x = (touch.clientX / window.innerWidth - 0.5) * 2;
  pointerTarget.y = -(touch.clientY / window.innerHeight - 0.5) * 2;
}

function onWheel(event) {
  if (wheelLock || Math.abs(event.deltaY) < 16) return;
  wheelLock = true;
  goToBoard(currentBoardIndex + (event.deltaY > 0 ? 1 : -1));
  setTimeout(() => { wheelLock = false; }, 360);
}

function onKeyDown(event) {
  if (['ArrowDown', 'ArrowRight', 's', 'S', 'w', 'W', 'ArrowUp', 'ArrowLeft'].includes(event.key)) {
    event.preventDefault();
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowRight' || event.key === 's' || event.key === 'S') {
    goToBoard(currentBoardIndex + 1);
  }
  if (event.key === 'ArrowUp' || event.key === 'ArrowLeft' || event.key === 'w' || event.key === 'W') {
    goToBoard(currentBoardIndex - 1);
  }
  if (event.key === 'Enter') {
    window.location.href = boards[currentBoardIndex].href;
  }
}

function onClick(event) {
  if (event.target !== renderer.domElement) return;
  const group = raycast(event.clientX, event.clientY);
  if (group?.userData?.href) {
    window.location.href = group.userData.href;
  }
}

function raycast(clientX, clientY) {
  const rect = renderer.domElement.getBoundingClientRect();
  const mouse = new THREE.Vector2(
    ((clientX - rect.left) / rect.width) * 2 - 1,
    -((clientY - rect.top) / rect.height) * 2 + 1
  );
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(interactiveGroups, true);
  const hit = hits.find(item => findInteractiveGroup(item.object))?.object || null;
  hoveredBoard = findInteractiveGroup(hit);
  document.body.style.cursor = hoveredBoard ? 'pointer' : '';
  return hoveredBoard;
}

function findInteractiveGroup(object) {
  let current = object;
  while (current) {
    if (interactiveGroups.includes(current)) return current;
    current = current.parent;
  }
  return null;
}

function resize() {
  const width = container.clientWidth || window.innerWidth;
  const height = container.clientHeight || window.innerHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

function boardZ(index) {
  return boardStartZ - index * boardSpacing;
}

function eventPosition(event) {
  const coords = event.location?.coordinates || [0, 0];
  const lat = Number(coords[0]);
  const lng = Number(coords[1]);
  const x = normalize(lng, bounds.minLng, bounds.maxLng) * 58 - 29;
  const z = -(normalize(lat, bounds.minLat, bounds.maxLat) * 35 - 17.5);
  return new THREE.Vector3(x, 0.4, z);
}

function getCoordinateBounds(events) {
  const coords = events.map(event => event.location?.coordinates || []).filter(pair => Number.isFinite(Number(pair[0])) && Number.isFinite(Number(pair[1])));
  const lats = coords.map(pair => Number(pair[0]));
  const lngs = coords.map(pair => Number(pair[1]));
  return {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLng: Math.min(...lngs),
    maxLng: Math.max(...lngs),
  };
}

function normalize(value, min, max) {
  if (max === min) return 0.5;
  return (value - min) / (max - min);
}

function getPlaces() {
  const map = new Map();
  data.events.forEach(event => {
    const name = event.location?.name;
    if (!name) return;
    if (!map.has(name)) map.set(name, { name, events: [] });
    map.get(name).events.push(event);
  });
  return [...map.values()].map(place => {
    place.events.sort(compareEvents);
    return place;
  });
}

function getSubject(id) {
  return data.subjects.find(subject => subject.id === id);
}

function getVisual(targetType, targetId) {
  return (data.museum?.visualAssets || []).find(visual => visual.targetType === targetType && visual.targetId === targetId);
}

function compareEvents(a, b) {
  return new Date(a.date) - new Date(b.date) || Number(a.sequence || 0) - Number(b.sequence || 0);
}

function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

function escapeAttr(value) {
  return escapeHTML(value);
}


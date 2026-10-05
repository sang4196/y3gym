(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.Y3GymGoogleMaps = api;
    const boot = () => root.document.querySelectorAll('[data-google-map]').forEach(area => api.mount(root, area));
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', boot, {once: true}); else boot();
  }
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  const bad = () => { throw new Error('Google 지도 퍼가기 코드 또는 주소를 확인하세요.'); };
  function validateURL(value) {
    if (typeof value !== 'string' || !value || value.length > 4096 || /[\s\x00-\x1f\x7f<>"'`\\]/u.test(value) || /%(?![0-9a-f]{2})/i.test(value)) return bad();
    const u = new URL(value), pairs = [...u.searchParams];
    if (u.search.includes('&')) return bad();
    // Also require the literal authority/path: URL() silently normalizes ports/dot segments.
    if (!value.startsWith('https://www.google.com/maps/embed?pb=') || u.origin !== 'https://www.google.com' || u.pathname !== '/maps/embed' || value.includes('#') || pairs.length !== 1 || pairs[0][0] !== 'pb' || !pairs[0][1].startsWith('!')) return bad();
    if (/[\x00-\x1f\x7f<>"'`\\]/u.test(decodeURIComponent(u.search))) return bad();
    return value;
  }
  function entity(value) {
    return value.replace(/&(#x[\da-f]+|#\d+|amp|quot|apos|lt|gt);/gi, (_, key) => {
      if (key[0] === '#') return String.fromCodePoint(parseInt(key.slice(key[1].toLowerCase() === 'x' ? 2 : 1), key[1].toLowerCase() === 'x' ? 16 : 10));
      return {amp:'&',quot:'"',apos:"'",lt:'<',gt:'>'}[key.toLowerCase()];
    });
  }
  function parseInput(raw) {
    if (typeof raw !== 'string' || raw.length > 8192) return bad();
    if (!raw.trimStart().startsWith('<') && /[\x00-\x1f\x7f]/u.test(raw)) return bad();
    raw = raw.trim();
    if (!raw) return '';
    if (!raw.startsWith('<')) return validateURL(raw);
    // String tokenization only. Never parse user markup into a live DOM.
    const match = /^<iframe\s+([\s\S]*?)>\s*<\/iframe\s*>$/i.exec(raw);
    if (!match) return bad();
    const allowed = new Set(['src','width','height','style','loading','allowfullscreen','referrerpolicy','title','class','frameborder']);
    const attrs = new Map(); let rest = match[1];
    while (rest.trim()) {
      const attr = /^\s*([a-z][a-z0-9-]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?(?=\s|$)/i.exec(rest);
      if (!attr) return bad();
      const name = attr[1].toLowerCase();
      if (!allowed.has(name) || attrs.has(name)) return bad();
      attrs.set(name, entity(attr[2] ?? attr[3] ?? attr[4] ?? '')); rest = rest.slice(attr[0].length);
    }
    return validateURL(attrs.get('src'));
  }
  function createFrame(win, canvas, status, title, onState = () => {}) {
    let generation = 0, timer = null, frame = null, suspended = false;
    function clean() {
      generation++;
      if (timer !== null) win.clearTimeout(timer);
      timer = null;
      if (frame) { frame.removeAttribute('src'); frame.remove(); }
      frame = null; canvas.hidden = true;
    }
    function state(name) {
      status.textContent = {idle:'',loading:'Google 지도를 불러오는 중입니다.',shown:'지도 내용을 확인하세요. 외부 화면의 실제 표시와 위치 일치는 직접 확인해야 합니다.',failed:'지도를 불러오지 못했거나 응답이 늦습니다. 다시 열기를 눌러 재시도하세요. 주소와 연락처는 그대로 이용할 수 있습니다.'}[name];
      onState(name);
    }
    function reset() { clean(); state('idle'); }
    function show(value) {
      if (suspended) return;
      clean();
      let url;
      try { url = validateURL(value); } catch (_) { state('failed'); return; }
      const mine = generation;
      state('loading');
      frame = win.document.createElement('iframe');
      frame.setAttribute('title', title);
      frame.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
      frame.setAttribute('allowfullscreen', '');
      frame.setAttribute('loading', 'eager');
      frame.addEventListener('load', () => {
        if (mine !== generation || suspended || timer === null) return;
        win.clearTimeout(timer); timer = null; state('shown');
      });
      frame.addEventListener('error', () => {
        if (mine !== generation || suspended) return;
        clean(); state('failed');
      });
      timer = win.setTimeout(() => { if (mine === generation) { clean(); state('failed'); } }, 15000);
      frame.setAttribute('src', url); canvas.hidden = false; canvas.appendChild(frame);
    }
    return {show, reset, suspend() { suspended = true; reset(); }, resume() { suspended = false; reset(); }};
  }
  function mount(win, area) {
    if (area.dataset.bound) return;
    area.dataset.bound = 'true';
    const open = area.querySelector('[data-map-open]'), close = area.querySelector('[data-map-close]');
    const controller = createFrame(win, area.querySelector('[data-map-canvas]'), area.querySelector('[data-map-status]'), area.dataset.mapTitle, state => {
      open.disabled = state === 'loading'; open.textContent = state === 'idle' ? 'Google 지도 보기' : '지도 다시 열기';
      close.hidden = state === 'idle';
    });
    open.addEventListener('click', () => controller.show(area.dataset.embedUrl));
    close.addEventListener('click', () => { controller.reset(); open.focus(); });
    win.addEventListener('pagehide', () => controller.suspend());
    win.addEventListener('pageshow', e => { if (e.persisted) controller.resume(); });
    return controller;
  }
  return {validateURL, parseInput, createFrame, mount};
});

/* Home-only notice. Node tests exercise this state machine; browser checks are separate. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    const region = root.document.querySelector('[data-home-popup]');
    if (!region) return;
    const ui = api.domUI(root.document, region);
    const controller = api.createController({
      fetch: root.fetch.bind(root), clock: () => root.performance.now(),
      storage: name => root[name], visible: () => !root.document.hidden,
      origin: root.location.origin, AbortController: root.AbortController,
      render: ui.render, hide: ui.hide,
    });
    root.addEventListener('pagehide', () => controller.suspend());
    root.addEventListener('pageshow', event => { if (event.persisted) controller.load(); });
    root.document.addEventListener('visibilitychange', () => {
      if (root.document.hidden) controller.suspend(); else controller.load();
    });
    controller.load();
  }
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  const SESSION_KEY = 'y3gym.popup.shown.v1';
  const HIDE_PREFIX = 'y3gym.popup.hidden.v1.';
  const DAY = 86400000, KST = 9 * 3600000, MAX_DELAY = 15000;
  const nextMidnight = now => (Math.floor((now + KST) / DAY) + 1) * DAY - KST;
  const id = value => typeof value === 'string' && /^[1-9][0-9]*$/.test(value);
  // Django's string limits count Unicode code points, not UTF-16 code units.
  const codePointLength = value => Array.from(value).length;
  function timestamp(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z$/.test(value)) return NaN;
    const parsed = Date.parse(value);
    return Number.isFinite(parsed) && new Date(parsed).toISOString().slice(0,19) === value.slice(0,19) ? parsed : NaN;
  }
  function valid(item, origin) {
    if (!item || !id(item.id) || typeof item.title !== 'string' || !item.title.trim() || codePointLength(item.title) > 200 ||
        !(item.message === null || (typeof item.message === 'string' && codePointLength(item.message) <= 1000)) ||
        !item.post || !id(item.post.id) || typeof item.post.title !== 'string' || item.post.detail_path !== '/posts/' + item.post.id + '/') return false;
    const start = timestamp(item.starts_at), end = timestamp(item.ends_at);
    if (!Number.isFinite(start) || !Number.isFinite(end) || start >= end) return false;
    if (item.image !== null) {
      const image = item.image;
      if (!image || typeof image.url !== 'string' || typeof image.alt !== 'string' || codePointLength(image.alt) > 200 ||
          !Number.isSafeInteger(image.width) || !Number.isSafeInteger(image.height) || image.width <= 0 || image.height <= 0) return false;
      try {
        const url = new URL(image.url);
        if (url.origin !== origin || !/^\/images\/display\/[1-9][0-9]*\/$/.test(url.pathname) || url.search || url.hash || url.username || url.password) return false;
      } catch (_) { return false; }
    }
    return !!(item.message || item.image);
  }
  function createController(env) {
    let shown = false, generation = 0, pending = null, anchor = null;
    const memoryHidden = new Map();
    function get(kind, key) { try { return env.storage(kind).getItem(key); } catch (_) { return null; } }
    function set(kind, key, value) { try { env.storage(kind).setItem(key, value); } catch (_) { /* Best-effort memory remains. */ } }
    function done() { return shown || get('sessionStorage', SESSION_KEY) === '1'; }
    function now() {
      if (!anchor) return NaN;
      const elapsed = env.clock() - anchor.tick;
      return elapsed >= 0 && Number.isFinite(elapsed) ? anchor.server + elapsed : NaN;
    }
    function hidden(item, time) {
      const value = memoryHidden.get(item.id) || get('localStorage', HIDE_PREFIX + item.id);
      const expiry = Number(value);
      // Corrupt or unrelated future deadlines must not suppress a popup forever.
      return Number.isFinite(expiry) && expiry === nextMidnight(time) && time < expiry;
    }
    function close() { env.hide(); }
    function today(item) {
      const time = now();
      if (Number.isFinite(time)) {
        const expiry = String(nextMidnight(time));
        memoryHidden.set(item.id, expiry); set('localStorage', HIDE_PREFIX + item.id, expiry);
      }
      close();
    }
    function suspend() {
      generation++; if (pending) pending.abort(); pending = null; anchor = null;
      env.hide();
    }
    async function load() {
      if (done() || !env.visible()) return 'skipped';
      if (pending) pending.abort();
      const token = ++generation;
      for (let attempt = 0; attempt < 2; attempt++) {
        const startTick = env.clock();
        const abort = new env.AbortController(); pending = abort;
        // Bounded network wait; no periodic polling.
        const timer = setTimeout(() => abort.abort(), MAX_DELAY);
        let payload;
        try {
          const response = await env.fetch('/api/v1/popups/active/', {cache:'no-store', credentials:'omit', signal:abort.signal});
          if (!response.ok || response.status !== 200 || !response.headers.get('Content-Type').includes('application/json')) return 'error';
          payload = await response.json();
        } catch (_) { return token === generation ? 'error' : 'stale'; }
        finally { clearTimeout(timer); if (pending === abort) pending = null; }
        if (token !== generation || done() || !env.visible()) return 'stale';
        const elapsed = env.clock() - startTick;
        const server = timestamp(payload && payload.meta && payload.meta.server_time);
        if (!Number.isFinite(server) || !Number.isFinite(elapsed) || elapsed < 0 || !payload || !Array.isArray(payload.items) || !payload.items.every(item => valid(item, env.origin))) return 'invalid';
        if (elapsed > MAX_DELAY) continue;
        // Adding the full request duration is conservative: never display a just-expired notice.
        anchor = {server:server + elapsed, tick:env.clock()};
        let expired = false;
        for (const item of payload.items) {
          const time = now();
          if (!Number.isFinite(time)) return 'invalid';
          if (timestamp(item.starts_at) > server || timestamp(item.ends_at) <= server) return 'invalid';
          if (time >= timestamp(item.ends_at)) { expired = true; continue; }
          if (hidden(item, time)) continue;
          // Recheck immediately before DOM insertion, including any time spent inspecting candidates.
          const finalTime = now();
          if (!Number.isFinite(finalTime)) return 'invalid';
          if (finalTime >= timestamp(item.ends_at)) { expired = true; continue; }
          try {
            if (env.render(item, close, () => today(item)) === false) return 'skipped';
          } catch (_) { return 'error'; }
          shown = true; set('sessionStorage', SESSION_KEY, '1');
          return 'shown';
        }
        if (!expired) return payload.items.length ? 'hidden' : 'empty';
      }
      return 'expired';
    }
    return {load, suspend, close};
  }
  function domUI(document, region) {
    let restore = null;
    function hide() {
      const focusedInside = region.contains(document.activeElement);
      region.hidden = true;
      region.replaceChildren();
      if (focusedInside) {
        const target = restore && restore.isConnected ? restore : document.querySelector('[data-popup-return]');
        if (target) target.focus({preventScroll:true});
      }
    }
    function render(item, close, today) {
      if (!region.isConnected || document.hidden) return false;
      restore = document.activeElement && document.activeElement !== document.body && !region.contains(document.activeElement) ? document.activeElement : null;
      const nodes = [];
      function element(tag, text) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; nodes.push(node); return node; }
      element('h2', item.title).id = 'home-popup-title';
      if (item.message) element('p', item.message);
      if (item.image) { const img = element('img'); img.src=item.image.url; img.alt=item.image.alt; img.width=item.image.width; img.height=item.image.height; }
      const link=element('a','자세히 보기: ' + item.post.title);link.href=item.post.detail_path;
      const closeButton=element('button','닫기');closeButton.type='button';closeButton.addEventListener('click',close);
      const todayButton=element('button','오늘 하루 보지 않기');todayButton.type='button';todayButton.addEventListener('click',today);
      region.replaceChildren(...nodes);region.hidden=false;
      return true;
    }
    return {render, hide};
  }
  return {createController, domUI, nextMidnight, valid, SESSION_KEY, HIDE_PREFIX};
});

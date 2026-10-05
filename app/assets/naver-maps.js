/* DEV-05-A: provider SDK rendering only, no geocoding/storage/address lookup. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    const data = root.document.getElementById('naver-map-config');
    if (!data || root.__y3gymNaverMaps) return;
    root.__y3gymNaverMaps = true;
    try {
      const controller = api.createController(root);
      controller.render(JSON.parse(data.textContent));
      root.addEventListener('pagehide', () => controller.dispose());
      root.addEventListener('pageshow', event => { if (event.persisted) controller.render(JSON.parse(data.textContent)); });
    } catch (_) { /* Address/contact content remains usable. */ }
  }
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  const key = value => typeof value === 'string' && value.length >= 1 && value.length <= 128 && !/[^A-Za-z0-9_-]/.test(value);
  const ID = /^[1-9][0-9]*$/;
  function location(value) {
    return value && Object.keys(value).length === 2 &&
      typeof value.latitude === 'number' && Number.isFinite(value.latitude) && Math.abs(value.latitude) <= 90 &&
      typeof value.longitude === 'number' && Number.isFinite(value.longitude) && Math.abs(value.longitude) <= 180;
  }
  // Each window owns a single loader, including after failure or duplicate calls.
  const loaders = new WeakMap();
  function loadSDK(win, keyId) {
    if (!key(keyId)) return Promise.reject(new Error('configuration'));
    if (loaders.has(win)) {
      const current = loaders.get(win);
      return current.keyId === keyId && !current.failed ? current.promise : Promise.reject(new Error('configuration'));
    }
    const promise = new Promise((resolve, reject) => {
      let done = false;
      const script = win.document.createElement('script');
      const finish = ok => {
        if (done) return;
        done = true; win.clearTimeout(timer);
        script.onerror = null;
        // Keep inert callbacks for late arrivals; never resurrect timed-out maps.
        win.__y3gymNaverReady = () => {};
        win.navermap_authFailure = () => {};
        if (ok && win.naver && win.naver.maps) resolve(win.naver.maps);
        else { script.remove(); reject(new Error('unavailable')); }
      };
      const timer = win.setTimeout(() => finish(false), 10000);
      win.__y3gymNaverReady = () => finish(true);
      win.navermap_authFailure = () => finish(false);
      script.onerror = () => finish(false);
      script.async = true;
      script.src = 'https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=' + encodeURIComponent(keyId) + '&callback=__y3gymNaverReady';
      win.document.head.appendChild(script);
    });
    loaders.set(win, {keyId, promise});
    return promise;
  }
  function createController(win) {
    let generation = 0;
    const active = [];
    function clear() {
      for (const item of active.splice(0)) {
        try { if (item.marker) item.marker.setMap(null); } catch (_) {}
        try { if (item.map) item.map.destroy(); } catch (_) {}
        item.element.hidden = true;
        item.element.replaceChildren();
      }
    }
    async function render(config) {
      const version = ++generation;
      clear();
      if (!config || !key(config.keyId) || !Array.isArray(config.items)) return 'empty';
      const seen = new Set();
      const items = config.items.filter(item => {
        if (!item || typeof item.id !== 'string' || item.id.trim() !== item.id || !ID.test(item.id) || seen.has(item.id) || !location(item.location)) return false;
        seen.add(item.id); return true;
      }).map(item => ({id: item.id, location: {...item.location}, element: win.document.getElementById('naver-map-' + item.id)}))
        .filter(item => item.element && item.element.isConnected);
      if (!items.length) return 'empty';
      try {
        const sdk = await loadSDK(win, config.keyId);
        if (version !== generation) return 'stale';
        win.navermap_authFailure = () => {
          loaders.get(win).failed = true;
          if (version === generation) { generation++; clear(); }
        };
        for (const item of items) {
          if (!item.element.isConnected) continue;
          active.push(item);
          item.element.hidden = false;
          const point = new sdk.LatLng(item.location.latitude, item.location.longitude);
          item.map = new sdk.Map(item.element, {center: point, zoom: 16});
          item.marker = new sdk.Marker({map: item.map, position: point});
        }
        return 'shown';
      } catch (_) {
        if (version === generation) clear();
        return 'unavailable';
      }
    }
    return {render, dispose() { generation++; clear(); }};
  }
  return {createController, loadSDK, location};
});

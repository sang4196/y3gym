/* Geocoder results belong only to the current SDK Map/Marker; no result cache. */
(function (root, factory) {
  if (root && root.Y3GymNaverMaps) return;
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    root.Y3GymNaverMaps = api;
    const data = root.document.getElementById('naver-map-config');
    if (data) { try { api.mountPublic(root, JSON.parse(data.textContent)); } catch (_) {} }
  }
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  const key = v => typeof v === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(v) && !/\s/.test(v);
  const queryOK = v => typeof v === 'string' && v.trim().length > 0 && v.length <= 255 && !/[\x00-\x1f\x7f]/.test(v);
  // No fuzzy/prefix matching, province aliases or dropping building/street numbers.
  const normalize = v => v.normalize('NFC').trim().replace(/\s+/gu, ' ');
  function pointFor(query, response) {
    const r = response && response.v2;
    if (!queryOK(query) || !r || r.status !== 'OK' || !r.meta || r.meta.totalCount !== 1 || r.meta.count !== 1 || r.meta.page !== 1 || !Array.isArray(r.addresses) || r.addresses.length !== 1) return null;
    const row = r.addresses[0];
    if (!row || !['roadAddress','jibunAddress'].some(k => queryOK(row[k]) && normalize(row[k]) === normalize(query))) return null;
    const number = v => typeof v === 'string' && /^-?\d{1,3}(\.\d{1,16})?$/.test(v) ? Number(v) : NaN;
    const lat = number(row.y), lng = number(row.x);
    return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? {lat,lng} : null;
  }
  const loaders = new WeakMap();
  function loadSDK(win, keyId) {
    if (!key(keyId)) return Promise.reject(new Error('configuration'));
    if (loaders.has(win)) {
      const s = loaders.get(win);
      return s.keyId === keyId && !s.failed ? s.promise : Promise.reject(new Error('unavailable'));
    }
    const s = {keyId,failed:false,listeners:new Set()}; loaders.set(win,s);
    s.promise = new Promise((resolve,reject) => {
      let done = false;
      const script = win.document.createElement('script');
      const finish = ok => {
        if (done) return;
        done = true; win.clearTimeout(timer); script.onerror = null;
        win.__y3gymNaverReady = () => {};
        const sdk = win.naver && win.naver.maps;
        if (ok && sdk && sdk.Service && typeof sdk.Service.geocode === 'function') resolve(sdk);
        else { s.failed = true; script.remove(); reject(new Error('unavailable')); }
      };
      const timer = win.setTimeout(() => finish(false),10000);
      win.__y3gymNaverReady = () => finish(true);
      win.navermap_authFailure = () => { s.failed = true; finish(false); for (const cb of s.listeners) cb(); };
      script.onerror = () => finish(false); script.async = true;
      script.src = 'https://oapi.map.naver.com/openapi/v3/maps.js?ncpKeyId=' + encodeURIComponent(keyId) + '&submodules=geocoder&callback=__y3gymNaverReady';
      win.document.head.appendChild(script);
    });
    return s.promise;
  }
  function createMap(win, element, notify = () => {}) {
    let generation = 0, suspended = false, pending = null, map = null, marker = null, sdkState = null;
    function clear() {
      try { if (marker) marker.setMap(null); } catch (_) {}
      try { if (map) map.destroy(); } catch (_) {}
      marker = null; map = null; element.hidden = true; element.replaceChildren();
    }
    function reset(state = 'idle') {
      generation++;
      if (pending) { const cancel = pending; pending = null; cancel('stale'); }
      clear(); notify(state);
    }
    const authFailure = () => reset('unavailable');
    function show(query, keyId) {
      if (suspended || !element.isConnected || !key(keyId) || !queryOK(query)) return Promise.resolve('disabled');
      if (pending) return Promise.resolve('busy');
      reset(); const version = generation; notify('loading');
      return new Promise(resolve => {
        let finished = false;
        const finish = state => {
          if (finished) return;
          finished = true; win.clearTimeout(timer); pending = null;
          if (version === generation) { if (state !== 'shown') clear(); notify(state,state === 'shown' ? query : undefined); }
          resolve(state);
        };
        const timer = win.setTimeout(() => finish('unavailable'),10000); pending = finish;
        loadSDK(win,keyId).then(sdk => {
          if (finished || version !== generation || suspended) return;
          sdkState = loaders.get(win); sdkState.listeners.add(authFailure);
          sdk.Service.geocode({query},(status,response) => {
            if (finished || version !== generation || suspended || !element.isConnected) return;
            try {
              const point = status === sdk.Service.Status.OK ? pointFor(query,response) : null;
              if (!point) return finish('unavailable');
              element.hidden = false;
              const position = new sdk.LatLng(point.lat,point.lng);
              map = new sdk.Map(element,{center:position,zoom:16});
              marker = new sdk.Marker({map,position});
              finish('shown'); // Never retain/return the response or candidate.
            } catch (_) { finish('unavailable'); }
          });
        }).catch(() => { if (!finished) finish('unavailable'); });
      });
    }
    return {show,reset,
      suspend() { suspended = true; reset(); if (sdkState) sdkState.listeners.delete(authFailure); },
      resume() { suspended = false; reset(); },
    };
  }
  function mountPublic(win,config) {
    if (!config || !key(config.keyId) || !Array.isArray(config.items)) return [];
    const controllers = [], seen = new Set();
    for (const item of config.items) {
      if (!item || typeof item.id !== 'string' || !/^[1-9][0-9]*$/.test(item.id) || seen.has(item.id) || !queryOK(item.query)) continue;
      seen.add(item.id);
      const area = win.document.querySelector('[data-public-map="' + item.id + '"]');
      if (!area) continue;
      const button = area.querySelector('[data-map-open]'), status = area.querySelector('[data-map-status]');
      const canvas = win.document.getElementById('naver-map-' + item.id);
      if (!button || !status || !canvas) continue;
      const query = item.query;
      const c = createMap(win,canvas,state => {
        button.disabled = state === 'loading' || state === 'shown';
        status.textContent = state === 'loading' ? '지도를 불러오는 중입니다.' : state === 'unavailable' ? '위치를 확인할 수 없습니다. 주소와 연락처를 이용해 주세요.' : '';
      });
      button.addEventListener('click',() => c.show(query,config.keyId)); controllers.push(c);
    }
    win.addEventListener('pagehide',() => controllers.forEach(c => c.suspend()));
    win.addEventListener('pageshow',e => { if (e.persisted) controllers.forEach(c => c.resume()); });
    return controllers;
  }
  return {loadSDK,pointFor,createMap,mountPublic,queryOK};
});

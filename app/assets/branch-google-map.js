(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    const boot = () => root.document.querySelectorAll('[data-branch-google-map]').forEach(area => api.mount(root, area, root.Y3GymGoogleMaps));
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', boot, {once:true}); else boot();
  }
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  function mount(win, area, maps) {
    if (!maps || area.dataset.bound) return;
    area.dataset.bound = 'true';
    const form = area.closest('form'), field = name => form.elements.namedItem(name);
    const input = field('google_map_input'), address = field('address'), version = field('edit_version');
    const intent = field('map_confirmation'), saved = area.querySelector('[data-saved-map-status]');
    const open = area.querySelector('[data-map-open]'), close = area.querySelector('[data-map-close]'), confirm = area.querySelector('[data-map-confirm]'), status = area.querySelector('[data-map-status]');
    let shown = null, requested = null, edited = false;
    function clearIntent() {
      intent.value = ''; ['map_confirmation_address','map_confirmation_version','map_confirmation_url'].forEach(name => field(name).value = '');
      confirm.disabled = true; shown = null;
    }
    function read() { return {url: maps.parseInput(input.value), address: address.value.trim(), version: version.value}; }
    function matches(a, b) { return a && b && a.url === b.url && a.address === b.address && a.version === b.version; }
    const controller = maps.createFrame(win, area.querySelector('[data-map-canvas]'), status, '입력한 지점 Google 지도', state => {
      clearIntent(); open.disabled = state === 'loading'; close.hidden = state === 'idle';
      open.textContent = state === 'idle' ? '입력한 지도 열기' : '지도 다시 열기';
      if (state === 'shown') {
        try { const now = read(); if (now.address && matches(now, requested)) { shown = now; confirm.disabled = false; } } catch (_) {}
      }
    });
    function invalidate() {
      requested = null; controller.reset(); clearIntent();
      saved.textContent = !edited && intent.dataset.savedConfirmed === 'true' ? '운영자 위치 확인됨' : '미등록 또는 미확인';
    }
    [input,address,version].forEach(el => ['input','change'].forEach(event => el.addEventListener(event, () => { edited = true; invalidate(); })));
    open.addEventListener('click', () => {
      clearIntent();
      try {
        requested = read();
        if (!requested.url || !requested.address) throw new Error('기본 주소와 Google 지도 퍼가기 코드를 입력하세요.');
        controller.show(requested.url);
      } catch (_) { controller.reset(); status.textContent = '기본 주소와 Google 지도 퍼가기 코드 또는 주소를 확인하세요.'; }
    });
    close.addEventListener('click', () => { invalidate(); open.focus(); });
    confirm.addEventListener('click', () => {
      try { if (confirm.disabled || !matches(read(), shown)) return invalidate(); } catch (_) { return invalidate(); }
      intent.value = 'true'; field('map_confirmation_address').value = shown.address;
      field('map_confirmation_url').value = shown.url; field('map_confirmation_version').value = shown.version;
      confirm.disabled = true; status.textContent = '위치를 확인했습니다. 지점 전체를 저장하면 반영됩니다.';
    });
    form.addEventListener('submit', () => {
      try { if (intent.value && !matches(read(), shown)) clearIntent(); } catch (_) { clearIntent(); }
    });
    form.addEventListener('reset', () => win.setTimeout(() => { edited = false; invalidate(); }, 0));
    win.addEventListener('pagehide', () => { controller.suspend(); clearIntent(); requested = null; });
    win.addEventListener('pageshow', e => { if (e.persisted) { controller.resume(); invalidate(); } });
    invalidate();
    return controller;
  }
  return {mount};
});

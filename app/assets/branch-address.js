(function (root,factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    const boot = () => root.document.querySelectorAll('[data-branch-map]').forEach(a => api.mount(root,a,root.Y3GymNaverMaps));
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded',boot,{once:true}); else boot();
  }
})(typeof window === 'undefined' ? null : window,function () {
  'use strict';
  function mount(win,area,maps) {
    if (!maps || area.dataset.bound) return;
    area.dataset.bound = 'true';
    const form = area.closest('form'), input = form.elements.namedItem('address'), version = form.elements.namedItem('edit_version');
    const intent = form.elements.namedItem('map_confirmation'), addressField = form.elements.namedItem('map_confirmation_address'), versionField = form.elements.namedItem('map_confirmation_version');
    const open = area.querySelector('[data-map-open]'), confirm = area.querySelector('[data-map-confirm]'), status = area.querySelector('[data-map-status]'), saved = area.querySelector('[data-saved-map-status]');
    const keyId = area.dataset.mapKey;
    let shownQuery = null, shownVersion = null, requestVersion = null;
    function clearIntent() { intent.value = ''; addressField.value = ''; versionField.value = ''; confirm.disabled = true; shownQuery = shownVersion = null; }
    function savedStatus() { saved.textContent = intent.dataset.savedConfirmed === 'true' && input.value.trim() === intent.dataset.savedAddress ? '저장된 주소 확인됨' : '미확인'; }
    const c = maps.createMap(win,area.querySelector('[data-map-canvas]'),(state,query) => {
      clearIntent(); savedStatus(); open.disabled = !keyId || state === 'loading';
      if (state === 'shown' && input.value.trim() === query && requestVersion === version.value) { shownQuery = query; shownVersion = requestVersion; confirm.disabled = false; }
      status.textContent = !keyId ? '지도 연결이 준비되지 않아 위치 확인은 할 수 없습니다. 주소는 확인 없이 저장할 수 있습니다.' :
        state === 'shown' ? '표시된 위치를 살펴보고 이 위치 확인을 누르세요.' : state === 'loading' ? '입력한 주소의 위치를 찾는 중입니다.' :
        state === 'unavailable' ? '위치를 확인할 수 없습니다. 전체 기본 주소를 확인하거나 잠시 후 다시 시도하세요. 주소는 확인 없이 저장할 수 있습니다.' : '위치를 확인한 다음 지점 전체를 저장하세요.';
    });
    function invalidate() { c.reset(); clearIntent(); savedStatus(); }
    invalidate(); input.addEventListener('input',invalidate); input.addEventListener('change',invalidate); version.addEventListener('change',invalidate);
    open.addEventListener('click',() => { requestVersion = version.value; return c.show(input.value.trim(),keyId); });
    confirm.addEventListener('click',() => {
      if (confirm.disabled || shownQuery !== input.value.trim() || shownVersion !== version.value) return invalidate();
      intent.value = 'true'; addressField.value = shownQuery; versionField.value = shownVersion; confirm.disabled = true;
      status.textContent = '위치를 확인했습니다. 지점을 저장하면 확인이 반영됩니다.';
    });
    form.addEventListener('submit',() => { if (intent.value && (addressField.value !== input.value.trim() || versionField.value !== version.value)) clearIntent(); });
    form.addEventListener('reset',() => win.setTimeout(invalidate,0));
    win.addEventListener('pagehide',() => { c.suspend(); clearIntent(); });
    win.addEventListener('pageshow',e => { if (e.persisted) c.resume(); });
    return c;
  }
  return {mount};
});

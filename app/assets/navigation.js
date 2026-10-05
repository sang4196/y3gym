(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    const boot = () => api.start(root);
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', boot, {once:true});
    else boot();
  }
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  function start(win) {
    const doc = win.document, header = doc.querySelector('[data-navigation]');
    if (!header || header.hasAttribute('data-nav-ready')) return;
    const toggle = header.querySelector('[data-menu-toggle]');
    const panel = header.querySelector('[data-menu-panel]');
    const brand = header.querySelector('.brand');
    if (!toggle || !panel || !brand) return;
    let media, opened = false, stopped = false;
    const listeners = [];
    function label(value) {
      toggle.setAttribute('aria-expanded', String(value));
      toggle.setAttribute('aria-label', value ? '메뉴 닫기' : '메뉴 열기');
    }
    function fallback() {
      stopped = true;
      panel.hidden = false;
      if (doc.activeElement === toggle) brand.focus({preventScroll:true});
      toggle.hidden = true;
      label(false);
      header.removeAttribute('data-nav-ready');
      for (const [target, event, fn] of listeners) target.removeEventListener(event, fn);
    }
    function listen(target, event, fn) {
      const guarded = event => { if (!stopped) { try { fn(event); } catch (_) { fallback(); } } };
      target.addEventListener(event, guarded);
      listeners.push([target, event, guarded]);
    }
    function close() {
      opened = false;
      // Preserve a useful focus destination before hiding a focused link.
      if (media.matches && panel.contains(doc.activeElement)) toggle.focus({preventScroll:true});
      panel.hidden = media.matches;
      label(false);
    }
    function sync() {
      if (media.matches) {
        toggle.hidden = false;
        close();
      } else {
        opened = false;
        panel.hidden = false;
        if (doc.activeElement === toggle) (panel.querySelector('a[href]') || brand).focus({preventScroll:true});
        toggle.hidden = true;
        label(false);
      }
    }
    try {
      // A newer script can arrive alongside old/missing CSS. In that case the
      // SSR links must stay visible instead of leaving an unstyled tiny toggle.
      if (typeof win.getComputedStyle !== 'function' ||
          win.getComputedStyle(header).getPropertyValue('--navigation-css-ready').trim() !== '1') {
        fallback(); return;
      }
      if (typeof win.matchMedia !== 'function') { fallback(); return; }
      media = win.matchMedia('(max-width: 60rem)');
      // Install every required listener before hiding any SSR navigation.
      listen(media, 'change', sync);
      listen(toggle, 'click', () => {
        if (!media.matches) return;
        if (opened) close();
        else { opened = true; panel.hidden = false; label(true); }
      });
      listen(doc, 'click', event => {
        if (!opened) return;
        const link = event.target.closest && event.target.closest('a[href]');
        if (!header.contains(event.target) || (link && panel.contains(link))) close();
        // Never cancel a link's default navigation (including fragments).
      });
      listen(doc, 'focusin', event => { if (opened && event.target !== toggle && !panel.contains(event.target)) close(); });
      listen(doc, 'keydown', event => {
        if (opened && event.key === 'Escape') { close(); event.preventDefault(); }
      });
      listen(win, 'pagehide', sync);
      listen(win, 'pageshow', sync);
      header.setAttribute('data-nav-ready', '');
      sync();
    } catch (_) { fallback(); }
    return {stop:fallback};
  }
  return {start};
});

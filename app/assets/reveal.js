(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else {
    const boot = () => api.start(root);
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', boot, {once:true}); else boot();
  }
})(typeof window === 'undefined' ? null : window, function () {
  'use strict';
  const started = new WeakSet();
  const excluded = 'header,footer,.hero,[data-home-popup],[data-google-map],[data-branch-google-map],.post-body,.post-detail,.preview-notice,form,[hidden],[data-reveal-off]';
  function start(win) {
    const doc = win.document;
    if (started.has(doc)) return;
    started.add(doc);
    const pending = new Set(), armed = new Set(), visibleSince = new Map(), listeners = [];
    let observer = null, timer = null, stopped = false;
    function detach() {
      if (timer !== null) { win.clearInterval(timer); timer = null; }
      if (observer) observer.disconnect();
    }
    function stop() {
      if (stopped) return;
      stopped = true;
      // CSS fallback covers every armed element even if cleanup encounters an error.
      doc.documentElement.setAttribute('data-reveal-disabled', '');
      try { detach(); } catch (_) {}
      for (const el of armed) {
        el.removeAttribute('data-reveal-state'); el.style.removeProperty('--reveal-delay');
      }
      pending.clear(); visibleSince.clear();
      for (const [target, event, fn] of listeners) target.removeEventListener(event, fn);
    }
    const safe = fn => (...args) => { if (!stopped) { try { fn(...args); } catch (_) { stop(); } } };
    function listen(target, event, fn) {
      const guarded = safe(fn); target.addEventListener(event, guarded, {passive:true});
      listeners.push([target,event,guarded]);
    }
    function reveal(el, animate) {
      const wasPending = pending.delete(el);
      if (!wasPending && (animate || !armed.has(el))) return;
      visibleSince.delete(el);
      if (animate) el.setAttribute('data-reveal-state','entering');
      else { el.removeAttribute('data-reveal-state'); el.style.removeProperty('--reveal-delay'); }
      if (wasPending && observer) observer.unobserve(el);
      if (!pending.size) detach();
    }
    function related(target) {
      if (!target || typeof target.contains !== 'function') return;
      for (const el of armed) if (el.contains(target) || target.contains(el)) reveal(el,false);
    }
    function hashTarget(hash) {
      if (!hash || hash === '#') return;
      related(doc.getElementById(decodeURIComponent(hash.slice(1))));
    }
    function sweep() {
      // Give normal observer delivery 500ms before failing visible. A target
      // already scrolled past is exposed immediately, without a stale animation.
      const now = win.performance && win.performance.now ? win.performance.now() : Date.now();
      for (const el of [...pending]) {
        const rect = el.getBoundingClientRect();
        if (!Number.isFinite(rect.top)) throw new Error('Invalid geometry');
        if (rect.top >= win.innerHeight) { visibleSince.delete(el); continue; }
        if (rect.bottom <= 0) { reveal(el,false); continue; }
        if (!visibleSince.has(el)) visibleSince.set(el,now);
        else if (now - visibleSince.get(el) >= 500) reveal(el,false);
      }
    }
    try {
      if (typeof win.IntersectionObserver !== 'function' || typeof win.matchMedia !== 'function') { stop(); return {stop}; }
      const reduced = win.matchMedia('(prefers-reduced-motion: reduce)');
      const printing = win.matchMedia('print');
      if (reduced.matches || printing.matches || doc.hidden) { stop(); return {stop}; }
      // If change notifications cannot be installed, leave everything visible.
      listen(reduced,'change',e => { if (e.matches) stop(); });
      listen(printing,'change',e => { if (e.matches) stop(); });
      listen(doc,'focusin',e => related(e.target));
      listen(win,'hashchange',() => hashTarget(win.location.hash));
      listen(doc,'click',e => {
        const a = e.target.closest && e.target.closest('a[href]');
        if (!a) return;
        const url = new URL(a.href,win.location.href), here = new URL(win.location.href);
        if (url.origin === here.origin && url.pathname === here.pathname && url.search === here.search) hashTarget(url.hash);
      });
      listen(win,'beforeprint',stop);
      listen(win,'pagehide',stop);
      listen(win,'pageshow',e => { if (e.persisted) stop(); });
      listen(doc,'visibilitychange',() => { if (doc.hidden) stop(); });
      listen(win,'resize',sweep);
      observer = new win.IntersectionObserver(safe(entries => {
        for (const entry of entries) {
          if (entry.isIntersecting || entry.boundingClientRect.top < win.innerHeight) reveal(entry.target,entry.isIntersecting && entry.boundingClientRect.bottom > 0);
        }
      }), {threshold:0, rootMargin:'0px'});
      const groups = new Map();
      for (const el of doc.querySelectorAll('[data-reveal]')) {
        if (el.closest(excluded) || el.querySelector(excluded) || (el.parentElement && el.parentElement.closest('[data-reveal]'))) continue;
        const rect = el.getBoundingClientRect();
        if (!Number.isFinite(rect.top)) throw new Error('Invalid geometry');
        if (rect.top < win.innerHeight || rect.height <= 0 || el.contains(doc.activeElement)) continue;
        const index = groups.get(el.parentElement) || 0;
        groups.set(el.parentElement,index+1);
        pending.add(el); armed.add(el);
        observer.observe(el); // A failure here leaves the entire page visible.
        if (pending.has(el)) {
          el.style.setProperty('--reveal-delay',Math.min(index*70,210)+'ms');
          el.setAttribute('data-reveal-state','waiting');
        }
      }
      if (doc.activeElement && doc.activeElement !== doc.body && doc.activeElement !== doc.documentElement) related(doc.activeElement);
      hashTarget(win.location.hash);
      if (pending.size) timer = win.setInterval(safe(sweep),250); else detach();
    } catch (_) { stop(); }
    return {stop};
  }
  return {start};
});

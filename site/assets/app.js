try { document.documentElement.dataset.theme = (localStorage.getItem('sh.theme') || (window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')); } catch (e) { document.documentElement.dataset.theme = 'light'; }

/* Study Hub app: vanilla JS, no dependencies, works from file://. */
(function () {
  'use strict';

  /* ---------- helpers ---------- */
  var doc = document;
  function $(sel, root) { return (root || doc).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || doc).querySelectorAll(sel)); }
  function el(tag, attrs, children) {
    var n = doc.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'text') n.textContent = attrs[k];
      else if (k === 'class') n.className = attrs[k];
      else if (k.slice(0, 2) === 'on') n.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== null && attrs[k] !== undefined) n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { n.appendChild(typeof c === 'string' ? doc.createTextNode(c) : c); });
    return n;
  }
  function store(key, val) {
    try {
      if (arguments.length === 1) { var v = localStorage.getItem(key); return v === null ? null : v; }
      localStorage.setItem(key, val);
    } catch (e) { /* storage unavailable */ }
    return null;
  }
  function loadJSON(key, fallback) {
    try { var v = JSON.parse(store(key)); return v === null || v === undefined ? fallback : v; } catch (e) { return fallback; }
  }
  function isTyping(t) {
    return !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT' || t.isContentEditable);
  }
  function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  var body = doc.body;
  var ROOT = (body && body.dataset.root) || '';
  var PAGE_ID = (body && body.dataset.pageId) || '';
  var PAGE_TYPE = (body && body.dataset.pageType) || '';
  var NAV = Array.isArray(window.NAV) ? window.NAV : [];
  var PAGES = Array.isArray(window.PAGES_FLAT) ? window.PAGES_FLAT : [];
  var INDEX = Array.isArray(window.SEARCH_INDEX) ? window.SEARCH_INDEX : [];

  /* ---------- nav model ---------- */
  var pageById = {};       // id -> {id,title,path}
  var trackPages = {};     // track key -> [ids]
  var allPageIds = [];

  function indexNav(nodes, track) {
    nodes.forEach(function (n) {
      var t = n.track || track || '';
      if (n.path && n.id) {
        pageById[n.id] = n;
        allPageIds.push(n.id);
        [t, n.path.split('/')[0]].forEach(function (k) {
          if (!k) return;
          (trackPages[k] = trackPages[k] || []);
          if (trackPages[k].indexOf(n.id) < 0) trackPages[k].push(n.id);
        });
      }
      if (n.children && n.children.length) indexNav(n.children, t);
    });
  }
  function orderedPages() {
    if (PAGES.length) return PAGES;
    return allPageIds.map(function (id) { return pageById[id]; });
  }

  /* ---------- theme ---------- */
  function currentTheme() { return doc.documentElement.dataset.theme === 'dark' ? 'dark' : 'light'; }
  function applyTheme(t) {
    doc.documentElement.dataset.theme = t;
    store('sh.theme', t);
    var b = $('#theme-toggle');
    if (b) {
      b.textContent = t === 'dark' ? '☀' : '☾';
      b.setAttribute('aria-label', t === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
      b.setAttribute('title', b.getAttribute('aria-label'));
    }
  }
  function initTheme() {
    var b = $('#theme-toggle');
    applyTheme(currentTheme());
    if (b) b.addEventListener('click', function () {
      applyTheme(currentTheme() === 'dark' ? 'light' : 'dark');
      renderMermaid();
    });
  }

  /* ---------- progress ---------- */
  var done = new Set();
  function loadDone() {
    var a = loadJSON('sh.done', []);
    done = new Set(Array.isArray(a) ? a.filter(function (x) { return typeof x === 'string'; }) : []);
  }
  function saveDone() { store('sh.done', JSON.stringify(Array.from(done))); }
  function toggleDone(id) {
    if (done.has(id)) done.delete(id); else done.add(id);
    saveDone();
    refreshProgress();
  }
  function countDone(ids) { var n = 0; ids.forEach(function (i) { if (done.has(i)) n++; }); return n; }

  function initMarkDone() {
    var b = $('#mark-done');
    if (!b) return;
    var id = b.dataset.id || PAGE_ID;
    b.addEventListener('click', function () { toggleDone(id); });
  }
  function updateMarkDone() {
    var b = $('#mark-done');
    if (!b) return;
    var d = done.has(b.dataset.id || PAGE_ID);
    b.textContent = d ? '✓ Done' : 'Mark as done';
    b.classList.toggle('is-done', d);
    b.setAttribute('aria-pressed', d ? 'true' : 'false');
  }
  function updateNavProgress() {
    $$('#nav-tree .nav-link').forEach(function (a) { a.classList.toggle('done', done.has(a.dataset.id)); });
    $$('#nav-tree .nav-folder').forEach(function (li) {
      var ids = li._ids || [], n = countDone(ids), c = $('.nav-count', li);
      if (c) c.textContent = n + '/' + ids.length + ' done';
      li.classList.toggle('complete', ids.length > 0 && n === ids.length);
    });
  }
  function updateHomeProgress() {
    $$('.track-card').forEach(function (card) {
      var ids = trackPages[card.dataset.track] || [];
      var n = countDone(ids), pct = ids.length ? Math.round(100 * n / ids.length) : 0;
      var bar = $('.progress', card), span = bar && $('span', bar);
      if (span) span.style.width = pct + '%';
      if (bar) { bar.setAttribute('role', 'progressbar'); bar.setAttribute('aria-valuenow', pct); bar.setAttribute('aria-valuemin', 0); bar.setAttribute('aria-valuemax', 100); bar.setAttribute('aria-label', 'Progress'); }
      var lab = $('.progress-label', card);
      if (!lab && bar) { lab = el('div', { class: 'progress-label' }); bar.parentNode.insertBefore(lab, bar.nextSibling); }
      if (lab) lab.textContent = n + '/' + ids.length + ' done (' + pct + '%)';
    });
    var o = $('#overall-progress');
    if (o) {
      var total = allPageIds.length, n = countDone(allPageIds), pct = total ? Math.round(100 * n / total) : 0;
      o.textContent = '';
      o.appendChild(doc.createTextNode('Overall: ' + pct + '% '));
      var bar = el('span', { class: 'progress', role: 'progressbar', 'aria-valuenow': pct, 'aria-valuemin': 0, 'aria-valuemax': 100 }, [el('span')]);
      bar.firstChild.style.width = pct + '%';
      o.appendChild(bar);
      o.appendChild(doc.createTextNode(n + '/' + total + ' lessons'));
    }
  }
  function refreshProgress() {
    updateMarkDone();
    updateNavProgress();
    if (PAGE_TYPE === 'home') { updateHomeProgress(); renderContinue(); }
  }

  /* export / import (home only) */
  function exportProgress() {
    var data = JSON.stringify({ app: 'study-hub', version: 1, exported: new Date().toISOString(), done: Array.from(done), last: store('sh.last') }, null, 2);
    var url = URL.createObjectURL(new Blob([data], { type: 'application/json' }));
    var a = el('a', { href: url, download: 'study-progress.json' });
    doc.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }
  function importProgress(file, msg) {
    var r = new FileReader();
    r.onload = function () {
      try {
        var j = JSON.parse(r.result), arr = Array.isArray(j) ? j : j.done;
        if (!Array.isArray(arr)) throw new Error('bad');
        var before = done.size;
        arr.forEach(function (x) { if (typeof x === 'string') done.add(x); });
        if (j && typeof j.last === 'string' && !store('sh.last')) store('sh.last', j.last);
        saveDone(); refreshProgress();
        msg.textContent = 'Imported. ' + (done.size - before) + ' new item(s) merged.';
      } catch (e) { msg.textContent = 'Import failed: not a valid progress file.'; }
    };
    r.readAsText(file);
  }
  function initProgressTools() {
    if (PAGE_TYPE !== 'home') return;
    var box = $('.progress-tools');
    if (!box) {
      box = el('div', { class: 'progress-tools' });
      var anchor = $('#tracks');
      if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(box, anchor);
      else { var art = $('#content article') || $('#content'); if (!art) return; art.appendChild(box); }
    }
    if (!$('#overall-progress')) box.appendChild(el('div', { id: 'overall-progress', class: 'overall' }));
    if ($('#export-progress')) return;
    var msg = el('span', { class: 'progress-msg', 'aria-live': 'polite' });
    var input = el('input', { type: 'file', accept: 'application/json,.json', id: 'import-file', tabindex: '-1' });
    input.addEventListener('change', function () { if (input.files && input.files[0]) importProgress(input.files[0], msg); input.value = ''; });
    box.appendChild(el('button', { class: 'btn', id: 'export-progress', type: 'button', text: 'Export progress', onclick: exportProgress }));
    box.appendChild(el('button', { class: 'btn', id: 'import-progress', type: 'button', text: 'Import progress', onclick: function () { input.click(); } }));
    box.appendChild(input);
    box.appendChild(msg);
  }

  /* ---------- continue ---------- */
  function renderContinue() {
    var box = $('#continue');
    if (!box) return;
    box.textContent = '';
    var pages = orderedPages();
    if (!pages.length) return;
    var lastId = store('sh.last'), last = null, lastIdx = -1;
    pages.forEach(function (p, i) { if (p.id === lastId) { last = p; lastIdx = i; } });
    var next = null, i, p;
    for (i = 1; i <= pages.length; i++) {
      p = pages[(lastIdx + i + pages.length) % pages.length];
      if (!done.has(p.id)) { next = p; break; }
    }
    box.appendChild(el('div', { class: 'cont-title', text: last ? 'Continue where you left off' : 'Start learning' }));
    var row = el('div', { class: 'cont-row' });
    if (last) row.appendChild(el('span', null, [el('span', { class: 'cont-label', text: 'Last visited:' }), el('a', { href: ROOT + last.path, text: last.title })]));
    if (next && (!last || next.id !== last.id)) row.appendChild(el('span', null, [el('span', { class: 'cont-label', text: last ? 'Next up:' : 'First lesson:' }), el('a', { href: ROOT + next.path, text: next.title })]));
    else if (!next) row.appendChild(el('span', { text: 'All lessons are marked done. Nice work!' }));
    box.appendChild(row);
  }
  function rememberVisit() {
    if ((PAGE_TYPE === 'doc' || PAGE_TYPE === 'code') && PAGE_ID) store('sh.last', PAGE_ID);
  }

  /* ---------- sidebar ---------- */
  var openFolders = new Set();
  function folderKey(n, depth, idx) { return n.id || ('f:' + depth + ':' + idx + ':' + n.title); }
  function leafIds(n, out) {
    if (n.path && n.id) out.push(n.id);
    (n.children || []).forEach(function (c) { leafIds(c, out); });
    return out;
  }
  function findAncestors(nodes, id, trail, depth) {
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i], key = folderKey(n, depth, i);
      if (n.id === id && n.path) return trail;
      if (n.children && n.children.length) {
        var r = findAncestors(n.children, id, trail.concat(key), depth + 1);
        if (r) return r;
      }
    }
    return null;
  }
  function setFolderOpen(li, open) {
    var btn = $('.nav-toggle', li), ul = li.lastChild;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    ul.hidden = !open;
    if (open) openFolders.add(li._key); else openFolders.delete(li._key);
  }
  function navLink(n) {
    var a = el('a', { class: 'nav-link', href: ROOT + n.path, 'data-id': n.id || '' }, [el('span', { class: 'nav-check', 'aria-hidden': 'true' }), el('span', { class: 'nav-label', text: n.title })]);
    if (n.id === PAGE_ID) { a.classList.add('active'); a.setAttribute('aria-current', 'page'); }
    return a;
  }
  function buildNode(n, depth, idx, ancestors) {
    var li = el('li'), kids = n.children && n.children.length;
    if (!kids) {
      if (!n.path) return null;
      li.appendChild(navLink(n));
      return li;
    }
    li.className = 'nav-folder';
    li._key = folderKey(n, depth, idx);
    li._ids = leafIds(n, []);
    var row = el('div', { class: 'nav-row' });
    var count = el('span', { class: 'nav-count' });
    var toggle = el('button', { type: 'button', class: 'nav-toggle' + (n.path ? ' chevron-only' : ''), 'aria-expanded': 'false' }, [el('span', { class: 'nav-chevron', 'aria-hidden': 'true', text: '▶' })]);
    if (n.path) {
      toggle.setAttribute('aria-label', 'Toggle ' + n.title);
      row.appendChild(toggle);
      row.appendChild(navLink(n));
      row.appendChild(count);
    } else {
      toggle.appendChild(el('span', { class: 'nav-label', text: n.title }));
      toggle.appendChild(count);
      row.appendChild(toggle);
    }
    li.appendChild(row);
    var ul = el('ul', { class: 'nav-children' });
    n.children.forEach(function (c, i) { var ch = buildNode(c, depth + 1, i, ancestors); if (ch) ul.appendChild(ch); });
    li.appendChild(ul);
    var open = openFolders.has(li._key) || ancestors.indexOf(li._key) >= 0;
    toggle.addEventListener('click', function () {
      setFolderOpen(li, toggle.getAttribute('aria-expanded') !== 'true');
      store('sh.nav', JSON.stringify(Array.from(openFolders)));
    });
    setFolderOpen(li, open);
    return li;
  }
  function allFolders() { return $$('#nav-tree .nav-folder'); }
  function setAllFolders(open) {
    allFolders().forEach(function (li) { setFolderOpen(li, open); });
    saveNavState();
  }
  function saveNavState() { store('sh.nav', JSON.stringify(Array.from(openFolders))); }
  function scrollSidebarTo(node, center) {
    var sb = $('#sidebar');
    if (!node || !sb) return;
    var r = node.getBoundingClientRect(), sbr = sb.getBoundingClientRect();
    sb.scrollTop += r.top - sbr.top - (center ? sb.clientHeight / 2 - r.height / 2 : 60);
  }
  function showTrack(key) {
    allFolders().forEach(function (li) { setFolderOpen(li, false); });
    var target = null;
    $$('#nav-tree .nav-root > .nav-folder').forEach(function (li) { if (li._key === key) target = li; });
    if (target) { setFolderOpen(target, true); scrollSidebarTo(target, false); }
    saveNavState();
  }
  function buildNavTools(currentTrack) {
    var tools = el('div', { class: 'nav-top' });
    var homeLink = el('a', { class: 'nav-home' + (PAGE_TYPE === 'home' ? ' active' : ''), href: ROOT + 'index.html' }, [el('span', { 'aria-hidden': 'true', text: '⌂ ' }), 'Home']);
    if (PAGE_TYPE === 'home') homeLink.setAttribute('aria-current', 'page');
    tools.appendChild(homeLink);
    var tracks = NAV.filter(function (n) { return n.children && n.children.length; });
    if (tracks.length) {
      var sel = el('select', { class: 'nav-track-select', 'aria-label': 'Jump to track' }, [el('option', { value: '', text: 'Jump to track…' })]);
      tracks.forEach(function (n) { sel.appendChild(el('option', { value: n.id, text: n.title })); });
      if (currentTrack) sel.value = currentTrack;
      sel.addEventListener('change', function () { if (sel.value) showTrack(sel.value); });
      tools.appendChild(sel);
    }
    tools.appendChild(el('div', { class: 'nav-actions' }, [
      el('button', { type: 'button', class: 'nav-action', text: 'Expand all', onclick: function () { setAllFolders(true); } }),
      el('button', { type: 'button', class: 'nav-action', text: 'Collapse all', onclick: function () { setAllFolders(false); } })
    ]));
    return tools;
  }
  function initSidebar() {
    var tree = $('#nav-tree');
    if (!tree || !NAV.length) return;
    var ancestors = findAncestors(NAV, PAGE_ID, [], 0) || [];
    var currentTrack = ancestors[0] || '';
    var saved = loadJSON('sh.nav', []);
    if (!Array.isArray(saved)) saved = [];
    // Show one level of detail by default: keep remembered folders only inside the current track.
    if (currentTrack) saved = saved.filter(function (k) { return k === currentTrack || k.indexOf(currentTrack + '/') === 0; });
    else if (PAGE_TYPE !== 'home') saved = [];
    openFolders = new Set(saved);
    var ul = el('ul', { class: 'nav-root' });
    NAV.forEach(function (n, i) { var li = buildNode(n, 0, i, ancestors); if (li) ul.appendChild(li); });
    tree.textContent = '';
    tree.appendChild(buildNavTools(currentTrack));
    tree.appendChild(ul);
    saveNavState();
    scrollSidebarTo($('.nav-link.active', tree), true);
    tree.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('a')) closeMenu(); });
  }

  /* ---------- mobile menu ---------- */
  function closeMenu() {
    body.classList.remove('nav-open');
    var b = $('#menu-toggle'); if (b) b.setAttribute('aria-expanded', 'false');
  }
  function initMenu() {
    var b = $('#menu-toggle');
    if (!b) return;
    b.setAttribute('aria-expanded', 'false');
    b.setAttribute('aria-controls', 'sidebar');
    if (!b.getAttribute('aria-label')) b.setAttribute('aria-label', 'Toggle navigation');
    if (!b.textContent.trim()) b.textContent = '☰';
    var bd = el('div', { class: 'nav-backdrop' });
    bd.addEventListener('click', closeMenu);
    body.appendChild(bd);
    b.addEventListener('click', function () {
      var open = body.classList.toggle('nav-open');
      b.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    doc.addEventListener('keydown', function (e) { if (e.key === 'Escape' && body.classList.contains('nav-open')) { closeMenu(); b.focus(); } });
  }

  /* ---------- skip link ---------- */
  function initSkipLink() {
    var main = $('#content');
    if (!main) return;
    if (!main.hasAttribute('tabindex')) main.setAttribute('tabindex', '-1');
    var a = el('a', { class: 'skip-link', href: '#content', text: 'Skip to content' });
    a.addEventListener('click', function (e) { e.preventDefault(); main.focus(); main.scrollIntoView(); });
    body.insertBefore(a, body.firstChild);
  }

  /* ---------- search ---------- */
  var sr = { active: -1, input: null, panel: null };
  function tokenize(q) { return q.toLowerCase().split(/\s+/).filter(Boolean); }
  function runSearch(q) {
    var toks = tokenize(q), out = [];
    if (!toks.length) return out;
    INDEX.forEach(function (e) {
      if (!e._l) e._l = { t: (e.title || '').toLowerCase(), s: (e.section || '').toLowerCase(), x: (e.text || '').toLowerCase() };
      var score = 0, i, tok, it, is, ix;
      for (i = 0; i < toks.length; i++) {
        tok = toks[i];
        it = e._l.t.indexOf(tok); is = e._l.s.indexOf(tok); ix = e._l.x.indexOf(tok);
        if (it < 0 && is < 0 && ix < 0) return;
        if (it >= 0) score += 20 + (it === 0 || /\W/.test(e._l.t.charAt(it - 1)) ? 6 : 0);
        if (is >= 0) score += 8;
        if (ix >= 0) score += 1 + (/\W/.test(e._l.x.charAt(ix - 1) || ' ') ? 1 : 0);
      }
      if (e._l.t === toks.join(' ')) score += 20;
      out.push({ e: e, score: score });
    });
    out.sort(function (a, b) { return b.score - a.score || (a.e.title || '').length - (b.e.title || '').length; });
    return out.slice(0, 12);
  }
  function highlight(text, toks) {
    var frag = doc.createDocumentFragment();
    if (!toks.length) { frag.appendChild(doc.createTextNode(text)); return frag; }
    // split with a capture group: odd indexes are the matches
    var parts = text.split(new RegExp('(' + toks.map(escRe).join('|') + ')', 'i'));
    parts.forEach(function (s, i) {
      if (!s) return;
      if (i % 2) frag.appendChild(el('mark', { text: s }));
      else frag.appendChild(doc.createTextNode(s));
    });
    return frag;
  }
  function snippet(text, toks) {
    text = (text || '').replace(/\s+/g, ' ');
    var low = text.toLowerCase(), idx = -1, i;
    for (i = 0; i < toks.length; i++) { var k = low.indexOf(toks[i]); if (k >= 0 && (idx < 0 || k < idx)) idx = k; }
    var start = Math.max(0, idx < 0 ? 0 : idx - 40);
    var s = text.slice(start, start + 120);
    return (start > 0 ? '…' : '') + s + (start + 120 < text.length ? '…' : '');
  }
  function setActive(i) {
    var nodes = $$('.sr-item', sr.panel);
    if (!nodes.length) return;
    sr.active = (i + nodes.length) % nodes.length;
    nodes.forEach(function (n, j) {
      n.classList.toggle('active', j === sr.active);
      n.setAttribute('aria-selected', j === sr.active ? 'true' : 'false');
    });
    var cur = nodes[sr.active];
    sr.input.setAttribute('aria-activedescendant', cur.id);
    if (cur.scrollIntoView) cur.scrollIntoView({ block: 'nearest' });
  }
  function closeSearch() {
    if (!sr.panel) return;
    sr.panel.hidden = true; sr.active = -1;
    sr.input.setAttribute('aria-expanded', 'false');
    sr.input.removeAttribute('aria-activedescendant');
  }
  function renderSearch() {
    var q = sr.input.value.trim(), toks = tokenize(q);
    if (!toks.length) { closeSearch(); return; }
    var res = runSearch(q);
    sr.panel.textContent = '';
    if (!res.length) sr.panel.appendChild(el('div', { class: 'sr-empty', text: 'No results for "' + q + '"' }));
    res.forEach(function (r, i) {
      var e = r.e, a = el('a', { class: 'sr-item', role: 'option', id: 'sr-opt-' + i, href: ROOT + e.path });
      var t = el('div', { class: 'sr-title' }); t.appendChild(highlight(e.title || '', toks));
      a.appendChild(t);
      if (e.section) { var s = el('div', { class: 'sr-section' }); s.appendChild(highlight(e.section, toks)); a.appendChild(s); }
      var sn = el('div', { class: 'sr-snippet' }); sn.appendChild(highlight(snippet(e.text, toks), toks)); a.appendChild(sn);
      a.addEventListener('mousemove', function () { if (sr.active !== i) setActive(i); });
      sr.panel.appendChild(a);
    });
    sr.panel.hidden = false;
    sr.input.setAttribute('aria-expanded', 'true');
    sr.active = -1;
    if (res.length) setActive(0);
  }
  function initSearch() {
    sr.input = $('#search'); sr.panel = $('#search-results');
    if (!sr.input || !sr.panel) return;
    sr.input.setAttribute('role', 'combobox');
    sr.input.setAttribute('aria-controls', 'search-results');
    sr.input.setAttribute('aria-expanded', 'false');
    sr.input.setAttribute('aria-autocomplete', 'list');
    sr.input.setAttribute('autocomplete', 'off');
    if (!sr.input.getAttribute('aria-label')) sr.input.setAttribute('aria-label', 'Search lessons');
    sr.panel.setAttribute('role', 'listbox');
    sr.input.addEventListener('input', renderSearch);
    sr.input.addEventListener('focus', function () { if (sr.input.value.trim()) renderSearch(); });
    sr.input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); if (sr.panel.hidden) renderSearch(); else setActive(sr.active + 1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(sr.active - 1); }
      else if (e.key === 'Enter') {
        var cur = $$('.sr-item', sr.panel)[Math.max(sr.active, 0)];
        if (cur && !sr.panel.hidden) { e.preventDefault(); window.location.href = cur.href; }
      } else if (e.key === 'Escape') {
        if (!sr.panel.hidden) closeSearch(); else sr.input.blur();
      }
    });
    doc.addEventListener('click', function (e) {
      if (e.target !== sr.input && !sr.panel.contains(e.target)) closeSearch();
    });
    doc.addEventListener('keydown', function (e) {
      var mod = (e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K');
      if (mod || (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey && !isTyping(e.target))) {
        e.preventDefault(); closeMenu(); sr.input.focus(); sr.input.select();
      }
    });
  }

  /* ---------- article: anchors, toc ---------- */
  function slug(s) { return s.toLowerCase().trim().replace(/[^\wÀ-￿]+/g, '-').replace(/^-+|-+$/g, '') || 'section'; }
  function articleEl() { return $('#content .doc') || $('#content article'); }
  function initHeadings() {
    var art = articleEl(); if (!art) return;
    var used = {};
    $$('[id]', art).forEach(function (n) { used[n.id] = true; });
    $$('h2, h3, h4', art).forEach(function (h) {
      if (!h.id) {
        var base = slug(h.textContent), id = base, i = 1;
        while (used[id]) id = base + '-' + (++i);
        used[id] = true; h.id = id;
      }
      if (!$('a.anchor', h)) {
        var a = el('a', { class: 'anchor', href: '#' + h.id, 'aria-label': 'Link to this section', text: '#' });
        h.insertBefore(a, h.firstChild);
      }
    });
  }
  function initToc() {
    var toc = $('#toc'), art = articleEl();
    if (!toc || !art) return;
    var heads = $$('h2, h3', art).filter(function (h) { return h.id; });
    if (heads.length < 2) return;
    toc.textContent = '';
    toc.setAttribute('aria-label', 'On this page');
    toc.appendChild(el('p', { class: 'toc-title', text: 'On this page' }));
    var ul = el('ul'), links = {};
    heads.forEach(function (h) {
      var txt = h.textContent.replace(/^#/, '').trim();
      var a = el('a', { href: '#' + h.id, class: 'toc-' + h.tagName.toLowerCase(), text: txt });
      links[h.id] = a;
      ul.appendChild(el('li', null, [a]));
    });
    toc.appendChild(ul);
    if (!('IntersectionObserver' in window)) return;
    var current = null, visible = {};
    function activate(id) {
      if (current === id || !links[id]) return;
      if (current && links[current]) { links[current].classList.remove('active'); links[current].removeAttribute('aria-current'); }
      current = id; links[id].classList.add('active'); links[id].setAttribute('aria-current', 'true');
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { visible[en.target.id] = en.isIntersecting; });
      for (var i = 0; i < heads.length; i++) if (visible[heads[i].id]) { activate(heads[i].id); return; }
      var best = null;
      heads.forEach(function (h) { if (h.getBoundingClientRect().top < 120) best = h.id; });
      if (best) activate(best);
    }, { rootMargin: '-60px 0px -70% 0px', threshold: 0 });
    heads.forEach(function (h) { io.observe(h); });
  }

  /* ---------- pager shortcuts ---------- */
  function initPagerKeys() {
    doc.addEventListener('keydown', function (e) {
      if (isTyping(e.target) || e.ctrlKey || e.metaKey) return;
      var dir = null;
      if (e.altKey && e.key === 'ArrowRight') dir = 'next';
      else if (e.altKey && e.key === 'ArrowLeft') dir = 'prev';
      else if (!e.altKey && !e.shiftKey && e.key === 'j') dir = 'next';
      else if (!e.altKey && !e.shiftKey && e.key === 'k') dir = 'prev';
      if (!dir) return;
      var a = $('.pager a.' + dir);
      if (a && a.getAttribute('href')) { e.preventDefault(); window.location.href = a.href; }
    });
  }

  /* ---------- code blocks ---------- */
  var LANGS = { py: 'Python', js: 'JavaScript', ts: 'TypeScript', json: 'JSON', sh: 'Shell', bash: 'Bash', sql: 'SQL', html: 'HTML', css: 'CSS', yml: 'YAML', yaml: 'YAML', md: 'Markdown', java: 'Java', c: 'C', cpp: 'C++', go: 'Go', rs: 'Rust', ipynb: 'Notebook', txt: 'Text', toml: 'TOML', ini: 'INI', cfg: 'Config' };
  function pageLangLabel() {
    var info = pageById[PAGE_ID] || {};
    var h1 = $('#content h1');
    var cands = [PAGE_ID, info.path || '', info.title || '', h1 ? h1.textContent : ''];
    for (var i = 0; i < cands.length; i++) {
      var m = (cands[i] || '').trim().match(/\.([A-Za-z0-9]+)(?:\.html)?$/);
      if (m && LANGS[m[1].toLowerCase()]) return LANGS[m[1].toLowerCase()];
    }
    return '';
  }
  function copyText(text, btn) {
    function ok() {
      btn.textContent = 'Copied'; btn.classList.add('copied');
      setTimeout(function () { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 1500);
    }
    function fallback() {
      var ta = el('textarea', { style: 'position:fixed;opacity:0;top:0;left:0' });
      ta.value = text; body.appendChild(ta); ta.select();
      try { doc.execCommand('copy'); ok(); } catch (e) { btn.textContent = 'Press Ctrl+C'; }
      ta.remove();
    }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(ok, fallback);
    else fallback();
  }
  function initCodeBlocks() {
    var art = articleEl(); if (!art) return;
    var pageLang = PAGE_TYPE === 'code' ? pageLangLabel() : '';
    var targets = [];
    $$('.highlight', art).forEach(function (h) { targets.push({ box: h, pre: $('pre', h) }); });
    $$('pre', art).forEach(function (p) {
      if (p.classList.contains('mermaid') || p.closest('.highlight') || p.closest('.code-wrap')) return;
      var wrap = el('div', { class: 'code-wrap' });
      p.parentNode.insertBefore(wrap, p); wrap.appendChild(p);
      targets.push({ box: wrap, pre: p });
    });
    var first = true;
    targets.forEach(function (t) {
      if (!t.pre) return;
      var btn = el('button', { type: 'button', class: 'copy-btn', 'aria-label': 'Copy code to clipboard', text: 'Copy' });
      btn.addEventListener('click', function () { copyText(t.pre.innerText.replace(/\n$/, ''), btn); });
      t.box.appendChild(btn);
      var lang = '';
      var c = $('code', t.pre), cls = ((c && c.className) || '') + ' ' + t.box.className + ' ' + t.pre.className;
      var m = cls.match(/language-([\w+-]+)/);
      if (m) lang = LANGS[m[1].toLowerCase()] || m[1];
      if (!lang && first && pageLang) lang = pageLang;
      if (lang) t.box.appendChild(el('span', { class: 'code-lang', text: lang }));
      first = false;
    });
  }

  /* ---------- mermaid ---------- */
  var mermaidState = 'idle'; // idle | loading | ready | failed
  function mermaidPres() { return $$('pre.mermaid'); }
  function renderMermaid() {
    var pres = mermaidPres();
    if (!pres.length || mermaidState === 'failed' || mermaidState === 'loading') return;
    if (mermaidState !== 'ready') {
      mermaidState = 'loading';
      var s = el('script', { src: 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js' });
      s.onload = function () {
        mermaidState = window.mermaid ? 'ready' : 'failed';
        if (mermaidState === 'ready') renderMermaid(); else mermaidFail();
      };
      s.onerror = function () { mermaidState = 'failed'; mermaidFail(); };
      doc.head.appendChild(s);
      return;
    }
    pres.forEach(function (p) {
      if (p._src === undefined) p._src = p.textContent;
      p.removeAttribute('data-processed');
      p.textContent = p._src;
    });
    try {
      window.mermaid.initialize({ startOnLoad: false, theme: currentTheme() === 'dark' ? 'dark' : 'default' });
      var r = window.mermaid.run({ nodes: pres });
      if (r && r.catch) r.catch(function () { mermaidFail(); });
    } catch (e) { mermaidFail(); }
  }
  function mermaidFail() {
    mermaidPres().forEach(function (p) {
      if (p._src !== undefined) { p.textContent = p._src; p.removeAttribute('data-processed'); }
      var n = p.nextElementSibling;
      if (!n || !n.classList.contains('mermaid-note'))
        p.parentNode.insertBefore(el('div', { class: 'mermaid-note', text: 'Diagram needs internet' }), p.nextSibling);
    });
  }
  function initMermaid() {
    var pres = mermaidPres();
    if (!pres.length) return;
    pres.forEach(function (p) { p._src = p.textContent; });
    renderMermaid();
  }

  /* ---------- Q&A mode ---------- */
  var Q_HEAD = /^\s*(?:Q\s*\d*\s*[.:)\-–—]|Q\d+\b|\d+\s*[.):\-–])/i;
  var Q_BOLD = /^\s*(?:Q\s*\d*\s*[.:)\-]|Q\d+\b|\d+\s*[.):])/i;
  function wrapGroup(start, isBoundary, keepHeading) {
    var d = el('details', { class: 'qa-item' }), sum = el('summary');
    start.parentNode.insertBefore(d, start);
    if (keepHeading) sum.appendChild(start);
    else { while (start.firstChild) sum.appendChild(start.firstChild); start.remove(); }
    d.appendChild(sum);
    var n = d.nextSibling, nxt;
    while (n && !isBoundary(n)) { nxt = n.nextSibling; d.appendChild(n); n = nxt; }
    return d;
  }
  function isHeading(n) { return n.nodeType === 1 && /^H[1-6]$/.test(n.tagName); }
  function initQA() {
    if (!/interview-qa\.html$/i.test(window.location.pathname)) return;
    var art = articleEl(); if (!art || $('.qa-item', art)) return;
    var items = [];
    var levels = { H2: [], H3: [], H4: [] };
    $$('h2, h3, h4', art).forEach(function (h) { if (Q_HEAD.test(h.textContent.replace(/^#/, ''))) levels[h.tagName].push(h); });
    var best = ['H3', 'H2', 'H4'].reduce(function (a, b) { return levels[b].length > levels[a].length ? b : a; }, 'H2');
    if (levels[best].length >= 2) {
      var rank = +best.charAt(1);
      var isB = function (n) { return isHeading(n) && +n.tagName.charAt(1) <= rank; };
      levels[best].forEach(function (h) { items.push(wrapGroup(h, isB, true)); });
    } else {
      var ps = $$('p', art).filter(function (p) {
        var f = p.firstElementChild;
        return f && f.tagName === 'STRONG' && p.firstChild === f && Q_BOLD.test(f.textContent) && p.parentNode === art;
      });
      if (ps.length < 2) return;
      var isP = function (n) { return ps.indexOf(n) >= 0 || isHeading(n); };
      ps.forEach(function (p) { items.push(wrapGroup(p, isP, false)); });
    }
    if (items.length < 2) return;
    var bar = el('div', { class: 'qa-controls', role: 'group', 'aria-label': 'Question controls' });
    function setAll(open) { items.forEach(function (d) { d.open = open; }); }
    bar.appendChild(el('button', { type: 'button', text: 'Expand all', onclick: function () { setAll(true); } }));
    bar.appendChild(el('button', { type: 'button', text: 'Collapse all', onclick: function () { setAll(false); } }));
    bar.appendChild(el('button', { type: 'button', text: 'Shuffle', onclick: function () {
      var slots = items.map(function (d) { var m = doc.createComment(''); d.parentNode.insertBefore(m, d); return m; });
      var order = items.slice();
      for (var k = order.length - 1; k > 0; k--) { var j = Math.floor(Math.random() * (k + 1)); var t = order[k]; order[k] = order[j]; order[j] = t; }
      slots.forEach(function (m, idx) { m.parentNode.replaceChild(order[idx], m); });
      items = order; setAll(false);
    } }));
    var h1 = $('h1', art);
    if (h1 && h1.parentNode) h1.parentNode.insertBefore(bar, h1.nextSibling);
    else art.insertBefore(bar, items[0]);
  }
  function openHashTarget() {
    if (!window.location.hash) return;
    var id; try { id = decodeURIComponent(window.location.hash.slice(1)); } catch (e) { return; }
    var t = doc.getElementById(id); if (!t) return;
    var d = t.closest('details'), changed = false;
    while (d) { if (!d.open) { d.open = true; changed = true; } d = d.parentElement && d.parentElement.closest('details'); }
    if (changed) t.scrollIntoView();
  }

  /* ---------- boot ---------- */
  function safe(fn) { try { fn(); } catch (e) { if (window.console) console.error(e); } }
  doc.addEventListener('DOMContentLoaded', function () {
    safe(initTheme);
    safe(function () { indexNav(NAV, ''); });
    safe(loadDone);
    safe(initSkipLink);
    safe(initMenu);
    safe(initSidebar);
    safe(initSearch);
    safe(initMarkDone);
    safe(initProgressTools);
    safe(rememberVisit);
    safe(initHeadings);
    safe(initToc);
    safe(initCodeBlocks);
    safe(initQA);
    safe(initPagerKeys);
    safe(initMermaid);
    safe(refreshProgress);
    safe(openHashTarget);
    window.addEventListener('hashchange', openHashTarget);
    window.addEventListener('storage', function (e) { if (e.key === 'sh.done') { loadDone(); refreshProgress(); } });
  });
})();

(function () {
  'use strict';

  /**
   * Sub-navigation map.
   * Key = directory name of the parent nav-link (matches `<basename>` or `<basename>/`).
   * Value = list of sub-pages relative to that parent directory.
   * `match` is the URL ending used to detect the active sub-page.
   */
  var SUBNAV = {
    'health': [
      { sub: '',           label: '体組成', match: 'health' },
      { sub: 'nutrition/', label: '栄養素', match: 'health/nutrition' },
      { sub: 'strength/',  label: '筋トレ', match: 'health/strength' }
    ]
  };

  function normalizedPath() {
    return window.location.pathname
      .replace(/index\.html$/, '')
      .replace(/\/$/, '');
  }

  function detectSubnavKey(a) {
    // Match by visible link text — robust across different relative-path forms
    var txt = (a.textContent || '').trim();
    return SUBNAV[txt] ? txt : null;
  }

  function enhanceDrawer() {
    var drawer = document.querySelector('.drawer');
    if (!drawer) return;
    var current = normalizedPath();

    drawer.querySelectorAll('.nav-link').forEach(function (a) {
      if (a.classList.contains('disabled')) return;
      var href = a.getAttribute('href') || '';
      var key = detectSubnavKey(a);
      if (!key) return;
      // Avoid double-injection if called twice
      if (a.nextElementSibling && a.nextElementSibling.classList.contains('nav-sub-list')) return;

      var parentDir = href.replace(/index\.html$/, '');
      // Ensure trailing slash
      if (parentDir && !parentDir.endsWith('/')) parentDir += '/';

      var container = document.createElement('div');
      container.className = 'nav-sub-list';

      SUBNAV[key].forEach(function (sub) {
        var link = document.createElement('a');
        link.className = 'nav-sub';
        link.href = parentDir + sub.sub;
        link.textContent = sub.label;
        if (current.endsWith('/' + sub.match)) {
          link.classList.add('active');
        }
        container.appendChild(link);
      });

      a.insertAdjacentElement('afterend', container);

      if (container.querySelector('.nav-sub.active')) {
        a.classList.add('has-active-sub');
      }
    });
  }

  function init() {
    var toggle = document.querySelector('.menu-toggle');
    var overlay = document.querySelector('.drawer-overlay');
    var body = document.body;

    if (toggle) {
      toggle.addEventListener('click', function () {
        body.classList.toggle('drawer-open');
      });
    }

    if (overlay) {
      overlay.addEventListener('click', function () {
        body.classList.remove('drawer-open');
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') body.classList.remove('drawer-open');
    });

    enhanceDrawer();

    document.querySelectorAll('.drawer a').forEach(function (a) {
      a.addEventListener('click', function () {
        body.classList.remove('drawer-open');
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

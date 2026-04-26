(function () {
  'use strict';

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

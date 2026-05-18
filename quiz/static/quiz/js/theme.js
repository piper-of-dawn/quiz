(function () {
  function themeFromLocalTime(date) {
    const hour = date.getHours();
    return hour >= 7 && hour < 19 ? 'light' : 'dark';
  }

  function initTheme() {
    const scope = document.body && document.body.dataset.themeScope || 'quiz';
    const key = scope === 'homepage' ? 'homepage_theme' : 'theme';
    const target = scope === 'homepage' ? document.body : document.documentElement;
    const btn = document.getElementById('themeToggleBtn');
    let saved = null;
    try { saved = localStorage.getItem(key); } catch (_) {}
    const theme = saved === 'light' || saved === 'dark' ? saved : themeFromLocalTime(new Date());

    function apply(next) {
      target.setAttribute('data-theme', next);
      if (document.body) document.body.setAttribute('data-theme', next);
      if (btn) btn.textContent = next === 'dark' ? 'Light mode' : 'Dark mode';
      window.dispatchEvent(new Event('themechange'));
    }

    apply(theme);
    if (btn) {
      btn.addEventListener('click', function () {
        const current = (target.getAttribute('data-theme') || theme) === 'dark' ? 'dark' : 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(key, next); } catch (_) {}
        apply(next);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme, { once: true });
  } else {
    initTheme();
  }
})();

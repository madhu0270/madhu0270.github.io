(function () {
  var yearEl = document.getElementById("year");
  if (yearEl) {
    yearEl.textContent = String(new Date().getFullYear());
  }

  var themeKey = "mdhakite-theme";
  var root = document.documentElement;
  var themeToggle = document.getElementById("themeToggle");

  function applyTheme(dark) {
    if (dark) {
      root.setAttribute("data-theme", "dark");
    } else {
      root.removeAttribute("data-theme");
    }
  }

  function syncThemeToggle() {
    if (!themeToggle) return;
    var dark = root.getAttribute("data-theme") === "dark";
    themeToggle.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    themeToggle.setAttribute("title", dark ? "Light mode" : "Dark mode");
  }

  try {
    var stored = localStorage.getItem(themeKey);
    if (stored === "dark") {
      applyTheme(true);
    } else if (stored === "light") {
      applyTheme(false);
    }
  } catch (e) {
    /* ignore */
  }

  if (themeToggle) {
    syncThemeToggle();
    themeToggle.addEventListener("click", function () {
      var dark = root.getAttribute("data-theme") === "dark";
      if (dark) {
        applyTheme(false);
        try {
          localStorage.setItem(themeKey, "light");
        } catch (e) {}
      } else {
        applyTheme(true);
        try {
          localStorage.setItem(themeKey, "dark");
        } catch (e) {}
      }
      syncThemeToggle();
    });
  }

  var toggle = document.querySelector(".nav-toggle");
  var panel = document.getElementById("nav-panel");
  if (!toggle || !panel) return;

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    panel.hidden = !open;
  }

  toggle.addEventListener("click", function () {
    var open = toggle.getAttribute("aria-expanded") === "true";
    setOpen(!open);
  });

  panel.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });

  window.addEventListener("resize", function () {
    if (window.matchMedia("(min-width: 768px)").matches) {
      setOpen(false);
    }
  });
})();

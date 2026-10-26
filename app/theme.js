(function () {
  var STORAGE_KEY = "mff-theme";

  function storedTheme() {
    try {
      return window.localStorage.getItem(STORAGE_KEY);
    } catch (error) {
      return null;
    }
  }

  function systemTheme() {
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    return "light";
  }

  function applyTheme(theme) {
    var next = theme === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    document.documentElement.style.colorScheme = next;
    var toggle = document.getElementById("theme-toggle");
    if (!toggle) return;
    var dark = next === "dark";
    toggle.setAttribute("aria-pressed", dark ? "true" : "false");
    var label = toggle.querySelector(".theme-toggle-label");
    if (label) label.textContent = dark ? "Light mode" : "Dark mode";
  }

  applyTheme(storedTheme() || "light");

  function bindToggle() {
    var toggle = document.getElementById("theme-toggle");
    if (!toggle || toggle.dataset.bound === "true") return;
    toggle.dataset.bound = "true";
    applyTheme(storedTheme() || "light");
    toggle.addEventListener("click", function () {
      var dark = document.documentElement.getAttribute("data-theme") === "dark";
      var next = dark ? "light" : "dark";
      applyTheme(next);
      try {
        window.localStorage.setItem(STORAGE_KEY, next);
      } catch (error) {
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindToggle);
  } else {
    bindToggle();
  }
})();

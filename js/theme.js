/* =========================================================
   THEME TOGGLE LOGIC
   - Day / Night mode
   - Persistent using localStorage
   - Reusable across all pages
========================================================= */

(function () {
  const THEME_KEY = "negd-theme";
  const toggle = document.getElementById("themeToggle");
  const root = document.documentElement;

  // ---------- Apply Theme ----------
  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }

  // ---------- Load Saved Theme ----------
  const savedTheme = localStorage.getItem(THEME_KEY);

  if (savedTheme) {
    applyTheme(savedTheme);
    if (toggle) toggle.checked = savedTheme === "dark";
  } else {
    // Default: Day mode
    applyTheme("light");
  }

  // ---------- Toggle Listener ----------
  if (toggle) {
    toggle.addEventListener("change", function () {
      const newTheme = this.checked ? "dark" : "light";
      applyTheme(newTheme);
    });
  }
})();
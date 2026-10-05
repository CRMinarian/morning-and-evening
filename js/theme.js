(function () {
  var storageKey = "me-theme";

  function storedTheme() {
    try {
      var theme = localStorage.getItem(storageKey);
      if (theme === "morning" || theme === "evening") {
        return theme;
      }
    } catch (error) {
      /* localStorage can be blocked; OS preference still works */
    }
    return "";
  }

  function preferredTheme() {
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "evening"
      : "morning";
  }

  function currentTheme() {
    var theme = document.documentElement.dataset.theme;
    if (theme === "morning" || theme === "evening") {
      return theme;
    }
    return preferredTheme();
  }

  function applyTheme(theme) {
    if (theme !== "morning" && theme !== "evening") {
      return;
    }
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(storageKey, theme);
    } catch (error) {
      /* persist is optional */
    }
    syncButtons();
  }

  function syncButtons() {
    var theme = currentTheme();
    document.querySelectorAll("[data-theme-set]").forEach(function (button) {
      button.setAttribute(
        "aria-pressed",
        button.getAttribute("data-theme-set") === theme ? "true" : "false"
      );
    });
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-theme-set]");
    if (!button) {
      return;
    }
    applyTheme(button.getAttribute("data-theme-set"));
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", syncButtons);
  } else {
    syncButtons();
  }
})();

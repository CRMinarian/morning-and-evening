(function () {
  var STORAGE_KEY = "me-intro-seen";
  var dialog = document.getElementById("intro-reveal");
  var video = document.getElementById("intro-reveal-video");
  var skip = document.getElementById("intro-reveal-skip");
  var main = document.getElementById("site-main");
  var leaving = false;

  function reducedMotion() {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function hasSeen() {
    try {
      return localStorage.getItem(STORAGE_KEY) === "1";
    } catch (error) {
      return false;
    }
  }

  function markSeen() {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch (error) {
      /* localStorage can be blocked */
    }
  }

  function restoreFocus() {
    if (main) {
      main.focus();
    }
  }

  function clearPending() {
    document.documentElement.removeAttribute("data-intro");
  }

  function finishClose() {
    clearPending();
    if (dialog && dialog.open) {
      dialog.close();
    }
    restoreFocus();
  }

  function dismiss() {
    if (leaving) {
      return;
    }
    leaving = true;
    markSeen();
    if (video) {
      video.pause();
    }
    if (!dialog || !dialog.open) {
      clearPending();
      restoreFocus();
      return;
    }
    dialog.classList.add("is-leaving");
    var done = false;
    function ended() {
      if (done) {
        return;
      }
      done = true;
      finishClose();
    }
    dialog.addEventListener("transitionend", ended);
    window.setTimeout(ended, 800);
  }

  function start() {
    if (!dialog || !skip) {
      clearPending();
      return;
    }

    if (hasSeen() || reducedMotion()) {
      clearPending();
      return;
    }

    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    } else {
      dialog.setAttribute("open", "open");
    }

    skip.focus();

    if (video) {
      var playAttempt = video.play();
      if (playAttempt && typeof playAttempt.catch === "function") {
        playAttempt.catch(function () {
          /* poster still remains; Skip stays available */
        });
      }
      video.addEventListener("ended", dismiss);
    }

    skip.addEventListener("click", dismiss);

    dialog.addEventListener("cancel", function (event) {
      event.preventDefault();
      dismiss();
    });

    dialog.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === "Escape") {
        event.preventDefault();
        dismiss();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

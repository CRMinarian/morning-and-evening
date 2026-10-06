(function () {
  var query = window.matchMedia("(prefers-reduced-motion: reduce)");

  function apply(reduce) {
    document.documentElement.setAttribute(
      "data-motion",
      reduce ? "reduce" : "ok"
    );
    document.querySelectorAll("[data-motion-video]").forEach(function (video) {
      if (reduce) {
        video.pause();
        video.removeAttribute("autoplay");
        try {
          video.currentTime = 0;
        } catch (error) {
          /* seeking can fail before metadata loads */
        }
        return;
      }
      video.setAttribute("autoplay", "autoplay");
      var playAttempt = video.play();
      if (playAttempt && typeof playAttempt.catch === "function") {
        playAttempt.catch(function () {
          /* poster still remains */
        });
      }
    });
  }

  function onChange(event) {
    apply(event.matches);
  }

  apply(query.matches);

  if (typeof query.addEventListener === "function") {
    query.addEventListener("change", onChange);
  } else if (typeof query.addListener === "function") {
    query.addListener(onChange);
  }
})();

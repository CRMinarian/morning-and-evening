(function () {
  var SLOTS = [
    { day: "2026-10-05", time: "morning" },
    { day: "2026-10-05", time: "evening" },
    { day: "2026-10-06", time: "morning" },
    { day: "2026-10-06", time: "evening" },
    { day: "2026-10-07", time: "morning" },
    { day: "2026-10-07", time: "evening" },
    { day: "2026-10-08", time: "morning" },
    { day: "2026-10-08", time: "evening" },
    { day: "2026-10-09", time: "morning" },
    { day: "2026-10-09", time: "evening" },
    { day: "2026-10-10", time: "morning" },
    { day: "2026-10-10", time: "evening" },
    { day: "2026-10-11", time: "morning" },
    { day: "2026-10-11", time: "evening" }
  ];

  function slotId(slot) {
    return slot.day + "-" + slot.time;
  }

  function findIndex(day, time) {
    for (var i = 0; i < SLOTS.length; i += 1) {
      if (SLOTS[i].day === day && SLOTS[i].time === time) {
        return i;
      }
    }
    return 0;
  }

  function queryValues() {
    var params = new URLSearchParams(window.location.search);
    var day = params.get("day") || "";
    var time = params.get("time") || "";
    return SLOTS[findIndex(day, time)];
  }

  function hashId() {
    var raw = window.location.hash || "";
    if (raw.charAt(0) === "#") {
      raw = raw.slice(1);
    }
    try {
      raw = decodeURIComponent(raw);
    } catch (e) {
      return "";
    }
    return raw;
  }

  function slotFromHash() {
    var id = hashId();
    if (!id) {
      return null;
    }
    for (var i = 0; i < SLOTS.length; i += 1) {
      if (slotId(SLOTS[i]) === id) {
        return SLOTS[i];
      }
    }
    return null;
  }

  function resolveSlot() {
    return slotFromHash() || queryValues();
  }

  function hrefFor(slot) {
    return "reading.html?day=" + slot.day + "&time=" + slot.time;
  }

  function timeLabel(time) {
    return time === "morning" ? "Morning" : "Evening";
  }

  function show(slot) {
    var articles = document.querySelectorAll("[data-reading]");
    articles.forEach(function (article) {
      if (article.id === slotId(slot)) {
        article.removeAttribute("hidden");
      } else {
        article.setAttribute("hidden", "hidden");
      }
    });

    var current = document.getElementById(slotId(slot));
    var heading = current ? current.querySelector("h3") : null;
    var titleBit = heading ? heading.textContent : timeLabel(slot.time);
    document.title =
      "Morning and Evening | Reading · " + slot.day + " " + timeLabel(slot.time);

    var index = findIndex(slot.day, slot.time);
    var pager = document.getElementById("reading-pager");
    if (!pager) {
      return;
    }
    pager.textContent = "";

    if (index > 0) {
      var prev = document.createElement("a");
      prev.setAttribute("href", hrefFor(SLOTS[index - 1]));
      prev.textContent = "Previous";
      pager.appendChild(prev);
      pager.appendChild(document.createTextNode(" "));
    }

    var back = document.createElement("a");
    back.setAttribute("href", "week.html");
    back.textContent = "Back to This Week";
    pager.appendChild(back);

    if (index < SLOTS.length - 1) {
      pager.appendChild(document.createTextNode(" "));
      var next = document.createElement("a");
      next.setAttribute("href", hrefFor(SLOTS[index + 1]));
      next.textContent = "Next";
      pager.appendChild(next);
    }

    if (titleBit && current) {
      current.setAttribute("aria-labelledby", current.id + "-title");
      if (heading && !heading.id) {
        heading.id = current.id + "-title";
      }
    }
  }

  function applyLocation(options) {
    var slot = resolveSlot();
    show(slot);
    if (options && options.scroll) {
      var current = document.getElementById(slotId(slot));
      if (current && typeof current.scrollIntoView === "function") {
        current.scrollIntoView();
      }
    }
  }

  function start() {
    applyLocation({ scroll: Boolean(slotFromHash()) });
  }

  window.addEventListener("hashchange", function () {
    if (!slotFromHash()) {
      return;
    }
    applyLocation({ scroll: true });
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();

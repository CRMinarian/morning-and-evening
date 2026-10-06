(function () {
  var WEEK_START = "2026-10-05";
  var WEEK_END = "2026-10-11";
  var DATA_URL = "data/this-week-full.json";

  function pad(value) {
    return value < 10 ? "0" + value : String(value);
  }

  function localIsoDate(now) {
    return (
      now.getFullYear() +
      "-" +
      pad(now.getMonth() + 1) +
      "-" +
      pad(now.getDate())
    );
  }

  function inWeek(iso) {
    return iso >= WEEK_START && iso <= WEEK_END;
  }

  function splitBody(body) {
    return body.split(/\n\n+/).map(function (part) {
      return part.replace(/\n/g, " ").trim();
    }).filter(function (part) {
      return part.length > 0;
    });
  }

  function fillCard(card, piece, date, time, timeLabel) {
    if (!card || !piece) {
      return;
    }
    var meta = card.querySelector(".meta");
    var heading = card.querySelector("h3");
    var body = card.querySelector(".reading-body");
    var open = card.querySelector(".reading-open a");
    if (meta) {
      meta.textContent = timeLabel + " · " + piece.scripture;
    }
    if (heading) {
      heading.textContent = piece.title;
    }
    if (body) {
      body.textContent = "";
      splitBody(piece.body).forEach(function (paragraph) {
        var p = document.createElement("p");
        p.textContent = paragraph;
        body.appendChild(p);
      });
    }
    if (open) {
      open.setAttribute("href", "reading.html?day=" + date + "&time=" + time);
    }
  }

  function applyDay(day, noteText) {
    var morning = document.querySelector('#today-pair [data-time="morning"]');
    var evening = document.querySelector('#today-pair [data-time="evening"]');
    fillCard(morning, day.morning, day.date, "morning", "Morning");
    fillCard(evening, day.evening, day.date, "evening", "Evening");
    var note = document.getElementById("today-note");
    if (note) {
      note.textContent = "";
      note.appendChild(document.createTextNode(noteText + " Open "));
      var week = document.createElement("a");
      week.setAttribute("href", "week.html");
      week.textContent = "This Week";
      note.appendChild(week);
      note.appendChild(document.createTextNode(" for the seven-day table."));
    }
  }

  function findDay(days, iso) {
    for (var i = 0; i < days.length; i += 1) {
      if (days[i].date === iso) {
        return days[i];
      }
    }
    return days[0];
  }

  function start(data) {
    var today = localIsoDate(new Date());
    var chosen = WEEK_START;
    var note = "Shown date " + WEEK_START + " (today is outside 2026-10-05 to 2026-10-11).";
    if (inWeek(today)) {
      chosen = today;
      note = "Shown date " + today + ".";
    }
    applyDay(findDay(data.days, chosen), note);
  }

  function load() {
    fetch(DATA_URL)
      .then(function (response) {
        if (!response.ok) {
          throw new Error("week data missing");
        }
        return response.json();
      })
      .then(start)
      .catch(function () {
        var note = document.getElementById("today-note");
        if (note) {
          note.textContent =
            "Shown date 2026-10-05. The live week file could not be read, so the Monday pair stays on the page.";
        }
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", load);
  } else {
    load();
  }
})();

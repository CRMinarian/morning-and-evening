# Morning and Evening

CIS 300 class site for Charles Spurgeon’s *Morning and Evening* readings.

## Pages
- `index.html`: Home (full featured pair and HTML5 video)
- `about.html`: About
- `week.html`: This Week (table and full bodies)
- `contact.html`: Contact (form and mailto)

## Data
- `data/today.json`, `data/this-week.json`, and `data/this-week-full.json`
  hold the public-domain text used to write the static Home and This Week
  pages (week of 2026-10-05 through 2026-10-11).

## Media
- `media/style-ref-grok-imagine.mp4` is the Home HTML5 video and the
  first-visit intro clip: an illustrative ink + watercolor style
  reference, not a shippable likeness and not a public-domain portrait.
- `images/imagine-watercolor.jpg` is a still frame from that clip. It
  replaces the old public-domain photograph on Home, About, and This Week.
- Home shows the intro overlay once per browser (`localStorage` key
  `me-intro-seen`). `js/intro.js` handles Skip, fade, and reduced motion.

## Author
Pierre Hulsebus (ASURITE `phulsebu`)

Course project for Arizona State University CIS 300.

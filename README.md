# Morning and Evening

CIS 300 class site for Charles Spurgeon’s *Morning and Evening* readings.

## Pages
- `index.html`: Home (featured pair and inline portrait video)
- `about.html`: About
- `week.html`: This Week (table of title tiles)
- `today.html`: Today (morning and evening pair for the local date)
- `reading.html`: Reading (one full body opened from a This Week tile)
- `contact.html`: Contact (form). Email is in the shared footer.

## Data
- `data/today.json`, `data/this-week.json`, and `data/this-week-full.json`
  hold the public-domain text used to write the static Home and This Week
  pages (week of 2026-10-05 through 2026-10-11).

## Media
- `media/portrait-loop.mp4` is the muted looping clip used in the Home,
  About, and This Week portrait spots (poster
  `images/imagine-watercolor.jpg`). `js/portrait.js` pauses it when
  `prefers-reduced-motion` is set.
- `media/style-ref-grok-imagine.mp4` is the original Imagine source used
  to cut that loop. It is not referenced by any page.

## Author
Pierre Hulsebus (ASURITE `phulsebu`)

Course project for Arizona State University CIS 300.

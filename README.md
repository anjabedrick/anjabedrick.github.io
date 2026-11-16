# anjabedrick.github.io

Portfolio site for Anja Bedrick, rebuilt from Framer in [Astro](https://astro.build).

## Run it on your computer

This folder has its own copy of Node in `.tools/` (it isn't uploaded to GitHub). In Terminal:

```bash
cd ~/Documents/anjabedrick-site
export PATH="$PWD/.tools/node/bin:$PATH"
npm install      # first time only
npm run dev      # then open http://localhost:4321
```

## Where things are

| What | Where |
| --- | --- |
| A project page | `src/content/projects/<name>.md` (the file name is the address, e.g. `momo.md` → `/momo`) |
| Home page (hero, "Hej, I'm Anja", experience, grid) | `src/pages/index.astro` |
| About page | `src/pages/about-anja.astro` |
| Colors, fonts, layout | `src/styles/global.css` (colors are at the top) |
| LinkedIn / CV links | `src/site.ts` |
| Images, videos | `public/media/` (use them as `/media/file.png`) |
| CV | `public/anja-bedrick-cv.pdf` |

### Adding a project

Copy an existing file in `src/content/projects/`, rename it, and edit the top section:

- `cover` – image on the home page (3D stack and grid), `cursorLabel` – text the cursor pill shows on hover
- `order` – position in the grid, `featured` – position in the 3D stack (delete the line to leave it out)
- `hero` – big image at the top of the project page

Below the `---` line the page is built from a few HTML blocks (copy them from another project):

- `<section class="glance">` – the outlined "At a Glance" box
- `<section class="sec">` – a section; start it with `<p class="pill pill-label">Label</p>` and `<h2>Title</h2>`
- `<div class="sec-split">` – image on the left (sticky), heading + STAR cards on the right
- `<div class="star-card" data-k="situation">` – a STAR card (`situation`, `problem`, `action`, `result` pick the icon)
- `<div class="step">` – numbered step: `step-text` beside `step-media`; add `step-flip` to swap sides
- `<div class="gallery gallery-2">` (or `-3`) – a row of images/videos

Any element with `data-cursor="Some text"` makes the cursor show that text on hover.

## Publishing

Every push to `main` on GitHub builds and publishes the site to https://anjabedrick.com
(see `.github/workflows/deploy.yml`).

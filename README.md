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

- `cover` – image on the home page grid, `cardLabel` – text on that card
- `order` – position in the grid, `featured` – position in the featured row (delete the line to leave it out)
- `hero` – big image at the top of the project page

Below the `---` line, write normally: `## Big heading`, `### Step heading`, paragraphs.
Images: `<div class="media"><img src="/media/file.png" alt="" /></div>`; put several
`<img>` or `<video>` tags in `<div class="media-grid cols-2">` (or `cols-3`) for a row.

## Publishing

Every push to `main` on GitHub builds and publishes the site to https://anjabedrick.github.io
(see `.github/workflows/deploy.yml`).

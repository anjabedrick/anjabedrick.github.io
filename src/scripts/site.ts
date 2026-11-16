// Interactions used across the whole site:
// smooth scrolling, the custom cursor, autoplaying videos,
// the 3D featured stack on the home page and drag-to-scroll strips.
import Lenis from 'lenis';

const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------------- smooth scroll ---------------- */
let scrollY = window.scrollY;
const lenis = reducedMotion ? null : new Lenis({ lerp: 0.09, smoothWheel: true, anchors: { offset: -80 } });
const frameCallbacks: ((t: number) => void)[] = [];
function raf(t: number) {
  lenis?.raf(t);
  scrollY = lenis ? lenis.scroll : window.scrollY;
  for (const cb of frameCallbacks) cb(t);
  requestAnimationFrame(raf);
}
requestAnimationFrame(raf);

/* ---------------- custom cursor ---------------- */
// Any element with data-cursor="Some text" turns the dot into a pill with that text.
// Any element inside [data-cursor-theme="light"] turns the dot white (for dark sections).
if (finePointer) {
  const cursor = document.querySelector<HTMLElement>('.cursor')!;
  const pill = cursor.querySelector<HTMLElement>('.cursor-pill')!;
  const label = cursor.querySelector<HTMLElement>('.cursor-text')!;
  // measure each label once so the dot can stretch to exactly the pill's width
  const measurer = document.createElement('span');
  measurer.className = 'cursor-measure';
  document.body.appendChild(measurer);
  const widths = new Map<string, number>();
  const widthOf = (text: string) => {
    if (!widths.has(text)) { measurer.textContent = text; widths.set(text, Math.ceil(measurer.getBoundingClientRect().width)); }
    return widths.get(text)!;
  };
  document.documentElement.classList.add('has-cursor');
  let x = -100, y = -100, cx = -100, cy = -100;
  window.addEventListener('pointermove', (e) => {
    x = e.clientX; y = e.clientY;
    cursor.classList.add('is-visible');
    update(e.target as Element);
  }, { passive: true });
  document.addEventListener('pointerleave', () => cursor.classList.remove('is-visible'));
  // the page moves under a still mouse while scrolling, so re-check what is under it
  window.addEventListener('scroll', () => update(document.elementFromPoint(x, y)), { passive: true });

  function update(target: Element | null) {
    const withLabel = target?.closest<HTMLElement>('[data-cursor]');
    if (withLabel) {
      const text = withLabel.dataset.cursor!;
      if (label.textContent !== text) {
        label.textContent = text;
        pill.style.setProperty('--w', `${widthOf(text) + 40 + 4 + 20 + 2}px`); // text + padding + gap + arrow + border
      }
      cursor.classList.add('is-label');
    } else {
      cursor.classList.remove('is-label');
    }
    cursor.classList.toggle('is-light', !!target?.closest('[data-cursor-theme="light"]'));
    cursor.classList.toggle('is-link', !withLabel && !!target?.closest('a, button'));
  }

  let frame = 0;
  frameCallbacks.push(() => {
    // things can move under a still mouse (the 3D stack keeps easing), so re-check now and then
    if (++frame % 8 === 0 && cursor.classList.contains('is-visible')) update(document.elementFromPoint(x, y));
    cx += (x - cx) * 0.22;
    cy += (y - cy) * 0.22;
    cursor.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
  });
}

/* ---------------- videos: play only while visible ---------------- */
const io = new IntersectionObserver((entries) => {
  for (const e of entries) {
    const v = e.target as HTMLVideoElement;
    if (e.isIntersecting) v.play().catch(() => {}); else v.pause();
  }
}, { threshold: 0.1 });
document.querySelectorAll<HTMLVideoElement>('video[data-autoplay]').forEach((v) => io.observe(v));

/* ---------------- 3D featured stack (home page) ---------------- */
// Ten cards sit 400px apart in depth inside a rotated 3D group. Scrolling slides
// every card toward the viewer; a card that passes the front wraps round to the back.
const stack = document.querySelector<HTMLElement>('.stack');
if (stack) {
  const cards = [...stack.querySelectorAll<HTMLElement>('.stack-card')];
  const STEP = 400, SPAN = STEP * cards.length, HALF = SPAN / 2;
  const wrap = (z: number) => ((((z + HALF) % SPAN) + SPAN) % SPAN) - HALF;
  let offset = 0;
  let manual = 0; // extra movement from the arrows, sideways swipes and arrow keys
  const go = (dir: number) => { manual = Math.round((manual + dir * STEP) / STEP) * STEP; };
  stack.parentElement!.querySelectorAll<HTMLElement>('[data-stack-dir]').forEach((b) =>
    b.addEventListener('click', () => go(Number(b.dataset.stackDir))));
  // sideways trackpad scroll moves through the stack (vertical scroll still scrolls the page)
  stack.addEventListener('wheel', (e) => {
    if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) { e.preventDefault(); manual += e.deltaX * 1.2; }
  }, { passive: false });
  // touch / pen: drag sideways
  let dragX: number | null = null, dragStart = 0;
  stack.addEventListener('pointerdown', (e) => { if (e.pointerType !== 'mouse') { dragX = e.clientX; dragStart = manual; } });
  window.addEventListener('pointermove', (e) => { if (dragX !== null) manual = dragStart - (e.clientX - dragX) * 2.5; });
  window.addEventListener('pointerup', () => { if (dragX !== null) { dragX = null; go(0); } });
  stack.parentElement!.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight') { e.preventDefault(); go(1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); go(-1); }
  });
  // hovering a card: it grows a touch and the cards around it slide away along the stack,
  // with a small springy overshoot (same feel as the grid tiles)
  let hovered = -1;
  const push = cards.map(() => ({ p: 0, v: 0, s: 1, sv: 0 }));
  cards.forEach((card, i) => {
    card.addEventListener('pointerenter', () => { hovered = i; });
    card.addEventListener('pointerleave', () => { if (hovered === i) hovered = -1; });
  });
  const render = () => {
    offset += (scrollY + manual - offset) * 0.12; // a little extra easing on top of the smooth scroll
    const hz = hovered >= 0 ? wrap(HALF - STEP * hovered + offset) : 0;
    cards.forEach((card, i) => {
      const base = wrap(HALF - STEP * i + offset);
      const k = push[i];
      const target = hovered < 0 || i === hovered ? 0 : (base > hz ? 140 : -140);
      k.v = (k.v + (target - k.p) * 0.12) * 0.78; k.p += k.v;
      k.sv = (k.sv + ((i === hovered ? 1.06 : 1) - k.s) * 0.12) * 0.78; k.s += k.sv;
      const z = base + k.p;
      const d = Math.abs(z);
      const scale = (1 + z / 5000) * k.s;
      let opacity = 1 - d / 3600;
      if (d > HALF - 300) opacity *= Math.max(0, (HALF - d) / 300); // fade out at the wrap point
      card.style.transform = `translate(-50%, -50%) translateZ(${z.toFixed(1)}px) scale(${scale.toFixed(4)}) translateY(var(--lift))`;
      card.style.opacity = opacity.toFixed(3);
      card.style.setProperty('--blur', `${(d / 112.5).toFixed(2)}px`);
      card.style.zIndex = String(Math.round(z + HALF));
      card.style.pointerEvents = opacity < 0.2 ? 'none' : '';
    });
  };
  render();
  frameCallbacks.push(render);
}

/* ---------------- grid tiles: the hovered tile grows and nudges its neighbours aside ---------------- */
const grid = document.querySelector<HTMLElement>('.grid');
if (grid && finePointer) {
  const GROW = 0.07;
  const tiles = [...grid.querySelectorAll<HTMLElement>('.card')];
  const reset = () => tiles.forEach((t) => { t.style.transform = ''; });
  tiles.forEach((tile) => {
    tile.addEventListener('pointerenter', () => {
      const a = tile.getBoundingClientRect();
      const dx = (a.width * GROW) / 2, dy = (a.height * GROW) / 2;
      tile.style.transform = `scale(${1 + GROW})`;
      for (const o of tiles) {
        if (o === tile) continue;
        const b = o.getBoundingClientRect();
        const sameCol = Math.abs(b.left - a.left) < 10;
        const overlapsY = b.bottom > a.top && b.top < a.bottom;
        let x = 0, y = 0;
        if (sameCol) y = b.top < a.top ? -dy : dy;
        else if (overlapsY) x = b.left < a.left ? -dx : dx;
        o.style.transform = x || y ? `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)` : '';
      }
    });
  });
  grid.addEventListener('pointerleave', reset);
}

/* ---------------- filter chips above the grid ---------------- */
const chips = [...document.querySelectorAll<HTMLButtonElement>('.filters .chip')];
if (grid && chips.length) {
  const cols = [...grid.querySelectorAll<HTMLElement>('.grid-col')];
  const all = [...grid.querySelectorAll<HTMLElement>('.card')];
  // the reading order (left to right, row by row) is the order the cards were dealt into the columns
  const reading: HTMLElement[] = [];
  const perCol = cols.map((c) => [...c.querySelectorAll<HTMLElement>('.card')]);
  for (let r = 0; perCol.some((c) => c[r]); r++) perCol.forEach((c) => c[r] && reading.push(c[r]));

  const apply = (filter: string) => {
    all.forEach((t) => { t.style.transform = ''; });
    const first = new Map(all.map((t) => [t, t.getBoundingClientRect()]));
    const wasHidden = new Set(all.filter((t) => t.classList.contains('is-hidden')));
    const show = reading.filter((t) => filter === '' ? true : (t.dataset.cats || '').split('|').includes(filter));
    reading.forEach((t) => t.classList.toggle('is-hidden', !show.includes(t)));
    show.forEach((t, i) => cols[i % cols.length].appendChild(t)); // deal the matches back into the columns
    // FLIP: slide cards from where they were to where they are now, with the springy transition
    for (const t of show) {
      if (wasHidden.has(t)) { t.animate([{ opacity: 0, transform: 'scale(.9)' }, { opacity: 1, transform: 'none' }], { duration: 500, easing: 'cubic-bezier(.34,1.56,.64,1)' }); continue; }
      const a = first.get(t)!, b = t.getBoundingClientRect();
      const dx = a.left - b.left, dy = a.top - b.top;
      if (!dx && !dy) continue;
      t.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'none' }], { duration: 700, easing: 'cubic-bezier(.34,1.56,.64,1)' });
    }
  };
  chips.forEach((chip) => chip.addEventListener('click', () => {
    chips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
    apply(chip.dataset.filter || '');
  }));
}

/* ---------------- stretchy page edges: overscrolling shows a strip of orange, then springs back ---------------- */
const page = document.querySelector<HTMLElement>('.page');
if (page && lenis && !reducedMotion) {
  const MAX = 90;
  const topNav = document.querySelector<HTMLElement>('.nav');
  let stretch = 0, velocity = 0, lastWheel = 0, gestureStart = 0;
  window.addEventListener('wheel', (e) => {
    const now = performance.now();
    if (now - lastWheel > 160) gestureStart = now; // a pause between events means a new swipe
    lastWheel = now;
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const atTop = window.scrollY <= 0 && e.deltaY < 0;
    const atBottom = window.scrollY >= max - 1 && e.deltaY > 0;
    if (!atTop && !atBottom) return;
    // only the first moment of a swipe pulls the edge; trackpad "coasting" afterwards is ignored,
    // so the orange strip never gets held open
    if (now - gestureStart > 220) return;
    const resistance = 1 - Math.min(Math.abs(stretch) / MAX, 0.95);
    stretch = Math.max(-MAX, Math.min(MAX, stretch - e.deltaY * 0.3 * resistance));
  }, { passive: true });
  frameCallbacks.push(() => {
    // the spring always pulls back, even while events arrive
    velocity = (velocity - stretch * 0.16) * 0.7;
    stretch += velocity;
    if (Math.abs(stretch) < 0.3 && Math.abs(velocity) < 0.3) { stretch = 0; velocity = 0; }
    page.style.transform = stretch ? `translate3d(0, ${stretch.toFixed(1)}px, 0)` : '';
    // at the top the navbar rides down with the page, so the orange shows above it, not behind it
    if (topNav) topNav.style.transform = stretch > 0 ? `translate3d(0, ${stretch.toFixed(1)}px, 0)` : '';
    document.documentElement.classList.toggle('peek-bottom', stretch < 0);
  });
}

/* ---------------- navbar: switch to a more opaque glass over dark sections (keeps text readable) ---------------- */
const nav = document.querySelector<HTMLElement>('.nav');
const darkBands = [...document.querySelectorAll<HTMLElement>('[data-cursor-theme="light"]')];
if (nav && darkBands.length) {
  frameCallbacks.push(() => {
    const navBottom = nav.offsetHeight;
    const overDark = darkBands.some((d) => { const r = d.getBoundingClientRect(); return r.top < navBottom && r.bottom > 0; });
    nav.classList.toggle('nav-on-dark', overDark);
  });
}

/* ---------------- about page timeline: slides sideways as you scroll down ---------------- */
document.querySelectorAll<HTMLElement>('[data-scroll-x]').forEach((box) => {
  const track = box.firstElementChild as HTMLElement;
  let x = 0;
  frameCallbacks.push(() => {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const travel = Math.max(0, track.scrollWidth - box.clientWidth);
    if (maxScroll < 40) { box.classList.add('is-manual'); return; } // page too short to scroll: let people swipe it
    const progress = Math.min(1, Math.max(0, scrollY / maxScroll));
    x += (progress * travel - x) * 0.15;
    track.style.transform = `translate3d(${-x.toFixed(1)}px, 0, 0)`;
  });
});

/* ---------------- drag to scroll ---------------- */
document.querySelectorAll<HTMLElement>('[data-drag-scroll]').forEach((el) => {
  let down = false, startX = 0, startLeft = 0;
  el.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'mouse') return;
    down = true; startX = e.clientX; startLeft = el.scrollLeft;
    el.setPointerCapture(e.pointerId); el.classList.add('is-dragging');
  });
  el.addEventListener('pointermove', (e) => { if (down) el.scrollLeft = startLeft - (e.clientX - startX); });
  const end = () => { down = false; el.classList.remove('is-dragging'); };
  el.addEventListener('pointerup', end);
  el.addEventListener('pointercancel', end);
});

/* ---------------- letters of the hero name blur in one by one ---------------- */
let letterIndex = 0;
document.querySelectorAll<HTMLElement>('[data-split] .line').forEach((line) => {
  const text = line.textContent ?? '';
  line.textContent = '';
  for (const ch of text) {
    const s = document.createElement('span');
    s.className = 'ch';
    s.style.setProperty('--i', String(letterIndex++));
    s.textContent = ch;
    s.setAttribute('aria-hidden', 'true');
    line.appendChild(s);
  }
});
document.querySelectorAll('[data-split]').forEach((el) => el.classList.add('is-split'));

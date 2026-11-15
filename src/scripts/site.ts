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
  const render = () => {
    offset += (scrollY - offset) * 0.12; // a little extra easing on top of the smooth scroll
    cards.forEach((card, i) => {
      const z = wrap(HALF - STEP * i + offset);
      const d = Math.abs(z);
      const scale = 1 + z / 5000;
      let opacity = 1 - d / 3600;
      if (d > HALF - 300) opacity *= Math.max(0, (HALF - d) / 300); // fade out at the wrap point
      card.style.transform = `translate(-50%, -50%) translateZ(${z.toFixed(1)}px) scale(${scale.toFixed(4)})`;
      card.style.opacity = opacity.toFixed(3);
      card.style.setProperty('--blur', `${(d / 112.5).toFixed(2)}px`);
      card.style.zIndex = String(Math.round(z + HALF));
      card.style.pointerEvents = opacity < 0.2 ? 'none' : '';
    });
  };
  render();
  if (!reducedMotion) frameCallbacks.push(render);
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

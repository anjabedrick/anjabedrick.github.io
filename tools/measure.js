// Paste into the browser console on http://127.0.0.1:9918/ (served by framer_proxy.py),
// then run:  await measureAll(['momo', 'snm-brand-identity', ...])
// Each Framer page is loaded in a 1440px-wide iframe, every heading/paragraph/image/video is
// recorded with its position, and the result is saved to tools/framer-data/<slug>.json.
window.measureAll = async (slugs) => {
  const report = [];
  for (const slug of slugs) {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:0;top:0;width:1440px;height:900px;opacity:0;pointer-events:none';
    f.src = '/' + slug;
    document.body.appendChild(f);
    await new Promise((r) => (f.onload = r));
    await new Promise((r) => setTimeout(r, 2500));
    const d = f.contentDocument, w = f.contentWindow;
    const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const rich = (el) => {
      let o = '';
      for (const n of el.childNodes) {
        if (n.nodeType === 3) o += esc(n.textContent);
        else if (n.nodeType === 1) {
          const t = n.tagName.toLowerCase(), inner = rich(n), href = n.getAttribute('href');
          if (t === 'strong' || t === 'b') o += inner.trim() ? `<strong>${inner}</strong>` : inner;
          else if (t === 'em' || t === 'i') o += inner.trim() ? `<em>${inner}</em>` : inner;
          else if (t === 'br') o += '<br>';
          else if (t === 'a' && href && !href.startsWith('./')) o += `<a href="${href}">${inner}</a>`;
          else o += inner;
        }
      }
      return o;
    };
    const hiddenUp = (e) => { for (let p = e; p && p !== d.body; p = p.parentElement) if (w.getComputedStyle(p).display === 'none') return true; return false; };
    const out = [];
    for (const e of d.querySelectorAll('#main h1,#main h2,#main h3,#main h4,#main h5,#main h6,#main p,#main img,#main video')) {
      if (e.closest('nav,header,footer') || hiddenUp(e)) continue;
      const t = e.tagName.toLowerCase();
      if ((t === 'p' || t[0] === 'h') && e.parentElement.closest('p,h1,h2,h3,h4,h5,h6')) continue;
      const r = e.getBoundingClientRect();
      const it = { t, top: Math.round(r.top + w.scrollY), left: Math.round(r.left), w: Math.round(r.width), h: Math.round(r.height) };
      if (t === 'img') { it.src = (e.getAttribute('src') || '').split('?')[0]; it.alt = e.alt || ''; }
      else if (t === 'video') { it.src = (e.getAttribute('src') || e.querySelector('source')?.getAttribute('src') || '').split('?')[0]; }
      else {
        it.text = rich(e).replace(/\s+/g, ' ').trim();
        if (!it.text) continue;
        it.li = !!e.closest('li');
        const a = e.closest('a'); if (a) it.href = a.getAttribute('href');
      }
      out.push(it);
    }
    await fetch('/' + slug.replace('.', ''), { method: 'POST', body: JSON.stringify(out) });
    report.push(slug + ':' + out.length);
    f.remove();
  }
  return report.join(', ');
};

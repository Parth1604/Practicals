/* AIgram — swipe feed shell. Content comes from feed/<date>.json. */
(() => {
  const $ = (s, el = document) => el.querySelector(s);
  const feedEl = $('#feed');
  const LOG_KEY = 'aigram.log';
  const SEEN_KEY = 'aigram.seen';

  // ---------- storage (localStorage may throw in private mode) ----------
  const store = {
    get(k, d) { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} },
  };
  const log = (entry) => {
    const l = store.get(LOG_KEY, []);
    l.push({ t: new Date().toISOString(), ...entry });
    store.set(LOG_KEY, l.slice(-2000));
  };

  // ---------- helpers ----------
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  // tiny markdown: `code`, *em*, **strong**
  const md = (s) => esc(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // single-pass tokenizer so spans never get re-matched
  const KW = /^(def|class|return|import|from|if|else|elif|not|for|in|with|as|lambda|None|True|False|async|await)$/;
  const highlight = (src) => src.replace(
    /("""[\s\S]*?"""|"[^"\n]*"|'[^'\n]*'|#[^\n]*|\b[A-Za-z_]\w*(?=\()|\b[A-Za-z_]\w*\b|[\s\S])/g,
    (tok, _g, offset) => {
      if (tok[0] === '#') return `<span class="cm">${esc(tok)}</span>`;
      if (tok[0] === '"' || tok[0] === "'") return `<span class="st">${esc(tok)}</span>`;
      if (KW.test(tok)) return `<span class="kw">${esc(tok)}</span>`;
      if (/^[A-Za-z_]\w*$/.test(tok) && src[offset + tok.length] === '(') return `<span class="fn">${esc(tok)}</span>`;
      return esc(tok);
    });

  // ---------- diagram renderer (boxes + arrows) ----------
  function diagramSVG(d) {
    const W = 340, boxW = 92, boxH = 36, gap = 28;
    const nodes = d.nodes, pos = {};
    let H;
    if (d.direction === 'col') {
      // first node on top, others in a row below, or a simple vertical stack if <=3
      if (nodes.length <= 3) {
        H = nodes.length * (boxH + gap);
        nodes.forEach((n, i) => pos[n.id] = { x: W / 2 - boxW / 2, y: 8 + i * (boxH + gap) });
      } else {
        const [hub, ...rest] = nodes;
        H = 2 * boxH + gap + 24;
        pos[hub.id] = { x: W / 2 - boxW / 2, y: 8 };
        const step = W / rest.length;
        rest.forEach((n, i) => pos[n.id] = { x: step * i + step / 2 - boxW / 2, y: 8 + boxH + gap });
      }
    } else {
      const n = nodes.length, bw = Math.min(boxW, (W - 16 - (n - 1) * 18) / n);
      H = boxH + 16;
      nodes.forEach((nd, i) => pos[nd.id] = { x: 8 + i * (bw + 18), y: 8, w: bw });
    }
    const center = (id) => { const p = pos[id]; return { x: p.x + (p.w || boxW) / 2, y: p.y + boxH / 2 }; };
    const seen = new Set();
    const edges = d.edges.map(([a, b]) => {
      const A = center(a), B = center(b), key = [a, b].sort().join('|');
      const bidir = seen.has(key); seen.add(key);
      const dx = B.x - A.x, dy = B.y - A.y, len = Math.hypot(dx, dy) || 1;
      const ux = dx / len, uy = dy / len;
      const pa = pos[a], pb = pos[b];
      const ra = Math.abs(dx) > Math.abs(dy) ? (pa.w || boxW) / 2 : boxH / 2;
      const rb = Math.abs(dx) > Math.abs(dy) ? (pb.w || boxW) / 2 : boxH / 2;
      const x1 = A.x + ux * ra, y1 = A.y + uy * ra, x2 = B.x - ux * (rb + 6), y2 = B.y - uy * (rb + 6);
      if (bidir) { // curve back edges
        const mx = (x1 + x2) / 2 - uy * 22, my = (y1 + y2) / 2 + ux * 22;
        return `<path d="M${x1},${y1} Q${mx},${my} ${x2},${y2}" class="e" marker-end="url(#ar)"/>`;
      }
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="e" marker-end="url(#ar)"/>`;
    }).join('');
    const boxes = nodes.map((n) => {
      const p = pos[n.id], w = p.w || boxW, term = n.kind === 'terminal';
      return `<g><rect x="${p.x}" y="${p.y}" width="${w}" height="${boxH}" rx="${term ? boxH / 2 : 10}" class="${term ? 'term' : 'box'}"/>
        <text x="${p.x + w / 2}" y="${p.y + boxH / 2 + 4}" text-anchor="middle">${esc(n.label)}</text></g>`;
    }).join('');
    return `<svg viewBox="0 0 ${W} ${H + 8}" xmlns="http://www.w3.org/2000/svg">
      <defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#8b93a7"/></marker></defs>
      <style>.box{fill:#1d2230;stroke:#7c9cff;stroke-width:1.2}.term{fill:#0b0d12;stroke:#5ad1a4;stroke-width:1.2}text{fill:#e9ecf1;font:12px -apple-system,system-ui,sans-serif}.e{stroke:#8b93a7;stroke-width:1.4;fill:none}</style>
      ${edges}${boxes}</svg>${d.caption ? `<div class="cap">${esc(d.caption)}</div>` : ''}`;
  }

  // ---------- card renderer ----------
  function renderCard(c, i, total) {
    const sec = document.createElement('section');
    sec.className = 'card'; sec.dataset.id = c.id; sec.dataset.i = i;
    const parts = [];
    parts.push(`<span class="badge ${c.bucket}">${esc(c.bucket)} · ${esc(c.type)} · ${esc(c.topic)}</span>`);
    parts.push(`<h2>${md(c.title)}</h2>`);
    if (c.body) parts.push(`<p class="body">${md(c.body)}</p>`);
    if (c.diagram) parts.push(`<div class="diagram">${diagramSVG(c.diagram)}</div>`);
    if (c.code) parts.push(`<pre>${highlight(c.code.src)}</pre>`);
    if (c.quiz) {
      parts.push(`<div class="quiz"><div class="q">${md(c.quiz.question)}</div>
        ${c.quiz.options.map((o, k) => `<button class="opt" data-k="${k}">${md(o)}</button>`).join('')}
        <div class="explain" hidden>${md(c.quiz.explain)}</div></div>`);
    }
    if (c.why) parts.push(`<div class="why">${md(c.why)}</div>`);
    parts.push(`<div class="actions">
      <button data-act="save">☆ Save</button>
      <button data-act="more">Explain more</button>
      <button data-act="known">Already know it</button></div>`);
    sec.innerHTML = `<div class="inner">${parts.join('')}</div>`;

    // quiz
    sec.querySelectorAll('.opt').forEach((b) => b.addEventListener('click', () => {
      const k = +b.dataset.k, ok = k === c.quiz.answer;
      sec.querySelectorAll('.opt').forEach((x) => { x.disabled = true; if (+x.dataset.k === c.quiz.answer) x.classList.add('right'); });
      if (!ok) b.classList.add('wrong');
      $('.explain', sec).hidden = false;
      log({ card: c.id, topic: c.topic, ev: 'quiz', correct: ok, picked: k });
      if (navigator.vibrate) navigator.vibrate(ok ? 10 : [20, 40, 20]);
    }));
    // actions
    sec.querySelectorAll('.actions button').forEach((b) => b.addEventListener('click', () => {
      b.classList.toggle('on');
      log({ card: c.id, topic: c.topic, ev: b.dataset.act, on: b.classList.contains('on') });
      $('#status').textContent = b.dataset.act === 'more' ? 'Noted — tomorrow goes deeper on this.' : 'Saved to your log.';
      setTimeout(() => $('#status').textContent = '', 1800);
    }));
    return sec;
  }

  function renderEnd(feed) {
    const sec = document.createElement('section');
    sec.className = 'card end';
    const l = store.get(LOG_KEY, []).filter((e) => e.t.slice(0, 10) === new Date().toISOString().slice(0, 10));
    const quiz = l.filter((e) => e.ev === 'quiz'), right = quiz.filter((e) => e.correct).length;
    sec.innerHTML = `<div class="inner"><span class="logo" style="width:28px;height:28px;border-radius:8px"></span>
      <h2>That's today.</h2>
      <p class="muted">${feed.cards.length} cards · quiz ${right}/${quiz.length}</p>
      <p class="muted" style="font-size:13px">Tomorrow's feed lands before you wake up.</p></div>`;
    return sec;
  }

  // ---------- load ----------
  async function loadFeed() {
    const idx = await (await fetch('feed/index.json', { cache: 'no-cache' })).json();
    const today = new Date().toISOString().slice(0, 10);
    const date = idx.dates.filter((d) => d <= today).sort().pop() || idx.latest;
    const feed = await (await fetch(`feed/${date}.json`, { cache: 'no-cache' })).json();
    return feed;
  }

  function mount(feed) {
    feedEl.innerHTML = '';
    const total = feed.cards.length;
    feed.cards.forEach((c, i) => feedEl.appendChild(renderCard(c, i, total)));
    feedEl.appendChild(renderEnd(feed));
    $('#date').textContent = feed.date;
    $('#progress').textContent = `1/${total}`;

    // progress + view log via IntersectionObserver
    const seen = new Set(store.get(SEEN_KEY, []));
    const io = new IntersectionObserver((ents) => ents.forEach((e) => {
      if (!e.isIntersecting) return;
      const i = +e.target.dataset.i, id = e.target.dataset.id;
      if (!isNaN(i)) $('#progress').textContent = `${i + 1}/${total}`;
      if (id && !seen.has(id)) { seen.add(id); store.set(SEEN_KEY, [...seen].slice(-5000)); log({ card: id, ev: 'view' }); }
    }), { root: feedEl, threshold: 0.6 });
    feedEl.querySelectorAll('.card').forEach((el) => io.observe(el));
  }

  // ---------- export ----------
  $('#btn-export').addEventListener('click', async () => {
    const data = JSON.stringify(store.get(LOG_KEY, []), null, 0);
    try { await navigator.clipboard.writeText(data); $('#status').textContent = 'Log copied — paste it to Claude.'; }
    catch { prompt('Copy your log:', data); }
    setTimeout(() => $('#status').textContent = '', 2500);
  });

  // ---------- iOS install hint ----------
  const standalone = window.navigator.standalone === true || matchMedia('(display-mode: standalone)').matches;
  const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  if (isIOS && !standalone && !store.get('aigram.hintDismissed', false)) {
    $('#install-hint').hidden = false;
    $('#hint-close').onclick = () => { $('#install-hint').hidden = true; store.set('aigram.hintDismissed', true); };
  }

  // ---------- service worker ----------
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});

  loadFeed().then(mount).catch((err) => {
    feedEl.innerHTML = `<section class="card"><div class="inner"><h2>Couldn't load the feed.</h2><p class="muted">${esc(err.message)}</p></div></section>`;
  });
})();

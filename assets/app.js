/* Idea Atlas — client logic. No AI in browser, no keys, static fetch only. */

async function loadJSON(paths) {
  for (const p of paths) {
    try {
      const r = await fetch(p);
      if (r.ok) return await r.json();
    } catch (e) { /* try next path */ }
  }
  return null;
}

const loadIndex = () => loadJSON(["../data/index.json", "data/index.json"]) || [];
const loadMeta = () => loadJSON(["../data/meta.json", "data/meta.json"]);
const loadCategory = (slug) => loadJSON(["../data/c/" + slug + ".json", "data/c/" + slug + ".json"]) || [];
const loadCategories = () => loadJSON(["../data/categories.json", "data/seed/categories.json"]) || [];

function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function highlight(title, query) {
  const safe = escapeHtml(title);
  const q = (query || "").trim();
  if (!q) return safe;
  const terms = q.split(/\s+/).filter((w) => w.length > 2).map(escapeRe);
  if (!terms.length) return safe;
  return safe.replace(new RegExp("(" + terms.join("|") + ")", "gi"), "<mark>$1</mark>");
}

const STATUS_ORDER = ["known", "debated", "undiscovered"];
const STATUS_WORD = { known: "Known", debated: "Debated", undiscovered: "Frontier" };
const STATUS_BLURB = {
  known: "Known — don't rebuild",
  debated: "Debated — people are discussing",
  undiscovered: "Frontier — genuinely open",
};

function isStale(meta, maxHours) {
  if (!meta || !meta.updated_at) return true;
  const t = Date.parse(meta.updated_at);
  if (isNaN(t)) return true;
  return Date.now() - t > (maxHours || 48) * 3600 * 1000;
}

function staleBadge(meta) {
  if (!meta) return '<span class="badge stale">data missing</span>';
  return isStale(meta)
    ? '<span class="badge stale">stale — updated ' + escapeHtml(meta.updated_at) + "</span>"
    : '<span class="badge fresh">updated ' + escapeHtml(meta.updated_at) + "</span>";
}

/* Validator: known exact/substring wins, then debated, then frontier.
   Returns {kind, verdict, hits, query} so pages can stamp + render. */
function validator(q, index) {
  q = (q || "").trim().toLowerCase();
  const items = index || [];
  if (!q) return { kind: "none", verdict: "", hits: [], query: q };
  const words = q.split(/\s+/).filter((w) => w.length > 2);
  const matches = (x) =>
    x.title && (x.title.toLowerCase().includes(q) || words.some((w) => x.title.toLowerCase().includes(w)));
  for (const status of STATUS_ORDER) {
    const hits = items.filter((x) => x.status === status && matches(x));
    if (hits.length)
      return { kind: status, verdict: STATUS_BLURB[status], hits: hits.slice(0, 8), query: q };
  }
  return { kind: "none", verdict: "Uncharted — nothing in the atlas matches yet", hits: [], query: q };
}

function renderVerdict(el, res) {
  if (!el) return;
  if (!res.query) { el.innerHTML = ""; return; }
  el.innerHTML =
    '<span class="verdict-stamp ' + res.kind + '">' +
    (res.kind !== "none" ? '<span class="glyph ' + res.kind + '"></span>' : "") +
    escapeHtml(res.verdict) + "</span>";
}

function renderHits(el, res) {
  if (!el) return;
  if (!res.query) { el.innerHTML = ""; return; }
  if (!res.hits.length) {
    el.innerHTML =
      '<p class="empty">No charted entry for “' + escapeHtml(res.query) +
      '”. That is either a genuinely new idea or a phrase the atlas hasn’t mapped yet — browse the frontier sheets below.</p>';
    return;
  }
  el.innerHTML = '<ol class="ledger">' + res.hits.map(hitRow(res.query)).join("") + "</ol>";
}

function hitRow(query) {
  return function (h, i) {
    const url = escapeHtml(h.url || "#");
    return (
      '<li><a class="row" href="' + url + '" target="_blank" rel="noopener">' +
      '<span class="no">' + String(i + 1).padStart(2, "0") + "</span>" +
      '<span class="title">' + highlight(h.title, query) + "</span>" +
      '<span class="meta"><span class="status-word ' + h.status + '">' + STATUS_WORD[h.status] + "</span>" +
      "<span>" + escapeHtml(h.category || "") + "</span>" +
      "<span>" + escapeHtml(h.source || "") + "</span></span>" +
      (h.note ? '<span class="callout">' + escapeHtml(h.note) + "</span>" : "") +
      "</a></li>"
    );
  };
}

/* Ledger rows for category pages. */
function renderEntries(el, items, query) {
  if (!el) return;
  if (!items.length) {
    el.innerHTML = '<li><p class="empty">Nothing charted here under this filter.</p></li>';
    return;
  }
  el.innerHTML = items.map(hitRow(query)).join("");
}

/* ---------- theme ---------- */
function initTheme() {
  const saved = localStorage.getItem("atlas-theme");
  const prefersLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;
  setTheme(saved || (prefersLight ? "light" : "dark"), false);
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    setTheme(next, true);
  });
}
function setTheme(theme, persist) {
  document.documentElement.dataset.theme = theme;
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.textContent = theme === "light" ? "☾" : "☀";
  if (persist) localStorage.setItem("atlas-theme", theme);
}

/* Count one stat number up once per load (single orchestrated moment). */
function countUp(el, target) {
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    el.textContent = target; return;
  }
  const dur = 900, t0 = performance.now();
  (function tick(t) {
    const p = Math.min(1, (t - t0) / dur);
    el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
    if (p < 1) requestAnimationFrame(tick);
  })(t0);
}

// Exposed for inline page scripts and tests.
if (typeof window !== "undefined") {
  window.Atlas = {
    loadIndex, loadMeta, loadCategory, loadCategories,
    validator, escapeHtml, escapeRe, highlight,
    isStale, staleBadge, renderHits, renderVerdict, renderEntries,
    STATUS_ORDER, STATUS_WORD,
    initTheme, setTheme, countUp,
  };
}

/* Idea Atlas — client logic. No AI in browser, no keys, static fetch only. */

async function loadIndex() {
  const paths = ["../data/index.json", "data/index.json"];
  for (const p of paths) {
    try {
      const r = await fetch(p);
      if (r.ok) return await r.json();
    } catch (e) { /* try next path */ }
  }
  return [];
}

async function loadMeta() {
  const paths = ["../data/meta.json", "data/meta.json"];
  for (const p of paths) {
    try {
      const r = await fetch(p);
      if (r.ok) return await r.json();
    } catch (e) { /* try next path */ }
  }
  return null;
}

async function loadCategory(slug) {
  const paths = ["../data/c/" + slug + ".json", "data/c/" + slug + ".json"];
  for (const p of paths) {
    try {
      const r = await fetch(p);
      if (r.ok) return await r.json();
    } catch (e) { /* try next path */ }
  }
  return [];
}

function validator(q, index) {
  q = (q || "").toLowerCase();
  const known = (index || []).filter(
    (x) =>
      x.status === "known" &&
      x.title &&
      (x.title.toLowerCase().includes(q) ||
        q.includes(x.title.toLowerCase().split(" ")[0]))
  );
  if (q && known.length)
    return { verdict: "SOLVED — don't rebuild", hits: known.slice(0, 5) };
  const debated = (index || []).filter(
    (x) =>
      x.status === "debated" &&
      x.title &&
      q.split(/\s+/).some(
        (w) => w.length > 3 && x.title.toLowerCase().includes(w)
      )
  );
  if (q && debated.length)
    return { verdict: "DEBATED — people are discussing", hits: debated.slice(0, 8) };
  return { verdict: "OPEN / FRONTIER — potentially new, check Undiscovered", hits: [] };
}

function escapeHtml(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

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

function renderHits(el, hits) {
  if (!hits.length) {
    el.innerHTML = '<p class="muted">No direct hits. Browse Undiscovered below.</p>';
    return;
  }
  el.innerHTML =
    "<ul>" +
    hits
      .map(
        (h) =>
          '<li><a href="' + escapeHtml(h.url || "#") + '">' + escapeHtml(h.title) + "</a>" +
          ' <span class="tag">' + escapeHtml(h.status) + "</span>" +
          ' <span class="tag">' + escapeHtml(h.category) + "</span></li>"
      )
      .join("") +
    "</ul>";
}

// Exposed for inline page scripts and tests.
if (typeof window !== "undefined") {
  window.Atlas = { loadIndex, loadMeta, loadCategory, validator, escapeHtml, isStale, staleBadge, renderHits };
}

// Load items.json, build source filter, render articles
(async function () {
  const srcSel = document.getElementById('source-select');
  const updatedEl = document.getElementById('updated-label');
  const listEl = document.getElementById('articles');

  // fetch with cache-busting to avoid stale mobile cache
  const res = await fetch(`items.json?ts=${Date.now()}`);
  const data = await res.json();

  // updated label
  if (data.updated_at) {
    updatedEl.textContent = `Updated: ${formatDateLocal(data.updated_at)}`;
  }

  const items = Array.isArray(data.items) ? data.items : [];
  // unique sources
  const sources = ['All sources', ...Array.from(new Set(
    items.map(i => i.source || hostFromUrl(i.link)).filter(Boolean)
  ))].sort((a,b)=> a==='All sources'?-1 : a.localeCompare(b));

  // populate dropdown
  srcSel.innerHTML = sources.map(s => `<option value="${escapeAttr(s)}">${escapeHTML(s)}</option>`).join('');

  function render(filterSource = 'All sources') {
    const max = 50;
    const filtered = items
      .filter(i => filterSource === 'All sources' ? true : (i.source || hostFromUrl(i.link)) === filterSource)
      .slice(0, max);

    listEl.innerHTML = filtered.map(renderCard).join('') || `<div class="article"><div class="meta">No articles yet.</div></div>`;
  }

  srcSel.addEventListener('change', e => render(e.target.value));
  render();

  // helpers
  function renderCard(i) {
    const title = escapeHTML(i.title || 'Untitled');
    const link = i.link || '#';
    const src = escapeHTML(i.source || hostFromUrl(link) || '—');
    const dt = formatDateLocal(i.iso_date || i.published || i.updated);

    return `
      <article class="article">
        <h2><a href="${escapeAttr(link)}" target="_blank" rel="noopener">${title}</a></h2>
        <div class="meta">
          <span>${src}</span>
          <span>•</span>
          <time>${dt || ''}</time>
        </div>
      </article>
    `;
  }

  function formatDateLocal(isoLike) {
    const d = new Date(isoLike);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: 'numeric', minute: '2-digit'
    });
  }

  function hostFromUrl(u) {
    try { return new URL(u).host.replace(/^www\./,''); } catch { return ''; }
  }

  function escapeHTML(s='') {
    return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  function escapeAttr(s=''){ return escapeHTML(s); }
})();
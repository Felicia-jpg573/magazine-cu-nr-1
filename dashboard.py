"""
dashboard.py
Generează un raport HTML interactiv din rezultatele scanării.
Include coloane: operator economic, persoană juridică/CUI, link site,
link pagină detectată, afirmație, verdict, indicatori sursă, context.
"""

import json
from datetime import datetime
from pathlib import Path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Raport Conformitate Publicitate — Nr. 1</title>
<style>
  :root {
    --red: #c0392b; --orange: #e67e22; --green: #27ae60; --blue: #2980b9;
    --dark: #1a1a2e; --mid: #16213e; --light: #0f3460;
    --text: #e0e0e0; --subtext: #a0aab4; --border: #2a2a4a; --card: #1e1e3a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--dark); color: var(--text); font-size: 14px; line-height: 1.6; }
  header { background: var(--mid); border-bottom: 2px solid var(--light); padding: 24px 32px; }
  header h1 { font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 4px; }
  header p { color: var(--subtext); font-size: 13px; }
  .container { max-width: 1600px; margin: 0 auto; padding: 24px 32px; }
  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }
  .stat-card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 18px 20px; }
  .stat-card .label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--subtext); margin-bottom: 6px; }
  .stat-card .value { font-size: 28px; font-weight: 700; color: #fff; }
  .stat-card.red .value { color: var(--red); }
  .stat-card.orange .value { color: var(--orange); }
  .stat-card.blue .value { color: var(--blue); }
  .filters { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; align-items: center; }
  .filters input[type="text"] { background: var(--card); border: 1px solid var(--border); color: var(--text); border-radius: 6px; padding: 8px 14px; font-size: 13px; width: 300px; outline: none; }
  .filters input[type="text"]:focus { border-color: var(--blue); }
  .filter-btn { background: var(--card); border: 1px solid var(--border); color: var(--subtext); border-radius: 6px; padding: 8px 16px; font-size: 12px; cursor: pointer; }
  .filter-btn:hover, .filter-btn.active { background: var(--light); border-color: var(--blue); color: #fff; }
  .export-btn { background: var(--light); border: 1px solid var(--blue); color: #fff; border-radius: 6px; padding: 8px 18px; font-size: 12px; cursor: pointer; font-weight: 600; margin-left: auto; }
  .export-btn:hover { background: var(--blue); }
  .table-wrap { overflow-x: auto; border-radius: 8px; border: 1px solid var(--border); }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  thead th { background: var(--mid); color: var(--subtext); font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em; font-weight: 600; padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }
  tbody tr { border-bottom: 1px solid var(--border); transition: background 0.1s; }
  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: rgba(41,128,185,0.07); }
  tbody td { padding: 10px 14px; vertical-align: top; }
  .store-name { font-weight: 600; color: #fff; font-size: 13px; }
  .pj-name { font-size: 11px; color: var(--subtext); margin-top: 2px; }
  .cui-code { font-size: 10px; color: #666; font-family: monospace; }
  .pj-missing { font-size: 11px; color: #555; font-style: italic; }
  .link-cell a { color: var(--blue); text-decoration: none; font-size: 12px; display: inline-flex; align-items: center; gap: 4px; }
  .link-cell a:hover { text-decoration: underline; }
  .pattern-badge { display: inline-block; background: rgba(192,57,43,0.18); color: #e74c3c; border: 1px solid rgba(192,57,43,0.4); border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; font-family: monospace; }
  .verdict-badge { display: inline-block; border-radius: 4px; padding: 3px 10px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; white-space: nowrap; }
  .verdict-red { background: rgba(192,57,43,0.2); color: #e74c3c; border: 1px solid rgba(192,57,43,0.5); }
  .verdict-orange { background: rgba(230,126,34,0.2); color: #f39c12; border: 1px solid rgba(230,126,34,0.5); }
  .context-text { font-size: 11px; color: var(--subtext); max-width: 380px; line-height: 1.5; }
  .context-toggle { color: var(--blue); cursor: pointer; font-size: 11px; margin-top: 4px; display: inline-block; }
  .context-full { display: none; }
  .context-full.visible { display: block; }
  .sources-list { font-size: 11px; color: #2ecc71; }
  .no-source { font-size: 11px; color: #555; font-style: italic; }
  .paginator { display: flex; gap: 8px; justify-content: center; margin-top: 20px; flex-wrap: wrap; }
  .page-btn { background: var(--card); border: 1px solid var(--border); color: var(--subtext); border-radius: 5px; padding: 6px 12px; font-size: 12px; cursor: pointer; }
  .page-btn.active { background: var(--light); color: #fff; border-color: var(--blue); }
  .page-btn:hover { border-color: var(--blue); }
  footer { text-align: center; padding: 24px; color: var(--subtext); font-size: 12px; border-top: 1px solid var(--border); margin-top: 32px; }
</style>
</head>
<body>
<header>
  <h1>Raport conformitate publicitate — afirmații „nr. 1" în comerțul electronic românesc</h1>
  <p>Generat la: {{ generated_at }} &nbsp;|&nbsp; Operatori scanați: {{ total_stores }} &nbsp;|&nbsp; Afirmații detectate: {{ total_findings }}</p>
</header>
<div class="container">
  <div class="stats-grid">
    <div class="stat-card red"><div class="label">Neconforme — lipsă sursă</div><div class="value">{{ count_nonconform }}</div></div>
    <div class="stat-card orange"><div class="label">Necesită verificare manuală</div><div class="value">{{ count_partial }}</div></div>
    <div class="stat-card blue"><div class="label">Magazine cu afirmații</div><div class="value">{{ stores_with_findings }}</div></div>
    <div class="stat-card"><div class="label">Magazine fără afirmații</div><div class="value">{{ stores_clean }}</div></div>
  </div>
  <div class="filters">
    <input type="text" id="searchInput" placeholder="Caută după magazin, persoană juridică, afirmație...">
    <button class="filter-btn active" onclick="filterVerdict('all', this)">Toate</button>
    <button class="filter-btn" onclick="filterVerdict('nonconform', this)">Neconforme</button>
    <button class="filter-btn" onclick="filterVerdict('partial', this)">Parțiale</button>
    <button class="export-btn" onclick="exportCSV()">Export CSV</button>
  </div>
  <div class="table-wrap">
    <table id="mainTable">
      <thead>
        <tr>
          <th>#</th>
          <th>Operator Economic</th>
          <th>Site</th>
          <th>Pagina Detectată</th>
          <th>Afirmație</th>
          <th>Verdict</th>
          <th>Indicatori Sursă</th>
          <th>Context</th>
          <th>Scanat la</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
  </div>
  <div class="paginator" id="paginator"></div>
</div>
<footer>
  Verdictele sunt preliminare și nu constituie constatare juridică definitivă. Verificare manuală obligatorie înainte de orice acțiune oficială.<br>
  Legislație aplicabilă: Legea 158/2008, OUG 34/2014, Directiva 2005/29/CE.
</footer>
<script>
const RAW_DATA = {{ raw_data }};
let filtered = [...RAW_DATA];
let currentPage = 1;
const PAGE_SIZE = 50;
let activeVerdict = 'all';
let searchTerm = '';

function getVerdictClass(v) {
  if (!v) return 'verdict-orange';
  if (v.includes('NECONFORMĂ')) return 'verdict-red';
  return 'verdict-orange';
}

function escHtml(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderTable() {
  const tbody = document.getElementById('tableBody');
  const start = (currentPage - 1) * PAGE_SIZE;
  const slice = filtered.slice(start, start + PAGE_SIZE);

  tbody.innerHTML = slice.map((row, i) => {
    const globalIdx = start + i + 1;
    const vClass = getVerdictClass(row.verdict);
    const sources = row.source_indicators_found && row.source_indicators_found.length
      ? '<span class="sources-list">' + escHtml(row.source_indicators_found.join(', ')) + '</span>'
      : '<span class="no-source">—</span>';
    const contextShort = row.context ? escHtml(row.context.substring(0, 120)) + '...' : '';
    const contextFull = escHtml(row.context || '');
    const ctxId = 'ctx_' + globalIdx;
    const pageUrl = row.page_url || row.store_url;
    const pagePath = pageUrl.replace(row.store_url, '') || '/';
    const siteDomain = row.store_url.replace('https://','').replace('http://','');

    const pjBlock = row.persoana_juridica
      ? '<div class="pj-name">' + escHtml(row.persoana_juridica) + '</div>'
        + (row.cui ? '<div class="cui-code">' + escHtml(row.cui) + '</div>' : '')
      : '<div class="pj-missing">neidentificată</div>';

    return '<tr>' +
      '<td style="color:var(--subtext)">' + globalIdx + '</td>' +
      '<td><div class="store-name">' + escHtml(row.store_name) + '</div>' + pjBlock + '</td>' +
      '<td class="link-cell"><a href="' + escHtml(row.store_url) + '" target="_blank" rel="noopener">&#127760; ' + escHtml(siteDomain) + '</a></td>' +
      '<td class="link-cell"><a href="' + escHtml(pageUrl) + '" target="_blank" rel="noopener">&#8599; ' + escHtml(pagePath) + '</a></td>' +
      '<td><span class="pattern-badge">' + escHtml(row.pattern_matched) + '</span></td>' +
      '<td><span class="verdict-badge ' + vClass + '">' + escHtml(row.verdict) + '</span></td>' +
      '<td>' + sources + '</td>' +
      '<td><div class="context-text" id="' + ctxId + '_short">' + contextShort + '</div>' +
        '<div class="context-text context-full" id="' + ctxId + '_full">' + contextFull + '</div>' +
        '<span class="context-toggle" onclick="toggleCtx(\'' + ctxId + '\')">&#9658; mai mult</span></td>' +
      '<td style="color:var(--subtext);white-space:nowrap;font-size:11px">' + escHtml(row.scanned_at || '') + '</td>' +
      '</tr>';
  }).join('');

  renderPaginator();
}

function renderPaginator() {
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pag = document.getElementById('paginator');
  if (totalPages <= 1) { pag.innerHTML = ''; return; }
  let html = '';
  for (let p = 1; p <= totalPages; p++) {
    html += '<button class="page-btn ' + (p === currentPage ? 'active' : '') + '" onclick="goPage(' + p + ')">' + p + '</button>';
  }
  pag.innerHTML = html;
}

function goPage(p) { currentPage = p; renderTable(); window.scrollTo(0,0); }

function applyFilters() {
  filtered = RAW_DATA.filter(row => {
    const matchVerdict = activeVerdict === 'all'
      || (activeVerdict === 'nonconform' && row.verdict && row.verdict.includes('NECONFORMĂ'))
      || (activeVerdict === 'partial' && row.verdict && row.verdict.includes('VERIFICARE'));
    const s = searchTerm.toLowerCase();
    const matchSearch = !s
      || (row.store_name || '').toLowerCase().includes(s)
      || (row.persoana_juridica || '').toLowerCase().includes(s)
      || (row.cui || '').toLowerCase().includes(s)
      || (row.store_url || '').toLowerCase().includes(s)
      || (row.pattern_matched || '').toLowerCase().includes(s)
      || (row.context || '').toLowerCase().includes(s);
    return matchVerdict && matchSearch;
  });
  currentPage = 1;
  renderTable();
}

function filterVerdict(v, btn) {
  activeVerdict = v;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  applyFilters();
}

document.getElementById('searchInput').addEventListener('input', function() {
  searchTerm = this.value;
  applyFilters();
});

function toggleCtx(id) {
  const short = document.getElementById(id + '_short');
  const full = document.getElementById(id + '_full');
  const toggle = full.nextElementSibling;
  if (full.classList.contains('visible')) {
    full.classList.remove('visible');
    short.style.display = '';
    toggle.innerHTML = '&#9658; mai mult';
  } else {
    full.classList.add('visible');
    short.style.display = 'none';
    toggle.innerHTML = '&#9660; mai puțin';
  }
}

function exportCSV() {
  const headers = ['Magazin','Persoana Juridica','CUI','URL','Pagina Detectata','Afirmatie','Verdict','Indicatori Sursa','Context','Scanat la'];
  const rows = filtered.map(r => [
    r.store_name, r.persoana_juridica || '', r.cui || '',
    r.store_url, r.page_url, r.pattern_matched,
    r.verdict, (r.source_indicators_found || []).join('; '),
    r.context, r.scanned_at
  ].map(v => '"' + String(v || '').replace(/"/g, '""') + '"'));
  const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\\n');
  const blob = new Blob(['\\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'raport_conformitate_' + new Date().toISOString().slice(0,10) + '.csv';
  a.click();
}

applyFilters();
</script>
</body>
</html>"""


def generate_dashboard(findings: list[dict], stores: list[dict], output_path: str) -> str:
    """Generează fișierul HTML de raportare."""
    total_stores = len(stores)
    total_findings = len(findings)
    stores_with_findings = len(set(f["store_url"] for f in findings))
    stores_clean = total_stores - stores_with_findings
    count_nonconform = sum(1 for f in findings if "NECONFORMĂ" in (f.get("verdict") or ""))
    count_partial = sum(1 for f in findings if "VERIFICARE" in (f.get("verdict") or ""))
    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")

    html = HTML_TEMPLATE
    html = html.replace("{{ generated_at }}", generated_at)
    html = html.replace("{{ total_stores }}", str(total_stores))
    html = html.replace("{{ total_findings }}", str(total_findings))
    html = html.replace("{{ count_nonconform }}", str(count_nonconform))
    html = html.replace("{{ count_partial }}", str(count_partial))
    html = html.replace("{{ stores_with_findings }}", str(stores_with_findings))
    html = html.replace("{{ stores_clean }}", str(stores_clean))
    html = html.replace("{{ raw_data }}", json.dumps(findings, ensure_ascii=False))

    Path(output_path).write_text(html, encoding="utf-8")
    return output_path

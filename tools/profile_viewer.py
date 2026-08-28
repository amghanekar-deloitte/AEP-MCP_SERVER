"""
profile_viewer — view_profile tool

Fetches one or more member profiles (comma-separated entity_ids), resolves segment names
in parallel, deduplicates commercialDetails, and returns populated HTML ready to publish.

Single ID  → single-profile view (sections + Formatted/Raw toggle)
Multiple   → multi-tab: one tab per member + "All Profiles" summary table with row JSON expand
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from auth import aep_get
from tools.schema_context import find_visits as _find_visits
from tools.usage_logger import track

# ── CSS ───────────────────────────────────────────────────────────────────────
_CSS = """<style>
  :root {
    --ground:#F2F4F7;--surface:#FFFFFF;--surface2:#F8F9FB;--border:#DDE1E9;
    --text:#0F1623;--text2:#4A5568;--text3:#7A8499;
    --accent:#1C5FA8;--accent-bg:#EBF2FC;
    --good:#16A34A;--good-bg:#DCFCE7;
    --muted:#64748B;--muted-bg:#F1F5F9;--tag-bg:#E9EDF5;--rule:#CBD5E1;
    --mono:'SF Mono','Cascadia Code','Fira Mono','Consolas',monospace;
    --jk:#7C3AED;--js:#0E7490;--jn:#065F46;--jb:#B45309;--jz:#94A3B8;
    --json-bg:#F6F8FF;--json-border:#E0E7F5;
  }
  @media(prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --ground:#0C0F14;--surface:#161B24;--surface2:#1C2230;--border:#252D3D;
    --text:#E4E9F2;--text2:#8B96B0;--text3:#5A6880;
    --accent:#4A90D9;--accent-bg:#112240;
    --good:#22C55E;--good-bg:#052E16;
    --muted:#7A8499;--muted-bg:#1A2030;--tag-bg:#1E2635;--rule:#2A3448;
    --jk:#C084FC;--js:#67E8F9;--jn:#6EE7B7;--jb:#FBBF24;--jz:#566E8A;
    --json-bg:#111827;--json-border:#1E2A3F;
  }}
  :root[data-theme="dark"]{
    --ground:#0C0F14;--surface:#161B24;--surface2:#1C2230;--border:#252D3D;
    --text:#E4E9F2;--text2:#8B96B0;--text3:#5A6880;
    --accent:#4A90D9;--accent-bg:#112240;
    --good:#22C55E;--good-bg:#052E16;
    --muted:#7A8499;--muted-bg:#1A2030;--tag-bg:#1E2635;--rule:#2A3448;
    --jk:#C084FC;--js:#67E8F9;--jn:#6EE7B7;--jb:#FBBF24;--jz:#566E8A;
    --json-bg:#111827;--json-border:#1E2A3F;
  }
  *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--ground);color:var(--text);font-family:'Segoe UI',system-ui,-apple-system,sans-serif;font-size:13px;line-height:1.5;min-height:100vh;padding:0 0 48px;}

  /* Topbar */
  .topbar{position:sticky;top:0;z-index:40;background:var(--surface);border-bottom:1px solid var(--border);padding:10px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;}
  .topbar-left{display:flex;flex-direction:column;gap:2px;}
  .eyebrow{font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:var(--accent);}
  .member-id{font-family:var(--mono);font-size:20px;font-weight:700;color:var(--text);letter-spacing:-0.01em;}
  .topbar-right{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
  .chip{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:4px;font-size:11px;font-weight:500;background:var(--tag-bg);color:var(--text2);border:1px solid var(--border);}
  .chip.accent{background:var(--accent-bg);color:var(--accent);border-color:transparent;}
  .chip.good{background:var(--good-bg);color:var(--good);border-color:transparent;}
  .chip-dot{width:6px;height:6px;border-radius:50%;background:currentColor;opacity:0.7;flex-shrink:0;}

  /* Tab bar */
  .tab-bar{position:sticky;top:57px;z-index:30;background:var(--surface);border-bottom:1px solid var(--border);padding:0 24px;display:flex;gap:0;overflow-x:auto;}
  .tab{padding:9px 16px;border:none;border-bottom:2px solid transparent;margin-bottom:-1px;background:transparent;color:var(--text3);font-size:12px;font-weight:500;cursor:pointer;white-space:nowrap;transition:all 100ms;}
  .tab.active{color:var(--accent);border-bottom-color:var(--accent);}
  .tab:hover:not(.active){color:var(--text2);background:var(--surface2);}
  .tab-content{display:none;}
  .tab-content.active{display:block;}

  /* Per-tab sub-toggle (Formatted / Raw JSON) */
  .stbar{display:flex;align-items:center;justify-content:flex-end;padding:10px 24px 0;gap:6px;}
  .stoggle{display:flex;background:var(--surface2);border:1px solid var(--border);border-radius:7px;padding:3px;gap:2px;}
  .stbtn{padding:3px 11px;border-radius:5px;border:none;background:transparent;color:var(--text3);font-size:11px;font-weight:500;cursor:pointer;transition:all 100ms;}
  .stbtn.active{background:var(--surface);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.12);font-weight:600;}
  .stbtn:hover:not(.active){color:var(--text2);}

  /* Page body */
  .page{max-width:900px;margin:0 auto;padding:20px 20px 0;}
  .grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;}
  @media(max-width:640px){.grid-2{grid-template-columns:1fr;}}
  .section-label{font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:var(--text3);margin:20px 0 8px;}
  .section-label:first-child{margin-top:0;}

  /* Cards */
  .card{background:var(--surface);border:1px solid var(--border);border-radius:6px;overflow:hidden;}
  .card-full{margin-bottom:16px;}
  .card-head{display:flex;align-items:center;justify-content:space-between;padding:9px 14px;border-bottom:1px solid var(--border);background:var(--surface2);}
  .card-head-left{display:flex;align-items:center;gap:8px;}
  .card-head-accent{width:3px;height:13px;background:var(--accent);border-radius:2px;flex-shrink:0;}
  .card-title{font-size:10.5px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;color:var(--text2);}

  /* JSON expand */
  .json-btn{font-size:10px;font-family:var(--mono);font-weight:600;padding:2px 7px;border-radius:3px;border:1px solid var(--border);background:var(--tag-bg);color:var(--jk);cursor:pointer;transition:all 100ms;white-space:nowrap;}
  .json-btn:hover{background:var(--accent-bg);border-color:var(--accent);}
  .json-btn.open{background:var(--accent-bg);border-color:var(--accent);color:var(--accent);}
  .json-panel{display:none;border-top:1px solid var(--json-border);background:var(--json-bg);overflow-x:auto;}
  .json-panel.open{display:block;}
  .json-panel pre{padding:12px 14px;font-family:var(--mono);font-size:11px;line-height:1.65;white-space:pre;tab-size:2;color:var(--text2);}
  .jk{color:var(--jk);}.js{color:var(--js);}.jn{color:var(--jn);font-variant-numeric:tabular-nums;}.jb{color:var(--jb);}.jz{color:var(--jz);}

  /* Ledger rows */
  .row{display:grid;grid-template-columns:38% 62%;border-bottom:1px solid var(--border);min-height:30px;}
  .row:last-child{border-bottom:none;}
  .row-key{padding:5px 12px 5px 14px;font-size:11px;color:var(--text3);font-weight:500;display:flex;align-items:center;background:var(--surface2);border-right:1px solid var(--border);}
  .row-val{padding:5px 12px;font-size:12px;color:var(--text);display:flex;align-items:center;flex-wrap:wrap;gap:4px;}
  .mono{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:11.5px;}
  .badge{display:inline-flex;align-items:center;gap:4px;padding:2px 7px;border-radius:3px;font-size:10.5px;font-weight:600;}
  .badge-yes{background:var(--good-bg);color:var(--good);}
  .badge-no{background:var(--muted-bg);color:var(--muted);}
  .badge-pol{background:var(--tag-bg);color:var(--text2);border:1px solid var(--border);}

  /* Policy table */
  .overflow-x{overflow-x:auto;}
  .policy-table{width:100%;border-collapse:collapse;}
  .policy-table th{font-size:10px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:var(--text3);padding:7px 12px;text-align:left;background:var(--surface2);border-bottom:1px solid var(--border);}
  .policy-table td{padding:7px 12px;font-size:11.5px;color:var(--text);border-bottom:1px solid var(--border);font-variant-numeric:tabular-nums;}
  .policy-table tr:last-child td{border-bottom:none;}
  .policy-table td.mono{font-family:var(--mono);font-size:11px;}
  .policy-table tr:hover td{background:var(--surface2);}

  /* Prompt */
  .prompt-card{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:start;padding:14px 16px;}
  .prompt-title{font-size:13px;font-weight:600;color:var(--text);margin-bottom:3px;}
  .prompt-sub{font-size:11px;color:var(--text2);margin-bottom:8px;}
  .prompt-meta{display:flex;flex-wrap:wrap;gap:6px;}
  .prompt-meta-item{font-size:10.5px;color:var(--text3);display:flex;align-items:center;gap:3px;}
  .prompt-meta-item strong{color:var(--text2);font-weight:600;}
  .savings-pill{background:var(--good-bg);color:var(--good);border-radius:5px;padding:8px 14px;text-align:center;flex-shrink:0;}
  .savings-amt{font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;display:block;}
  .savings-label{font-size:10px;opacity:0.75;text-transform:uppercase;letter-spacing:0.06em;}
  .no-prompts{padding:14px 16px;color:var(--text3);font-size:11.5px;}

  /* AH flags */
  .flags-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));}
  .flag-item{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:12px 8px;border-right:1px solid var(--border);border-bottom:1px solid var(--border);text-align:center;gap:5px;}
  .flag-icon{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;}
  .flag-on{background:var(--good-bg);color:var(--good);}
  .flag-off{background:var(--muted-bg);color:var(--muted);}
  .flag-name{font-size:10px;color:var(--text3);font-weight:500;line-height:1.3;}

  /* Segments */
  .seg-row{display:flex;align-items:center;justify-content:space-between;padding:8px 14px;border-bottom:1px solid var(--border);gap:12px;}
  .seg-row:last-child{border-bottom:none;}
  .seg-info{display:flex;flex-direction:column;gap:2px;flex:1;min-width:0;}
  .seg-name{font-size:11.5px;color:var(--text);font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .seg-id{font-family:var(--mono);font-size:10px;color:var(--text3);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
  .seg-status{font-size:10.5px;font-weight:600;color:var(--good);background:var(--good-bg);padding:2px 7px;border-radius:3px;flex-shrink:0;}
  .seg-time{font-size:10.5px;color:var(--text3);font-family:var(--mono);flex-shrink:0;}

  /* Raw view */
  .raw-wrap{background:var(--surface);border:1px solid var(--border);border-radius:6px;overflow:hidden;margin-bottom:24px;}
  .raw-toolbar{display:flex;align-items:center;justify-content:space-between;padding:8px 14px;border-bottom:1px solid var(--border);background:var(--surface2);}
  .raw-label{font-size:10.5px;font-weight:700;color:var(--text2);letter-spacing:0.04em;text-transform:uppercase;}
  .copy-btn{font-size:11px;padding:3px 10px;border-radius:4px;border:1px solid var(--border);background:var(--tag-bg);color:var(--text2);cursor:pointer;transition:all 100ms;}
  .copy-btn:hover{background:var(--accent-bg);color:var(--accent);border-color:var(--accent);}
  .raw-pre{padding:16px;font-family:var(--mono);font-size:11px;line-height:1.7;white-space:pre;overflow-x:auto;color:var(--text2);max-height:70vh;overflow-y:auto;}

  /* Summary table (All Profiles tab) */
  .summary-wrap{background:var(--surface);border:1px solid var(--border);border-radius:6px;overflow:hidden;margin-bottom:16px;}
  .summary-table{width:100%;border-collapse:collapse;min-width:700px;}
  .summary-table th{font-size:10px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;color:var(--text3);padding:8px 14px;text-align:left;background:var(--surface2);border-bottom:1px solid var(--border);white-space:nowrap;}
  .summary-table td{padding:9px 14px;font-size:12px;color:var(--text);border-bottom:1px solid var(--border);vertical-align:middle;}
  .summary-table .data-row:hover td{background:var(--surface2);cursor:default;}
  .summary-table .data-row:last-of-type td{border-bottom:none;}
  .member-link{font-family:var(--mono);font-size:11.5px;color:var(--accent);font-weight:600;background:var(--accent-bg);padding:2px 7px;border-radius:3px;cursor:pointer;border:none;text-decoration:none;}
  .member-link:hover{text-decoration:underline;}
  .count-badge{display:inline-flex;align-items:center;justify-content:center;min-width:22px;height:20px;padding:0 5px;border-radius:10px;font-size:11px;font-weight:600;background:var(--tag-bg);color:var(--text2);}
  .count-badge.has{background:var(--accent-bg);color:var(--accent);}
  .json-expand-row{display:none;background:var(--json-bg);}
  .json-expand-row td{padding:0;border-bottom:1px solid var(--json-border);}
  .json-expand-row pre{padding:14px;font-family:var(--mono);font-size:10.5px;line-height:1.65;white-space:pre;overflow-x:auto;color:var(--text2);max-height:400px;overflow-y:auto;}

  /* Footer */
  .footer{margin-top:24px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;font-size:10.5px;color:var(--text3);padding-top:14px;border-top:1px solid var(--border);margin-bottom:20px;}
  .footer-dot{width:3px;height:3px;border-radius:50%;background:var(--rule);}
</style>"""

# ── JS ────────────────────────────────────────────────────────────────────────
_JS = """
function highlight(json) {
  const s = JSON.stringify(json, null, 2);
  return s.replace(/("(\\\\u[a-zA-Z0-9]{4}|\\\\[^u]|[^\\\\"])*"(\\s*:)?|\\b(true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)/g, m => {
    let cls = 'jn';
    if (/^"/.test(m)) { cls = /:$/.test(m) ? 'jk' : 'js'; }
    else if (/true|false/.test(m)) cls = 'jb';
    else if (/null/.test(m)) cls = 'jz';
    const clean = m.endsWith(':') ? m.slice(0,-1) : m;
    const suffix = m.endsWith(':') ? ':' : '';
    return '<span class="'+cls+'">'+clean.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')+'</span>'+suffix;
  });
}

// Section JSON expand (within a profile tab)
function toggleJson(btn, panelId) {
  const panel = document.getElementById(panelId);
  const pre   = document.getElementById(panelId + '-pre');
  const open  = panel.classList.toggle('open');
  btn.classList.toggle('open', open);
  btn.textContent = open ? '{ \\u2715 }' : '{ }';
  if (open && !pre.innerHTML) pre.innerHTML = highlight(SECTION_JSON[panelId]);
}

// Multi-profile: switch top-level tab
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => { el.style.display='none'; el.classList.remove('active'); });
  document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
  const tc = document.getElementById('tab-' + tabId);
  if (tc) { tc.style.display='block'; tc.classList.add('active'); }
  const tb = document.querySelector('.tab[data-tab="' + tabId + '"]');
  if (tb) tb.classList.add('active');
}

// Per-tab Formatted / Raw JSON sub-toggle
function setTabView(memberId, view) {
  const fmt = document.getElementById('fmt-' + memberId);
  const raw = document.getElementById('raw-' + memberId);
  if (fmt) fmt.style.display = view === 'formatted' ? 'block' : 'none';
  if (raw) raw.style.display = view === 'raw' ? 'block' : 'none';
  document.querySelectorAll('#tab-' + memberId + ' .stbtn').forEach((b,i) => {
    b.classList.toggle('active', (i===0) === (view==='formatted'));
  });
  if (view === 'raw') {
    const pre = document.getElementById('rawpre-' + memberId);
    if (pre && !pre.innerHTML) pre.innerHTML = highlight(ALL_DATA[memberId]);
  }
}

// Single-profile Formatted / Raw toggle (no tabs)
function setView(v) {
  const fmt = document.getElementById('view-formatted');
  const raw = document.getElementById('view-raw');
  if (fmt) fmt.style.display = v === 'formatted' ? 'block' : 'none';
  if (raw) raw.style.display = v === 'raw' ? 'block' : 'none';
  document.querySelectorAll('.toggle-btn').forEach((b,i) => b.classList.toggle('active',(i===0)===(v==='formatted')));
  if (v === 'raw') {
    const pre = document.getElementById('raw-pre');
    if (pre && !pre.innerHTML) pre.innerHTML = highlight(ALL_DATA['__single__'] || {});
  }
}

// All-profiles summary: expand full JSON for a row
function toggleRowJson(btn, memberId) {
  const row = document.getElementById('rowjson-' + memberId);
  const pre = document.getElementById('rowpre-' + memberId);
  const open = row.style.display !== 'table-row';
  row.style.display = open ? 'table-row' : 'none';
  btn.classList.toggle('open', open);
  btn.textContent = open ? '{ \\u2715 }' : '{ }';
  if (open && pre && !pre.innerHTML) pre.innerHTML = highlight(ALL_DATA[memberId]);
}

// Copy raw JSON (single profile)
function copyRaw(memberId) {
  const key = memberId || '__single__';
  navigator.clipboard.writeText(JSON.stringify(ALL_DATA[key], null, 2)).then(() => {
    const btn = document.querySelector('#raw-' + key + ' .copy-btn, .copy-btn');
    if (btn) { btn.textContent='Copied!'; setTimeout(()=>btn.textContent='Copy',1500); }
  });
}
"""


# ── HTML helpers ──────────────────────────────────────────────────────────────

def _row(key, val_html):
    return f'<div class="row"><span class="row-key">{key}</span><span class="row-val">{val_html}</span></div>'

def _mono(val):
    return f'<span class="mono">{val}</span>'

def _badge_yn(val):
    on  = str(val) in ("Y", "1", "true", "True")
    lbl = "&#10003; Yes" if on else "No"
    cls = "badge-yes" if on else "badge-no"
    return f'<span class="badge {cls}">{lbl}</span>'

def _first(pipe_str):
    return str(pipe_str).split("|")[0].strip() if pipe_str else "—"

def _json_btn_panel(panel_id):
    return f'<button class="json-btn" onclick="toggleJson(this,\'{panel_id}\')">{{ }}</button>'

def _card(title, panel_id, body_html, extra_title=""):
    extra = (f' &nbsp;&middot;&nbsp; <span style="font-weight:400;text-transform:none;'
             f'letter-spacing:0;color:var(--text2)">{extra_title}</span>') if extra_title else ""
    return (
        f'<div class="card">'
        f'<div class="card-head">'
        f'<div class="card-head-left"><div class="card-head-accent"></div>'
        f'<span class="card-title">{title}{extra}</span></div>'
        f'{_json_btn_panel(panel_id)}'
        f'</div>'
        f'<div class="card-body">{body_html}</div>'
        f'<div class="json-panel" id="{panel_id}"><pre id="{panel_id}-pre"></pre></div>'
        f'</div>'
    )

def _card_full(title, panel_id, inner_html, extra_title=""):
    extra = (f' &nbsp;&middot;&nbsp; <span style="font-weight:400;text-transform:none;'
             f'letter-spacing:0;color:var(--text2)">{extra_title}</span>') if extra_title else ""
    return (
        f'<div class="card card-full">'
        f'<div class="card-head">'
        f'<div class="card-head-left"><div class="card-head-accent"></div>'
        f'<span class="card-title">{title}{extra}</span></div>'
        f'{_json_btn_panel(panel_id)}'
        f'</div>'
        f'{inner_html}'
        f'<div class="json-panel" id="{panel_id}"><pre id="{panel_id}-pre"></pre></div>'
        f'</div>'
    )


# ── Section builders (prefix = member ID for multi-profile) ───────────────────

def _build_ids_card(entity_id, entity_key, mem_univ, prefix=""):
    pid = f"{prefix}-json-ids" if prefix else "json-ids"
    rows = "".join([
        _row("Proxy ID",          _mono(entity_id)),
        _row("Entity ID",         f'<span class="mono" style="font-size:10.5px">{entity_key}</span>'),
        _row("EDW Member ID",     _mono(_first(mem_univ.get("edwMemberId", "—")))),
        _row("Member ID",         _mono(_first(mem_univ.get("memberID", "—")))),
        _row("Sub Cumb ID",       _mono(_first(mem_univ.get("subCumbID", "—")))),
        _row("Cumb ID",           _mono(_first(mem_univ.get("cumbID", "—")))),
        _row("PS Unique ID",      _mono(_first(mem_univ.get("psUniqId", "—")))),
        _row("MZB Individual ID", _mono(mem_univ.get("mzbIndivId", "—"))),
        _row("MZB Address ID",    _mono(_first(mem_univ.get("mzbAddressId", "—")))),
        _row("Control #",         _mono(_first(mem_univ.get("control", "—")))),
        _row("Org Arrangement",   _mono(_first(mem_univ.get("orgArrg", "—")))),
    ])
    return _card("Member Identifiers", pid, rows)


def _build_portal_card(cvs, commercial, mem_univ, prefix=""):
    pid = f"{prefix}-json-portal" if prefix else "json-portal"
    rows = "".join([
        _row("Portal Registered", _mono(cvs.get("portalRegDt", "—"))),
        _row("Portal Active",     _badge_yn(cvs.get("portalInd", "N"))),
        _row("Role",              '<span class="badge badge-pol">SUB</span>'),
        _row("PCP Selected",      _badge_yn(_first(commercial.get("pcpSelected", "N")))),
        _row("PayFlex Member",    _badge_yn("Y" if cvs.get("payflexMember", 0) else "N")),
        _row("A1A Eligible",      _badge_yn(mem_univ.get("a1aEligibility", "N"))),
        _row("ACO Eligible",      _badge_yn(commercial.get("acoEligibility", "N"))),
        _row("Orig ID Date",      _mono(_first(mem_univ.get("origIdDt", "—"))[:10])),
    ])
    return _card("Portal &amp; Eligibility", pid, rows)


def _build_commercial_card(deduped_details, prefix=""):
    pid      = f"{prefix}-json-commercial" if prefix else "json-commercial"
    employer = deduped_details[0].get("cust_nm", "") if deduped_details else ""
    rows_html = ""
    for d in deduped_details:
        pol  = d.get("pol_id", "")
        plan = d.get("planProd", "")
        eff  = d.get("memberEffDt", "")
        term = d.get("memberTermDt", "")
        term_td = ('<td class="mono" style="color:var(--good)">Active</td>'
                   if term == "9999-12-31" else f'<td class="mono">{term}</td>')
        acct = d.get("account", "")
        orig = d.get("memberOrigEffDate", "")
        rows_html += (
            f'<tr><td><span class="badge badge-pol">{pol}</span></td>'
            f'<td class="mono">{plan}</td><td class="mono">{eff}</td>'
            f'{term_td}<td class="mono">{acct}</td><td class="mono">{orig}</td></tr>'
        )
    inner = (
        f'<div class="overflow-x"><table class="policy-table">'
        f'<thead><tr><th>Policy ID</th><th>Plan / Product</th><th>Eff Date</th>'
        f'<th>Term Date</th><th>Account</th><th>Orig Eff</th></tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>'
    )
    return _card_full("Plan &amp; Policy Details", pid, inner, extra_title=employer)


def _build_prompts_card(visits, prefix=""):
    pid   = f"{prefix}-json-prompts" if prefix else "json-prompts"
    today = date.today().isoformat()

    def _is_active(v):
        end = (v.get("endDate") or "")
        return bool(end) and end >= today

    total   = len(visits)
    n_active  = sum(1 for v in visits if _is_active(v))
    n_expired = total - n_active

    if not visits:
        count_label = (
            f'<span style="font-weight:400;text-transform:none;letter-spacing:0;color:var(--text3)">'
            f'0 prompts</span>'
        )
        return _card_full(
            f'Personalized Prompts &nbsp;{count_label}', pid,
            '<div class="no-prompts">No personalized prompts found.</div>'
        )

    parts_cl = []
    if n_active:
        parts_cl.append(f'<span style="color:var(--good)">{n_active} active</span>')
    if n_expired:
        parts_cl.append(f'<span style="color:var(--muted)">{n_expired} expired</span>')
    count_label = (
        f'<span style="font-weight:400;text-transform:none;letter-spacing:0;color:var(--text3)">'
        f'{total} total &nbsp;&middot;&nbsp; {"&nbsp;&middot;&nbsp;".join(parts_cl)}</span>'
    )

    cards_html = ""
    for v in visits:
        active     = _is_active(v)
        status_badge = (
            '<span class="badge badge-yes" style="font-size:10px;padding:1px 7px">Active</span>'
            if active else
            '<span class="badge badge-no" style="font-size:10px;padding:1px 7px">Expired</span>'
        )
        claim_id = (v.get("claimInformation") or {}).get("associatedClaimId", "") or "—"
        savings  = v.get("projectedSavings", "")
        last_svc = ""
        try:
            ca = v.get("customAttributes", "")
            if ca and "last_service_dt" in str(ca):
                last_svc = str(ca).split("'last_service_dt':'")[1].split("'")[0]
        except Exception:
            pass
        savings_html = (
            f'<div class="savings-pill"><span class="savings-amt">${savings}</span>'
            f'<span class="savings-label">Proj. Savings</span></div>'
        ) if savings else ""
        sep = '<span class="prompt-meta-item" style="color:var(--rule)">|</span>'
        meta_parts = [
            f'Window: <strong>{v.get("startDate","")}&nbsp;&rarr;&nbsp;{v.get("endDate","")}</strong>',
            f'Claim: <strong class="mono" style="font-size:11px">{claim_id}</strong>',
        ]
        if last_svc:
            meta_parts.append(f'Last Svc: <strong>{last_svc}</strong>')
        if v.get("individualId"):
            meta_parts.append(f'Individual: <strong class="mono" style="font-size:11px">{v["individualId"]}</strong>')
        meta_html = sep.join(f'<span class="prompt-meta-item">{p}</span>' for p in meta_parts)
        opacity = '' if active else ' style="opacity:0.6"'
        cards_html += (
            f'<div class="prompt-card"{opacity}><div>'
            f'<div class="prompt-title" style="display:flex;align-items:center;gap:8px">'
            f'{v.get("promptName","")} {status_badge}</div>'
            f'<div class="prompt-sub">Cohort {v.get("cohortName","")} &middot; '
            f'Prompt ID {v.get("promptId","")} &middot; v{v.get("version","1")}</div>'
            f'<div class="prompt-meta">{meta_html}</div>'
            f'</div>{savings_html}</div>'
        )
    return _card_full(f'Personalized Prompts &nbsp;{count_label}', pid, cards_html)


def _build_flags_card(ah_list, prefix=""):
    pid = f"{prefix}-json-flags" if prefix else "json-flags"
    def fi(label, key, last=False):
        on   = ah_list.get(key, "N") == "Y"
        cls  = "flag-on" if on else "flag-off"
        icon = "&#10003;" if on else "&mdash;"
        s    = ' style="border-right:none"' if last else ""
        return (f'<div class="flag-item"{s}>'
                f'<div class="flag-icon {cls}">{icon}</div>'
                f'<span class="flag-name">{label}</span></div>')
    inner = '<div class="flags-grid">' + (
        fi("Portal",         "ahPortalInd") +
        fi("Web",            "ahWebInd") +
        fi("App",            "ahAppInd") +
        fi("Web Pricing",    "ahWebPricingInd") +
        fi("App Pricing",    "ahAppPricingInd") +
        fi("Improve Rec.",   "ahWebImproveRecordsInd", last=True)
    ) + '</div>'
    return _card_full("AH Digital Flags", pid, inner)


def _build_segs_card(seg_membership, segment_names, prefix=""):
    pid   = f"{prefix}-json-segs" if prefix else "json-segs"
    count = len(seg_membership)
    cl    = f'<span style="font-weight:400;text-transform:none;letter-spacing:0;color:var(--accent)">{count} realized</span>'
    rows_html = ""
    for sid, info in seg_membership.items():
        name   = segment_names.get(sid, {}).get("name", sid)
        status = info.get("status", "realized").capitalize()
        lqt    = info.get("lastQualificationTime", "")
        td     = (lqt[5:10] + "&nbsp;" + lqt[11:16]) if len(lqt) >= 16 else lqt
        rows_html += (
            f'<div class="seg-row">'
            f'<div class="seg-info">'
            f'<span class="seg-name">{name}</span>'
            f'<span class="seg-id">{sid}</span>'
            f'</div>'
            f'<span class="seg-status">{status}</span>'
            f'<span class="seg-time">{td}</span>'
            f'</div>'
        )
    return _card_full(f'Segment Membership &nbsp;{cl}', pid, rows_html)


# ── Section JSON slices (for JS SECTION_JSON) ─────────────────────────────────

def _section_json(entity_key, entity_data, segment_names, deduped_details, prefix=""):
    entity     = entity_data.get("entity", {})
    cvs        = entity.get("_cvs", {})
    mem_univ   = cvs.get("aetnaMemUniv", {})
    commercial = cvs.get("aetnacommercial", {})
    visits     = _find_visits(cvs)
    seg_memb   = entity.get("segmentMembership", {}).get("ups", {})

    def pk(name):
        return f"{prefix}-{name}" if prefix else name

    return {
        pk("json-ids"): {
            "proxyID":      cvs.get("proxyID", ""),
            "aetnaProxyId": cvs.get("aetnaProxyId", ""),
            "entityId":     entity_key,
            "identityMap":  entity.get("identityMap", {}),
            "identityGraph":entity_data.get("identityGraph", []),
            "aetnaMemUniv": mem_univ,
        },
        pk("json-portal"): {
            "portalRegDt":    cvs.get("portalRegDt", ""),
            "portalInd":      cvs.get("portalInd", ""),
            "payflexMember":  cvs.get("payflexMember", 0),
            "pcpSelected":    commercial.get("pcpSelected", ""),
            "a1aEligibility": mem_univ.get("a1aEligibility", ""),
            "acoEligibility": commercial.get("acoEligibility", ""),
            "origIdDt":       mem_univ.get("origIdDt", ""),
        },
        pk("json-commercial"): {"commercialDetails": deduped_details},
        pk("json-prompts"): visits,
        pk("json-flags"):   cvs.get("ahList", {}),
        pk("json-segs"): {
            sid: {
                "name":        segment_names.get(sid, {}).get("name", sid),
                "description": segment_names.get(sid, {}).get("description", ""),
                **info,
            }
            for sid, info in seg_memb.items()
        },
    }


# ── Profile sections (reusable inner HTML per member) ─────────────────────────

def _profile_sections(entity_id, entity_key, entity_data, segment_names, deduped_details,
                      sandbox, merge_policy_id, prefix=""):
    entity     = entity_data.get("entity", {})
    cvs        = entity.get("_cvs", {})
    mem_univ   = cvs.get("aetnaMemUniv", {})
    commercial = cvs.get("aetnacommercial", {})
    visits     = _find_visits(cvs)
    seg_memb   = entity.get("segmentMembership", {}).get("ups", {})
    sources    = entity_data.get("sources", [])
    ds_count   = len([s for s in sources if s != "segments"])
    mp_display = "Edge Merge Policy" if "7dc5b130" in merge_policy_id else f"{merge_policy_id[:8]} Merge Policy"

    ids_card     = _build_ids_card(entity_id, entity_key, mem_univ, prefix)
    portal_card  = _build_portal_card(cvs, commercial, mem_univ, prefix)
    comm_card    = _build_commercial_card(deduped_details, prefix)
    prompts_card = _build_prompts_card(visits, prefix)
    flags_card   = _build_flags_card(cvs.get("ahList", {}), prefix)
    segs_card    = _build_segs_card(seg_memb, segment_names, prefix)

    return f"""
    <p class="section-label">Identity &amp; Enrollment</p>
    <div class="grid-2">{ids_card}{portal_card}</div>
    <p class="section-label">Commercial Coverage</p>
    {comm_card}
    <p class="section-label">Personalized Prompts</p>
    {prompts_card}
    <p class="section-label">Digital Access &amp; Audience Membership</p>
    <div class="grid-2">{flags_card}{segs_card}</div>
    <div class="footer">
      <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;">
        <span>Sandbox: <strong style="color:var(--text2)">{sandbox}</strong></span>
        <span class="footer-dot"></span>
        <span>Namespace: <strong style="color:var(--text2)">ProxyID</strong></span>
        <span class="footer-dot"></span>
        <span>Merge Policy: <strong style="color:var(--text2)">{mp_display}</strong></span>
        <span class="footer-dot"></span>
        <span>Sources: <strong style="color:var(--text2)">{ds_count} dataset{"s" if ds_count!=1 else ""} + segments</strong></span>
      </div>
      <span>Adobe Experience Platform</span>
    </div>"""


# ── Single-profile HTML ───────────────────────────────────────────────────────

def _build_single_html(entity_id, entity_key, entity_data, segment_names, deduped_details, sandbox):
    merge_policy_id = entity_data.get("mergePolicy", {}).get("id", "")
    last_modified   = entity_data.get("lastModifiedAt", "")
    lm_display = last_modified.replace("T"," ").replace("Z"," UTC")[:22] if last_modified else ""
    mp_display = "Edge Merge Policy" if "7dc5b130" in merge_policy_id else f"{merge_policy_id[:8]} Merge Policy"

    inner = _profile_sections(entity_id, entity_key, entity_data, segment_names,
                               deduped_details, sandbox, merge_policy_id, prefix="")
    all_data_js   = json.dumps({entity_id: entity_data}, ensure_ascii=False)
    sect_json_js  = json.dumps(
        _section_json(entity_key, entity_data, segment_names, deduped_details, prefix=""),
        ensure_ascii=False
    )
    toggle_html = (
        '<div class="toggle" style="display:flex;background:var(--surface2);border:1px solid var(--border);'
        'border-radius:7px;padding:3px;gap:2px;">'
        '<button style="padding:4px 12px;border-radius:5px;border:none;background:var(--surface);'
        'color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.12);font-size:11.5px;font-weight:600;cursor:pointer;" '
        "onclick=\"setView('formatted')\">Formatted</button>"
        '<button style="padding:4px 12px;border-radius:5px;border:none;background:transparent;'
        'color:var(--text3);font-size:11.5px;font-weight:500;cursor:pointer;" '
        "onclick=\"setView('raw')\">Raw JSON</button>"
        '</div>'
    )

    return f"""<title>Member {entity_id}</title>
{_CSS}
<div class="topbar">
  <div class="topbar-left">
    <span class="eyebrow">Aetna &middot; {sandbox} &middot; Real-Time Customer Profile</span>
    <span class="member-id">{entity_id}</span>
  </div>
  <div class="topbar-right">
    <span class="chip"><span style="color:var(--text3);font-size:10px">Modified</span>&nbsp;{lm_display}</span>
    <span class="chip good"><span class="chip-dot"></span>Coverage Active</span>
    <span class="chip accent"><span class="chip-dot"></span>{mp_display}</span>
    {toggle_html}
  </div>
</div>
<div class="page">
  <div id="view-formatted">{inner}</div>
  <div id="view-raw" style="display:none">
    <div class="raw-wrap">
      <div class="raw-toolbar">
        <span class="raw-label">Full Profile JSON</span>
        <button class="copy-btn" onclick="copyRaw('{entity_id}')">Copy</button>
      </div>
      <div class="raw-pre" id="rawpre-{entity_id}"></div>
    </div>
  </div>
</div>
<script>
const ALL_DATA = {all_data_js};
const SECTION_JSON = {sect_json_js};
{_JS}
// alias for single-profile raw view
document.getElementById('view-raw') && (document.getElementById('view-raw').id = 'raw-{entity_id}');
document.querySelector('#raw-{entity_id} .raw-pre') && (document.querySelector('#raw-{entity_id} .raw-pre').id = 'rawpre-{entity_id}');
</script>"""


# ── Multi-profile HTML ────────────────────────────────────────────────────────

def _build_multi_html(profiles, sandbox):
    """profiles: list of dicts with keys entity_id, entity_key, entity_data,
       segment_names, deduped_details."""

    # Build ALL_DATA and SECTION_JSON across all profiles
    all_data: dict = {}
    section_json: dict = {}
    for p in profiles:
        mid  = p["entity_id"]
        ekey = p["entity_key"]
        edat = p["entity_data"]
        snames = p["segment_names"]
        deduped = p["deduped_details"]
        all_data[mid] = edat
        section_json.update(_section_json(ekey, edat, snames, deduped, prefix=mid))

    all_data_js  = json.dumps(all_data, ensure_ascii=False)
    sect_json_js = json.dumps(section_json, ensure_ascii=False)

    count = len(profiles)

    # ── Tab bar ──────────────────────────────────────────────────────────────
    tab_bar = (
        f'<button class="tab active" data-tab="all" onclick="switchTab(\'all\')">'
        f'All Profiles ({count})</button>'
    )
    for p in profiles:
        mid = p["entity_id"]
        tab_bar += (
            f'<button class="tab" data-tab="{mid}" onclick="switchTab(\'{mid}\')">'
            f'{mid}</button>'
        )

    # ── All Profiles summary table ────────────────────────────────────────────
    summary_rows = ""
    for p in profiles:
        mid    = p["entity_id"]
        edat   = p["entity_data"]
        ded    = p["deduped_details"]
        entity = edat.get("entity", {})
        cvs    = entity.get("_cvs", {})
        employer = ded[0].get("cust_nm", "—") if ded else "—"
        portal_reg = cvs.get("portalRegDt", "—")
        eff    = ded[0].get("memberEffDt", "—") if ded else "—"
        term   = ded[0].get("memberTermDt", "") if ded else ""
        cov    = f"{eff} → Active" if term == "9999-12-31" else (f"{eff} → {term}" if eff else "—")
        nseg   = len(entity.get("segmentMembership", {}).get("ups", {}))
        nvis   = len(cvs.get("personlizedVisits", []))
        seg_cls  = "has" if nseg else ""
        vis_cls  = "has" if nvis else ""

        summary_rows += f"""
        <tr class="data-row">
          <td><button class="member-link" onclick="switchTab('{mid}')">{mid}</button></td>
          <td style="font-size:11.5px">{employer}</td>
          <td><span class="badge badge-pol">SUB</span></td>
          <td class="mono" style="font-size:11px">{portal_reg}</td>
          <td style="font-size:11.5px">{cov}</td>
          <td><span class="count-badge {seg_cls}">{nseg}</span></td>
          <td><span class="count-badge {vis_cls}">{nvis}</span></td>
          <td><button class="json-btn" onclick="toggleRowJson(this,'{mid}')">{{ }}</button></td>
        </tr>
        <tr class="json-expand-row" id="rowjson-{mid}">
          <td colspan="8"><pre id="rowpre-{mid}"></pre></td>
        </tr>"""

    all_tab_html = f"""
    <div class="page" style="padding-top:20px;">
      <div class="overflow-x summary-wrap">
        <table class="summary-table">
          <thead><tr>
            <th>Proxy ID</th><th>Employer</th><th>Role</th>
            <th>Portal Reg</th><th>Coverage</th>
            <th>Segs</th><th>Prompts</th><th></th>
          </tr></thead>
          <tbody>{summary_rows}</tbody>
        </table>
      </div>
    </div>"""

    # ── Individual profile tabs ───────────────────────────────────────────────
    profile_tabs = ""
    for p in profiles:
        mid     = p["entity_id"]
        ekey    = p["entity_key"]
        edat    = p["entity_data"]
        snames  = p["segment_names"]
        deduped = p["deduped_details"]
        mpid    = edat.get("mergePolicy", {}).get("id", "")

        inner = _profile_sections(mid, ekey, edat, snames, deduped, sandbox, mpid, prefix=mid)

        profile_tabs += f"""
    <div class="tab-content" id="tab-{mid}" style="display:none">
      <div class="stbar">
        <div class="stoggle">
          <button class="stbtn active" onclick="setTabView('{mid}','formatted')">Formatted</button>
          <button class="stbtn" onclick="setTabView('{mid}','raw')">Raw JSON</button>
        </div>
      </div>
      <div id="fmt-{mid}">
        <div class="page" style="padding-top:16px;">{inner}</div>
      </div>
      <div id="raw-{mid}" style="display:none">
        <div class="page" style="padding-top:16px;">
          <div class="raw-wrap">
            <div class="raw-toolbar">
              <span class="raw-label">Full Profile JSON — {mid}</span>
              <button class="copy-btn" onclick="copyRaw('{mid}')">Copy</button>
            </div>
            <div class="raw-pre" id="rawpre-{mid}"></div>
          </div>
        </div>
      </div>
    </div>"""

    return f"""<title>{count} Member Profiles</title>
{_CSS}

<div class="topbar">
  <div class="topbar-left">
    <span class="eyebrow">Aetna &middot; {sandbox} &middot; Real-Time Customer Profile</span>
    <span class="member-id" style="font-size:18px">{count} Members</span>
  </div>
  <div class="topbar-right">
    <span class="chip accent"><span class="chip-dot"></span>aetna-hipaa-dev</span>
    <span class="chip good"><span class="chip-dot"></span>Edge Merge Policy</span>
  </div>
</div>

<div class="tab-bar">{tab_bar}</div>

<div class="tab-content active" id="tab-all">{all_tab_html}</div>
{profile_tabs}

<script>
const ALL_DATA = {all_data_js};
const SECTION_JSON = {sect_json_js};
{_JS}
</script>"""


# ── Tool registration ─────────────────────────────────────────────────────────

def register(mcp) -> None:

    @mcp.tool()
    @track("view_profile")
    def view_profile(
        entity_ids: str,
        entity_id_ns: str,
        sandbox: str = "",
        merge_policy_id: str = "",
    ) -> dict:
        """Fetch one or more member profiles and return HTML ready to publish as an artifact.

        Resolves all segment names in parallel, deduplicates commercialDetails rows.
        For a single ID: returns a single-profile view with Formatted/Raw toggle.
        For multiple IDs (comma-separated): returns a multi-tab view with an
        All Profiles summary table plus one tab per member.

        Claude should write the html field to the scratchpad as <member_ids>.html
        and publish it as an Artifact using the Artifact tool.

        Args:
            entity_ids: One or more identity values, comma-separated (e.g. 'A,B,C').
            entity_id_ns: Identity namespace code (e.g. 'ProxyID').
            sandbox: Sandbox name (defaults to AEP_SANDBOX_NAME env var).
            merge_policy_id: Optional merge policy ID applied to all profiles.
        """
        try:
            ids = [i.strip() for i in entity_ids.replace(";", ",").split(",") if i.strip()]
            if not ids:
                return {"error": "entity_ids is empty"}

            eff_sandbox = sandbox or "aetna-hipaa-dev"

            # ── 1. Fetch all profiles in parallel ─────────────────────────────
            def _fetch_profile(eid):
                params: dict = {
                    "schema.name": "_xdm.context.profile",
                    "entityId": eid,
                    "entityIdNS": entity_id_ns,
                }
                if merge_policy_id:
                    params["mergePolicyId"] = merge_policy_id
                return eid, aep_get(
                    "/data/core/ups/access/entities",
                    sandbox=sandbox or None,
                    params=params,
                )

            profile_results: dict = {}
            with ThreadPoolExecutor(max_workers=min(len(ids), 8)) as pool:
                futures = {pool.submit(_fetch_profile, eid): eid for eid in ids}
                for fut in as_completed(futures):
                    eid, resp = fut.result()
                    profile_results[eid] = resp

            # ── 2. Collect all unique segment IDs across all profiles ──────────
            all_seg_ids: set = set()
            for eid in ids:
                resp = profile_results.get(eid, {})
                if "error" not in resp:
                    ekey = next(iter(resp), None)
                    if ekey:
                        edat = resp[ekey]
                        seg_memb = edat.get("entity", {}).get("segmentMembership", {}).get("ups", {})
                        all_seg_ids.update(seg_memb.keys())

            def _fetch_seg(sid):
                try:
                    r = aep_get(f"/data/core/ups/segment/definitions/{sid}", sandbox=sandbox or None)
                    return sid, r.get("name", sid), r.get("description", "")
                except Exception:
                    return sid, sid, ""

            segment_names: dict = {}
            if all_seg_ids:
                with ThreadPoolExecutor(max_workers=min(len(all_seg_ids), 10)) as pool:
                    futures2 = {pool.submit(_fetch_seg, sid): sid for sid in all_seg_ids}
                    for fut in as_completed(futures2):
                        sid, name, desc = fut.result()
                        segment_names[sid] = {"name": name, "description": desc}

            # ── 3. Build per-profile data, deduplicate commercialDetails ───────
            profiles_data = []
            errors = []
            for eid in ids:
                resp = profile_results.get(eid, {})
                if "error" in resp:
                    errors.append({"entity_id": eid, "error": resp["error"]})
                    continue
                ekey = next(iter(resp), None)
                if not ekey:
                    errors.append({"entity_id": eid, "error": "empty response"})
                    continue
                edat = resp[ekey]
                cvs  = edat.get("entity", {}).get("_cvs", {})
                seen: set = set()
                deduped: list = []
                for row in cvs.get("aetnacommercial", {}).get("commercialDetails", []):
                    pol = row.get("pol_id", "")
                    if pol not in seen:
                        seen.add(pol)
                        deduped.append(row)
                profiles_data.append({
                    "entity_id":      eid,
                    "entity_key":     ekey,
                    "entity_data":    edat,
                    "segment_names":  segment_names,
                    "deduped_details":deduped,
                })

            if not profiles_data:
                return {"error": "All profile lookups failed", "details": errors}

            # ── 4. Build HTML ─────────────────────────────────────────────────
            if len(profiles_data) == 1:
                p = profiles_data[0]
                html = _build_single_html(
                    p["entity_id"], p["entity_key"], p["entity_data"],
                    p["segment_names"], p["deduped_details"], eff_sandbox,
                )
                filename = f"{p['entity_id']}.html"
            else:
                html = _build_multi_html(profiles_data, eff_sandbox)
                filename = "-".join(p["entity_id"] for p in profiles_data) + ".html"

            html_path = f"/tmp/aep-profile-{filename}"
            with open(html_path, "w", encoding="utf-8") as _fh:
                _fh.write(html)

            return {
                "html_file": html_path,
                "filename": filename,
                "member_ids": [p["entity_id"] for p in profiles_data],
                "errors": errors,
                "instruction": (
                    f"Read {html_path} and publish it as an Artifact "
                    f"titled '{filename.replace('.html', '')}'."
                ),
            }

        except Exception as exc:
            return {"error": str(exc)}

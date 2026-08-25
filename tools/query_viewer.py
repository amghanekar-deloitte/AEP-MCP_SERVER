"""
tools/query_viewer.py — view_query_results MCP tool

Runs a SQL query via QS PostgreSQL, generates a self-contained HTML artifact
(table view + Raw JSON toggle, syntax-highlighted), writes to /tmp/, and
returns the file path for Claude to read and publish as an artifact.
"""

import html as _html
import json
import re as _re
import time

from tools.usage_logger import track

# ── CSS ──────────────────────────────────────────────────────────────────────
_CSS = """
<style>
:root {
  --bg:#F4F7FB; --surface:#FFFFFF; --surface2:#F0F4FA; --surface3:#E8EEF8;
  --border:#DDE4EF; --text:#0C2340; --text2:#4A5E78; --muted:#7A8FA8;
  --accent:#1473E6; --accent-bg:rgba(20,115,230,0.10);
  --mono:'SF Mono','Fira Code','Cascadia Code',monospace;
  --j-s:#0E7490; --j-n:#065F46; --j-k:#7C3AED;
  --topbar:#1473E6; --topbar-text:#fff;
}
@media (prefers-color-scheme:dark) {
  :root:not([data-theme="light"]) {
    --bg:#0D1626; --surface:#152035; --surface2:#1C2B42; --surface3:#243450;
    --border:#263A55; --text:#E2EAF4; --text2:#94AABF; --muted:#566E8A;
    --accent:#4A9EE5; --accent-bg:rgba(74,158,229,0.12);
    --j-s:#67E8F9; --j-n:#6EE7B7; --j-k:#C084FC;
    --topbar:#1C2B42; --topbar-text:#E2EAF4;
  }
}
:root[data-theme="dark"] {
  --bg:#0D1626; --surface:#152035; --surface2:#1C2B42; --surface3:#243450;
  --border:#263A55; --text:#E2EAF4; --text2:#94AABF; --muted:#566E8A;
  --accent:#4A9EE5; --accent-bg:rgba(74,158,229,0.12);
  --j-s:#67E8F9; --j-n:#6EE7B7; --j-k:#C084FC;
  --topbar:#1C2B42; --topbar-text:#E2EAF4;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.5;}

.topbar{background:var(--topbar);color:var(--topbar-text);padding:10px 24px;display:flex;align-items:center;justify-content:space-between;}
.topbar-title{font-size:13px;font-weight:600;letter-spacing:.02em;}
.topbar-sub{font-size:11px;opacity:.75;margin-top:1px;}

header{background:var(--surface);border-bottom:1px solid var(--border);padding:12px 24px;position:sticky;top:0;z-index:20;}
.header-row{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;}
.chips{display:flex;flex-wrap:wrap;gap:6px;}
.chip{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--border);border-radius:20px;padding:3px 10px;font-size:11.5px;color:var(--text2);background:var(--surface2);font-variant-numeric:tabular-nums;}
.chip strong{color:var(--text);font-weight:600;}
.chip-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0;}
.toggle{display:flex;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:3px;gap:2px;}
.toggle-btn{padding:5px 13px;border-radius:6px;border:none;background:transparent;color:var(--muted);font-size:12px;font-weight:500;cursor:pointer;transition:all 120ms;white-space:nowrap;}
.toggle-btn.active{background:var(--surface);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.12);font-weight:600;}
.toggle-btn:hover:not(.active){color:var(--text);}

.sql-bar{background:var(--surface2);border-bottom:1px solid var(--border);padding:8px 24px;}
.sql-label{font-size:10.5px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin-bottom:3px;}
.sql-text{font-family:var(--mono);font-size:12px;color:var(--text2);white-space:pre-wrap;word-break:break-all;max-height:56px;overflow:hidden;}
.sql-text.expanded{max-height:none;}
.sql-expand{font-size:11px;color:var(--accent);cursor:pointer;background:none;border:none;padding:2px 0 0;display:block;}

main{padding:20px 24px;}
.table-wrap{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;overflow-x:auto;}
table{width:100%;border-collapse:collapse;min-width:400px;}
thead tr{background:var(--surface2);}
thead th{padding:9px 14px;text-align:left;font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border);white-space:nowrap;}
thead th:first-child{padding-left:18px;}thead th:last-child{padding-right:18px;}
tbody tr{border-bottom:1px solid var(--border);transition:background 100ms;}
tbody tr:last-child{border-bottom:none;}
tbody tr:hover{background:var(--surface2);}
td{padding:10px 14px;vertical-align:top;font-size:13px;}
td:first-child{padding-left:18px;}td:last-child{padding-right:18px;}
.footer{text-align:center;padding:9px;font-size:11.5px;color:var(--muted);background:var(--surface2);border-top:1px solid var(--border);}

.null-val{color:var(--muted);}
.mono-val{font-family:var(--mono);font-size:12px;}
.nested-toggle{cursor:pointer;font-family:var(--mono);font-size:12px;color:var(--accent);background:var(--accent-bg);padding:1px 7px;border-radius:4px;border:none;}
.nested-json{font-family:var(--mono);font-size:11.5px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:10px;margin-top:5px;white-space:pre;overflow-x:auto;max-width:640px;}
.j-s{color:var(--j-s);} .j-n{color:var(--j-n);} .j-k{color:var(--j-k);}

.raw-wrap{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.raw-toolbar{display:flex;justify-content:flex-end;padding:8px 14px;border-bottom:1px solid var(--border);background:var(--surface2);}
.copy-btn{font-size:11.5px;padding:4px 12px;border-radius:6px;border:1px solid var(--border);background:var(--surface);color:var(--text2);cursor:pointer;}
.copy-btn:hover{color:var(--text);}
.raw-pre{font-family:var(--mono);font-size:12px;padding:16px 20px;white-space:pre;overflow-x:auto;line-height:1.6;}
.empty-state{text-align:center;padding:48px 24px;color:var(--muted);font-size:13px;}
</style>
"""

# ── JS ────────────────────────────────────────────────────────────────────────
_JS = r"""
<script>
function switchView(v, btn) {
  document.getElementById('view-formatted').style.display = v === 'formatted' ? 'block' : 'none';
  document.getElementById('view-raw').style.display = v === 'raw' ? 'block' : 'none';
  document.querySelectorAll('.toggle-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
}
function toggleNested(id) {
  var el = document.getElementById(id);
  if (!el) return;
  var open = el.style.display !== 'none';
  el.style.display = open ? 'none' : 'block';
  if (!open && !el.dataset.hl) {
    el.innerHTML = highlight(el.textContent);
    el.dataset.hl = '1';
  }
}
function expandSql() {
  var el = document.getElementById('sql-text');
  var btn = document.getElementById('sql-expand-btn');
  el.classList.toggle('expanded');
  btn.textContent = el.classList.contains('expanded') ? 'show less ▴' : 'show more ▾';
}
function copyRaw() {
  var pre = document.getElementById('raw-pre');
  navigator.clipboard.writeText(pre ? pre.dataset.raw || pre.textContent : '').catch(function(){});
}
function highlight(text) {
  var t = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t = t.replace(/"((?:[^"\\\\]|\\\\.)*)"(\s*):/g, '<span class="j-k">"$1"</span>$2:');
  t = t.replace(/:\s*"((?:[^"\\\\]|\\\\.)*)"(?=[,\n\r\]\}]|$)/g, ': <span class="j-s">"$1"</span>');
  t = t.replace(/:\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)(?=[,\n\r\]\}]|$)/g, ': <span class="j-n">$1</span>');
  t = t.replace(/:\s*(true|false|null)(?=[,\n\r\]\}]|$)/g, ': <span class="j-k">$1</span>');
  return t;
}
document.addEventListener('DOMContentLoaded', function() {
  var rawPre = document.getElementById('raw-pre');
  if (rawPre) {
    rawPre.dataset.raw = rawPre.textContent;
    rawPre.innerHTML = highlight(rawPre.textContent);
  }
  var sqlEl = document.getElementById('sql-text');
  var sqlBtn = document.getElementById('sql-expand-btn');
  if (sqlEl && sqlBtn && sqlEl.scrollHeight <= sqlEl.clientHeight + 4) {
    sqlBtn.style.display = 'none';
  }
  document.querySelectorAll('.nested-json[data-hl="0"]').forEach(function(el) {
    // highlight on first expand, not on load (perf)
  });
});
</script>
"""

# ── cell renderer ─────────────────────────────────────────────────────────────
_nested_counter = 0


def _sanitize(val):
    """Convert psycopg2 non-JSON-serializable types to plain Python types."""
    import datetime, decimal
    if val is None:
        return None
    if isinstance(val, (bool, int, float, str)):
        return val
    if isinstance(val, (datetime.date, datetime.datetime, datetime.time)):
        return val.isoformat()
    if isinstance(val, decimal.Decimal):
        return float(val)
    if isinstance(val, (list, tuple)):
        return [_sanitize(v) for v in val]
    if isinstance(val, dict):
        return {k: _sanitize(v) for k, v in val.items()}
    return str(val)


def _cell_html(val, col_idx: int, row_idx: int) -> str:
    if val is None:
        return '<span class="null-val">—</span>'

    # dict / list → collapsible JSON block
    if isinstance(val, (dict, list)):
        return _nested_block(val, col_idx, row_idx)

    s = str(val)

    # string that is JSON → expand
    if s.strip().startswith(("{", "[")):
        try:
            parsed = json.loads(s)
            return _nested_block(parsed, col_idx, row_idx)
        except Exception:
            pass

    # long string → truncate with title tooltip
    if len(s) > 140:
        esc = _html.escape(s)
        return f'<span class="mono-val" title="{esc}">{_html.escape(s[:140])}…</span>'

    return _html.escape(s)


def _nested_block(val, col_idx: int, row_idx: int) -> str:
    uid = f"n{col_idx}r{row_idx}"
    pretty = json.dumps(val, indent=2, ensure_ascii=False)
    esc = _html.escape(pretty)
    preview = "{…}" if isinstance(val, dict) else "[…]"
    return (
        f'<button class="nested-toggle" onclick="toggleNested(\'{uid}\')">{preview}</button>'
        f'<pre class="nested-json" id="{uid}" style="display:none" data-hl="0">{esc}</pre>'
    )


# ── HTML builder ──────────────────────────────────────────────────────────────
def _generate_html(sql: str, columns: list, rows: list, sandbox: str, title: str) -> str:
    row_count = len(rows)
    col_count = len(columns)
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    chips = (
        f'<span class="chip"><span class="chip-dot" style="background:#1473E6"></span>'
        f'<strong>{row_count}</strong> row{"s" if row_count != 1 else ""}</span>'
        f'<span class="chip"><strong>{col_count}</strong> col{"s" if col_count != 1 else ""}</span>'
        f'<span class="chip">{_html.escape(sandbox)}</span>'
        f'<span class="chip">{_html.escape(ts)}</span>'
    )

    th_html = "".join(f"<th>{_html.escape(c)}</th>" for c in columns)

    tbody_parts = []
    for r_idx, row in enumerate(rows):
        cells = "".join(
            f"<td>{_cell_html(row.get(c), c_idx, r_idx)}</td>"
            for c_idx, c in enumerate(columns)
        )
        tbody_parts.append(f"<tr>{cells}</tr>")
    tbody_html = "\n".join(tbody_parts)

    raw_json = json.dumps(rows, indent=2, ensure_ascii=False)
    raw_esc = _html.escape(raw_json)
    sql_esc = _html.escape(sql.strip())
    title_esc = _html.escape(title)
    sandbox_esc = _html.escape(sandbox)
    footer = f"{row_count} row{'s' if row_count != 1 else ''} returned"

    empty = (
        '<div class="empty-state">No rows returned.</div>'
        if row_count == 0
        else f'<table><thead><tr>{th_html}</tr></thead><tbody>{tbody_html}</tbody></table>'
             f'<div class="footer">{footer}</div>'
    )

    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title_esc}</title>",
        _CSS,
        "</head>",
        "<body>",
        f'<div class="topbar">',
        f'  <div><div class="topbar-title">{title_esc}</div>',
        f'  <div class="topbar-sub">AEP Query Service · {sandbox_esc}</div></div>',
        "</div>",
        "<header>",
        f'  <div class="header-row">',
        f'    <div class="chips">{chips}</div>',
        '    <div class="toggle">',
        '      <button class="toggle-btn active" onclick="switchView(\'formatted\', this)">Formatted</button>',
        '      <button class="toggle-btn" onclick="switchView(\'raw\', this)">Raw JSON</button>',
        "    </div>",
        "  </div>",
        "</header>",
        '<div class="sql-bar">',
        '  <div class="sql-label">SQL</div>',
        f'  <div class="sql-text" id="sql-text">{sql_esc}</div>',
        '  <button class="sql-expand" id="sql-expand-btn" onclick="expandSql()">show more ▾</button>',
        "</div>",
        "<main>",
        '  <div id="view-formatted">',
        '    <div class="table-wrap">',
        f"      {empty}",
        "    </div>",
        "  </div>",
        '  <div id="view-raw" style="display:none">',
        '    <div class="raw-wrap">',
        '      <div class="raw-toolbar">',
        '        <button class="copy-btn" onclick="copyRaw()">Copy JSON</button>',
        "      </div>",
        f'      <pre class="raw-pre" id="raw-pre">{raw_esc}</pre>',
        "    </div>",
        "  </div>",
        "</main>",
        _JS,
        "</body>",
        "</html>",
    ])


# ── text summary ──────────────────────────────────────────────────────────────
def _text_summary(sql: str, columns: list, rows: list, sandbox: str, title: str) -> str:
    lines = [f"**{title}** — {len(rows)} row{'s' if len(rows) != 1 else ''} in `{sandbox}`"]
    if not rows:
        lines.append("_No rows returned._")
        return "\n".join(lines)

    lines.append(f"Columns: {', '.join(f'`{c}`' for c in columns)}")
    lines.append("")

    # preview up to 5 rows
    preview_rows = rows[:5]
    # header
    header = " | ".join(columns)
    sep = " | ".join("---" for _ in columns)
    lines.append(f"| {header} |")
    lines.append(f"| {sep} |")
    for row in preview_rows:
        cells = []
        for c in columns:
            v = row.get(c)
            if v is None:
                cells.append("—")
            elif isinstance(v, (dict, list)):
                cells.append("{…}")
            else:
                s = str(v).replace("|", "\\|").replace("\n", " ")
                cells.append(s[:60] + ("…" if len(s) > 60 else ""))
        lines.append(f"| {' | '.join(cells)} |")

    if len(rows) > 5:
        lines.append(f"_… and {len(rows) - 5} more row{'s' if len(rows) - 5 != 1 else ''}_")

    return "\n".join(lines)


# ── personalized-prompts: composite tuple parser ──────────────────────────────
_PROMPT_FIELDS = [
    "priority", "cohort_name", "end_date", "category_priority",
    "prompt_name", "start_date", "status", "attributes",
    "auth_info", "pcp_info", "service_info", "member_id", "projected_savings",
]

_PP_CATS = {
    "radiology": {"label": "Radiology",          "dot": "#1D4ED8", "cls": "cat-radiology"},
    "ahv":       {"label": "Annual Health Visit", "dot": "#166534", "cls": "cat-ahv"},
    "er":        {"label": "ER Avoidance",        "dot": "#C2410C", "cls": "cat-er"},
    "acuity":    {"label": "Low Acuity",          "dot": "#BE123C", "cls": "cat-acuity"},
    "other":     {"label": "Other",               "dot": "#475569", "cls": "cat-other"},
}


def _pp_split_tuples(s: str) -> list:
    """Split a PostgreSQL composite array into individual record strings.

    Handles two formats psycopg2 may return:
      [{field,field,...},{...}]   — array of row-type (most common)
      {(field,field,...),(...)}   — older text representation
    """
    s = s.strip()
    if s.startswith("["):
        # Array-of-records format: [{...},{...}]
        s = s[1:]
        if s.endswith("]"):
            s = s[:-1]
        open_c, close_c = "{", "}"
    else:
        # Composite format: {(...),(...)}
        if s.startswith("{"):
            s = s[1:]
        if s.endswith("}"):
            s = s[:-1]
        open_c, close_c = "(", ")"

    result, depth, start = [], 0, 0
    for i, c in enumerate(s):
        if c == open_c:
            depth += 1
        elif c == close_c:
            depth -= 1
            if depth == 0:
                result.append(s[start:i + 1].strip())
                start = i + 2 if i + 1 < len(s) and s[i + 1] == "," else i + 1
    return result


def _pp_split_fields(s: str) -> list:
    fields, depth, in_q, cur = [], 0, False, []
    for c in s:
        if c == '"':
            in_q = not in_q
        if not in_q:
            if c in ("(", "{", "["):
                depth += 1
            elif c in (")", "}", "]"):
                depth -= 1
        if c == "," and depth == 0 and not in_q:
            fields.append("".join(cur).strip())
            cur = []
        else:
            cur.append(c)
    if cur:
        fields.append("".join(cur).strip())
    return fields


def _pp_parse_attrs(s: str) -> dict:
    attrs = {}
    for m in _re.finditer(r"'([^']+)'\s*:\s*'([^']*)'", s):
        attrs[m.group(1)] = m.group(2)
    for m in _re.finditer(r"'([^']+)'\s*:\s*(\d+)", s):
        if m.group(1) not in attrs:
            attrs[m.group(1)] = m.group(2)
    return attrs


def _pp_parse_visits(visits_str: str) -> list:
    if not visits_str:
        return []
    result = []
    for t in _pp_split_tuples(str(visits_str)):
        inner = t
        if inner and inner[0] in ("(", "{"):
            inner = inner[1:]
        if inner and inner[-1] in (")", "}"):
            inner = inner[:-1]
        fields = _pp_split_fields(inner)
        visit = {}
        for i, fname in enumerate(_PROMPT_FIELDS):
            val = fields[i].strip() if i < len(fields) else None
            if val in (None, "NULL", "null", ""):
                visit[fname] = None
            elif fname == "attributes":
                visit[fname] = _pp_parse_attrs(val)
            elif fname in ("priority", "category_priority", "status"):
                try:
                    visit[fname] = int(val)
                except (ValueError, TypeError):
                    visit[fname] = val
            elif fname == "projected_savings":
                try:
                    visit[fname] = int(val)
                except (ValueError, TypeError):
                    visit[fname] = None
            else:
                visit[fname] = val.strip('"').strip("'")
        result.append(visit)
    return result


def _pp_category(cohort: str, prompt: str) -> str:
    c = (cohort or "").lower()
    p = (prompt or "").lower()
    if "annual health" in p or "ahv" in c:
        return "ahv"
    if "emergency room" in p or " er " in p or "er avoidance" in p:
        return "er"
    if "radiology" in p or "c3" in c or "c1" in c:
        return "radiology"
    if "acuity" in p or "low acuity" in p:
        return "acuity"
    return "other"


def _pp_ctx_sub(cat: str, attrs: dict) -> str:
    if not attrs:
        return ""
    if cat == "ahv":
        first = (attrs.get("pcp_first_name") or "").capitalize()
        last = (attrs.get("pcp_last_name") or "").capitalize()
        name = f"{first} {last}".strip()
        svc = attrs.get("last_service_date", "")
        return (f"PCP: {name}" if name else "") + (f" · last visit: {svc}" if svc else "")
    if cat == "er":
        parts = []
        if attrs.get("last_er_start_dt"):
            parts.append(f"ER visit: {attrs['last_er_start_dt']}")
        if attrs.get("last_er_clm_hdr_id"):
            parts.append(f"Claim: {attrs['last_er_clm_hdr_id']}")
        if attrs.get("n_er_1yr"):
            parts.append(f"{attrs['n_er_1yr']} ER in last yr")
        return " · ".join(parts)
    if attrs.get("auth_clm_id"):
        return f"Claim: {attrs['auth_clm_id']}"
    if attrs.get("last_service_dt"):
        return f"Last svc: {attrs['last_service_dt']}"
    return ""


def _pp_fmt_date(d) -> str:
    if not d:
        return ""
    parts = str(d).split("-")
    return f"{parts[1]}/{parts[2]}/{parts[0]}" if len(parts) == 3 else str(d)


# Raw string — no escape processing, so regex character classes stay intact.
_PP_JS = r"""<script>
function setMode(m){
  document.getElementById('view-formatted').style.display=m==='formatted'?'block':'none';
  document.getElementById('view-raw').style.display=m==='raw'?'block':'none';
  document.querySelectorAll('.toggle-btn').forEach(function(b){
    b.classList.toggle('active',b.textContent.toLowerCase().startsWith(m));
  });
}
function toggleExpand(id){
  var p=document.getElementById(id),b=document.getElementById('btn-'+id);
  var open=p.classList.toggle('open');
  b.classList.toggle('open',open);
  var txt=b.querySelector('.btn-label');
  if(txt) txt.textContent=open?'Collapse':'Expand';
  if(open&&!p.dataset.hl){
    p.querySelectorAll('.j-pre').forEach(function(el){el.innerHTML=hl(el.textContent);el.dataset.hl='1';});
    p.dataset.hl='1';
  }
}
function hl(t){
  t=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t=t.replace(/"([^"\\]|\\.)*"(\s*):/g,function(m){return'<span class="jk">'+m.replace(/:/,'</span>:');});
  t=t.replace(/:\s*"([^"\\]|\\.)*"(?=[,\n\r\]}]|$)/g,function(m){return': <span class="jv">'+m.slice(m.indexOf('"'))+'</span>';});
  t=t.replace(/:\s*(-?\d+(?:\.\d+)?)(?=[,\n\r\]}]|$)/g,': <span class="jn">$1</span>');
  t=t.replace(/:\s*(true|false|null)(?=[,\n\r\]}]|$)/g,': <span class="jnull">$1</span>');
  return t;
}
</script>"""


def _generate_prompts_html(members: list, sandbox: str, title: str) -> str:
    total_offers = sum(len(m["visits"]) for m in members)
    cat_counts: dict = {}
    ts = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    title_esc = _html.escape(title)
    sandbox_esc = _html.escape(sandbox)

    # ── formatted table rows ───────────────────────────────────────────────
    fmt_rows = []
    for m in members:
        visits = m["visits"]
        multi = len(visits) > 1
        for i, v in enumerate(visits):
            cat = _pp_category(v.get("cohort_name", ""), v.get("prompt_name", ""))
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            meta = _PP_CATS.get(cat, _PP_CATS["other"])
            attrs = v.get("attributes") or {}
            sub = _pp_ctx_sub(cat, attrs)
            svc = attrs.get("last_service_dt") or attrs.get("last_service_date") or ""
            savings = v.get("projected_savings")
            row_cls = ""
            if multi:
                row_cls = "group-start" if i == 0 else ("group-end" if i == len(visits) - 1 else "group-mid")

            id_cell = ""
            if i == 0:
                id_cell = f'<span class="proxy-id">{_html.escape(m["proxy_id"])}</span>'
                if multi:
                    id_cell += f'<div class="multi-label">{len(visits)} offers</div>'

            savings_html = (
                f'<span class="savings-val">${savings:,}</span>' if savings
                else '<span class="savings-null">—</span>'
            )
            ctx_html = (
                f'<div class="ctx-main">{_html.escape(v.get("cohort_name","") or "")} · '
                f'{_html.escape(v.get("prompt_name","") or "")}</div>'
                + (f'<div class="ctx-sub">{_html.escape(sub)}</div>' if sub else "")
            )
            start_html = f'<div class="date-main">{_html.escape(_pp_fmt_date(v.get("start_date")) or "—")}</div>'
            if svc:
                start_html += f'<div class="date-sub">svc: {_html.escape(svc)}</div>'
            end_html = f'<div class="date-main">{_html.escape(_pp_fmt_date(v.get("end_date")) or "—")}</div>'

            fmt_rows.append(
                f'<tr class="{row_cls}">'
                f'<td class="id-cell">{id_cell}</td>'
                f'<td><span class="cat-badge {meta["cls"]}">{meta["label"]}</span></td>'
                f'<td>{ctx_html}</td>'
                f'<td>{start_html}</td>'
                f'<td>{end_html}</td>'
                f'<td>{savings_html}</td>'
                f'</tr>'
            )

    # ── raw rows ────────────────────────────────────────────────────────────
    raw_rows = []
    for idx, m in enumerate(members):
        eid = f"e{idx}"
        visits_json = json.dumps(m["visits"], indent=2, ensure_ascii=False)
        esc_json = _html.escape(visits_json)
        preview = _html.escape(str(m["visits"])[:80]) + ("…" if len(str(m["visits"])) > 80 else "")
        raw_rows.append(
            f'<tr>'
            f'<td style="color:var(--muted);font-size:12px;width:36px;font-variant-numeric:tabular-nums">{idx+1}</td>'
            f'<td><span class="raw-id">{_html.escape(m["proxy_id"])}</span></td>'
            f'<td class="raw-cell">'
            f'<span class="raw-preview">{preview}</span>'
            f'<button class="expand-btn" id="btn-{eid}" onclick="toggleExpand(\'{eid}\')">'
            f'<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">'
            f'<polyline points="4,6 8,10 12,6"/></svg>'
            f'<span class="btn-label">Expand</span></button>'
            f'<div class="json-panel" id="{eid}">'
            f'<div class="json-scroll"><pre class="j-pre" data-json="1">{esc_json}</pre></div>'
            f'</div></td></tr>'
        )

    # ── chips ───────────────────────────────────────────────────────────────
    chips = (
        f'<span class="chip"><strong>{len(members)}</strong> members</span>'
        f'<span class="chip"><strong>{total_offers}</strong> offer assignments</span>'
        f'<span class="chip">{sandbox_esc}</span>'
        f'<span class="chip">{_html.escape(ts)}</span>'
    )
    for cat, count in cat_counts.items():
        meta = _PP_CATS.get(cat, _PP_CATS["other"])
        chips += (
            f'<span class="chip">'
            f'<span class="chip-dot" style="background:{meta["dot"]}"></span>'
            f'<strong>{count}</strong> {meta["label"].split()[0]}</span>'
        )

    footer_txt = _html.escape(
        f"{total_offers} offers · {len(members)} members · {sandbox} · {ts}"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_esc}</title>
<style>
:root {{
  --bg:#F4F7FB; --surface:#FFFFFF; --surface2:#F0F4FA; --surface3:#E8EEF8;
  --border:#DDE4EF; --text:#0C2340; --text2:#4A5E78; --muted:#7A8FA8;
  --accent:#1473E6; --accent-bg:rgba(20,115,230,0.10);
  --mono:'SF Mono','Fira Code','Cascadia Code',monospace;
  --cat-radiology-bg:#EFF6FF; --cat-radiology-text:#1D4ED8; --cat-radiology-border:#BFDBFE;
  --cat-ahv-bg:#F0FDF4;      --cat-ahv-text:#166534;      --cat-ahv-border:#BBF7D0;
  --cat-er-bg:#FFF7ED;       --cat-er-text:#C2410C;       --cat-er-border:#FED7AA;
  --cat-acuity-bg:#FFF1F2;   --cat-acuity-text:#BE123C;   --cat-acuity-border:#FECDD3;
  --cat-other-bg:#F8FAFC;    --cat-other-text:#475569;    --cat-other-border:#CBD5E1;
  --savings-text:#065F46; --savings-bg:#D1FAE5;
  --j-k:#7C3AED; --j-v:#0E7490; --j-n:#065F46; --j-null:#94A3B8;
}}
@media (prefers-color-scheme:dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#0D1626; --surface:#152035; --surface2:#1C2B42; --surface3:#243450;
    --border:#263A55; --text:#E2EAF4; --text2:#94AABF; --muted:#566E8A;
    --accent:#4A9EE5; --accent-bg:rgba(74,158,229,0.12);
    --cat-radiology-bg:#1E3A5F; --cat-radiology-text:#93C5FD; --cat-radiology-border:#1E40AF;
    --cat-ahv-bg:#064E3B;      --cat-ahv-text:#6EE7B7;      --cat-ahv-border:#065F46;
    --cat-er-bg:#431407;       --cat-er-text:#FED7AA;       --cat-er-border:#9A3412;
    --cat-acuity-bg:#4C0519;   --cat-acuity-text:#FDA4AF;   --cat-acuity-border:#9F1239;
    --cat-other-bg:#1E293B;    --cat-other-text:#94A3B8;    --cat-other-border:#334155;
    --savings-text:#6EE7B7; --savings-bg:#064E3B;
    --j-k:#C084FC; --j-v:#67E8F9; --j-n:#6EE7B7; --j-null:#566E8A;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#0D1626; --surface:#152035; --surface2:#1C2B42; --surface3:#243450;
  --border:#263A55; --text:#E2EAF4; --text2:#94AABF; --muted:#566E8A;
  --accent:#4A9EE5; --accent-bg:rgba(74,158,229,0.12);
  --cat-radiology-bg:#1E3A5F; --cat-radiology-text:#93C5FD; --cat-radiology-border:#1E40AF;
  --cat-ahv-bg:#064E3B;      --cat-ahv-text:#6EE7B7;      --cat-ahv-border:#065F46;
  --cat-er-bg:#431407;       --cat-er-text:#FED7AA;       --cat-er-border:#9A3412;
  --cat-acuity-bg:#4C0519;   --cat-acuity-text:#FDA4AF;   --cat-acuity-border:#9F1239;
  --cat-other-bg:#1E293B;    --cat-other-text:#94A3B8;    --cat-other-border:#334155;
  --savings-text:#6EE7B7; --savings-bg:#064E3B;
  --j-k:#C084FC; --j-v:#67E8F9; --j-n:#6EE7B7; --j-null:#566E8A;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.5;}}
header{{background:var(--surface);border-bottom:1px solid var(--border);padding:14px 24px;position:sticky;top:0;z-index:20;}}
.header-row1{{display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:10px;margin-bottom:10px;}}
.header-title{{font-size:15px;font-weight:700;}}
.header-sub{{font-size:11.5px;color:var(--muted);margin-top:2px;}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;}}
.chip{{display:inline-flex;align-items:center;gap:5px;border:1px solid var(--border);border-radius:20px;padding:3px 10px;font-size:11.5px;color:var(--text2);background:var(--surface2);font-variant-numeric:tabular-nums;}}
.chip strong{{color:var(--text);font-weight:600;}}
.chip-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0;}}
.toggle{{display:flex;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:3px;gap:2px;}}
.toggle-btn{{padding:5px 13px;border-radius:6px;border:none;background:transparent;color:var(--muted);font-size:12px;font-weight:500;cursor:pointer;transition:all 120ms;white-space:nowrap;}}
.toggle-btn.active{{background:var(--surface);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.12);font-weight:600;}}
.toggle-btn:hover:not(.active){{color:var(--text);}}
main{{padding:20px 24px;}}
.table-wrap{{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;overflow-x:auto;}}
table{{width:100%;border-collapse:collapse;min-width:700px;}}
thead tr{{background:var(--surface2);}}
thead th{{padding:9px 14px;text-align:left;font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--border);white-space:nowrap;}}
thead th:first-child{{padding-left:18px;}}thead th:last-child{{padding-right:18px;}}
tbody tr{{border-bottom:1px solid var(--border);transition:background 100ms;}}
tbody tr:last-child{{border-bottom:none;}}
tbody tr:hover{{background:var(--surface2);}}
td{{padding:10px 14px;vertical-align:middle;font-size:13px;}}
td:first-child{{padding-left:18px;}}td:last-child{{padding-right:18px;}}
.footer{{text-align:center;padding:9px;font-size:11.5px;color:var(--muted);background:var(--surface2);border-top:1px solid var(--border);}}
tbody tr.group-start td:first-child,
tbody tr.group-mid td:first-child,
tbody tr.group-end td:first-child{{border-left:3px solid var(--accent);padding-left:15px;}}
tbody tr.group-mid{{border-bottom:none;}}
.proxy-id{{font-family:var(--mono);font-size:11.5px;color:var(--accent);background:var(--accent-bg);padding:2px 7px;border-radius:4px;white-space:nowrap;display:inline-block;}}
.multi-label{{font-size:11px;color:var(--muted);margin-top:3px;}}
.cat-badge{{display:inline-flex;align-items:center;padding:3px 9px;border-radius:20px;font-size:11.5px;font-weight:500;border:1px solid;white-space:nowrap;}}
.cat-radiology{{background:var(--cat-radiology-bg);color:var(--cat-radiology-text);border-color:var(--cat-radiology-border);}}
.cat-ahv{{background:var(--cat-ahv-bg);color:var(--cat-ahv-text);border-color:var(--cat-ahv-border);}}
.cat-er{{background:var(--cat-er-bg);color:var(--cat-er-text);border-color:var(--cat-er-border);}}
.cat-acuity{{background:var(--cat-acuity-bg);color:var(--cat-acuity-text);border-color:var(--cat-acuity-border);}}
.cat-other{{background:var(--cat-other-bg);color:var(--cat-other-text);border-color:var(--cat-other-border);}}
.ctx-main{{font-weight:500;}}
.ctx-sub{{font-size:11.5px;color:var(--accent);margin-top:2px;opacity:.85;}}
.date-main{{font-variant-numeric:tabular-nums;font-size:12.5px;color:var(--text2);white-space:nowrap;}}
.date-sub{{font-size:11px;color:var(--muted);margin-top:1px;white-space:nowrap;}}
.savings-val{{font-variant-numeric:tabular-nums;font-weight:600;color:var(--savings-text);background:var(--savings-bg);padding:2px 8px;border-radius:4px;font-size:12.5px;}}
.savings-null{{color:var(--muted);}}
.raw-id{{font-family:var(--mono);font-size:11.5px;color:var(--accent);white-space:nowrap;}}
.raw-cell{{max-width:520px;}}
.raw-preview{{font-family:var(--mono);font-size:11.5px;color:var(--text2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:500px;display:block;}}
.expand-btn{{display:inline-flex;align-items:center;gap:4px;margin-top:5px;padding:3px 9px;border:1px solid var(--border);border-radius:5px;background:var(--surface2);color:var(--text2);font-size:11px;font-weight:500;cursor:pointer;transition:all 100ms;}}
.expand-btn:hover{{background:var(--surface3);color:var(--text);}}
.expand-btn svg{{width:12px;height:12px;transition:transform 120ms;flex-shrink:0;}}
.expand-btn.open svg{{transform:rotate(180deg);}}
.json-panel{{display:none;margin-top:8px;background:var(--surface2);border:1px solid var(--border);border-radius:7px;overflow:hidden;}}
.json-panel.open{{display:block;}}
.json-scroll{{overflow-x:auto;padding:12px 14px;}}
.json-scroll pre{{font-family:var(--mono);font-size:11.5px;line-height:1.6;white-space:pre;}}
.jk{{color:var(--j-k);}} .jv{{color:var(--j-v);}} .jn{{color:var(--j-n);}} .jnull{{color:var(--j-null);}}
</style>
</head>
<body>
<header>
  <div class="header-row1">
    <div>
      <div class="header-title">{title_esc} — Profile Dataset</div>
      <div class="header-sub">aetna_dataset_profile_personalized_prompts · {sandbox_esc}</div>
    </div>
    <div class="toggle">
      <button class="toggle-btn active" onclick="setMode('formatted')">Formatted</button>
      <button class="toggle-btn" onclick="setMode('raw')">Raw Data</button>
    </div>
  </div>
  <div class="chips">{chips}</div>
</header>
<main>
  <div id="view-formatted" class="table-wrap">
    <table>
      <thead><tr>
        <th>Proxy ID</th><th>Offer Category</th><th>Context / Trigger</th>
        <th>Start Date</th><th>End Date</th><th>Savings</th>
      </tr></thead>
      <tbody>{"".join(fmt_rows)}</tbody>
    </table>
    <div class="footer">{footer_txt}</div>
  </div>
  <div id="view-raw" class="table-wrap" style="display:none">
    <table>
      <thead><tr><th>#</th><th>Proxy ID</th><th>personlizedVisits</th></tr></thead>
      <tbody>{"".join(raw_rows)}</tbody>
    </table>
    <div class="footer">{footer_txt}</div>
  </div>
</main>
{_PP_JS}
</body>
</html>"""


# ── register ───────────────────────────────────────────────────────────────────
def register(mcp):
    @mcp.tool()
    @track("view_query_results")
    def view_query_results(
        sql: str,
        sandbox: str = "",
        row_limit: int = 500,
        title: str = "",
    ) -> dict:
        """Run a SQL query and return a formatted HTML artifact with the results.

        Executes the query via QS PostgreSQL (same as run_query_sync), then
        generates a self-contained HTML page with a Formatted table view and
        Raw JSON toggle. Writes the page to /tmp/ and returns the file path
        for Claude to read and publish as an artifact.

        Args:
            sql: SQL SELECT statement to execute.
            sandbox: Sandbox name (defaults to active profile sandbox).
            row_limit: Max rows to return (default 500, max 5000).
            title: Optional display title for the artifact (auto-generated from SQL if omitted).
        """
        try:
            import psycopg2
            from auth import aep_get, get_active_sandbox

            effective_sandbox = sandbox or get_active_sandbox()

            cp = aep_get(
                "/data/foundation/query/connection_parameters",
                sandbox=effective_sandbox,
            )

            conn = psycopg2.connect(
                host=cp["host"],
                port=cp["port"],
                dbname=cp["dbName"],
                user=cp["username"],
                password=cp["token"],
                sslmode="require",
                connect_timeout=30,
            )
            try:
                cur = conn.cursor()
                cur.execute(sql)
                cols = [d[0] for d in cur.description] if cur.description else []
                limit = min(max(1, row_limit), 5000)
                raw_rows = cur.fetchmany(limit)
                rows = [
                    {c: _sanitize(v) for c, v in zip(cols, row)}
                    for row in raw_rows
                ]
                cur.close()
            finally:
                conn.close()

            # derive title from SQL if not provided
            if not title:
                first_line = sql.strip().splitlines()[0][:80]
                title = first_line if len(first_line) > 5 else "Query Results"

            html_out = _generate_html(sql, cols, rows, effective_sandbox, title)

            slug = title[:40].replace(" ", "-").replace("/", "-").lower()
            ts_slug = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
            html_path = f"/tmp/aep-query-{slug}-{ts_slug}.html"
            with open(html_path, "w", encoding="utf-8") as fh:
                fh.write(html_out)

            text = _text_summary(sql, cols, rows, effective_sandbox, title)

            return {
                "text_summary": text,
                "html_file": html_path,
                "row_count": len(rows),
                "columns": cols,
                "instruction": (
                    f"Display the text_summary in your response. "
                    f"Then read {html_path} and publish it as an artifact "
                    f"titled '{title}'."
                ),
            }
        except Exception as exc:
            return {"error": str(exc)}

    @mcp.tool()
    @track("view_personalized_prompts")
    def view_personalized_prompts(
        sandbox: str = "",
        limit: int = 20,
    ) -> dict:
        """Fetch and display Aetna personalized prompts with rich category cards.

        Queries aetna_dataset_profile_personalized_prompts via QS PostgreSQL,
        parses the composite visit tuples (cohort, prompt, dates, savings, PCP
        info, claim IDs), and renders a schema-aware HTML artifact with:
        - Category color badges (Radiology, AHV, ER Avoidance, Low Acuity)
        - Per-visit rows grouped by member with left-border accent
        - Projected savings highlighted in green
        - Context sub-lines (PCP name, claim ID, ER date)
        - Raw JSON expand panels per member
        - Formatted / Raw Data toggle

        Args:
            sandbox: Sandbox name (defaults to active profile sandbox).
            limit: Max members to return (default 20, max 500).
        """
        try:
            import psycopg2
            from auth import aep_get, get_active_sandbox

            effective_sandbox = sandbox or get_active_sandbox()
            cp = aep_get(
                "/data/foundation/query/connection_parameters",
                sandbox=effective_sandbox,
            )
            conn = psycopg2.connect(
                host=cp["host"], port=cp["port"], dbname=cp["dbName"],
                user=cp["username"], password=cp["token"],
                sslmode="require", connect_timeout=30,
            )
            try:
                cur = conn.cursor()
                n = min(max(1, limit), 500)
                cur.execute(
                    f"SELECT _cvs.aetnaProxyId as proxy_id, "
                    f"CAST(_cvs.personlizedVisits AS TEXT) as visits "
                    f"FROM aetna_dataset_profile_personalized_prompts LIMIT {n}"
                )
                raw_rows = cur.fetchall()
                cur.close()
            finally:
                conn.close()

            members = []
            for row in raw_rows:
                proxy_id = str(row[0]) if row[0] else ""
                visits_str = str(row[1]) if row[1] else ""
                visits = _pp_parse_visits(visits_str)
                members.append({"proxy_id": proxy_id, "visits": visits})

            title = "Personalized Prompts"
            html_out = _generate_prompts_html(members, effective_sandbox, title)
            ts_slug = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
            html_path = f"/tmp/aep-prompts-{ts_slug}.html"
            with open(html_path, "w", encoding="utf-8") as fh:
                fh.write(html_out)

            total_offers = sum(len(m["visits"]) for m in members)
            text_lines = [
                f"**{title}** — {len(members)} members, {total_offers} offer assignments in `{effective_sandbox}`",
                "",
            ]
            for m in members[:5]:
                cats = set(_pp_category(v.get("cohort_name",""), v.get("prompt_name","")) for v in m["visits"])
                cat_labels = ", ".join(_PP_CATS[c]["label"] for c in cats if c in _PP_CATS)
                text_lines.append(f"- **{m['proxy_id']}** — {len(m['visits'])} offer(s): {cat_labels}")
            if len(members) > 5:
                text_lines.append(f"_… and {len(members) - 5} more members_")

            return {
                "text_summary": "\n".join(text_lines),
                "html_file": html_path,
                "member_count": len(members),
                "total_offers": total_offers,
                "instruction": (
                    f"Display the text_summary in your response. "
                    f"Then read {html_path} and publish it as an artifact "
                    f"titled '{title}'."
                ),
            }
        except Exception as exc:
            return {"error": str(exc)}

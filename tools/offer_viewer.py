"""
AJO Offer Viewer — fetch and display personalized offers for a member.

Returns a markdown text_summary for chat display and a formatted HTML artifact.
"""

import base64
import html as _html
import json
from datetime import datetime, timezone

from auth import aep_get, aep_post, get_active_sandbox
from tools.ajo import _extract_placements
from tools.schema_context import extract_prompt_text
from tools.usage_logger import track

_ODS = "/data/core/ods"
_DPS = "/data/core/dps"

# ── CSS ─────────────────────────────────────────────────────────────────────

_CSS = """
:root {
  --ground: #F2F6FB;
  --surface: #FFFFFF;
  --surface-raised: #EDF3FA;
  --accent: #1C5FA8;
  --accent-dim: rgba(28,95,168,0.10);
  --accent-border: #A5C0E0;
  --text: #0F1B2D;
  --text-muted: #5C738A;
  --border: #C8D8EC;
  --tag-en-bg: #D7F1E0;
  --tag-en-fg: #155A2E;
  --tag-es-bg: #FDECD4;
  --tag-es-fg: #7B3A00;
  --tag-other-bg: #E8EAFF;
  --tag-other-fg: #2D3EB8;
  --content-bg: #F5F9FF;
  --content-border: #C0D6EE;
  --json-key: #155AB0;
  --json-str: #1A7A42;
  --json-num: #B05A00;
  --topbar-bg: #1C5FA8;
  --topbar-text: #FFFFFF;
  --topbar-muted: #A8C6E8;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #0C1420;
    --surface: #111D2D;
    --surface-raised: #162538;
    --accent: #5591D0;
    --accent-dim: rgba(85,145,208,0.12);
    --accent-border: #2A4A70;
    --text: #D8E8F8;
    --text-muted: #6A8AAA;
    --border: #1E3352;
    --tag-en-bg: #0D3A20;
    --tag-en-fg: #72D99A;
    --tag-es-bg: #3A2000;
    --tag-es-fg: #E8A050;
    --tag-other-bg: #1A1E50;
    --tag-other-fg: #9AA8FF;
    --content-bg: #0E1A2C;
    --content-border: #1C3352;
    --json-key: #72AAEE;
    --json-str: #72D99A;
    --json-num: #E8A050;
    --topbar-bg: #0E2A50;
    --topbar-text: #D8E8F8;
    --topbar-muted: #5A80A8;
  }
}
:root[data-theme="dark"] {
  --ground: #0C1420;
  --surface: #111D2D;
  --surface-raised: #162538;
  --accent: #5591D0;
  --accent-dim: rgba(85,145,208,0.12);
  --accent-border: #2A4A70;
  --text: #D8E8F8;
  --text-muted: #6A8AAA;
  --border: #1E3352;
  --tag-en-bg: #0D3A20;
  --tag-en-fg: #72D99A;
  --tag-es-bg: #3A2000;
  --tag-es-fg: #E8A050;
  --tag-other-bg: #1A1E50;
  --tag-other-fg: #9AA8FF;
  --content-bg: #0E1A2C;
  --content-border: #1C3352;
  --json-key: #72AAEE;
  --json-str: #72D99A;
  --json-num: #E8A050;
  --topbar-bg: #0E2A50;
  --topbar-text: #D8E8F8;
  --topbar-muted: #5A80A8;
}

*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  background: var(--ground);
  color: var(--text);
  font-size: 14px;
  line-height: 1.5;
}

/* ── Topbar ── */
.topbar {
  position: sticky; top: 0; z-index: 100;
  background: var(--topbar-bg);
  color: var(--topbar-text);
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 50px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.22);
}
.topbar-title {
  font-weight: 700;
  font-size: 15px;
  letter-spacing: .01em;
  white-space: nowrap;
}
.topbar-chip {
  background: rgba(255,255,255,0.15);
  border-radius: 20px;
  padding: 3px 12px;
  font-size: 12px;
  color: var(--topbar-muted);
  font-family: "SF Mono", "Consolas", monospace;
  white-space: nowrap;
}
.topbar-spacer { flex: 1; }
.topbar-meta {
  font-size: 12px;
  color: var(--topbar-muted);
  white-space: nowrap;
  margin-right: 8px;
}
.view-toggle {
  display: flex;
  background: rgba(255,255,255,0.12);
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}
.view-toggle button {
  border: none;
  background: transparent;
  color: var(--topbar-muted);
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
  transition: background .15s, color .15s;
}
.view-toggle button.active {
  background: rgba(255,255,255,0.25);
  color: var(--topbar-text);
  font-weight: 600;
}

/* ── Main ── */
.main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}
.section-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 14px;
}

/* ── Grid ── */
.offers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(460px, 1fr));
  gap: 18px;
}

/* ── Offer card ── */
.offer-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
}
.card-header {
  background: var(--accent);
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.card-idx {
  color: rgba(255,255,255,0.6);
  font-size: 11px;
  font-family: "SF Mono", "Consolas", monospace;
  font-weight: 700;
  flex-shrink: 0;
}
.card-id-pills {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  flex: 1;
  min-width: 0;
}
.card-id-pill {
  background: rgba(255,255,255,0.14);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  font-family: "SF Mono", "Consolas", monospace;
  color: rgba(255,255,255,0.88);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 210px;
}
.card-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.tag-lang {
  border-radius: 20px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.tag-en  { background: var(--tag-en-bg);    color: var(--tag-en-fg); }
.tag-es  { background: var(--tag-es-bg);    color: var(--tag-es-fg); }
.tag-oth { background: var(--tag-other-bg); color: var(--tag-other-fg); }
.btn-expand {
  background: rgba(255,255,255,0.14);
  border: none;
  border-radius: 4px;
  color: rgba(255,255,255,0.8);
  font-size: 11px;
  font-family: "SF Mono", "Consolas", monospace;
  padding: 3px 9px;
  cursor: pointer;
  transition: background .15s;
  flex-shrink: 0;
}
.btn-expand:hover { background: rgba(255,255,255,0.26); }

/* ── Card body ── */
.card-body {
  padding: 16px;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.offer-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
  line-height: 1.3;
}
.offer-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.meta-tag {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: "SF Mono", "Consolas", monospace;
}
.score-badge {
  background: var(--accent-dim);
  border: 1px solid var(--accent-border);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--accent);
  font-weight: 600;
}

/* ── Content box ── */
.content-box {
  background: var(--content-bg);
  border: 1px solid var(--content-border);
  border-radius: 7px;
  padding: 13px 14px;
  flex: 1;
}
.content-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.content-text {
  font-size: 13.5px;
  line-height: 1.65;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-word;
}
.content-html-code {
  font-size: 12px;
  font-family: "SF Mono", "Consolas", monospace;
  line-height: 1.55;
  color: var(--text-muted);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 180px;
  overflow-y: auto;
}
.content-empty {
  color: var(--text-muted);
  font-style: italic;
  font-size: 13px;
}

/* ── IDs row ── */
.ids-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.ids-row-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  font-size: 11px;
  font-family: "SF Mono", "Consolas", monospace;
}
.ids-key { color: var(--accent); flex-shrink: 0; }
.ids-val { color: var(--text-muted); word-break: break-all; }

/* ── JSON expand panel ── */
.json-panel {
  display: none;
  background: var(--surface-raised);
  border-top: 1px solid var(--border);
  padding: 12px 16px;
  font-size: 11.5px;
  font-family: "SF Mono", "Consolas", monospace;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
  overflow-x: auto;
  max-height: 380px;
  overflow-y: auto;
}
.json-key  { color: var(--json-key); }
.json-str  { color: var(--json-str); }
.json-num  { color: var(--json-num); }
.json-bool { color: var(--json-num); }
.json-null { color: var(--text-muted); }

/* ── Raw JSON view ── */
#view-raw {
  display: none;
  padding: 20px;
  max-width: 1100px;
  margin: 0 auto;
}
.raw-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.raw-title { font-weight: 600; font-size: 14px; }
.btn-copy {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
}
.raw-block {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
}
.raw-block pre {
  margin: 0;
  font-size: 12px;
  font-family: "SF Mono", "Consolas", monospace;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
  color: var(--text);
}

/* ── Offer type badges ── */
.badge-type {
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .05em;
  text-transform: uppercase;
}
.badge-selected { background: #D7F1E0; color: #155A2E; }
.badge-eligible  { background: rgba(255,255,255,0.18); color: rgba(255,255,255,0.92); border: 1px solid rgba(255,255,255,0.25); }
.badge-fallback  { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.5); }

/* Fallback cards are more muted */
.card-header.header-fallback { background: var(--text-muted); }

/* ── Activity/placement label ── */
.act-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 2px;
}
.plc-label {
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}

/* ── Characteristics pills ── */
.char-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.char-pill {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: "SF Mono", "Consolas", monospace;
}
.char-key { color: var(--accent); }

/* ── Section divider ── */
.section-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 32px 0 16px;
}
.section-divider-line {
  flex: 1;
  height: 1px;
  background: var(--border);
}
.section-divider-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--text-muted);
  white-space: nowrap;
}

/* ── Empty state ── */
.empty-state {
  text-align: center;
  padding: 64px 20px;
  color: var(--text-muted);
}
.empty-icon { font-size: 40px; margin-bottom: 16px; }
.empty-title { font-size: 18px; font-weight: 600; color: var(--text); margin-bottom: 8px; }

/* ── Responsive ── */
@media (max-width: 600px) {
  .offers-grid { grid-template-columns: 1fr; }
  .topbar { padding: 0 12px; gap: 6px; }
  .topbar-title { font-size: 13px; }
  .topbar-chip { display: none; }
}
"""

_JS = r"""
function highlight(code) {
  return code
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"([^"\\]*(\\.[^"\\]*)*)"(\s*):/g,'<span class="json-key">"$1"</span>$3:')
    .replace(/:\s*"([^"\\]*(\\.[^"\\]*)*)"/g,': <span class="json-str">"$1"</span>')
    .replace(/:\s*(-?\d+\.?\d*)/g,': <span class="json-num">$1</span>')
    .replace(/:\s*(true|false)/g,': <span class="json-bool">$1</span>')
    .replace(/:\s*(null)/g,': <span class="json-null">null</span>');
}

function toggleJson(panelId, btn) {
  var p = document.getElementById(panelId);
  if (!p) return;
  var open = p.style.display === 'block';
  p.style.display = open ? 'none' : 'block';
  btn.textContent = open ? '{ }' : '{ \u2026 }';
  if (!open && !p.dataset.hl) {
    p.innerHTML = highlight(p.textContent);
    p.dataset.hl = '1';
  }
}

function setView(v) {
  document.getElementById('view-formatted').style.display = v === 'formatted' ? 'block' : 'none';
  document.getElementById('view-raw').style.display = v === 'raw' ? 'block' : 'none';
  document.querySelectorAll('.view-toggle button').forEach(function(b) {
    b.classList.toggle('active', b.dataset.view === v);
  });
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[data-json]').forEach(function(el) {
    el.innerHTML = highlight(el.textContent);
  });
});

function copyRaw() {
  var el = document.getElementById('raw-json');
  if (!el) return;
  navigator.clipboard.writeText(el.textContent).then(function() {
    var btn = document.getElementById('copy-btn');
    btn.textContent = 'Copied!';
    setTimeout(function(){ btn.textContent = 'Copy'; }, 2000);
  });
}
"""


# ── Helpers ─────────────────────────────────────────────────────────────────

def _short_id(full_id: str) -> str:
    """Return the trailing segment after the last colon."""
    return full_id.split(":")[-1] if ":" in full_id else full_id


def _lang_badge(lang: str) -> str:
    if not lang:
        return ""
    if lang.lower() == "en":
        cls = "tag-lang tag-en"
    elif lang.lower() == "es":
        cls = "tag-lang tag-es"
    else:
        cls = "tag-lang tag-oth"
    return f'<span class="{cls}">{_html.escape(lang)}</span>'


def _parse_propositions(response_data: dict) -> list:
    """Flatten xdm:propositions into a list of offer dicts.

    ODS can return offers in three locations:
      xdm:items   — the winning/selected offer (post-ranking)
      xdm:options — all eligible candidates evaluated (some sandboxes return this
                    instead of xdm:items when include_content=True)
      xdm:fallback — the fallback used when no personalized offer matched

    Content fields may be at item level (dc:format / dc:language / xdm:content)
    or nested inside xdm:data (xdm:format / xdm:language / xdm:content).
    """
    offers = []
    for prop in response_data.get("xdm:propositions", []):
        activity  = prop.get("xdm:activity",  {})
        placement = prop.get("xdm:placement", {})
        activity_id    = activity.get("xdm:id", "")
        activity_name  = activity.get("xdm:name", "")
        placement_id   = placement.get("xdm:id", "")
        placement_name = placement.get("xdm:name", "")

        def _parse_item(item: dict, offer_type: str) -> dict:
            # Content can be nested in xdm:data OR directly on item (dc:* fields)
            data = item.get("xdm:data", {})
            lang_list = (
                data.get("xdm:language")
                or item.get("dc:language")
                or item.get("xdm:language")
                or []
            )
            fmt = data.get("xdm:format") or item.get("dc:format") or ""
            content = data.get("xdm:content") or item.get("xdm:content") or ""
            # Pretty-print JSON content so it renders readably in the card
            if fmt and "json" in fmt and content:
                try:
                    content = json.dumps(json.loads(content), indent=2, ensure_ascii=False)
                except Exception:
                    pass
            return {
                "activity_id":     activity_id,
                "activity_name":   activity_name,
                "placement_id":    placement_id,
                "placement_name":  placement_name,
                "offer_id":        item.get("xdm:id", ""),
                "name":            item.get("xdm:name", ""),
                "score":           item.get("xdm:score"),
                "priority":        item.get("xdm:priority"),
                "format":          fmt,
                "content":         content,
                "language":        lang_list[0] if lang_list else "",
                "offer_type":      offer_type,
                "characteristics": item.get("xdm:characteristics", {}),
                "raw":             item,
            }

        # 1. Winning/selected offers
        for item in prop.get("xdm:items", []):
            offers.append(_parse_item(item, "selected"))

        # 2. Eligible candidate offers (used when no single winner is surfaced)
        for item in prop.get("xdm:options", []):
            offers.append(_parse_item(item, "eligible"))

        # 3. Fallback — only when no personalized offer was returned
        if not prop.get("xdm:items") and not prop.get("xdm:options"):
            fallback = prop.get("xdm:fallback")
            if fallback:
                offers.append(_parse_item(fallback, "fallback"))

    # Sort: selected first, eligible second, fallback last
    order = {"selected": 0, "eligible": 1, "fallback": 2}
    offers.sort(key=lambda o: order.get(o["offer_type"], 3))
    return offers


def _content_preview(content: str, characteristics: dict) -> str:
    """Return a one-line human-readable preview of offer content for chat display."""
    # Prefer characteristic fields — discover key name dynamically at runtime
    pt = extract_prompt_text(characteristics)
    if pt and len(pt) > 5:
        return pt[:160] + ("…" if len(pt) > 160 else "")
    # Try to extract first meaningful string from JSON
    if content.strip().startswith("{"):
        try:
            parsed = json.loads(content)
            def _first_str(obj, depth=0):
                if isinstance(obj, str) and len(obj) > 10 and " " in obj:
                    return obj
                if isinstance(obj, dict) and depth < 4:
                    for v in obj.values():
                        r = _first_str(v, depth + 1)
                        if r:
                            return r
                if isinstance(obj, list) and depth < 4:
                    for v in obj:
                        r = _first_str(v, depth + 1)
                        if r:
                            return r
                return None
            found = _first_str(parsed)
            if found:
                return found[:160] + ("…" if len(found) > 160 else "")
        except Exception:
            pass
    # Fallback to plain text (non-JSON content)
    if not content.strip().startswith("{"):
        return content[:160] + ("…" if len(content) > 160 else "")
    return ""


def _text_summary(identity_id: str, identity_namespace: str, offers: list, sandbox: str) -> str:
    """Generate a markdown text summary suitable for display in chat."""
    personalized = [o for o in offers if o["offer_type"] in ("selected", "eligible")]
    fallbacks    = [o for o in offers if o["offer_type"] == "fallback"]

    p_count = len(personalized)
    f_count = len(fallbacks)
    lines = [
        f"**Offers for {identity_id}** ({identity_namespace}) in `{sandbox}` — "
        f"{p_count} personalized offer{'s' if p_count != 1 else ''}"
        + (f", {f_count} fallback{'s' if f_count != 1 else ''}" if f_count else "")
        + ":\n"
    ]
    for i, o in enumerate(personalized, 1):
        name    = o["name"] or o["offer_id"] or "Unnamed Offer"
        lang    = f" [{o['language']}]" if o["language"] else ""
        act_nm  = o.get("activity_name") or _short_id(o["activity_id"])
        type_lbl = "✓" if o["offer_type"] == "selected" else "·"
        lines.append(f"{i}. {type_lbl} **{name}**{lang}")
        lines.append(f"   Activity: {act_nm}")
        if o["content"]:
            preview = _content_preview(o["content"], o.get("characteristics", {}))
            if preview:
                lines.append(f"   > {preview}")
        lines.append("")
    if fallbacks:
        f_activities = ", ".join(
            f.get("activity_name") or _short_id(f["activity_id"])
            for f in fallbacks
        )
        lines.append(f"*Fallback ({f_count}): {f_activities}*")
    if not offers:
        lines.append("No offers were returned for this member.")
    return "\n".join(lines)


def _offer_card(idx: int, offer: dict) -> str:
    """Build HTML for a single offer card."""
    panel_id   = f"json-offer-{idx}"
    offer_type = offer.get("offer_type", "eligible")
    name       = _html.escape(offer["name"] or offer["offer_id"] or "Offer")
    fmt        = offer.get("format", "")
    content    = offer.get("content", "")
    score      = offer.get("score")
    act_name   = _html.escape(offer.get("activity_name") or _short_id(offer["activity_id"]))
    plc_name   = _html.escape(offer.get("placement_name") or _short_id(offer["placement_id"]))
    chars      = offer.get("characteristics", {})

    # Header colour varies by offer type
    hdr_class = "card-header" + (" header-fallback" if offer_type == "fallback" else "")

    # Type badge
    type_label = {"selected": "Selected", "eligible": "Eligible", "fallback": "Fallback"}.get(offer_type, offer_type)
    type_badge = f'<span class="badge-type badge-{offer_type}">{type_label}</span>'

    # Content area
    if content:
        is_json = fmt and "json" in fmt
        if fmt == "text/html":
            label = "HTML Content (source)"
            inner_body = f'<div class="content-html-code">{_html.escape(content)}</div>'
        elif is_json:
            label = "Content (JSON)"
            inner_body = f'<div class="content-html-code" data-json="1">{_html.escape(content)}</div>'
        else:
            label = "Content"
            inner_body = f'<div class="content-text">{_html.escape(content)}</div>'
        content_inner = f'<div class="content-label">{label}</div>{inner_body}'
    else:
        content_inner = '<span class="content-empty">No content representation included</span>'

    score_html = f'<span class="score-badge">Score: {score}</span>' if score is not None else ""
    fmt_short  = fmt.split("/")[-1] if fmt else ""
    fmt_html   = f'<span class="meta-tag">{_html.escape(fmt_short)}</span>' if fmt_short else ""

    # Characteristics pills
    char_pills = ""
    if chars:
        pills = "".join(
            f'<span class="char-pill"><span class="char-key">{_html.escape(k)}</span>: {_html.escape(str(v))}</span>'
            for k, v in chars.items()
        )
        char_pills = f'<div class="char-row">{pills}</div>'

    raw_json = _html.escape(json.dumps(offer["raw"], indent=2, ensure_ascii=False))

    return f"""<div class="offer-card">
  <div class="{hdr_class}">
    <span class="card-idx">#{idx + 1}</span>
    <div class="card-id-pills" style="flex:1;min-width:0">
      <span class="card-id-pill" title="{_html.escape(offer['activity_id'])}">{act_name}</span>
    </div>
    <div class="card-actions">
      {type_badge}
      {_lang_badge(offer['language'])}
      <button class="btn-expand" onclick="toggleJson('{panel_id}',this)">{{ }}</button>
    </div>
  </div>
  <div class="card-body">
    <h2 class="offer-name">{name}</h2>
    <div class="act-label">Placement: {plc_name}</div>
    <div class="offer-meta">{fmt_html}{score_html}</div>
    <div class="content-box">{content_inner}</div>
    {char_pills}
    <div class="ids-row">
      <div class="ids-row-item"><span class="ids-key">offer</span><span class="ids-val">{_html.escape(offer['offer_id'])}</span></div>
      <div class="ids-row-item"><span class="ids-key">activity</span><span class="ids-val">{_html.escape(offer['activity_id'])}</span></div>
      <div class="ids-row-item"><span class="ids-key">placement</span><span class="ids-val">{_html.escape(offer['placement_id'])}</span></div>
    </div>
  </div>
  <div class="json-panel" id="{panel_id}">{raw_json}</div>
</div>"""


def _build_html(
    identity_id: str,
    identity_namespace: str,
    offers: list,
    raw_json: str,
    sandbox: str,
    merge_policy_id: str = "",
    context_language: str = "",
) -> str:
    """Build the full HTML artifact."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    count   = len(offers)

    personalized = [o for o in offers if o.get("offer_type") in ("selected", "eligible")]
    fallbacks    = [o for o in offers if o.get("offer_type") == "fallback"]

    if offers:
        sections = []
        if personalized:
            p_label = f"{len(personalized)} personalized offer{'s' if len(personalized) != 1 else ''}"
            p_cards = "\n".join(_offer_card(i, o) for i, o in enumerate(personalized))
            sections.append(
                f'<div class="section-label">{p_label}</div>\n'
                f'<div class="offers-grid">\n{p_cards}\n</div>'
            )
        if fallbacks:
            f_label = f"{len(fallbacks)} fallback offer{'s' if len(fallbacks) != 1 else ''} (no personalized match)"
            f_start = len(personalized)
            f_cards = "\n".join(_offer_card(f_start + i, o) for i, o in enumerate(fallbacks))
            sections.append(
                f'<div class="section-divider">'
                f'<div class="section-divider-line"></div>'
                f'<span class="section-divider-label">{f_label}</span>'
                f'<div class="section-divider-line"></div></div>\n'
                f'<div class="offers-grid">\n{f_cards}\n</div>'
            )
        body = "\n".join(sections)
    else:
        body = """<div class="empty-state">
  <div class="empty-icon">🎯</div>
  <div class="empty-title">No Offers Returned</div>
  <p>No eligible offers were found for this member. Check eligibility rules,<br>offer status (must be live/approved), context data, and merge policy.</p>
</div>"""

    # Build context chips
    chips = [
        f'<span class="topbar-chip">{_html.escape(identity_id)}</span>',
        f'<span class="topbar-chip">{_html.escape(identity_namespace)}</span>',
        f'<span class="topbar-chip">{_html.escape(sandbox)}</span>',
    ]
    if context_language:
        chips.append(f'<span class="topbar-chip">lang:{_html.escape(context_language)}</span>')
    if merge_policy_id:
        short_mp = merge_policy_id[:8]
        chips.append(f'<span class="topbar-chip" title="{_html.escape(merge_policy_id)}">mp:{_html.escape(short_mp)}…</span>')

    chips_html = "\n  ".join(chips)
    raw_escaped = _html.escape(raw_json)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AJO Offers — {_html.escape(identity_id)}</title>
<style>{_CSS}</style>
</head>
<body>

<div class="topbar">
  <span class="topbar-title">AJO Offers</span>
  {chips_html}
  <div class="topbar-spacer"></div>
  <span class="topbar-meta">{len(personalized)} personalized · {len(fallbacks)} fallback · {now_str}</span>
  <div class="view-toggle">
    <button class="active" data-view="formatted" onclick="setView('formatted')">Formatted</button>
    <button data-view="raw" onclick="setView('raw')">Raw JSON</button>
  </div>
</div>

<div id="view-formatted">
  <div class="main">{body}</div>
</div>

<div id="view-raw">
  <div class="raw-toolbar">
    <span class="raw-title">Raw Response JSON</span>
    <button class="btn-copy" id="copy-btn" onclick="copyRaw()">Copy</button>
  </div>
  <div class="raw-block"><pre id="raw-json">{raw_escaped}</pre></div>
</div>

<script>{_JS}</script>
</body>
</html>"""


# ── Tool registration ────────────────────────────────────────────────────────

def register(mcp) -> None:

    @mcp.tool()
    @track("view_offers")
    def view_offers(
        identity_id: str,
        identity_namespace: str,
        activity_ids: str = "",
        decision_scopes: str = "",
        merge_policy_id: str = "",
        context_language: str = "",
        context_data: str = "",
        sandbox: str = "",
    ) -> dict:
        """Fetch AJO offers for a member and return a text summary plus formatted HTML.

        Evaluates offer eligibility and ranking for the member via the ODS Decisions
        API, then returns both a markdown text_summary (for chat display) and a
        formatted HTML artifact with offer cards showing content, placement, and
        expandable JSON panels.

        Provide activity_ids to evaluate specific activities; omit to evaluate all
        live activities in the sandbox. Pass decision_scopes (Base64) as an alternative.

        Args:
            identity_id: Member identity value (e.g. "9066FGBBBPXY").
            identity_namespace: Namespace code (e.g. "ProxyID", "Email").
            activity_ids: Comma-separated offer activity IDs. Placements are resolved
                automatically from each activity object.
            decision_scopes: Comma-separated Base64-encoded decision scopes
                (takes priority over activity_ids when both are supplied).
            merge_policy_id: Merge policy UUID for profile resolution
                (e.g. "7dc5b130-0bea-4ba1-a506-21cb48ff2240" for Aetna dev Edge).
                Uses sandbox default when omitted.
            context_language: Language code injected into eligibility context
                (e.g. "en", "es"). Required for language-gated eligibility rules.
            context_data: JSON object of additional context key-value pairs
                (e.g. '{"xdm:channel":"web"}').
            sandbox: Sandbox name (defaults to active org profile sandbox).
        """
        _CT = (
            'application/vnd.adobe.xdm+json; schema='
            '"https://ns.adobe.com/experience/offer-management/decision-request;version=1.0"'
        )
        _ACCEPT = (
            'application/vnd.adobe.xdm+json; schema='
            '"https://ns.adobe.com/experience/offer-management/decision-response;version=1.0"'
        )

        try:
            effective_sandbox = sandbox or get_active_sandbox()

            # ── Build xdm:propositionRequests ────────────────────────────────
            prop_requests: list = []

            if decision_scopes:
                for scope in [s.strip() for s in decision_scopes.split(",") if s.strip()]:
                    try:
                        decoded = json.loads(base64.b64decode(scope).decode())
                        entry: dict = {"xdm:activityId": decoded.get("activityId", scope)}
                        if decoded.get("placementId"):
                            entry["xdm:placementId"] = decoded["placementId"]
                        prop_requests.append(entry)
                    except Exception:
                        prop_requests.append({"xdm:activityId": scope})

            elif activity_ids:
                acts_resp = aep_get(
                    f"{_DPS}/offer-decisions",
                    sandbox=sandbox or None,
                    params={"limit": 100},
                )
                all_acts = (
                    acts_resp.get("results")
                    or acts_resp.get("items")
                    or acts_resp.get("_embedded", {}).get("decisions", [])
                    or []
                )
                act_map = {
                    a.get("id") or a.get("@id") or a.get("xdm:id", ""): a
                    for a in all_acts
                }
                for act_id in [a.strip() for a in activity_ids.split(",") if a.strip()]:
                    act = act_map.get(act_id, {})
                    placements = _extract_placements(act)
                    if placements:
                        for pid in placements:
                            prop_requests.append(
                                {"xdm:activityId": act_id, "xdm:placementId": pid}
                            )
                    else:
                        prop_requests.append({"xdm:activityId": act_id})

            else:
                resp = aep_get(
                    f"{_DPS}/offer-decisions",
                    sandbox=sandbox or None,
                    params={"limit": 100},
                )
                activities = (
                    resp.get("items")
                    or resp.get("results")
                    or resp.get("_embedded", {}).get("decisions", [])
                    or []
                )
                now = datetime.now(timezone.utc)
                for act in activities:
                    act_id = act.get("id") or act.get("@id") or act.get("xdm:id", "")
                    if not act_id:
                        continue
                    if act.get("status") != "live":
                        continue
                    end = act.get("endDate")
                    if end:
                        try:
                            if datetime.fromisoformat(end.replace("Z", "+00:00")) < now:
                                continue
                        except Exception:
                            pass
                    placements = _extract_placements(act)
                    if placements:
                        for pid in placements:
                            prop_requests.append(
                                {"xdm:activityId": act_id, "xdm:placementId": pid}
                            )
                    else:
                        prop_requests.append({"xdm:activityId": act_id})

            if not prop_requests:
                return {
                    "error": (
                        "No offer activities resolved. Provide activity_ids or "
                        "decision_scopes, or ensure active offer activities exist."
                    )
                }

            # ── Build profile context ────────────────────────────────────────
            ctx_data: dict = {}
            if context_language:
                ctx_data["xdm:language"] = context_language
            if context_data:
                try:
                    ctx_data.update(json.loads(context_data))
                except json.JSONDecodeError as exc:
                    return {"error": f"Invalid context_data JSON: {exc}"}

            profile: dict = {
                "xdm:identityMap": {
                    identity_namespace: [{"xdm:id": identity_id, "primary": True}]
                }
            }
            if ctx_data:
                profile["xdm:contextData"] = [
                    {
                        "@type": "_xdm.context.additionalParameters;version=1",
                        "xdm:data": ctx_data,
                    }
                ]

            # ── Assemble and send ODS request ────────────────────────────────
            body: dict = {
                "xdm:propositionRequests": prop_requests,
                "xdm:profiles": [profile],
                "xdm:allowDuplicatePropositions": {
                    "xdm:acrossActivities": True,
                    "xdm:acrossPlacements": True,
                },
                "xdm:responseFormat": {"xdm:includeContent": True},
            }
            if merge_policy_id:
                body["xdm:mergePolicy"] = {"xdm:id": merge_policy_id}

            raw_response = aep_post(
                f"{_ODS}/decisions",
                body,
                sandbox=sandbox or None,
                content_type=_CT,
                accept=_ACCEPT,
            )

            # ── Parse and render ─────────────────────────────────────────────
            offers   = _parse_propositions(raw_response)
            raw_json = json.dumps(raw_response, indent=2, ensure_ascii=False)
            text     = _text_summary(identity_id, identity_namespace, offers, effective_sandbox)
            html_out = _build_html(
                identity_id,
                identity_namespace,
                offers,
                raw_json,
                effective_sandbox,
                merge_policy_id=merge_policy_id,
                context_language=context_language,
            )

            # Write HTML to a file so the MCP response stays small enough
            # for Claude's context window — Claude reads and publishes from path.
            html_path = f"/tmp/aep-offers-{identity_id}.html"
            with open(html_path, "w", encoding="utf-8") as _fh:
                _fh.write(html_out)

            personalized = [o for o in offers if o.get("offer_type") in ("selected", "eligible")]
            fallbacks    = [o for o in offers if o.get("offer_type") == "fallback"]

            return {
                "text_summary": text,
                "html_file": html_path,
                "offer_count": len(offers),
                "personalized_count": len(personalized),
                "fallback_count": len(fallbacks),
                "instruction": (
                    f"Display the text_summary in your response. "
                    f"Then read {html_path} and publish it as an artifact "
                    f"titled 'AJO Offers — {identity_id}'."
                ),
            }

        except Exception as exc:
            return {"error": str(exc)}

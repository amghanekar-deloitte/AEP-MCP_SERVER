#!/usr/bin/env python3
"""Mermaid ERD generation from CSV file structure and profile data.

Usage: python generate_erd.py <input_dir> [output_dir]
  input_dir  — directory containing CSV files
  output_dir — where to write ERD (default: {input_dir}/output)
               Reads profiles from {output_dir}/profiles/all_profiles.json if available

Output: {output_dir}/erd_data_model.md — Mermaid erDiagram in a markdown file

Standard library only — no third-party dependencies.
"""

import csv
import json
import os
import sys
from pathlib import Path


# Map inferred types to XDM-style types for ERD display
TYPE_MAP = {
    "uuid": "string",
    "email": "string",
    "int": "int",
    "float": "number",
    "date": "date",
    "datetime": "datetime",
    "boolean": "boolean",
    "string": "string",
}


def _entity_name(filename: str) -> str:
    """Convert filename to UPPER_SNAKE_CASE entity name."""
    stem = Path(filename).stem
    # Replace hyphens/spaces with underscores, uppercase
    return stem.replace("-", "_").replace(" ", "_").upper()


def _load_profiles(output_dir: Path) -> dict:
    """Load all_profiles.json if available."""
    profiles_path = output_dir / "profiles" / "all_profiles.json"
    if profiles_path.exists():
        with open(profiles_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _read_csv_headers(input_dir: Path) -> dict:
    """Read CSV headers directly as fallback when profiles unavailable."""
    result = {}
    for csv_path in sorted(input_dir.glob("*.csv")):
        with open(csv_path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
        result[csv_path.name] = {
            "file": csv_path.name,
            "record_count": 0,
            "fields": {h: {"inferred_type": "string", "is_potential_pk": False, "is_potential_fk": False} for h in headers},
        }
    return result


def _build_entities(profiles: dict) -> list:
    """Build entity definitions from profiles."""
    entities = []
    for fname, profile in profiles.items():
        entity_name = _entity_name(fname)
        fields = []
        for field_name, fstats in profile["fields"].items():
            inferred = fstats.get("inferred_type", "string")
            erd_type = TYPE_MAP.get(inferred, "string")
            is_pk = fstats.get("is_potential_pk", False)
            is_fk = fstats.get("is_potential_fk", False)
            fk_ref = fstats.get("fk_references", "")

            marker = ""
            comment = ""
            if is_pk:
                marker = "PK"
            elif is_fk:
                marker = "FK"
                if fk_ref:
                    comment = f"references {_entity_name(fk_ref)}"

            fields.append({
                "name": field_name,
                "type": erd_type,
                "marker": marker,
                "comment": comment,
            })
        entities.append({
            "name": entity_name,
            "file": fname,
            "record_count": profile.get("record_count", 0),
            "fields": fields,
        })
    return entities


def _detect_relationships(profiles: dict) -> list:
    """Detect relationships between entities."""
    relationships = []
    seen = set()

    for fname, profile in profiles.items():
        entity_from = _entity_name(fname)
        from_count = profile.get("record_count", 0)

        for field_name, fstats in profile["fields"].items():
            if fstats.get("is_potential_fk") and fstats.get("fk_references"):
                ref_file = fstats["fk_references"]
                entity_to = _entity_name(ref_file)
                ref_count = profiles.get(ref_file, {}).get("record_count", 0)

                # Determine cardinality
                # Many side has more records, one side has fewer
                if from_count > ref_count:
                    rel = f"    {entity_from} }}o--|| {entity_to} : \"{field_name}\""
                else:
                    rel = f"    {entity_from} ||--o{{ {entity_to} : \"{field_name}\""

                key = tuple(sorted([entity_from, entity_to])) + (field_name,)
                if key not in seen:
                    seen.add(key)
                    relationships.append(rel)

            # Shared fields (non-FK like email)
            shared = fstats.get("shared_across", [])
            for other_file in shared:
                entity_to = _entity_name(other_file)
                key = tuple(sorted([entity_from, entity_to])) + (field_name,)
                if key not in seen:
                    seen.add(key)
                    relationships.append(
                        f"    {entity_from} }}o--o{{ {entity_to} : \"shared {field_name}\""
                    )

    return relationships


def generate_mermaid(profiles: dict) -> str:
    """Generate complete Mermaid erDiagram string."""
    entities = _build_entities(profiles)
    relationships = _detect_relationships(profiles)

    lines = ["erDiagram"]

    for entity in entities:
        lines.append(f"    {entity['name']} {{")
        for field in entity["fields"]:
            parts = [f"        {field['type']} {field['name']}"]
            if field["marker"]:
                parts.append(field["marker"])
            if field["comment"]:
                parts.append(f'"{field["comment"]}"')
            elif field["marker"] == "PK":
                parts.append('"Primary Key"')
            lines.append(" ".join(parts))
        lines.append("    }")

    if relationships:
        lines.append("")
        lines.extend(relationships)

    return "\n".join(lines)


def generate_html(profiles: dict, project_name: str = "") -> str:
    """Generate a rich self-contained HTML ERD + Data Mapping report with reviewer comment section."""
    import datetime as _dt
    entities = _build_entities(profiles)
    relationships = _detect_relationships(profiles)
    generated_at = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Parse relationships into structured rows
    rel_rows = []
    card_map = {
        "}o--||": "Many-to-One",
        "||--o{": "One-to-Many",
        "}o--o{": "Many-to-Many (shared field)",
        "||--||": "One-to-One",
    }
    for rel in relationships:
        rel_clean = rel.strip()
        parts = rel_clean.split(" : ")
        label = parts[1].strip('"') if len(parts) > 1 else ""
        tokens = parts[0].split() if parts else []
        if len(tokens) >= 3:
            cardinality = card_map.get(tokens[1], tokens[1])
            rel_rows.append((tokens[0], tokens[2], label, cardinality))

    # Palette: (header_bg, card_border)
    PALETTE = [
        ("#1e3a5f", "#2196f3"),
        ("#2d5a27", "#4caf50"),
        ("#7b2d00", "#ff7043"),
        ("#4a0072", "#ab47bc"),
        ("#00515a", "#00acc1"),
        ("#5a3a00", "#ffb300"),
    ]

    # Entity cards
    entity_cards = ""
    for i, entity in enumerate(entities):
        hdr, border = PALETTE[i % len(PALETTE)]
        rows = ""
        for f in entity["fields"]:
            badge = ""
            if f["marker"] == "PK":
                badge = '<span class="badge pk">PK</span>'
            elif f["marker"] == "FK":
                badge = '<span class="badge fk">FK</span>'
            note = f'<span class="fk-ref"> &rarr; {f["comment"]}</span>' if f["comment"] else ""
            rows += (
                f"<tr><td class='fn'>{f['name']}</td>"
                f"<td class='ft'>{f['type']}</td>"
                f"<td>{badge}{note}</td></tr>"
            )
        entity_cards += f"""
<div class="ecard" style="border-top:4px solid {border}">
  <div class="ehdr" style="background:{hdr}">
    <span class="ename">{entity['name']}</span>
    <span class="emeta">{entity['record_count']:,} records &bull; {entity['file']}</span>
  </div>
  <table class="ftbl">
    <thead><tr><th>Field</th><th>Type</th><th>Key</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""

    # Relationships table rows
    if rel_rows:
        rel_html = "".join(
            f"<tr><td>{r[0]}</td><td>{r[1]}</td><td><code>{r[2]}</code></td><td>{r[3]}</td></tr>"
            for r in rel_rows
        )
    else:
        rel_html = "<tr><td colspan='4' class='empty'>No relationships detected</td></tr>"

    # Data mapping table rows
    map_html = ""
    for i, entity in enumerate(entities):
        _, border = PALETTE[i % len(PALETTE)]
        for j, f in enumerate(entity["fields"]):
            rs = f' rowspan="{len(entity["fields"])}"' if j == 0 else ""
            ent_cell = (
                f'<td{rs} class="ecell" style="border-left:4px solid {border}">'
                f'{entity["name"]}<br/><small>{entity["file"]}</small></td>'
            ) if j == 0 else ""
            badge = ""
            if f["marker"] == "PK":
                badge = '<span class="badge pk">PK</span>'
            elif f["marker"] == "FK":
                badge = f'<span class="badge fk">FK &rarr; {f["comment"]}</span>'
            map_html += f"<tr>{ent_cell}<td class='fn'>{f['name']}</td><td class='ft'>{f['type']}</td><td>{badge}</td><td class='notes-cell'></td></tr>"

    title = f"{project_name} &mdash; " if project_name else ""
    total_fields = sum(len(e["fields"]) for e in entities)
    total_records = sum(e["record_count"] for e in entities)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>{title}ERD &amp; Data Mapping</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#222}}
a{{cursor:pointer;text-decoration:none}}
header{{background:#1a2340;color:#fff;padding:22px 40px}}
header h1{{font-size:1.6rem;font-weight:700}}
header p{{font-size:0.85rem;color:#9aaccc;margin-top:5px}}
nav{{display:flex;background:#fff;border-bottom:1px solid #dde;position:sticky;top:0;z-index:10}}
nav a{{padding:13px 22px;font-size:0.875rem;font-weight:500;color:#555;border-bottom:3px solid transparent}}
nav a:hover{{color:#1a73e8}}
nav a.active{{color:#1a73e8;border-bottom-color:#1a73e8}}
.tab{{display:none;padding:32px 40px}}
.tab.active{{display:block}}
.stitle{{font-size:1rem;font-weight:600;color:#1a2340;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #e0e4ef}}
/* Stats */
.stats{{display:flex;gap:14px;margin-bottom:28px;flex-wrap:wrap}}
.scard{{background:#fff;border-radius:8px;padding:16px 22px;box-shadow:0 1px 4px rgba(0,0,0,.09);min-width:130px}}
.scard .num{{font-size:2rem;font-weight:700;color:#1a73e8}}
.scard .lbl{{font-size:0.78rem;color:#666;margin-top:2px}}
/* Entity cards */
.egrid{{display:flex;flex-wrap:wrap;gap:20px}}
.ecard{{background:#fff;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.1);min-width:260px;max-width:400px;flex:1;overflow:hidden}}
.ehdr{{padding:11px 14px;display:flex;flex-direction:column}}
.ename{{font-size:.95rem;font-weight:700;color:#fff;letter-spacing:.4px}}
.emeta{{font-size:.72rem;color:rgba(255,255,255,.75);margin-top:3px}}
.ftbl{{width:100%;border-collapse:collapse;font-size:.84rem}}
.ftbl thead tr{{background:#f5f7fa}}
.ftbl th{{padding:7px 12px;text-align:left;font-size:.72rem;font-weight:600;color:#666;text-transform:uppercase;letter-spacing:.4px}}
.ftbl td{{padding:6px 12px;border-top:1px solid #f0f0f0}}
.ftbl tr:hover{{background:#fafbff}}
.fn{{font-family:monospace;font-size:.84rem;color:#1a2340}}
.ft{{font-size:.78rem;color:#777}}
/* Badges */
.badge{{display:inline-block;padding:1px 7px;border-radius:11px;font-size:.71rem;font-weight:600}}
.badge.pk{{background:#fff3cd;color:#856404}}
.badge.fk{{background:#cfe2ff;color:#084298}}
.fk-ref{{font-size:.71rem;color:#888}}
/* Tables */
.dtbl{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);font-size:.875rem}}
.dtbl thead tr{{background:#1a2340;color:#fff}}
.dtbl th{{padding:10px 14px;text-align:left;font-weight:500;white-space:nowrap}}
.dtbl td{{padding:8px 14px;border-bottom:1px solid #f0f0f0;vertical-align:middle}}
.dtbl tbody tr:hover{{background:#f5f8ff}}
.ecell{{font-weight:600;font-size:.84rem;vertical-align:top;padding-top:10px}}
.ecell small{{font-weight:400;color:#888;display:block;font-size:.75rem}}
.notes-cell{{min-width:200px}}
.empty{{text-align:center;color:#aaa;padding:24px;font-size:.875rem}}
code{{font-family:monospace;font-size:.85em;background:#f0f2f5;padding:1px 5px;border-radius:4px}}
/* Comments */
.cform{{background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,.08);padding:24px;margin-bottom:24px}}
.cform h3{{font-size:.95rem;font-weight:600;color:#1a2340;margin-bottom:16px}}
.frow{{display:flex;gap:12px;margin-bottom:14px;flex-wrap:wrap}}
.frow label{{font-size:.78rem;font-weight:500;color:#555;display:block;margin-bottom:4px}}
.frow input,.frow select{{padding:7px 10px;border:1px solid #ccd;border-radius:6px;font-size:.84rem;width:100%}}
.frow .f1{{flex:1;min-width:150px}}
.frow .f2{{flex:2;min-width:200px}}
textarea.cbox{{width:100%;border:1px solid #ccd;border-radius:6px;padding:10px;font-size:.84rem;min-height:90px;resize:vertical;font-family:inherit}}
.btn-add{{margin-top:10px;padding:8px 20px;background:#1a73e8;color:#fff;border:none;border-radius:6px;font-size:.875rem;font-weight:500;cursor:pointer}}
.btn-add:hover{{background:#1558c0}}
.centry{{background:#f8f9ff;border:1px solid #e0e4ef;border-radius:6px;padding:14px 16px;margin-bottom:10px}}
.cmeta{{font-size:.75rem;color:#888;margin-bottom:5px}}
.cbody{{font-size:.875rem;color:#222;line-height:1.5}}
.csec{{font-size:.71rem;font-weight:700;color:#1a73e8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:3px}}
.pri-low{{color:#6c757d}}.pri-med{{color:#fd7e14}}.pri-high{{color:#dc3545}}.pri-block{{color:#6f42c1}}
</style>
</head>
<body>
<header>
  <h1>{title}Entity Relationship Diagram &amp; Data Mapping</h1>
  <p>Generated: {generated_at} &nbsp;&bull;&nbsp; {len(entities)} entities &nbsp;&bull;&nbsp; {total_fields} fields &nbsp;&bull;&nbsp; {len(rel_rows)} relationships &nbsp;&bull;&nbsp; {total_records:,} total records</p>
</header>
<nav>
  <a class="active" onclick="show('erd',this)">ERD Overview</a>
  <a onclick="show('relationships',this)">Relationships</a>
  <a onclick="show('mapping',this)">Data Mapping</a>
  <a onclick="show('comments',this)">Reviewer Comments</a>
</nav>

<!-- ERD -->
<div id="t-erd" class="tab active">
  <div class="stats">
    <div class="scard"><div class="num">{len(entities)}</div><div class="lbl">Entities</div></div>
    <div class="scard"><div class="num">{total_fields}</div><div class="lbl">Total Fields</div></div>
    <div class="scard"><div class="num">{len(rel_rows)}</div><div class="lbl">Relationships</div></div>
    <div class="scard"><div class="num">{total_records:,}</div><div class="lbl">Total Records</div></div>
  </div>
  <div class="stitle">Entity Overview</div>
  <div class="egrid">{entity_cards}</div>
</div>

<!-- Relationships -->
<div id="t-relationships" class="tab">
  <div class="stitle">Detected Relationships</div>
  <table class="dtbl">
    <thead><tr><th>From Entity</th><th>To Entity</th><th>Key Field</th><th>Cardinality</th></tr></thead>
    <tbody>{rel_html}</tbody>
  </table>
</div>

<!-- Data Mapping -->
<div id="t-mapping" class="tab">
  <div class="stitle">Field-Level Data Mapping</div>
  <p style="margin-bottom:14px;font-size:.84rem;color:#666">The Notes column is for reviewers to annotate XDM field mappings, transformation rules, or data quality observations.</p>
  <table class="dtbl">
    <thead><tr><th>Entity</th><th>Field Name</th><th>Data Type</th><th>Key</th><th>Notes / XDM Mapping</th></tr></thead>
    <tbody>{map_html}</tbody>
  </table>
</div>

<!-- Reviewer Comments -->
<div id="t-comments" class="tab">
  <div class="cform">
    <h3>Add Review Comment</h3>
    <div class="frow">
      <div class="f1"><label>Reviewer Name</label><input type="text" id="cn" placeholder="e.g. Jane Smith"/></div>
      <div class="f1"><label>Section</label>
        <select id="cs">
          <option>ERD / Entity Model</option><option>Relationships</option><option>Data Mapping</option>
          <option>Data Quality</option><option>Identity Strategy</option><option>Schema Design</option><option>General</option>
        </select>
      </div>
      <div class="f1"><label>Priority</label>
        <select id="cp">
          <option>Low</option><option>Medium</option><option selected>High</option><option>Blocker</option>
        </select>
      </div>
    </div>
    <label style="font-size:.78rem;font-weight:500;color:#555;display:block;margin-bottom:4px">Comment</label>
    <textarea class="cbox" id="ct" placeholder="Add your review comment, question, or suggestion here..."></textarea>
    <button class="btn-add" onclick="addC()">Add Comment</button>
  </div>
  <div id="clog"><div id="cempty" style="text-align:center;color:#aaa;padding:32px;font-size:.875rem">No comments yet. Be the first to add a review comment.</div></div>
</div>

<script>
function show(id,el){{
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('nav a').forEach(a=>a.classList.remove('active'));
  document.getElementById('t-'+id).classList.add('active');
  el.classList.add('active');
}}
var priCls={{Low:'pri-low',Medium:'pri-med',High:'pri-high',Blocker:'pri-block'}};
function mk(tag,className,text){{
    var node=document.createElement(tag);
    if(className) node.className=className;
    if(text!==undefined) node.textContent=text;
    return node;
}}
function addC(){{
  var name=document.getElementById('cn').value.trim()||'Anonymous';
  var sec=document.getElementById('cs').value;
  var pri=document.getElementById('cp').value;
  var txt=document.getElementById('ct').value.trim();
  if(!txt){{alert('Please enter a comment.');return;}}
  var now=new Date().toLocaleString();
    var e=mk('div','centry');
    var secDiv=mk('div','csec',sec+' ');
    var priSpan=mk('span',priCls[pri],'['+pri+']');
    secDiv.appendChild(priSpan);

    var metaDiv=mk('div','cmeta',name+' - '+now);
    var bodyDiv=mk('div','cbody');
    txt.split(/\n/).forEach(function(line,i){{
        if(i>0) bodyDiv.appendChild(document.createElement('br'));
        bodyDiv.appendChild(document.createTextNode(line));
    }});

    e.appendChild(secDiv);
    e.appendChild(metaDiv);
    e.appendChild(bodyDiv);
  var log=document.getElementById('clog');
  var emp=document.getElementById('cempty');
  if(emp)emp.remove();
  log.appendChild(e);
  document.getElementById('ct').value='';
}}
</script>
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_erd.py <input_dir> [output_dir] [project_name]")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else input_dir / "output"
    project_name = sys.argv[3] if len(sys.argv) > 3 else ""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try loading profiles, fall back to reading CSV headers
    profiles = _load_profiles(output_dir)
    if profiles:
        print(f"Loaded profiles for {len(profiles)} files")
    else:
        print("No profiles found — reading CSV headers directly")
        profiles = _read_csv_headers(input_dir)
        if not profiles:
            print(f"No CSV files found in {input_dir}")
            sys.exit(1)

    # --- 1. Mermaid ERD (Markdown) ---
    mermaid = generate_mermaid(profiles)
    erd_md_path = output_dir / "erd_data_model.md"
    with open(erd_md_path, "w", encoding="utf-8") as f:
        f.write("# Entity-Relationship Diagram\n\n")
        f.write("```mermaid\n")
        f.write(mermaid)
        f.write("\n```\n")
    print(f"Mermaid ERD written to {erd_md_path}")

    # --- 2. Rich HTML ERD + Data Mapping + Reviewer Comments ---
    html = generate_html(profiles, project_name=project_name)
    erd_html_path = output_dir / "erd_data_model.html"
    with open(erd_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML ERD written to {erd_html_path}")

    print("\n--- Mermaid ERD (preview) ---")
    print(mermaid)
    print("--- End ERD ---")
    print("\nERD generation complete. Both Mermaid and HTML outputs written.")


if __name__ == "__main__":
    main()

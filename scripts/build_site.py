#!/usr/bin/env python3
"""Render the static, self-contained London planning-approval map.

Embeds the borough/OA boundary GeoJSON and precomputed area_stats.json
directly as inline JS variables (rather than fetch()ing them) so the page
works standalone when opened via file://, with no backend or live DB access.

Usage
-----
    python scripts/build_site.py
"""

import json
from pathlib import Path

DATA_DIR = Path("data")
OUT_PATH = Path("site/london_planning_map.html")

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>London Opportunity Area planning approval map</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
  html, body {{ height: 100%; margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  #app {{ display: flex; height: 100%; }}
  #map {{ flex: 1; }}
  #sidebar {{ width: 320px; padding: 16px; box-sizing: border-box; overflow-y: auto; border-left: 1px solid #ddd; }}
  h1 {{ font-size: 16px; margin: 0 0 12px; }}
  .mode-toggle {{ margin-bottom: 12px; }}
  .mode-toggle label {{ margin-right: 12px; font-size: 14px; cursor: pointer; }}
  .year-filter {{ margin-bottom: 16px; font-size: 14px; display: flex; align-items: center; gap: 6px; }}
  .year-filter select {{ font-size: 14px; }}
  #stats-panel {{ font-size: 14px; }}
  #stats-panel .placeholder {{ color: #888; }}
  #stats-panel .area-name {{ font-size: 18px; font-weight: 600; margin-bottom: 8px; }}
  #stats-panel table {{ width: 100%; border-collapse: collapse; }}
  #stats-panel td {{ padding: 3px 0; }}
  #stats-panel td.value {{ text-align: right; font-variant-numeric: tabular-nums; }}
  #stats-panel .rate-row td {{ font-weight: 600; border-top: 1px solid #ddd; padding-top: 6px; }}
  #stats-panel .warning {{ background: #fff4e5; border: 1px solid #f0b95c; border-radius: 4px; padding: 8px 10px; margin-bottom: 12px; font-size: 13px; color: #6b4a00; }}
</style>
</head>
<body>
<div id="app">
  <div id="map"></div>
  <div id="sidebar">
    <h1>London Opportunity Area planning approvals</h1>
    <div class="mode-toggle">
      <label><input type="radio" name="mode" value="boroughs" checked> Boroughs</label>
      <label><input type="radio" name="mode" value="opportunity_areas"> Opportunity Areas</label>
    </div>
    <div class="year-filter">
      Applications submitted
      <select id="year-from"></select>
      to
      <select id="year-to"></select>
    </div>
    <div id="stats-panel"><p class="placeholder">Click a borough or Opportunity Area on the map.</p></div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const BOROUGH_GEOJSON = {borough_geojson};
const OA_GEOJSON = {oa_geojson};
const AREA_STATS = {area_stats};

const NAME_PROP = {{ boroughs: "NAME", opportunity_areas: "opportunityarea" }};
const GEOJSON = {{ boroughs: BOROUGH_GEOJSON, opportunity_areas: OA_GEOJSON }};

// Coverage in the source planning-applications export varies hugely by area
// (from ~50 to ~30,000 total applications) - rates from small samples, and
// especially a 0% or 100% rate, likely reflect gaps in what was scraped for
// that area rather than the real-world approval pattern. See README.md.
const LOW_SAMPLE_THRESHOLD = 500;

const map = L.map("map").setView([51.509, -0.09], 10);
L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
  attribution: "&copy; OpenStreetMap contributors",
  maxZoom: 18,
}}).addTo(map);

const defaultStyle = {{ color: "#3388ff", weight: 1, fillOpacity: 0.15 }};
const selectedStyle = {{ color: "#e6194b", weight: 3, fillOpacity: 0.35 }};

let currentMode = "boroughs";
let currentLayer = null;
let selectedLayer = null;
let selectedName = null;

function aggregateStats(mode, name, fromYear, toYear) {{
  const byYear = (AREA_STATS[mode] && AREA_STATS[mode][name]) || {{}};
  const totals = {{ total: 0, approved: 0, rejected: 0, excluded: 0 }};
  for (const [year, counts] of Object.entries(byYear)) {{
    const y = parseInt(year, 10);
    if (y < fromYear || y > toYear) continue;
    totals.total += counts.total;
    totals.approved += counts.approved;
    totals.rejected += counts.rejected;
    totals.excluded += counts.excluded;
  }}
  const decided = totals.approved + totals.rejected;
  return {{
    ...totals,
    decided,
    approval_rate_pct: decided ? Math.round((totals.approved / decided) * 1000) / 10 : null,
    approved_rejected_ratio: totals.rejected ? Math.round((totals.approved / totals.rejected) * 100) / 100 : null,
  }};
}}

function coverageWarning(stats) {{
  if (stats.decided > 0 && (stats.approved === 0 || stats.rejected === 0)) {{
    const missing = stats.rejected === 0 ? "rejected" : "approved";
    return `<div class="warning">No ${{missing}} applications recorded for this area in the source data.
      This is very likely a gap in what was scraped for this council, not a genuine
      ${{stats.rejected === 0 ? "100%" : "0%"}} approval rate.</div>`;
  }}
  if (stats.total < LOW_SAMPLE_THRESHOLD) {{
    return `<div class="warning">Small sample: only ${{stats.total.toLocaleString()}} applications recorded
      for this area. Coverage in the source data varies a lot by council (from ~50 to
      ~30,000 total applications) - treat this rate with caution.</div>`;
  }}
  return "";
}}

function statsHtml(name, stats) {{
  if (!stats || stats.total === 0) {{
    return `<div class="area-name">${{name}}</div><p class="placeholder">No matched applications for this area.</p>`;
  }}
  const rate = stats.approval_rate_pct !== null ? stats.approval_rate_pct + "%" : "n/a";
  const ratio = stats.approved_rejected_ratio !== null ? stats.approved_rejected_ratio + " : 1" : "n/a";
  return `
    <div class="area-name">${{name}}</div>
    ${{coverageWarning(stats)}}
    <table>
      <tr><td>Total applications</td><td class="value">${{stats.total.toLocaleString()}}</td></tr>
      <tr><td>Approved (Permitted/Conditions)</td><td class="value">${{stats.approved.toLocaleString()}}</td></tr>
      <tr><td>Rejected</td><td class="value">${{stats.rejected.toLocaleString()}}</td></tr>
      <tr><td>Excluded (non-final state)</td><td class="value">${{stats.excluded.toLocaleString()}}</td></tr>
      <tr><td>Decided (approved+rejected)</td><td class="value">${{stats.decided.toLocaleString()}}</td></tr>
      <tr class="rate-row"><td>Approval rate</td><td class="value">${{rate}}</td></tr>
      <tr class="rate-row"><td>Approved : rejected</td><td class="value">${{ratio}}</td></tr>
    </table>`;
}}

function selectedYearRange() {{
  const from = parseInt(document.getElementById("year-from").value, 10);
  const to = parseInt(document.getElementById("year-to").value, 10);
  return [Math.min(from, to), Math.max(from, to)];
}}

function updatePanel() {{
  if (selectedName === null) return;
  const [fromYear, toYear] = selectedYearRange();
  const stats = aggregateStats(currentMode, selectedName, fromYear, toYear);
  document.getElementById("stats-panel").innerHTML = statsHtml(selectedName, stats);
}}

function selectFeature(layer, name) {{
  if (selectedLayer) selectedLayer.setStyle(defaultStyle);
  layer.setStyle(selectedStyle);
  selectedLayer = layer;
  selectedName = name;
  updatePanel();
}}

function renderLayer(mode) {{
  if (currentLayer) map.removeLayer(currentLayer);
  selectedLayer = null;
  selectedName = null;
  document.getElementById("stats-panel").innerHTML =
    '<p class="placeholder">Click a borough or Opportunity Area on the map.</p>';

  const nameProp = NAME_PROP[mode];
  currentLayer = L.geoJSON(GEOJSON[mode], {{
    style: () => defaultStyle,
    onEachFeature: (feature, layer) => {{
      const name = feature.properties[nameProp];
      layer.on("click", () => selectFeature(layer, name));
      layer.bindTooltip(name, {{ sticky: true }});
    }},
  }}).addTo(map);
}}

function populateYearSelects() {{
  const fromSelect = document.getElementById("year-from");
  const toSelect = document.getElementById("year-to");
  for (let y = AREA_STATS.min_year; y <= AREA_STATS.max_year; y++) {{
    fromSelect.add(new Option(y, y, y === AREA_STATS.min_year, y === AREA_STATS.min_year));
    toSelect.add(new Option(y, y, y === AREA_STATS.max_year, y === AREA_STATS.max_year));
  }}
  fromSelect.addEventListener("change", updatePanel);
  toSelect.addEventListener("change", updatePanel);
}}

document.querySelectorAll('input[name="mode"]').forEach((el) => {{
  el.addEventListener("change", (e) => {{
    currentMode = e.target.value;
    renderLayer(currentMode);
  }});
}});

populateYearSelects();
renderLayer(currentMode);
</script>
</body>
</html>
"""


def main() -> None:
    borough_geojson = json.loads((DATA_DIR / "london_borough_boundaries.geojson").read_text())
    oa_geojson = json.loads((DATA_DIR / "london_oa_boundaries.geojson").read_text())
    area_stats = json.loads((DATA_DIR / "area_stats.json").read_text())

    html = HTML_TEMPLATE.format(
        borough_geojson=json.dumps(borough_geojson),
        oa_geojson=json.dumps(oa_geojson),
        area_stats=json.dumps(area_stats),
    )
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(html)
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()

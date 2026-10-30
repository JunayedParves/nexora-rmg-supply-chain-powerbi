// Filter interactions for the Nexora report (run after build_storytelling.js).
// A slicer should narrow the story, never collapse a chart into a single point. So a slicer does NOT
// filter a visual when it would leave that visual with one item to look at:
//   1. the visual is broken down by the slicer's own field (Year slicer -> year trend lines,
//      Company slicer -> company ranking / company scorecard, Stock Type -> stock-type bars, ...)
//   2. the slicer's field nests inside the visual's breakdown (one factory = one company,
//      one export region = one market type), checked against the data
// Those visuals keep the full comparison as the benchmark, while KPI cards and every other chart
// follow the filter. Usage: node tools/build_interactions.js "<path to .Report dir>"
const fs = require("fs");
const path = require("path");

const PAGES = path.join(process.argv[2], "definition", "pages");
const readJ = (p) => JSON.parse(fs.readFileSync(p, "utf8"));

// slicer field -> breakdowns it collapses to one or two items (verified with DISTINCTCOUNT checks)
const NESTS_IN = {
  "dim_factory.factory_name": ["dim_company.company_name"],
  "dim_buyer.market_region": ["dim_buyer.market_classification"],
};

const ref = (f) => { const c = f.Column; return c ? `${c.Expression.SourceRef.Entity}.${c.Property}` : null; };

// the field(s) a visual is broken down by: chart axis + legend, or a table's first (row-grain) column
function grain(v) {
  const q = v.visual.query && v.visual.query.queryState;
  if (!q) return [];
  if (v.visual.visualType === "tableEx") { const c = q.Values.projections.map((p) => ref(p.field)).find(Boolean); return c ? [c] : []; }
  return ["Category", "Series"].flatMap((r) => (q[r] ? q[r].projections.map((p) => ref(p.field)) : [])).filter(Boolean);
}

for (const pageId of readJ(path.join(PAGES, "pages.json")).pageOrder) {
  const vdir = path.join(PAGES, pageId, "visuals");
  const visuals = fs.readdirSync(vdir).map((n) => readJ(path.join(vdir, n, "visual.json")));
  const slicers = visuals.filter((v) => v.visual.visualType === "slicer");
  const rules = [];
  for (const s of slicers) {
    const field = ref(s.visual.query.queryState.Values.projections[0].field);
    const blocked = [field, ...(NESTS_IN[field] || [])];
    for (const v of visuals) {
      if (v === s || v.visual.visualType === "slicer") continue;
      if (grain(v).some((g) => blocked.includes(g))) rules.push({ source: s.name, target: v.name, type: "NoFilter" });
    }
  }
  const pf = path.join(PAGES, pageId, "page.json");
  const pj = readJ(pf);
  if (rules.length) pj.visualInteractions = rules; else delete pj.visualInteractions;
  for (let i = 0; ; i++) { try { fs.writeFileSync(pf, JSON.stringify(pj, null, 2)); break; } catch (e) { if (i >= 30) throw e; Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 200); } }
  console.log(`${pj.displayName}: ${rules.map((r) => `${r.source} -/-> ${r.target}`).join(", ") || "all filters apply"}`);
}

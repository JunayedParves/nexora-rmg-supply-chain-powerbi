// Storytelling-with-Data measures for the Nexora dashboard.
// Every measure is a one-line call to the model's Nexora.* DAX functions:
//   Nexora.Fmt, Nexora.KpiContext, Nexora.KpiColor, Nexora.Trend, Nexora.RankTitle,
//   Nexora.TwoRatio, Nexora.BarColor, Nexora.Index
// Usage: node tools/storytelling_measures.js <out.json>
const fs = require("fs");

const FOLDER = "90. Storytelling";
const FOCUS = "#0B2C5F", ALERT = "#B54708";
const q = (s) => `"${s.replace(/"/g, '""')}"`;
const M = (n) => `[${n}]`;

const defs = [];
const add = (name, expression, formatString) =>
  defs.push({ name, tableName: "Executive_Measures", expression, displayFolder: FOLDER, ...(formatString ? { formatString } : {}) });

// ---------- support + index lines ----------
add("Late Shipped Quantity (PCS)", `CALCULATE ( [Shipped Quantity (PCS)], KEEPFILTERS ( fact_shipment_line[delay_reason] <> "On-Time Delivery (No Delay)" ) )`, "#,0");
const IDX = {
  "Nexora revenue": "Shipped FOB Revenue (USD)", "National RMG exports": "BGMEA National RMG Export ($B)",
  "Minimum wage": "Statutory Minimum Wage (BDT)", "Output per labour hour": "Output per Labour Hour (PCS)",
  "Payroll": "Total Workforce Payroll (USD)", "Headcount": "Active Headcount",
};
for (const [n, m] of Object.entries(IDX)) add(`${n} (index)`, `Nexora.Index ( ${M(m)} )`, "0");

// ---------- KPI context line + alert colour ----------
// [measure, number format, kind (add | level | rate), good direction (1 up, -1 down, 0 neutral)]
const KPIS = [
  ["Shipped FOB Revenue (USD)", "usd", "add", 1],
  ["Order Intake Value (USD)", "usd", "add", 1],
  ["Operational Gross Margin %", "pct1", "rate", 1],
  ["On-Time In-Full (OTIF) %", "pct1", "rate", 1],
  ["Closing Inventory Value (USD)", "usd", "level", 0],
  ["Actual Good Output (PCS)", "cnt", "add", 1],
  ["Shipped Revenue YoY Growth %", "pct1", "rate", 1],
  ["Average Selling Price (USD)", "usd", "level", 1],
  ["Average BDT/USD Exchange Rate", "n1", "level", 0],
  ["Statutory Minimum Wage (BDT)", "bdt", "level", 0],
  ["BGMEA National RMG Export ($B)", "usdbn", "level", 1],
  ["Container Freight Index", "n0", "level", -1],
  ["Ordered Quantity (PCS)", "cnt", "add", 1],
  ["Unfulfilled Order Backlog (PCS)", "cnt", "add", -1],
  ["Order Cancellation Rate %", "pct2", "rate", -1],
  ["Order Fulfilment Rate %", "pct1", "rate", 1],
  ["Total Procurement Value (USD)", "usd", "add", 0],
  ["Imported Procurement Share %", "pct1", "rate", -1],
  ["Supplier On-Time Delivery %", "pct1", "rate", 1],
  ["Supplier Material Rejection Rate %", "pct2", "rate", -1],
  ["Avg Supplier Delay (Days)", "n1", "level", -1],
  ["Material Wastage Cost (USD)", "usd", "add", -1],
  ["Closing Inventory Value (BDT)", "bdt", "level", 0],
  ["Inventory Turnover Ratio", "n1", "level", 1],
  ["Days Inventory Outstanding (DIO)", "n0", "level", -1],
  ["Stockout Incident Rate %", "pct1", "rate", -1],
  ["Safety Stock Compliance %", "pct1", "rate", 1],
  ["Plan vs Actual Attainment %", "pct1", "rate", 1],
  ["Production Line Efficiency %", "pct1", "rate", 1],
  ["Output per Labour Hour (PCS)", "n2", "level", 1],
  ["Labour Cost per Garment (USD)", "usd", "level", -1],
  ["Active Headcount", "cnt", "level", 0],
  ["First-Pass Yield (FPY) %", "pct1", "rate", 1],
  ["AQL Defect Rate %", "pct2", "rate", -1],
  ["Garment Rework Rate %", "pct2", "rate", -1],
  ["Total Cost of Poor Quality (USD)", "usd", "add", -1],
  ["On-Time Shipment (OTS) %", "pct1", "rate", 1],
  ["Total Production Cost (COGS USD)", "usd", "add", 0],
  ["Operational Gross Margin (USD)", "usd", "add", 1],
  ["Electricity per Garment (kWh)", "n3", "level", -1],
  ["Renewable Solar Share %", "pct1", "rate", 1],
  ["Carbon Footprint (kg CO2e/PC)", "n3", "level", -1],
];
for (const [m, f, kind, good] of KPIS) {
  add(`KPI Context | ${m}`, `Nexora.KpiContext ( ${M(m)}, ${q(f)}, ${q(kind)} )`);
  add(`KPI Color | ${m}`, `Nexora.KpiColor ( [KPI Context | ${m}], ${good} )`);
}

// ---------- action titles: the headline is the takeaway ----------
const trend = (m, label, f, up, down, ratio) => `Nexora.TrendTitle ( ${M(m)}, ${q(label)}, ${q(f)}, ${q(up)}, ${q(down)}, ${ratio ? 1 : 0} )`;
const rank = (d, m, f, lowFirst, n, pattern) => `Nexora.RankTitle ( ${d}, ${M(m)}, ${q(f)}, ${lowFirst}, ${n}, ${q(pattern)} )`;
const two = (a, b, pattern) => `Nexora.TwoRatio ( ${M(a)}, ${M(b)}, ${q(pattern)} )`;
const TITLES = {
  p1_vis01: trend("Shipped FOB Revenue (USD)", "Shipped revenue", "usd", "grew", "fell", true),
  p1_vis02: trend("On-Time In-Full (OTIF) %", "On-time-in-full delivery", "pct0", "improved", "fell", false),
  p1_vis03: rank("dim_company[company_name]", "Operational Gross Margin %", "pct1", 1, 1, "{name} trails at {value} gross margin vs {total} for the group"),
  p2_vis01: two("Shipped FOB Revenue (USD)", "BGMEA National RMG Export ($B)", "Since {y0}, Nexora revenue grew {a} vs {b} for national RMG exports"),
  p2_vis02: rank("dim_product[knit_woven_classification]", "Shipped FOB Revenue (USD)", "usd", 0, 1, "{name} garments generate {share} of revenue"),
  p2_vis03: two("Statutory Minimum Wage (BDT)", "Output per Labour Hour (PCS)", "Since {y0}, the minimum wage rose {a} while output per labour hour rose only {b}"),
  p3_vis01: rank("dim_buyer[buyer_name]", "Shipped FOB Revenue (USD)", "usd", 0, 2, "Two buyers ({name}) generate {share} of revenue"),
  p3_vis02: rank("dim_product[product_category]", "Shipped FOB Revenue (USD)", "usd", 0, 1, "{name} lead with {value}, {share} of revenue"),
  p3_vis03: rank("dim_buyer[market_classification]", "Shipped FOB Revenue (USD)", "usd", 0, 1, "{name} markets still supply {share} of revenue"),
  p4_vis01: rank("dim_supplier[origin_country]", "Total Procurement Value (USD)", "usd", 0, 1, "{name} supplies {share} of procurement spend ({value})"),
  p4_vis02: rank("dim_material[material_category]", "BOM Material Wastage Rate %", "pct1", 0, 1, "{name} has the highest wastage rate at {value} (all materials: {total})"),
  p4_vis03: rank("dim_supplier[domestic_import_classification]", "Total Procurement Value (USD)", "usd", 0, 1, "{name} materials make up {share} of procurement spend"),
  p5_vis01: trend("Days Inventory Outstanding (DIO)", "Days of inventory on hand", "days", "rose", "fell", false),
  p5_vis02: rank("fact_inventory_snapshot_monthly[stock_type]", "Closing Inventory Value (USD)", "usd", 0, 1, "{name} ties up {share} of closing inventory ({value})"),
  p5_vis03: rank("fact_inventory_snapshot_monthly[ageing_bucket]", "Closing Inventory Value (USD)", "usd", 0, 1, "{share} of closing inventory is {name} stock"),
  p6_vis01: rank("dim_company[company_name]", "Production Line Efficiency %", "pct1", 1, 1, "{name} trails at {value} line efficiency vs {total} for the group"),
  p6_vis02: two("Total Workforce Payroll (USD)", "Active Headcount", "Since {y0}, payroll grew {a} while headcount grew only {b}"),
  p6_vis03: rank("fact_workforce_monthly[department_name]", "Total Workforce Payroll (USD)", "usd", 0, 1, "{name} absorbs {share} of payroll"),
  p7_vis01: rank("dim_company[company_name]", "AQL Defect Rate %", "pct1", 0, 1, "{name} has the highest defect rate at {value} vs {total} for the group"),
  p7_vis02: rank("fact_shipment_line[delay_reason]", "Late Shipped Quantity (PCS)", "cnt", 0, 1, "{name} causes {share} of late shipment volume"),
  p7_vis03: `"Air freight carries " & FORMAT ( [Air Freight Revenue Share %], "0.0%" ) & " of revenue, the costly exception lane"`,
  p8_vis01: `"Direct material makes up " & FORMAT ( DIVIDE ( [Direct Material Cost (USD)], [Total Cost Ledger (USD)] ), "0%" ) & " of total cost, the biggest lever on margin"`,
  p8_vis02: trend("Carbon Footprint (kg CO2e/PC)", "Carbon per garment (kg CO2e)", "n3", "rose", "fell", true),
  p8_vis03: `"Gross margin keeps " & FORMAT ( [Operational Gross Margin %], "0%" ) & " of revenue; direct material takes " & FORMAT ( DIVIDE ( [Direct Material Cost (USD)], [Shipped FOB Revenue (USD)] ), "0%" )`,
};
for (const [id, expr] of Object.entries(TITLES)) add(`Title | ${id}`, expr);

// ---------- bar colours: grey by default, focus (navy) or alert (orange) on what matters ----------
const bar = (d, m, lowFirst, n, color) => `Nexora.BarColor ( ${d}, ${M(m)}, ${lowFirst}, ${n}, ${q(color)} )`;
const COLORS = {
  p1_vis03: bar("dim_company[company_name]", "Operational Gross Margin %", 1, 1, ALERT),
  p3_vis01: bar("dim_buyer[buyer_name]", "Shipped FOB Revenue (USD)", 0, 2, FOCUS),
  p3_vis02: bar("dim_product[product_category]", "Shipped FOB Revenue (USD)", 0, 1, FOCUS),
  p3_vis03: bar("dim_buyer[market_classification]", "Shipped FOB Revenue (USD)", 0, 1, FOCUS),
  p4_vis01: bar("dim_supplier[origin_country]", "Total Procurement Value (USD)", 0, 1, FOCUS),
  p4_vis02: bar("dim_material[material_category]", "BOM Material Wastage Rate %", 0, 1, ALERT),
  p4_vis03: bar("dim_supplier[domestic_import_classification]", "Total Procurement Value (USD)", 0, 1, FOCUS),
  p5_vis02: bar("fact_inventory_snapshot_monthly[stock_type]", "Closing Inventory Value (USD)", 0, 1, FOCUS),
  p5_vis03: bar("fact_inventory_snapshot_monthly[ageing_bucket]", "Closing Inventory Value (USD)", 0, 1, FOCUS),
  p6_vis01: bar("dim_company[company_name]", "Production Line Efficiency %", 1, 1, ALERT),
  p6_vis03: bar("fact_workforce_monthly[department_name]", "Total Workforce Payroll (USD)", 0, 1, FOCUS),
  p7_vis01: bar("dim_company[company_name]", "AQL Defect Rate %", 0, 1, ALERT),
  p7_vis02: bar("fact_shipment_line[delay_reason]", "Late Shipped Quantity (PCS)", 0, 1, ALERT),
  p7_vis03: bar("fact_shipment_line[shipping_mode]", "Shipped FOB Revenue (USD)", 1, 1, ALERT),
};
for (const [id, expr] of Object.entries(COLORS)) add(`Color | ${id}`, expr);

fs.writeFileSync(process.argv[2], JSON.stringify(defs));
console.log(`${defs.length} measures -> ${process.argv[2]}`);

// --tmdl <Executive_Measures.tmdl>: replace the storytelling measures in the TMDL file (Desktop must be closed)
const ti = process.argv.indexOf("--tmdl");
if (ti > 0) {
  const file = process.argv[ti + 1];
  const names = new Set(defs.map((d) => d.name));
  const kept = []; let skipping = false;
  for (const l of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const mm = l.match(/^\tmeasure '((?:[^']|'')+)' = /);
    if (mm) skipping = names.has(mm[1].replace(/''/g, "'"));
    else if (/^\t\S/.test(l)) skipping = false;
    if (!skipping) kept.push(l);
  }
  const block = defs.map((d) => `\tmeasure '${d.name.replace(/'/g, "''")}' = ${d.expression}\n` +
    (d.formatString ? `\t\tformatString: ${d.formatString}\n` : "") + `\t\tdisplayFolder: ${FOLDER}\n`).join("\n");
  let s = kept.join("\n");
  const at = s.search(/^\tcolumn /m);
  s = s.slice(0, at) + block + "\n" + s.slice(at);
  fs.writeFileSync(file, s);
  console.log(`TMDL updated: ${file}`);
}

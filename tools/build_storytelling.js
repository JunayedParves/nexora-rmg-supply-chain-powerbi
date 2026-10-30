// Storytelling-with-Data pass for the Nexora report (run after build_report.js).
// Principles applied (Knaflic): context first, right visual for the job, declutter,
// grey by default + one focus/alert colour, action titles that state the takeaway.
// Usage: node tools/build_storytelling.js "<path to .Report dir>"
const fs = require("fs");
const path = require("path");

const REPORT = process.argv[2];
const DEF = path.join(REPORT, "definition");
const PAGES = path.join(DEF, "pages");
const RES = path.join(REPORT, "StaticResources", "RegisteredResources");
const THEME_NAME = "NexoraBrand-5d8e2b17.json";

const C = {
  focus: "#0B2C5F", alert: "#B54708", context: "#868F9C", context2: "#A9B1BC", context3: "#CDD3DB",
  ink: "#1F2937", ink2: "#374151", muted: "#4B5563", line: "#DDE3EA", white: "#FFFFFF", page: "#F3F5F8",
};

// ---------- expression helpers ----------
const lit = (v) => ({ expr: { Literal: { Value: v } } });
const str = (s) => lit(`'${String(s).replace(/'/g, "''")}'`);
const num = (n) => lit(`${n}D`);
const bool = (b) => lit(b ? "true" : "false");
const color = (hex) => ({ solid: { color: str(hex) } });
const MT = "Executive_Measures";
const msrField = (name) => ({ Measure: { Expression: { SourceRef: { Entity: MT } }, Property: name } });
const colField = (e, p) => ({ Column: { Expression: { SourceRef: { Entity: e } }, Property: p } });
const measureColor = (name) => ({ solid: { color: { expr: msrField(name) } } });
const readJ = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const writeJ = (p, o) => fs.writeFileSync(p, JSON.stringify(o, null, 2));

const projCol = (e, p, label) => ({ field: colField(e, p), queryRef: `${e}.${p}`, nativeQueryRef: p, active: true, ...(label ? { displayName: label } : {}) });
const projMsr = (m, label) => ({ field: msrField(m), queryRef: `${MT}.${m}`, nativeQueryRef: m, ...(label ? { displayName: label } : {}) });

// ---------- page questions (context: what decision is this page for?) ----------
const QUESTIONS = {
  p1: "Are we growing profitably while serving buyers reliably?",
  p2: "Is Nexora keeping pace with the industry and absorbing cost inflation?",
  p3: "Where does revenue come from, and how concentrated is it?",
  p4: "How dependent and how reliable is our supply base?",
  p5: "Is working capital tied up efficiently?",
  p6: "Are productivity gains keeping up with labour costs?",
  p7: "Where do quality and delivery failures come from?",
  p8: "What drives cost, and are we decarbonising?",
};

// ---------- chart specs: one takeaway per chart ----------
const YEAR = ["dim_date", "calendar_year", "Year"];
const SPECS = {
  p1_vis01: { kind: "line", cat: YEAR, y: [["Shipped FOB Revenue (USD)", "Revenue", C.focus]], sub: "Shipped FOB revenue per year, USD" },
  p1_vis02: { kind: "line", cat: YEAR, y: [["On-Time In-Full (OTIF) %", "OTIF", C.alert]], sub: "Share of shipment lines delivered on time and in full, per year" },
  p1_vis03: { kind: "bar", cat: ["dim_company", "company_name", "Company"], y: ["Operational Gross Margin %", "Gross margin %"], fill: "Color | p1_vis03", sub: "Operational gross margin % by company. Orange = lowest" },
  p2_vis01: { kind: "line", cat: YEAR, y: [["Nexora revenue (index)", "Nexora revenue", C.focus], ["National RMG exports (index)", "National RMG exports", C.context]], sub: "Growth indexed to the first selected year = 100" },
  p2_vis02: { kind: "line", cat: YEAR, y: [["Shipped FOB Revenue (USD)", "Revenue"]], series: ["dim_product", "knit_woven_classification", { Woven: C.focus, Knit: C.context }], sub: "Shipped FOB revenue per year by garment construction, USD" },
  p2_vis03: { kind: "line", cat: YEAR, y: [["Minimum wage (index)", "Minimum wage", C.alert], ["Output per labour hour (index)", "Output per labour hour", C.focus]], sub: "Indexed to the first selected year = 100. The gap is cost pressure productivity has not absorbed" },
  p3_vis01: { kind: "bar", cat: ["dim_buyer", "buyer_name", "Buyer"], y: ["Shipped FOB Revenue (USD)", "Revenue"], fill: "Color | p3_vis01", sub: "Shipped FOB revenue by buyer, USD. Navy = top two" },
  p3_vis02: { kind: "bar", cat: ["dim_product", "product_category", "Category"], y: ["Shipped FOB Revenue (USD)", "Revenue"], fill: "Color | p3_vis02", sub: "Shipped FOB revenue by product category, USD" },
  p3_vis03: { kind: "bar", cat: ["dim_buyer", "market_classification", "Market"], y: ["Shipped FOB Revenue (USD)", "Revenue"], fill: "Color | p3_vis03", sub: "Shipped FOB revenue by market type, USD" },
  p4_vis01: { kind: "bar", cat: ["dim_supplier", "origin_country", "Country"], y: ["Total Procurement Value (USD)", "Spend"], fill: "Color | p4_vis01", sub: "Procurement spend by supplier country, USD" },
  p4_vis02: { kind: "bar", cat: ["dim_material", "material_category", "Material"], y: ["BOM Material Wastage Rate %", "Wastage %"], fill: "Color | p4_vis02", sub: "Material wastage rate vs bill of materials. Orange = highest" },
  p4_vis03: { kind: "bar", cat: ["dim_supplier", "domestic_import_classification", "Source"], y: ["Total Procurement Value (USD)", "Spend"], fill: "Color | p4_vis03", sub: "Procurement spend, domestic vs imported, USD" },
  p5_vis01: { kind: "line", cat: YEAR, y: [["Days Inventory Outstanding (DIO)", "Days of inventory", C.alert]], sub: "Days of COGS held as inventory, per year. Lower is better" },
  p5_vis02: { kind: "bar", cat: ["fact_inventory_snapshot_monthly", "stock_type", "Stock stage"], y: ["Closing Inventory Value (USD)", "Closing inventory"], fill: "Color | p5_vis02", sub: "Closing inventory value by stock stage, USD" },
  p5_vis03: { kind: "bar", cat: ["fact_inventory_snapshot_monthly", "ageing_bucket", "Age"], y: ["Closing Inventory Value (USD)", "Closing inventory"], fill: "Color | p5_vis03", sortByCat: true, sub: "Closing inventory value by age bucket, USD" },
  p6_vis01: { kind: "bar", cat: ["dim_company", "company_name", "Company"], y: ["Production Line Efficiency %", "Line efficiency %"], fill: "Color | p6_vis01", sub: "Earned vs available standard minutes by company. Orange = lowest" },
  p6_vis02: { kind: "line", cat: YEAR, y: [["Payroll (index)", "Payroll", C.alert], ["Headcount (index)", "Headcount", C.context]], sub: "Indexed to the first selected year = 100" },
  p6_vis03: { kind: "bar", cat: ["fact_workforce_monthly", "department_name", "Department"], y: ["Total Workforce Payroll (USD)", "Payroll"], fill: "Color | p6_vis03", sub: "Workforce payroll by department, USD" },
  p7_vis01: { kind: "bar", cat: ["dim_company", "company_name", "Company"], y: ["AQL Defect Rate %", "Defect rate %"], fill: "Color | p7_vis01", sub: "Defective share of inspected pieces by company. Defect types are evenly split (~14% each), so the lever is where garments are made, not what fails" },
  p7_vis02: { kind: "bar", cat: ["fact_shipment_line", "delay_reason", "Delay reason"], y: ["Late Shipped Quantity (PCS)", "Late pcs"], fill: "Color | p7_vis02", sub: "Pieces shipped late, by root cause (on-time shipments excluded)" },
  p7_vis03: { kind: "bar", cat: ["fact_shipment_line", "shipping_mode", "Mode"], y: ["Shipped FOB Revenue (USD)", "Revenue"], fill: "Color | p7_vis03", sub: "Shipped FOB revenue by shipping mode, USD" },
  p8_vis02: { kind: "line", cat: YEAR, y: [["Carbon Footprint (kg CO2e/PC)", "kg CO2e per garment", C.focus]], sub: "Estimated emissions per garment, kg CO2e. Lower is better" },
};

// ---------- builders ----------
function chrome(id, sub) {
  return {
    title: [{ properties: { show: bool(true), text: { expr: msrField(`Title | ${id}`) }, fontSize: num(14), fontFamily: str("Segoe UI Semibold"), fontColor: color(C.ink), titleWrap: bool(true) } }],
    subTitle: [{ properties: { show: bool(true), text: str(sub), fontSize: num(10), fontColor: color(C.muted), titleWrap: bool(true) } }],
    background: [{ properties: { show: bool(true), color: color(C.white), transparency: num(0) } }],
    border: [{ properties: { show: bool(false) } }],
    dropShadow: [{ properties: { show: bool(false) } }],
    general: [{ properties: { altText: str(sub) } }],
  };
}

const axisQuiet = (showValueAxis) => ({
  categoryAxis: [{ properties: { show: bool(true), showAxisTitle: bool(false), fontSize: num(10), labelColor: color(C.ink2), gridlineShow: bool(false) } }],
  valueAxis: [{ properties: { show: bool(showValueAxis), showAxisTitle: bool(false), fontSize: num(10), labelColor: color(C.muted), gridlineShow: bool(false) } }],
});

function lineVisual(id, s) {
  const [ce, cp, cl] = s.cat;
  const queryState = { Category: { projections: [projCol(ce, cp, cl)] }, Y: { projections: s.y.map(([m, l]) => projMsr(m, l)) } };
  if (s.series) queryState.Series = { projections: [projCol(s.series[0], s.series[1], "Series")] };
  const multi = s.y.length > 1 || !!s.series;
  const fills = s.series
    ? Object.entries(s.series[2]).map(([val, hex]) => ({
        properties: { fill: color(hex) },
        selector: { data: [{ scopeId: { Comparison: { ComparisonKind: 0, Left: colField(s.series[0], s.series[1]), Right: { Literal: { Value: `'${val}'` } } } } }] },
      }))
    : s.y.map(([m, , hex]) => ({ properties: { fill: color(hex) }, selector: { metadata: `${MT}.${m}` } }));
  return {
    visualType: "lineChart",
    query: { queryState, sortDefinition: { sort: [{ field: colField(ce, cp), direction: "Ascending" }], isDefaultSort: false } },
    objects: {
      ...axisQuiet(true),
      legend: [{ properties: { show: bool(false) } }],
      dataPoint: fills,
      lineStyles: [{ properties: { strokeWidth: lit("3L"), showMarker: bool(false) } }],
      seriesLabels: [{ properties: { show: bool(multi), textSize: num(10), seriesMatchColor: bool(true) } }],
      labels: [{ properties: { show: bool(false) } }],
    },
    visualContainerObjects: chrome(id, s.sub),
    drillFilterOtherVisuals: true,
  };
}

function barVisual(id, s) {
  const [ce, cp, cl] = s.cat;
  const [m, ml] = s.y;
  const sortField = s.sortByCat ? colField(ce, cp) : msrField(m);
  return {
    visualType: "clusteredBarChart",
    query: {
      queryState: { Category: { projections: [projCol(ce, cp, cl)] }, Y: { projections: [projMsr(m, ml)] } },
      sortDefinition: { sort: [{ field: sortField, direction: s.sortByCat ? "Ascending" : "Descending" }], isDefaultSort: false },
    },
    objects: {
      ...axisQuiet(false),
      legend: [{ properties: { show: bool(false) } }],
      labels: [{ properties: { show: bool(true), fontSize: num(10), color: color(C.ink) } }],
      dataPoint: [{ properties: { fill: measureColor(s.fill) }, selector: { data: [{ dataViewWildcard: { matchingOption: 1 } }] } }],
    },
    visualContainerObjects: chrome(id, s.sub),
    drillFilterOtherVisuals: true,
  };
}

// KPI: name as title, context line as subtitle (orange only when it moved the wrong way), value in ink
function styleKpi(v) {
  const p = v.visual.query.queryState.Data.projections[0];
  const m = p.field.Measure.Property;
  const label = m.replace(/ \((USD|PCS)\)$/, "");
  const o = (v.visual.objects ||= {});
  o.label = [{ properties: { show: bool(false) }, selector: { id: "default" } }];
  o.value = [{ properties: { fontSize: num(28), fontFamily: str("Segoe UI Semibold"), fontColor: color(C.ink) }, selector: { id: "default" } }];
  const vco = (v.visual.visualContainerObjects ||= {});
  vco.title = [{ properties: { show: bool(true), text: str(label), fontSize: num(11), fontFamily: str("Segoe UI"), fontColor: color(C.ink2) } }];
  vco.subTitle = [{ properties: { show: bool(true), text: { expr: msrField(`KPI Context | ${m}`) }, fontSize: num(10), fontColor: { solid: { color: { expr: msrField(`KPI Color | ${m}`) } } } } }];
  vco.border = [{ properties: { show: bool(false) } }];
  vco.background = [{ properties: { show: bool(true), color: color(C.white), transparency: num(0) } }];
  vco.general = [{ properties: { altText: str(`KPI: ${label}`) } }];
}

// tables: let the numbers carry the ink, not the header box
function styleTable(v) {
  const o = v.visual.objects;
  Object.assign(o.columnHeaders[0].properties, { fontColor: color(C.ink), backColor: color(C.white), bold: bool(true) });
  Object.assign(o.values[0].properties, { backColorSecondary: color(C.white), fontColorSecondary: color(C.ink) });
  o.total = [{ properties: { fontSize: num(10), bold: bool(true), fontColor: color(C.ink), backColor: color(C.white) } }];
  const vco = v.visual.visualContainerObjects;
  vco.border = [{ properties: { show: bool(false) } }];
  vco.subTitle = vco.subTitle && [{ properties: { ...vco.subTitle[0].properties, fontColor: color(C.muted) } }];
}

function waterfallStory(v) {
  const axes = axisQuiet(false);
  delete axes.categoryAxis[0].properties.gridlineShow;
  v.visual.objects = {
    ...axes,
    legend: [{ properties: { show: bool(false) } }],
    labels: [{ properties: { show: bool(true), fontSize: num(10), color: color(C.ink) } }],
    sentimentColors: [{ properties: { increaseFill: color(C.context), decreaseFill: color(C.alert), totalFill: color(C.focus) } }],
  };
  v.visual.visualContainerObjects = chrome("p8_vis01", "Total cost build-up by P&L line, USD. Navy = total cost");
}

function stackedStory(v) {
  const order = [["Direct Material Cost (USD)", C.context], ["Direct Labour Cost (USD)", C.context2], ["Factory Overhead Cost (USD)", C.context3], ["Operational Gross Margin (USD)", C.focus]];
  const labels = { "Direct Material Cost (USD)": "Material", "Direct Labour Cost (USD)": "Labour", "Factory Overhead Cost (USD)": "Overhead", "Operational Gross Margin (USD)": "Gross margin" };
  for (const p of v.visual.query.queryState.Y.projections) p.displayName = labels[p.field.Measure.Property] || p.displayName;
  v.visual.objects = {
    ...axisQuiet(false),
    legend: [{ properties: { show: bool(true), position: str("Top"), fontSize: num(10), labelColor: color(C.ink2) } }],
    dataPoint: order.map(([m, hex]) => ({ properties: { fill: color(hex) }, selector: { metadata: `${MT}.${m}` } })),
  };
  v.visual.visualContainerObjects = chrome("p8_vis03", "Each bar is shipped revenue split into cost and margin (grey = cost, navy = margin), USD");
}

// ---------- main ----------
const pagesMeta = readJ(path.join(PAGES, "pages.json"));
for (const pageId of pagesMeta.pageOrder) {
  const vdir = path.join(PAGES, pageId, "visuals");
  const prefix = fs.readdirSync(vdir)[0].split("_")[0];

  // header subtitle becomes the page question
  const hf = path.join(vdir, `${prefix}_hdr01`, "visual.json");
  const h = readJ(hf);
  h.visual.objects.general[0].properties.paragraphs[1].textRuns[0].value = QUESTIONS[prefix];
  writeJ(hf, h);

  for (const name of fs.readdirSync(vdir)) {
    const f = path.join(vdir, name, "visual.json");
    if (/_kpiico\d+$/.test(name)) { fs.rmSync(path.join(vdir, name), { recursive: true }); continue; } // decoration, not data
    const v = readJ(f);
    if (/_kpi\d+$/.test(name)) styleKpi(v);
    else if (SPECS[name]) {
      const s = SPECS[name];
      v.visual = s.kind === "line" ? lineVisual(name, s) : barVisual(name, s);
      delete v.filterConfig;
      // keep the right-hand top chart in its grid slot (it was dragged out of place once in Desktop)
      if (name === "p1_vis02") Object.assign(v.position, { x: 1170, y: 282, width: 734, height: 380 });
    } else if (name === "p8_vis01") waterfallStory(v);
    else if (name === "p8_vis03") stackedStory(v);
    else if (v.visual.visualType === "tableEx") styleTable(v);
    else continue;
    writeJ(f, v);
  }
  console.log(`${pageId} (${prefix}) done`);
}

// ---------- theme: grey-first palette, no borders, no gridlines ----------
const rj = readJ(path.join(DEF, "report.json"));
const oldName = rj.themeCollection.customTheme.name;
const theme = readJ(path.join(RES, oldName));
theme.name = THEME_NAME;
theme.dataColors = [C.focus, C.context, C.alert, "#4F7CAC", C.context2, "#5B6770", "#8C6D1F", "#0F7F81"];
const all = theme.visualStyles["*"]["*"];
all.border = [{ show: false }];
all.valueAxis = [{ ...all.valueAxis[0], gridlineShow: false }];
all.legend = [{ ...all.legend[0], show: false }];
fs.rmSync(path.join(RES, oldName));
writeJ(path.join(RES, THEME_NAME), theme);
rj.themeCollection.customTheme.name = THEME_NAME;
const reg = rj.resourcePackages.find((p) => p.type === "RegisteredResources");
for (const i of reg.items) if (i.type === "CustomTheme") { i.name = THEME_NAME; i.path = THEME_NAME; }
writeJ(path.join(DEF, "report.json"), rj);
console.log("theme ->", THEME_NAME);

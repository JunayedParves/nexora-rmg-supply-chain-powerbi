// Nexora Apparels — report redesign generator (PBIR). Usage: node tools/build_report.js "<path to .Report dir>"
const fs = require("fs");
const path = require("path");

const REPORT = process.argv[2];
const DEF = path.join(REPORT, "definition");
const PAGES = path.join(DEF, "pages");
const RES = path.join(REPORT, "StaticResources", "RegisteredResources");

// ---------- Brand & accessibility tokens ----------
const C = {
  navy: "#0B2C5F", green: "#5BA829", ink: "#1F2937", ink2: "#374151", muted: "#4B5563",
  line: "#C7D0DC", lineSoft: "#DDE3EA", page: "#F3F5F8", white: "#FFFFFF", band: "#F3F6FA", hover: "#E8EEF6",
};
const THEME_NAME = "NexoraBrand-7c41e9a2.json";

// ---------- Expression helpers ----------
const lit = (v) => ({ expr: { Literal: { Value: v } } });
const str = (s) => lit(`'${String(s).replace(/'/g, "''")}'`);
const num = (n) => lit(`${n}D`);
const bool = (b) => lit(b ? "true" : "false");
const color = (hex) => ({ solid: { color: str(hex) } });
const col = (entity, prop) => ({ Column: { Expression: { SourceRef: { Entity: entity } }, Property: prop } });
const msr = (entity, prop) => ({ Measure: { Expression: { SourceRef: { Entity: entity } }, Property: prop } });

const readJ = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
// Power BI Desktop briefly locks files it is watching, so retry a write instead of failing mid-build
const writeRetry = (p, data) => { for (let i = 0; ; i++) { try { return fs.writeFileSync(p, data); } catch (e) { if (i >= 30) throw e; Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 200); } } };
const writeJ = (p, o) => { fs.mkdirSync(path.dirname(p), { recursive: true }); writeRetry(p, JSON.stringify(o, null, 2)); };

let SCHEMA_VC = null;

// ---------- Page plan (management-consultant decisions) ----------
const PLAN = {
  e5224d3fb000009d5a9d: {
    nav: "Executive", icon: "page_01_executive_brand.svg",
    title: "Executive Command Center",
    sub: "Group revenue, margin, customer delivery, working capital and output across 8 companies and 26 factories",
    slicers: [{ entity: "dim_factory", prop: "factory_name", label: "Factory" }, { entity: "dim_factory", prop: "compliance_profile", label: "Compliance Tier" }],
  },
  page2_macro_trends00: {
    nav: "Macro & Market", icon: "page_02_macro_brand.svg",
    title: "Macro Environment & 20-Year Trends",
    sub: "Nexora growth against Bangladesh RMG exports, exchange rate, minimum wage and freight costs",
    slicers: [{ entity: "dim_product", prop: "knit_woven_classification", label: "Knit / Woven" }],
    note: "National data (FX, CPI, wage, freight, RMG exports) ignores these filters.",
  },
  page3_commercial0000: {
    nav: "Commercial", icon: "page_03_commercial_brand.svg",
    title: "Commercial Performance: Buyers & Markets",
    sub: "Order intake, shipped revenue, pricing, cancellations and fulfilment by buyer, product and export market",
    slicers: [{ entity: "dim_buyer", prop: "market_region", label: "Export Market" }, { entity: "dim_product", prop: "knit_woven_classification", label: "Knit / Woven" }],
  },
  page4_procurement000: {
    nav: "Procurement", icon: "page_04_procurement_brand.svg",
    title: "Procurement & Supplier Reliability",
    sub: "Spend, import dependence, supplier on-time delivery, rejections and material wastage",
    slicers: [{ entity: "dim_material", prop: "material_category", label: "Material Category" }, { entity: "dim_factory", prop: "factory_name", label: "Factory" }],
  },
  page5_inventory00000: {
    nav: "Inventory", icon: "page_05_inventory_brand.svg",
    title: "Inventory & Working Capital",
    sub: "Stock value, ageing, turnover, days on hand and stock-out risk across factories",
    slicers: [{ entity: "fact_inventory_snapshot_monthly", prop: "stock_type", label: "Stock Type" }, { entity: "dim_material", prop: "material_category", label: "Material Category" }],
  },
  page6_manufacturing0: {
    nav: "Production", icon: "page_06_manufacturing_brand.svg",
    title: "Manufacturing Productivity & Workforce",
    sub: "Good output, plan attainment, line efficiency, labour productivity, headcount and payroll",
    slicers: [{ entity: "dim_factory", prop: "factory_name", label: "Factory" }, { entity: "dim_factory", prop: "compliance_profile", label: "Compliance Tier" }],
  },
  page7_quality_otif00: {
    nav: "Quality & OTIF", icon: "page_07_quality_brand.svg",
    title: "Quality Assurance & On-Time Delivery",
    sub: "First-pass yield, defects, cost of poor quality and on-time-in-full shipment performance",
    slicers: [{ entity: "dim_factory", prop: "compliance_profile", label: "Compliance Tier" }, { entity: "dim_product", prop: "product_category", label: "Product Category" }],
  },
  page8_finance_esg000: {
    nav: "Finance & ESG", icon: "page_08_sustainability_brand.svg",
    title: "Cost Structure & Sustainability (ESG)",
    sub: "COGS composition, gross margin, energy intensity, renewable share and carbon footprint",
    slicers: [{ entity: "dim_factory", prop: "compliance_profile", label: "Compliance Tier" }, { entity: "dim_factory", prop: "factory_name", label: "Factory" }],
  },
};

// ---------- Layout grid (1920 x 1080) ----------
const L = {
  hdr: { x: 16, y: 12, w: 1888, h: 84 },
  ctl: { y: 102, h: 70 },
  slicerX: [16, 224, 432, 640], slicerW: 200,
  nav: { x: 852, w: 1052 },
  kpiY: 180, kpiH: 108, kpiIcoY: 192,
  row1: { y: 296, h: 366 }, row2: { y: 672, h: 392 },
};

// ---------- Visual builders ----------
function container(name, pos, visual, extra = {}) {
  return {
    $schema: SCHEMA_VC, name,
    position: { x: pos.x, y: pos.y, z: pos.z, width: pos.w, height: pos.h, tabOrder: pos.z },
    visual, ...extra,
  };
}

function headerTextbox(name, plan) {
  return container(name, { ...L.hdr, z: 100 }, {
    visualType: "textbox",
    objects: {
      general: [{
        properties: {
          paragraphs: [
            { textRuns: [{ value: plan.title, textStyle: { fontFamily: "Segoe UI Semibold", fontSize: "22pt", color: C.navy } }] },
            { textRuns: [{ value: plan.sub, textStyle: { fontFamily: "Segoe UI", fontSize: "12pt", color: C.muted } }] },
          ],
        },
      }],
    },
    visualContainerObjects: {
      background: [{ properties: { show: bool(true), color: color(C.white), transparency: num(0) } }],
      border: [{ properties: { show: bool(true), color: color(C.lineSoft), radius: num(8), width: num(1) } }],
      padding: [{ properties: { top: num(8), bottom: num(4), left: num(392), right: num(420) } }],
    },
    drillFilterOtherVisuals: true,
  });
}

function periodTextbox(name) {
  return container(name, { x: 1500, y: 24, w: 392, h: 60, z: 160 }, {
    visualType: "textbox",
    objects: {
      general: [{
        properties: {
          paragraphs: [
            { textRuns: [{ value: "Reporting period: 2006 – 2025", textStyle: { fontFamily: "Segoe UI Semibold", fontSize: "12pt", color: C.ink2 } }], horizontalTextAlignment: "right" },
            { textRuns: [{ value: "Values in USD unless stated · Use the filters below", textStyle: { fontFamily: "Segoe UI", fontSize: "11pt", color: C.muted } }], horizontalTextAlignment: "right" },
          ],
        },
      }],
    },
    visualContainerObjects: {
      background: [{ properties: { show: bool(false) } }],
      border: [{ properties: { show: bool(false) } }],
    },
    drillFilterOtherVisuals: true,
  });
}

function imageVisual(name, pos, item, alt) {
  return container(name, pos, {
    visualType: "image",
    objects: {
      general: [{ properties: { imageUrl: { expr: { ResourcePackageItem: { PackageName: "RegisteredResources", PackageType: 1, ItemName: item } } } } }],
      imageScaling: [{ properties: { imageScalingType: str("Fit") } }],
    },
    visualContainerObjects: {
      background: [{ properties: { show: bool(false) } }],
      border: [{ properties: { show: bool(false) } }],
      general: [{ properties: { altText: str(alt) } }],
    },
    drillFilterOtherVisuals: true,
  });
}

function divider(name, pos, fill) {
  return container(name, pos, {
    visualType: "shape",
    objects: {
      shape: [{ properties: { tileShape: str("rectangle") } }],
      fill: [{ properties: { fillColor: color(fill), transparency: num(0) }, selector: { id: "default" } }],
      outline: [{ properties: { show: bool(false) }, selector: { id: "default" } }],
    },
    visualContainerObjects: {
      background: [{ properties: { show: bool(false) } }],
      border: [{ properties: { show: bool(false) } }],
      padding: [{ properties: { top: num(0), bottom: num(0), left: num(0), right: num(0) } }],
    },
    drillFilterOtherVisuals: true,
  });
}

function slicer(name, x, z, entity, prop, label, syncGroup) {
  const visual = {
    visualType: "slicer",
    query: {
      queryState: {
        Values: { projections: [{ field: col(entity, prop), queryRef: `${entity}.${prop}`, nativeQueryRef: prop, active: true, displayName: label }] },
      },
    },
    objects: {
      data: [{ properties: { mode: str("Dropdown") } }],
      header: [{ properties: { show: bool(false) } }],
      items: [{ properties: { textSize: num(12), fontColor: color(C.ink) } }],
    },
    visualContainerObjects: {
      title: [{ properties: { show: bool(true), text: str(label), fontSize: num(12), bold: bool(true), fontColor: color(C.ink2) } }],
      background: [{ properties: { show: bool(true), color: color(C.white), transparency: num(0) } }],
      border: [{ properties: { show: bool(true), color: color(C.line), radius: num(6), width: num(1) } }],
      padding: [{ properties: { top: num(2), bottom: num(2), left: num(10), right: num(10) } }],
      spacing: [{ properties: { customizeSpacing: bool(true), spaceAbovePlotArea: num(4) } }],
      general: [{ properties: { altText: str(`${label} filter`) } }],
    },
    drillFilterOtherVisuals: true,
  };
  if (syncGroup) visual.syncGroup = { groupName: syncGroup, fieldChanges: true, filterChanges: true };
  // spacing.spaceAbovePlotArea only exists from visualContainer 2.14.0 (the version Desktop saves)
  return { ...container(name, { x, y: L.ctl.y, w: L.slicerW, h: L.ctl.h, z }, visual), $schema: SCHEMA_VC.replace(/\/\d+\.\d+\.\d+\//, "/2.14.0/") };
}

function noteTextbox(name, x, text) {
  return container(name, { x, y: L.ctl.y, w: L.slicerW, h: L.ctl.h, z: 310 }, {
    visualType: "textbox",
    objects: { general: [{ properties: { paragraphs: [{ textRuns: [{ value: text, textStyle: { fontFamily: "Segoe UI", fontSize: "10pt", color: C.ink2 } }] }] } }] },
    visualContainerObjects: {
      background: [{ properties: { show: bool(true), color: color(C.hover), transparency: num(0) } }],
      border: [{ properties: { show: bool(true), color: color(C.line), radius: num(6), width: num(1) } }],
      padding: [{ properties: { top: num(4), bottom: num(4), left: num(10), right: num(10) } }],
    },
    drillFilterOtherVisuals: true,
  });
}

function navigator(name) {
  const st = (id, props) => ({ properties: props, selector: { id } });
  return container(name, { x: L.nav.x, y: L.ctl.y, w: L.nav.w, h: L.ctl.h, z: 200 }, {
    visualType: "pageNavigator",
    objects: {
      layout: [{ properties: { cellPadding: lit("4L") } }],
      fill: [
        { properties: { show: bool(true), fillColor: color(C.white), transparency: num(0) } },
        st("default", { show: bool(true), fillColor: color(C.white), transparency: num(0) }),
        st("hover", { show: bool(true), fillColor: color(C.hover), transparency: num(0) }),
        st("selected", { show: bool(true), fillColor: color(C.navy), transparency: num(0) }),
      ],
      text: [
        { properties: { fontFamily: str("Segoe UI Semibold"), fontSize: num(11), fontColor: color(C.ink) } },
        st("default", { fontFamily: str("Segoe UI Semibold"), fontSize: num(11), fontColor: color(C.ink) }),
        st("hover", { fontColor: color(C.navy) }),
        st("selected", { fontColor: color(C.white), bold: bool(true) }),
      ],
      outline: [
        { properties: { show: bool(true), lineColor: color(C.line), weight: num(1) } },
        st("default", { show: bool(true), lineColor: color(C.line), weight: num(1) }),
        st("selected", { show: bool(true), lineColor: color(C.navy), weight: num(1) }),
      ],
      accentBar: [st("selected", { show: bool(true) })],
    },
    visualContainerObjects: {
      background: [{ properties: { show: bool(true), color: color(C.white), transparency: num(0) } }],
      border: [{ properties: { show: bool(true), color: color(C.lineSoft), radius: num(8), width: num(1) } }],
      padding: [{ properties: { top: num(6), bottom: num(6), left: num(8), right: num(8) } }],
      general: [{ properties: { altText: str("Page navigation") } }],
    },
    drillFilterOtherVisuals: true,
  });
}

// ---------- Formatting passes for existing visuals ----------
function getTitle(v) {
  try { return v.visual.visualContainerObjects.title[0].properties.text.expr.Literal.Value.replace(/^'|'$/g, "").replace(/''/g, "'"); } catch { return null; }
}

function setVco(v, key, props) {
  const vco = (v.visual.visualContainerObjects ||= {});
  vco[key] = [{ properties: { ...((vco[key] && vco[key][0] && vco[key][0].properties) || {}), ...props } }];
}

function styleChartChrome(v) {
  setVco(v, "background", { show: bool(true), color: color(C.white), transparency: num(0) });
  setVco(v, "border", { show: bool(true), color: color(C.lineSoft), radius: num(8), width: num(1) });
  const vco = v.visual.visualContainerObjects;
  if (vco.title) setVco(v, "title", { fontColor: color(C.ink), fontSize: num(13), fontFamily: str("Segoe UI Semibold") });
  if (vco.subTitle) setVco(v, "subTitle", { fontColor: color(C.muted), fontSize: num(12) });
  const t = getTitle(v);
  if (t) setVco(v, "general", { altText: str(t) });
}

function styleKpi(v) {
  v.position.y = L.kpiY; v.position.height = L.kpiH;
  const o = (v.visual.objects ||= {});
  o.value = [{ properties: { fontSize: num(26), fontFamily: str("Segoe UI Semibold"), fontColor: color(C.navy) }, selector: { id: "default" } }];
  o.label = [{ properties: { fontSize: num(11), fontFamily: str("Segoe UI"), fontColor: color(C.ink2) }, selector: { id: "default" } }];
  setVco(v, "background", { show: bool(true), color: color(C.white), transparency: num(0) });
  setVco(v, "border", { show: bool(true), color: color(C.lineSoft), radius: num(8), width: num(1) });
  const p = v.visual.query.queryState.Data.projections[0];
  setVco(v, "general", { altText: str(`KPI: ${p.nativeQueryRef}`) });
}

function styleTable(v) {
  const o = (v.visual.objects ||= {});
  o.columnHeaders = [{ properties: {
    fontSize: num(11), bold: bool(true), fontColor: color(C.white), backColor: color(C.navy),
    autoSizeColumnWidth: bool(true), columnAdjustment: str("growToFit"), wordWrap: bool(true),
  } }];
  o.values = [{ properties: {
    fontSize: num(11), fontColorPrimary: color(C.ink), backColorPrimary: color(C.white),
    fontColorSecondary: color(C.ink), backColorSecondary: color(C.band),
  } }];
  o.total = [{ properties: { fontSize: num(11), bold: bool(true), fontColor: color(C.ink), backColor: color(C.hover) } }];
  o.grid = [{ properties: { gridHorizontal: bool(true), gridHorizontalColor: color(C.lineSoft), rowPadding: num(4) } }];
  setVco(v, "stylePreset", { name: str("None") });
}

// Descriptive text columns that crowd the scorecards out of view (kept available via tooltips/slicers elsewhere)
const TABLE_DROP = {
  p1_vis04: ["dim_company.operating_archetype"],
  p3_vis04: ["dim_buyer.customer_segment"],
  p4_vis04: ["dim_supplier.supplier_type"],
  p5_vis04: ["dim_factory.product_specialization"],
  p6_vis04: ["dim_factory.production_technology"],
  p7_vis04: ["dim_factory.production_technology"],
};

// Short, scannable column headers (units stay in the visual title/subtitle)
const SHORT = {
  "Shipped FOB Revenue (USD)": "FOB Revenue", "Order Intake Value (USD)": "Order Intake",
  "Operational Gross Margin %": "Gross Margin %", "Production Line Efficiency %": "Line Efficiency %",
  "First-Pass Yield (FPY) %": "FPY %", "On-Time In-Full (OTIF) %": "OTIF %",
  "Average BDT/USD Exchange Rate": "BDT per USD", "CPI Inflation YoY %": "CPI YoY %",
  "Statutory Minimum Wage (BDT)": "Min. Wage (BDT)", "Shipped Revenue YoY Growth %": "Revenue YoY %",
  "Labour Cost per Garment (USD)": "Labour $/pc", "Shipped Quantity (PCS)": "Shipped Qty",
  "Average Selling Price (USD)": "ASP ($/pc)", "Order Cancellation Rate %": "Cancellation %",
  "Order Fulfilment Rate %": "Fulfilment %", "Total Procurement Value (USD)": "Procurement Spend",
  "Documented Delivery Value (USD)": "Delivered Value", "Supplier On-Time Delivery %": "On-Time %",
  "Avg Supplier Delay (Days)": "Avg Delay (days)", "Supplier Material Rejection Rate %": "Rejection %",
  "Purchase Price Variance (USD)": "Price Variance", "Closing Inventory Value (USD)": "Closing Inventory",
  "Slow & Obsolete Stock (90+ Days USD)": "Aged 90+ Days", "Slow & Obsolete Stock Share %": "Aged Share %",
  "Stockout Incident Rate %": "Stockout %", "Safety Stock Compliance %": "Safety Stock %",
  "Days Inventory Outstanding (DIO)": "DIO (days)", "Actual Good Output (PCS)": "Good Output (pcs)",
  "Plan vs Actual Attainment %": "Plan Attainment %", "Output per Labour Hour (PCS)": "Pcs per Labour Hr",
  "Machine Downtime Hours": "Downtime (hrs)", "Active Headcount": "Headcount",
  "Inspected Quantity (PCS)": "Inspected (pcs)", "AQL Defect Rate %": "Defect %",
  "Garment Rework Rate %": "Rework %", "Total Cost of Poor Quality (USD)": "Cost of Poor Quality",
  "On-Time Shipment (OTS) %": "OTS %", "On-Time Delivery (OTD) %": "OTD %",
  "Air Freight Revenue Share %": "Air Freight %", "Electricity per Garment (kWh)": "kWh per pc",
  "Renewable Solar Share %": "Solar %", "Water per Garment (Liters)": "Water (L/pc)",
  "Carbon Footprint (kg CO2e/PC)": "kg CO2e per pc", "Fabric Waste Recycling Rate %": "Recycling %",
};

function tidyTable(v, name) {
  const proj = v.visual.query.queryState.Values;
  const drop = TABLE_DROP[name] || [];
  proj.projections = proj.projections.filter((p) => !drop.includes(p.queryRef));
  for (const p of proj.projections) if (p.field.Measure && SHORT[p.field.Measure.Property]) p.displayName = SHORT[p.field.Measure.Property];
  const sort = v.visual.query.sortDefinition;
  if (sort) sort.sort = sort.sort.filter((s) => !drop.some((d) => JSON.stringify(s.field).includes(`"Property":"${d.split(".")[1]}"`)));
}

function setTitle(v, title, subtitle) {
  if (title) setVco(v, "title", { show: bool(true), text: str(title) });
  if (subtitle) setVco(v, "subTitle", { show: bool(true), text: str(subtitle) });
  setVco(v, "general", { altText: str(title || getTitle(v)) });
}

function swapProjection(v, oldProp, newProp) {
  for (const role of Object.values(v.visual.query.queryState)) {
    for (const p of role.projections) {
      if (p.field.Measure && p.field.Measure.Property === oldProp) {
        p.field.Measure.Property = newProp;
        p.queryRef = `Executive_Measures.${newProp}`;
        p.nativeQueryRef = newProp;
        delete p.displayName;
      }
    }
  }
}

// ---------- Main ----------
function main() {
  const pagesMeta = readJ(path.join(PAGES, "pages.json"));
  const log = [];

  for (const pageId of pagesMeta.pageOrder) {
    const plan = PLAN[pageId];
    if (!plan) { log.push(`skip unknown page ${pageId}`); continue; }
    const pdir = path.join(PAGES, pageId);
    const vdir = path.join(pdir, "visuals");
    const prefix = fs.readdirSync(vdir)[0].split("_")[0]; // e.g. p1

    if (!SCHEMA_VC) SCHEMA_VC = readJ(path.join(vdir, fs.readdirSync(vdir)[0], "visual.json")).$schema;

    // page.json: short nav-friendly names + accessible canvas colour
    const pj = readJ(path.join(pdir, "page.json"));
    pj.displayName = plan.nav;
    pj.objects = { background: [{ properties: { color: color(C.page), transparency: num(0) } }] };
    writeJ(path.join(pdir, "page.json"), pj);

    // remove header / control bar elements that get rebuilt
    for (const name of fs.readdirSync(vdir)) {
      if (/_(hdr\w*|slc\d+|nav\d+|logo|note\d*|period)$/.test(name)) fs.rmSync(path.join(vdir, name), { recursive: true, force: true });
    }

    const add = (v) => writeJ(path.join(vdir, v.name, "visual.json"), v);

    // header: logo | divider | page icon | title + subtitle | period note
    add(headerTextbox(`${prefix}_hdr01`, plan));
    add(imageVisual(`${prefix}_logo`, { x: 30, y: 20, w: 258, h: 68, z: 150 }, "nexora_logo.png", "Nexora Apparels Ltd. logo"));
    add(divider(`${prefix}_hdrdiv`, { x: 306, y: 26, w: 2, h: 56, z: 151 }, C.lineSoft));
    add(imageVisual(`${prefix}_hdricon`, { x: 324, y: 26, w: 56, h: 56, z: 152 }, plan.icon, `${plan.nav} section icon`));
    add(periodTextbox(`${prefix}_period`));

    // filters: Year (synced everywhere), Company (synced where relationships exist), page-specific
    add(slicer(`${prefix}_slc01`, L.slicerX[0], 300, "dim_date", "calendar_year", "Calendar Year", "NexoraYear"));
    add(slicer(`${prefix}_slc02`, L.slicerX[1], 301, "dim_company", "company_name", "Company", "NexoraCompany"));
    plan.slicers.forEach((f, i) => add(slicer(`${prefix}_slc0${i + 3}`, L.slicerX[i + 2], 302 + i, f.entity, f.prop, f.label, null)));
    if (plan.note) add(noteTextbox(`${prefix}_note1`, L.slicerX[plan.slicers.length + 2], plan.note));
    add(navigator(`${prefix}_nav01`));

    // restyle existing content visuals
    for (const name of fs.readdirSync(vdir)) {
      const f = path.join(vdir, name, "visual.json");
      const v = readJ(f);
      const t = v.visual.visualType;
      if (/_kpi\d+$/.test(name)) styleKpi(v);
      else if (/_kpiico\d+$/.test(name)) {
        v.position.y = L.kpiIcoY;
        setVco(v, "general", { altText: str("KPI icon") });
      } else if (/_vis\d+$/.test(name)) {
        if (v.position.y === 264 || v.position.y === 282) { v.position.y = L.row1.y; v.position.height = L.row1.h; }
        else if (v.position.y === 668) { v.position.y = L.row2.y; v.position.height = L.row2.h; }
        styleChartChrome(v);
        if (t === "tableEx") { styleTable(v); tidyTable(v, name); }
        // combo charts were bound to a non-existent "ColumnY" role, so columns never rendered
        const qs = v.visual.query && v.visual.query.queryState;
        if (qs && qs.ColumnY) { qs.Y = qs.ColumnY; delete qs.ColumnY; log.push(`${name}: ColumnY -> Y`); }
      } else continue;
      writeJ(f, v);
    }

    // page-specific analytical changes
    if (prefix === "p1") {
      // 7-slice donut -> ranked bar chart (easier to compare, colour-independent)
      const f = path.join(vdir, "p1_vis02", "visual.json");
      const v = readJ(f);
      v.visual.visualType = "clusteredBarChart";
      v.visual.objects = { labels: [{ properties: { show: bool(true), fontSize: num(10), color: color(C.ink) } }] };
      const yp = v.visual.query.queryState.Y.projections[0];
      v.visual.query.sortDefinition = { sort: [{ field: yp.field, direction: "Descending" }], isDefaultSort: false };
      writeJ(f, v);
      log.push("p1_vis02 donut -> clusteredBarChart");
    }
    if (prefix === "p5") {
      // Wastage is not filtered by stock type -> replace with DIO (inventory measure)
      const f = path.join(vdir, "p5_vis04", "visual.json");
      const v = readJ(f);
      swapProjection(v, "Material Wastage Cost (USD)", "Days Inventory Outstanding (DIO)");
      writeJ(f, v);
      log.push("p5_vis04 wastage -> DIO");
      const f3 = path.join(vdir, "p5_vis03", "visual.json");
      const v3 = readJ(f3);
      setTitle(v3, null, "Stock ageing profile: 61–90 days is slow-moving; 90+ days is excess / obsolescence risk");
      writeJ(f3, v3);
    }
    if (prefix === "p6") {
      // 26 factory names were unreadable when rotated -> compare the 8 companies instead
      const f = path.join(vdir, "p6_vis01", "visual.json");
      const v = readJ(f);
      const cat = v.visual.query.queryState.Category.projections[0];
      cat.field = col("dim_company", "company_name");
      cat.queryRef = "dim_company.company_name"; cat.nativeQueryRef = "company_name"; cat.displayName = "Company";
      const yp = v.visual.query.queryState.Y.projections[0];
      v.visual.query.sortDefinition = { sort: [{ field: yp.field, direction: "Descending" }], isDefaultSort: false };
      setTitle(v, "Good Output (PCS) & Line Efficiency % by Company", "Volume leaders vs. efficiency leaders — use the scorecard below for factory-level detail");
      writeJ(f, v);
      log.push("p6_vis01 factory -> company");
    }
    if (prefix === "p7") {
      // root-cause view should show late shipments only
      const f = path.join(vdir, "p7_vis02", "visual.json");
      const v = readJ(f);
      v.filterConfig = { filters: [{
        name: "fltLateOnly7a2c9e41b3d5",
        field: col("fact_shipment_line", "delay_reason"),
        type: "Categorical",
        filter: {
          Version: 2,
          From: [{ Name: "f", Entity: "fact_shipment_line", Type: 0 }],
          Where: [{ Condition: { Not: { Expression: { In: {
            Expressions: [{ Column: { Expression: { SourceRef: { Source: "f" } }, Property: "delay_reason" } }],
            Values: [[{ Literal: { Value: "'On-Time Delivery (No Delay)'" } }]],
          } } } } }],
        },
      }] };
      const yp = v.visual.query.queryState.Y.projections[0];
      v.visual.query.sortDefinition = { sort: [{ field: yp.field, direction: "Descending" }], isDefaultSort: false };
      setTitle(v, "Late Shipments: Volume & Freight Cost by Delay Root Cause", "Late shipments only (on-time shipments excluded) — where delivery reliability is lost");
      writeJ(f, v);
      log.push("p7_vis02 late-only filter");
      // defect axis rounded every tick to "0M"; show 1 decimal and start the cost axis at zero
      const f1 = path.join(vdir, "p7_vis01", "visual.json");
      const v1 = readJ(f1);
      v1.visual.objects = { ...(v1.visual.objects || {}), valueAxis: [{ properties: {
        labelDisplayUnits: num(1000000), labelPrecision: lit("1L"), secStart: num(0), secLabelDisplayUnits: num(1000000), secLabelPrecision: lit("1L"),
      } }] };
      writeJ(f1, v1);
    }
    if (prefix === "p8") {
      // waterfall: 14 squashed cost lines -> 8 P&L classifications
      const f1 = path.join(vdir, "p8_vis01", "visual.json");
      const v1 = readJ(f1);
      const c1 = v1.visual.query.queryState.Category.projections[0];
      c1.field = col("dim_cost_category", "income_statement_classification");
      c1.queryRef = "dim_cost_category.income_statement_classification"; c1.nativeQueryRef = "income_statement_classification"; c1.displayName = "P&L Line";
      const y1 = v1.visual.query.queryState.Y.projections[0];
      v1.visual.query.sortDefinition = { sort: [{ field: y1.field, direction: "Descending" }], isDefaultSort: false };
      setTitle(v1, "Total Cost Build-Up by P&L Line (USD)", "COGS (material, labour, overhead, quality, subcontract) plus selling, admin and finance costs");
      writeJ(f1, v1);
      // clustered cost bars -> stacked revenue decomposition (Material + Labour + Overhead + Margin = Revenue)
      const f3 = path.join(vdir, "p8_vis03", "visual.json");
      const v3 = readJ(f3);
      v3.visual.visualType = "barChart";
      v3.visual.objects = {};
      setTitle(v3, "Revenue Decomposition by Company (USD)", "Each bar = shipped FOB revenue split into material, labour, overhead and gross margin");
      writeJ(f3, v3);
      log.push("p8 waterfall + stacked decomposition");
    }
    log.push(`${pageId} (${prefix}) -> ${plan.nav}`);
  }

  // ---------- theme + resources ----------
  writeTheme();
  const rj = readJ(path.join(DEF, "report.json"));
  rj.themeCollection.customTheme = {
    name: THEME_NAME,
    reportVersionAtImport: rj.themeCollection.baseTheme.reportVersionAtImport,
    type: "RegisteredResources",
  };
  const reg = rj.resourcePackages.find((p) => p.type === "RegisteredResources");
  reg.items = reg.items.filter((i) => i.type !== "CustomTheme");
  const ensure = (name, type) => { if (!reg.items.some((i) => i.name === name)) reg.items.push({ name, path: name, type }); };
  ensure(THEME_NAME, "CustomTheme");
  ensure("nexora_logo.png", "Image");
  for (const p of Object.values(PLAN)) ensure(p.icon, "Image");
  writeJ(path.join(DEF, "report.json"), rj);

  console.log(log.join("\n"));
}

function writeTheme() {
  // Data colours: each >= 3:1 contrast on white (WCAG 1.4.11); blue/orange lead for colour-vision safety
  const theme = {
    name: THEME_NAME,
    dataColors: ["#1F5AA6", "#C2610C", "#3E8E2F", "#6A4C9C", "#0F7F81", "#B3365B", "#5B6770", "#8C6D1F", "#2F7FC1", "#7A3E00"],
    foreground: C.ink, foregroundNeutralSecondary: C.muted, foregroundNeutralTertiary: "#6B7280",
    background: C.white, backgroundLight: C.page, backgroundNeutral: C.lineSoft,
    tableAccent: C.navy, good: "#2E7D32", neutral: "#B26A00", bad: "#C62828",
    maximum: C.navy, center: "#7F9CC4", minimum: "#E8EEF6",
    textClasses: {
      callout: { fontSize: 32, fontFace: "Segoe UI Semibold", color: C.navy },
      title: { fontSize: 16, fontFace: "Segoe UI Semibold", color: C.ink },
      header: { fontSize: 14, fontFace: "Segoe UI Semibold", color: C.ink },
      label: { fontSize: 12, fontFace: "Segoe UI", color: C.ink2 },
    },
    visualStyles: {
      "*": {
        "*": {
          title: [{ fontColor: { solid: { color: C.ink } }, fontSize: 16, fontFamily: "Segoe UI Semibold" }],
          subTitle: [{ fontColor: { solid: { color: C.muted } }, fontSize: 12 }],
          background: [{ show: true, color: { solid: { color: C.white } }, transparency: 0 }],
          border: [{ show: true, color: { solid: { color: C.lineSoft } }, radius: 8 }],
          dropShadow: [{ show: false }],
          categoryAxis: [{ labelColor: { solid: { color: C.ink2 } }, fontSize: 12, titleColor: { solid: { color: C.ink2 } } }],
          valueAxis: [{ labelColor: { solid: { color: C.ink2 } }, fontSize: 12, titleColor: { solid: { color: C.ink2 } }, gridlineColor: { solid: { color: "#E5E7EB" } } }],
          legend: [{ labelColor: { solid: { color: C.ink2 } }, fontSize: 12, position: "Top" }],
          labels: [{ color: { solid: { color: C.ink } }, fontSize: 12 }],
        },
      },
      page: { "*": { background: [{ color: { solid: { color: C.page } }, transparency: 0 }] } },
    },
  };
  for (const f of fs.readdirSync(RES)) if (/^NexoraBrand-.*\.json$/.test(f)) fs.rmSync(path.join(RES, f));
  writeJ(path.join(RES, THEME_NAME), theme);
}

main();

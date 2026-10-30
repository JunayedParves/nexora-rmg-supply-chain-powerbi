"""
Generates 37 custom vector SVG icons for the Nexora Apparels Ltd. Executive Power BI Dashboard:
- 8 Executive Page Header Badges (Dark-theme glowing glass badges)
- 29 KPI Card Badges (Soft-tinted rounded badges with crisp vector paths)

Saves icons to:
1. c:\\Users\\Junayed\\Documents\\RMG Company\\dashboard_icons\\svg\\
2. c:\\Users\\Junayed\\Documents\\RMG Company\\Nexora Apparels Ltd. Dashboard.Report\\StaticResources\\RegisteredResources\\
3. Generates c:\\Users\\Junayed\\Documents\\RMG Company\\dashboard_icons\\ICON_GALLERY.html and ICON_CATALOG.md
"""

import json
import pathlib
import shutil

WORKSPACE_ROOT = pathlib.Path(r"c:\Users\Junayed\Documents\RMG Company")
ICONS_DIR = WORKSPACE_ROOT / "dashboard_icons"
SVG_DIR = ICONS_DIR / "svg"
REPORT_DIR = WORKSPACE_ROOT / "Nexora Apparels Ltd. Dashboard.Report"
REG_RES_DIR = REPORT_DIR / "StaticResources" / "RegisteredResources"


def make_page_badge_svg(accent_hex: str, glow_hex: str, inner_paths: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{accent_hex}" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="{glow_hex}" stop-opacity="0.12"/>
    </linearGradient>
  </defs>
  <rect x="2" y="2" width="60" height="60" rx="14" fill="url(#bgGrad)" stroke="{accent_hex}" stroke-width="2" stroke-opacity="0.75"/>
  <g fill="none" stroke="{glow_hex}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">
    {inner_paths}
  </g>
</svg>"""


def make_kpi_badge_svg(bg_hex: str, border_hex: str, stroke_hex: str, inner_paths: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <rect x="2" y="2" width="44" height="44" rx="12" fill="{bg_hex}" stroke="{border_hex}" stroke-width="1.5"/>
  <g fill="none" stroke="{stroke_hex}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    {inner_paths}
  </g>
</svg>"""


# Color Palettes (bg_hex, border_hex, stroke_hex)
PALETTES = {
    "emerald": ("#ECFDF5", "#A7F3D0", "#059669"),
    "blue": ("#EFF6FF", "#BFDBFE", "#2563EB"),
    "indigo": ("#EEF2FF", "#C7D2FE", "#4F46E5"),
    "teal": ("#F0FDFA", "#99F6E4", "#0D9488"),
    "amber": ("#FFFBEB", "#FDE68A", "#D97706"),
    "violet": ("#F5F3FF", "#DDD6FE", "#7C3AED"),
    "rose": ("#FFF1F2", "#FECDD3", "#E11D48"),
    "cyan": ("#F0F9FF", "#BAE6FD", "#0284C7"),
    "slate": ("#F8FAFC", "#CBD5E1", "#334155"),
}


PAGE_ICONS = {
    "page_01_executive.svg": (
        "Executive Command Center",
        "#38BDF8",
        "#7DD3FC",
        """<rect x="14" y="14" width="15" height="15" rx="3"/>
    <rect x="35" y="14" width="15" height="15" rx="3"/>
    <rect x="14" y="35" width="15" height="15" rx="3"/>
    <path d="M35 46 L41 39 L45 43 L51 35"/>
    <polyline points="46 35 51 35 51 40"/>""",
    ),
    "page_02_macro.svg": (
        "Macroeconomic & 20Y Structural Trends",
        "#818CF8",
        "#C7D2FE",
        """<circle cx="32" cy="32" r="18"/>
    <ellipse cx="32" cy="32" rx="8" ry="18"/>
    <line x1="14" y1="32" x2="50" y2="32"/>
    <path d="M17 22 H47"/>
    <path d="M17 42 H47"/>""",
    ),
    "page_03_commercial.svg": (
        "Commercial Demand, Buyers & Markets",
        "#34D399",
        "#A7F3D0",
        """<path d="M16 24 H48 L45 50 H19 Z"/>
    <path d="M24 24 V20 A8 8 0 0 1 40 20 V24"/>
    <path d="M26 36 L30 40 L39 31"/>""",
    ),
    "page_04_procurement.svg": (
        "Procurement & Supplier Reliability",
        "#FBBF24",
        "#FDE68A",
        """<ellipse cx="24" cy="32" rx="7" ry="14"/>
    <path d="M24 18 H44 C48 18 51 24 51 32 C51 40 48 46 44 46 H24"/>
    <circle cx="24" cy="32" r="2.5"/>
    <line x1="33" y1="25" x2="45" y2="25"/>
    <line x1="33" y1="32" x2="45" y2="32"/>
    <line x1="33" y1="39" x2="45" y2="39"/>""",
    ),
    "page_05_inventory.svg": (
        "Inventory & Working Capital",
        "#F59E0B",
        "#FDE68A",
        """<path d="M32 14 L50 24 V40 L32 50 L14 40 V24 Z"/>
    <path d="M14 24 L32 34 L50 24"/>
    <line x1="32" y1="34" x2="32" y2="50"/>
    <path d="M23 19 L41 29"/>""",
    ),
    "page_06_manufacturing.svg": (
        "Manufacturing Productivity & Workforce",
        "#A78BFA",
        "#DDD6FE",
        """<path d="M14 48 V26 L26 34 V26 L38 34 V18 H50 V48 Z"/>
    <line x1="10" y1="48" x2="54" y2="48"/>
    <rect x="22" y="40" width="6" height="8"/>
    <rect x="36" y="40" width="6" height="8"/>""",
    ),
    "page_07_quality.svg": (
        "Quality Assurance & OTIF Delivery",
        "#2DD4BF",
        "#99F6E4",
        """<path d="M32 13 L48 20 V31 C48 42 40 48 32 52 C24 48 16 42 16 31 V20 Z"/>
    <polyline points="24 32 30 38 41 26"/>""",
    ),
    "page_08_sustainability.svg": (
        "Financial Cost Bridge & ESG Sustainability",
        "#4ADE80",
        "#BBF7D0",
        """<path d="M18 46 C18 28 30 16 48 16 C48 34 38 46 20 46 Z"/>
    <path d="M16 48 C24 40 32 32 42 24"/>""",
    ),
}


KPI_ICONS = {
    "kpi_revenue_usd.svg": (
        "Shipped FOB Revenue (USD)",
        "emerald",
        """<circle cx="24" cy="24" r="13"/>
    <path d="M24 16 V32"/>
    <path d="M28 19.5 C28 17.8 26.2 17 24 17 C21.8 17 20 17.8 20 19.8 C20 22 28 21.8 28 25 C28 27.2 26.2 28 24 28 C21.5 28 20 27 20 25.5"/>""",
    ),
    "kpi_order_intake.svg": (
        "Order Intake Value (USD)",
        "blue",
        """<rect x="14" y="12" width="20" height="26" rx="3"/>
    <path d="M19 12 V10 H29 V12"/>
    <line x1="19" y1="20" x2="29" y2="20"/>
    <line x1="19" y1="25" x2="29" y2="25"/>
    <polyline points="19 31 22 34 29 28"/>""",
    ),
    "kpi_gross_margin.svg": (
        "Operational Gross Margin %",
        "indigo",
        """<polyline points="12 32 20 24 26 29 36 17"/>
    <polyline points="29 17 36 17 36 24"/>
    <line x1="12" y1="36" x2="36" y2="36"/>""",
    ),
    "kpi_otif_delivery.svg": (
        "On-Time In-Full (OTIF) %",
        "teal",
        """<rect x="10" y="16" width="18" height="14" rx="2"/>
    <path d="M28 20 H34 L38 25 V30 H28 Z"/>
    <circle cx="16" cy="33" r="3"/>
    <circle cx="33" cy="33" r="3"/>
    <polyline points="15 23 18 26 23 20"/>""",
    ),
    "kpi_inventory_val.svg": (
        "Closing Inventory Value",
        "amber",
        """<path d="M24 11 L37 18.5 V31.5 L24 39 L11 31.5 V18.5 Z"/>
    <path d="M11 18.5 L24 26 L37 18.5"/>
    <line x1="24" y1="26" x2="24" y2="39"/>""",
    ),
    "kpi_good_output.svg": (
        "Actual Good Output (PCS)",
        "violet",
        """<path d="M17 13 L21 16 H27 L31 13 L38 18 L34 24 L31 22 V36 H17 V22 L14 24 L10 18 Z"/>
    <polyline points="21 26 23.5 28.5 28 23.5"/>""",
    ),
    "kpi_yoy_growth.svg": (
        "Shipped Revenue YoY Growth %",
        "emerald",
        """<line x1="14" y1="35" x2="14" y2="27"/>
    <line x1="21" y1="35" x2="21" y2="22"/>
    <line x1="28" y1="35" x2="28" y2="18"/>
    <line x1="35" y1="35" x2="35" y2="13"/>
    <polyline points="13 21 24 13 35 13"/>""",
    ),
    "kpi_asp_price.svg": (
        "Average Selling Price (USD)",
        "blue",
        """<path d="M13 25 L25 13 H35 V23 L23 35 Z"/>
    <circle cx="30" cy="18" r="2"/>
    <line x1="19" y1="26" x2="22" y2="29"/>""",
    ),
    "kpi_fx_rate.svg": (
        "Average BDT/USD Exchange Rate",
        "cyan",
        """<path d="M13 19 H34"/>
    <polyline points="29 14 34 19 29 24"/>
    <path d="M35 29 H14"/>
    <polyline points="19 24 14 29 19 34"/>""",
    ),
    "kpi_min_wage.svg": (
        "Statutory Minimum Wage (BDT)",
        "amber",
        """<ellipse cx="24" cy="16" rx="10" ry="4"/>
    <path d="M14 16 V24 C14 26.2 18.5 28 24 28 C29.5 28 34 26.2 34 24 V16"/>
    <path d="M14 24 V32 C14 34.2 18.5 36 24 36 C29.5 36 34 34.2 34 32 V24"/>""",
    ),
    "kpi_bgmea_export.svg": (
        "BGMEA National RMG Export ($B)",
        "indigo",
        """<circle cx="24" cy="24" r="13"/>
    <ellipse cx="24" cy="24" rx="5.5" ry="13"/>
    <line x1="11" y1="24" x2="37" y2="24"/>
    <line x1="13" y1="18" x2="35" y2="18"/>
    <line x1="13" y1="30" x2="35" y2="30"/>""",
    ),
    "kpi_freight_idx.svg": (
        "Container Freight Index",
        "slate",
        """<path d="M11 28 L14 35 H34 L37 28 L24 24 Z"/>
    <rect x="16" y="16" width="16" height="9" rx="1"/>
    <line x1="24" y1="16" x2="24" y2="25"/>
    <path d="M10 38 C14 36 18 40 24 38 C30 36 34 40 38 38"/>""",
    ),
    "kpi_order_qty.svg": (
        "Ordered Quantity (PCS)",
        "blue",
        """<polygon points="24 12 36 18 24 24 12 18"/>
    <polyline points="12 24 24 30 36 24"/>
    <polyline points="12 30 24 36 36 30"/>""",
    ),
    "kpi_backlog.svg": (
        "Unfulfilled Order Backlog (PCS)",
        "amber",
        """<path d="M16 12 H32"/>
    <path d="M16 36 H32"/>
    <path d="M18 12 V18 L24 24 L18 30 V36"/>
    <path d="M30 12 V18 L24 24 L30 30 V36"/>""",
    ),
    "kpi_cancellation.svg": (
        "Order Cancellation Rate %",
        "rose",
        """<circle cx="24" cy="24" r="13"/>
    <line x1="19" y1="19" x2="29" y2="29"/>
    <line x1="29" y1="19" x2="19" y2="29"/>""",
    ),
    "kpi_fulfilment.svg": (
        "Order Fulfilment Rate %",
        "emerald",
        """<circle cx="24" cy="24" r="13"/>
    <polyline points="18 24.5 22.5 29 31 19.5"/>""",
    ),
    "kpi_procurement.svg": (
        "Total Procurement Value (USD)",
        "indigo",
        """<circle cx="19" cy="35" r="2.5"/>
    <circle cx="31" cy="35" r="2.5"/>
    <path d="M11 14 H15 L18 29 H33 L36 18 H16"/>""",
    ),
    "kpi_import_share.svg": (
        "Imported Procurement Share %",
        "cyan",
        """<path d="M12 29 L15 36 H33 L36 29 Z"/>
    <rect x="17" y="20" width="14" height="9" rx="1"/>
    <path d="M24 12 V20"/>
    <polyline points="20 16 24 12 28 16"/>""",
    ),
    "kpi_supplier_otd.svg": (
        "Supplier On-Time Delivery %",
        "teal",
        """<circle cx="24" cy="24" r="13"/>
    <polyline points="24 16 24 24 30 27"/>""",
    ),
    "kpi_rejection.svg": (
        "Material / Garment Defect Rate %",
        "rose",
        """<path d="M24 12 L37 35 H11 Z"/>
    <line x1="24" y1="21" x2="24" y2="27"/>
    <circle cx="24" cy="31" r="1"/>""",
    ),
    "kpi_delay_days.svg": (
        "Average Supplier Delay (Days)",
        "amber",
        """<rect x="12" y="14" width="24" height="22" rx="3"/>
    <line x1="18" y1="11" x2="18" y2="16"/>
    <line x1="30" y1="11" x2="30" y2="16"/>
    <line x1="12" y1="20" x2="36" y2="20"/>
    <polyline points="24 24 24 29 28 29"/>""",
    ),
    "kpi_wastage_cost.svg": (
        "Material Wastage / COPQ Cost",
        "rose",
        """<circle cx="17" cy="18" r="4"/>
    <circle cx="17" cy="30" r="4"/>
    <line x1="20" y1="20" x2="35" y2="32"/>
    <line x1="20" y1="28" x2="35" y2="16"/>""",
    ),
    "kpi_turnover_dio.svg": (
        "Inventory Turnover & DIO",
        "blue",
        """<path d="M35 21 A12 12 0 0 0 14 17"/>
    <polyline points="14 12 14 18 20 18"/>
    <path d="M13 27 A12 12 0 0 0 34 31"/>
    <polyline points="34 36 34 30 28 30"/>""",
    ),
    "kpi_stockout.svg": (
        "Stockout Incident Rate %",
        "rose",
        """<path d="M24 11 L36 18 V30 L24 37 L12 30 V18 Z"/>
    <line x1="24" y1="19" x2="24" y2="25"/>
    <circle cx="24" cy="29" r="1"/>""",
    ),
    "kpi_safety_stock.svg": (
        "Safety Stock Compliance %",
        "emerald",
        """<path d="M24 11 L36 16 V24 C36 31.5 30.5 36.5 24 39 C17.5 36.5 12 31.5 12 24 V16 Z"/>
    <polyline points="19 24.5 22.5 28 30 20.5"/>""",
    ),
    "kpi_attainment.svg": (
        "Plan vs Actual Attainment %",
        "teal",
        """<circle cx="24" cy="24" r="13"/>
    <circle cx="24" cy="24" r="7"/>
    <circle cx="24" cy="24" r="2"/>""",
    ),
    "kpi_efficiency.svg": (
        "Production Line Efficiency %",
        "indigo",
        """<path d="M12 31 A13 13 0 1 1 36 31"/>
    <line x1="24" y1="28" x2="31" y2="19"/>
    <circle cx="24" cy="28" r="2.5"/>""",
    ),
    "kpi_labour_prod.svg": (
        "Output per Labour Hour (PCS)",
        "blue",
        """<circle cx="24" cy="26" r="11"/>
    <line x1="24" y1="11" x2="24" y2="15"/>
    <line x1="20" y1="11" x2="28" y2="11"/>
    <polyline points="24 21 24 26 28 28"/>""",
    ),
    "kpi_labour_cost.svg": (
        "Labour Cost per Garment (USD)",
        "amber",
        """<circle cx="20" cy="18" r="5"/>
    <path d="M12 34 C12 28.5 15.5 25 20 25 C24.5 25 28 28.5 28 34"/>
    <path d="M33 20 V32"/>
    <path d="M36 22 C36 20.5 31 20.5 31 23.5 C31 26.5 36 26.5 36 29.5 C36 32 31 32 31 30"/>""",
    ),
    "kpi_headcount.svg": (
        "Active Workforce Headcount",
        "violet",
        """<circle cx="19" cy="18" r="4.5"/>
    <path d="M11 34 C11 29 14.5 26 19 26 C23.5 26 27 29 27 34"/>
    <circle cx="30" cy="19" r="3.5"/>
    <path d="M29 26 C33 26 36.5 28.5 37 34"/>""",
    ),
    "kpi_fpy_quality.svg": (
        "First-Pass Yield (FPY) %",
        "emerald",
        """<circle cx="24" cy="20" r="9"/>
    <polyline points="20 28 17 37 24 34 31 37 28 28"/>
    <polyline points="20.5 20 23 22.5 28 17.5"/>""",
    ),
    "kpi_rework.svg": (
        "Garment Rework Rate %",
        "amber",
        """<path d="M15 24 A9 9 0 0 1 31 18"/>
    <polyline points="31 13 31 19 25 19"/>
    <path d="M33 24 A9 9 0 0 1 17 30"/>
    <polyline points="17 35 17 29 23 29"/>""",
    ),
    "kpi_ots_ship.svg": (
        "On-Time Shipment (OTS) %",
        "cyan",
        """<path d="M12 27 L15 34 H33 L36 27 L24 23 Z"/>
    <path d="M18 24 V16 H30 V24"/>
    <polyline points="21 19 23.5 21.5 28 17"/>""",
    ),
    "kpi_cogs_cost.svg": (
        "Total Production Cost (COGS USD)",
        "slate",
        """<rect x="13" y="12" width="22" height="24" rx="2"/>
    <line x1="17" y1="18" x2="31" y2="18"/>
    <line x1="17" y1="24" x2="25" y2="24"/>
    <line x1="17" y1="30" x2="25" y2="30"/>
    <circle cx="29" cy="28" r="2.5"/>""",
    ),
    "kpi_electricity.svg": (
        "Electricity per Garment (kWh)",
        "amber",
        """<polygon points="26 11 14 26 23 26 21 37 34 22 25 22"/>""",
    ),
    "kpi_solar_share.svg": (
        "Renewable Solar Share %",
        "emerald",
        """<circle cx="24" cy="17" r="4"/>
    <line x1="24" y1="10" x2="24" y2="11"/>
    <line x1="17" y1="17" x2="18" y2="17"/>
    <line x1="30" y1="17" x2="31" y2="17"/>
    <polygon points="15 26 33 26 36 36 12 36"/>
    <line x1="24" y1="26" x2="24" y2="36"/>
    <line x1="13.5" y1="31" x2="34.5" y2="31"/>""",
    ),
    "kpi_carbon_co2.svg": (
        "Carbon Footprint (kg CO2e/PC)",
        "teal",
        """<path d="M15 34 C15 22 23 13 35 13 C35 25 28 34 16 34 Z"/>
    <path d="M14 35 C20 29 25 24 31 19"/>""",
    ),
}


def main():
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    REG_RES_DIR.mkdir(parents=True, exist_ok=True)

    registered_items = []
    catalog_rows = []

    # 1. Generate Page Header Icons
    for filename, (title, accent, glow, paths) in PAGE_ICONS.items():
        svg_content = make_page_badge_svg(accent, glow, paths)
        (SVG_DIR / filename).write_text(svg_content, encoding="utf-8")
        (REG_RES_DIR / filename).write_text(svg_content, encoding="utf-8")
        registered_items.append({"name": filename, "path": filename, "type": "Image"})
        catalog_rows.append((filename, "Page Header Badge (64x64)", title, accent))

    # 2. Generate KPI Card Icons
    for filename, (title, pal_name, paths) in KPI_ICONS.items():
        bg_hex, border_hex, stroke_hex = PALETTES[pal_name]
        svg_content = make_kpi_badge_svg(bg_hex, border_hex, stroke_hex, paths)
        (SVG_DIR / filename).write_text(svg_content, encoding="utf-8")
        (REG_RES_DIR / filename).write_text(svg_content, encoding="utf-8")
        registered_items.append({"name": filename, "path": filename, "type": "Image"})
        catalog_rows.append((filename, f"KPI Card Badge (48x48, {pal_name.title()})", title, stroke_hex))

    # 3. Update report.json with RegisteredResources package
    report_json_path = REPORT_DIR / "definition" / "report.json"
    report_data = json.loads(report_json_path.read_text(encoding="utf-8"))
    res_pkgs = [p for p in report_data.get("resourcePackages", []) if p.get("name") != "RegisteredResources"]
    res_pkgs.append(
        {
            "name": "RegisteredResources",
            "type": "RegisteredResources",
            "items": registered_items,
        }
    )
    report_data["resourcePackages"] = res_pkgs
    report_json_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")

    # 4. Generate ICON_CATALOG.md and ICON_GALLERY.html
    md_lines = [
        "# Nexora Apparels Ltd. — Executive Power BI Dashboard Icon Catalog",
        "",
        f"Total Custom Vector Icons Generated: **{len(catalog_rows)}** (`8` Page Header Badges + `{len(KPI_ICONS)}` KPI Card Badges).",
        "",
        "- **Standalone SVG Folder**: `c:\\Users\\Junayed\\Documents\\RMG Company\\dashboard_icons\\svg\\`",
        "- **Power BI Registered Resources Folder**: `c:\\Users\\Junayed\\Documents\\RMG Company\\Nexora Apparels Ltd. Dashboard.Report\\StaticResources\\RegisteredResources\\`",
        "",
        "| Icon File | Category | Dashboard Metric / Page | Primary Color |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for fn, cat, desc, col in catalog_rows:
        md_lines.append(f"| `{fn}` | {cat} | {desc} | `{col}` |")
    (ICONS_DIR / "ICON_CATALOG.md").write_text("\n".join(md_lines), encoding="utf-8")

    html_cards = []
    for fn, cat, desc, col in catalog_rows:
        svg_inline = (SVG_DIR / fn).read_text(encoding="utf-8")
        dark_cls = "dark-card" if fn.startswith("page_") else "light-card"
        html_cards.append(
            f"""<div class="card {dark_cls}">
                <div class="icon-wrap">{svg_inline}</div>
                <div class="meta">
                    <div class="title">{desc}</div>
                    <div class="fn">{fn}</div>
                    <div class="cat">{cat}</div>
                </div>
            </div>"""
        )

    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Nexora Apparels Power BI Icon Gallery</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; background: #F1F5F9; color: #0F172A; margin: 32px; }}
  h1 {{ margin-bottom: 4px; }}
  p.sub {{ color: #475569; margin-top: 0; margin-bottom: 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
  .card {{ display: flex; align-items: center; gap: 16px; padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0; background: #FFFFFF; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
  .card.dark-card {{ background: #0F172A; color: #FFFFFF; border-color: #1E293B; }}
  .card.dark-card .fn, .card.dark-card .cat {{ color: #94A3B8; }}
  .title {{ font-weight: 600; font-size: 14px; margin-bottom: 4px; }}
  .fn {{ font-family: Consolas, monospace; font-size: 12px; color: #2563EB; }}
  .cat {{ font-size: 11px; color: #64748B; margin-top: 2px; }}
</style>
</head>
<body>
  <h1>Nexora Apparels Ltd. — Power BI Executive Icon Pack ({len(catalog_rows)} Icons)</h1>
  <p class="sub">All icons are embedded directly into your Power BI Report (<code>RegisteredResources</code>) and saved in <code>dashboard_icons/svg/</code>.</p>
  <div class="grid">
    {''.join(html_cards)}
  </div>
</body>
</html>"""
    (ICONS_DIR / "ICON_GALLERY.html").write_text(html_doc, encoding="utf-8")
    print(f"Generated {len(catalog_rows)} SVG icons in {SVG_DIR} and registered them in report.json!")


if __name__ == "__main__":
    main()

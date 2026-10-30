# Power BI 12-Page Executive & Operational Report Architecture

Each page of the Power BI solution is structured around a concrete **management question**, explicit **KPI cards**, **visual layouts**, **drill-through paths**, and **decision-support actions**.

---

## Page 1: Executive Intelligence Command Center
- **Management Question**: *How is the manufacturing group performing across revenue, operational margin, order backlog, working capital exposure, and customer delivery reliability?*
- **Primary KPIs**: `Order Intake Value (USD/BDT)`, `Shipped FOB Revenue`, `Operational Gross Margin %`, `On-Time In-Full (OTIF) %`, `Closing Inventory Value`, `Unfulfilled Order Backlog (PCS)`.
- **Recommended Visuals**:
  1. Top KPI Ribbon with YoY & Fiscal-Year (`FY July–June`) sparklines and currency toggle (`BDT` / `USD`).
  2. Combo Line & Clustered Column Chart: Monthly Shipped FOB Revenue vs. Operational Gross Margin % (2006–2025).
  3. Matrix with Conditional Formatting Bars: Company Archetype Benchmark (`PADMA`, `MEGHNA`, `KARNAPHULI`, `JAMUNA`, `BRAHMAPUTRA`, `SURMA`, `TEESTA`, `DHALESWARI`).
  4. Top Management Exceptions Table: Late high-value orders, stockout alerts, and low-FPY lines.
- **Drill-Through Dimensions**: `dim_company[company_name]`, `dim_factory[factory_name]`, `dim_date[fiscal_year]`.

---

## Page 2: Twenty-Year Industry & Macroeconomic Trends (2006–2025)
- **Management Question**: *How have Bangladesh's structural transformations (knitwear crossover, 5 statutory minimum wage jumps, 2013 safety remediation, 2020 COVID shock, and 2022–2025 FX/energy crisis) impacted our top and bottom lines?*
- **Primary KPIs**: `Shipped FOB Revenue (USD)`, `BGMEA National RMG Export Benchmark ($B)`, `BDT/USD Exchange Rate`, `Statutory Entry Minimum Wage (BDT)`, `Industrial Energy Tariff Index`.
- **Recommended Visuals**:
  1. Annotated 20-Year Area Chart with Shock Regime Shading (`GFC 2008–09`, `Post-Rana Plaza 2013`, `COVID-19 2020`, `2021–22 Freight Boom`, `2022–25 FX & Gas Shock`).
  2. 100% Stacked Area Chart: Knitwear vs. Woven vs. MMF Activewear Revenue Share (showing the post-FY14 knitwear & MMF rise).
  3. Dual-Axis Line Chart: Statutory Minimum Wage Revisions (`1,662.50 -> 3,000 -> 5,300 -> 8,000 -> 12,500 BDT`) vs. Output per Labour Hour (`PCS/Hr`).

---

## Page 3: Sales, Market Diversification & Customer Intelligence
- **Management Question**: *Which buyers, product categories, and export markets drive profitable growth, and where is our buyer concentration or cancellation risk highest?*
- **Primary KPIs**: `Order Intake Value`, `Average Selling Price (ASP)`, `Top 5 Buyer Concentration %`, `Order Cancellation Rate %`, `Non-Traditional Market Share %`.
- **Recommended Visuals**:
  1. Pareto (80/20) Combo Chart of the 52 International Buyers by FOB Revenue and Cumulative Share %.
  2. Filled Map / Decomposition Tree: Traditional (`EU`, `USA`, `UK`, `Canada`) vs. Non-Traditional Markets (`Japan`, `Australia`, `India`, `Turkiye`, `South Korea`, `UAE`).
  3. Scatter Plot: Buyer Volume (`Shipped PCS`) vs. `Operational Contribution Margin %`, sized by `Order Cancellation Rate %`.

---

## Page 4: Procurement & Supplier Performance
- **Management Question**: *How reliable and cost-effective are our domestic backward-linkage mills versus imported fabric/yarn suppliers in China, India, and Pakistan?*
- **Primary KPIs**: `Total Procurement Value`, `Imported Procurement Share %`, `Supplier OTD Rate %`, `Supplier Material Rejection Rate %`, `Average Procurement Lead Time (Days)`, `Purchase Price Variance (PPV)`.
- **Recommended Visuals**:
  1. Clustered Bar Chart: Domestic Back-to-Back L/C vs. Direct Bonded Import Lead Times & OTD Rates.
  2. Supplier Risk Quadrant Scatter Plot: `Average Lead Time (Days)` vs. `Supplier OTD Rate %`, colored by `Supplier Rejection Rate %`.
  3. Ribbon Chart: Raw Material Unit Cost Evolution (`Cotton Yarn`, `Woven Poplin`, `Indigo Denim`, `MMF Tricot`, `Reactive Dyes`).

---

## Page 5: Inventory & Working Capital Diagnostics
- **Management Question**: *Where is working capital trapped in slow-moving or aged raw materials and finished goods, and which critical materials face stockout risk?*
- **Primary KPIs**: `Closing Inventory Value (USD/BDT)`, `Inventory Turnover Ratio`, `Days Inventory Outstanding (DIO)`, `Slow-Moving & Aged Share (60+ Days) %`, `Stockout Incident Rate %`.
- **Recommended Visuals**:
  1. Stacked Column Chart: Monthly Inventory Valuation split by `Raw Material`, `Work in Progress (WIP)`, and `Finished Goods (FG)`.
  2. Ageing Waterfall / Matrix: Inventory Value across `0–30 Days`, `31–60 Days`, `61–90 Days`, and `90+ Days` buckets by Factory.
  3. Critical Material Stockout Heatmap: `dim_material[material_name]` vs. `dim_factory[factory_code]`.

---

## Page 6: Manufacturing Productivity & Capacity Utilization
- **Management Question**: *Which factories and production lines achieve the highest SMV line efficiency and output per labour hour, and where does capacity utilization trigger excessive overtime?*
- **Primary KPIs**: `Actual Good Output (PCS)`, `Capacity Utilization %`, `Production Line Efficiency %`, `Output per Labour Hour`, `Labour Cost per Garment`, `Machine Downtime Hours`.
- **Recommended Visuals**:
  1. Small Multiples / Box-and-Whisker Plot: Line Efficiency % across all 26 Factories and 8 Companies.
  2. Scatter Plot: `Capacity Utilization %` vs. `Overtime Expense % of Payroll` (highlighting bottleneck thresholds above 92% utilization).
  3. Line Chart: 20-Year Productivity Evolution (Computerized Jacquard & Automated Cutting adoption in `SURMA`, `TEESTA`, and `PADMA` vs. legacy manual lines in `DHALESWARI`).

---

## Page 7: Product Quality, Rework & Compliance
- **Management Question**: *What are the primary root causes of garment defects and rework across styles and lines, and what is our total Cost of Poor Quality (COPQ)?*
- **Primary KPIs**: `First-Pass Yield (FPY) %`, `Defect Rate %`, `Garment Rework Rate %`, `Garment Rejection Rate %`, `Total Cost of Poor Quality (COPQ USD)`.
- **Recommended Visuals**:
  1. Pareto Chart of Defect Categories (`Stitching`, `Measurement Out-of-Tolerance`, `Fabric Shade Variation`, `Oil Stain`, `Puckering`, `Trim Defect`, `Needle Hole`).
  2. Matrix: Factory & Line `First-Pass Yield %` vs. `Manufacturing Complexity` (`Low`, `Medium`, `High`, `Very High`).
  3. Dual Line Chart: Schedule Delay / Overtime Pressure vs. Defect Rate %.

---

## Page 8: Shipment, Port Logistics & Customer Delivery
- **Management Question**: *Why do shipments miss buyer delivery windows, how much are emergency air-freight shipments costing us, and how does Chattogram EPZ compare to Dhaka-corridor factories?*
- **Primary KPIs**: `On-Time Shipment (OTS) %`, `On-Time Delivery (OTD) %`, `On-Time In-Full (OTIF) %`, `Avg Order-to-Shipment Lead Time`, `Avg Transit Time`, `Freight Cost per Unit`.
- **Recommended Visuals**:
  1. Breakdown Bar Chart: Late Delivery Root Causes (`Raw Material & Production Bottleneck`, `Global Container Shortage`, `COVID-19 Lockdown`, `Red Sea Rerouting`, `Customs & Inland Congestion`).
  2. Sea vs. Air Freight Cost & Volume Trend (highlighting the 2021–2022 container crisis and 2024 Red Sea surcharges).
  3. Corridor Comparison: `Karnaphuli (CEPZ Chattogram)` vs. `Gazipur / Savar / Mymensingh` factory-to-port inland transit days.

---

## Page 9: Financial Performance, Unit Economics & Margin Bridge
- **Management Question**: *How do unit selling prices, direct material costs, wage hikes, utility tariff increases, and BDT/USD depreciation decompose into company and style profitability?*
- **Primary KPIs**: `Shipped FOB Revenue`, `Total Production Cost (COGS)`, `Operational Gross Margin %`, `Operational Contribution Margin %`, `Total Conversion Cost per Garment`.
- **Recommended Visuals**:
  1. Waterfall Chart (Margin Bridge): `Gross Order Value -> Discounts -> FOB Revenue -> Direct Materials & Trims -> Direct Labour -> Factory Utilities & Overhead -> Operational Gross Margin -> Logistics & Finance -> Net Operational Margin`.
  2. Unit Economics Stacked Bar by Garment Category (`Basic Tee`, `Pique Polo`, `Woven Shirt`, `Chino`, `Stretch Denim`, `Jacquard Sweater`, `MMF Waterproof Jacket`).
  3. Currency Sensitivity Chart: BDT Revenue tailwinds vs. Imported Fabric USD Cost headwinds during the 2022–2025 Taka depreciation.

---

## Page 10: Sustainability, Energy & Environmental Efficiency
- **Management Question**: *How effectively are our factories reducing electricity, natural gas, water intensity, and carbon emissions per garment?*
- **Primary KPIs**: `Electricity per Garment (kWh/PC)`, `Natural Gas per Garment (m3/PC)`, `Water Withdrawal (Liters/PC)`, `Renewable Solar Share %`, `Waste Recycling Rate %`, `Carbon Footprint (kg CO2e/PC)`.
- **Recommended Visuals**:
  1. Benchmark Bar Chart: `Carbon Footprint (kg CO2e/PC)` and `Water Withdrawal (Liters/PC)` across Eco-Design Benchmark factories (`JAMUNA`, `FAC-04`, `FAC-09`, `FAC-12`) vs. conventional wet-processing units.
  2. Area Chart: Rooftop Solar (`renewable_solar_kwh`) adoption and Fabric Waste Recycling Rate (2006–2025).
  3. Utility Tariff Impact Chart: Industrial Gas (`BDT/m3`) and Electricity (`BDT/kWh`) unit cost escalation (2022–2025).

---

## Page 11: Forecasting & Scenario Sensitivity Analysis
- **Management Question**: *What is our projected 12-month demand, capacity requirement, and margin sensitivity to future wage increases, BDT/USD shifts, cotton inflation, or energy hikes?*
- **Primary KPIs**: `Forecasted Order Demand (PCS)`, `Projected Capacity Gap (PCS)`, `Simulated Gross Margin % under Stress Scenarios`.
- **Recommended Visuals**:
  1. Time-Series Forecast Chart (Train: 2006–2023, Holdout Test: 2024–2025) with 95% confidence bands.
  2. What-If Parameter Sliders:
     - `Raw Material Price Shock (-15% to +25%)`
     - `BDT/USD Exchange Rate Shift (110 to 135 BDT/USD)`
     - `Wage Increment (+0% to +20%)`
     - `Utility Tariff Hike (+0% to +35%)`
  3. Scenario Matrix showing impact on each of the 8 companies' operational margins.

---

## Page 12: Data Quality, Reconciliation & Audit Exceptions
- **Management Question**: *Do all supply chain quantities and financial ledgers reconcile cleanly across orders, batches, shipments, and inventory snapshots?*
- **Primary KPIs**: `Order-to-Shipment Variance (0 PCS)`, `Inventory Equation Discrepancy (0 Rows)`, `Unfulfilled Open Backlog Lines`, `Supplier Short-Shipped PO Lines`.
- **Recommended Visuals**:
  1. Automated Reconciliation Scorecard (displaying live `0` variance checks across Sales, Production, Shipments, and Inventory).
  2. Exception Drill-Through Table of Partial Shipments, Short-Closed POs, and High-Wastage Production Batches (`wastage_rate_pct > 11%`).

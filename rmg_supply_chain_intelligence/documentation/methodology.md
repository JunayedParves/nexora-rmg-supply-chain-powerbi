# Synthetic Data Generation & Historical Calibration Methodology

## 1. Research-Backed Calibration Philosophy

Rather than applying static probabilities across 2006–2025, the generation pipeline (`generate_macro_context.py`, `generate_dimensions.py`, `generate_facts.py`) embeds a **time-varying structural econometrics model** calibrated to official Bangladesh Ready-Made Garment (RMG) statistics:

1. **National Export Trajectory & Knitwear-Woven Crossover**:
   - Sourced from BGMEA and Export Promotion Bureau (EPB) data, national RMG exports grew nearly 5-fold from **\$7.90B in FY2005–06** to **\$39.35B in FY2024–25**.
   - Around **FY2013–14**, knitwear exports structurally overtook woven exports due to domestic spinning and knitting backward-linkage expansion. Our 8 synthetic companies mirror this structural shift, scaling combined order intake and shipments from ~\$95M in 2006 to ~\$520M in 2025 (~1.3% national share).

2. **Exact Statutory Minimum Wage Gazette Dates**:
   - Garment sector minimum wage revisions do **not** occur on 1 January. The pipeline implements exact historical effective dates:
     - Prior to 22 Oct 2006: **BDT 930** statutory baseline (modeled transitional market floor **BDT 1,550**).
     - Effective **22 October 2006**: **BDT 1,662.50** (Grade 7 entry).
     - Effective **1 November 2010**: **BDT 3,000.00** (Basic 2,000 + House Rent 800 + Medical 200).
     - Effective **1 December 2013**: **BDT 5,300.00** (post-Rana Plaza wage board revision).
     - Effective **1 December 2018**: **BDT 8,000.00** (`S.R.O. No. 345-Law/2018`).
     - Effective **1 December 2023**: **BDT 12,500.00** (condensed 5-grade structure, entry Grade 4).
   - Worker grades (Grades 2 through 5) earn realistic skill multipliers (`1.02x` to `1.88x`) above the floor wage, plus statutory `2.0x` basic hourly overtime pay and festival bonuses.

3. **Exchange Rate Regimes & Imported Input Inflation**:
   - **2006–2010**: Stable managed float around **68.6–69.7 BDT/USD**.
   - **2011–2012**: First reserve pressure and cotton price spike (**74.1 to 81.9 BDT/USD**; global cotton index jumping to `154.0`).
   - **2013–2021**: Controlled crawl between **77.6 and 85.1 BDT/USD**.
   - **2022–2025**: Post-pandemic reserve drain, energy price shock, and transition to IMF-supported crawling peg, pushing the Taka from **93.5 BDT/USD (2022)** to **107.8 (2023)**, **115.8 (2024)**, and **120.4 BDT/USD (2025)** alongside industrial gas and electricity tariff surges.

4. **Major Historical Shocks & Operational Propagation**:
   - **2008–2009 Global Financial Crisis (GFC)**: 8% demand contraction multiplier, higher buyer discount requests (`+1.5%`), and elevated order cancellations (`4.8%`).
   - **April 2013 Rana Plaza Aftermath & Remediation (2013–2015)**: Structural surge in safety/compliance audit costs (`COST-QLT` +65%), diversion of tier-1 buyers away from non-remediated legacy units, and the permanent closure of `FAC-25` (*Dhaleswari Keraniganj Unit-1*) in August 2014.
   - **2020 COVID-19 Pandemic Shock**: Acute order cancellation wave (`16.5%` in Mar–May 2020), factory utilization drop, raw material inventory build-up, vessel blank sailings, and permanent closure of `FAC-26` (*Dhaleswari Heritage Garments*) in October 2020.
   - **2021–2022 Restocking Boom & Global Container Crisis**: Surge in order volume (`1.18x`) accompanied by a `2.25x` spike in container freight costs and port congestion delays.
   - **2024–2025 Red Sea Maritime Rerouting**: Adds ~7 transit days and `+45%` freight surcharge to EU/UK/US East Coast sea shipments.

---

## 2. Hierarchical Reconciliation Pipeline

The Python generation pipeline (`scripts/`) executes in 9 deterministic steps using `SEED = 20261026`:

1. `generate_macro_context.py` builds the 240-month macroeconomic & industry table (`fact_macro_monthly`).
2. `generate_dimensions.py` creates the 9 core dimensions (`dim_date`, `dim_company`, `dim_factory`, `dim_factory_line`, `dim_buyer`, `dim_supplier`, `dim_product`, `dim_material`, `dim_cost_category`).
3. `generate_facts.py` generates `fact_sales_order_line` (240,000 rows) and the 1:1 conformed bridge `dim_order_line` respecting company/factory opening and closure dates.
4. Active (non-cancelled) order lines are scheduled into `fact_production_batch` (290,415 rows), splitting large orders (`>= 9,000 pcs`) across multiple batches and lines.
5. `fact_material_consumption` (580,830 rows) computes BOM-driven primary fabric/yarn and trim/packaging consumption plus realistic process wastage (`2.8%` to `14.5%`).
6. `fact_quality_inspection` (290,415 rows) models end-line and final AQL inspections where `rework_qty_pcs + rejected_qty_pcs == defective_qty_pcs` and `accepted_qty_pcs == actual_good_output_pcs`.
7. `fact_shipment_line` (259,205 rows) dispatches finished goods after production completion, supporting partial shipments and reconciling 100% back to `fact_sales_order_line.shipped_qty_pcs`.
8. `fact_purchase_order_line` (245,000 rows) and `fact_supplier_delivery` (281,781 rows) backward-schedule material procurement from batch consumption requirements and supplier lead times.
9. `fact_workforce_monthly` (47,880 rows), `fact_sustainability_monthly` (5,320 rows), `fact_inventory_snapshot_monthly` (255,360 rows), and `fact_cost_transaction` (348,017 rows) generate reconciled monthly operational and financial snapshots.

---

## 3. Accounting & Estimation Disclaimers

- **Operational Contribution & Gross Margin**: In `fact_cost_transaction` and the Power BI DAX catalog, calculated gross profit and contribution margin represent **operational management accounting indicators**, not statutory audited IFRS financial statements.
- **Sustainability & Emissions**: Electricity (`kWh`), natural gas (`m3`), water (`m3`), and Scope 1+2 carbon emissions (`kg CO2e`) in `fact_sustainability_monthly` are activity-based engineering estimates for fictional facilities and must never be cited as verified ESG disclosures of real companies.

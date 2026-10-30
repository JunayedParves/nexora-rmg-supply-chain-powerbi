# Power BI Semantic Model Specification

## 1. Star-Schema Constellation Architecture

To support high-performance interactive analysis across ~3.04 million rows in **Power BI Desktop** (Import Mode or Composite DirectQuery over Google BigQuery), the semantic model is organized into **10 Conformed Dimensions** and **12 Fact Tables**.

### Core Design Rules

1. **Strictly One-to-Many (`1:*`) Single-Direction Relationships**:
   - Every active relationship flows from a Dimension table (`1`) to a Fact table (`*`) with `CrossFilterDirection = Single`.
   - Bidirectional cross-filtering is disabled across the model to prevent ambiguous filter paths and performance degradation.
2. **Conformed Bridge Dimension (`dim_order_line`)**:
   - Sales orders (`fact_sales_order_line`), production batches (`fact_production_batch`), quality inspections (`fact_quality_inspection`), and shipment lines (`fact_shipment_line`) all share `order_line_key`.
   - Instead of joining fact tables directly to one another (which would create many-to-many cardinalities when orders have both split production batches and split shipments), all four tables link to `dim_order_line[order_line_key]`.
3. **Role-Playing Date Relationships (`dim_date`)**:
   - `dim_date` has one **Active** relationship per fact table (based on the primary business event date) and **Inactive** relationships for secondary lifecycle dates, activated on demand via `USERELATIONSHIP()`:
     - `fact_sales_order_line`: Active on `order_date_key`; Inactive on `requested_delivery_date_key`.
     - `fact_purchase_order_line`: Active on `po_order_date_key`; Inactive on `expected_delivery_date_key`.
     - `fact_supplier_delivery`: Active on `receipt_date_key`; Inactive on `dispatch_date_key`.
     - `fact_production_batch`: Active on `actual_completion_date_key`; Inactive on `planned_start_date_key`, `actual_start_date_key`, `planned_completion_date_key`.
     - `fact_shipment_line`: Active on `actual_ship_date_key`; Inactive on `dispatch_date_key`, `expected_ship_date_key`, `actual_arrival_date_key`, `confirmed_delivery_date_key`.
   - If a report visual requires simultaneous slicing by two independent dates (e.g., *Order Intake Month* on rows vs. *Shipment Month* on columns), either use the DAX measures with `USERELATIONSHIP()` or create a calculated role-playing table `dim_delivery_date = dim_date`.
4. **Preventing Double Counting Across Mixed Grains**:
   - **Transactional Facts** (`fact_sales_order_line`, `fact_production_batch`, `fact_shipment_line`, `fact_purchase_order_line`, `fact_supplier_delivery`, `fact_material_consumption`, `fact_quality_inspection`) are fully additive across all dimensions.
   - **Periodic Monthly Snapshots** (`fact_inventory_snapshot_monthly`, `fact_workforce_monthly`) are **semi-additive**: stock balances (`closing_qty`, `inventory_value_usd`) and headcount (`active_headcount`) are additive across factories/companies/items, but must use `LASTNONBLANKVALUE(dim_date[date_key], ...)` or `AVERAGEX(VALUES(dim_date[year_month]), ...)` across time periods.
   - **Financial Cost Postings** (`fact_cost_transaction`) combine batch-level direct material/trim costs (`cost_category_key IN {1, 2}`) with factory/company monthly overhead, labour, utility, and logistics postings (`cost_category_key IN {3..12}`). Therefore, total company/factory profitability is evaluated at the `(company_key, factory_key, year_month)` grain using conformed dimensions (`dim_company`, `dim_factory`, `dim_date`).

---

## 2. Currency & Unit-of-Measure Handling

- **Dual Currency Support (`BDT` and `USD`)**:
  - Every monetary fact table stores both the **USD amount** (fixed-precision `NUMERIC(18,2)`) and the **BDT amount** (`NUMERIC(18,2)`), alongside the exact historical `bdt_usd_exchange_rate` (`FLOAT64`) effective on that transaction date.
  - Never multiply an already-converted column by the exchange rate a second time.
  - Create a disconnected parameter table `prm_currency = DATATABLE("Currency", STRING, {{"BDT"}, {"USD"}})` in Power BI so executives can toggle the entire report between Bangladesh Taka (`BDT`) and US Dollars (`USD`).
- **Explicit Units of Measure (`base_uom`)**:
  - Garment sales, production batches, quality inspections, and shipments are measured in **Pieces (`PCS`)**.
  - Raw materials (`dim_material[base_uom]`) use domain-authentic units: `KG` (yarn, knit fabric, dyes/chemicals), `YARD` (woven & denim fabric, interlining), `CONE` (thread), `PCS`/`SET`/`GROSS` (trims, zippers, cartons, polybags).
  - Never sum raw material quantities across incompatible UOMs without filtering by `dim_material[base_uom]` or using monetary valuation (`inventory_value_usd` / `total_material_cost_usd`).

---

## 3. Power BI Desktop Import & Setup Steps

1. Open **Power BI Desktop** -> **Get Data** -> **Parquet** (or **Folder** / **Google BigQuery**).
2. To load locally via Power Query (`M`), use the following pattern for partitioned fact tables (e.g., `fact_sales_order_line`):
   ```powerquery
   let
       Source = Folder.Files("C:\Users\Junayed\Documents\RMG Company\rmg_supply_chain_intelligence\data\facts\fact_sales_order_line"),
       ParquetFiles = Table.SelectRows(Source, each ([Extension] = ".parquet")),
       Combined = Table.Combine(List.Transform(ParquetFiles[Content], each Parquet.Document(_)))
   in
       Combined
   ```
3. Mark `dim_date` as the official **Date Table** (`Mark as date table` -> `full_date`).
4. Configure the 62 relationships defined in `documentation/model_relationships.csv`.
5. Create a dedicated `_Measures` table and paste the measures from `power_bi/dax_measure_catalog.md`.

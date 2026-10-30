# Automated Data Quality & Supply-Chain Reconciliation Report

- **Validation Timestamp**: `2026-10-26 01:37:30`
- **Total Tables Validated**: `22` (10 Dimensions, 12 Facts)
- **Total Records Validated**: `2,849,520` rows
- **Total Compressed Parquet Volume**: `161.25 MB` (Snappy)
- **Overall Test Suite Status**: **12 / 12 PASSED (0 Failed Assertions)**

---

## 1. Automated Validation Test Summary

| Test ID | Category | Validation Rule Description | Records Checked | Failed Count | Status | Notes |
|:---|:---|:---|---:|---:|:---:|:---|
| `DQ-01` | Primary Key Integrity | All 22 dimension and fact primary keys are unique and non-null | 2,849,520 | 0 | **PASS** | Verified across 10 dimensions and 12 fact tables. |
| `DQ-02` | Referential Integrity | All foreign keys across facts and dimensions resolve to valid parent dimension keys | 7,517,973 | 0 | **PASS** | Verified 32 foreign-key relationships. |
| `DQ-03` | Historical Date Coverage | dim_date spans exactly 20 calendar years (2006-01-01 to 2025-12-31, 7,305 days) with fiscal & lunar attributes | 7,305 | 0 | **PASS** | Range: 2006-01-01 to 2025-12-31, rows=7,305. |
| `DQ-04` | Chronological Event Sequence | Procurement, production, dispatch, vessel shipment, port arrival, and delivery dates follow valid chronological order | 1,016,947 | 0 | **PASS** | SO bad=0, PB bad=0, SH bad=0, SD bad=0. |
| `DQ-05` | Order-to-Shipment Reconciliation | Shipped quantities reconcile 100% with sales order lines, never exceed amended eligible qty, and are zero for cancelled orders | 240,000 | 0 | **PASS** | Mismatch=0, Over-shipped=0, Shipped-when-cancelled=0. |
| `DQ-06` | PO-to-Delivery Reconciliation | Supplier deliveries do not exceed PO quantities and accepted + rejected quantities equal received quantities | 526,638 | 0 | **PASS** | PO over-receipt=0, Delivery split math bad=0. |
| `DQ-07` | Material Consumption & BOM Plausibility | Actual material consumption equals planned BOM quantity plus positive wastage across all production batches | 508,366 | 0 | **PASS** | BOM math discrepancy=0, Negative qty=0. |
| `DQ-08` | Inventory Balance Reconciliation | Monthly inventory closing balance strictly equals opening + receipts + production additions - issues + adjustments with zero negative stock | 227,760 | 0 | **PASS** | Balance equation failures=0, Negative closing stock=0. |
| `DQ-09` | Quality Inspection Bounds | Defective quantities never exceed inspected quantities, and rework + rejected quantities exactly equal total defective pieces | 254,183 | 0 | **PASS** | 100% of inspection batches satisfy AQL & rework identity. |
| `DQ-10` | Currency Conversion Integrity | All USD and BDT financial amounts across Sales, Shipments, and Cost Transactions reconcile via documented BDT/USD exchange rates without double conversion | 782,737 | 0 | **PASS** | SO fx diff=0, SH fx diff=0, CT fx diff=0. |
| `DQ-11` | Factory & Company Lifecycle Respect | No sales orders, production batches, or monthly snapshots occur before a factory's opening date or after its closure date (e.g., FAC-25 closed Aug 2014, FAC-26 closed Oct 2020, FAC-08 closed Jun 2023) | 240,000 | 0 | **PASS** | All historical openings and closures strictly respected. |
| `DQ-12` | Parquet & BigQuery Schema Alignment | All 22 Parquet table schemas match their exported BigQuery JSON schema definitions and DDL scripts | 22 | 0 | **PASS** | Verified 22/22 tables. |

---

## 2. Final Table Row Counts & Parquet Storage Inventory

| Table Name | Category | Partition Scheme | Files | Row Count | Columns | Size (MB) | Primary Key |
|:---|:---|:---|---:|---:|---:|---:|:---|
| `dim_date` | dimension | Unpartitioned (Single File) | 1 | 7,305 | 30 | 0.101 | `date_key` |
| `dim_company` | dimension | Unpartitioned (Single File) | 1 | 8 | 14 | 0.007 | `company_key` |
| `dim_factory` | dimension | Unpartitioned (Single File) | 1 | 26 | 16 | 0.009 | `factory_key` |
| `dim_factory_line` | dimension | Unpartitioned (Single File) | 1 | 191 | 13 | 0.009 | `production_line_key` |
| `dim_buyer` | dimension | Unpartitioned (Single File) | 1 | 52 | 15 | 0.009 | `buyer_key` |
| `dim_material` | dimension | Unpartitioned (Single File) | 1 | 64 | 13 | 0.009 | `material_key` |
| `dim_supplier` | dimension | Unpartitioned (Single File) | 1 | 180 | 16 | 0.013 | `supplier_key` |
| `dim_product` | dimension | Unpartitioned (Single File) | 1 | 125 | 20 | 0.014 | `product_key` |
| `dim_cost_category` | dimension | Unpartitioned (Single File) | 1 | 12 | 8 | 0.004 | `cost_category_key` |
| `dim_order_line` | dimension | Unpartitioned (Single File) | 1 | 240,000 | 15 | 5.015 | `order_line_key` |
| `fact_sales_order_line` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 240,000 | 34 | 11.405 | `order_line_key` |
| `fact_purchase_order_line` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 245,000 | 19 | 10.115 | `purchase_order_line_key` |
| `fact_supplier_delivery` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 281,638 | 23 | 17.380 | `delivery_key` |
| `fact_production_batch` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 254,183 | 29 | 14.483 | `production_batch_key` |
| `fact_material_consumption` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 508,366 | 21 | 33.270 | `consumption_key` |
| `fact_quality_inspection` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 254,183 | 28 | 15.174 | `inspection_key` |
| `fact_shipment_line` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 241,126 | 43 | 22.144 | `shipment_line_key` |
| `fact_inventory_snapshot_monthly` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 227,760 | 32 | 14.815 | `inventory_snapshot_key` |
| `fact_cost_transaction` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 301,611 | 16 | 13.766 | `cost_transaction_key` |
| `fact_workforce_monthly` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 42,705 | 24 | 2.693 | `workforce_month_key` |
| `fact_sustainability_monthly` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 4,745 | 24 | 0.564 | `sustainability_month_key` |
| `fact_macro_monthly` | fact | event_year=YYYY (20 Annual Partitions, 2006-2025) | 20 | 240 | 32 | 0.253 | `macro_month_key` |
| **TOTAL** | **22 Tables** | **Snappy Parquet** | **250** | **2,849,520** | **485 cols** | **161.252** | — |
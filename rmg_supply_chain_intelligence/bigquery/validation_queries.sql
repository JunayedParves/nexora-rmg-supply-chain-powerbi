-- =============================================================================
-- BigQuery Post-Load Validation & Supply-Chain Reconciliation Script
-- Dataset: `rmg_supply_chain_dw`
-- =============================================================================

-- 1. Row Count & Year Coverage Summary Across All 12 Fact Tables
SELECT 'fact_sales_order_line' AS table_name, COUNT(*) AS row_count, MIN(event_year) AS min_yr, MAX(event_year) AS max_yr FROM `rmg_supply_chain_dw.fact_sales_order_line`
UNION ALL
SELECT 'fact_purchase_order_line', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_purchase_order_line`
UNION ALL
SELECT 'fact_supplier_delivery', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_supplier_delivery`
UNION ALL
SELECT 'fact_production_batch', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_production_batch`
UNION ALL
SELECT 'fact_material_consumption', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_material_consumption`
UNION ALL
SELECT 'fact_quality_inspection', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_quality_inspection`
UNION ALL
SELECT 'fact_shipment_line', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_shipment_line`
UNION ALL
SELECT 'fact_inventory_snapshot_monthly', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_inventory_snapshot_monthly`
UNION ALL
SELECT 'fact_cost_transaction', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_cost_transaction`
UNION ALL
SELECT 'fact_workforce_monthly', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_workforce_monthly`
UNION ALL
SELECT 'fact_sustainability_monthly', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_sustainability_monthly`
UNION ALL
SELECT 'fact_macro_monthly', COUNT(*), MIN(event_year), MAX(event_year) FROM `rmg_supply_chain_dw.fact_macro_monthly`
ORDER BY table_name;

-- 2. Verify Zero Orphan Foreign Keys Between Sales Orders, Production Batches, and Shipments
SELECT
    COUNTIF(ol.order_line_key IS NULL) AS orphan_sales_order_lines,
    COUNTIF(c.company_key IS NULL) AS orphan_companies,
    COUNTIF(f.factory_key IS NULL) AS orphan_factories,
    COUNTIF(b.buyer_key IS NULL) AS orphan_buyers,
    COUNTIF(p.product_key IS NULL) AS orphan_products
FROM `rmg_supply_chain_dw.fact_sales_order_line` so
LEFT JOIN `rmg_supply_chain_dw.dim_order_line` ol ON so.order_line_key = ol.order_line_key
LEFT JOIN `rmg_supply_chain_dw.dim_company` c ON so.company_key = c.company_key
LEFT JOIN `rmg_supply_chain_dw.dim_factory` f ON so.factory_key = f.factory_key
LEFT JOIN `rmg_supply_chain_dw.dim_buyer` b ON so.buyer_key = b.buyer_key
LEFT JOIN `rmg_supply_chain_dw.dim_product` p ON so.product_key = p.product_key;

-- 3. Reconcile Shipped Quantities Between `fact_sales_order_line` and `fact_shipment_line`
WITH ship_sum AS (
    SELECT order_line_key, SUM(shipped_qty_pcs) AS total_shipped_pcs
    FROM `rmg_supply_chain_dw.fact_shipment_line`
    GROUP BY order_line_key
)
SELECT
    COUNT(*) AS total_order_lines_checked,
    COUNTIF(so.shipped_qty_pcs != COALESCE(s.total_shipped_pcs, 0)) AS reconciliation_mismatches,
    COUNTIF(so.shipped_qty_pcs > so.amended_order_qty_pcs) AS over_shipment_violations,
    COUNTIF(so.is_cancelled AND so.shipped_qty_pcs > 0) AS cancelled_order_shipment_violations
FROM `rmg_supply_chain_dw.fact_sales_order_line` so
LEFT JOIN ship_sum s ON so.order_line_key = s.order_line_key;

-- 4. Verify Monthly Inventory Balance Continuity (Opening + Inflows - Outflows + Adjustments = Closing)
SELECT
    COUNT(*) AS total_snapshots,
    COUNTIF(
        ABS(
            (opening_qty + receipts_qty + production_additions_qty - consumption_issues_qty - shipment_issues_qty + adjustment_qty)
            - closing_qty
        ) > 0.05
    ) AS balance_equation_errors,
    COUNTIF(closing_qty < 0) AS negative_stock_errors
FROM `rmg_supply_chain_dw.fact_inventory_snapshot_monthly`;

-- 5. Verify Chronological Sequence Across Supply Chain Events
SELECT
    (SELECT COUNTIF(order_date > requested_delivery_date) FROM `rmg_supply_chain_dw.fact_sales_order_line`) AS invalid_order_dates,
    (SELECT COUNTIF(actual_start_date > actual_completion_date) FROM `rmg_supply_chain_dw.fact_production_batch`) AS invalid_production_dates,
    (SELECT COUNTIF(dispatch_date > actual_ship_date OR actual_ship_date > actual_arrival_date OR actual_arrival_date > confirmed_delivery_date) FROM `rmg_supply_chain_dw.fact_shipment_line`) AS invalid_shipment_dates,
    (SELECT COUNTIF(dispatch_date > receipt_date) FROM `rmg_supply_chain_dw.fact_supplier_delivery`) AS invalid_supplier_delivery_dates;

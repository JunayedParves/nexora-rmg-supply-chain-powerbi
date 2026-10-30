-- =============================================================================
-- BigQuery Analytical KPI Views for Power BI & Executive Reporting
-- Dataset: `rmg_supply_chain_dw`
-- Explicitly separates order, production, shipment, and monthly cost grains
-- to prevent systematic double-counting.
-- =============================================================================

-- 1. Executive Company & Fiscal-Year Commercial & Profitability View
CREATE OR REPLACE VIEW `rmg_supply_chain_dw.vw_company_fiscal_kpi` AS
WITH sales_agg AS (
    SELECT
        company_key,
        fiscal_year,
        COUNT(DISTINCT sales_order_id) AS total_orders,
        COUNT(order_line_key) AS total_order_lines,
        SUM(ordered_qty_pcs) AS ordered_qty_pcs,
        SUM(amended_order_qty_pcs) AS eligible_order_qty_pcs,
        SUM(net_order_value_usd) AS order_intake_usd,
        SUM(net_order_value_bdt) AS order_intake_bdt,
        SUM(unfulfilled_backlog_qty_pcs) AS backlog_qty_pcs,
        SAFE_DIVIDE(COUNTIF(is_cancelled), COUNT(order_line_key)) AS order_cancellation_rate
    FROM `rmg_supply_chain_dw.fact_sales_order_line`
    GROUP BY company_key, fiscal_year
),
ship_agg AS (
    SELECT
        sh.company_key,
        d.fiscal_year,
        SUM(sh.shipped_qty_pcs) AS shipped_qty_pcs,
        SUM(sh.fob_revenue_usd) AS fob_revenue_usd,
        SUM(sh.fob_revenue_bdt) AS fob_revenue_bdt,
        SUM(sh.freight_cost_usd + sh.inland_logistics_cost_usd) AS logistics_cost_usd,
        SUM(sh.freight_cost_bdt + sh.inland_logistics_cost_bdt) AS logistics_cost_bdt,
        SAFE_DIVIDE(COUNTIF(sh.is_on_time_shipment), COUNT(*)) AS on_time_shipment_rate,
        SAFE_DIVIDE(COUNTIF(sh.is_on_time_delivery), COUNT(*)) AS otd_delivery_rate
    FROM `rmg_supply_chain_dw.fact_shipment_line` sh
    JOIN `rmg_supply_chain_dw.dim_date` d ON sh.actual_ship_date_key = d.date_key
    GROUP BY sh.company_key, d.fiscal_year
),
cost_agg AS (
    SELECT
        ct.company_key,
        d.fiscal_year,
        SUM(IF(cc.cost_category_code IN ('COST-DM', 'COST-TRM'), ct.amount_usd, 0)) AS direct_material_cost_usd,
        SUM(IF(cc.cost_category_code = 'COST-DL', ct.amount_usd, 0)) AS direct_labour_cost_usd,
        SUM(IF(cc.cost_group = 'Factory Overhead', ct.amount_usd, 0)) AS factory_overhead_cost_usd,
        SUM(IF(cc.cost_category_code = 'COST-QLT', ct.amount_usd, 0)) AS quality_compliance_cost_usd,
        SUM(ct.amount_usd) AS total_cost_usd,
        SUM(ct.amount_bdt) AS total_cost_bdt
    FROM `rmg_supply_chain_dw.fact_cost_transaction` ct
    JOIN `rmg_supply_chain_dw.dim_cost_category` cc ON ct.cost_category_key = cc.cost_category_key
    JOIN `rmg_supply_chain_dw.dim_date` d ON ct.transaction_date_key = d.date_key
    GROUP BY ct.company_key, d.fiscal_year
)
SELECT
    c.company_code,
    c.company_name,
    c.operating_archetype,
    s.fiscal_year,
    s.total_orders,
    s.ordered_qty_pcs,
    s.order_intake_usd,
    sh.shipped_qty_pcs,
    sh.fob_revenue_usd,
    sh.fob_revenue_bdt,
    k.direct_material_cost_usd,
    k.direct_labour_cost_usd,
    k.factory_overhead_cost_usd,
    (sh.fob_revenue_usd - (k.direct_material_cost_usd + k.direct_labour_cost_usd + k.factory_overhead_cost_usd)) AS operational_gross_margin_usd,
    SAFE_DIVIDE(
        sh.fob_revenue_usd - (k.direct_material_cost_usd + k.direct_labour_cost_usd + k.factory_overhead_cost_usd),
        sh.fob_revenue_usd
    ) AS operational_gross_margin_pct,
    sh.on_time_shipment_rate,
    sh.otd_delivery_rate,
    s.order_cancellation_rate
FROM sales_agg s
JOIN `rmg_supply_chain_dw.dim_company` c ON s.company_key = c.company_key
LEFT JOIN ship_agg sh ON s.company_key = sh.company_key AND s.fiscal_year = sh.fiscal_year
LEFT JOIN cost_agg k ON s.company_key = k.company_key AND s.fiscal_year = k.fiscal_year;

-- 2. Factory Monthly Productivity, Quality & Sustainability Benchmark View
CREATE OR REPLACE VIEW `rmg_supply_chain_dw.vw_factory_monthly_performance` AS
WITH prod_m AS (
    SELECT
        pb.factory_key,
        d.year_month,
        SUM(pb.planned_qty_pcs) AS planned_qty_pcs,
        SUM(pb.actual_good_output_pcs) AS good_output_pcs,
        SUM(pb.rework_qty_pcs) AS rework_qty_pcs,
        SUM(pb.rejected_scrap_qty_pcs) AS rejected_qty_pcs,
        SUM(pb.earned_standard_minutes) AS earned_standard_minutes,
        SUM(pb.actual_labour_hours) AS actual_labour_hours,
        SUM(pb.machine_downtime_hours) AS machine_downtime_hours,
        AVG(pb.line_efficiency_pct) AS avg_line_efficiency_pct
    FROM `rmg_supply_chain_dw.fact_production_batch` pb
    JOIN `rmg_supply_chain_dw.dim_date` d ON pb.actual_completion_date_key = d.date_key
    GROUP BY pb.factory_key, d.year_month
),
wf_m AS (
    SELECT
        w.factory_key,
        d.year_month,
        SUM(w.active_headcount) AS total_headcount,
        SUM(w.overtime_hours) AS total_overtime_hours,
        SUM(w.total_payroll_bdt) AS total_payroll_bdt,
        SUM(w.total_payroll_usd) AS total_payroll_usd
    FROM `rmg_supply_chain_dw.fact_workforce_monthly` w
    JOIN `rmg_supply_chain_dw.dim_date` d ON w.date_key = d.date_key
    GROUP BY w.factory_key, d.year_month
)
SELECT
    f.factory_code,
    f.factory_name,
    f.location_city,
    f.compliance_profile,
    sm.calendar_year,
    sm.calendar_month,
    sm.fiscal_year,
    pm.planned_qty_pcs,
    pm.good_output_pcs,
    SAFE_DIVIDE(pm.good_output_pcs, f.base_monthly_capacity_pcs) AS capacity_utilization_ratio,
    SAFE_DIVIDE(pm.good_output_pcs, pm.actual_labour_hours) AS output_pcs_per_labour_hour,
    SAFE_DIVIDE(wm.total_payroll_usd, pm.good_output_pcs) AS labour_cost_per_garment_usd,
    pm.avg_line_efficiency_pct,
    wm.total_headcount,
    wm.total_overtime_hours,
    sm.electricity_consumption_kwh,
    sm.renewable_energy_share_pct,
    sm.water_withdrawal_m3,
    sm.emissions_per_garment_kg_co2e
FROM `rmg_supply_chain_dw.fact_sustainability_monthly` sm
JOIN `rmg_supply_chain_dw.dim_factory` f ON sm.factory_key = f.factory_key
JOIN `rmg_supply_chain_dw.dim_date` d ON sm.date_key = d.date_key
LEFT JOIN prod_m pm ON sm.factory_key = pm.factory_key AND d.year_month = pm.year_month
LEFT JOIN wf_m wm ON sm.factory_key = wm.factory_key AND d.year_month = wm.year_month;

-- =============================================================================
-- Google BigQuery DDL for 20-Year Bangladesh RMG Supply Chain Intelligence
-- Dataset: `rmg_supply_chain_dw`
-- All tables match the exported Snappy-compressed Parquet logical types.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS `rmg_supply_chain_dw`
OPTIONS(location='asia-south1', description='20-Year Bangladesh RMG Supply Chain Intelligence Warehouse (2006-2025)');

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_date` (
    `date_key` INT64 NOT NULL,
    `full_date` DATE,
    `day_of_month` INT64,
    `day_of_year` INT64,
    `iso_weekday` INT64,
    `weekday_name` STRING,
    `iso_week_of_year` INT64,
    `calendar_month` INT64,
    `month_name` STRING,
    `month_short` STRING,
    `year_month` STRING,
    `calendar_quarter` INT64,
    `calendar_quarter_label` STRING,
    `calendar_year` INT64,
    `fiscal_year` STRING,
    `fiscal_year_numeric` INT64,
    `fiscal_quarter` INT64,
    `fiscal_quarter_label` STRING,
    `fiscal_month` INT64,
    `is_leap_year` BOOL,
    `is_weekend` BOOL,
    `is_month_start` BOOL,
    `is_month_end` BOOL,
    `is_public_holiday` BOOL,
    `holiday_name` STRING,
    `is_ramadan_period` BOOL,
    `is_eid_festival_window` BOOL,
    `is_working_day` BOOL,
    `apparel_buying_season` STRING,
    `bangladesh_climate_season` STRING
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_company` (
    `company_key` INT64 NOT NULL,
    `company_code` STRING,
    `company_name` STRING,
    `operating_archetype` STRING,
    `year_established` INT64,
    `primary_product_specialization` STRING,
    `business_model` STRING,
    `trade_association` STRING,
    `headquarters_city` STRING,
    `backward_linkage_level` STRING,
    `active_from_date` DATE,
    `active_to_date` DATE,
    `is_currently_active` BOOL,
    `base_market_share_weight` FLOAT64
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_factory` (
    `factory_key` INT64 NOT NULL,
    `company_key` INT64,
    `factory_code` STRING,
    `factory_name` STRING,
    `location_city` STRING,
    `industrial_zone` STRING,
    `product_specialization` STRING,
    `production_technology` STRING,
    `design_line_count` INT64,
    `base_monthly_capacity_pcs` INT64,
    `opening_date` DATE,
    `closure_date` DATE,
    `is_closed` BOOL,
    `compliance_profile` STRING,
    `base_efficiency_factor` FLOAT64,
    `unit_cost_multiplier` NUMERIC
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_factory_line` (
    `production_line_key` INT64 NOT NULL,
    `factory_key` INT64,
    `company_key` INT64,
    `line_code` STRING,
    `line_name` STRING,
    `line_specialization` STRING,
    `shift_pattern` STRING,
    `standard_daily_hours` FLOAT64,
    `operators_per_line` INT64,
    `helpers_per_line` INT64,
    `monthly_standard_capacity_pcs` INT64,
    `active_from_date` DATE,
    `active_to_date` DATE
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_buyer` (
    `buyer_key` INT64 NOT NULL,
    `buyer_code` STRING,
    `buyer_name` STRING,
    `customer_segment` STRING,
    `destination_country` STRING,
    `market_region` STRING,
    `market_classification` STRING,
    `product_preference` STRING,
    `order_size_tier` STRING,
    `payment_terms` STRING,
    `quality_tolerance_aql` FLOAT64,
    `compliance_strictness` STRING,
    `relationship_start_date` DATE,
    `relationship_end_date` DATE,
    `demand_share_weight` FLOAT64
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_material` (
    `material_key` INT64 NOT NULL,
    `material_code` STRING,
    `material_name` STRING,
    `material_category` STRING,
    `material_group` STRING,
    `base_uom` STRING,
    `sourcing_profile` STRING,
    `sourcing_classification` STRING,
    `is_primarily_imported` BOOL,
    `standard_lead_time_days` INT64,
    `base_unit_cost_usd_2015` NUMERIC,
    `storage_characteristics` STRING,
    `is_critical_path_material` BOOL
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_supplier` (
    `supplier_key` INT64 NOT NULL,
    `supplier_code` STRING,
    `supplier_name` STRING,
    `supplier_type` STRING,
    `origin_country` STRING,
    `domestic_import_classification` STRING,
    `major_materials_supplied` STRING,
    `average_lead_time_days` INT64,
    `lead_time_variability_days` FLOAT64,
    `payment_terms` STRING,
    `baseline_reliability_score` FLOAT64,
    `minimum_order_value_usd` INT64,
    `active_from_date` DATE,
    `active_to_date` DATE,
    `is_currently_active` BOOL,
    `spend_share_weight` FLOAT64
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_product` (
    `product_key` INT64 NOT NULL,
    `product_code` STRING,
    `style_name` STRING,
    `product_category` STRING,
    `knit_woven_classification` STRING,
    `garment_type` STRING,
    `fabric_type` STRING,
    `fiber_composition` STRING,
    `target_market_segment` STRING,
    `value_tier` STRING,
    `manufacturing_complexity` STRING,
    `standard_minute_value_smv` FLOAT64,
    `primary_material_key` INT64,
    `primary_material_consumption_per_unit` FLOAT64,
    `primary_material_uom` STRING,
    `base_fob_unit_price_usd` NUMERIC,
    `seasonality_profile` STRING,
    `introduction_date` DATE,
    `discontinuation_date` DATE,
    `is_active_style` BOOL
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_cost_category` (
    `cost_category_key` INT64 NOT NULL,
    `cost_category_code` STRING,
    `cost_category_name` STRING,
    `cost_group` STRING,
    `cost_behavior` STRING,
    `allocation_basis` STRING,
    `income_statement_classification` STRING,
    `is_direct_production_cost` BOOL
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.dim_order_line` (
    `order_line_key` INT64 NOT NULL,
    `sales_order_id` STRING,
    `order_line_code` STRING,
    `company_key` INT64,
    `factory_key` INT64,
    `buyer_key` INT64,
    `product_key` INT64,
    `order_date` DATE,
    `requested_delivery_date` DATE,
    `order_status` STRING,
    `incoterm` STRING,
    `destination_country` STRING,
    `payment_terms` STRING,
    `knit_woven_classification` STRING,
    `product_category` STRING
);

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_sales_order_line` (
    `order_line_key` INT64 NOT NULL,
    `sales_order_id` STRING,
    `order_line_number` INT64,
    `calendar_year` INT64,
    `calendar_month` INT64,
    `calendar_quarter` INT64,
    `fiscal_year` STRING,
    `fiscal_month` INT64,
    `company_key` INT64,
    `factory_key` INT64,
    `buyer_key` INT64,
    `product_key` INT64,
    `ordered_qty_pcs` INT64,
    `amended_order_qty_pcs` INT64,
    `unit_price_usd` NUMERIC,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `gross_order_value_usd` NUMERIC,
    `discount_rate` FLOAT64,
    `discount_amount_usd` NUMERIC,
    `net_order_value_usd` NUMERIC,
    `net_order_value_bdt` NUMERIC,
    `order_status` STRING,
    `is_cancelled` BOOL,
    `is_amended` BOOL,
    `is_partial_fulfilment` BOOL,
    `event_year` INT64,
    `order_date` DATE,
    `order_date_key` INT64,
    `requested_delivery_date` DATE,
    `requested_delivery_date_key` INT64,
    `incoterm` STRING,
    `shipped_qty_pcs` INT64,
    `unfulfilled_backlog_qty_pcs` INT64
)
PARTITION BY `order_date`
CLUSTER BY `company_key`, `factory_key`, `buyer_key`, `product_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_purchase_order_line` (
    `purchase_order_line_key` INT64 NOT NULL,
    `purchase_order_id` STRING,
    `po_line_number` INT64,
    `supplier_key` INT64,
    `company_key` INT64,
    `receiving_factory_key` INT64,
    `material_key` INT64,
    `po_order_date_key` INT64,
    `po_order_date` DATE,
    `expected_delivery_date_key` INT64,
    `expected_delivery_date` DATE,
    `ordered_qty` FLOAT64,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `unit_cost_usd` NUMERIC,
    `order_value_usd` NUMERIC,
    `order_value_bdt` NUMERIC,
    `purchase_status` STRING,
    `event_year` INT64
)
PARTITION BY `po_order_date`
CLUSTER BY `company_key`, `receiving_factory_key`, `supplier_key`, `material_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_supplier_delivery` (
    `delivery_key` INT64 NOT NULL,
    `delivery_id` STRING,
    `purchase_order_line_key` INT64,
    `purchase_order_id` STRING,
    `supplier_key` INT64,
    `company_key` INT64,
    `receiving_factory_key` INT64,
    `material_key` INT64,
    `dispatch_date_key` INT64,
    `dispatch_date` DATE,
    `receipt_date_key` INT64,
    `receipt_date` DATE,
    `received_qty` FLOAT64,
    `accepted_qty` FLOAT64,
    `rejected_qty` FLOAT64,
    `delivery_delay_days` INT64,
    `is_on_time_delivery` BOOL,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `unit_cost_usd` NUMERIC,
    `documented_material_cost_usd` NUMERIC,
    `documented_material_cost_bdt` NUMERIC,
    `event_year` INT64
)
PARTITION BY `receipt_date`
CLUSTER BY `company_key`, `receiving_factory_key`, `supplier_key`, `material_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_production_batch` (
    `production_batch_key` INT64 NOT NULL,
    `batch_id` STRING,
    `order_line_key` INT64,
    `company_key` INT64,
    `factory_key` INT64,
    `production_line_key` INT64,
    `product_key` INT64,
    `planned_start_date_key` INT64,
    `planned_start_date` DATE,
    `actual_start_date_key` INT64,
    `actual_start_date` DATE,
    `planned_completion_date_key` INT64,
    `planned_completion_date` DATE,
    `actual_completion_date_key` INT64,
    `actual_completion_date` DATE,
    `planned_qty_pcs` INT64,
    `gross_produced_qty_pcs` INT64,
    `actual_good_output_pcs` INT64,
    `rework_qty_pcs` INT64,
    `rejected_scrap_qty_pcs` INT64,
    `standard_minute_value_smv` FLOAT64,
    `earned_standard_minutes` FLOAT64,
    `actual_production_line_hours` FLOAT64,
    `actual_labour_hours` FLOAT64,
    `machine_downtime_hours` FLOAT64,
    `line_efficiency_pct` FLOAT64,
    `schedule_delay_days` INT64,
    `production_status` STRING,
    `event_year` INT64
)
PARTITION BY `actual_completion_date`
CLUSTER BY `company_key`, `factory_key`, `production_line_key`, `product_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_material_consumption` (
    `consumption_key` INT64 NOT NULL,
    `production_batch_key` INT64,
    `batch_id` STRING,
    `company_key` INT64,
    `factory_key` INT64,
    `product_key` INT64,
    `material_key` INT64,
    `consumption_date_key` INT64,
    `consumption_date` DATE,
    `planned_material_qty` FLOAT64,
    `actual_material_qty` FLOAT64,
    `wastage_qty` FLOAT64,
    `wastage_rate_pct` FLOAT64,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `unit_cost_usd` NUMERIC,
    `total_material_cost_usd` NUMERIC,
    `total_material_cost_bdt` NUMERIC,
    `wastage_cost_usd` NUMERIC,
    `wastage_cost_bdt` NUMERIC,
    `event_year` INT64
)
PARTITION BY `consumption_date`
CLUSTER BY `company_key`, `factory_key`, `material_key`, `product_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_quality_inspection` (
    `inspection_key` INT64 NOT NULL,
    `inspection_id` STRING,
    `production_batch_key` INT64,
    `batch_id` STRING,
    `order_line_key` INT64,
    `company_key` INT64,
    `factory_key` INT64,
    `production_line_key` INT64,
    `product_key` INT64,
    `inspection_date_key` INT64,
    `inspection_date` DATE,
    `inspection_stage` STRING,
    `inspected_qty_pcs` INT64,
    `defective_qty_pcs` INT64,
    `rework_qty_pcs` INT64,
    `rejected_qty_pcs` INT64,
    `accepted_qty_pcs` INT64,
    `defect_rate_pct` FLOAT64,
    `first_pass_yield_pct` FLOAT64,
    `primary_defect_category` STRING,
    `aql_standard_threshold` FLOAT64,
    `passed_first_inspection` BOOL,
    `inspection_status` STRING,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `estimated_quality_cost_usd` NUMERIC,
    `estimated_quality_cost_bdt` NUMERIC,
    `event_year` INT64
)
PARTITION BY `inspection_date`
CLUSTER BY `company_key`, `factory_key`, `product_key`, `primary_defect_category`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_shipment_line` (
    `shipment_line_key` INT64 NOT NULL,
    `shipment_id` STRING,
    `order_line_key` INT64,
    `sales_order_id` STRING,
    `company_key` INT64,
    `factory_key` INT64,
    `buyer_key` INT64,
    `product_key` INT64,
    `dispatch_date_key` INT64,
    `dispatch_date` DATE,
    `expected_ship_date_key` INT64,
    `expected_ship_date` DATE,
    `actual_ship_date_key` INT64,
    `actual_ship_date` DATE,
    `estimated_arrival_date_key` INT64,
    `estimated_arrival_date` DATE,
    `actual_arrival_date_key` INT64,
    `actual_arrival_date` DATE,
    `confirmed_delivery_date_key` INT64,
    `confirmed_delivery_date` DATE,
    `shipped_qty_pcs` INT64,
    `delivered_qty_pcs` INT64,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `fob_revenue_usd` NUMERIC,
    `fob_revenue_bdt` NUMERIC,
    `delivered_revenue_usd` NUMERIC,
    `delivered_revenue_bdt` NUMERIC,
    `freight_cost_usd` NUMERIC,
    `freight_cost_bdt` NUMERIC,
    `inland_logistics_cost_usd` NUMERIC,
    `inland_logistics_cost_bdt` NUMERIC,
    `shipping_mode` STRING,
    `port_of_loading` STRING,
    `export_destination_country` STRING,
    `shipment_delay_days` INT64,
    `delivery_delay_days` INT64,
    `is_on_time_shipment` BOOL,
    `is_on_time_delivery` BOOL,
    `is_partial_shipment` BOOL,
    `delivery_status` STRING,
    `delay_reason` STRING,
    `event_year` INT64
)
PARTITION BY `actual_ship_date`
CLUSTER BY `company_key`, `factory_key`, `buyer_key`, `export_destination_country`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_inventory_snapshot_monthly` (
    `inventory_snapshot_key` INT64 NOT NULL,
    `date_key` INT64,
    `snapshot_month_date` DATE,
    `calendar_year` INT64,
    `calendar_month` INT64,
    `fiscal_year` STRING,
    `company_key` INT64,
    `factory_key` INT64,
    `item_code` STRING,
    `material_key` INT64,
    `product_key` INT64,
    `stock_type` STRING,
    `uom` STRING,
    `opening_qty` FLOAT64,
    `receipts_qty` FLOAT64,
    `production_additions_qty` FLOAT64,
    `consumption_issues_qty` FLOAT64,
    `shipment_issues_qty` FLOAT64,
    `adjustment_qty` FLOAT64,
    `closing_qty` FLOAT64,
    `reserved_qty` FLOAT64,
    `safety_stock_qty` FLOAT64,
    `is_below_safety_stock` BOOL,
    `is_stockout_incident` BOOL,
    `average_ageing_days` FLOAT64,
    `ageing_bucket` STRING,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `unit_valuation_usd` NUMERIC,
    `inventory_value_usd` NUMERIC,
    `inventory_value_bdt` NUMERIC,
    `event_year` INT64
)
PARTITION BY `snapshot_month_date`
CLUSTER BY `company_key`, `factory_key`, `stock_type`, `material_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_cost_transaction` (
    `cost_transaction_key` INT64 NOT NULL,
    `cost_transaction_id` STRING,
    `transaction_date_key` INT64,
    `transaction_date` DATE,
    `company_key` INT64,
    `factory_key` INT64,
    `cost_category_key` INT64,
    `production_batch_key` INT64,
    `order_line_key` INT64,
    `reference_quantity` FLOAT64,
    `currency_code` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `amount_usd` NUMERIC,
    `amount_bdt` NUMERIC,
    `allocation_method` STRING,
    `event_year` INT64
)
PARTITION BY `transaction_date`
CLUSTER BY `company_key`, `factory_key`, `cost_category_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_workforce_monthly` (
    `workforce_month_key` INT64 NOT NULL,
    `date_key` INT64,
    `month_start_date` DATE,
    `calendar_year` INT64,
    `calendar_month` INT64,
    `fiscal_year` STRING,
    `company_key` INT64,
    `factory_key` INT64,
    `department_name` STRING,
    `worker_grade_role` STRING,
    `active_headcount` INT64,
    `monthly_hires` INT64,
    `monthly_separations` INT64,
    `statutory_entry_min_wage_bdt` NUMERIC,
    `average_monthly_wage_bdt` NUMERIC,
    `overtime_hours` FLOAT64,
    `base_payroll_bdt` NUMERIC,
    `allowances_and_bonus_bdt` NUMERIC,
    `overtime_expense_bdt` NUMERIC,
    `total_payroll_bdt` NUMERIC,
    `total_payroll_usd` NUMERIC,
    `absenteeism_rate_pct` FLOAT64,
    `training_hours` FLOAT64,
    `event_year` INT64
)
PARTITION BY `month_start_date`
CLUSTER BY `company_key`, `factory_key`, `department_name`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_sustainability_monthly` (
    `sustainability_month_key` INT64 NOT NULL,
    `date_key` INT64,
    `month_start_date` DATE,
    `calendar_year` INT64,
    `calendar_month` INT64,
    `fiscal_year` STRING,
    `company_key` INT64,
    `factory_key` INT64,
    `monthly_output_pcs` INT64,
    `electricity_consumption_kwh` FLOAT64,
    `renewable_solar_kwh` FLOAT64,
    `renewable_energy_share_pct` FLOAT64,
    `natural_gas_consumption_m3` FLOAT64,
    `water_withdrawal_m3` FLOAT64,
    `wastewater_treated_m3` FLOAT64,
    `solid_fabric_waste_kg` FLOAT64,
    `recycled_material_kg` FLOAT64,
    `waste_recycling_rate_pct` FLOAT64,
    `estimated_carbon_emissions_kg_co2e` FLOAT64,
    `emissions_per_garment_kg_co2e` FLOAT64,
    `utility_cost_bdt` NUMERIC,
    `utility_cost_usd` NUMERIC,
    `estimation_methodology` STRING,
    `event_year` INT64
)
PARTITION BY `month_start_date`
CLUSTER BY `company_key`, `factory_key`;

CREATE OR REPLACE TABLE `rmg_supply_chain_dw.fact_macro_monthly` (
    `macro_month_key` INT64 NOT NULL,
    `date_key` INT64,
    `month_start_date` DATE,
    `calendar_year` INT64,
    `calendar_month` INT64,
    `year_month` STRING,
    `fiscal_year` STRING,
    `fiscal_month` INT64,
    `geographic_scope` STRING,
    `bdt_usd_exchange_rate` FLOAT64,
    `cpi_inflation_yoy_pct` FLOAT64,
    `cpi_index_2006_base` FLOAT64,
    `statutory_min_wage_entry_bdt` NUMERIC,
    `modeled_industry_floor_wage_bdt` NUMERIC,
    `global_cotton_price_index` FLOAT64,
    `carded_cotton_yarn_usd_per_kg` NUMERIC,
    `industrial_energy_tariff_index` FLOAT64,
    `industrial_electricity_bdt_per_kwh` NUMERIC,
    `industrial_gas_bdt_per_m3` NUMERIC,
    `container_freight_rate_index` FLOAT64,
    `working_capital_interest_rate_pct` FLOAT64,
    `bgmea_fy_woven_export_usd_bn` NUMERIC,
    `bgmea_fy_knit_export_usd_bn` NUMERIC,
    `bgmea_fy_total_rmg_export_usd_bn` NUMERIC,
    `epb_fy_national_export_usd_bn` NUMERIC,
    `annual_export_measurement_frequency` STRING,
    `monthly_series_methodology` STRING,
    `macro_regime_label` STRING,
    `industry_demand_multiplier` FLOAT64,
    `source_status` STRING,
    `quality_flag` STRING,
    `event_year` INT64
)
PARTITION BY `month_start_date`
CLUSTER BY `calendar_year`, `fiscal_year`;

# Power BI DAX Measure Catalog & KPI Specification

This catalog defines the production-ready **DAX measures** for the **20-Year Bangladesh RMG Supply Chain Intelligence** semantic model. Each KPI includes its business definition, DAX formula, source tables, aggregation grain, and management interpretation.

---

## 1. Sales & Commercial Performance KPIs

### 1.1 Order Intake Value (USD & BDT)
- **Source Table**: `fact_sales_order_line`
- **Grain**: All sales order lines (or non-cancelled net order intake)
```dax
Order Intake Value (USD) = 
CALCULATE(
    SUM(fact_sales_order_line[net_order_value_usd]),
    fact_sales_order_line[is_cancelled] = FALSE()
)

Order Intake Value (BDT) = 
CALCULATE(
    SUM(fact_sales_order_line[net_order_value_bdt]),
    fact_sales_order_line[is_cancelled] = FALSE()
)

Order Intake Qty (PCS) = 
CALCULATE(
    SUM(fact_sales_order_line[amended_order_qty_pcs]),
    fact_sales_order_line[is_cancelled] = FALSE()
)
```

### 1.2 Shipped FOB Revenue vs. Confirmed Delivered Revenue
- **Source Table**: `fact_shipment_line` (distinguishes vessel shipment date from customer warehouse delivery date via `USERELATIONSHIP`)
```dax
Shipped FOB Revenue (USD) = 
SUM(fact_shipment_line[fob_revenue_usd])

Shipped FOB Revenue (BDT) = 
SUM(fact_shipment_line[fob_revenue_bdt])

Confirmed Delivered Revenue (USD) = 
CALCULATE(
    SUM(fact_shipment_line[delivered_revenue_usd]),
    USERELATIONSHIP(fact_shipment_line[confirmed_delivery_date_key], dim_date[date_key])
)
```

### 1.3 YoY & MoM Revenue Growth (Calendar & Bangladesh Fiscal Year)
```dax
Shipped Revenue PY (USD) = 
CALCULATE(
    [Shipped FOB Revenue (USD)],
    SAMEPERIODLASTYEAR(dim_date[full_date])
)

Shipped Revenue YoY Growth % = 
DIVIDE(
    [Shipped FOB Revenue (USD)] - [Shipped Revenue PY (USD)],
    [Shipped Revenue PY (USD)]
)

Shipped Revenue MoM Growth % = 
VAR PrevMonthRev = CALCULATE([Shipped FOB Revenue (USD)], DATEADD(dim_date[full_date], -1, MONTH))
RETURN DIVIDE([Shipped FOB Revenue (USD)] - PrevMonthRev, PrevMonthRev)
```

### 1.4 Order Backlog, Cancellation Rate, Fulfilment Rate & ASP
```dax
Unfulfilled Order Backlog (PCS) = 
SUM(fact_sales_order_line[unfulfilled_backlog_qty_pcs])

Order Cancellation Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_sales_order_line), fact_sales_order_line[is_cancelled] = TRUE()),
    COUNTROWS(fact_sales_order_line)
)

Order Fulfilment Rate % = 
DIVIDE(
    SUM(fact_sales_order_line[shipped_qty_pcs]),
    CALCULATE(SUM(fact_sales_order_line[amended_order_qty_pcs]), fact_sales_order_line[is_cancelled] = FALSE())
)

Average Selling Price (ASP USD/Garment) = 
DIVIDE([Shipped FOB Revenue (USD)], SUM(fact_shipment_line[shipped_qty_pcs]))

Top 5 Buyer Concentration % = 
VAR Top5Rev = 
    CALCULATE(
        [Shipped FOB Revenue (USD)],
        TOPN(5, ALLSELECTED(dim_buyer), [Shipped FOB Revenue (USD)], DESC)
    )
VAR TotalRev = CALCULATE([Shipped FOB Revenue (USD)], ALLSELECTED(dim_buyer))
RETURN DIVIDE(Top5Rev, TotalRev)
```

---

## 2. Procurement & Supplier Performance KPIs

```dax
Total Procurement Value (USD) = 
SUM(fact_purchase_order_line[order_value_usd])

Total Procurement Value (BDT) = 
SUM(fact_purchase_order_line[order_value_bdt])

Imported Procurement Share % = 
DIVIDE(
    CALCULATE([Total Procurement Value (USD)], dim_supplier[domestic_import_classification] = "Imported"),
    [Total Procurement Value (USD)]
)

Supplier On-Time Delivery (OTD) Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_supplier_delivery), fact_supplier_delivery[is_on_time_delivery] = TRUE()),
    COUNTROWS(fact_supplier_delivery)
)

Supplier Material Rejection Rate % = 
DIVIDE(
    SUM(fact_supplier_delivery[rejected_qty]),
    SUM(fact_supplier_delivery[received_qty])
)

Average Procurement Lead Time (Days) = 
AVERAGEX(
    fact_purchase_order_line,
    DATEDIFF(fact_purchase_order_line[po_order_date], fact_purchase_order_line[expected_delivery_date], DAY)
)

Purchase Price Variance (PPV USD) = 
SUMX(
    fact_purchase_order_line,
    (fact_purchase_order_line[unit_cost_usd] - RELATED(dim_material[base_unit_cost_usd_2015]))
    * fact_purchase_order_line[ordered_qty]
)
```

---

## 3. Inventory & Working Capital KPIs

> **Note**: Inventory balances are semi-additive across time; `Closing Inventory Value (USD)` evaluates the ending monthly snapshot in the selected period.

```dax
Closing Inventory Value (USD) = 
VAR MaxDateKey = MAX(fact_inventory_snapshot_monthly[date_key])
RETURN
CALCULATE(
    SUM(fact_inventory_snapshot_monthly[inventory_value_usd]),
    fact_inventory_snapshot_monthly[date_key] = MaxDateKey
)

Closing Inventory Value (BDT) = 
VAR MaxDateKey = MAX(fact_inventory_snapshot_monthly[date_key])
RETURN
CALCULATE(
    SUM(fact_inventory_snapshot_monthly[inventory_value_bdt]),
    fact_inventory_snapshot_monthly[date_key] = MaxDateKey
)

Average Inventory Value (USD) = 
AVERAGEX(
    VALUES(dim_date[year_month]),
    CALCULATE(SUM(fact_inventory_snapshot_monthly[inventory_value_usd]))
)

Inventory Turnover Ratio (Annualized) = 
VAR AnnualizedCOGS = [Total Production Cost (USD)] * DIVIDE(12, DISTINCTCOUNT(dim_date[year_month]))
RETURN DIVIDE(AnnualizedCOGS, [Average Inventory Value (USD)])

Days Inventory Outstanding (DIO) = 
DIVIDE(365, [Inventory Turnover Ratio (Annualized)])

Slow-Moving & Aged Inventory Share (60+ Days) % = 
VAR AgedVal = 
    CALCULATE(
        [Closing Inventory Value (USD)],
        fact_inventory_snapshot_monthly[ageing_bucket] IN {"61-90 Days (Slow-Moving)", "90+ Days (Aged / Excess Risk)"}
    )
RETURN DIVIDE(AgedVal, [Closing Inventory Value (USD)])

Stockout Incident Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_inventory_snapshot_monthly), fact_inventory_snapshot_monthly[is_stockout_incident] = TRUE()),
    COUNTROWS(fact_inventory_snapshot_monthly)
)

Safety Stock Compliance Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_inventory_snapshot_monthly), fact_inventory_snapshot_monthly[is_below_safety_stock] = FALSE()),
    COUNTROWS(fact_inventory_snapshot_monthly)
)
```

---

## 4. Manufacturing & Productivity KPIs

- **Formula & Denominator Clarity**:
  - **Line Efficiency %**: `SUM(earned_standard_minutes) / (SUM(actual_labour_hours) * 60)` — compares standard allowed minutes produced against actual floor clock hours worked.
  - **Capacity Utilization %**: `SUM(actual_good_output_pcs) / SUM(monthly_Active_Factory_Capacity)` — measures actual good pieces against factory design capacity.

```dax
Planned Production (PCS) = SUM(fact_production_batch[planned_qty_pcs])

Actual Good Output (PCS) = SUM(fact_production_batch[actual_good_output_pcs])

Plan vs Actual Production Attainment % = 
DIVIDE([Actual Good Output (PCS)], [Planned Production (PCS)])

Production Line Efficiency % = 
DIVIDE(
    SUM(fact_production_batch[earned_standard_minutes]),
    SUM(fact_production_batch[actual_labour_hours]) * 60.0
)

Capacity Utilization % = 
VAR ActiveFactoryMonths = 
    SUMX(
        SUMMARIZE(fact_sustainability_monthly, dim_factory[factory_key], dim_date[year_month]),
        CALCULATE(MAX(dim_factory[base_monthly_capacity_pcs]))
    )
RETURN DIVIDE([Actual Good Output (PCS)], ActiveFactoryMonths)

Output per Labour Hour (PCS/Hr) = 
DIVIDE([Actual Good Output (PCS)], SUM(fact_production_batch[actual_labour_hours]))

Labour Cost per Garment (USD) = 
DIVIDE([Direct Labour Cost (USD)], [Actual Good Output (PCS)])

Material Wastage Rate % = 
DIVIDE(
    SUM(fact_material_consumption[wastage_qty]),
    SUM(fact_material_consumption[actual_material_qty])
)

Production Schedule Adherence % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_production_batch), fact_production_batch[schedule_delay_days] <= 1),
    COUNTROWS(fact_production_batch)
)
```

---

## 5. Quality & Compliance KPIs

```dax
First-Pass Yield (FPY) % = 
DIVIDE(
    SUM(fact_quality_inspection[inspected_qty_pcs]) - SUM(fact_quality_inspection[defective_qty_pcs]),
    SUM(fact_quality_inspection[inspected_qty_pcs])
)

Defect Rate (DHU / Defective %) = 
DIVIDE(
    SUM(fact_quality_inspection[defective_qty_pcs]),
    SUM(fact_quality_inspection[inspected_qty_pcs])
)

Garment Rework Rate % = 
DIVIDE(
    SUM(fact_quality_inspection[rework_qty_pcs]),
    SUM(fact_quality_inspection[inspected_qty_pcs])
)

Garment Rejection (Scrap) Rate % = 
DIVIDE(
    SUM(fact_quality_inspection[rejected_qty_pcs]),
    SUM(fact_quality_inspection[inspected_qty_pcs])
)

Total Cost of Poor Quality (COPQ USD) = 
SUM(fact_quality_inspection[estimated_quality_cost_usd])
    + SUM(fact_material_consumption[wastage_cost_usd])
```

---

## 6. Logistics & Customer Delivery KPIs

```dax
On-Time Shipment (OTS) Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_shipment_line), fact_shipment_line[is_on_time_shipment] = TRUE()),
    COUNTROWS(fact_shipment_line)
)

On-Time Delivery (OTD) Rate % = 
DIVIDE(
    CALCULATE(COUNTROWS(fact_shipment_line), fact_shipment_line[is_on_time_delivery] = TRUE()),
    COUNTROWS(fact_shipment_line)
)

On-Time In-Full (OTIF) Order Rate % = 
VAR FulfilledOnTimeOrders = 
    FILTER(
        fact_sales_order_line,
        fact_sales_order_line[is_cancelled] = FALSE()
        && fact_sales_order_line[shipped_qty_pcs] >= fact_sales_order_line[amended_order_qty_pcs]
        && CALCULATE(MIN(fact_shipment_line[is_on_time_delivery])) = TRUE()
    )
RETURN
DIVIDE(
    COUNTROWS(FulfilledOnTimeOrders),
    CALCULATE(COUNTROWS(fact_sales_order_line), fact_sales_order_line[is_cancelled] = FALSE())
)

Avg Order-to-Shipment Lead Time (Days) = 
AVERAGEX(
    fact_shipment_line,
    DATEDIFF(RELATED(dim_order_line[order_date]), fact_shipment_line[actual_ship_date], DAY)
)

Avg Vessel/Air Transit Time (Days) = 
AVERAGEX(
    fact_shipment_line,
    DATEDIFF(fact_shipment_line[actual_ship_date], fact_shipment_line[actual_arrival_date], DAY)
)

Freight Cost per Shipped Unit (USD) = 
DIVIDE(
    SUM(fact_shipment_line[freight_cost_usd]),
    SUM(fact_shipment_line[shipped_qty_pcs])
)
```

---

## 7. Finance & Operational Profitability KPIs

```dax
Direct Material & Trim Cost (USD) = 
CALCULATE(
    SUM(fact_cost_transaction[amount_usd]),
    dim_cost_category[cost_category_code] IN {"COST-DM", "COST-TRM"}
)

Direct Labour Cost (USD) = 
CALCULATE(
    SUM(fact_cost_transaction[amount_usd]),
    dim_cost_category[cost_category_code] = "COST-DL"
)

Factory Overhead & Utilities Cost (USD) = 
CALCULATE(
    SUM(fact_cost_transaction[amount_usd]),
    dim_cost_category[cost_group] IN {"Factory Overhead", "Quality & Compliance Cost"}
        || dim_cost_category[cost_category_code] = "COST-SUB"
)

Total Production Cost (COGS USD) = 
[Direct Material & Trim Cost (USD)] + [Direct Labour Cost (USD)] + [Factory Overhead & Utilities Cost (USD)]

Operational Gross Margin (USD) = 
[Shipped FOB Revenue (USD)] - [Total Production Cost (COGS USD)]

Operational Gross Margin % = 
DIVIDE([Operational Gross Margin (USD)], [Shipped FOB Revenue (USD)])

Operational Contribution Margin (USD) = 
[Shipped FOB Revenue (USD)]
    - [Direct Material & Trim Cost (USD)]
    - [Direct Labour Cost (USD)]
    - CALCULATE(SUM(fact_cost_transaction[amount_usd]), dim_cost_category[cost_behavior] = "Variable")

Operational Contribution Margin % = 
DIVIDE([Operational Contribution Margin (USD)], [Shipped FOB Revenue (USD)])

Total Conversion Cost per Garment (USD) = 
DIVIDE([Total Production Cost (COGS USD)], [Actual Good Output (PCS)])
```

---

## 8. Sustainability & Resource Efficiency KPIs

```dax
Electricity per Garment (kWh/PC) = 
DIVIDE(
    SUM(fact_sustainability_monthly[electricity_consumption_kwh]),
    SUM(fact_sustainability_monthly[monthly_output_pcs])
)

Natural Gas per Garment (m3/PC) = 
DIVIDE(
    SUM(fact_sustainability_monthly[natural_gas_consumption_m3]),
    SUM(fact_sustainability_monthly[monthly_output_pcs])
)

Water Withdrawal per Garment (Liters/PC) = 
DIVIDE(
    SUM(fact_sustainability_monthly[water_withdrawal_m3]) * 1000.0,
    SUM(fact_sustainability_monthly[monthly_output_pcs])
)

Solid Fabric Waste Recycling Rate % = 
DIVIDE(
    SUM(fact_sustainability_monthly[recycled_material_kg]),
    SUM(fact_sustainability_monthly[solid_fabric_waste_kg])
)

Renewable Solar Energy Share % = 
DIVIDE(
    SUM(fact_sustainability_monthly[renewable_solar_kwh]),
    SUM(fact_sustainability_monthly[electricity_consumption_kwh])
)

Carbon Footprint per Garment (kg CO2e/PC) = 
DIVIDE(
    SUM(fact_sustainability_monthly[estimated_carbon_emissions_kg_co2e]),
    SUM(fact_sustainability_monthly[monthly_output_pcs])
)
```

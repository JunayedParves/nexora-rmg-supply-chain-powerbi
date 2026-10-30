"""
Programmatic Power BI Project (.pbip) Builder for:
Nexora Apparels Ltd. Dashboard (20-Year Bangladesh RMG Supply Chain Intelligence Platform)

Generates:
1. Complete TMDL Semantic Model (22 star-schema Parquet tables + Executive_Measures table with 65+ DAX measures + 64 relationships)
2. Complete 8-Page Executive Power BI Report (PBIR v2.0.0 / report 3.3.0 / page 2.1.0 / visualContainer 2.5.0)
"""

import csv
import json
import os
import shutil
import uuid
from pathlib import Path

WORKSPACE_ROOT = Path(r"c:\Users\Junayed\Documents\RMG Company")
DATA_ROOT = WORKSPACE_ROOT / "rmg_supply_chain_intelligence"
SCHEMA_JSON_PATH = DATA_ROOT / "schemas" / "parquet_schema.json"
RELS_CSV_PATH = DATA_ROOT / "documentation" / "model_relationships.csv"
DICT_CSV_PATH = DATA_ROOT / "documentation" / "data_dictionary.csv"

PBIP_MODEL_DIR = WORKSPACE_ROOT / "Nexora Apparels Ltd. Dashboard.SemanticModel"
PBIP_REPORT_DIR = WORKSPACE_ROOT / "Nexora Apparels Ltd. Dashboard.Report"


def deterministic_guid(seed_str: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"nexora.rmg.pbip.{seed_str}"))


def load_metadata():
    with open(SCHEMA_JSON_PATH, "r", encoding="utf-8") as f:
        parquet_schemas = json.load(f)
    with open(RELS_CSV_PATH, "r", encoding="utf-8") as f:
        relationships = list(csv.DictReader(f))
    col_descriptions = {}
    if DICT_CSV_PATH.exists():
        with open(DICT_CSV_PATH, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                col_descriptions[(row["table_name"], row["column_name"])] = row.get("description", "")
    return parquet_schemas, relationships, col_descriptions


def map_tmdl_datatype(parquet_type: str, col_name: str):
    if parquet_type == "int64":
        return "int64", "0"
    elif parquet_type in ("double", "decimal128(18, 2)", "decimal128(18, 3)"):
        if "pct" in col_name or "share" in col_name or "rate" in col_name and "exchange" not in col_name and "tariff" not in col_name and "freight" not in col_name:
            return "double", "#,0.00"
        elif "usd" in col_name:
            return "double", "$#,0.00;($#,0.00);$#,0.00"
        elif "bdt" in col_name:
            return "double", "৳#,0.00;(৳#,0.00);৳#,0.00"
        elif parquet_type == "decimal128(18, 3)":
            return "double", "#,0.000"
        else:
            return "double", "#,0.00"
    elif parquet_type == "bool":
        return "boolean", None
    elif parquet_type == "date32[day]":
        return "dateTime", "yyyy-mm-dd"
    else:
        return "string", None


PRIMARY_KEYS = {
    "dim_date": "date_key",
    "dim_company": "company_key",
    "dim_factory": "factory_key",
    "dim_factory_line": "production_line_key",
    "dim_buyer": "buyer_key",
    "dim_supplier": "supplier_key",
    "dim_product": "product_key",
    "dim_material": "material_key",
    "dim_cost_category": "cost_category_key",
    "dim_order_line": "order_line_key",
    "fact_sales_order_line": "order_line_key",
    "fact_purchase_order_line": "purchase_order_line_key",
    "fact_supplier_delivery": "delivery_key",
    "fact_production_batch": "production_batch_key",
    "fact_material_consumption": "consumption_key",
    "fact_quality_inspection": "inspection_key",
    "fact_shipment_line": "shipment_line_key",
    "fact_inventory_snapshot_monthly": "inventory_snapshot_key",
    "fact_cost_transaction": "cost_transaction_key",
    "fact_workforce_monthly": "workforce_month_key",
    "fact_sustainability_monthly": "sustainability_month_key",
    "fact_macro_monthly": "macro_month_key",
}

SORT_BY_COLUMNS = {
    ("dim_date", "month_name"): "calendar_month",
    ("dim_date", "month_short"): "calendar_month",
    ("dim_date", "weekday_name"): "iso_weekday",
    ("dim_date", "calendar_quarter_label"): "calendar_quarter",
    ("dim_date", "fiscal_quarter_label"): "fiscal_quarter",
}


def build_table_tmdl(table_name: str, table_meta: dict, col_descriptions: dict) -> str:
    lines = []
    lines.append(f"table {table_name}")
    lines.append(f"\tlineageTag: {deterministic_guid('table.' + table_name)}")
    lines.append("")

    pk_col = PRIMARY_KEYS.get(table_name)
    is_dim = table_name.startswith("dim_")

    for col in table_meta["columns"]:
        col_name = col["name"]
        pq_type = col["parquet_type"]
        tmdl_type, fmt_str = map_tmdl_datatype(pq_type, col_name)
        desc = col_descriptions.get((table_name, col_name), "")

        if desc:
            safe_desc = desc.replace('"', "'")
            lines.append(f"\t/// {safe_desc}")
        lines.append(f"\tcolumn {col_name}")
        lines.append(f"\t\tdataType: {tmdl_type}")
        if col_name == pk_col:
            lines.append("\t\tisKey")
        if fmt_str:
            lines.append(f"\t\tformatString: {fmt_str}")
        lines.append(f"\t\tlineageTag: {deterministic_guid(f'col.{table_name}.{col_name}')}")

        if (table_name, col_name) in SORT_BY_COLUMNS:
            lines.append(f"\t\tsortByColumn: {SORT_BY_COLUMNS[(table_name, col_name)]}")

        # SummarizeBy logic
        if tmdl_type in ("int64", "double"):
            if (
                is_dim
                or col_name.endswith("_key")
                or col_name.endswith("_id")
                or col_name.endswith("_number")
                or "year" in col_name
                or "month" in col_name
                or "quarter" in col_name
                or "day" in col_name
                or "week" in col_name
            ):
                lines.append("\t\tsummarizeBy: none")
            else:
                lines.append("\t\tsummarizeBy: sum")
        else:
            lines.append("\t\tsummarizeBy: none")

        lines.append(f"\t\tsourceColumn: {col_name}")
        if tmdl_type == "dateTime":
            lines.append("\t\tannotation UnderlyingDateTimeDataType = Date")
        lines.append("")

    # Partition M query
    lines.append(f"\tpartition {table_name} = m")
    lines.append("\t\tmode: import")
    lines.append("\t\tsource =")
    if is_dim:
        parquet_file = str(DATA_ROOT / "data" / "dimensions" / table_name / "part-00000.parquet")
        lines.append("\t\t\tlet")
        lines.append(f'\t\t\t    Source = Parquet.Document(File.Contents("{parquet_file}"))')
        lines.append("\t\t\tin")
        lines.append("\t\t\t    Source")
    else:
        fact_folder = str(DATA_ROOT / "data" / "facts" / table_name)
        lines.append("\t\t\tlet")
        lines.append(f'\t\t\t    Source = Folder.Files("{fact_folder}"),')
        lines.append('\t\t\t    FilteredFiles = Table.SelectRows(Source, each [Extension] = ".parquet"),')
        lines.append("\t\t\t    CombinedParquet = Table.Combine(List.Transform(FilteredFiles[Content], each Parquet.Document(_)))")
        lines.append("\t\t\tin")
        lines.append("\t\t\t    CombinedParquet")
    lines.append("")
    lines.append("\tannotation PBI_ResultType = Table")
    lines.append("")
    return "\n".join(lines)


EXECUTIVE_MEASURES = [
    # 01. Commercial & Orders
    (
        "Order Intake Value (USD)",
        "CALCULATE ( SUM ( fact_sales_order_line[net_order_value_usd] ), fact_sales_order_line[is_cancelled] = FALSE () )",
        "$#,0;($#,0);$#,0",
        "01. Commercial & Orders",
        "Net confirmed sales order intake value in USD excluding cancelled lines.",
    ),
    (
        "Order Intake Value (BDT)",
        "CALCULATE ( SUM ( fact_sales_order_line[net_order_value_bdt] ), fact_sales_order_line[is_cancelled] = FALSE () )",
        "৳#,0;(৳#,0);৳#,0",
        "01. Commercial & Orders",
        "Net confirmed sales order intake value in BDT excluding cancelled lines.",
    ),
    (
        "Gross Order Value (USD)",
        "SUM ( fact_sales_order_line[gross_order_value_usd] )",
        "$#,0;($#,0);$#,0",
        "01. Commercial & Orders",
        "Total gross order value in USD including cancelled and discounted lines.",
    ),
    (
        "Ordered Quantity (PCS)",
        "CALCULATE ( SUM ( fact_sales_order_line[amended_order_qty_pcs] ), fact_sales_order_line[is_cancelled] = FALSE () )",
        "#,0",
        "01. Commercial & Orders",
        "Total amended order quantity in pieces for active/fulfilled orders.",
    ),
    (
        "Unfulfilled Order Backlog (PCS)",
        "CALCULATE ( SUM ( fact_sales_order_line[unfulfilled_backlog_qty_pcs] ), fact_sales_order_line[is_cancelled] = FALSE () )",
        "#,0",
        "01. Commercial & Orders",
        "Remaining unshipped backlog quantity in pieces on active orders.",
    ),
    (
        "Order Cancellation Rate %",
        "DIVIDE ( CALCULATE ( COUNTROWS ( fact_sales_order_line ), fact_sales_order_line[is_cancelled] = TRUE () ), COUNTROWS ( fact_sales_order_line ), 0 )",
        "0.00%",
        "01. Commercial & Orders",
        "Percentage of sales order lines cancelled by buyers.",
    ),
    (
        "Order Fulfilment Rate %",
        "DIVIDE ( CALCULATE ( SUM ( fact_sales_order_line[shipped_qty_pcs] ), fact_sales_order_line[is_cancelled] = FALSE () ), [Ordered Quantity (PCS)], 0 )",
        "0.0%",
        "01. Commercial & Orders",
        "Ratio of shipped quantity to amended ordered quantity on non-cancelled orders.",
    ),
    (
        "Average Selling Price (USD)",
        "DIVIDE ( [Shipped FOB Revenue (USD)], [Shipped Quantity (PCS)], 0 )",
        "$#,0.00",
        "01. Commercial & Orders",
        "Realized FOB average selling price per garment in USD.",
    ),
    (
        "Active Buyers Count",
        "DISTINCTCOUNT ( fact_sales_order_line[buyer_key] )",
        "#,0",
        "01. Commercial & Orders",
        "Count of distinct international buyers placing orders in the period.",
    ),

    # 02. Revenue & Profitability
    (
        "Shipped FOB Revenue (USD)",
        "SUM ( fact_shipment_line[fob_revenue_usd] )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Total realized Free-on-Board (FOB) export revenue in USD upon shipment.",
    ),
    (
        "Shipped FOB Revenue (BDT)",
        "SUM ( fact_shipment_line[fob_revenue_bdt] )",
        "৳#,0;(৳#,0);৳#,0",
        "02. Revenue & Profitability",
        "Total realized Free-on-Board (FOB) export revenue in BDT upon shipment.",
    ),
    (
        "Delivered Revenue (USD)",
        "SUM ( fact_shipment_line[delivered_revenue_usd] )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Total realized revenue for buyer-accepted delivered garments in USD.",
    ),
    (
        "Shipped Revenue PY (USD)",
        "VAR _MinDate = MIN ( dim_date[full_date] ) VAR _MaxDate = MAX ( dim_date[full_date] ) VAR _PrevMinKey = ( YEAR ( _MinDate ) - 1 ) * 10000 + MONTH ( _MinDate ) * 100 + DAY ( _MinDate ) VAR _PrevMaxKey = ( YEAR ( _MaxDate ) - 1 ) * 10000 + MONTH ( _MaxDate ) * 100 + DAY ( _MaxDate ) RETURN CALCULATE ( [Shipped FOB Revenue (USD)], REMOVEFILTERS ( dim_date ), dim_date[date_key] >= _PrevMinKey && dim_date[date_key] <= _PrevMaxKey )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Prior-year Shipped FOB Revenue in USD across any calendar or fiscal slice.",
    ),
    (
        "Shipped Revenue YoY Growth %",
        "VAR _Curr = [Shipped FOB Revenue (USD)] VAR _Prev = [Shipped Revenue PY (USD)] RETURN IF ( _Prev > 0, DIVIDE ( _Curr - _Prev, _Prev, 0 ), BLANK () )",
        "+0.0%;-0.0%;0.0%",
        "02. Revenue & Profitability",
        "Year-over-Year percentage growth in Shipped FOB Revenue (USD).",
    ),
    (
        "Total Cost Ledger (USD)",
        "SUM ( fact_cost_transaction[amount_usd] )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Total cost recorded in the unified cost ledger in USD across all categories.",
    ),
    (
        "Total Cost Ledger (BDT)",
        "SUM ( fact_cost_transaction[amount_bdt] )",
        "৳#,0;(৳#,0);৳#,0",
        "02. Revenue & Profitability",
        "Total cost recorded in the unified cost ledger in BDT across all categories.",
    ),
    (
        "Total Production Cost (COGS USD)",
        "CALCULATE ( SUM ( fact_cost_transaction[amount_usd] ), dim_cost_category[income_statement_classification] = \"COGS\" )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Total Cost of Goods Sold (COGS) in USD from the cost transaction ledger.",
    ),
    (
        "Total Production Cost (COGS BDT)",
        "CALCULATE ( SUM ( fact_cost_transaction[amount_bdt] ), dim_cost_category[income_statement_classification] = \"COGS\" )",
        "৳#,0;(৳#,0);৳#,0",
        "02. Revenue & Profitability",
        "Total Cost of Goods Sold (COGS) in BDT from the cost transaction ledger.",
    ),
    (
        "Direct Material Cost (USD)",
        "CALCULATE ( SUM ( fact_cost_transaction[amount_usd] ), dim_cost_category[cost_group] = \"Direct Material\" )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Direct fabric, yarn, trims, and accessories cost in USD.",
    ),
    (
        "Direct Labour Cost (USD)",
        "CALCULATE ( SUM ( fact_cost_transaction[amount_usd] ), dim_cost_category[cost_group] = \"Direct Labour\" )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Direct factory sewing, cutting, and finishing labour cost in USD.",
    ),
    (
        "Factory Overhead Cost (USD)",
        "CALCULATE ( SUM ( fact_cost_transaction[amount_usd] ), dim_cost_category[cost_group] IN { \"Factory Overhead\", \"Quality & Compliance\" } )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Factory utilities, depreciation, maintenance, compliance, and quality costs in USD.",
    ),
    (
        "Selling & Logistics Cost (USD)",
        "CALCULATE ( SUM ( fact_cost_transaction[amount_usd] ), dim_cost_category[income_statement_classification] = \"Selling & Distribution Expense\" )",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Inland transport and international freight expense in USD.",
    ),
    (
        "Operational Gross Margin (USD)",
        "[Shipped FOB Revenue (USD)] - [Total Production Cost (COGS USD)]",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Operational gross margin in USD (Shipped FOB Revenue minus COGS).",
    ),
    (
        "Operational Gross Margin (BDT)",
        "[Shipped FOB Revenue (BDT)] - [Total Production Cost (COGS BDT)]",
        "৳#,0;(৳#,0);৳#,0",
        "02. Revenue & Profitability",
        "Operational gross margin in BDT (Shipped FOB Revenue minus COGS).",
    ),
    (
        "Operational Gross Margin %",
        "DIVIDE ( [Operational Gross Margin (USD)], [Shipped FOB Revenue (USD)], 0 )",
        "0.0%",
        "02. Revenue & Profitability",
        "Operational Gross Margin as a percentage of Shipped FOB Revenue (USD).",
    ),
    (
        "Net Operating Contribution (USD)",
        "[Shipped FOB Revenue (USD)] - [Total Cost Ledger (USD)]",
        "$#,0;($#,0);$#,0",
        "02. Revenue & Profitability",
        "Operating contribution after COGS, logistics, and quality costs in USD.",
    ),
    (
        "Net Operating Margin %",
        "DIVIDE ( [Net Operating Contribution (USD)], [Shipped FOB Revenue (USD)], 0 )",
        "0.0%",
        "02. Revenue & Profitability",
        "Net operating contribution percentage of FOB revenue.",
    ),

    # 03. Procurement & Suppliers
    (
        "Total Procurement Value (USD)",
        "SUM ( fact_purchase_order_line[order_value_usd] )",
        "$#,0;($#,0);$#,0",
        "03. Procurement & Suppliers",
        "Total raw material and trim purchase order value in USD.",
    ),
    (
        "Total Procurement Value (BDT)",
        "SUM ( fact_purchase_order_line[order_value_bdt] )",
        "৳#,0;(৳#,0);৳#,0",
        "03. Procurement & Suppliers",
        "Total raw material and trim purchase order value in BDT.",
    ),
    (
        "Documented Delivery Value (USD)",
        "SUM ( fact_supplier_delivery[documented_material_cost_usd] )",
        "$#,0;($#,0);$#,0",
        "03. Procurement & Suppliers",
        "Total value of supplier material deliveries received at factory gate in USD.",
    ),
    (
        "Imported Procurement Share %",
        "DIVIDE ( CALCULATE ( [Total Procurement Value (USD)], dim_supplier[domestic_import_classification] = \"Imported\" ), [Total Procurement Value (USD)], 0 )",
        "0.0%",
        "03. Procurement & Suppliers",
        "Share of procurement spend sourced from international imported suppliers.",
    ),
    (
        "Domestic Backward Linkage Share %",
        "DIVIDE ( CALCULATE ( [Total Procurement Value (USD)], dim_supplier[domestic_import_classification] = \"Domestic\" ), [Total Procurement Value (USD)], 0 )",
        "0.0%",
        "03. Procurement & Suppliers",
        "Share of procurement spend sourced from domestic Bangladeshi spinners/mills.",
    ),
    (
        "Supplier On-Time Delivery %",
        "DIVIDE ( CALCULATE ( COUNTROWS ( fact_supplier_delivery ), fact_supplier_delivery[is_on_time_delivery] = TRUE () ), COUNTROWS ( fact_supplier_delivery ), 0 )",
        "0.0%",
        "03. Procurement & Suppliers",
        "Percentage of supplier material deliveries received on or before expected PO date.",
    ),
    (
        "Avg Supplier Delay (Days)",
        "AVERAGE ( fact_supplier_delivery[delivery_delay_days] )",
        "0.0",
        "03. Procurement & Suppliers",
        "Average delivery delay in days across supplier GRN receipts.",
    ),
    (
        "Supplier Material Rejection Rate %",
        "DIVIDE ( SUM ( fact_supplier_delivery[rejected_qty] ), SUM ( fact_supplier_delivery[received_qty] ), 0 )",
        "0.00%",
        "03. Procurement & Suppliers",
        "Percentage of delivered raw material quantity rejected upon incoming inspection.",
    ),
    (
        "Total Material Cost Consumed (USD)",
        "SUM ( fact_material_consumption[total_material_cost_usd] )",
        "$#,0;($#,0);$#,0",
        "03. Procurement & Suppliers",
        "Total cost of raw materials consumed in production batches in USD.",
    ),
    (
        "Material Wastage Cost (USD)",
        "SUM ( fact_material_consumption[wastage_cost_usd] )",
        "$#,0;($#,0);$#,0",
        "03. Procurement & Suppliers",
        "Cost of excess raw material wastage above BOM standard allowance in USD.",
    ),
    (
        "BOM Material Wastage Rate %",
        "DIVIDE ( SUM ( fact_material_consumption[wastage_qty] ), SUM ( fact_material_consumption[actual_material_qty] ), 0 )",
        "0.00%",
        "03. Procurement & Suppliers",
        "Weighted average material wastage percentage across production batches.",
    ),
    (
        "Purchase Price Variance (USD)",
        "SUMX ( fact_purchase_order_line, fact_purchase_order_line[ordered_qty] * ( fact_purchase_order_line[unit_cost_usd] - RELATED ( dim_material[base_unit_cost_usd_2015] ) ) )",
        "$#,0;($#,0);$#,0",
        "03. Procurement & Suppliers",
        "Purchase price variance against 2015 base material standard cost in USD.",
    ),

    # 04. Inventory & Working Capital
    (
        "Closing Inventory Value (USD)",
        "VAR _MaxDateKey = MAX ( fact_inventory_snapshot_monthly[date_key] ) RETURN CALCULATE ( SUM ( fact_inventory_snapshot_monthly[inventory_value_usd] ), fact_inventory_snapshot_monthly[date_key] = _MaxDateKey )",
        "$#,0;($#,0);$#,0",
        "04. Inventory & Working Capital",
        "Semi-additive closing inventory valuation in USD at the end of the selected period.",
    ),
    (
        "Closing Inventory Value (BDT)",
        "VAR _MaxDateKey = MAX ( fact_inventory_snapshot_monthly[date_key] ) RETURN CALCULATE ( SUM ( fact_inventory_snapshot_monthly[inventory_value_bdt] ), fact_inventory_snapshot_monthly[date_key] = _MaxDateKey )",
        "৳#,0;(৳#,0);৳#,0",
        "04. Inventory & Working Capital",
        "Semi-additive closing inventory valuation in BDT at the end of the selected period.",
    ),
    (
        "Average Inventory Value (USD)",
        "AVERAGEX ( VALUES ( dim_date[year_month] ), CALCULATE ( SUM ( fact_inventory_snapshot_monthly[inventory_value_usd] ) ) )",
        "$#,0;($#,0);$#,0",
        "04. Inventory & Working Capital",
        "Average monthly inventory valuation in USD across the selected timeframe.",
    ),
    (
        "Inventory Turnover Ratio",
        "DIVIDE ( [Total Production Cost (COGS USD)], [Average Inventory Value (USD)], 0 )",
        "0.00",
        "04. Inventory & Working Capital",
        "Ratio of COGS to Average Inventory Value.",
    ),
    (
        "Days Inventory Outstanding (DIO)",
        "DIVIDE ( [Average Inventory Value (USD)], [Total Production Cost (COGS USD)], 0 ) * 365",
        "0.0",
        "04. Inventory & Working Capital",
        "Average number of days inventory is held before consumption/shipment.",
    ),
    (
        "Slow & Obsolete Stock (90+ Days USD)",
        "VAR _MaxDateKey = MAX ( fact_inventory_snapshot_monthly[date_key] ) RETURN CALCULATE ( SUM ( fact_inventory_snapshot_monthly[inventory_value_usd] ), fact_inventory_snapshot_monthly[date_key] = _MaxDateKey, fact_inventory_snapshot_monthly[ageing_bucket] IN { \"91-180 Days\", \"180+ Days\" } )",
        "$#,0;($#,0);$#,0",
        "04. Inventory & Working Capital",
        "Closing inventory value aged over 90 days in USD.",
    ),
    (
        "Slow & Obsolete Stock Share %",
        "DIVIDE ( [Slow & Obsolete Stock (90+ Days USD)], [Closing Inventory Value (USD)], 0 )",
        "0.0%",
        "04. Inventory & Working Capital",
        "Percentage of closing inventory value aged over 90 days.",
    ),
    (
        "Stockout Incident Rate %",
        "DIVIDE ( CALCULATE ( COUNTROWS ( fact_inventory_snapshot_monthly ), fact_inventory_snapshot_monthly[is_stockout_incident] = TRUE () ), COUNTROWS ( fact_inventory_snapshot_monthly ), 0 )",
        "0.00%",
        "04. Inventory & Working Capital",
        "Percentage of monthly factory-item inventory snapshots experiencing a stockout.",
    ),
    (
        "Safety Stock Compliance %",
        "1 - DIVIDE ( CALCULATE ( COUNTROWS ( fact_inventory_snapshot_monthly ), fact_inventory_snapshot_monthly[is_below_safety_stock] = TRUE () ), COUNTROWS ( fact_inventory_snapshot_monthly ), 0 )",
        "0.0%",
        "04. Inventory & Working Capital",
        "Percentage of monthly inventory snapshots maintaining stock at or above safety threshold.",
    ),

    # 05. Manufacturing & Productivity
    (
        "Planned Production (PCS)",
        "SUM ( fact_production_batch[planned_qty_pcs] )",
        "#,0",
        "05. Manufacturing & Productivity",
        "Total planned production quantity in pieces across scheduled batches.",
    ),
    (
        "Actual Good Output (PCS)",
        "SUM ( fact_production_batch[actual_good_output_pcs] )",
        "#,0",
        "05. Manufacturing & Productivity",
        "Total first-quality + reworked good garment output in pieces.",
    ),
    (
        "Plan vs Actual Attainment %",
        "DIVIDE ( [Actual Good Output (PCS)], [Planned Production (PCS)], 0 )",
        "0.0%",
        "05. Manufacturing & Productivity",
        "Manufacturing attainment of actual good output against planned batch quantity.",
    ),
    (
        "Production Line Efficiency %",
        "DIVIDE ( SUM ( fact_production_batch[earned_standard_minutes] ), SUM ( fact_production_batch[actual_labour_hours] ) * 60, 0 )",
        "0.0%",
        "05. Manufacturing & Productivity",
        "True industrial engineering sewing efficiency: Earned Standard Minutes / Available Labour Minutes.",
    ),
    (
        "Output per Labour Hour (PCS)",
        "DIVIDE ( [Actual Good Output (PCS)], SUM ( fact_production_batch[actual_labour_hours] ), 0 )",
        "0.00",
        "05. Manufacturing & Productivity",
        "Physical garment output produced per direct operator/helper labour hour.",
    ),
    (
        "Machine Downtime Hours",
        "SUM ( fact_production_batch[machine_downtime_hours] )",
        "#,0",
        "05. Manufacturing & Productivity",
        "Total production line downtime hours due to machine breakdown, power, or material wait.",
    ),
    (
        "Labour Cost per Garment (USD)",
        "DIVIDE ( [Direct Labour Cost (USD)], [Actual Good Output (PCS)], 0 )",
        "$#,0.00",
        "05. Manufacturing & Productivity",
        "Direct labour cost in USD per good garment produced.",
    ),

    # 06. Quality & Compliance
    (
        "Inspected Quantity (PCS)",
        "SUM ( fact_quality_inspection[inspected_qty_pcs] )",
        "#,0",
        "06. Quality & Compliance",
        "Total garments inspected across inline and final AQL quality audits.",
    ),
    (
        "Defective Quantity (PCS)",
        "SUM ( fact_quality_inspection[defective_qty_pcs] )",
        "#,0",
        "06. Quality & Compliance",
        "Total defective garments identified during quality inspections.",
    ),
    (
        "First-Pass Yield (FPY) %",
        "1 - DIVIDE ( [Defective Quantity (PCS)], [Inspected Quantity (PCS)], 0 )",
        "0.0%",
        "06. Quality & Compliance",
        "Percentage of inspected garments passing inspection defect-free on the first pass.",
    ),
    (
        "AQL Defect Rate %",
        "DIVIDE ( [Defective Quantity (PCS)], [Inspected Quantity (PCS)], 0 )",
        "0.00%",
        "06. Quality & Compliance",
        "Overall garment defect rate across quality inspections.",
    ),
    (
        "Garment Rework Rate %",
        "DIVIDE ( SUM ( fact_quality_inspection[rework_qty_pcs] ), [Inspected Quantity (PCS)], 0 )",
        "0.00%",
        "06. Quality & Compliance",
        "Percentage of inspected garments requiring rectification/rework.",
    ),
    (
        "Garment Rejection Rate %",
        "DIVIDE ( SUM ( fact_quality_inspection[rejected_qty_pcs] ), [Inspected Quantity (PCS)], 0 )",
        "0.00%",
        "06. Quality & Compliance",
        "Percentage of inspected garments permanently scrapped/rejected.",
    ),
    (
        "Estimated Quality Cost (USD)",
        "SUM ( fact_quality_inspection[estimated_quality_cost_usd] )",
        "$#,0;($#,0);$#,0",
        "06. Quality & Compliance",
        "Direct rework and scrap quality cost estimated at inspection in USD.",
    ),
    (
        "Total Cost of Poor Quality (USD)",
        "[Estimated Quality Cost (USD)] + [Material Wastage Cost (USD)]",
        "$#,0;($#,0);$#,0",
        "06. Quality & Compliance",
        "Combined Cost of Poor Quality (COPQ): garment rework/scrap + excess BOM material wastage in USD.",
    ),

    # 07. Logistics & OTIF
    (
        "Shipped Quantity (PCS)",
        "SUM ( fact_shipment_line[shipped_qty_pcs] )",
        "#,0",
        "07. Logistics & OTIF",
        "Total garment pieces shipped via sea and air freight.",
    ),
    (
        "Delivered Quantity (PCS)",
        "SUM ( fact_shipment_line[delivered_qty_pcs] )",
        "#,0",
        "07. Logistics & OTIF",
        "Total garment pieces accepted at buyer destination warehouse.",
    ),
    (
        "On-Time Shipment (OTS) %",
        "DIVIDE ( CALCULATE ( COUNTROWS ( fact_shipment_line ), fact_shipment_line[is_on_time_shipment] = TRUE () ), COUNTROWS ( fact_shipment_line ), 0 )",
        "0.0%",
        "07. Logistics & OTIF",
        "Percentage of export shipments departing port on or before scheduled ship date.",
    ),
    (
        "On-Time Delivery (OTD) %",
        "DIVIDE ( CALCULATE ( COUNTROWS ( fact_shipment_line ), fact_shipment_line[is_on_time_delivery] = TRUE () ), COUNTROWS ( fact_shipment_line ), 0 )",
        "0.0%",
        "07. Logistics & OTIF",
        "Percentage of export shipments arriving at buyer destination on or before confirmed delivery date.",
    ),
    (
        "On-Time In-Full (OTIF) %",
        "DIVIDE ( CALCULATE ( COUNTROWS ( fact_shipment_line ), fact_shipment_line[is_on_time_delivery] = TRUE (), fact_shipment_line[is_partial_shipment] = FALSE () ), COUNTROWS ( fact_shipment_line ), 0 )",
        "0.0%",
        "07. Logistics & OTIF",
        "Percentage of shipments delivered both On-Time and In-Full without partial split shortages.",
    ),
    (
        "Total Freight Cost (USD)",
        "SUM ( fact_shipment_line[freight_cost_usd] ) + SUM ( fact_shipment_line[inland_logistics_cost_usd] )",
        "$#,0;($#,0);$#,0",
        "07. Logistics & OTIF",
        "Combined international freight and domestic inland transport cost in USD.",
    ),
    (
        "Air Freight Revenue Share %",
        "DIVIDE ( CALCULATE ( [Shipped FOB Revenue (USD)], fact_shipment_line[shipping_mode] = \"Air\" ), [Shipped FOB Revenue (USD)], 0 )",
        "0.00%",
        "07. Logistics & OTIF",
        "Percentage of FOB export revenue shipped via expedited air freight.",
    ),

    # 08. Workforce & Payroll
    (
        "Active Headcount",
        "VAR _MaxDateKey = MAX ( fact_workforce_monthly[date_key] ) RETURN CALCULATE ( SUM ( fact_workforce_monthly[active_headcount] ), fact_workforce_monthly[date_key] = _MaxDateKey )",
        "#,0",
        "08. Workforce & Payroll",
        "Semi-additive active workforce headcount at the end of the selected period.",
    ),
    (
        "Total Workforce Payroll (USD)",
        "SUM ( fact_workforce_monthly[total_payroll_usd] )",
        "$#,0;($#,0);$#,0",
        "08. Workforce & Payroll",
        "Total monthly workforce payroll (base + allowances/Eid bonus + overtime) in USD.",
    ),
    (
        "Total Workforce Payroll (BDT)",
        "SUM ( fact_workforce_monthly[total_payroll_bdt] )",
        "৳#,0;(৳#,0);৳#,0",
        "08. Workforce & Payroll",
        "Total monthly workforce payroll (base + allowances/Eid bonus + overtime) in BDT.",
    ),
    (
        "Overtime Hours",
        "SUM ( fact_workforce_monthly[overtime_hours] )",
        "#,0",
        "08. Workforce & Payroll",
        "Total worker overtime hours logged across factory departments.",
    ),
    (
        "Overtime Share of Payroll %",
        "DIVIDE ( SUM ( fact_workforce_monthly[overtime_expense_bdt] ), SUM ( fact_workforce_monthly[total_payroll_bdt] ), 0 )",
        "0.0%",
        "08. Workforce & Payroll",
        "Overtime expense as a percentage of total factory payroll.",
    ),
    (
        "Absenteeism Rate %",
        "AVERAGE ( fact_workforce_monthly[absenteeism_rate_pct] ) / 100",
        "0.00%",
        "08. Workforce & Payroll",
        "Average monthly worker absenteeism rate percentage.",
    ),

    # 09. Sustainability & Macro
    (
        "Electricity per Garment (kWh)",
        "DIVIDE ( SUM ( fact_sustainability_monthly[electricity_consumption_kwh] ), SUM ( fact_sustainability_monthly[monthly_output_pcs] ), 0 )",
        "0.000",
        "09. Sustainability & Macro",
        "Total grid and solar electricity consumed in kWh per garment produced.",
    ),
    (
        "Renewable Solar Share %",
        "DIVIDE ( SUM ( fact_sustainability_monthly[renewable_solar_kwh] ), SUM ( fact_sustainability_monthly[electricity_consumption_kwh] ), 0 )",
        "0.0%",
        "09. Sustainability & Macro",
        "Percentage of factory electricity generated by rooftop solar PV.",
    ),
    (
        "Water per Garment (Liters)",
        "DIVIDE ( SUM ( fact_sustainability_monthly[water_withdrawal_m3] ) * 1000, SUM ( fact_sustainability_monthly[monthly_output_pcs] ), 0 )",
        "0.0",
        "09. Sustainability & Macro",
        "Water withdrawal in liters per garment produced.",
    ),
    (
        "Carbon Footprint (kg CO2e/PC)",
        "DIVIDE ( SUM ( fact_sustainability_monthly[estimated_carbon_emissions_kg_co2e] ), SUM ( fact_sustainability_monthly[monthly_output_pcs] ), 0 )",
        "0.000",
        "09. Sustainability & Macro",
        "Estimated Scope 1+2 carbon emissions in kg CO2e per garment produced.",
    ),
    (
        "Fabric Waste Recycling Rate %",
        "DIVIDE ( SUM ( fact_sustainability_monthly[recycled_material_kg] ), SUM ( fact_sustainability_monthly[solid_fabric_waste_kg] ), 0 )",
        "0.0%",
        "09. Sustainability & Macro",
        "Percentage of solid cutting/sewing jhut fabric waste recycled or upcycled.",
    ),
    (
        "Average BDT/USD Exchange Rate",
        "AVERAGE ( fact_macro_monthly[bdt_usd_exchange_rate] )",
        "৳#,0.00",
        "09. Sustainability & Macro",
        "Average BDT per 1 USD exchange rate across the selected period.",
    ),
    (
        "Statutory Minimum Wage (BDT)",
        "MAX ( fact_macro_monthly[statutory_min_wage_entry_bdt] )",
        "৳#,0",
        "09. Sustainability & Macro",
        "Gazetted Bangladesh garment entry-level statutory minimum wage in BDT.",
    ),
    (
        "CPI Inflation YoY %",
        "AVERAGE ( fact_macro_monthly[cpi_inflation_yoy_pct] ) / 100",
        "0.0%",
        "09. Sustainability & Macro",
        "Average Bangladesh Consumer Price Index (CPI) annual inflation rate.",
    ),
    (
        "BGMEA National RMG Export ($B)",
        "AVERAGE ( fact_macro_monthly[bgmea_fy_total_rmg_export_usd_bn] )",
        "$#,0.00B",
        "09. Sustainability & Macro",
        "Published BGMEA national Bangladesh RMG export benchmark in USD Billions.",
    ),
    (
        "Container Freight Index",
        "AVERAGE ( fact_macro_monthly[container_freight_rate_index] )",
        "#,0.0",
        "09. Sustainability & Macro",
        "Global container freight rate index (2015 = 100).",
    ),
]


def build_executive_measures_tmdl() -> str:
    lines = []
    lines.append("table Executive_Measures")
    lines.append(f"\tlineageTag: {deterministic_guid('table.Executive_Measures')}")
    lines.append("")

    for name, expr, fmt, folder, desc in EXECUTIVE_MEASURES:
        lines.append(f"\t/// {desc}")
        lines.append(f"\tmeasure '{name}' = {expr}")
        lines.append(f'\t\tformatString: "{fmt}"')
        lines.append(f"\t\tdisplayFolder: {folder}")
        lines.append(f"\t\tlineageTag: {deterministic_guid('measure.' + name)}")
        lines.append("")

    lines.append("\tcolumn Measure_Group")
    lines.append("\t\tdataType: string")
    lines.append("\t\tisHidden")
    lines.append(f"\t\tlineageTag: {deterministic_guid('col.Executive_Measures.Measure_Group')}")
    lines.append("\t\tsummarizeBy: none")
    lines.append("\t\tsourceColumn: Measure_Group")
    lines.append("")
    lines.append("\tpartition Executive_Measures = m")
    lines.append("\t\tmode: import")
    lines.append("\t\tsource =")
    lines.append("\t\t\tlet")
    lines.append('\t\t\t    Source = #table({"Measure_Group"}, {{"Nexora RMG Executive Intelligence"}})')
    lines.append("\t\t\tin")
    lines.append("\t\t\t    Source")
    lines.append("")
    lines.append("\tannotation PBI_ResultType = Table")
    lines.append("")
    return "\n".join(lines)


def build_relationships_tmdl(relationships: list) -> str:
    lines = []
    for idx, r in enumerate(relationships):
        ft = r["from_table"]
        fc = r["from_column"]
        tt = r["to_table"]
        tc = r["to_column"]
        active = r["relationship_status"].strip().lower() == "active"
        rel_id = deterministic_guid(f"rel.{idx}.{ft}.{fc}.{tt}.{tc}")

        lines.append(f"relationship {rel_id}")
        if not active:
            lines.append("\tisActive: false")
        lines.append(f"\tfromColumn: {ft}.{fc}")
        lines.append(f"\ttoColumn: {tt}.{tc}")
        lines.append("")
    return "\n".join(lines)


def build_model_tmdl(table_names: list) -> str:
    lines = [
        "model Model",
        "\tculture: en-US",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: en-US",
        "\tvalueFilterBehavior: independent",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 1",
        "",
        'annotation PBI_ProTooling = ["DevMode"]',
        "",
    ]
    all_tables = ["Executive_Measures"] + table_names
    q_order = json.dumps(all_tables)
    lines.append(f"annotation PBI_QueryOrder = {q_order}")
    lines.append("")
    for t in all_tables:
        lines.append(f"ref table {t}")
    lines.append("")
    lines.append("ref relationship")
    lines[-1] = "ref cultureInfo en-US"
    lines.append("")
    return "\n".join(lines)


# ==============================================================================
# REPORT (PBIR) BUILDER HELPERS
# ==============================================================================

def col_field(entity: str, prop: str, display_name: str = None):
    proj = {
        "field": {
            "Column": {
                "Expression": {
                    "SourceRef": {
                        "Entity": entity
                    }
                },
                "Property": prop
            }
        },
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
        "active": True
    }
    if display_name:
        proj["displayName"] = display_name
    return proj


def measure_field(prop: str, display_name: str = None, entity: str = "Executive_Measures"):
    proj = {
        "field": {
            "Measure": {
                "Expression": {
                    "SourceRef": {
                        "Entity": entity
                    }
                },
                "Property": prop
            }
        },
        "queryRef": f"{entity}.{prop}",
        "nativeQueryRef": prop,
        "active": True
    }
    if display_name:
        proj["displayName"] = display_name
    return proj


def make_container_objects(title_text: str, subtitle_text: str = None, bg_color: str = "#FFFFFF", border_color: str = "#E2E8F0", show_title: bool = True):
    vco = {
        "title": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true" if show_title else "false"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title_text}'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "13D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}},
                }
            }
        ],
        "background": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{bg_color}'"}}}}},
                    "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": f"'{border_color}'"}}}}},
                    "radius": {"expr": {"Literal": {"Value": "8D"}}},
                    "width": {"expr": {"Literal": {"Value": "1D"}}},
                }
            }
        ],
    }
    if subtitle_text:
        vco["subTitle"] = [
            {
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{subtitle_text}'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}},
                }
            }
        ]
    return vco


def make_header_banner(visual_id: str, page_title: str, page_subtitle: str):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {
            "x": 16,
            "y": 10,
            "z": 100,
            "width": 1888,
            "height": 66,
            "tabOrder": 100,
        },
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": f"NEXORA APPARELS GROUP  |  {page_title}",
                                            "textStyle": {
                                                "fontFamily": "Segoe UI Semibold",
                                                "fontSize": "16pt",
                                                "fontWeight": "bold",
                                                "color": "#FFFFFF",
                                            },
                                        }
                                    ]
                                },
                                {
                                    "textRuns": [
                                        {
                                            "value": page_subtitle,
                                            "textStyle": {
                                                "fontFamily": "Segoe UI",
                                                "fontSize": "10pt",
                                                "color": "#CBD5E1",
                                            },
                                        }
                                    ]
                                },
                            ]
                        }
                    }
                ]
            },
            "visualContainerObjects": {
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}},
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E293B'"}}}}},
                            "radius": {"expr": {"Literal": {"Value": "8D"}}},
                            "width": {"expr": {"Literal": {"Value": "1D"}}},
                        }
                    }
                ],
                "padding": [
                    {
                        "properties": {
                            "top": {"expr": {"Literal": {"Value": "8D"}}},
                            "bottom": {"expr": {"Literal": {"Value": "8D"}}},
                            "left": {"expr": {"Literal": {"Value": "74D"}}},
                            "right": {"expr": {"Literal": {"Value": "18D"}}},
                        }
                    }
                ],
            },
            "drillFilterOtherVisuals": True,
        },
    }


def make_image_visual(visual_id: str, x: int, y: int, width: int, height: int, z: int, icon_filename: str):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height,
            "tabOrder": z,
        },
        "visual": {
            "visualType": "image",
            "objects": {
                "general": [
                    {
                        "properties": {
                            "imageUrl": {
                                "expr": {
                                    "ResourcePackageItem": {
                                        "PackageName": "RegisteredResources",
                                        "PackageType": 1,
                                        "ItemName": icon_filename,
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            "drillFilterOtherVisuals": True,
        },
    }


MEASURE_TO_ICON = {
    "Shipped FOB Revenue (USD)": "kpi_revenue_usd.svg",
    "Order Intake Value (USD)": "kpi_order_intake.svg",
    "Operational Gross Margin %": "kpi_gross_margin.svg",
    "Operational Gross Margin (USD)": "kpi_gross_margin.svg",
    "On-Time In-Full (OTIF) %": "kpi_otif_delivery.svg",
    "Closing Inventory Value (USD)": "kpi_inventory_val.svg",
    "Closing Inventory Value (BDT)": "kpi_inventory_val.svg",
    "Actual Good Output (PCS)": "kpi_good_output.svg",
    "Shipped Revenue YoY Growth %": "kpi_yoy_growth.svg",
    "Average Selling Price (USD)": "kpi_asp_price.svg",
    "Average BDT/USD Exchange Rate": "kpi_fx_rate.svg",
    "Statutory Minimum Wage (BDT)": "kpi_min_wage.svg",
    "BGMEA National RMG Export ($B)": "kpi_bgmea_export.svg",
    "Container Freight Index": "kpi_freight_idx.svg",
    "Ordered Quantity (PCS)": "kpi_order_qty.svg",
    "Unfulfilled Order Backlog (PCS)": "kpi_backlog.svg",
    "Order Cancellation Rate %": "kpi_cancellation.svg",
    "Order Fulfilment Rate %": "kpi_fulfilment.svg",
    "Total Procurement Value (USD)": "kpi_procurement.svg",
    "Imported Procurement Share %": "kpi_import_share.svg",
    "Supplier On-Time Delivery %": "kpi_supplier_otd.svg",
    "Supplier Material Rejection Rate %": "kpi_rejection.svg",
    "Avg Supplier Delay (Days)": "kpi_delay_days.svg",
    "Material Wastage Cost (USD)": "kpi_wastage_cost.svg",
    "Inventory Turnover Ratio": "kpi_turnover_dio.svg",
    "Days Inventory Outstanding (DIO)": "kpi_turnover_dio.svg",
    "Stockout Incident Rate %": "kpi_stockout.svg",
    "Safety Stock Compliance %": "kpi_safety_stock.svg",
    "Plan vs Actual Attainment %": "kpi_attainment.svg",
    "Production Line Efficiency %": "kpi_efficiency.svg",
    "Output per Labour Hour (PCS)": "kpi_labour_prod.svg",
    "Labour Cost per Garment (USD)": "kpi_labour_cost.svg",
    "Active Headcount": "kpi_headcount.svg",
    "First-Pass Yield (FPY) %": "kpi_fpy_quality.svg",
    "AQL Defect Rate %": "kpi_rejection.svg",
    "Garment Rework Rate %": "kpi_rework.svg",
    "Total Cost of Poor Quality (USD)": "kpi_wastage_cost.svg",
    "On-Time Shipment (OTS) %": "kpi_ots_ship.svg",
    "Total Production Cost (COGS USD)": "kpi_cogs_cost.svg",
    "Electricity per Garment (kWh)": "kpi_electricity.svg",
    "Renewable Solar Share %": "kpi_solar_share.svg",
    "Carbon Footprint (kg CO2e/PC)": "kpi_carbon_co2.svg",
}


PAGE_TO_HEADER_ICON = {
    "p1": "page_01_executive.svg",
    "p2": "page_02_macro.svg",
    "p3": "page_03_commercial.svg",
    "p4": "page_04_procurement.svg",
    "p5": "page_05_inventory.svg",
    "p6": "page_06_manufacturing.svg",
    "p7": "page_07_quality.svg",
    "p8": "page_08_sustainability.svg",
}


def make_page_navigator(visual_id: str):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {
            "x": 980,
            "y": 84,
            "z": 200,
            "width": 924,
            "height": 56,
            "tabOrder": 200,
        },
        "visual": {
            "visualType": "pageNavigator",
            "visualContainerObjects": {
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}},
                            "radius": {"expr": {"Literal": {"Value": "8D"}}},
                            "width": {"expr": {"Literal": {"Value": "1D"}}},
                        }
                    }
                ],
                "padding": [
                    {
                        "properties": {
                            "top": {"expr": {"Literal": {"Value": "6D"}}},
                            "bottom": {"expr": {"Literal": {"Value": "6D"}}},
                            "left": {"expr": {"Literal": {"Value": "10D"}}},
                            "right": {"expr": {"Literal": {"Value": "10D"}}},
                        }
                    }
                ],
            },
            "drillFilterOtherVisuals": True,
        },
    }


def make_slicer(visual_id: str, x: int, y: int, width: int, height: int, z: int, entity: str, prop: str, title_text: str):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height,
            "tabOrder": z,
        },
        "visual": {
            "visualType": "slicer",
            "query": {
                "queryState": {
                    "Values": {
                        "projections": [col_field(entity, prop, title_text)]
                    }
                }
            },
            "objects": {
                "data": [
                    {
                        "properties": {
                            "mode": {"expr": {"Literal": {"Value": "'Dropdown'"}}}
                        }
                    }
                ],
                "header": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "false"}}}
                        }
                    }
                ],
            },
            "visualContainerObjects": {
                "title": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "text": {"expr": {"Literal": {"Value": f"'{title_text}'"}}},
                            "fontSize": {"expr": {"Literal": {"Value": "9.5D"}}},
                            "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#475569'"}}}}},
                        }
                    }
                ],
                "background": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}},
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ],
                "border": [
                    {
                        "properties": {
                            "show": {"expr": {"Literal": {"Value": "true"}}},
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#CBD5E1'"}}}}},
                            "radius": {"expr": {"Literal": {"Value": "8D"}}},
                            "width": {"expr": {"Literal": {"Value": "1D"}}},
                        }
                    }
                ],
                "padding": [
                    {
                        "properties": {
                            "top": {"expr": {"Literal": {"Value": "4D"}}},
                            "bottom": {"expr": {"Literal": {"Value": "4D"}}},
                            "left": {"expr": {"Literal": {"Value": "10D"}}},
                            "right": {"expr": {"Literal": {"Value": "10D"}}},
                        }
                    }
                ],
            },
            "drillFilterOtherVisuals": True,
        },
    }


def make_kpi_card(visual_id: str, x: int, y: int, width: int, height: int, z: int, measure_name: str, label: str = None):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": z,
            "width": width,
            "height": height,
            "tabOrder": z,
        },
        "visual": {
            "visualType": "cardVisual",
            "query": {
                "queryState": {
                    "Data": {
                        "projections": [measure_field(measure_name, label or measure_name)]
                    }
                }
            },
            "drillFilterOtherVisuals": True,
        },
    }


def make_combo_chart(
    visual_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
    title: str,
    subtitle: str,
    cat_entity: str,
    cat_prop: str,
    cat_label: str,
    col_measures: list,
    line_measures: list,
    sort_by_cat_asc: bool = False,
):
    sort_field = (
        {"Column": {"Expression": {"SourceRef": {"Entity": cat_entity}}, "Property": cat_prop}}
        if sort_by_cat_asc
        else {"Measure": {"Expression": {"SourceRef": {"Entity": "Executive_Measures"}}, "Property": col_measures[0]}}
    )
    sort_dir = "Ascending" if sort_by_cat_asc else "Descending"

    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z},
        "visual": {
            "visualType": "lineClusteredColumnComboChart",
            "query": {
                "queryState": {
                    "Category": {"projections": [col_field(cat_entity, cat_prop, cat_label)]},
                    "ColumnY": {"projections": [measure_field(m) for m in col_measures]},
                    "Y2": {"projections": [measure_field(m) for m in line_measures]},
                },
                "sortDefinition": {
                    "sort": [{"field": sort_field, "direction": sort_dir}],
                    "isDefaultSort": False,
                },
            },
            "visualContainerObjects": make_container_objects(title, subtitle),
            "drillFilterOtherVisuals": True,
        },
    }


def make_bar_or_column_chart(
    visual_id: str,
    visual_type: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
    title: str,
    subtitle: str,
    cat_entity: str,
    cat_prop: str,
    cat_label: str,
    y_measures: list,
    series_entity: str = None,
    series_prop: str = None,
    series_label: str = None,
    sort_by_cat_asc: bool = False,
):
    qs = {
        "Category": {"projections": [col_field(cat_entity, cat_prop, cat_label)]},
        "Y": {"projections": [measure_field(m) for m in y_measures]},
    }
    if series_entity and series_prop:
        qs["Series"] = {"projections": [col_field(series_entity, series_prop, series_label)]}

    sort_field = (
        {"Column": {"Expression": {"SourceRef": {"Entity": cat_entity}}, "Property": cat_prop}}
        if sort_by_cat_asc
        else {"Measure": {"Expression": {"SourceRef": {"Entity": "Executive_Measures"}}, "Property": y_measures[0]}}
    )
    sort_dir = "Ascending" if sort_by_cat_asc else "Descending"

    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z},
        "visual": {
            "visualType": visual_type,
            "query": {
                "queryState": qs,
                "sortDefinition": {
                    "sort": [{"field": sort_field, "direction": sort_dir}],
                    "isDefaultSort": False,
                },
            },
            "visualContainerObjects": make_container_objects(title, subtitle),
            "drillFilterOtherVisuals": True,
        },
    }


def make_donut_chart(
    visual_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
    title: str,
    subtitle: str,
    cat_entity: str,
    cat_prop: str,
    cat_label: str,
    measure_name: str,
):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z},
        "visual": {
            "visualType": "donutChart",
            "query": {
                "queryState": {
                    "Category": {"projections": [col_field(cat_entity, cat_prop, cat_label)]},
                    "Y": {"projections": [measure_field(measure_name)]},
                },
                "sortDefinition": {
                    "sort": [
                        {
                            "field": {
                                "Measure": {
                                    "Expression": {"SourceRef": {"Entity": "Executive_Measures"}},
                                    "Property": measure_name,
                                }
                            },
                            "direction": "Descending",
                        }
                    ],
                    "isDefaultSort": False,
                },
            },
            "visualContainerObjects": make_container_objects(title, subtitle),
            "drillFilterOtherVisuals": True,
        },
    }


def make_table_visual(
    visual_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    z: int,
    title: str,
    subtitle: str,
    columns: list,
    measures: list,
    sort_measure: str = None,
    sort_asc_col: tuple = None,
):
    projections = []
    for ent, prop, lbl in columns:
        projections.append(col_field(ent, prop, lbl))
    for m in measures:
        projections.append(measure_field(m))

    if sort_asc_col:
        sort_field = {
            "Column": {
                "Expression": {"SourceRef": {"Entity": sort_asc_col[0]}},
                "Property": sort_asc_col[1],
            }
        }
        sort_dir = "Ascending"
    else:
        sm = sort_measure or measures[0]
        sort_field = {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": "Executive_Measures"}},
                "Property": sm,
            }
        }
        sort_dir = "Descending"

    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
        "name": visual_id,
        "position": {"x": x, "y": y, "z": z, "width": width, "height": height, "tabOrder": z},
        "visual": {
            "visualType": "tableEx",
            "query": {
                "queryState": {
                    "Values": {"projections": projections}
                },
                "sortDefinition": {
                    "sort": [{"field": sort_field, "direction": sort_dir}],
                    "isDefaultSort": False,
                },
            },
            "visualContainerObjects": make_container_objects(title, subtitle),
            "drillFilterOtherVisuals": True,
        },
    }


def build_standard_page_scaffold(page_prefix: str, page_title: str, page_subtitle: str, fourth_slicer: tuple, kpi_measures: list):
    visuals = []
    # Header banner + Header domain icon
    visuals.append(make_header_banner(f"{page_prefix}_hdr01", page_title, page_subtitle))
    hdr_icon = PAGE_TO_HEADER_ICON.get(page_prefix, "page_01_executive.svg")
    visuals.append(make_image_visual(f"{page_prefix}_hdricon", 28, 19, 48, 48, 150, hdr_icon))

    # Page Navigator
    visuals.append(make_page_navigator(f"{page_prefix}_nav01"))

    # 4 Slicers on the left side of the filter bar (x=16..968, y=84, height=56)
    slicer_defs = [
        ("dim_date", "calendar_year", "📅 Calendar Year"),
        ("dim_company", "company_name", "🏢 RMG Company"),
        ("dim_date", "fiscal_year", "📆 BD Fiscal Year"),
        (fourth_slicer[0], fourth_slicer[1], f"🔎 {fourth_slicer[2]}"),
    ]
    for i, (s_ent, s_prop, s_lbl) in enumerate(slicer_defs):
        sx = 16 + i * 238
        visuals.append(make_slicer(f"{page_prefix}_slc0{i+1}", sx, 84, 230, 56, 300 + i, s_ent, s_prop, s_lbl))

    # 6 KPI Cards across y=148, height=106, width=304 each + Top-Right KPI Icon Badge
    for i, m_name in enumerate(kpi_measures):
        kx = int(round(16 + i * 316.8))
        kw = 304 if i < 5 else 1904 - kx
        visuals.append(make_kpi_card(f"{page_prefix}_kpi0{i+1}", kx, 148, kw, 106, 400 + i, m_name))
        kpi_icon = MEASURE_TO_ICON.get(m_name, "kpi_revenue_usd.svg")
        visuals.append(make_image_visual(f"{page_prefix}_kpiico0{i+1}", kx + kw - 50, 160, 36, 36, 450 + i, kpi_icon))

    return visuals


def build_all_pages():
    pages = []

    # ==========================================================================
    # PAGE 1: Executive Overview (Keep existing page ID e5224d3fb000009d5a9d)
    # ==========================================================================
    p1_id = "e5224d3fb000009d5a9d"
    p1_visuals = build_standard_page_scaffold(
        "p1",
        "EXECUTIVE SUPPLY CHAIN COMMAND CENTER (2006–2025)",
        "20-Year Multi-Company Bangladesh RMG Commercial, Operational, Working Capital & OTIF Intelligence",
        ("dim_buyer", "market_region", "Export Market Region"),
        [
            "Shipped FOB Revenue (USD)",
            "Order Intake Value (USD)",
            "Operational Gross Margin %",
            "On-Time In-Full (OTIF) %",
            "Closing Inventory Value (USD)",
            "Actual Good Output (PCS)",
        ],
    )
    # Row 1 charts (y=264, height=392)
    p1_visuals.append(
        make_combo_chart(
            "p1_vis01", 16, 264, 1140, 392, 501,
            "20-Year Shipped FOB Revenue (USD) & Operational Gross Margin % Trajectory",
            "Historical growth across GFC (2008-09), Rana Plaza Accord (2013), COVID-19 (2020) & FX Energy Transition (2022-25)",
            "dim_date", "calendar_year", "Calendar Year",
            ["Shipped FOB Revenue (USD)", "Total Production Cost (COGS USD)"],
            ["Operational Gross Margin %"],
            sort_by_cat_asc=True,
        )
    )
    p1_visuals.append(
        make_donut_chart(
            "p1_vis02", 1170, 264, 734, 392, 502,
            "Shipped FOB Revenue by Export Market Region",
            "Diversification across EU, North America, UK, Asia-Pacific & Non-Traditional Markets",
            "dim_buyer", "market_region", "Export Market Region",
            "Shipped FOB Revenue (USD)",
        )
    )
    # Row 2 charts (y=668, height=396)
    p1_visuals.append(
        make_bar_or_column_chart(
            "p1_vis03", "clusteredBarChart", 16, 668, 760, 396, 503,
            "FOB Revenue & Operational Gross Margin by RMG Company",
            "Benchmarking the 8 operating company archetypes in the Nexora Group",
            "dim_company", "company_name", "Company Name",
            ["Shipped FOB Revenue (USD)", "Operational Gross Margin (USD)"],
        )
    )
    p1_visuals.append(
        make_table_visual(
            "p1_vis04", 790, 668, 1114, 396, 504,
            "Multi-Company Executive Benchmarking Scorecard",
            "End-to-end commercial, manufacturing, quality, and customer delivery KPIs by company",
            [
                ("dim_company", "company_name", "Company"),
                ("dim_company", "operating_archetype", "Operating Archetype"),
            ],
            [
                "Order Intake Value (USD)",
                "Shipped FOB Revenue (USD)",
                "Operational Gross Margin %",
                "Production Line Efficiency %",
                "First-Pass Yield (FPY) %",
                "On-Time In-Full (OTIF) %",
            ],
        )
    )
    pages.append((p1_id, "01. Executive Command", p1_visuals))

    # ==========================================================================
    # PAGE 2: 20-Year Macro & Industry Structural Trends
    # ==========================================================================
    p2_id = "page2_macro_trends00"
    p2_visuals = build_standard_page_scaffold(
        "p2",
        "MACROECONOMIC & INDUSTRY STRUCTURAL DYNAMICS (2006–2025)",
        "BDT/USD Exchange Rate, Wage Gazette Revisions, BGMEA National Export Context & Knit/Woven Crossover",
        ("fact_macro_monthly", "macro_regime_label", "Macro Regime"),
        [
            "Shipped Revenue YoY Growth %",
            "Average Selling Price (USD)",
            "Average BDT/USD Exchange Rate",
            "Statutory Minimum Wage (BDT)",
            "BGMEA National RMG Export ($B)",
            "Container Freight Index",
        ],
    )
    p2_visuals.append(
        make_combo_chart(
            "p2_vis01", 16, 264, 936, 392, 501,
            "Group FOB Revenue (USD) vs. BGMEA National RMG Export Benchmark ($B)",
            "Calibrated synthetic group revenue tracking Bangladesh national garment export expansion",
            "dim_date", "calendar_year", "Calendar Year",
            ["Shipped FOB Revenue (USD)"],
            ["BGMEA National RMG Export ($B)"],
            sort_by_cat_asc=True,
        )
    )
    p2_visuals.append(
        make_bar_or_column_chart(
            "p2_vis02", "stackedAreaChart", 968, 264, 936, 392, 502,
            "20-Year Product Mix Structural Crossover: Knit vs. Woven Garments",
            "Tracking knitwear expansion and post-2020 activewear/MMF structural shift",
            "dim_date", "calendar_year", "Calendar Year",
            ["Shipped FOB Revenue (USD)"],
            series_entity="dim_product", series_prop="knit_woven_classification", series_label="Knit / Woven",
            sort_by_cat_asc=True,
        )
    )
    p2_visuals.append(
        make_combo_chart(
            "p2_vis03", 16, 668, 860, 396, 503,
            "Gazetted Minimum Wage Step-Jumps (BDT) vs. Output per Labour Hour",
            "Wage revisions (2006, 2010, 2013, 2018, 2023) offset by factory automation and IE efficiency",
            "dim_date", "calendar_year", "Calendar Year",
            ["Statutory Minimum Wage (BDT)"],
            ["Output per Labour Hour (PCS)"],
            sort_by_cat_asc=True,
        )
    )
    p2_visuals.append(
        make_table_visual(
            "p2_vis04", 890, 668, 1014, 396, 504,
            "20-Year Annual Macroeconomic & Operational Calibration Table",
            "Annual BDT/USD exchange rate, CPI inflation, statutory minimum wage, YoY growth, and unit economics",
            [("dim_date", "calendar_year", "Year")],
            [
                "Average BDT/USD Exchange Rate",
                "CPI Inflation YoY %",
                "Statutory Minimum Wage (BDT)",
                "Shipped FOB Revenue (USD)",
                "Shipped Revenue YoY Growth %",
                "Operational Gross Margin %",
                "Labour Cost per Garment (USD)",
            ],
            sort_asc_col=("dim_date", "calendar_year"),
        )
    )
    pages.append((p2_id, "02. Macro & 20Y Trends", p2_visuals))

    # ==========================================================================
    # PAGE 3: Commercial, Buyers & Export Market Diversification
    # ==========================================================================
    p3_id = "page3_commercial0000"
    p3_visuals = build_standard_page_scaffold(
        "p3",
        "COMMERCIAL DEMAND, BUYERS & EXPORT MARKET INTELLIGENCE",
        "Order Book Intake, Backlog, Cancellation Rates, Buyer Concentration & Product Category Mix",
        ("dim_buyer", "market_classification", "Market Classification"),
        [
            "Order Intake Value (USD)",
            "Ordered Quantity (PCS)",
            "Unfulfilled Order Backlog (PCS)",
            "Order Cancellation Rate %",
            "Order Fulfilment Rate %",
            "Average Selling Price (USD)",
        ],
    )
    p3_visuals.append(
        make_bar_or_column_chart(
            "p3_vis01", "clusteredBarChart", 16, 264, 680, 392, 501,
            "Top International Buyers by Shipped FOB Revenue & Order Intake",
            "Customer revenue concentration across global retail, fast-fashion, and sportswear brands",
            "dim_buyer", "buyer_name", "Buyer Name",
            ["Shipped FOB Revenue (USD)", "Order Intake Value (USD)"],
        )
    )
    p3_visuals.append(
        make_bar_or_column_chart(
            "p3_vis02", "clusteredColumnChart", 710, 264, 650, 392, 502,
            "Order Intake & Shipped FOB Revenue by Garment Product Category",
            "Performance across T-Shirts, Denim, Trousers, Sweaters, Activewear, Outerwear & Shirts",
            "dim_product", "product_category", "Product Category",
            ["Order Intake Value (USD)", "Shipped FOB Revenue (USD)"],
        )
    )
    p3_visuals.append(
        make_donut_chart(
            "p3_vis03", 1374, 264, 530, 392, 503,
            "Traditional vs. Non-Traditional Export Markets",
            "Strategic diversification into Japan, Australia, India & Middle East",
            "dim_buyer", "market_classification", "Market Class",
            "Shipped FOB Revenue (USD)",
        )
    )
    p3_visuals.append(
        make_table_visual(
            "p3_vis04", 16, 668, 1888, 396, 504,
            "International Buyer Commercial & Delivery Performance Matrix",
            "Buyer-level order intake, realized FOB revenue, average selling price (ASP), cancellation rate, and OTIF reliability",
            [
                ("dim_buyer", "buyer_name", "Buyer"),
                ("dim_buyer", "customer_segment", "Customer Segment"),
                ("dim_buyer", "destination_country", "Destination Country"),
                ("dim_buyer", "market_region", "Market Region"),
            ],
            [
                "Order Intake Value (USD)",
                "Shipped FOB Revenue (USD)",
                "Shipped Quantity (PCS)",
                "Average Selling Price (USD)",
                "Order Cancellation Rate %",
                "Order Fulfilment Rate %",
                "On-Time In-Full (OTIF) %",
            ],
        )
    )
    pages.append((p3_id, "03. Commercial & Buyers", p3_visuals))

    # ==========================================================================
    # PAGE 4: Procurement, Suppliers & Backward Linkage
    # ==========================================================================
    p4_id = "page4_procurement000"
    p4_visuals = build_standard_page_scaffold(
        "p4",
        "PROCUREMENT, SUPPLIER RELIABILITY & MATERIAL COST INTELLIGENCE",
        "Domestic Backward Linkage vs. Imported Fabrics/Yarns, Supplier OTD, Lead-Time Delays & BOM Wastage",
        ("dim_supplier", "origin_country", "Supplier Country"),
        [
            "Total Procurement Value (USD)",
            "Imported Procurement Share %",
            "Supplier On-Time Delivery %",
            "Supplier Material Rejection Rate %",
            "Avg Supplier Delay (Days)",
            "Material Wastage Cost (USD)",
        ],
    )
    p4_visuals.append(
        make_bar_or_column_chart(
            "p4_vis01", "clusteredBarChart", 16, 264, 680, 392, 501,
            "Procurement Spend & Delivered Material Value by Supplier Country",
            "Bangladesh domestic backward linkage vs. China, India, Vietnam, Pakistan & Indonesia imports",
            "dim_supplier", "origin_country", "Origin Country",
            ["Total Procurement Value (USD)", "Documented Delivery Value (USD)"],
        )
    )
    p4_visuals.append(
        make_combo_chart(
            "p4_vis02", 710, 264, 650, 392, 502,
            "Production Material Consumption Cost (USD) & BOM Wastage Rate %",
            "Material cost and cutting/dyeing wastage across Yarn, Knit/Woven Fabric, Trims & Chemicals",
            "dim_material", "material_category", "Material Category",
            ["Total Material Cost Consumed (USD)", "Material Wastage Cost (USD)"],
            ["BOM Material Wastage Rate %"],
        )
    )
    p4_visuals.append(
        make_donut_chart(
            "p4_vis03", 1374, 264, 530, 392, 503,
            "Domestic vs. Imported Raw Material Spend",
            "Measuring local spinning/knitting backward linkage vs. imported woven fabrics",
            "dim_supplier", "domestic_import_classification", "Sourcing Origin",
            "Total Procurement Value (USD)",
        )
    )
    p4_visuals.append(
        make_table_visual(
            "p4_vis04", 16, 668, 1888, 396, 504,
            "Supplier Performance, Lead-Time Delay & Quality Rejection Scorecard",
            "Granular supplier evaluation across PO spend, on-time delivery %, average delay days, incoming rejection rate, and price variance",
            [
                ("dim_supplier", "supplier_name", "Supplier Name"),
                ("dim_supplier", "supplier_type", "Supplier Type"),
                ("dim_supplier", "origin_country", "Origin Country"),
                ("dim_supplier", "domestic_import_classification", "Domestic / Imported"),
            ],
            [
                "Total Procurement Value (USD)",
                "Documented Delivery Value (USD)",
                "Supplier On-Time Delivery %",
                "Avg Supplier Delay (Days)",
                "Supplier Material Rejection Rate %",
                "Purchase Price Variance (USD)",
            ],
        )
    )
    pages.append((p4_id, "04. Procurement & Suppliers", p4_visuals))

    # ==========================================================================
    # PAGE 5: Inventory & Working Capital Diagnostics
    # ==========================================================================
    p5_id = "page5_inventory00000"
    p5_visuals = build_standard_page_scaffold(
        "p5",
        "INVENTORY VALUATION, STOCK AGEING & WORKING CAPITAL DIAGNOSTICS",
        "Semi-Additive Closing Stock across Raw Material, WIP & Finished Goods, DIO, Stockouts & Obsolete Stock",
        ("fact_inventory_snapshot_monthly", "stock_type", "Inventory Stage"),
        [
            "Closing Inventory Value (USD)",
            "Closing Inventory Value (BDT)",
            "Inventory Turnover Ratio",
            "Days Inventory Outstanding (DIO)",
            "Stockout Incident Rate %",
            "Safety Stock Compliance %",
        ],
    )
    p5_visuals.append(
        make_bar_or_column_chart(
            "p5_vis01", "clusteredColumnChart", 16, 264, 1140, 392, 501,
            "Closing Inventory Valuation (USD) by Year & Stock Stage (2006–2025)",
            "Year-end working capital tied up in Raw Materials, Work-in-Progress (WIP), and Finished Goods",
            "dim_date", "calendar_year", "Calendar Year",
            ["Closing Inventory Value (USD)"],
            series_entity="fact_inventory_snapshot_monthly", series_prop="stock_type", series_label="Stock Stage",
            sort_by_cat_asc=True,
        )
    )
    p5_visuals.append(
        make_donut_chart(
            "p5_vis02", 1170, 264, 734, 392, 502,
            "Closing Inventory Share by Stock Stage",
            "Distribution of working capital across RM, WIP & Finished Goods",
            "fact_inventory_snapshot_monthly", "stock_type", "Stock Stage",
            "Closing Inventory Value (USD)",
        )
    )
    p5_visuals.append(
        make_bar_or_column_chart(
            "p5_vis03", "clusteredBarChart", 16, 668, 680, 396, 503,
            "Closing Inventory Value (USD) by Stock Ageing Bucket",
            "Identifying slow-moving (91-180 Days) and obsolete/dead stock (180+ Days)",
            "fact_inventory_snapshot_monthly", "ageing_bucket", "Ageing Bucket",
            ["Closing Inventory Value (USD)"],
        )
    )
    p5_visuals.append(
        make_table_visual(
            "p5_vis04", 710, 668, 1194, 396, 504,
            "Factory Working Capital, Ageing & Stockout Diagnostic Matrix",
            "Factory-level closing inventory value, slow/obsolete stock exposure, stockout incident frequency, and BOM wastage cost",
            [
                ("dim_factory", "factory_name", "Factory"),
                ("dim_factory", "industrial_zone", "Industrial Zone"),
                ("dim_factory", "product_specialization", "Specialization"),
            ],
            [
                "Closing Inventory Value (USD)",
                "Slow & Obsolete Stock (90+ Days USD)",
                "Slow & Obsolete Stock Share %",
                "Stockout Incident Rate %",
                "Safety Stock Compliance %",
                "Material Wastage Cost (USD)",
            ],
        )
    )
    pages.append((p5_id, "05. Inventory & Capital", p5_visuals))

    # ==========================================================================
    # PAGE 6: Manufacturing Productivity & Workforce Analytics
    # ==========================================================================
    p6_id = "page6_manufacturing0"
    p6_visuals = build_standard_page_scaffold(
        "p6",
        "MANUFACTURING PRODUCTIVITY, LINE EFFICIENCY & WORKFORCE ANALYTICS",
        "Sewing Line SMV Efficiency, Plan Attainment, Machine Downtime, Headcount, Payroll & Overtime",
        ("dim_factory", "industrial_zone", "Industrial Zone"),
        [
            "Actual Good Output (PCS)",
            "Plan vs Actual Attainment %",
            "Production Line Efficiency %",
            "Output per Labour Hour (PCS)",
            "Labour Cost per Garment (USD)",
            "Active Headcount",
        ],
    )
    p6_visuals.append(
        make_combo_chart(
            "p6_vis01", 16, 264, 1020, 392, 501,
            "Actual Good Output (PCS) & Sewing Line Efficiency % by Factory",
            "Comparing physical output scale with industrial engineering SMV line efficiency across factories",
            "dim_factory", "factory_name", "Factory Name",
            ["Actual Good Output (PCS)"],
            ["Production Line Efficiency %"],
        )
    )
    p6_visuals.append(
        make_combo_chart(
            "p6_vis02", 1050, 264, 854, 392, 502,
            "Annual Workforce Payroll (USD) & Active Headcount Trajectory",
            "20-year evolution of factory workforce scale and total USD payroll expenditure",
            "dim_date", "calendar_year", "Calendar Year",
            ["Total Workforce Payroll (USD)"],
            ["Active Headcount"],
            sort_by_cat_asc=True,
        )
    )
    p6_visuals.append(
        make_bar_or_column_chart(
            "p6_vis03", "clusteredBarChart", 16, 668, 680, 396, 503,
            "Workforce Payroll (USD) by Factory Department",
            "Payroll distribution across Sewing, Cutting, Finishing, Dyeing/Washing, QA & Maintenance",
            "fact_workforce_monthly", "department_name", "Department",
            ["Total Workforce Payroll (USD)"],
        )
    )
    p6_visuals.append(
        make_table_visual(
            "p6_vis04", 710, 668, 1194, 396, 504,
            "Factory Manufacturing Productivity, Downtime & Labour Cost Scorecard",
            "Factory-by-factory production attainment, SMV efficiency, labour productivity, downtime, and unit labour cost",
            [
                ("dim_factory", "factory_name", "Factory"),
                ("dim_factory", "production_technology", "Technology Tier"),
                ("dim_factory", "industrial_zone", "Cluster"),
            ],
            [
                "Actual Good Output (PCS)",
                "Plan vs Actual Attainment %",
                "Production Line Efficiency %",
                "Output per Labour Hour (PCS)",
                "Machine Downtime Hours",
                "Labour Cost per Garment (USD)",
                "Active Headcount",
            ],
        )
    )
    pages.append((p6_id, "06. Manufacturing & HR", p6_visuals))

    # ==========================================================================
    # PAGE 7: Quality, Compliance & Customer Delivery (OTIF)
    # ==========================================================================
    p7_id = "page7_quality_otif00"
    p7_visuals = build_standard_page_scaffold(
        "p7",
        "QUALITY ASSURANCE, COMPLIANCE & CUSTOMER DELIVERY (OTIF)",
        "Inline & Final AQL Inspections, First-Pass Yield, Cost of Poor Quality, Shipping Modes & Delay Root Causes",
        ("dim_factory", "compliance_profile", "Compliance Profile"),
        [
            "First-Pass Yield (FPY) %",
            "AQL Defect Rate %",
            "Garment Rework Rate %",
            "Total Cost of Poor Quality (USD)",
            "On-Time Shipment (OTS) %",
            "On-Time In-Full (OTIF) %",
        ],
    )
    p7_visuals.append(
        make_combo_chart(
            "p7_vis01", 16, 264, 680, 392, 501,
            "Defective Garments (PCS) & Quality Cost by Defect Category",
            "Pareto breakdown across Stitching, Measurement, Fabric Flaw, Dyeing/Shade, Spot/Stain & Trim defects",
            "fact_quality_inspection", "primary_defect_category", "Defect Category",
            ["Defective Quantity (PCS)"],
            ["Estimated Quality Cost (USD)"],
        )
    )
    p7_visuals.append(
        make_combo_chart(
            "p7_vis02", 710, 264, 650, 392, 502,
            "Shipped Volume & Freight Cost by Logistics Delay Root Cause",
            "Analyzing Chattogram port congestion, customs, material lead-time delays & vessel rollovers",
            "fact_shipment_line", "delay_reason", "Delay Root Cause",
            ["Shipped Quantity (PCS)"],
            ["Total Freight Cost (USD)"],
        )
    )
    p7_visuals.append(
        make_donut_chart(
            "p7_vis03", 1374, 264, 530, 392, 503,
            "Export FOB Revenue by Shipping Mode (Sea vs. Air)",
            "Monitoring costly air-freight penalties vs. standard sea container shipments",
            "fact_shipment_line", "shipping_mode", "Shipping Mode",
            "Shipped FOB Revenue (USD)",
        )
    )
    p7_visuals.append(
        make_table_visual(
            "p7_vis04", 16, 668, 1888, 396, 504,
            "Factory Compliance Tier, Quality AQL & Customer Delivery (OTIF) Matrix",
            "Demonstrating how LEED Platinum/Gold compliance modernization drives higher First-Pass Yield and OTIF reliability",
            [
                ("dim_factory", "factory_name", "Factory"),
                ("dim_factory", "compliance_profile", "Compliance Tier"),
                ("dim_factory", "production_technology", "Technology Tier"),
            ],
            [
                "Inspected Quantity (PCS)",
                "First-Pass Yield (FPY) %",
                "AQL Defect Rate %",
                "Garment Rework Rate %",
                "Total Cost of Poor Quality (USD)",
                "On-Time Shipment (OTS) %",
                "On-Time Delivery (OTD) %",
                "On-Time In-Full (OTIF) %",
                "Air Freight Revenue Share %",
            ],
        )
    )
    pages.append((p7_id, "07. Quality & OTIF", p7_visuals))

    # ==========================================================================
    # PAGE 8: Financial Margin Bridge & ESG Sustainability
    # ==========================================================================
    p8_id = "page8_finance_esg000"
    p8_visuals = build_standard_page_scaffold(
        "p8",
        "FINANCIAL COST STRUCTURE & ESG SUSTAINABILITY INTELLIGENCE",
        "Unified Cost Ledger Breakdown, Gross-to-Net Margin Bridge, Rooftop Solar Adoption & Carbon Intensity",
        ("dim_product", "knit_woven_classification", "Knit / Woven"),
        [
            "Shipped FOB Revenue (USD)",
            "Total Production Cost (COGS USD)",
            "Operational Gross Margin (USD)",
            "Electricity per Garment (kWh)",
            "Renewable Solar Share %",
            "Carbon Footprint (kg CO2e/PC)",
        ],
    )
    p8_visuals.append(
        make_bar_or_column_chart(
            "p8_vis01", "waterfallChart", 16, 264, 936, 392, 501,
            "Unified Cost Ledger Breakdown by Cost Category (USD)",
            "Complete cost structure across Raw Material, Direct Labour, Utilities, Overhead, Freight, Compliance & Quality",
            "dim_cost_category", "cost_category_name", "Cost Category",
            ["Total Cost Ledger (USD)"],
        )
    )
    p8_visuals.append(
        make_combo_chart(
            "p8_vis02", 968, 264, 936, 392, 502,
            "20-Year Decarbonization: Carbon Footprint (kg CO2e/PC) & Solar Share %",
            "Post-2015 rooftop solar PV expansion and energy efficiency reducing emissions per garment",
            "dim_date", "calendar_year", "Calendar Year",
            ["Carbon Footprint (kg CO2e/PC)"],
            ["Renewable Solar Share %"],
            sort_by_cat_asc=True,
        )
    )
    p8_visuals.append(
        make_bar_or_column_chart(
            "p8_vis03", "clusteredBarChart", 16, 668, 720, 396, 503,
            "Cost Components & Operational Gross Margin by Company (USD)",
            "Comparing Direct Material, Direct Labour, Factory Overhead, and Gross Margin across companies",
            "dim_company", "company_name", "Company Name",
            [
                "Direct Material Cost (USD)",
                "Direct Labour Cost (USD)",
                "Factory Overhead Cost (USD)",
                "Operational Gross Margin (USD)",
            ],
        )
    )
    p8_visuals.append(
        make_table_visual(
            "p8_vis04", 750, 668, 1154, 396, 504,
            "Factory ESG Sustainability, Resource Efficiency & Profitability Matrix",
            "Evaluating environmental intensity (kWh/pc, liters/pc, kg CO2e/pc, jhut recycling %) alongside gross margin %",
            [
                ("dim_factory", "factory_name", "Factory"),
                ("dim_factory", "compliance_profile", "LEED / Compliance Tier"),
            ],
            [
                "Shipped FOB Revenue (USD)",
                "Operational Gross Margin %",
                "Electricity per Garment (kWh)",
                "Renewable Solar Share %",
                "Water per Garment (Liters)",
                "Carbon Footprint (kg CO2e/PC)",
                "Fabric Waste Recycling Rate %",
            ],
        )
    )
    pages.append((p8_id, "08. Finance & ESG", p8_visuals))

    return pages


def main():
    print("Loading dataset schemas and relationship metadata...")
    parquet_schemas, relationships, col_descriptions = load_metadata()

    # 1. Build Semantic Model (.tmdl files)
    def_dir = PBIP_MODEL_DIR / "definition"
    tables_dir = def_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    table_order = [
        "dim_date",
        "dim_company",
        "dim_factory",
        "dim_factory_line",
        "dim_buyer",
        "dim_supplier",
        "dim_product",
        "dim_material",
        "dim_cost_category",
        "dim_order_line",
        "fact_sales_order_line",
        "fact_purchase_order_line",
        "fact_supplier_delivery",
        "fact_production_batch",
        "fact_material_consumption",
        "fact_quality_inspection",
        "fact_shipment_line",
        "fact_inventory_snapshot_monthly",
        "fact_cost_transaction",
        "fact_workforce_monthly",
        "fact_sustainability_monthly",
        "fact_macro_monthly",
    ]

    for t_name in table_order:
        tmdl_content = build_table_tmdl(t_name, parquet_schemas[t_name], col_descriptions)
        (tables_dir / f"{t_name}.tmdl").write_text(tmdl_content, encoding="utf-8")

    # Write Executive_Measures.tmdl
    exec_measures_tmdl = build_executive_measures_tmdl()
    (tables_dir / "Executive_Measures.tmdl").write_text(exec_measures_tmdl, encoding="utf-8")

    # Write relationships.tmdl
    rels_tmdl = build_relationships_tmdl(relationships)
    (def_dir / "relationships.tmdl").write_text(rels_tmdl, encoding="utf-8")

    # Write model.tmdl
    model_tmdl = build_model_tmdl(table_order)
    # Also include ref to relationships in model.tmdl? Wait: let's check how relationships.tmdl is referenced or discovered in TMDL!
    # In TMDL, relationships.tmdl in `definition/relationships.tmdl` is automatically part of the model root alongside model.tmdl and database.tmdl!
    (def_dir / "model.tmdl").write_text(model_tmdl, encoding="utf-8")

    # Update .pbi/editorSettings.json to disable autodetectRelationships so our 64 star-schema relationships stay intact
    editor_settings_path = PBIP_MODEL_DIR / ".pbi" / "editorSettings.json"
    if editor_settings_path.exists():
        es = json.loads(editor_settings_path.read_text(encoding="utf-8"))
        es["autodetectRelationships"] = False
        editor_settings_path.write_text(json.dumps(es, indent=2), encoding="utf-8")

    # Remove stale blank cache.abf so Power BI Desktop loads the new 23-table TMDL model cleanly
    cache_abf_path = PBIP_MODEL_DIR / ".pbi" / "cache.abf"
    if cache_abf_path.exists():
        cache_abf_path.unlink()
        print("Removed stale blank .pbi/cache.abf so Power BI Desktop loads the new TMDL schema cleanly.")

    print(f"Generated 23 TMDL table definitions + 64 relationships in {def_dir}")

    # 2. Build Multi-Page Executive Report (PBIR)
    pages_dir = PBIP_REPORT_DIR / "definition" / "pages"
    if pages_dir.exists():
        shutil.rmtree(pages_dir)
    pages_dir.mkdir(parents=True, exist_ok=True)

    pages = build_all_pages()
    page_ids = []

    for page_id, display_name, visuals in pages:
        page_ids.append(page_id)
        p_folder = pages_dir / page_id
        p_folder.mkdir(parents=True, exist_ok=True)

        page_json = {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": page_id,
            "displayName": display_name,
            "displayOption": "FitToPage",
            "height": 1080,
            "width": 1920,
            "objects": {
                "background": [
                    {
                        "properties": {
                            "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F1F5F9'"}}}}},
                            "transparency": {"expr": {"Literal": {"Value": "0D"}}},
                        }
                    }
                ]
            },
        }
        (p_folder / "page.json").write_text(json.dumps(page_json, indent=2), encoding="utf-8")

        vis_root = p_folder / "visuals"
        for v in visuals:
            v_id = v["name"]
            v_folder = vis_root / v_id
            v_folder.mkdir(parents=True, exist_ok=True)
            (v_folder / "visual.json").write_text(json.dumps(v, indent=2), encoding="utf-8")

    pages_meta = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": page_ids,
        "activePageName": page_ids[0],
    }
    (pages_dir / "pages.json").write_text(json.dumps(pages_meta, indent=2), encoding="utf-8")
    print(f"Generated {len(pages)} Full-HD (1920x1080) report pages and {sum(len(v) for _, _, v in pages)} visuals in {pages_dir}")


if __name__ == "__main__":
    main()

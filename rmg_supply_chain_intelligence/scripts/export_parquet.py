"""
export_parquet.py
Exports all 10 dimension tables and 12 fact tables into BigQuery-ready Snappy-compressed Parquet files,
partitioning fact tables by `event_year=YYYY/part-00000.parquet` while retaining `event_year` inside the Parquet schema.
Also generates:
- `data/manifests/table_manifest.csv` and `data/manifests/table_manifest.json`
- `data/samples/<table_name>_sample.csv` (100 rows per table for quick preview)
- `schemas/parquet_schema.json`
- `schemas/bigquery_schema/<table_name>.json`
- `schemas/bigquery_ddl.sql` and `bigquery/create_tables.sql`
"""

import os
import json
import shutil
import datetime
import decimal
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from generate_facts import generate_all_datasets

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
SCHEMA_DIR = os.path.join(BASE_DIR, "schemas")
BQ_SCHEMA_DIR = os.path.join(SCHEMA_DIR, "bigquery_schema")
BQ_DIR = os.path.join(BASE_DIR, "bigquery")


def is_monetary_column(col_name: str) -> bool:
    c = col_name.lower()
    if "exchange_rate" in c:
        return False
    if any(k in c for k in ["_usd", "_bdt", "unit_price", "unit_cost", "unit_valuation"]):
        return True
    return False


def dataframe_to_arrow_table(df: pd.DataFrame) -> pa.Table:
    """
    Convert a pandas DataFrame into a PyArrow Table with explicit native logical types:
    - Business dates -> pa.date32()
    - Monetary / financial columns -> pa.decimal128(18, 2) or pa.decimal128(18, 4) for unit costs
    - Exchange rates / ratios / percentages / quantities -> pa.float64() or pa.int64()
    - Booleans -> pa.bool_()
    - Strings -> pa.string()
    """
    arrays = []
    fields = []

    for col in df.columns:
        s = df[col]
        dtype = s.dtype
        col_low = col.lower()

        if col_low.endswith("_date") or col_low in ("full_date", "active_from_date", "active_to_date"):
            # Convert to native PyArrow date32
            arr = pa.array(pd.to_datetime(s).dt.date, type=pa.date32())
            fields.append(pa.field(col, pa.date32()))
            arrays.append(arr)
        elif pd.api.types.is_bool_dtype(dtype):
            arr = pa.array(s.fillna(False).to_numpy(dtype=bool), type=pa.bool_())
            fields.append(pa.field(col, pa.bool_()))
            arrays.append(arr)
        elif pd.api.types.is_integer_dtype(dtype):
            arr = pa.array(s.fillna(0).to_numpy(dtype=np.int64), type=pa.int64())
            fields.append(pa.field(col, pa.int64()))
            arrays.append(arr)
        elif pd.api.types.is_float_dtype(dtype):
            if is_monetary_column(col_low):
                # Use fixed-precision NUMERIC / DECIMAL(18, 2) or DECIMAL(18, 3) for unit costs
                scale = 3 if ("unit_cost" in col_low or "unit_valuation" in col_low or "yarn_usd" in col_low) else 2
                dec_type = pa.decimal128(18, scale)
                arr = pa.array(np.round(s.fillna(0.0).to_numpy(dtype=np.float64), scale), type=pa.float64()).cast(dec_type)
                fields.append(pa.field(col, dec_type))
                arrays.append(arr)
            else:
                arr = pa.array(s.fillna(0.0).to_numpy(dtype=np.float64), type=pa.float64())
                fields.append(pa.field(col, pa.float64()))
                arrays.append(arr)
        else:
            arr = pa.array(s.fillna("").astype(str).to_numpy(), type=pa.string())
            fields.append(pa.field(col, pa.string()))
            arrays.append(arr)

    schema = pa.schema(fields)
    return pa.Table.from_arrays(arrays, schema=schema)


def arrow_type_to_bigquery_type(pa_type: pa.DataType) -> str:
    if pa.types.is_int64(pa_type) or pa.types.is_int32(pa_type):
        return "INT64"
    elif pa.types.is_boolean(pa_type):
        return "BOOL"
    elif pa.types.is_date(pa_type):
        return "DATE"
    elif pa.types.is_timestamp(pa_type):
        return "TIMESTAMP"
    elif pa.types.is_decimal(pa_type):
        return "NUMERIC"
    elif pa.types.is_floating(pa_type):
        return "FLOAT64"
    else:
        return "STRING"


def export_all_to_parquet():
    os.makedirs(os.path.join(DATA_DIR, "dimensions"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "facts"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "manifests"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "samples"), exist_ok=True)
    os.makedirs(BQ_SCHEMA_DIR, exist_ok=True)
    os.makedirs(BQ_DIR, exist_ok=True)

    dims, facts = generate_all_datasets()

    manifest_rows = []
    parquet_schemas_dict = {}
    ddl_statements = [
        "-- =============================================================================",
        "-- Google BigQuery DDL for 20-Year Bangladesh RMG Supply Chain Intelligence",
        "-- Dataset: `rmg_supply_chain_dw`",
        "-- All tables match the exported Snappy-compressed Parquet logical types.",
        "-- =============================================================================",
        "",
        "CREATE SCHEMA IF NOT EXISTS `rmg_supply_chain_dw`",
        "OPTIONS(location='asia-south1', description='20-Year Bangladesh RMG Supply Chain Intelligence Warehouse (2006-2025)');",
        "",
    ]

    # 1. Export Dimension Tables
    for name, df in dims.items():
        table_dir = os.path.join(DATA_DIR, "dimensions", name)
        if os.path.exists(table_dir):
            shutil.rmtree(table_dir)
        os.makedirs(table_dir, exist_ok=True)

        pa_tbl = dataframe_to_arrow_table(df)
        out_path = os.path.join(table_dir, "part-00000.parquet")
        pq.write_table(
            pa_tbl,
            out_path,
            compression="snappy",
            use_dictionary=True,
            write_statistics=True,
        )
        size_bytes = os.path.getsize(out_path)

        # Save 100-row CSV preview sample
        df.head(100).to_csv(os.path.join(DATA_DIR, "samples", f"{name}_sample.csv"), index=False)

        # Record schema
        col_meta = []
        bq_schema_fields = []
        ddl_cols = []
        for field in pa_tbl.schema:
            bq_t = arrow_type_to_bigquery_type(field.type)
            col_meta.append({"name": field.name, "parquet_type": str(field.type), "bigquery_type": bq_t})
            bq_schema_fields.append({
                "name": field.name,
                "type": bq_t,
                "mode": "REQUIRED" if field.name.endswith("_key") else "NULLABLE",
            })
            not_null = " NOT NULL" if field.name == df.columns[0] else ""
            ddl_cols.append(f"    `{field.name}` {bq_t}{not_null}")

        parquet_schemas_dict[name] = {
            "table_type": "dimension",
            "partition_field": None,
            "row_count": len(df),
            "columns": col_meta,
        }
        with open(os.path.join(BQ_SCHEMA_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(bq_schema_fields, f, indent=2)

        ddl_statements.append(f"CREATE OR REPLACE TABLE `rmg_supply_chain_dw.{name}` (")
        ddl_statements.append(",\n".join(ddl_cols))
        ddl_statements.append(");")
        ddl_statements.append("")

        manifest_rows.append({
            "table_name": name,
            "table_category": "dimension",
            "relative_directory": f"data/dimensions/{name}",
            "partition_scheme": "Unpartitioned (Single File)",
            "file_count": 1,
            "row_count": len(df),
            "column_count": len(df.columns),
            "compression": "SNAPPY",
            "total_size_bytes": size_bytes,
            "total_size_mb": round(size_bytes / (1024 * 1024), 3),
            "primary_key": df.columns[0],
        })
        print(f"Exported DIM  {name:34s}: {len(df):10,d} rows | {size_bytes / (1024*1024):6.2f} MB")

    # Recommended date partitioning and clustering metadata for fact tables
    fact_bq_specs = {
        "fact_sales_order_line": ("order_date", ["company_key", "factory_key", "buyer_key", "product_key"]),
        "fact_purchase_order_line": ("po_order_date", ["company_key", "receiving_factory_key", "supplier_key", "material_key"]),
        "fact_supplier_delivery": ("receipt_date", ["company_key", "receiving_factory_key", "supplier_key", "material_key"]),
        "fact_production_batch": ("actual_completion_date", ["company_key", "factory_key", "production_line_key", "product_key"]),
        "fact_material_consumption": ("consumption_date", ["company_key", "factory_key", "material_key", "product_key"]),
        "fact_quality_inspection": ("inspection_date", ["company_key", "factory_key", "product_key", "primary_defect_category"]),
        "fact_shipment_line": ("actual_ship_date", ["company_key", "factory_key", "buyer_key", "export_destination_country"]),
        "fact_inventory_snapshot_monthly": ("snapshot_month_date", ["company_key", "factory_key", "stock_type", "material_key"]),
        "fact_cost_transaction": ("transaction_date", ["company_key", "factory_key", "cost_category_key"]),
        "fact_workforce_monthly": ("month_start_date", ["company_key", "factory_key", "department_name"]),
        "fact_sustainability_monthly": ("month_start_date", ["company_key", "factory_key"]),
        "fact_macro_monthly": ("month_start_date", ["calendar_year", "fiscal_year"]),
    }

    # 2. Export Fact Tables (partitioned by event_year=YYYY/part-00000.parquet while retaining event_year column inside schema)
    for name, df in facts.items():
        table_dir = os.path.join(DATA_DIR, "facts", name)
        if os.path.exists(table_dir):
            shutil.rmtree(table_dir)
        os.makedirs(table_dir, exist_ok=True)

        pa_tbl_full = dataframe_to_arrow_table(df)
        total_size_bytes = 0
        file_count = 0

        for yr, df_yr in df.groupby("event_year", sort=True):
            yr_dir = os.path.join(table_dir, f"event_year={int(yr)}")
            os.makedirs(yr_dir, exist_ok=True)
            pa_yr = dataframe_to_arrow_table(df_yr)
            part_file = os.path.join(yr_dir, "part-00000.parquet")
            pq.write_table(
                pa_yr,
                part_file,
                compression="snappy",
                use_dictionary=True,
                write_statistics=True,
            )
            total_size_bytes += os.path.getsize(part_file)
            file_count += 1

        # Save 100-row CSV preview sample
        df.head(100).to_csv(os.path.join(DATA_DIR, "samples", f"{name}_sample.csv"), index=False)

        col_meta = []
        bq_schema_fields = []
        ddl_cols = []
        for field in pa_tbl_full.schema:
            bq_t = arrow_type_to_bigquery_type(field.type)
            col_meta.append({"name": field.name, "parquet_type": str(field.type), "bigquery_type": bq_t})
            bq_schema_fields.append({
                "name": field.name,
                "type": bq_t,
                "mode": "REQUIRED" if field.name == df.columns[0] else "NULLABLE",
            })
            not_null = " NOT NULL" if field.name == df.columns[0] else ""
            ddl_cols.append(f"    `{field.name}` {bq_t}{not_null}")

        parquet_schemas_dict[name] = {
            "table_type": "fact",
            "partition_field": "event_year",
            "row_count": len(df),
            "columns": col_meta,
        }
        with open(os.path.join(BQ_SCHEMA_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(bq_schema_fields, f, indent=2)

        part_col, cluster_cols = fact_bq_specs[name]
        cluster_str = ", ".join(f"`{c}`" for c in cluster_cols)
        ddl_statements.append(f"CREATE OR REPLACE TABLE `rmg_supply_chain_dw.{name}` (")
        ddl_statements.append(",\n".join(ddl_cols))
        ddl_statements.append(")")
        ddl_statements.append(f"PARTITION BY `{part_col}`")
        ddl_statements.append(f"CLUSTER BY {cluster_str};")
        ddl_statements.append("")

        manifest_rows.append({
            "table_name": name,
            "table_category": "fact",
            "relative_directory": f"data/facts/{name}",
            "partition_scheme": "event_year=YYYY (20 Annual Partitions, 2006-2025)",
            "file_count": file_count,
            "row_count": len(df),
            "column_count": len(df.columns),
            "compression": "SNAPPY",
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 3),
            "primary_key": df.columns[0],
        })
        print(f"Exported FACT {name:34s}: {len(df):10,d} rows | {file_count:2d} files | {total_size_bytes / (1024*1024):6.2f} MB")

    # Write manifests and schemas
    df_manifest = pd.DataFrame(manifest_rows)
    df_manifest.to_csv(os.path.join(DATA_DIR, "manifests", "table_manifest.csv"), index=False)
    with open(os.path.join(DATA_DIR, "manifests", "table_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_rows, f, indent=2)

    with open(os.path.join(SCHEMA_DIR, "parquet_schema.json"), "w", encoding="utf-8") as f:
        json.dump(parquet_schemas_dict, f, indent=2)

    ddl_text = "\n".join(ddl_statements)
    with open(os.path.join(SCHEMA_DIR, "bigquery_ddl.sql"), "w", encoding="utf-8") as f:
        f.write(ddl_text)
    with open(os.path.join(BQ_DIR, "create_tables.sql"), "w", encoding="utf-8") as f:
        f.write(ddl_text)

    total_rows = int(df_manifest["row_count"].sum())
    total_mb = float(df_manifest["total_size_mb"].sum())
    print(f"\nALL PARQUET EXPORTS COMPLETE: {len(df_manifest)} tables | {total_rows:,} total rows | {total_mb:.2f} MB compressed Parquet.")


if __name__ == "__main__":
    export_all_to_parquet()

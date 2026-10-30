# Loading 20-Year Bangladesh RMG Parquet Dataset into Google BigQuery

This guide provides step-by-step instructions for uploading the generated Snappy-compressed Parquet files to **Google Cloud Storage (GCS)** and loading them into **Google BigQuery** (`rmg_supply_chain_dw`).

---

## 1. Prerequisites

1. **Google Cloud SDK (`gcloud` and `bq` CLI)** installed and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_GCP_PROJECT_ID
   ```
2. **Create a GCS Bucket** (recommended region: `asia-south1` or multi-region `US`/`ASIA` matching your BigQuery dataset):
   ```bash
   gcloud storage buckets create gs://YOUR_RMG_BUCKET_NAME --location=asia-south1
   ```

---

## 2. Upload Parquet Files to Google Cloud Storage

From the root of `rmg_supply_chain_intelligence/`, upload the `data/dimensions` and `data/facts` directories using parallel composite uploads:

```bash
gcloud storage cp --recursive data/dimensions gs://YOUR_RMG_BUCKET_NAME/rmg_dw/dimensions
gcloud storage cp --recursive data/facts gs://YOUR_RMG_BUCKET_NAME/rmg_dw/facts
```

---

## 3. Create the BigQuery Dataset and Partitioned/Clustered Tables

Run the generated DDL script (`bigquery/create_tables.sql` or `schemas/bigquery_ddl.sql`):

```bash
bq query --use_legacy_sql=false < bigquery/create_tables.sql
```

All 12 fact tables are pre-configured with **native `DATE` partitioning** and **multi-column clustering** on `company_key`, `factory_key`, and relevant operational foreign keys.

---

## 4. Load Dimension & Fact Parquet Files into BigQuery

Because every Parquet file uses native logical types (`INT64`, `DATE`, `NUMERIC(18,2)`, `FLOAT64`, `BOOL`, `STRING`) that match the BigQuery DDL 1:1, no manual type casting or staging cleanup is required. Importantly, `event_year` is stored directly inside every fact Parquet file schema, so wildcard loading works seamlessly.

### A. Load All 10 Dimension Tables

```bash
for tbl in dim_date dim_company dim_factory dim_factory_line dim_buyer dim_supplier dim_product dim_material dim_cost_category dim_order_line; do
  bq load \
    --replace \
    --source_format=PARQUET \
    rmg_supply_chain_dw.${tbl} \
    "gs://YOUR_RMG_BUCKET_NAME/rmg_dw/dimensions/${tbl}/*.parquet"
done
```

### B. Load All 12 Partitioned Fact Tables

```bash
for tbl in fact_sales_order_line fact_purchase_order_line fact_supplier_delivery fact_production_batch fact_material_consumption fact_quality_inspection fact_shipment_line fact_inventory_snapshot_monthly fact_cost_transaction fact_workforce_monthly fact_sustainability_monthly fact_macro_monthly; do
  bq load \
    --replace \
    --source_format=PARQUET \
    rmg_supply_chain_dw.${tbl} \
    "gs://YOUR_RMG_BUCKET_NAME/rmg_dw/facts/${tbl}/event_year=*/*.parquet"
done
```

### C. Alternative: Hive-Partitioned External or Native Load (`LOAD DATA INTO`)

You can also execute pure BigQuery SQL (`LOAD DATA OVERWRITE`) directly inside the BigQuery Studio console:

```sql
LOAD DATA OVERWRITE `rmg_supply_chain_dw.fact_sales_order_line`
FROM FILES (
  format = 'PARQUET',
  uris = ['gs://YOUR_RMG_BUCKET_NAME/rmg_dw/facts/fact_sales_order_line/event_year=*/*.parquet']
);
```

---

## 5. Run Post-Load BigQuery Validation & Analytical Views

1. Execute the post-load reconciliation queries:
   ```bash
   bq query --use_legacy_sql=false < bigquery/validation_queries.sql
   ```
2. Create the pre-aggregated KPI views for Power BI DirectQuery / Import acceleration:
   ```bash
   bq query --use_legacy_sql=false < bigquery/kpi_views.sql
   ```

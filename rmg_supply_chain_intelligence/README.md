# 20-Year Bangladesh Ready-Made Garment (RMG) Supply Chain Intelligence Platform (2006–2025)

> **SYNTHETIC DATASET DISCLAIMER**: This platform contains a **100% synthetic, relational operational and financial dataset** covering 20 calendar years (`2006-01-01` to `2025-12-31`). While calibrated against publicly documented Bangladesh RMG macroeconomic, trade, labour, and geographic benchmarks (BGMEA, BKMEA, EPB, Bangladesh Bank, BBS, World Bank, Minimum Wage Gazette notifications, and BRAC University's Mapped in Bangladesh), **all 8 companies, 26 factories, 52 buyers, 180 suppliers, and ~3.04 million records are fictional**. Never attribute these synthetic figures to any real-world company.

---

## 1. Executive Overview & Central Management Question

This project provides an enterprise-grade **Google BigQuery** data warehouse and **Power BI Desktop** semantic model designed to answer:

> **How can a Bangladesh-based RMG manufacturing group improve profitability, supply chain reliability, customer service, factory productivity, inventory efficiency, and long-term competitiveness using 20 years of business intelligence?**

### Key Highlights
- **Historical Coverage**: `2006-01-01` to `2025-12-31` (20 complete calendar years; `FY2005-06` to `FY2025-26` July–June Bangladesh fiscal calendar; `7,305` daily dates including Fridays as weekly factory holidays, Ramadan periods, Eid-ul-Fitr, Eid-ul-Adha, and national holidays).
- **Scale & Volume**: **22 relational tables** (**10 Conformed Dimensions** + **12 Fact Tables**) containing **~3.04 million records** stored in **Snappy-compressed Parquet** format (`event_year=YYYY/part-00000.parquet` partitioning for all fact tables).
- **Dual Currency & Authentic Units**: Full support for **Bangladesh Taka (`BDT`)** and **US Dollars (`USD`)** with historical monthly exchange rates (`69.0 BDT/USD` in 2006 to `120.4 BDT/USD` in 2025) and domain-authentic units of measure (`PCS`, `KG`, `YARD`, `CONE`, `SET`, `GROSS`, `kWh`, `m3`, `kg CO2e`).

---

## 2. Complete Project Directory Structure

```text
rmg_supply_chain_intelligence/
├── README.md
├── requirements.txt
├── config/
│   └── generation_config.yaml
├── scripts/
│   ├── generate_macro_context.py
│   ├── generate_dimensions.py
│   ├── generate_facts.py
│   ├── export_parquet.py
│   ├── validate_data.py
│   └── analyze_insights.py
├── data/
│   ├── dimensions/                  # 10 Snappy Parquet dimension tables
│   ├── facts/                       # 12 Snappy Parquet fact tables (partitioned by event_year=2006..2025)
│   ├── manifests/
│   │   ├── table_manifest.csv
│   │   └── table_manifest.json
│   └── samples/                     # 100-row CSV preview samples for all 22 tables
├── schemas/
│   ├── parquet_schema.json
│   ├── bigquery_ddl.sql
│   └── bigquery_schema/             # 22 BigQuery JSON schema definitions
├── bigquery/
│   ├── create_tables.sql            # Partitioned & clustered BigQuery DDL
│   ├── load_instructions.md         # GCS upload & bq load CLI / SQL guide
│   ├── validation_queries.sql       # Post-load reconciliation SQL tests
│   └── kpi_views.sql                # Pre-aggregated executive & factory KPI views
├── documentation/
│   ├── data_dictionary.csv          # Column-level metadata for all 22 tables
│   ├── model_relationships.csv      # 62 star-schema relationships (1:* single-direction)
│   ├── data_model.md                # Mermaid ER diagram & table grain definitions
│   ├── methodology.md               # Econometric calibration & reconciliation logic
│   ├── source_register.csv          # 12 official & industry benchmark sources
│   ├── synthetic_company_profiles.md# Profiles of the 8 fictional RMG groups
│   ├── validation_report.md         # Automated 12-suite DQ test report
│   └── business_insights.md         # Empirical 20-year findings & recommendations
└── power_bi/
    ├── semantic_model_specification.md
    ├── dax_measure_catalog.md       # 50+ production-ready DAX measures
    └── suggested_report_pages.md    # 12-page Power BI report blueprint
```

---

## 3. Reproducing the Dataset Locally

1. **Install Python Dependencies** (`Python 3.10+`):
   ```bash
   pip install -r requirements.txt
   ```
2. **Generate All 22 Tables & Export to Partitioned Parquet** (uses deterministic seed `20261026`):
   ```bash
   python scripts/export_parquet.py
   ```
3. **Run Automated Data Quality & Supply-Chain Reconciliation Tests**:
   ```bash
   python scripts/validate_data.py
   ```
4. **Generate Empirical Business Insights via DuckDB**:
   ```bash
   python scripts/analyze_insights.py
   ```

---

## 4. Loading into Google BigQuery & Connecting Power BI Desktop

- **Google BigQuery**: Follow [`bigquery/load_instructions.md`](bigquery/load_instructions.md) to upload `data/dimensions` and `data/facts` to Google Cloud Storage (`gs://...`), execute [`bigquery/create_tables.sql`](bigquery/create_tables.sql), load the Parquet files, and verify with [`bigquery/validation_queries.sql`](bigquery/validation_queries.sql).
- **Power BI Desktop**: Follow [`power_bi/semantic_model_specification.md`](power_bi/semantic_model_specification.md) to connect directly to BigQuery or local Parquet files, apply the relationships in [`documentation/model_relationships.csv`](documentation/model_relationships.csv), and load the measures from [`power_bi/dax_measure_catalog.md`](power_bi/dax_measure_catalog.md).

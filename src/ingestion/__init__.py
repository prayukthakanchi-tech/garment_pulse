"""
GarmentPulse Data Ingestion Module

Handles the full ETL pipeline:
  CSV (raw) → Parquet (processed) → DuckDB (analytical database)

Sub-modules
-----------
csv_loader        – Lazy / eager readers for the H&M Kaggle CSVs.
parquet_converter – Stream-converts CSVs to columnar Parquet files.
db_loader         – Loads Parquet into DuckDB and orchestrates the pipeline.
"""

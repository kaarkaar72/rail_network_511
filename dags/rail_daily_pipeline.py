"""
rail_daily_pipeline
===================
Daily batch pipeline for Rail3.

Task order:
  1. schedule_extract  — Download CIF schedule from Network Rail, transform to
                         Parquet, upload to GCS, load into BigQuery.
  2. dbt_run           — Run all dbt models (staging → intermediate → core → marts).
  3. redis_refresh     — Warm Redis caches (dim_geo, dim_train_schedule) from
                         the freshly-built BigQuery tables.

Schedule: 02:00 UTC daily. Retries: 2 (5-minute delay each).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

# All scripts are mounted at /opt/airflow/<dir> — see docker-compose.yml volumes.
WORKDIR = "/opt/airflow"

default_args = {
    "owner": "rail3",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "depends_on_past": False,
}

with DAG(
    dag_id="rail_daily_pipeline",
    description="Daily CIF extract → dbt run → Redis warm-up",
    default_args=default_args,
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["rail3", "batch"],
) as dag:

    schedule_extract = BashOperator(
        task_id="schedule_extract",
        bash_command=f"cd {WORKDIR} && python extraction/schedule_extract_daily.py",
        execution_timeout=timedelta(hours=2),
        doc_md=(
            "Downloads the full daily CIF schedule file from Network Rail, "
            "transforms it to Parquet, uploads to GCS, and loads into BigQuery."
        ),
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {WORKDIR} && python pipelines/batch/dim_refresh_daily.py",
        execution_timeout=timedelta(hours=1),
        doc_md=(
            "Runs all dbt models via dbtRunner: staging → intermediate → core → marts. "
            "Incremental models only scan today's partition."
        ),
    )

    redis_refresh = BashOperator(
        task_id="redis_refresh",
        bash_command=f"cd {WORKDIR} && python pipelines/batch/live_refresh.py",
        execution_timeout=timedelta(minutes=30),
        doc_md=(
            "Warms the Redis cache by loading dim_geo and dim_train_schedule "
            "from BigQuery into Redis. Required for the enrichment pipeline and dashboard."
        ),
    )

    schedule_extract >> dbt_run >> redis_refresh

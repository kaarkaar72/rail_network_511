import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def main():
    from dbt.cli.main import dbtRunner

    # Resolve paths relative to this file so the script works from any working directory
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dbt"))
    profiles_dir = project_dir

    logging.info(f"Starting dbt run (project: {project_dir})")
    dbt = dbtRunner()
    res = dbt.invoke([
        "run",
        "--project-dir", project_dir,
        "--profiles-dir", profiles_dir,
    ])

    if not res.success:
        logging.error("dbt run failed")
        sys.exit(1)

    logging.info("dbt run completed successfully")


if __name__ == "__main__":
    main()

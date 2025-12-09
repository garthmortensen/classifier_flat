# Inpatient Readmission Risk Classifier

This project implements a 4-Agent System (DataOps, MLOps, Analyst, Reviewer) to predict inpatient readmission risk using historical claims data.

## Project Structure

* `config.yaml`, `dataops.yaml`: Configuration files.
* `dataops.py`, `mlops.py`, `vizops.py`: Python modules containing the deterministic tools for each agent.
* `output/`: Directory where all artifacts (datasets, models, plots, logs) are saved.
* `*.md`: Project documentation.

## Setup

1.  **Environment**: Ensure you have Python 3.13+ installed.
2.  **Dependencies**: Install the required packages using `uv`.
    ```bash
    uv sync
    # Or manually:
    uv add sqlalchemy psycopg2-binary pandas pyyaml...
    ```

## How to Run

### Testing DataOps Tools

To verify that the DataOps tools are working correctly (database connection, schema retrieval, SQL execution), run the test script:

```bash
uv run python test_dataops_tools.py
```

This script will:
1.  Connect to the database defined in `config.yaml`.
2.  Fetch the schema for the `fct_claim` table.
3.  Execute a sample query (limit 5 rows).
4.  Profile the resulting dataset.
5.  Log the results to `dataops.md`.

### Using the Tools

The tools are designed to be used by the AI Agents or imported into your own scripts.

Example usage:

```python
from dataops import execute_sql, profile_dataset

# Run a query
csv_path = execute_sql("SELECT * FROM fct_claim WHERE claim_amount > 1000 LIMIT 100")

# Profile the data
stats = profile_dataset(csv_path)
print(stats)
```
# classifier_flat

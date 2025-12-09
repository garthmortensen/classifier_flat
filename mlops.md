# MLOps Agent Implementation Notes

## Status: Implemented

### 1. Tooling (`tools/mlops.py`)
The following deterministic tools have been implemented and verified:

*   **`split_data_time_series(file_path, date_col, cutoff_date)`**
    *   Splits data into train/test sets based on a cutoff date.
    *   Saves splits to `output/<timestamp>/mlops/` with hash-based filenames.
    *   Returns paths to train and test CSVs.

*   **`train_model(train_path, target, algorithm, params)`**
    *   Supports `xgboost` and `lightgbm`.
    *   Trains a classifier on the provided training data.
    *   Saves the model artifact (`.joblib`) to `output/<timestamp>/mlops/`.
    *   Returns path to the saved model.

*   **`run_backtest(model_path, test_path, target_col)`**
    *   Loads a saved model and evaluates it against the test set.
    *   Calculates AUC, F1, Precision, and Recall.
    *   Returns a dictionary of metrics.

*   **`optimize_hyperparameters(train_path, target, n_trials)`**
    *   Uses `optuna` to optimize XGBoost hyperparameters.
    *   Returns the best parameter set.

### 2. Infrastructure (`tools/clerk.py`)
Updates made to the central clerk module to support MLOps:

*   **`save_model(model, prefix, subdir="mlops")`**: Added support for saving joblib artifacts.
*   **Directory Structure**: `get_run_context` now automatically creates `dataops` and `mlops` subdirectories.
*   **Filename Generation**: Refactored to `_generate_filename` for consistency across CSVs and models.

### 3. Dependencies
Added via `uv`:
*   `joblib`
*   `xgboost`
*   `lightgbm`
*   `optuna`
*   `scikit-learn`

### 4. Verification
*   `test_mlops_tools.py` created and passed.
*   Verified integration with `clerk.py` (hashing, versioning, directory structure).

## Next Steps
*   Integrate with the Analyst agent for visualization.
*   Refine hyperparameter search spaces for LightGBM.
*   Add support for categorical feature handling in `train_model`.

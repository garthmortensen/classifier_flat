# VizOps Tools

**Type:** Analysis & Visualization  
**Description:** This module provides tools for the VizOps agent to visualize model performance and interpret results. It uses Altair for generating interactive charts.

## Tools

### `plot_roc_curve`
Generates a Receiver Operating Characteristic (ROC) curve to evaluate the trade-off between true positive rate and false positive rate.

- **Input:**
  - `model_path` (str): Path to the trained model artifact.
  - `test_path` (str): Path to the test dataset CSV.
  - `output_dir` (str): Directory to save the output chart (default: "vizops").
- **Output:**
  - Returns the path to the saved HTML chart.

### `plot_confusion_matrix`
Generates a confusion matrix to visualize the performance of the classification model.

- **Input:**
  - `model_path` (str): Path to the trained model artifact.
  - `test_path` (str): Path to the test dataset CSV.
  - `output_dir` (str): Directory to save the output chart (default: "vizops").
  - `threshold` (float): Probability threshold for classification (default: 0.5).
- **Output:**
  - Returns the path to the saved HTML chart.

### `plot_feature_importance`
Generates a bar chart showing the importance of each feature in the model.

- **Input:**
  - `model_path` (str): Path to the trained model artifact.
  - `output_dir` (str): Directory to save the output chart (default: "vizops").
- **Output:**
  - Returns the path to the saved HTML chart.

### `plot_calibration_curve`
Generates a calibration curve to assess how well the predicted probabilities match the actual outcomes.

- **Input:**
  - `model_path` (str): Path to the trained model artifact.
  - `test_path` (str): Path to the test dataset CSV.
  - `output_dir` (str): Directory to save the output chart (default: "vizops").
- **Output:**
  - Returns the path to the saved HTML chart.

## Analysis Workflow

1.  **Receive Request:** The VizOps agent receives a request from the Orchestrator to analyze the results of a model training experiment.
2.  **Load Artifacts:** The agent uses the provided paths to load the trained model and the test dataset.
3.  **Generate Visualizations:**
    - Calls `plot_roc_curve` to assess overall discrimination power.
    - Calls `plot_calibration_curve` to check if the model's probability estimates are reliable.
    - Calls `plot_confusion_matrix` to understand the types of errors (false positives vs. false negatives) at a specific threshold.
    - Calls `plot_feature_importance` to identify the key drivers of the predictions.
4.  **Interpret Results:** The agent analyzes the generated charts and metrics to form a conclusion about the model's performance and validity.
5.  **Report Findings:** The agent drafts a report summarizing the findings, including the paths to the generated charts, and submits it to the Reviewer.

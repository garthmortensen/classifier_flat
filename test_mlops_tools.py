import pandas as pd
import os
from mlops import split_data_time_series, train_model, run_backtest, optimize_hyperparameters
from rich.console import Console

console = Console()

def create_dummy_data():
    data = {
        "date": pd.date_range(start="2023-01-01", periods=100, freq="D"),
        "feature1": range(100),
        "feature2": [x * 2 for x in range(100)],
        "target": [1 if x % 2 == 0 else 0 for x in range(100)]
    }
    df = pd.DataFrame(data)
    df.to_csv("dummy_data.csv", index=False)
    return "dummy_data.csv"

def test_mlops():
    console.rule("Testing MLOps Tools")
    
    # 0. Create dummy data
    dummy_path = create_dummy_data()
    console.print(f"[green]✓ Created dummy data at {dummy_path}[/green]")
    
    # 1. Split Data
    console.print("\n[bold]Step 1: Splitting Data...[/bold]")
    splits = split_data_time_series(dummy_path, "date", "2023-03-01")
    console.print(f"Train path: {splits['train']}")
    console.print(f"Test path: {splits['test']}")
    
    # 2. Train Model
    console.print("\n[bold]Step 2: Training Model (XGBoost)...[/bold]")
    model_path = train_model(splits['train'], "target", "xgboost", {"n_estimators": 10, "max_depth": 2})
    console.print(f"Model saved to: {model_path}")
    
    # 3. Run Backtest
    console.print("\n[bold]Step 3: Running Backtest...[/bold]")
    results = run_backtest(model_path, splits['test'], target_col="target")
    console.print(f"Metrics: {results['metrics']}")
    console.print(f"Metrics File: {results['metrics_file']}")
    console.print(f"Plots File: {results['plots_file']}")
    
    # Verify files exist
    if os.path.exists(results['metrics_file']):
        console.print("[green]✓ Metrics JSON file created[/green]")
    else:
        console.print("[red]✗ Metrics JSON file missing[/red]")
        
    if os.path.exists(results['plots_file']):
        console.print("[green]✓ Plots JSON file created[/green]")
    else:
        console.print("[red]✗ Plots JSON file missing[/red]")
    
    # 4. Optimize Hyperparameters
    console.print("\n[bold]Step 4: Optimizing Hyperparameters...[/bold]")
    best_params = optimize_hyperparameters(splits['train'], "target", n_trials=2)
    console.print(f"Best Params: {best_params}")
    
    # Cleanup
    if os.path.exists("dummy_data.csv"):
        os.remove("dummy_data.csv")

if __name__ == "__main__":
    test_mlops()

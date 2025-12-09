import os
import pandas as pd
import yaml
from datetime import datetime
import hashlib
import shutil
import joblib
from rich.console import Console

# Initialize Rich Console
console = Console()

# Load config
def load_config():
    config = {}
    # Load main config
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f:
            config.update(yaml.safe_load(f))
    
    # Load dataops config
    if os.path.exists("dataops.yaml"):
        with open("dataops.yaml", "r") as f:
            dataops_config = yaml.safe_load(f)
            if dataops_config:
                config.update(dataops_config)
                
    return config

CONFIG = load_config()

# Global Run Context
_RUN_CONTEXT = {
    "dir": None,
    "timestamp": None,
    "step": 0
}

def get_run_context() -> dict:
    """Initializes or retrieves the current run context."""
    global _RUN_CONTEXT
    
    if _RUN_CONTEXT["dir"] is None:
        root_dir = CONFIG.get("output", {}).get("root_dir", "output")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(root_dir, timestamp)
        
        config_dst = os.path.join(run_dir, "config")
        
        # Create agent directories
        os.makedirs(os.path.join(run_dir, "dataops"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "mlops"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "vizops"), exist_ok=True)
        
        if not os.path.exists(config_dst):
            os.makedirs(config_dst, exist_ok=True)
            for f in ["config.yaml", "dataops.yaml", "infrastructure.yml"]:
                if os.path.exists(f):
                    shutil.copy(f, config_dst)
            
        _RUN_CONTEXT["dir"] = run_dir
        _RUN_CONTEXT["timestamp"] = timestamp
        
    return _RUN_CONTEXT

def calculate_file_hash(file_path: str) -> str:
    """Calculates a hash of a file's content."""
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()[:8]

def _generate_filename(prefix: str, extension: str, content_hash: str) -> str:
    """Generates the standardized filename."""
    context = get_run_context()
    context["step"] += 1
    step = context["step"]
    timestamp = context["timestamp"]
    
    nn = step % 100
    return f"{step:03d}_{timestamp}{nn:02d}_{content_hash}_{prefix}.{extension}"

def save_dataframe_to_csv(df: pd.DataFrame, prefix: str, subdir: str = "dataops") -> str:
    """Saves DataFrame to CSV with content hash in filename."""
    context = get_run_context()
    output_dir = os.path.join(context["dir"], subdir)
    
    # Temp filename
    temp_filename = f"{prefix}_temp.csv"
    temp_path = os.path.join(output_dir, temp_filename)
    
    df.to_csv(temp_path, index=False)
    
    # Calculate hash from file
    content_hash = calculate_file_hash(temp_path)
    
    # Final filename
    final_filename = _generate_filename(prefix, "csv", content_hash)
    final_path = os.path.join(output_dir, final_filename)
    
    os.rename(temp_path, final_path)
    console.print(f"[dim]Saved CSV:[/dim] {final_path}")
    return final_path

def save_model(model, prefix: str, subdir: str = "mlops") -> str:
    """Saves a model object to a file with content hash in filename."""
    context = get_run_context()
    output_dir = os.path.join(context["dir"], subdir)
    
    # Temp filename
    temp_filename = f"{prefix}_temp.joblib"
    temp_path = os.path.join(output_dir, temp_filename)
    
    joblib.dump(model, temp_path)
    
    # Calculate hash from file
    content_hash = calculate_file_hash(temp_path)
    
    # Final filename
    final_filename = _generate_filename(prefix, "joblib", content_hash)
    final_path = os.path.join(output_dir, final_filename)
    
    os.rename(temp_path, final_path)
    console.print(f"[dim]Saved Model:[/dim] {final_path}")
    return final_path

import json

def save_metrics(metrics: dict, prefix: str, subdir: str = "mlops") -> str:
    """Saves metrics dictionary to a JSON file."""
    context = get_run_context()
    output_dir = os.path.join(context["dir"], subdir)
    
    # Temp filename
    temp_filename = f"{prefix}_temp.json"
    temp_path = os.path.join(output_dir, temp_filename)
    
    with open(temp_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    # Calculate hash from file
    content_hash = calculate_file_hash(temp_path)
    
    # Final filename
    final_filename = _generate_filename(prefix, "json", content_hash)
    final_path = os.path.join(output_dir, final_filename)
    
    os.rename(temp_path, final_path)
    console.print(f"[dim]Saved Metrics:[/dim] {final_path}")
    return final_path

def save_altair_chart(chart, prefix: str, subdir: str = "vizops") -> str:
    """Saves an Altair chart to an HTML file."""
    context = get_run_context()
    output_dir = os.path.join(context["dir"], subdir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Temp filename
    temp_filename = f"{prefix}_temp.html"
    temp_path = os.path.join(output_dir, temp_filename)
    
    chart.save(temp_path)
    
    # Calculate hash from file
    content_hash = calculate_file_hash(temp_path)
    
    # Final filename
    final_filename = _generate_filename(prefix, "html", content_hash)
    final_path = os.path.join(output_dir, final_filename)
    
    os.rename(temp_path, final_path)
    console.print(f"[dim]Saved Chart:[/dim] {final_path}")
    return final_path

def log_analysis(hypothesis: str, finding: str, artifacts: list = None, subdir: str = "vizops"):
    """
    Logs an analysis entry.

    Args:
        hypothesis: The hypothesis being tested.
        finding: The conclusion or observation derived from the data.
        artifacts: List of file paths (CSVs, charts) generated during the analysis.
        subdir: Subdirectory to save the log (default: 'vizops').
    """
    context = get_run_context()
    log_file = os.path.join(context["dir"], subdir, "analysis_log.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    entry = f"\n### Analysis Entry: {timestamp}\n"
    entry += f"**Hypothesis:** {hypothesis}\n\n"
    entry += f"**Finding:** {finding}\n\n"
    if artifacts:
        entry += "**Artifacts:**\n"
        for artifact in artifacts:
            entry += f"- `{artifact}`\n"
    entry += "---\n"
    
    with open(log_file, "a") as f:
        f.write(entry)
    
    # Output to terminal
    console.print(f"[bold]Analysis Entry:[/bold] {timestamp}")
    console.print(f"[blue]Hypothesis:[/blue] {hypothesis}")
    console.print(f"[green]Finding:[/green] {finding}")
    if artifacts:
        console.print("[yellow]Artifacts:[/yellow]")
        for artifact in artifacts:
            console.print(f"- {artifact}")
            
    return "Analysis logged successfully."

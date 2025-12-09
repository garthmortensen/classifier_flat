import sys
import os
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from tabulate import tabulate

# Add the current directory to sys.path so we can import tools
sys.path.append(os.getcwd())

from dataops import get_table_schema, execute_sql, log_analysis, profile_dataset

console = Console()

def test_tools():
    console.rule("[bold blue]Testing DataOps Tools[/bold blue]")
    
    # 1. Test Connection and Schema
    try:
        console.print("[yellow]Step 1: Attempting to fetch schema for 'fct_claim'...[/yellow]")
        schema = get_table_schema("fct_claim")
        
        # Display Schema using Rich Table
        table = Table(title="Table Schema: fct_claim")
        table.add_column("Column Name", style="cyan", no_wrap=True)
        table.add_column("Data Type", style="magenta")
        
        for col, dtype in schema.items():
            table.add_row(col, str(dtype))
            
        console.print(table)
        
        # Log this finding
        log_analysis(
            hypothesis="Database connection and schema retrieval work.",
            finding=f"Successfully connected to DB. 'fct_claim' schema retrieved.",
            artifacts=[]
        )
        console.print("[green]✓ Schema fetched and logged successfully.[/green]\n")
        
    except Exception as e:
        console.print(f"[bold red]Error fetching schema:[/bold red] {e}")
        return

    # 2. Test SQL Execution (Limit 5)
    try:
        console.print("[yellow]Step 2: Attempting to query 'fct_claim' (limit 5)...[/yellow]")
        csv_path = execute_sql("SELECT * FROM fct_claim LIMIT 5")
        console.print(f"Query executed. Result saved to: [bold underline]{csv_path}[/bold underline]")
        
        # 3. Test Profiling
        console.print("[yellow]Step 3: Profiling the result...[/yellow]")
        profile = profile_dataset(csv_path)
        
        # Display General Stats
        console.print(Panel(f"Rows: [bold]{profile['rows']}[/bold]\nColumns: [bold]{len(profile['columns'])}[/bold]", title="General Stats", expand=False))

        # Display Numeric Stats using Tabulate
        if profile.get('numeric_stats'):
            console.print("[bold]Numeric Statistics (via Tabulate):[/bold]")
            # Convert dict of dicts to a format suitable for tabulate
            # Transpose so that stats (count, mean, etc.) are columns
            stats_df = pd.DataFrame(profile['numeric_stats']).T
            print(tabulate(stats_df, headers='keys', tablefmt='psql'))
        
        log_analysis(
            hypothesis="Data extraction and profiling work.",
            finding=f"Extracted 5 rows. Profile generated.",
            artifacts=[csv_path]
        )
        console.print("[green]✓ Data extracted, profiled, and logged successfully.[/green]")
        
    except Exception as e:
        console.print(f"[bold red]Error executing SQL:[/bold red] {e}")

if __name__ == "__main__":
    test_tools()

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from orchestrator import CONFIG, save_dataframe_to_csv, log_analysis

def get_db_engine():
    """Creates a SQLAlchemy engine based on config.yaml."""
    db_config = CONFIG.get("database", {})
    if not db_config:
        raise ValueError("Database configuration not found.")
        
    # Construct connection string for PostgreSQL
    url = f"postgresql+psycopg2://{db_config['username']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    return create_engine(url)

def execute_sql(query: str) -> str:
    """
    Runs a SQL query against the warehouse and returns the path to the saved CSV result.

    Args:
        query: A valid SQL SELECT statement.

    Returns:
        str: File path to the saved CSV containing the query results.
    """
    engine = get_db_engine()
    with engine.connect() as conn:
        if "schema" in CONFIG.get("database", {}):
            conn.execute(text(f"SET search_path TO {CONFIG['database']['schema']}"))
        
        df = pd.read_sql(query, conn)
    
    return save_dataframe_to_csv(df, "query_result")

def get_table_schema(table_name: str) -> dict:
    """
    Returns column names and types for a given table.

    Args:
        table_name: The name of the table (e.g., 'fct_claim' or 'dw.fct_claim').

    Returns:
        dict: A dictionary mapping column names to their data types.
    """
    engine = get_db_engine()
    inspector = inspect(engine)
    
    schema = CONFIG.get("database", {}).get("schema")
    if "." in table_name:
        schema, table_name = table_name.split(".", 1)
        
    columns = inspector.get_columns(table_name, schema=schema)
    schema_info = {col["name"]: str(col["type"]) for col in columns}
    return schema_info

def profile_dataset(file_path: str) -> dict:
    """
    Returns summary statistics (mean, null counts, cardinality) for a dataset.

    Args:
        file_path: Path to the CSV file to profile.

    Returns:
        dict: A dictionary containing row count, column list, null counts, cardinality, and numeric stats.
    """
    df = pd.read_csv(file_path)
    profile = {
        "rows": len(df),
        "columns": list(df.columns),
        "null_counts": df.isnull().sum().to_dict(),
        "cardinality": df.nunique().to_dict(),
        "numeric_stats": df.describe().to_dict()
    }
    return profile

def join_datasets(left_path: str, right_path: str, on: list, how: str = "inner") -> str:
    """
    Merges two datasets and returns the new file path.

    Args:
        left_path: Path to the left CSV file.
        right_path: Path to the right CSV file.
        on: List of column names to join on (must exist in both files).
        how: Type of join ('inner', 'left', 'right', 'outer'). Defaults to 'inner'.

    Returns:
        str: File path to the merged CSV.
    """
    df_left = pd.read_csv(left_path)
    df_right = pd.read_csv(right_path)
    
    merged_df = pd.merge(df_left, df_right, on=on, how=how)
    
    return save_dataframe_to_csv(merged_df, "joined_data")

def create_derived_feature(file_path: str, expression: str, new_col_name: str) -> str:
    """
    Adds a new column based on a pandas-compatible expression.

    Args:
        file_path: Path to the CSV file.
        expression: A string expression to evaluate (e.g., "total_amount / 100" or "col_a + col_b").
        new_col_name: The name of the new column to create.

    Returns:
        str: File path to the CSV with the new feature.
    """
    df = pd.read_csv(file_path)
    try:
        df[new_col_name] = df.eval(expression)
    except Exception as e:
        raise ValueError(f"Failed to evaluate expression '{expression}': {e}")
        
    return save_dataframe_to_csv(df, "derived_feature")

def aggregate_dataset(file_path: str, group_by: list, aggregations: dict) -> str:
    """
    Aggregates a dataset by grouping columns and applying aggregation functions.

    Args:
        file_path: Path to the CSV file.
        group_by: List of column names to group by.
        aggregations: Dictionary mapping columns to functions (e.g., {'amount': 'sum', 'id': 'count'}).

    Returns:
        str: File path to the aggregated CSV.
    """
    df = pd.read_csv(file_path)
    agg_df = df.groupby(group_by).agg(aggregations).reset_index()
    
    return save_dataframe_to_csv(agg_df, "aggregated_data")

def extract_date_features(file_path: str, date_col: str, features: list = ["year", "month", "day", "weekday"]) -> str:
    """
    Extracts date components from a datetime column.

    Args:
        file_path: Path to the CSV file.
        date_col: The name of the column containing date/datetime values.
        features: List of features to extract. Options: "year", "month", "day", "weekday".

    Returns:
        str: File path to the CSV with added date features.
    """
    df = pd.read_csv(file_path)
    df[date_col] = pd.to_datetime(df[date_col])
    
    for feature in features:
        if feature == "year":
            df[f"{date_col}_year"] = df[date_col].dt.year
        elif feature == "month":
            df[f"{date_col}_month"] = df[date_col].dt.month
        elif feature == "day":
            df[f"{date_col}_day"] = df[date_col].dt.day
        elif feature == "weekday":
            df[f"{date_col}_weekday"] = df[date_col].dt.weekday
            
    return save_dataframe_to_csv(df, "date_features")

def bin_numeric_feature(file_path: str, col_name: str, bins: int = 10, labels: list = None) -> str:
    """
    Bins a numeric column into discrete intervals.

    Args:
        file_path: Path to the CSV file.
        col_name: The numeric column to bin.
        bins: Number of bins to create.
        labels: Optional list of labels for the bins.

    Returns:
        str: File path to the CSV with the new binned column.
    """
    df = pd.read_csv(file_path)
    new_col = f"{col_name}_bin"
    df[new_col] = pd.cut(df[col_name], bins=bins, labels=labels)
    
    return save_dataframe_to_csv(df, "binned_feature")

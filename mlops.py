import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, roc_curve
from sklearn.calibration import calibration_curve
from sklearn.model_selection import cross_val_score
import optuna
import joblib
from orchestrator import save_model, save_dataframe_to_csv, save_metrics

def split_data_time_series(file_path: str, date_col: str, cutoff_date: str) -> dict:
    """
    Splits data into train/test paths based on time.
    """
    df = pd.read_csv(file_path)
    df[date_col] = pd.to_datetime(df[date_col])
    cutoff = pd.to_datetime(cutoff_date)
    
    train_df = df[df[date_col] < cutoff]
    test_df = df[df[date_col] >= cutoff]
    
    train_path = save_dataframe_to_csv(train_df, "train_split", subdir="mlops")
    test_path = save_dataframe_to_csv(test_df, "test_split", subdir="mlops")
    
    return {"train": train_path, "test": test_path}

def train_model(train_path: str, target: str, algorithm: str, params: dict) -> str:
    """
    Trains a model (XGBoost/LGBM) and returns the model artifact path.
    """
    df = pd.read_csv(train_path)
    X = df.drop(columns=[target])
    y = df[target]
    
    # Ensure we only use numeric columns for simplicity, or assume preprocessed
    # Dropping non-numeric columns to avoid errors if not handled
    X = X.select_dtypes(include=['number'])
    
    if algorithm.lower() == "xgboost":
        model = xgb.XGBClassifier(**params)
        model.fit(X, y)
    elif algorithm.lower() == "lightgbm":
        model = lgb.LGBMClassifier(**params)
        model.fit(X, y)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
        
    return save_model(model, f"{algorithm}_model", subdir="mlops")

def run_backtest(model_path: str, test_path: str, target_col: str = "readmission_30d") -> dict:
    """
    Generates predictions and returns a dictionary of metrics.
    Saves metrics and plot data to JSON files in output/mlops/.
    """
    model = joblib.load(model_path)
    df = pd.read_csv(test_path)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in test data.")
        
    X_test = df.drop(columns=[target_col])
    # Ensure we match the training columns (numeric only as per train_model)
    X_test = X_test.select_dtypes(include=['number'])
    
    y_test = df[target_col]
    
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # 1. Scalar Metrics
    metrics = {
        "auc": float(roc_auc_score(y_test, y_prob)),
        "f1": float(f1_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred))
    }
    
    metrics_path = save_metrics(metrics, "evaluation_metrics", subdir="mlops")
    
    # 2. Curve Data (ROC & Calibration)
    fpr, tpr, thresh_roc = roc_curve(y_test, y_prob)
    roc_data = [{"fpr": float(f), "tpr": float(t), "threshold": float(th)} 
                for f, t, th in zip(fpr, tpr, thresh_roc)]

    prob_true, prob_pred_cal = calibration_curve(y_test, y_prob, n_bins=10)
    cal_data = [{"prob_pred": float(pp), "prob_true": float(pt)} 
                for pp, pt in zip(prob_pred_cal, prob_true)]
                
    plots_data = {
        "roc_curve": roc_data,
        "calibration_curve": cal_data
    }
    
    plots_path = save_metrics(plots_data, "plots_data", subdir="mlops")
    
    return {
        "metrics": metrics,
        "metrics_file": metrics_path,
        "plots_file": plots_path
    }

def optimize_hyperparameters(train_path: str, target: str, n_trials: int) -> dict:
    """
    Runs an Optuna study and returns the best parameters.
    """
    df = pd.read_csv(train_path)
    X = df.drop(columns=[target])
    X = X.select_dtypes(include=['number'])
    y = df[target]
    
    def objective(trial):
        param = {
            'verbosity': 0,
            'objective': 'binary:logistic',
            'booster': trial.suggest_categorical('booster', ['gbtree', 'gblinear', 'dart']),
            'lambda': trial.suggest_float('lambda', 1e-8, 1.0, log=True),
            'alpha': trial.suggest_float('alpha', 1e-8, 1.0, log=True),
        }

        if param['booster'] == 'gbtree' or param['booster'] == 'dart':
            param['max_depth'] = trial.suggest_int('max_depth', 1, 9)
            param['eta'] = trial.suggest_float('eta', 1e-8, 1.0, log=True)
            param['gamma'] = trial.suggest_float('gamma', 1e-8, 1.0, log=True)
            param['grow_policy'] = trial.suggest_categorical('grow_policy', ['depthwise', 'lossguide'])

        if param['booster'] == 'dart':
            param['sample_type'] = trial.suggest_categorical('sample_type', ['uniform', 'weighted'])
            param['normalize_type'] = trial.suggest_categorical('normalize_type', ['tree', 'forest'])
            param['rate_drop'] = trial.suggest_float('rate_drop', 1e-8, 1.0, log=True)
            param['skip_drop'] = trial.suggest_float('skip_drop', 1e-8, 1.0, log=True)

        model = xgb.XGBClassifier(**param)
        
        score = cross_val_score(model, X, y, n_jobs=-1, cv=3, scoring="roc_auc").mean()
        return score

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    
    return study.best_params

import pandas as pd
import altair as alt
import joblib
from sklearn.metrics import roc_curve, confusion_matrix
from sklearn.calibration import calibration_curve
from orchestrator import save_altair_chart

def plot_roc_curve(model_path: str, test_path: str, output_dir: str = "vizops", target_col: str = "readmission_30d") -> str:
    """
    Generates a ROC curve chart and returns the path.
    """
    model = joblib.load(model_path)
    df = pd.read_csv(test_path)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in test data.")
        
    X_test = df.drop(columns=[target_col])
    X_test = X_test.select_dtypes(include=['number'])
    y_test = df[target_col]
    
    y_prob = model.predict_proba(X_test)[:, 1]
    
    fpr, tpr, thresholds = roc_curve(y_test, y_prob)
    
    roc_df = pd.DataFrame({
        'False Positive Rate': fpr,
        'True Positive Rate': tpr,
        'Threshold': thresholds
    })
    
    base = alt.Chart(roc_df).encode(
        x='False Positive Rate',
        y='True Positive Rate',
        tooltip=['False Positive Rate', 'True Positive Rate', 'Threshold']
    )
    
    line = base.mark_line(color='blue')
    
    diagonal = alt.Chart(pd.DataFrame({'x': [0, 1], 'y': [0, 1]})).mark_line(
        color='gray', strokeDash=[5, 5]
    ).encode(x='x', y='y')
    
    chart = (line + diagonal).properties(title='ROC Curve')
    
    return save_altair_chart(chart, "roc_curve", subdir=output_dir)

def plot_confusion_matrix(model_path: str, test_path: str, output_dir: str = "vizops", target_col: str = "readmission_30d", threshold: float = 0.5) -> str:
    """
    Generates a confusion matrix chart.
    """
    model = joblib.load(model_path)
    df = pd.read_csv(test_path)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in test data.")

    X_test = df.drop(columns=[target_col])
    X_test = X_test.select_dtypes(include=['number'])
    y_test = df[target_col]
    
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)
    
    cm = confusion_matrix(y_test, y_pred)
    
    cm_df = pd.DataFrame({
        'Actual': ['Negative', 'Negative', 'Positive', 'Positive'],
        'Predicted': ['Negative', 'Positive', 'Negative', 'Positive'],
        'Count': cm.flatten()
    })
    
    chart = alt.Chart(cm_df).mark_rect().encode(
        x='Predicted:N',
        y='Actual:N',
        color='Count:Q',
        tooltip=['Actual', 'Predicted', 'Count']
    ).properties(title=f'Confusion Matrix (Threshold={threshold})')
    
    text = chart.mark_text(baseline='middle').encode(
        text='Count:Q',
        color=alt.condition(
            alt.datum.Count > cm.max() / 2,
            alt.value('white'),
            alt.value('black')
        )
    )
    
    return save_altair_chart(chart + text, "confusion_matrix", subdir=output_dir)

def plot_feature_importance(model_path: str, output_dir: str = "vizops") -> str:
    """
    Generates a feature importance bar chart.
    """
    model = joblib.load(model_path)
    
    # Handle different model types if necessary, assuming XGBoost/LGBM/Sklearn with feature_importances_
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        # Try to get feature names
        if hasattr(model, 'feature_names_in_'):
            feature_names = model.feature_names_in_
        elif hasattr(model, 'get_booster'): # XGBoost
             feature_names = model.get_booster().feature_names
        else:
            feature_names = [f'feature_{i}' for i in range(len(importances))]
            
        df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': importances
        }).sort_values(by='Importance', ascending=False).head(20) # Top 20
        
        chart = alt.Chart(df).mark_bar().encode(
            x='Importance:Q',
            y=alt.Y('Feature:N', sort='-x'),
            tooltip=['Feature', 'Importance']
        ).properties(title='Feature Importance')
        
        return save_altair_chart(chart, "feature_importance", subdir=output_dir)
    else:
        raise ValueError("Model does not support feature importance.")

def plot_calibration_curve(model_path: str, test_path: str, output_dir: str = "vizops", target_col: str = "readmission_30d") -> str:
    """
    Generates a calibration plot.
    """
    model = joblib.load(model_path)
    df = pd.read_csv(test_path)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in test data.")

    X_test = df.drop(columns=[target_col])
    X_test = X_test.select_dtypes(include=['number'])
    y_test = df[target_col]
    
    y_prob = model.predict_proba(X_test)[:, 1]
    
    prob_true, prob_pred = calibration_curve(y_test, y_prob, n_bins=10)
    
    cal_df = pd.DataFrame({
        'Mean Predicted Probability': prob_pred,
        'Fraction of Positives': prob_true
    })
    
    base = alt.Chart(cal_df).encode(
        x='Mean Predicted Probability',
        y='Fraction of Positives',
        tooltip=['Mean Predicted Probability', 'Fraction of Positives']
    )
    
    points = base.mark_circle(color='blue')
    line = base.mark_line(color='blue')
    
    diagonal = alt.Chart(pd.DataFrame({'x': [0, 1], 'y': [0, 1]})).mark_line(
        color='gray', strokeDash=[5, 5]
    ).encode(x='x', y='y')
    
    chart = (points + line + diagonal).properties(title='Calibration Curve')
    
    return save_altair_chart(chart, "calibration_curve", subdir=output_dir)

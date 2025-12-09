import unittest
import os
import shutil
import tempfile
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
import vizops
import orchestrator

class TestVizOpsTools(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for INPUTS (data/model)
        self.input_dir = tempfile.mkdtemp()
        
        # Define OUTPUT directory
        self.output_dir = os.path.abspath("output")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Save original context
        self.original_context = orchestrator._RUN_CONTEXT.copy()
        
        # Patch orchestrator context to write to output/
        # We set 'dir' to self.output_dir so subdir='vizops' becomes output/vizops
        orchestrator._RUN_CONTEXT = {
            "dir": self.output_dir,
            "timestamp": "TEST",
            "step": 0
        }
        
        # Create dummy data
        self.target_col = "target"
        self.df = pd.DataFrame({
            "feature1": np.random.rand(100),
            "feature2": np.random.rand(100),
            self.target_col: np.random.randint(0, 2, 100)
        })
        
        self.test_path = os.path.join(self.input_dir, "test_data.csv")
        self.df.to_csv(self.test_path, index=False)
        
        # Train and save a dummy model
        self.model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = self.df.drop(columns=[self.target_col])
        y = self.df[self.target_col]
        self.model.fit(X, y)
        
        self.model_path = os.path.join(self.input_dir, "model.joblib")
        joblib.dump(self.model, self.model_path)

    def tearDown(self):
        # Restore original context
        orchestrator._RUN_CONTEXT = self.original_context
        
        # Remove the temporary input directory
        shutil.rmtree(self.input_dir)

    def test_plot_roc_curve(self):
        output_path = vizops.plot_roc_curve(
            self.model_path, 
            self.test_path, 
            output_dir="vizops", 
            target_col=self.target_col
        )
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(output_path.endswith(".html"))
        self.assertIn("roc_curve", output_path)

    def test_plot_confusion_matrix(self):
        output_path = vizops.plot_confusion_matrix(
            self.model_path, 
            self.test_path, 
            output_dir="vizops", 
            target_col=self.target_col,
            threshold=0.5
        )
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(output_path.endswith(".html"))
        self.assertIn("confusion_matrix", output_path)

    def test_plot_feature_importance(self):
        output_path = vizops.plot_feature_importance(
            self.model_path, 
            output_dir="vizops"
        )
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(output_path.endswith(".html"))
        self.assertIn("feature_importance", output_path)

    def test_plot_calibration_curve(self):
        output_path = vizops.plot_calibration_curve(
            self.model_path, 
            self.test_path, 
            output_dir="vizops", 
            target_col=self.target_col
        )
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(output_path.endswith(".html"))
        self.assertIn("calibration_curve", output_path)

if __name__ == '__main__':
    unittest.main()

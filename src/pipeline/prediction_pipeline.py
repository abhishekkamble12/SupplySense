import os
import sys
import pickle
import pandas as pd
import numpy as np
from logger.logger import logging
from exception.exception import CustomException

class PredictionPipeline:
    def __init__(self):
        self.model_path = os.path.join("saved_models", "model.pkl")

    def predict(self, features_df: pd.DataFrame) -> np.ndarray:
        try:
            logging.info("Starting prediction pipeline")
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found at {self.model_path}. Please run training pipeline first.")
                
            with open(self.model_path, 'rb') as f:
                model = pickle.load(f)
                
            # Perform prediction
            logging.info("Model loaded successfully. Generating predictions...")
            preds = model.predict(features_df)
            return preds
            
        except Exception as e:
            raise CustomException(e, sys)

import sys
import pandas as pd
import numpy as np
from pipeline.prediction_pipeline import PredictionPipeline
from exception.exception import CustomException

class Step06PredictionPipeline:
    def __init__(self):
        self.predictor = PredictionPipeline()

    def main(self, features_df: pd.DataFrame) -> np.ndarray:
        try:
            return self.predictor.predict(features_df)
        except Exception as e:
            raise CustomException(e, sys)

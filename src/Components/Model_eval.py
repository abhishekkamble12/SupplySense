import os
import sys
import pickle
import numpy as np
from sklearn.metrics import mean_squared_error
from entity.config_entity import ModelEvaluationConfig
from entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact, ModelEvaluationArtifact
from logger.logger import logging
from exception.exception import CustomException

class ModelEvaluation:
    def __init__(self, model_evaluation_config: ModelEvaluationConfig,
                 data_transformation_artifact: DataTransformationArtifact,
                 model_trainer_artifact: ModelTrainerArtifact):
        self.config = model_evaluation_config
        self.transformation_artifact = data_transformation_artifact
        self.model_trainer_artifact = model_trainer_artifact

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        logging.info("Starting Model Evaluation component")
        try:
            # 1. Load the validation dataset (transformed test set)
            test_arr = np.load(self.transformation_artifact.transformed_test_file_path)
            X_val, y_val = test_arr[:, :-1], test_arr[:, -1]
            
            # 2. Load the newly trained model
            with open(self.model_trainer_artifact.trained_model_file_path, 'rb') as f:
                trained_model = pickle.load(f)
                
            trained_model_preds = trained_model.predict(X_val)
            trained_model_rmse = np.sqrt(mean_squared_error(y_val, trained_model_preds))
            
            is_model_accepted = True
            changed_accuracy = 0.0
            s3_model_path = ""
            
            # 3. Load baseline/production model if exists (e.g. local registry or AWS S3 simulator)
            # In a real setup, we would download the model from S3 using self.config.s3_model_key_path
            # For local simulator, we check if a baseline model exists in a target folder
            baseline_model_path = os.path.join("artifacts", "baseline_model.pkl")
            
            if os.path.exists(baseline_model_path):
                logging.info("Found baseline model. Comparing performance...")
                with open(baseline_model_path, 'rb') as f:
                    baseline_model = pickle.load(f)
                baseline_preds = baseline_model.predict(X_val)
                baseline_rmse = np.sqrt(mean_squared_error(y_val, baseline_preds))
                
                # Check if new model is better (lower RMSE is better)
                rmse_difference = baseline_rmse - trained_model_rmse
                logging.info(f"Baseline RMSE: {baseline_rmse:.4f} | Trained Model RMSE: {trained_model_rmse:.4f}")
                
                if rmse_difference >= self.config.changed_threshold_score:
                    is_model_accepted = True
                    changed_accuracy = rmse_difference
                    logging.info("Trained model outperforms baseline. Model accepted.")
                else:
                    is_model_accepted = False
                    changed_accuracy = rmse_difference
                    logging.info("Trained model does not outperform baseline enough. Model rejected.")
            else:
                logging.info("No baseline model found. Accepting the newly trained model by default.")
                
            return ModelEvaluationArtifact(
                is_model_accepted=is_model_accepted,
                changed_accuracy=changed_accuracy,
                s3_model_path=s3_model_path,
                trained_model_path=self.model_trainer_artifact.trained_model_file_path
            )
        except Exception as e:
            raise CustomException(e, sys)

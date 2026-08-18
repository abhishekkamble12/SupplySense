import os
import sys
import shutil
from entity.config_entity import ModelPusherConfig
from entity.artifact_entity import ModelEvaluationArtifact, ModelPusherArtifact
from logger.logger import logging
from exception.exception import CustomException

class ModelPusher:
    def __init__(self, model_pusher_config: ModelPusherConfig, model_evaluation_artifact: ModelEvaluationArtifact):
        self.config = model_pusher_config
        self.model_eval_artifact = model_evaluation_artifact

    def initiate_model_pusher(self) -> ModelPusherArtifact:
        logging.info("Starting Model Pusher component")
        try:
            if self.model_eval_artifact.is_model_accepted:
                # In production: Upload model to S3 bucket using self.config.bucket_name
                # Local deploy: Copy to baseline model registry and deployment model paths
                
                trained_model_path = self.model_eval_artifact.trained_model_path
                baseline_model_path = os.path.join("artifacts", "baseline_model.pkl")
                os.makedirs(os.path.dirname(baseline_model_path), exist_ok=True)
                
                # Copy to baseline to act as comparison model for next run
                shutil.copy(trained_model_path, baseline_model_path)
                
                # Copy to saved models directory
                saved_model_dir = os.path.join("saved_models")
                os.makedirs(saved_model_dir, exist_ok=True)
                shutil.copy(trained_model_path, os.path.join(saved_model_dir, "model.pkl"))
                
                logging.info("Model pushed successfully to local registry and saved_models directory.")
                s3_model_path = os.path.join(self.config.bucket_name, self.config.s3_model_key_path)
            else:
                logging.info("Model was not accepted during evaluation. Skipping model pushing.")
                s3_model_path = ""
                
            return ModelPusherArtifact(
                bucket_name=self.config.bucket_name,
                s3_model_path=s3_model_path
            )
        except Exception as e:
            raise CustomException(e, sys)

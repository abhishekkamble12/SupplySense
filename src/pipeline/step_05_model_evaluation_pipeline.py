import sys
from logger.logger import logging
from Components.Model_eval import ModelEvaluation
from Components.Model_pusher import ModelPusher
from config.confirguation import ConfigurationManager
from entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact,
    ModelPusherArtifact
)
from exception.exception import CustomException

class ModelEvaluationPipeline:
    def __init__(self):
        pass

    def main(self, data_transformation_artifact: DataTransformationArtifact,
             model_trainer_artifact: ModelTrainerArtifact) -> ModelPusherArtifact:
        try:
            logging.info(">>> Starting Model Evaluation and Pushing Pipeline Stage <<<")
            
            # 1. Initialize Configuration Manager
            config_manager = ConfigurationManager()
            
            # 2. Get Model Evaluation Configurations
            model_eval_config = config_manager.get_model_evaluation_config()

            # 3. Instantiate and run Model Evaluation component
            model_evaluation = ModelEvaluation(
                model_evaluation_config=model_eval_config,
                data_transformation_artifact=data_transformation_artifact,
                model_trainer_artifact=model_trainer_artifact
            )
            model_eval_artifact = model_evaluation.initiate_model_evaluation()

            # 4. Get Model Pusher Configurations
            model_pusher_config = config_manager.get_model_pusher_config()

            # 5. Instantiate and run Model Pusher component
            model_pusher = ModelPusher(
                model_pusher_config=model_pusher_config,
                model_evaluation_artifact=model_eval_artifact
            )
            model_pusher_artifact = model_pusher.initiate_model_pusher()

            logging.info(">>> Model Evaluation and Pushing Pipeline Stage Completed Successfully <<<\n")
            return model_pusher_artifact
            
        except Exception as e:
            raise CustomException(e, sys)

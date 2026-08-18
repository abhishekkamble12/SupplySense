import sys
from logger.logger import logging
from Components.Model_trainer import ModelTrainer
from config.confirguation import ConfigurationManager
from entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact
from exception.exception import CustomException

class ModelTrainerPipeline:
    def __init__(self):
        pass

    def main(self, data_transformation_artifact: DataTransformationArtifact) -> ModelTrainerArtifact:
        try:
            logging.info(">>> Starting Model Trainer Pipeline Stage <<<")
            
            # 1. Initialize Configuration Manager
            config_manager = ConfigurationManager()
            
            # 2. Get Model Trainer Configurations
            model_trainer_config = config_manager.get_model_trainer_config()

            # 3. Instantiate Model Trainer component
            model_trainer = ModelTrainer(
                model_trainer_config=model_trainer_config,
                data_transformation_artifact=data_transformation_artifact
            )

            # 4. Run model training (LightGBM fit, pickle save)
            model_trainer_artifact = model_trainer.initiate_model_trainer()

            logging.info(">>> Model Trainer Pipeline Stage Completed Successfully <<<\n")
            return model_trainer_artifact
            
        except Exception as e:
            raise CustomException(e, sys)

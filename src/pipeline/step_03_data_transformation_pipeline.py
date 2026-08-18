import sys
from logger.logger import logging
from Components.Data_transformation import DataTransformation
from config.confirguation import ConfigurationManager
from entity.artifact_entity import DataValidationArtifact, DataTransformationArtifact
from exception.exception import CustomException

class DataTransformationPipeline:
    def __init__(self):
        pass

    def main(self, data_validation_artifact: DataValidationArtifact) -> DataTransformationArtifact:
        try:
            logging.info(">>> Starting Data Transformation Pipeline Stage <<<")
            
            # 1. Initialize Configuration Manager
            config_manager = ConfigurationManager()
            
            # 2. Get Data Transformation Configurations
            data_transformation_config = config_manager.get_data_transformation_config()

            # 3. Instantiate Data Transformation component
            data_transformation = DataTransformation(
                data_transformation_config=data_transformation_config,
                data_validation_artifact=data_validation_artifact
            )

            # 4. Run data transformation (lags, rolling features, category codes)
            data_transformation_artifact = data_transformation.initiate_data_transformation()

            logging.info(">>> Data Transformation Pipeline Stage Completed Successfully <<<\n")
            return data_transformation_artifact
            
        except Exception as e:
            raise CustomException(e, sys)

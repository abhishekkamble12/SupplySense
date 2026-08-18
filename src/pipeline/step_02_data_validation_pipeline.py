import sys 
from logger.logger import logging
from Components.Data_Validation import DataValidation
from config.confirguation import ConfigurationManager
from entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from exception.exception import CustomException

class DataValidationPipeline:
    def __init__(self):
        pass

    def main(self, data_ingestion_artifact: DataIngestionArtifact) -> DataValidationArtifact:
        try:
            logging.info(">>> Starting Data Validation Pipeline Stage <<<")
            
            # 1. Initialize Configuration Manager
            config_manager = ConfigurationManager()
            
            # 2. Get Data Validation Configurations
            data_validation_config = config_manager.get_data_validation_config()

            # 3. Instantiate Data Validation component (requires ingestion artifact to load the data files)
            data_validation = DataValidation(
                data_validation_config=data_validation_config,
                data_ingestion_artifact=data_ingestion_artifact
            )

            # 4. Run data validation
            data_validation_artifact = data_validation.initiate_data_validation()

            logging.info(">>> Data Validation Pipeline Stage Completed Successfully <<<\n")
            return data_validation_artifact
            
        except Exception as e:
            raise CustomException(e, sys)
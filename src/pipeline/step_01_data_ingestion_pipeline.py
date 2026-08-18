import sys
from config.configuration import ConfigurationManager
from Components.Data_ingestion import DataIngestion
from entity.artifact_entity import DataIngestionArtifact
from logger.logger import logging
from exception.exception import CustomException

class DataIngestionPipeline:
    def __init__(self):
        pass

    def main(self) -> DataIngestionArtifact:
        try:
            logging.info(">>> Starting Data Ingestion Pipeline Stage <<<")
            
            # 1. Initialize Configuration Manager (reads config.yaml)
            config_manager = ConfigurationManager()
            
            # 2. Get Data Ingestion Configurations
            data_ingestion_config = config_manager.get_data_ingestion_config()
            
            # 3. Instantiate Data Ingestion component
            data_ingestion = DataIngestion(data_ingestion_config=data_ingestion_config)
            
            # 4. Run data ingestion (download, melt, merge, split)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
            
            logging.info(">>> Data Ingestion Pipeline Stage Completed Successfully <<<\n")
            return data_ingestion_artifact
            
        except Exception as e:
            raise CustomException(e, sys)

if __name__ == "__main__":
    try:
        pipeline = DataIngestionPipeline()
        pipeline.main()
    except Exception as e:
        print(e)

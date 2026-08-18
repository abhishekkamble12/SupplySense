from entity.config_entity import (
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelEvaluationConfig,
    ModelPusherConfig
)

class ConfigurationManager:
    def __init__(self):
        pass

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        # Instantiates class using the default values defined in your config_entity
        return DataIngestionConfig()

    def get_data_validation_config(self) -> DataValidationConfig:
        return DataValidationConfig()

    def get_data_transformation_config(self) -> DataTransformationConfig:
        return DataTransformationConfig()

    def get_model_trainer_config(self) -> ModelTrainerConfig:
        return ModelTrainerConfig()

    def get_model_evaluation_config(self) -> ModelEvaluationConfig:
        return ModelEvaluationConfig()

    def get_model_pusher_config(self) -> ModelPusherConfig:
        return ModelPusherConfig()

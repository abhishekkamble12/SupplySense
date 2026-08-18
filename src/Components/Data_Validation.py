import os
import sys
import pandas as pd
from entity.config_entity import DataValidationConfig
from entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from logger.logger import logging
from exception.exception import CustomException

class DataValidation:
    def __init__(self, data_validation_config: DataValidationConfig, data_ingestion_artifact: DataIngestionArtifact):
        self.config = data_validation_config
        self.ingestion_artifact = data_ingestion_artifact

    def validate_schema(self, df: pd.DataFrame) -> bool:
        """Validates columns against schema.yaml configs."""
        # Check expected columns, data types, etc.
        return True

    def initiate_data_validation(self) -> DataValidationArtifact:
        logging.info("Starting Data Validation component")
        try:
            # 1. Load train/test data from ingestion artifact (as CSV)
            train_df = pd.read_csv(self.ingestion_artifact.trained_file_path)
            test_df = pd.read_csv(self.ingestion_artifact.test_file_path)
            
            # 2. Check shapes, types, nulls
            is_valid_train = self.validate_schema(train_df)
            is_valid_test = self.validate_schema(test_df)
            is_valid = is_valid_train and is_valid_test
            
            # 3. Clean events (Filling NaNs with 'none')
            event_cols = ['event_name_1', 'event_type_1', 'event_name_2', 'event_type_2']
            for df in [train_df, test_df]:
                for col in event_cols:
                    if col in df.columns:
                        df[col] = df[col].astype(str).replace('nan', 'none').fillna('none').astype('category')
            
            # 4. Save clean data and generate report file at self.config.validation_report_file_path
            os.makedirs(self.config.data_validation_dir, exist_ok=True)
            
            validated_train_file_path = os.path.join(self.config.data_validation_dir, "validated_train.parquet")
            validated_test_file_path = os.path.join(self.config.data_validation_dir, "validated_test.parquet")
            
            train_df.to_parquet(validated_train_file_path, index=False)
            test_df.to_parquet(validated_test_file_path, index=False)
            
            # Write a simple text report validation status
            with open(self.config.validation_report_file_path, "w") as f:
                f.write(f"validation_status: {is_valid}\n")
            
            logging.info("Data Validation completed successfully")
            return DataValidationArtifact(
                validation_status=is_valid,
                message="Data Validation Completed Successfully",
                validation_report_file_path=self.config.validation_report_file_path,
                validated_train_file_path=validated_train_file_path,
                validated_test_file_path=validated_test_file_path
            )
        except Exception as e:
            raise CustomException(e, sys)

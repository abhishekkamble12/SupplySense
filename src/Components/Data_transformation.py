import os
import sys
import pickle
import pandas as pd
import numpy as np
from entity.config_entity import DataTransformationConfig
from entity.artifact_entity import DataTransformationArtifact, DataValidationArtifact
from logger.logger import logging
from exception.exception import CustomException

class DataTransformation:
    def __init__(self, data_transformation_config: DataTransformationConfig, data_validation_artifact: DataValidationArtifact):
        self.config = data_transformation_config
        self.validation_artifact = data_validation_artifact

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        logging.info("Starting Data Transformation component")
        try:
            # 1. Load validated data (from validated_train_file_path)
            df = pd.read_parquet(self.validation_artifact.validated_train_file_path)
            
            # 2. Sort values to calculate correct groups/shifts
            df['d_num'] = df['d'].str.replace('d_', '').astype('int16')
            df = df.sort_values(by=['id', 'd_num']).reset_index(drop=True)
            
            # 3. Create Lag features
            df['lag_28'] = df.groupby('id')['sales'].shift(28)
            df['lag_34'] = df.groupby('id')['sales'].shift(34)
            
            # 4. Create Rolling Mean features
            df['rolling_mean_7'] = df.groupby('id')['lag_28'].transform(lambda x: x.rolling(7).mean())
            df['rolling_mean_28'] = df.groupby('id')['lag_28'].transform(lambda x: x.rolling(28).mean())
            
            # 5. Drop NaN rows from shift windows
            lag_cols = ['lag_28', 'lag_34', 'rolling_mean_7', 'rolling_mean_28']
            df = df.dropna(subset=lag_cols).reset_index(drop=True)
            
            # 6. Convert category columns to integer codes so they can be saved in numpy arrays
            cat_cols = ['item_id', 'dept_id', 'cat_id', 'store_id', 'state_id', 'event_name_1', 'event_type_1']
            for col in cat_cols:
                if col in df.columns:
                    df[col] = df[col].cat.codes.astype('int16')
            
            # 7. Split train and test data based on time (days <= max_d - 28 vs days > max_d - 28)
            max_d = df['d_num'].max()
            train_df = df[df['d_num'] <= (max_d - 28)]
            test_df = df[df['d_num'] > (max_d - 28)]
            
            features = [
                'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id',
                'wday', 'month', 'year', 'event_name_1', 'event_type_1',
                'snap_CA', 'snap_TX', 'snap_WI', 'sell_price',
                'lag_28', 'lag_34', 'rolling_mean_7', 'rolling_mean_28'
            ]
            target = 'sales'
            
            train_arr = np.c_[train_df[features].values.astype(np.float32), train_df[target].values.astype(np.float32)]
            test_arr = np.c_[test_df[features].values.astype(np.float32), test_df[target].values.astype(np.float32)]
            
            # 8. Save transformed features and save preprocessing object (scaling/labels)
            os.makedirs(self.config.data_transformation_dir, exist_ok=True)
            os.makedirs(os.path.dirname(self.config.transformed_train_file_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.config.transformed_test_file_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.config.transformed_object_file_path), exist_ok=True)
            
            np.save(self.config.transformed_train_file_path, train_arr)
            np.save(self.config.transformed_test_file_path, test_arr)
            
            with open(self.config.transformed_object_file_path, 'wb') as f:
                pickle.dump({}, f)
            
            logging.info("Data Transformation completed successfully")
            return DataTransformationArtifact(
                transformed_object_file_path=self.config.transformed_object_file_path,
                transformed_train_file_path=self.config.transformed_train_file_path,
                transformed_test_file_path=self.config.transformed_test_file_path
            )
        except Exception as e:
            raise CustomException(e, sys)

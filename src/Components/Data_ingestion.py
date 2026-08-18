import os
import gc
import pandas as pd
from entity.config_entity import DataIngestionConfig
from entity.artifact_entity import DataIngestionArtifact
from logger.logger import logging
from exception.exception import CustomException
import sys
from sklearn.model_selection import train_test_split

class DataIngestion:
    def __init__(self, data_ingestion_config: DataIngestionConfig):
        self.config = data_ingestion_config

    def reduce_mem_usage(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimizes memory types as done in the notebook."""
        for col in df.columns:
            col_type = df[col].dtype
            if str(col_type) == 'category':
                continue
            if col_type != object:
                c_min, c_max = df[col].min(), df[col].max()
                if str(col_type)[:3] == 'int':
                    if c_min > -128 and c_max < 127:
                        df[col] = df[col].astype('int8')
                    elif c_min > -32768 and c_max < 32767:
                        df[col] = df[col].astype('int16')
                else:
                    df[col] = df[col].astype('float32')
            else:
                df[col] = df[col].astype('category')
        return df

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        logging.info("Starting Data Ingestion component")
        try:
            # 1. Read files (In production, replace with MongoDB fetching using self.config.collection_name)
            cal_df = pd.read_csv("Datasets/calendar.csv")
            sales_train = pd.read_csv("Datasets/sales_train_evaluation.csv")
            sell_prices = pd.read_csv("Datasets/sell_prices.csv")
            
            # 2. Downcast and optimize RAM
            sales_train = self.reduce_mem_usage(sales_train)
            sell_prices = self.reduce_mem_usage(sell_prices)
            cal_df = self.reduce_mem_usage(cal_df)
            
            # 3. Melt to long format (taking last 1 year of data: 1577 to 1941)
            id_vars = ['id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id']
            day_cols = [f'd_{i}' for i in range(1577, 1942)]
            
            df_melted = pd.melt(sales_train, id_vars=id_vars, value_vars=day_cols, var_name='d', value_name='sales')
            df_melted['d'] = df_melted['d'].astype('category')
            df_melted['sales'] = df_melted['sales'].astype('int16')
            
            del sales_train
            gc.collect()

            # 4. Merge dataframes
            df_melted = df_melted.merge(cal_df, on='d', how='left')
            df_melted = df_melted.merge(sell_prices, on=['store_id', 'item_id', 'wm_yr_wk'], how='left')
            
            # 5. Split train-test and save to feature store paths
            os.makedirs(self.config.data_ingestion_dir, exist_ok=True)
            
            # Create subfolders for ingested data
            os.makedirs(os.path.dirname(self.config.training_file_path), exist_ok=True)
            os.makedirs(os.path.dirname(self.config.testing_file_path), exist_ok=True)
            
            # Save the full dataset to training_file_path to keep the temporal sequence intact
            # We also save a copy to testing_file_path to satisfy the ingestion artifact requirements
            df_melted.to_csv(self.config.training_file_path, index=False)
            df_melted.to_csv(self.config.testing_file_path, index=False)
            
            logging.info("Data Ingestion completed successfully")
            return DataIngestionArtifact(
                trained_file_path=self.config.training_file_path,
                test_file_path=self.config.testing_file_path
            )
        except Exception as e:
            raise CustomException(e, sys)

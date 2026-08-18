import sys
from logger.logger import logging
from exception.exception import CustomException
from pipeline.training_pipeline import TrainingPipeline
STAGE_NAME = "Full Training Pipeline Execution"
if __name__ == "__main__":
    try:
        logging.info(f">>>>>> Stage {STAGE_NAME} started <<<<<<")
        pipeline = TrainingPipeline()
        pipeline.run_pipeline()
        logging.info(f">>>>>> Stage {STAGE_NAME} completed <<<<<<\n\nx==========x")
    except Exception as e:
        logging.exception(e)
        raise CustomException(e, sys)
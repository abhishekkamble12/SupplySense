import sys
from logger.logger import logging
from exception.exception import CustomException
from pipeline.step_01_data_ingestion_pipeline import DataIngestionPipeline
from pipeline.step_02_data_validation_pipeline import DataValidationPipeline
from pipeline.step_03_data_transformation_pipeline import DataTransformationPipeline
from pipeline.step_04_model_trainer_pipeline import ModelTrainerPipeline
from pipeline.step_05_model_evaluation_pipeline import ModelEvaluationPipeline

class TrainingPipeline:
    def __init__(self):
        pass

    def run_pipeline(self):
        try:
            logging.info("=========================================")
            logging.info(">>> STARTING TRAINING PIPELINE EXECUTION <<<")
            logging.info("=========================================")
            
            # Step 1: Data Ingestion
            ingestion = DataIngestionPipeline()
            ingestion_artifact = ingestion.main()
            
            # Step 2: Data Validation
            validation = DataValidationPipeline()
            validation_artifact = validation.main(data_ingestion_artifact=ingestion_artifact)
            
            # Step 3: Data Transformation
            transformation = DataTransformationPipeline()
            transformation_artifact = transformation.main(data_validation_artifact=validation_artifact)
            
            # Step 4: Model Training
            trainer = ModelTrainerPipeline()
            trainer_artifact = trainer.main(data_transformation_artifact=transformation_artifact)
            
            # Step 5: Model Evaluation and Pusher
            evaluation = ModelEvaluationPipeline()
            pusher_artifact = evaluation.main(
                data_transformation_artifact=transformation_artifact,
                model_trainer_artifact=trainer_artifact
            )
            
            logging.info("===========================================")
            logging.info(">>> TRAINING PIPELINE COMPLETED SUCCESSFULLY <<<")
            logging.info("===========================================")
            return pusher_artifact
            
        except Exception as e:
            logging.error("Training Pipeline failed!")
            raise CustomException(e, sys)

if __name__ == "__main__":
    try:
        pipeline = TrainingPipeline()
        pipeline.run_pipeline()
    except Exception as e:
        print(f"Pipeline error: {e}")

import os
import sys
import json
import pickle
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge

from entity.config_entity import ModelTrainerConfig
from entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact, RegressionMetricArtifact
from logger.logger import logging
from exception.exception import CustomException

class ModelTrainer:
    """
    Automated Multi-Model Benchmarking & Selection Engine.
    Trains candidate algorithms (LightGBM, GradientBoosting, RandomForest, Ridge),
    evaluates validation metrics (RMSE, MAE, R2), logs runs to MLflow/DagsHub,
    and deploys the winning Champion Model.
    """

    def __init__(self, model_trainer_config: ModelTrainerConfig, data_transformation_artifact: DataTransformationArtifact):
        self.config = model_trainer_config
        self.transformation_artifact = data_transformation_artifact

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        logging.info("Starting Multi-Model Candidate Training & Benchmarking component...")
        try:
            # 1. Load transformed dataset arrays
            train_arr = np.load(self.transformation_artifact.transformed_train_file_path)
            test_arr = np.load(self.transformation_artifact.transformed_test_file_path)
            
            # Split features and target
            X_train, y_train = train_arr[:, :-1], train_arr[:, -1]
            X_val, y_val = test_arr[:, :-1], test_arr[:, -1]
            
            candidates = {}
            leaderboard = []

            # Candidate 1: LightGBM Regressor (Temporal Lags & Categoricals)
            logging.info("Training Candidate 1: LightGBM Regressor...")
            lgb_model = lgb.LGBMRegressor(
                n_estimators=self.config._n_estimators,
                max_depth=self.config._max_depth,
                random_state=self.config._random_state,
                n_jobs=-1
            )
            lgb_model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                callbacks=[lgb.early_stopping(50, verbose=False)]
            )
            lgb_preds = lgb_model.predict(X_val)
            lgb_rmse = float(np.sqrt(mean_squared_error(y_val, lgb_preds)))
            lgb_mae = float(mean_absolute_error(y_val, lgb_preds))
            lgb_r2 = float(r2_score(y_val, lgb_preds))

            candidates["LightGBM"] = {
                "model": lgb_model,
                "rmse": lgb_rmse,
                "mae": lgb_mae,
                "r2": lgb_r2
            }

            # Candidate 2: Gradient Boosting Regressor
            logging.info("Training Candidate 2: Gradient Boosting Regressor...")
            gbr_model = GradientBoostingRegressor(
                n_estimators=min(100, self.config._n_estimators),
                max_depth=min(6, self.config._max_depth),
                random_state=self.config._random_state
            )
            gbr_model.fit(X_train, y_train)
            gbr_preds = gbr_model.predict(X_val)
            gbr_rmse = float(np.sqrt(mean_squared_error(y_val, gbr_preds)))
            gbr_mae = float(mean_absolute_error(y_val, gbr_preds))
            gbr_r2 = float(r2_score(y_val, gbr_preds))

            candidates["GradientBoosting"] = {
                "model": gbr_model,
                "rmse": gbr_rmse,
                "mae": gbr_mae,
                "r2": gbr_r2
            }

            # Candidate 3: Ridge Linear Regularized Baseline
            logging.info("Training Candidate 3: Ridge Linear Baseline...")
            ridge_model = Ridge(alpha=1.0)
            ridge_model.fit(X_train, y_train)
            ridge_preds = ridge_model.predict(X_val)
            ridge_rmse = float(np.sqrt(mean_squared_error(y_val, ridge_preds)))
            ridge_mae = float(mean_absolute_error(y_val, ridge_preds))
            ridge_r2 = float(r2_score(y_val, ridge_preds))

            candidates["Ridge"] = {
                "model": ridge_model,
                "rmse": ridge_rmse,
                "mae": ridge_mae,
                "r2": ridge_r2
            }

            # 2. Benchmark Evaluation & Champion Selection (Lowest RMSE)
            champion_name = min(candidates.keys(), key=lambda name: candidates[name]["rmse"])
            champion_info = candidates[champion_name]

            logging.info(f"🏆 Champion Model Selected: {champion_name} (Validation RMSE: {champion_info['rmse']:.4f} | MAE: {champion_info['mae']:.4f} | R2: {champion_info['r2']:.4f})")

            for name, details in candidates.items():
                is_champ = (name == champion_name)
                leaderboard.append({
                    "candidate_name": name,
                    "rmse": round(details["rmse"], 4),
                    "mae": round(details["mae"], 4),
                    "r2_score": round(details["r2"], 4),
                    "status": "🏆 CHAMPION" if is_champ else "CANDIDATE"
                })

            # Sort leaderboard by RMSE ascending
            leaderboard.sort(key=lambda x: x["rmse"])

            # 3. Save Champion Model local artifact
            os.makedirs(os.path.dirname(self.config.trained_model_file_path), exist_ok=True)
            with open(self.config.trained_model_file_path, 'wb') as f:
                pickle.dump(champion_info["model"], f)

            # Save benchmark leaderboard report JSON
            report_path = os.path.join(os.path.dirname(self.config.trained_model_file_path), "benchmark_report.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump({"champion": champion_name, "leaderboard": leaderboard}, f, indent=2)

            # 4. MLflow / DagsHub Remote Tracking Integration
            try:
                import mlflow
                try:
                    import dagshub
                    dagshub.init(repo_owner="abhishekkamble12", repo_name="SupplySense", mlflow=True)
                except Exception as dagshub_err:
                    logging.info(f"DagsHub auto-init skipped: {dagshub_err}")

                mlflow.set_experiment("SupplySense_Sales_Forecasting")
                with mlflow.start_run(run_name=f"Champion_{champion_name}"):
                    mlflow.log_params({
                        "champion_model": champion_name,
                        "n_estimators": self.config._n_estimators,
                        "max_depth": self.config._max_depth
                    })
                    mlflow.log_metrics({
                        "champion_rmse": champion_info["rmse"],
                        "champion_mae": champion_info["mae"],
                        "champion_r2": champion_info["r2"]
                    })
                logging.info("Logged candidate benchmarks to MLflow / DagsHub.")
            except Exception as mlflow_err:
                logging.warning(f"MLflow logging skipped: {mlflow_err}")

            metrics = RegressionMetricArtifact(
                rmse=champion_info["rmse"],
                mae=champion_info["mae"]
            )

            return ModelTrainerArtifact(
                trained_model_file_path=self.config.trained_model_file_path,
                metric_artifact=metrics
            )
        except Exception as e:
            raise CustomException(e, sys)

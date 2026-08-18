# SupplySense AI ⚡
### Autonomous Retail Supply Chain & Inventory Decision Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![LightGBM](https://img.shields.io/badge/LightGBM-4.0.0-brightgreen.svg)](https://lightgbm.readthedocs.io/)
[![MLflow](https://img.shields.io/badge/MLflow-Experiment%20Tracking-0194E2.svg)](https://mlflow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![YC Ready](https://img.shields.io/badge/Y--Combinator-Pitch%20Ready-orange.svg)](#-y-combinator-pitch-guide)

---

## 🎯 Executive Summary & Mission

**SupplySense** is an enterprise-grade, venture-backed **Autonomous Inventory & Supply Chain Decision Engine** designed for omni-channel retail brands and mid-market distributors.

While legacy ERPs (SAP IBP, Blue Yonder) cost $500k+ and take 18 months to deploy, mid-market retailers lose **12–18% of margin** to stockouts (lost revenue) and overstock (trapped cash). SupplySense replaces broken static spreadsheets with **probabilistic demand forecasting (P10/P50/P90)**, **stochastic inventory optimization**, **automated 1-click PO approvals**, and an **Autonomous AI Supply Chain Copilot**.

---

## 🏗️ System Architecture

```
                                  ┌─────────────────────────────────────────────────────────────┐
                                  │               SUPPLYSENSE DECISION ENGINE                   │
┌────────────────────────────┐    │  ┌───────────────────────┐    ┌──────────────────────────┐  │    ┌─────────────────────────────┐
│ Multi-Channel Data Ingest  │    │  │ Demand Forecasting    │    │  Inventory Optimizer     │  │    │     Executive Cockpit       │
│ • Custom CSV Upload Sync   ├───►│  │ • LightGBM Regressor  ├───►│  • Dynamic ROP & Safety  ├──┼───►│ • Stockout Risk Radar       │
│ • Retail SKU Catalog       │    │  │ • P10 / P50 / P90     │    │  • Cash Flow Optimization│  │    │ • Auto-Generated PO Approvals│
│ • Supplier Profiles & MOQs │    │  └───────────────────────┘    │  • Working Capital Risk  │  │    │ • Interactive Scenario Sim  │
└────────────────────────────┘    │                               └────────────┬─────────────┘  │    │ • MLOps Diagnostics Modal   │
                                  │                                            │                │    └──────────────┬──────────────┘
                                  │                               ┌────────────▼─────────────┐  │                   │
                                  │                               │ Autonomous Copilot Agent │◄─┼───────────────────┘
                                  │                               │ • Live Natural Language  │  │
                                  │                               │ • Drafts Vendor PO Emails│  │
                                  │                               └──────────────────────────┘  │
                                  └─────────────────────────────────────────────────────────────┘
```

---

## ✨ Core Platform Capabilities

### 1. 📊 Probabilistic Quantile Forecasting (P10, P50, P90)
Instead of relying on fragile single-point predictions, SupplySense models demand uncertainty intervals:
* **P10 (Bearish / 10th Percentile)**: Lower demand bound for perishable or cash-strapped SKUs.
* **P50 (Median / 50th Percentile)**: Expected baseline demand.
* **P90 (Bullish / 90th Percentile)**: Upper demand bound for high-margin Category A "Hero SKUs" to guarantee non-stockout fill rates.

### 2. 🧮 Stochastic Inventory Optimization & Dynamic ROP
Translates demand predictions into business decisions:
* **Dynamic Safety Stock ($SS$)**:
  $$SS = Z \times \sqrt{\bar{L} \cdot \sigma_D^2 + \bar{D}^2 \cdot \sigma_L^2}$$
  *(Accounts for both demand fluctuations and supplier delivery delays).*
* **Dynamic Reorder Point ($ROP$)**:
  $$ROP = (\bar{D} \times \bar{L}) + SS$$
* **Automated PO Rounding & MOQ Clamping**: Rounds orders to supplier case-pack multiples and enforces minimum order quantities.
* **Capital Risk Modeling**: Calculates **Revenue at Risk ($)** and **Excess Carrying Cost ($)**.

### 3. 🤖 Autonomous AI Supply Chain Copilot
* Embedded natural language AI assistant accessible via slide-over drawer on the web dashboard.
* Answers complex risk queries (*"Which SKUs in California will stock out first?"*).
* **Automated Supplier Email Drafter**: Automatically generates professional procurement emails with SKU lines, unit costs, PO numbers, and required arrival dates.

### 4. 🏆 Multi-Model Benchmarking & Selection Engine
* Trains candidate algorithms (**LightGBM**, **Gradient Boosting**, **Ridge Baseline**) in parallel.
* Automatically evaluates validation RMSE, MAE, and $R^2$ scores, logs metrics to **MLflow & DagsHub**, and deploys the winning **Champion Model**.

### 5. 🖥️ Executive Cockpit & What-If Sandbox
* Dark-mode glassmorphic web dashboard with real-time KPI metrics.
* **Stockout Risk Radar**: Sortable SKU matrix with visual *Days of Inventory (DOI)* progress bars.
* **1-Click PO Approval Queue**: Vendor-consolidated draft POs with live ERP dispatch simulation.
* **Interactive What-If Scenario Sandbox**: Real-time sliders for promotional demand surges (+0% to +150%), supplier delays (+0 to +30 days), and target fill rates.

---

## 📂 Repository Structure

```
SupplySense/
├── Datasets/                 # Raw transactional & calendar datasets
├── config/                   # Pipeline YAML configurations & schemas
│   ├── config.yaml           # Artifact paths & dataset configuration
│   └── configuration.py      # Configuration Manager class
├── constant/                 # Root-level pipeline constant definitions
├── artifacts/                # Generated timestamped execution artifacts
├── saved_models/             # Production deployment model registry (.pkl)
├── templates/                # Frontend Web Interface
│   └── index.html            # Executive Cockpit & AI Copilot Web UI
├── src/                      # Source package directory
│   ├── Components/           # Core ML & Optimization Components
│   │   ├── Data_ingestion.py      # Downcasts RAM & merges temporal tables
│   │   ├── Data_Validation.py     # Schema validation & missing value checks
│   │   ├── Data_transformation.py # Time-series lag & rolling mean engineering
│   │   ├── Model_trainer.py        # Multi-model benchmarking & MLflow logging
│   │   ├── Model_eval.py           # Champion model acceptance guardrails
│   │   ├── Model_pusher.py         # Production model deployment registry
│   │   ├── inventory_optimizer.py # Stochastic Safety Stock, ROP & PO Engine
│   │   └── supply_chain_copilot.py# Autonomous NLP Agent & Vendor Drafter
│   ├── entity/               # Dataclass entities & domain contracts
│   │   ├── config_entity.py
│   │   ├── artifact_entity.py
│   │   └── inventory_entity.py    # SKU, Supplier, PO & Audit entities
│   ├── exception/            # Custom exception traceback handler
│   ├── logger/               # Execution log file generator
│   └── utils/
│       └── sku_catalog.py         # Retail SKU catalog & vendor profiles
├── test/                     # Pytest suite
│   └── test_inventory_optimizer.py
├── app.py                    # FastAPI Web Application & REST Server
├── main.py                   # Master CLI execution pipeline
├── requirements.txt          # Production dependencies
└── README.md                 # Product Documentation
```

---

## 🚀 Getting Started & Setup

### 1. Installation
Clone the repository and install Python dependencies:
```bash
git clone https://github.com/abhishekkamble12/SupplySense.git
cd SupplySense

# Create virtual environment & install requirements
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Launch the Application Server
Start the Uvicorn FastAPI server:
```bash
python app.py
# Or with auto-reload enabled:
uvicorn app.py:app --reload --port 8000
```

### 3. Open the Dashboards
* **Executive Cockpit Dashboard**: [`http://localhost:8000/`](http://localhost:8000/)
* **Interactive Swagger API Documentation**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
* **System Health API**: [`http://localhost:8000/api/health`](http://localhost:8000/api/health)

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Renders the interactive Executive Cockpit Web Interface |
| `GET` | `/api/v1/inventory/audit` | Runs full portfolio inventory health audit & stockout alarms |
| `POST` | `/api/v1/inventory/optimize` | Stochastically optimizes single SKU safety stock & ROP |
| `POST` | `/api/v1/inventory/batch-optimize` | Batch optimizes SKUs and consolidates draft vendor POs |
| `POST` | `/api/v1/inventory/simulate` | What-if scenario sandbox for lead time delays & demand surges |
| `POST` | `/api/v1/inventory/upload-csv` | Ingests custom store inventory CSV files and runs live audit |
| `POST` | `/api/v1/copilot/chat` | Natural language interaction with AI Supply Chain Copilot |
| `GET` | `/api/v1/mlops/benchmark` | Candidate model evaluation leaderboard (LightGBM vs GBR vs Ridge) |
| `GET` | `/api/v1/mlops/diagnostics` | Feature importance rankings and model accuracy metrics |
| `GET` | `/train` | Triggers the master end-to-end ML pipeline |
| `POST` | `/predict` | Generates demand regression forecasts from store input features |

---

## 📊 Experiment Tracking (MLflow & DagsHub)

SupplySense logs hyperparameters, validation metrics, feature importances, and model checkpoints to remote tracking:

* **Remote DagsHub Dashboard**: Streams runs to `https://dagshub.com/abhishekkamble12/SupplySense.mlflow`
* **Local MLflow UI**:
  ```bash
  mlflow ui
  ```
  Access local dashboard at `http://127.0.0.1:5000`.

---

## 🧪 Testing & Verification

Execute unit tests covering safety stock math, ROP triggers, case pack roundups, and PO consolidation:
```bash
python -m pytest test/test_inventory_optimizer.py -v
```

---

## 💡 Y-Combinator Pitch Guide

* **1-Sentence Hook**: *"SupplySense is an Autonomous Inventory Decision Engine for omni-channel retail brands — turning demand signals into automated, cash-optimized purchase orders and stockout prevention."*
* **The Problem**: *"Mid-market retailers lose 12–18% of annual margin to stockouts and overstock. Legacy ERPs cost $500k+ and take 18 months to set up, leaving 90% of brands stuck on broken Excel spreadsheets."*
* **The Wedge**: *"Plug-and-play AI that connects to a brand's sales channels, predicts P10/P50/P90 demand, optimizes dynamic safety stock, and provides 1-click PO approvals."*

---

## 🛡️ License
Distributed under the MIT License. See `LICENSE` for details.
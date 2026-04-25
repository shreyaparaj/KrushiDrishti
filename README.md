# KrushiDrishti

KrushiDrishti is a Flask-based smart agriculture web app focused on Maharashtra crop planning.  
It combines fertilizer recommendation logic, weather-aware yield estimation, and crop price risk intelligence.

## Features

- Fertilizer recommendations by crop and soil type
- Cost, soil-impact, and health-impact comparison
- Expected yield prediction using a trained ML model (`yield_model.pkl`)
- Crop market price and overproduction risk prediction
- Regional crop intelligence dashboard
- District map analytics endpoints
- Feedback form with SQLite storage
- Multi-language support through `translations.py`

## Tech Stack

- Python
- Flask
- SQLite
- scikit-learn
- pandas / numpy
- HTML, CSS, JavaScript (Jinja templates)

## Project Structure

```text
KrushiDrishti/
|- app.py
|- config.py
|- requirements.txt
|- routes/
|  `- main_routes.py
|- models/
|  |- fertilizer_model.py
|  |- train_price_model.py
|  |- train_yield_model.py
|  |- price_model.pkl
|  |- risk_model.pkl
|  `- yield_model.pkl
|- ml/
|  |- price_risk_model.py
|  `- predict_price_risk.py
|- database/
|  `- schema.sql
|- data/
|  |- crop_price_dataset.csv
|  `- maharashtra_weather.csv
|- scripts/
|  `- import_agmarknet_prices.py
|- templates/
`- static/
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the App

```bash
python app.py
```

Open: `http://127.0.0.1:5000/`

## Database

- Database file path is configured in `config.py` as `database/safegrow.db`.
- On first run, the app auto-creates the DB and initializes tables using `database/schema.sql`.

## Train / Refresh ML Models

Train price + risk models:

```bash
python models/train_price_model.py
```

Train yield model:

```bash
python models/train_yield_model.py
```

Alternative launcher for price/risk training:

```bash
python ml/price_risk_model.py
```

## Import Agmarknet Price History

Normalize a raw Agmarknet CSV export into project format:

```bash
python scripts/import_agmarknet_prices.py <input_csv_path> --output data/agmarknet_price_history.csv
```

If `data/agmarknet_price_history.csv` exists, price model training prefers it over `data/crop_price_dataset.csv`.

## Core Routes

- `/` home page
- `/analyzer` fertilizer analyzer
- `/recommend` recommendation result (POST)
- `/price-risk` price-risk page
- `/predict-risk` risk prediction result (POST)
- `/map` crop planning map
- `/api/region_data/<region_name>` region-wise crop distribution API
- `/api/all_regions_data` all-region heatmap API
- `/feedback` feedback form

## Notes

- Weather values are loaded from `data/maharashtra_weather.csv` via `utils/weather.py`.
- Trained model metadata is stored in `models/price_model_meta.pkl`.
- Current sample data and region list are Maharashtra-focused.

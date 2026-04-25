import os
from datetime import UTC, datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DEFAULT_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "crop_price_dataset.csv")
AGMARKNET_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "agmarknet_price_history.csv")
PRICE_MODEL_PATH = os.path.join(BASE_DIR, "price_model.pkl")
RISK_MODEL_PATH = os.path.join(BASE_DIR, "risk_model.pkl")
PRICE_META_PATH = os.path.join(BASE_DIR, "price_model_meta.pkl")

SEASON_MAP = {
    12: "Rabi",
    1: "Rabi",
    2: "Rabi",
    3: "Summer",
    4: "Summer",
    5: "Summer",
    6: "Kharif",
    7: "Kharif",
    8: "Kharif",
    9: "Kharif",
    10: "Post-Monsoon",
    11: "Post-Monsoon",
}


def _pick_first_existing_column(df, candidates, default=None):
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    return default


def _normalize_source_dataframe(df):
    region_col = _pick_first_existing_column(df, ["Region", "region", "District", "district"])
    crop_col = _pick_first_existing_column(df, ["Crop", "crop", "Commodity", "commodity"])
    date_col = _pick_first_existing_column(
        df,
        ["Date", "date", "Arrival_Date", "arrival_date", "Reported_Date", "reported_date"],
    )
    price_col = _pick_first_existing_column(
        df,
        ["Price", "price", "Modal_Price", "modal_price", "Modal Price", "Last_Year_Price"],
    )
    cultivation_col = _pick_first_existing_column(
        df,
        ["Cultivation_Percentage", "cultivation_percentage", "Area_Percentage"],
    )
    rainfall_col = _pick_first_existing_column(df, ["Rainfall", "rainfall"])
    temperature_col = _pick_first_existing_column(df, ["Temperature", "temperature"])
    risk_col = _pick_first_existing_column(df, ["Price_Risk", "price_risk", "Risk", "Market_Risk"])
    min_price_col = _pick_first_existing_column(df, ["Min_Price", "min_price", "Min Price"])
    max_price_col = _pick_first_existing_column(df, ["Max_Price", "max_price", "Max Price"])

    if not region_col or not crop_col or not price_col:
        raise ValueError("Dataset must include region, crop, and price columns.")

    normalized = pd.DataFrame(
        {
            "region": df[region_col],
            "crop": df[crop_col],
            "date": df[date_col] if date_col else pd.NaT,
            "price": pd.to_numeric(df[price_col], errors="coerce"),
            "min_price": pd.to_numeric(df[min_price_col], errors="coerce") if min_price_col else np.nan,
            "max_price": pd.to_numeric(df[max_price_col], errors="coerce") if max_price_col else np.nan,
            "cultivation_percentage": pd.to_numeric(df[cultivation_col], errors="coerce")
            if cultivation_col
            else np.nan,
            "rainfall": pd.to_numeric(df[rainfall_col], errors="coerce") if rainfall_col else np.nan,
            "temperature": pd.to_numeric(df[temperature_col], errors="coerce")
            if temperature_col
            else np.nan,
            "price_risk": df[risk_col] if risk_col else None,
        }
    )
    return normalized


def load_historical_price_data():
    dataset_path = AGMARKNET_DATASET_PATH if os.path.exists(AGMARKNET_DATASET_PATH) else DEFAULT_DATASET_PATH
    df = pd.read_csv(dataset_path)
    df = _normalize_source_dataframe(df)

    df["region"] = df["region"].astype(str).str.strip()
    df["crop"] = df["crop"].astype(str).str.strip()
    df = df.dropna(subset=["region", "crop", "price"]).copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    if df["date"].isna().all():
        # Fallback for the sample dataset bundled with the repo, which has no dates.
        start_date = pd.Timestamp(datetime.today().year - 2, 1, 1)
        fallback_dates = pd.date_range(start=start_date, periods=len(df), freq="MS")
        df["date"] = fallback_dates
    else:
        df["date"] = df["date"].ffill().bfill()

    df = df.sort_values(["region", "crop", "date"]).reset_index(drop=True)
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter
    df["season"] = df["month"].map(SEASON_MAP).fillna("Unknown")

    df["previous_price"] = df.groupby(["region", "crop"])["price"].shift(1)
    df["previous_price"] = df["previous_price"].fillna(
        df.groupby(["region", "crop"])["price"].transform("median")
    )
    df["previous_price"] = df["previous_price"].fillna(df["price"])

    rolling_price_mean = (
        df.groupby(["region", "crop"])["price"]
        .transform(lambda series: series.shift(1).rolling(window=3, min_periods=1).mean())
    )
    rolling_price_std = (
        df.groupby(["region", "crop"])["price"]
        .transform(lambda series: series.shift(1).rolling(window=3, min_periods=2).std())
    )
    df["price_trend_3"] = rolling_price_mean.fillna(df["previous_price"])
    df["price_volatility_3"] = rolling_price_std.fillna(0.0)
    safe_previous_price = df["previous_price"].replace(0, np.nan)
    df["price_momentum"] = ((df["price"] - df["previous_price"]) / safe_previous_price).replace(
        [np.inf, -np.inf],
        np.nan,
    )
    df["price_momentum"] = df["price_momentum"].fillna(0.0)
    df["arrival_gap_days"] = (
        df.groupby(["region", "crop"])["date"].diff().dt.days.fillna(30).clip(lower=1, upper=120)
    )

    df["min_price"] = df["min_price"].fillna(df["price"])
    df["max_price"] = df["max_price"].fillna(df["price"])
    df["price_spread"] = (df["max_price"] - df["min_price"]).clip(lower=0)

    for column in ["cultivation_percentage", "rainfall", "temperature"]:
        group_values = df.groupby(["region", "crop"])[column].transform("median")
        df[column] = df[column].fillna(group_values)
        df[column] = df[column].fillna(df[column].median())

    if "price_risk" in df.columns and df["price_risk"].notna().any():
        normalized_risk = df["price_risk"].astype(str).str.strip().str.lower()
        df["is_saturated"] = normalized_risk.eq("high").astype(int)
    else:
        crop_medians = df.groupby("crop")["price"].transform("median")
        saturation_signal = (
            (df["cultivation_percentage"] >= 60)
            | (df["price"] < crop_medians * 0.85)
        )
        df["is_saturated"] = saturation_signal.astype(int)

    return df, dataset_path


def build_feature_metadata(df):
    feature_columns = [
        "region",
        "crop",
        "month",
        "year",
        "quarter",
        "season",
        "cultivation_percentage",
        "rainfall",
        "temperature",
        "previous_price",
        "price_trend_3",
        "price_volatility_3",
        "price_momentum",
        "arrival_gap_days",
        "price_spread",
    ]

    group_defaults = {}
    for (region, crop), group in df.groupby(["region", "crop"]):
        group_defaults[f"{region}::{crop}"] = {
            "cultivation_percentage": float(group["cultivation_percentage"].median()),
            "rainfall": float(group["rainfall"].median()),
            "temperature": float(group["temperature"].median()),
            "previous_price": float(group["price"].iloc[-1]),
            "price_trend_3": float(group["price_trend_3"].iloc[-1]),
            "price_volatility_3": float(group["price_volatility_3"].median()),
            "price_momentum": float(group["price_momentum"].iloc[-1]),
            "arrival_gap_days": float(group["arrival_gap_days"].median()),
            "price_spread": float(group["price_spread"].median()),
        }

    crop_defaults = {}
    for crop, group in df.groupby("crop"):
        crop_defaults[crop] = {
            "cultivation_percentage": float(group["cultivation_percentage"].median()),
            "rainfall": float(group["rainfall"].median()),
            "temperature": float(group["temperature"].median()),
            "previous_price": float(group["price"].median()),
            "price_trend_3": float(group["price_trend_3"].median()),
            "price_volatility_3": float(group["price_volatility_3"].median()),
            "price_momentum": float(group["price_momentum"].median()),
            "arrival_gap_days": float(group["arrival_gap_days"].median()),
            "price_spread": float(group["price_spread"].median()),
        }

    overall_defaults = {
        "cultivation_percentage": float(df["cultivation_percentage"].median()),
        "rainfall": float(df["rainfall"].median()),
        "temperature": float(df["temperature"].median()),
        "previous_price": float(df["price"].median()),
        "price_trend_3": float(df["price_trend_3"].median()),
        "price_volatility_3": float(df["price_volatility_3"].median()),
        "price_momentum": float(df["price_momentum"].median()),
        "arrival_gap_days": float(df["arrival_gap_days"].median()),
        "price_spread": float(df["price_spread"].median()),
    }

    return {
        "feature_columns": feature_columns,
        "group_defaults": group_defaults,
        "crop_defaults": crop_defaults,
        "overall_defaults": overall_defaults,
        "row_count": int(len(df)),
        "date_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "trained_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source_dataset": os.path.basename(AGMARKNET_DATASET_PATH)
        if os.path.exists(AGMARKNET_DATASET_PATH)
        else os.path.basename(DEFAULT_DATASET_PATH),
    }


def create_preprocessor():
    categorical_features = ["region", "crop", "season"]
    numeric_features = [
        "month",
        "year",
        "quarter",
        "cultivation_percentage",
        "rainfall",
        "temperature",
        "previous_price",
        "price_trend_3",
        "price_volatility_3",
        "price_momentum",
        "arrival_gap_days",
        "price_spread",
    ]

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )


def chronological_train_test_split(features, target_price, target_risk, dates, test_ratio=0.2):
    order = np.argsort(dates.to_numpy())
    cutoff = max(1, int(len(features) * (1 - test_ratio)))
    cutoff = min(cutoff, len(features) - 1)

    train_idx = order[:cutoff]
    test_idx = order[cutoff:]
    return (
        features.iloc[train_idx],
        features.iloc[test_idx],
        target_price.iloc[train_idx],
        target_price.iloc[test_idx],
        target_risk.iloc[train_idx],
        target_risk.iloc[test_idx],
    )


def train_price_models():
    print("Loading historical crop price data...")
    df, dataset_path = load_historical_price_data()
    metadata = build_feature_metadata(df)
    print(f"Using dataset: {dataset_path}")

    X = df[metadata["feature_columns"]]
    y_price = df["price"]
    y_risk = df["is_saturated"]

    X_train, X_test, y_price_train, y_price_test, y_risk_train, y_risk_test = chronological_train_test_split(
        X,
        y_price,
        y_risk,
        df["date"],
    )

    preprocessor = create_preprocessor()

    price_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                MLPRegressor(
                    hidden_layer_sizes=(64, 32),
                    activation="relu",
                    learning_rate_init=0.001,
                    max_iter=1200,
                    early_stopping=True,
                    random_state=42,
                ),
            ),
        ]
    )

    risk_pipeline = Pipeline(
        steps=[
            ("preprocessor", create_preprocessor()),
            (
                "classifier",
                MLPClassifier(
                    hidden_layer_sizes=(32, 16),
                    activation="relu",
                    learning_rate_init=0.001,
                    max_iter=1200,
                    early_stopping=True,
                    random_state=42,
                ),
            ),
        ]
    )

    print("Training feedforward ANN for crop price regression...")
    price_pipeline.fit(X_train, y_price_train)
    print("Training feedforward ANN for market saturation classification...")
    risk_pipeline.fit(X_train, y_risk_train)

    price_predictions = price_pipeline.predict(X_test)
    risk_predictions = risk_pipeline.predict(X_test)

    metrics = {
        "price_mae": float(mean_absolute_error(y_price_test, price_predictions)),
        "price_r2": float(r2_score(y_price_test, price_predictions)),
        "risk_accuracy": float(accuracy_score(y_risk_test, risk_predictions)),
    }
    metadata["metrics"] = metrics
    metadata["split"] = {
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "strategy": "chronological",
    }

    os.makedirs(BASE_DIR, exist_ok=True)
    joblib.dump(price_pipeline, PRICE_MODEL_PATH)
    joblib.dump(risk_pipeline, RISK_MODEL_PATH)
    joblib.dump(metadata, PRICE_META_PATH)

    print("Models saved successfully.")
    print(f"Price MAE: {metrics['price_mae']:.2f}")
    print(f"Price R^2: {metrics['price_r2']:.3f}")
    print(f"Risk accuracy: {metrics['risk_accuracy']:.3f}")


if __name__ == "__main__":
    train_price_models()

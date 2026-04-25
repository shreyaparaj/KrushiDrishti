import pandas as pd

from models.fertilizer_model import build_price_feature_row, get_price_model, get_risk_model

def predict_price_risk(region, crop, cultivation_percentage, rainfall, temperature, last_price):
    price_model = get_price_model()
    risk_model = get_risk_model()

    if price_model is None or risk_model is None:
        raise RuntimeError("Price predictor artifacts are missing. Run models/train_price_model.py first.")

    feature_row = build_price_feature_row(region, crop, cultivation_percentage)
    feature_row["rainfall"] = float(rainfall)
    feature_row["temperature"] = float(temperature)
    feature_row["previous_price"] = float(last_price)
    feature_row["price_trend_3"] = float(last_price)

    input_data = pd.DataFrame([feature_row])
    saturated_prediction = risk_model.predict(input_data)[0]
    predicted_price = float(price_model.predict(input_data)[0])

    return {
        "risk_label": "High" if int(saturated_prediction) == 1 else "Low",
        "is_saturated": bool(int(saturated_prediction) == 1),
        "predicted_price": predicted_price,
    }

# Simple test if run directly
if __name__ == "__main__":
    result = predict_price_risk("Pune", "Tomato", 60, 800, 30, 20)
    print(f"Test Prediction for Pune Tomato: {result}")

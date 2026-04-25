import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import os

def generate_synthetic_data(num_samples=2000):
    np.random.seed(42)
    
    # Base characteristics
    data = []
    
    for _ in range(num_samples):
        # Let's generate random combinations of valid IDs from DB
        # Soil IDs typically 1-4
        soil_id = np.random.randint(1, 5)
        # Crop IDs typically 1-12
        crop_id = np.random.randint(1, 13)
        # Fertilizer IDs typically 1-6
        fertilizer_id = np.random.randint(1, 7)
        
        # Environmental conditions
        # Temperature typically 15 to 45 °C
        temp = np.random.uniform(15.0, 45.0)
        # Rainfall typically 50 to 300 mm
        rainfall = np.random.uniform(50.0, 300.0)
        
        # Base yield depending mostly on crop type (Tons per Hectare)
        base_yield = np.random.uniform(1.0, 5.0)
        if crop_id in [10]: # Banana
            base_yield += 30.0
        elif crop_id in [5]: # Sugarcane
            base_yield += 70.0
        
        # Environmental multipliers
        # Optimal temps: 20-30
        temp_mult = 1.0 - (abs(25 - temp) / 40.0) 
        
        # Optimal rainfall: 100-200
        rain_mult = 1.0 - (abs(150 - rainfall) / 300.0)
        
        # Fertilizer modifier (simple: Urea/DAP gives high boost, organic gives moderate but stable)
        fert_mult = 1.0
        if fertilizer_id in [1, 2]: # Chemical
            fert_mult = 1.3
        elif fertilizer_id in [4, 5]: # Organic/Bio
            fert_mult = 1.15
        
        # Final expected yield in Tons/Hectare + noise
        noise = np.random.normal(0, 0.5)
        expected_yield = max(0.5, (base_yield * temp_mult * rain_mult * fert_mult) + noise)
        
        data.append({
            'soil_id': soil_id,
            'crop_id': crop_id,
            'temperature': temp,
            'rainfall': rainfall,
            'fertilizer_id': fertilizer_id,
            'expected_yield': expected_yield
        })
        
    return pd.DataFrame(data)

def train_and_save_model():
    print("Generating synthetic data...")
    df = generate_synthetic_data(5000)
    
    X = df[['soil_id', 'crop_id', 'temperature', 'rainfall', 'fertilizer_id']]
    y = df['expected_yield']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    print(f"Model MSE: {mse:.4f}")
    
    # Save the model
    os.makedirs('models', exist_ok=True)
    model_path = os.path.join('models', 'yield_model.pkl')
    joblib.dump(model, model_path)
    print(f"Model successfully saved to {model_path}")

if __name__ == '__main__':
    train_and_save_model()

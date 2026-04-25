from flask import current_app
from translations import translations
import joblib
import os
from datetime import datetime

# Global variable to cache the loaded model
_YIELD_MODEL = None
_PRICE_MODEL = None
_RISK_MODEL = None
_PRICE_META = None

def get_yield_model():
    global _YIELD_MODEL
    if _YIELD_MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), 'yield_model.pkl')
        if os.path.exists(model_path):
            try:
                _YIELD_MODEL = joblib.load(model_path)
            except Exception as e:
                print(f"Error loading yield model: {e}")
    return _YIELD_MODEL

def get_price_model():
    global _PRICE_MODEL
    if _PRICE_MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), 'price_model.pkl')
        if os.path.exists(model_path):
            try:
                _PRICE_MODEL = joblib.load(model_path)
            except Exception as e:
                print(f"Error loading price model: {e}")
    return _PRICE_MODEL

def get_risk_model():
    global _RISK_MODEL
    if _RISK_MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), 'risk_model.pkl')
        if os.path.exists(model_path):
            try:
                _RISK_MODEL = joblib.load(model_path)
            except Exception as e:
                print(f"Error loading risk model: {e}")
    return _RISK_MODEL

def get_price_model_meta():
    global _PRICE_META
    if _PRICE_META is None:
        meta_path = os.path.join(os.path.dirname(__file__), 'price_model_meta.pkl')
        if os.path.exists(meta_path):
            try:
                _PRICE_META = joblib.load(meta_path)
            except Exception as e:
                print(f"Error loading price model metadata: {e}")
                _PRICE_META = {}
        else:
            _PRICE_META = {}
    return _PRICE_META

def _season_for_month(month):
    if month in (12, 1, 2):
        return "Rabi"
    if month in (3, 4, 5):
        return "Summer"
    if month in (6, 7, 8, 9):
        return "Kharif"
    return "Post-Monsoon"

def build_price_feature_row(region, crop_name, cultivation_percentage=None, forecast_date=None):
    metadata = get_price_model_meta() or {}
    group_defaults = metadata.get("group_defaults", {})
    crop_defaults = metadata.get("crop_defaults", {})
    overall_defaults = metadata.get("overall_defaults", {})

    feature_defaults = overall_defaults.copy()
    feature_defaults.update(crop_defaults.get(crop_name, {}))
    feature_defaults.update(group_defaults.get(f"{region}::{crop_name}", {}))

    if cultivation_percentage is not None:
        feature_defaults["cultivation_percentage"] = float(cultivation_percentage)

    forecast_date = forecast_date or datetime.today()
    month = int(forecast_date.month)
    year = int(forecast_date.year)

    return {
        "region": region,
        "crop": crop_name,
        "month": month,
        "year": year,
        "quarter": ((month - 1) // 3) + 1,
        "season": _season_for_month(month),
        "cultivation_percentage": float(feature_defaults.get("cultivation_percentage", 0.0)),
        "rainfall": float(feature_defaults.get("rainfall", 0.0)),
        "temperature": float(feature_defaults.get("temperature", 0.0)),
        "previous_price": float(feature_defaults.get("previous_price", 0.0)),
        "price_trend_3": float(feature_defaults.get("price_trend_3", feature_defaults.get("previous_price", 0.0))),
        "price_volatility_3": float(feature_defaults.get("price_volatility_3", 0.0)),
        "price_momentum": float(feature_defaults.get("price_momentum", 0.0)),
        "arrival_gap_days": float(feature_defaults.get("arrival_gap_days", 30.0)),
        "price_spread": float(feature_defaults.get("price_spread", 0.0)),
    }

def get_price_range_for_crop(region, crop_name):
    """
    Get the price range for a crop in a specific region.
    Returns price category (Low/Stable/High) based on average price.
    Only one category is returned based on the average price ranges:
    - Low Market Prize: 5-40 (Red)
    - Stable Market Prize: 40-100 (Blue)
    - High Market Prize: 100-200+ (Green)
    
    Ensures at least ₹10 gap in the price range display.
    """
    import pandas as pd
    
    try:
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'data', 'crop_price_dataset.csv'))
        
        # Filter by region and crop
        subset = df[(df['Region'] == region) & (df['Crop'] == crop_name)]
        
        if subset.empty:
            # Try just by crop if region not found
            subset = df[df['Crop'] == crop_name]
        
        if not subset.empty:
            min_price = subset['Last_Year_Price'].min()
            max_price = subset['Last_Year_Price'].max()
            avg_price = subset['Last_Year_Price'].mean()
            
            # Ensure at least ₹10 gap
            if (max_price - min_price) < 10:
                max_price = min_price + 10
            
            # Determine category based on average price
            if 5 <= avg_price < 40:
                category = "Low Market Prize"
                color = "#d32f2f"  # Red
                bg_color = "#ffcdd2"
                border_color = "#ef5350"
                text_color = "#c62828"
            elif 40 <= avg_price < 100:
                category = "Stable Market Prize"
                color = "#1976d2"  # Blue
                bg_color = "#bbdefb"
                border_color = "#42a5f5"
                text_color = "#1565c0"
            elif avg_price >= 100:
                category = "High Market Prize"
                color = "#388e3c"  # Green
                bg_color = "#c8e6c9"
                border_color = "#66bb6a"
                text_color = "#2e7d32"
            else:
                category = "Market Prize"
                color = "#666666"
                bg_color = "#eeeeee"
                border_color = "#999999"
                text_color = "#333333"
            
            return {
                'category': category,
                'average_price': int(avg_price),
                'min_price': int(min_price),
                'max_price': int(max_price),
                'price_range_str': f"₹{int(min_price)}-₹{int(max_price)}",
                'color': color,
                'bg_color': bg_color,
                'border_color': border_color,
                'text_color': text_color
            }
    except Exception as e:
        print(f"Error getting price range: {e}")
    
    # Default return if no data found
    return {
        'category': 'Market Prize',
        'average_price': 0,
        'min_price': 0,
        'max_price': 0,
        'price_range_str': 'Not available',
        'color': '#666666',
        'bg_color': '#eeeeee',
        'border_color': '#999999',
        'text_color': '#333333'
    }

def get_recommendation(crop_id, soil_id, current_fertilizer_id, temperature, rainfall, lang='en'):
    db = current_app.get_db()
    t = translations.get(lang, translations['en'])

    # --------------------------------------------------
    # 1. Fetch Recommended Fertilizer
    # --------------------------------------------------
    recommendation = db.execute("""
        SELECT r.recommended_quantity,
               r.notes,
               f.id,
               f.name,
               f.type,
               f.cost_per_kg,
               f.soil_impact,
               f.health_impact,
               f.yield_effect
        FROM recommendations r
        JOIN fertilizers f ON r.fertilizer_id = f.id
        WHERE r.crop_id = ? AND r.soil_id = ?
    """, (crop_id, soil_id)).fetchone()

    if recommendation is None:
        # Fallback 1: Try same crop, any soil
        recommendation = db.execute("""
            SELECT r.recommended_quantity,
                   r.notes,
                   f.id,
                   f.name,
                   f.type,
                   f.cost_per_kg,
                   f.soil_impact,
                   f.health_impact,
                   f.yield_effect
            FROM recommendations r
            JOIN fertilizers f ON r.fertilizer_id = f.id
            WHERE r.crop_id = ?
            LIMIT 1
        """, (crop_id,)).fetchone()

    if recommendation is None:
        # Fallback 2: Try any crop, same soil
        recommendation = db.execute("""
            SELECT r.recommended_quantity,
                   r.notes,
                   f.id,
                   f.name,
                   f.type,
                   f.cost_per_kg,
                   f.soil_impact,
                   f.health_impact,
                   f.yield_effect
            FROM recommendations r
            JOIN fertilizers f ON r.fertilizer_id = f.id
            WHERE r.soil_id = ?
            LIMIT 1
        """, (soil_id,)).fetchone()

    if recommendation is None:
        # Fallback 3: Default to best organic fertilizer (Vermicompost)
        recommendation = db.execute("""
            SELECT '150 kg/acre' as recommended_quantity,
                   'General recommendation for sustainable farming.' as notes,
                   f.id,
                   f.name,
                   f.type,
                   f.cost_per_kg,
                   f.soil_impact,
                   f.health_impact,
                   f.yield_effect
            FROM fertilizers f
            WHERE f.name = 'Vermicompost'
        """).fetchone()

    if recommendation is None:
        return {
            "error": t.get('res_no_rec', "No recommendation available for the selected crop and soil type.")
        }

    # --------------------------------------------------
    # 2. Fetch Current Fertilizer Details
    # --------------------------------------------------
    current_fertilizer = db.execute("""
        SELECT *
        FROM fertilizers
        WHERE id = ?
    """, (current_fertilizer_id,)
    ).fetchone()

    # --------------------------------------------------
    # 3. Cost Comparison
    # --------------------------------------------------
    cost_analysis = t.get('res_no_comp')
    soil_comparison = t.get('res_no_comp')
    health_comparison = t.get('res_no_comp')

    if current_fertilizer is not None:
        cost_difference = recommendation["cost_per_kg"] - current_fertilizer["cost_per_kg"]
        
        # Safe float formatting to handle decimals appropriately
        safe_cost_val = abs(cost_difference)

        if cost_difference < 0:
            cost_analysis = t.get('res_save').replace('{amt}', f"{safe_cost_val:.2f}")
        elif cost_difference > 0:
            cost_analysis = t.get('res_cost_more').replace('{amt}', f"{safe_cost_val:.2f}")
        else:
            cost_analysis = t.get('res_same_cost')

        curr_soil_tr = t.get(current_fertilizer['soil_impact'], current_fertilizer['soil_impact'])
        rec_soil_tr = t.get(recommendation['soil_impact'], recommendation['soil_impact'])
        soil_comparison = f"{t.get('res_current_label')} {curr_soil_tr} | {t.get('res_rec_label')} {rec_soil_tr}"

        curr_health_tr = t.get(current_fertilizer['health_impact'], current_fertilizer['health_impact'])
        rec_health_tr = t.get(recommendation['health_impact'], recommendation['health_impact'])
        health_comparison = f"{t.get('res_current_label')} {curr_health_tr} | {t.get('res_rec_label')} {rec_health_tr}"

        # --------------------------------------------------
        # 3.2. Quantitative Soil Health Score Algorithm
        # --------------------------------------------------
        # Assign a base weight to different types of fertilizer for visual appeal.
        def calculate_score(f_type, f_soil_impact):
            base_score = 50
            if 'Organic' in f_type:
                base_score += 30
            elif 'Chemical' in f_type:
                base_score -= 10
            
            # Simple keyword adjustments for demo simulation
            impact_lower = str(f_soil_impact).lower()
            if 'improve' in impact_lower or 'enrich' in impact_lower:
                base_score += 15
            if 'harden' in impact_lower or 'degrade' in impact_lower:
                base_score -= 20
                
            return min(max(base_score, 10), 98) # Clamp between 10 and 98

        current_score = calculate_score(current_fertilizer['type'], current_fertilizer['soil_impact'])
        recommended_score = calculate_score(recommendation['type'], recommendation['soil_impact'])
        
        soil_health_score = {
            "current": current_score,
            "recommended": recommended_score
        }
    else:
        soil_health_score = None

    # --------------------------------------------------
    # 3.5. Fetch Market Products
    # --------------------------------------------------
    market_products_rows = db.execute("""
        SELECT brand_name, price_per_bag, bag_weight_kg
        FROM market_products
        WHERE fertilizer_id = ?
    """, (recommendation["id"],)
    ).fetchall()

    market_products = [dict(row) for row in market_products_rows]

    # Simple logic to find the best value: the one with lowest price_per_bag.
    if market_products:
        market_products.sort(key=lambda x: x['price_per_bag'])
        market_products[0]['is_best_value'] = True

        for i in range(1, len(market_products)):
            market_products[i]['is_best_value'] = False

    # --------------------------------------------------
    # 4. Predict Expected Yield
    # --------------------------------------------------
    expected_yield = None
    if temperature and rainfall:
        try:
            model = get_yield_model()
            if model is not None:
                # Prepare features -> ['soil_id', 'crop_id', 'temperature', 'rainfall', 'fertilizer_id']
                # The model expects fertilizer_id to be the *recommended* fertilizer
                features = [[
                    float(soil_id),
                    float(crop_id),
                    float(temperature),
                    float(rainfall),
                    float(recommendation["id"])
                ]]
                prediction = model.predict(features)[0]
                # Convert from Tons/Hectare to kg/acre: 1 Ton/Ha = 1000 kg / 2.471 acre ≈ 404.68 kg/acre
                prediction_kg_per_acre = prediction * 404.68
                expected_yield = round(prediction_kg_per_acre, 2)
                
                chart_labels = [t.get('res_rec_label', 'Recommended:') + " " + t.get(recommendation["name"], recommendation["name"])]
                chart_yields = [expected_yield]
                
                for f_id, f_name in [(2, 'DAP'), (3, 'Neem Coated Urea'), (4, 'Vermicompost')]:
                    if f_id != recommendation["id"]:
                        feat = [[float(soil_id), float(crop_id), float(temperature), float(rainfall), float(f_id)]]
                        pred = model.predict(feat)[0] * 404.68
                        # Replace generic Vermicompost term with 'Organic' for the chart
                        display_name = "Organic" if f_name == 'Vermicompost' else f_name
                        chart_labels.append(t.get(display_name, display_name))
                        chart_yields.append(round(pred, 2))
                
                chart_data = {
                    "labels": chart_labels,
                    "yields": chart_yields
                }
        except Exception as e:
            print(f"Prediction failed: {e}")

    # --------------------------------------------------
    # 4.5 Regional Crop Intelligence System
    # --------------------------------------------------
    regional_intelligence = None
    
    try:
        crop_data = db.execute("SELECT name FROM crops WHERE id = ?", (crop_id,)).fetchone()
        crop_name = crop_data['name'] if crop_data else ''
        from flask import request
        region = request.form.get('region', '')
        
        regional_intelligence = get_regional_intelligence(region, crop_name)
            
    except Exception as e:
        print(f"Regional intelligence logic error: {e}")

    # --------------------------------------------------


    # --------------------------------------------------
    # 5. Final Result Dictionary
    # --------------------------------------------------
    result = {
        "recommended_name": t.get(recommendation["name"], recommendation["name"]),
        "recommended_type": t.get(recommendation["type"], recommendation["type"]),
        "recommended_cost": recommendation["cost_per_kg"],
        "recommended_quantity": t.get(recommendation["recommended_quantity"], recommendation["recommended_quantity"]),
        "soil_impact": t.get(recommendation["soil_impact"], recommendation["soil_impact"]),
        "health_impact": t.get(recommendation["health_impact"], recommendation["health_impact"]),
        "yield_effect": t.get(recommendation["yield_effect"], recommendation["yield_effect"]),
        "expected_yield": expected_yield,
        "chart_data": chart_data if expected_yield else None,
        "soil_health_score": soil_health_score,
        "regional_intelligence": regional_intelligence,
        "notes": t.get(recommendation["notes"], recommendation["notes"]),
        "cost_analysis": cost_analysis,
        "soil_comparison": soil_comparison,
        "health_comparison": health_comparison,
        "market_products": market_products
    }

    return result

def get_regional_intelligence(region, crop_name, cultivation_percentage=None):
    """
    Returns regional market intelligence data for a given region and crop.
    This logic powers the Regional Crop Intelligence Dashboard.
    """
    import pandas as pd
    
    top_crops_map = {
        "Kolhapur": ["Sugarcane", "Tomato", "Soybean"],
        "Pune": ["Onion", "Tomato", "Wheat"],
        "Nashik": ["Onion", "Grapes", "Pomegranate"],
        "Solapur": ["Sugarcane", "Jowar", "Pomegranate"]
    }
    
    if region in top_crops_map:
        top_crops = top_crops_map[region]
    else:
        top_crops = ["Cotton", "Soybean", "Wheat"] # generic fallback

    is_saturated = False
    predicted_price = 0.0
    low_price = 0
    stable_price = 0
    high_price = 0
    variance = 0

    historical_range = 'Not available'
    try:
        price_model = get_price_model()
        risk_model = get_risk_model()
        
        if price_model is not None and risk_model is not None:
            feature_row = build_price_feature_row(region, crop_name, cultivation_percentage)
            features = pd.DataFrame([feature_row])
            
            risk_pred = risk_model.predict(features)[0]
            is_saturated = bool(risk_pred == 1)
            
            predicted_price = float(price_model.predict(features)[0])
            if predicted_price <= 1:
                predicted_price = float(feature_row.get("previous_price", 0.0))

        # Historical range from dataset with cultivation ratio context
        df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'data', 'crop_price_dataset.csv'))
        subset = df[(df['Region'] == region) & (df['Crop'] == crop_name)]

        window = 20 if is_saturated else 10
        if cultivation_percentage is not None and not subset.empty:
            subset = subset[(subset['Cultivation_Percentage'] >= cultivation_percentage - window) &
                            (subset['Cultivation_Percentage'] <= cultivation_percentage + window)]

        if subset.empty:
            subset = df[(df['Region'] == region) & (df['Crop'] == crop_name)]

        if subset.empty:
            subset = df[df['Crop'] == crop_name]

        if not subset.empty:
            min_price = subset['Last_Year_Price'].min()
            max_price = subset['Last_Year_Price'].max()

            # Ensure at least ₹5 spread, to make range useful
            if (max_price - min_price) < 5:
                mid_price = (max_price + min_price) / 2
                min_price = max(mid_price - 2.5, 0)
                max_price = min_price + 5

            historical_range = f"₹{min_price:.2f} - ₹{max_price:.2f} / kg"
            if len(subset) > 1:
                avg_price = subset['Last_Year_Price'].mean()
                historical_range += f" (avg ₹{avg_price:.2f})"
    except Exception as e:
        print(f"ML Prediction failed: {e}")
        pass
    
    if is_saturated:
        risk = "res_risk_high"
        demand = "res_demand_down"
        
        if crop_name in ["Tomato", "Onion", "Sugarcane"]:
            alternatives = ["Sorghum", "Chili", "Okra", "Cotton"]
        else:
            alternatives = ["Wheat", "Sorghum", "Banana"]

        if predicted_price > 0:
            unit = "Ton" if crop_name == "Sugarcane" else "kg"
            low_price = predicted_price * 0.80
            stable_price = predicted_price * 0.90
            high_price = predicted_price * 1.00
            variance = max(5, int((high_price - low_price) / 2))
            price_prediction = f"₹{low_price:.0f}–₹{high_price:.0f} / {unit} (Expected drop)"
        else:
            price_prediction = "Expected to drop by 20-30%"
            low_price = 0
            stable_price = 0
            high_price = 0
            variance = 0
    else:
        risk = "res_risk_low"
        demand = "res_demand_high"
        
        if predicted_price > 0:
            unit = "Ton" if crop_name == "Sugarcane" else "kg"
            low_price = predicted_price * 0.95
            stable_price = predicted_price * 1.05
            high_price = predicted_price * 1.15
            variance = max(5, int((high_price - low_price) / 2))
            price_prediction = f"₹{low_price:.0f}–₹{high_price:.0f} / {unit} (Stable/Premium)"
        else:
            price_prediction = "Stable Premium Market"
            low_price = 0
            stable_price = 0
            high_price = 0
            variance = 0
            
        alternatives = []
        
    # Get actual price ranges from dataset
    price_range_data = get_price_range_for_crop(region, crop_name)
        
    return {
        "region": region if region else "Maharashtra",
        "crop": crop_name,
        "top_crops": top_crops,
        "risk_key": risk,
        "demand_key": demand,
        "price_prediction": price_prediction,
        "low_price": low_price,
        "stable_price": stable_price,
        "high_price": high_price,
        "variance": variance,
        "price_category": price_range_data['category'],
        "price_average": price_range_data['average_price'],
        "price_range_str": price_range_data['price_range_str'],
        "price_color": price_range_data['color'],
        "price_bg_color": price_range_data['bg_color'],
        "price_border_color": price_range_data['border_color'],
        "price_text_color": price_range_data['text_color'],
        "historical_price_range": historical_range,
        "model_source": (get_price_model_meta() or {}).get("source_dataset"),
        "model_trained_at": (get_price_model_meta() or {}).get("trained_at"),
        "model_row_count": (get_price_model_meta() or {}).get("row_count"),
        "model_date_range": (get_price_model_meta() or {}).get("date_range"),
        "alternatives": alternatives,
        "is_saturated": is_saturated
    }

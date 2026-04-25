from flask import Blueprint, render_template, request, current_app
from models.fertilizer_model import get_recommendation, get_regional_intelligence
from utils.weather import get_region_weather
from translations import translations

main = Blueprint('main', __name__)

def get_lang():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'
    return lang

# -----------------------------
# Home Page - Input Form
# -----------------------------
@main.route('/')
def home():
    lang = get_lang()
    t = translations[lang]

    return render_template(
        'index.html',
        t=t,
        lang=lang
    )

# -----------------------------
# Analyzer Page
# -----------------------------
@main.route('/analyzer')
def analyzer():
    db = current_app.get_db()
    lang = get_lang()
    t = translations[lang]

    crops = db.execute("SELECT * FROM crops").fetchall()
    soils = db.execute("SELECT * FROM soil_types").fetchall()
    fertilizers = db.execute("SELECT * FROM fertilizers").fetchall()

    return render_template(
        'analyzer.html',
        crops=crops,
        soils=soils,
        fertilizers=fertilizers,
        t=t,
        lang=lang
    )


# -----------------------------
# Recommendation Result
# -----------------------------
@main.route('/recommend', methods=['POST'])
def recommend():
    lang = request.args.get('lang', 'en')
    if lang not in translations:
        lang = 'en'
    t = translations[lang]

    crop_id = request.form.get('crop')
    soil_id = request.form.get('soil')
    current_fertilizer_id = request.form.get('current_fertilizer')
    region = request.form.get('region')

    if region:
        weather_data = get_region_weather(region)
        temperature = weather_data['temp']
        rainfall = weather_data['rain']
    else:
        temperature = None
        rainfall = None

    result = get_recommendation(
        crop_id,
        soil_id,
        current_fertilizer_id,
        temperature,
        rainfall,
        lang
    )
    
    # Add mapped environmental data to the result dict for display
    result['region'] = region
    result['temperature'] = temperature
    result['rainfall'] = rainfall

    return render_template('result.html', result=result, t=t, lang=lang)

# -----------------------------
# Feedback Form
# -----------------------------
@main.route('/feedback', methods=['GET', 'POST'])
def feedback():
    lang = get_lang()
    t = translations[lang]
    db = current_app.get_db()

    success_message = None

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        db.execute(
            "INSERT INTO feedback (name, email, message) VALUES (?, ?, ?)",
            (name, email, message)
        )
        db.commit()
        success_message = t.get('feedback_success', 'Thank you! Your feedback has been received.')

    return render_template('feedback.html', t=t, lang=lang, success_message=success_message)

# -----------------------------
# Price Risk Predictor
# -----------------------------
@main.route('/price-risk')
def price_risk():
    db = current_app.get_db()
    lang = get_lang()
    t = translations[lang]

    crops = db.execute("SELECT * FROM crops").fetchall()
    
    # Keeping to English names for mapping logic to ML
    regions = [
        "Kolhapur", "Pune", "Nashik", "Solapur", "Nagpur", "Aurangabad", 
        "Ajra", "Bhudargad", "Chandgad", "Gadhinglaj", "Gaganbavda", 
        "Hatkanangle", "Kagal", "Karvir", "Panhala", "Radhanagari", "Shahuwadi", "Shirol"
    ]

    return render_template(
        'price_risk.html',
        crops=crops,
        regions=regions,
        t=t,
        lang=lang
    )

@main.route('/predict-risk', methods=['POST'])
def predict_risk():
    lang = get_lang()
    t = translations[lang]

    db = current_app.get_db()
    crop_name = request.form.get('crop')
    region = request.form.get('region')

    cultivation_percentage = None
    try:
        result = db.execute("""
            SELECT r.percentage
            FROM regional_crop_data r
            LEFT JOIN crops c ON r.crop_id = c.id
            WHERE r.region_name = ? AND c.name = ?
            LIMIT 1
        """, (region, crop_name)).fetchone()
        if result is not None:
            cultivation_percentage = float(result['percentage'])
    except Exception:
        cultivation_percentage = None

    intelligence = get_regional_intelligence(region, crop_name, cultivation_percentage)

    return render_template('price_risk_result.html', intelligence=intelligence, t=t, lang=lang)

# -----------------------------
# Crop Planning Map
# -----------------------------
@main.route('/map')
def crop_map():
    db = current_app.get_db()
    lang = get_lang()
    t = translations[lang]

    # Initial page load with generic data (just structure, data will be loaded via JS)
    return render_template('map.html', t=t, lang=lang)

@main.route('/api/region_data/<region_name>')
def get_region_data(region_name):
    db = current_app.get_db()
    lang = get_lang()
    t = translations[lang]

    query = """
    SELECT r.region_name, c.name as crop_name, r.percentage 
    FROM regional_crop_data r
    LEFT JOIN crops c ON r.crop_id = c.id
    WHERE r.region_name = ?
    ORDER BY r.percentage DESC
    """
    
    # Capitalize region for DB match
    region_name = region_name.capitalize()
    
    try:
        distribution_data = db.execute(query, (region_name,)).fetchall()
    except Exception as e:
        return {"error": "⚠ Data unavailable<br>Please try another region", "region_name": region_name}
    
    result = []
    top_crop_name = None
    for idx, row in enumerate(distribution_data):
        crop_base = row['crop_name'] if row['crop_name'] else 'Others'
        if idx == 0 and crop_base != 'Others':
            top_crop_name = crop_base
            
        # Translate the crop name
        crop_trans = t.get(crop_base, crop_base)
        result.append({
            'crop_name': crop_trans,
            'percentage': row['percentage']
        })
        
    regional_intelligence = None
    if top_crop_name or len(distribution_data) == 0:
        # Fallback to random common crop if no DB data
        query_crop = top_crop_name if top_crop_name else "Wheat"
        intel = get_regional_intelligence(region_name, query_crop)
        
        regional_intelligence = {
            "region": intel["region"],
            "crop": t.get(intel["crop"], intel["crop"]),
            "top_crops": [t.get(c, c) for c in intel["top_crops"]],
            "risk_key": t.get(intel["risk_key"], intel["risk_key"]),
            "demand_key": t.get(intel["demand_key"], intel["demand_key"]),
            "price_prediction": intel["price_prediction"],
            "alternatives": [t.get(a, a) for a in intel["alternatives"]],
            "is_saturated": intel["is_saturated"],
            "t_dashboard_title": t.get('res_regional_dashboard_title', 'Regional Crop Intelligence Dashboard'),
            "t_top_crops": t.get('res_top_crops', 'Top Crops in District'),
            "t_future_price_risk": t.get('res_future_price_risk', 'Future Price Risk'),
            "t_market_demand": t.get('res_market_demand', 'Market Demand'),
            "t_expected_price": t.get('res_expected_price', 'Expected Price Next Season:'),
            "t_warning_title": f"⚠ {t.get(intel['crop'], intel['crop'])} {t.get('res_oversupply_title', 'production already high in this district')}",
            "t_consider_alternatives": t.get('res_consider_alternatives', 'Consider planting alternatives:')
        }
        
    return {"region_name": region_name, "distribution": result, "intelligence": regional_intelligence}

@main.route('/api/all_regions_data')
def get_all_regions_data():
    """
    Retrieves the dominant crop and its threshold percentage for every region
    in the database, mapped specifically to power the Overproduction Heat Map mode.
    """
    db = current_app.get_db()
    lang = get_lang()
    t = translations[lang]

    # Group by region and find the max percentage via a window function equivalent or simple aggregation.
    # We will just fetch all, ordered by region and percentage descending, and take the first of each.
    query = """
    SELECT r.region_name, c.name as crop_name, r.percentage 
    FROM regional_crop_data r
    LEFT JOIN crops c ON r.crop_id = c.id
    ORDER BY r.region_name, r.percentage DESC
    """
    try:
        all_data = db.execute(query).fetchall()
    except Exception as e:
        all_data = []
    
    regions_map = {}
    for row in all_data:
        r_name = row['region_name']
        if r_name not in regions_map:
            # First row for this region is the highest percentage
            crop_base = row['crop_name'] if row['crop_name'] else 'Others'
            regions_map[r_name] = {
                'dominant_crop': t.get(crop_base, crop_base),
                'dominant_crop_base': crop_base, # Need base name for intelligence loop
                'max_percentage': row['percentage']
            }
            
    # Also pack the region mapping intelligence for the hover tooltips
    response_map = {}
    for r_name, data in regions_map.items():
        base_crop = data['dominant_crop_base']
        intel = get_regional_intelligence(r_name, base_crop)
        
        # Calculate Overproduction Risk based on user instructions
        pct = float(data['max_percentage'])
        if pct > 50.0:
            risk_level = "High"
            color_code = "red"
        elif pct > 30.0:
            risk_level = "Medium"
            color_code = "yellow"
        else:
            risk_level = "Low"
            color_code = "green"
            
        t_risk_level = t.get(f"risk_{risk_level.lower()}", risk_level)
            
        response_map[r_name] = {
            'dominant_crop': data['dominant_crop'],
            'max_percentage': pct,
            'risk_level': risk_level,
            't_risk_level': t_risk_level,
            'color_code': color_code,
            'is_saturated': intel['is_saturated'],
            'price_prediction': intel['price_prediction']
        }
        
    return {"regions": response_map}
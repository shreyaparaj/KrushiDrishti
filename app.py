from flask import Flask, g, request, render_template
import os
import sqlite3
from translations import translations


def create_app():
    app = Flask(__name__)

    # -----------------------------
    # Configuration
    # -----------------------------
    app.config.from_pyfile('config.py')

    # -----------------------------
    # Database Path Setup
    # -----------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, app.config['DATABASE'])

    app.config['DATABASE_PATH'] = DATABASE_PATH

    # -----------------------------
    # Database Functions
    # -----------------------------
    def get_db():
        if 'db' not in g:
            g.db = sqlite3.connect(app.config['DATABASE_PATH'])
            g.db.row_factory = sqlite3.Row
        return g.db

    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def init_db():
        db = sqlite3.connect(app.config['DATABASE_PATH'])
        schema_path = os.path.join(BASE_DIR, 'database', 'schema.sql')

        with open(schema_path, 'r') as f:
            db.executescript(f.read())

        db.commit()
        db.close()

    # Attach DB functions to app
    app.teardown_appcontext(close_db)
    app.get_db = get_db
    app.init_db = init_db

    # -----------------------------
    # Create Database If Not Exists
    # -----------------------------
    if not os.path.exists(app.config['DATABASE_PATH']):
        print("Database not found. Creating new database...")
        open(app.config['DATABASE_PATH'], 'w').close()
        init_db()
        print("Database initialized successfully.")

    # -----------------------------
    # Register Blueprints
    # -----------------------------
    from routes.main_routes import main
    app.register_blueprint(main)

    # -----------------------------
    # ML Price Risk Route
    # -----------------------------
    @app.route("/price-risk", methods=["POST"])
    def price_risk():
        # Using .get() and fallbacks as safety since we are fetching direct form values
        crop = request.form.get("crop", "")
        region = request.form.get("region", "")
        
        try:
            cultivation_percentage = float(request.form.get("area", 0))
            rainfall = float(request.form.get("rainfall", 0))
            temperature = float(request.form.get("temperature", 0))
            last_price = float(request.form.get("last_price", 0))
        except ValueError:
            # Fallbacks just in case the form submission was malformed
            cultivation_percentage = 0.0
            rainfall = 0.0
            temperature = 0.0
            last_price = 0.0

        # Get regional intelligence which includes price prediction details
        from models.fertilizer_model import get_regional_intelligence
        risk_data = get_regional_intelligence(region, crop, cultivation_percentage)

        lang = request.args.get('lang', 'en')
        t = translations.get(lang, translations['en'])

        return render_template(
            "price_result.html",
            crop=crop,
            region=region,
            risk=risk_data,
            lang=lang,
            t=t
        )

    return app


# Create App Instance
app = create_app()


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

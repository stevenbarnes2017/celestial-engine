from flask import Blueprint, jsonify
from app.services.astrology_engine import AstrologyEngine
from app.services.bazi_engine import BaziEngine
from app.services.aspect_engine import AspectEngine  # <-- 1. IMPORT ASPECT ENGINE
from datetime import date, time

test_bp = Blueprint('test_astro', __name__, url_prefix='/api/test')

@test_bp.route('/chart', methods=['GET'])
def test_chart():
    engine = AstrologyEngine()
    bazi = BaziEngine()
    aspect_scanner = AspectEngine()  # <-- 2. INSTANTIATE ASPECT ENGINE
    
    try:
        birth_date = date(1990, 3, 2)
        birth_time = time(8, 45, 0)
        timezone_str = 'America/Denver'
        latitude = 38.8339
        longitude = -104.8214
        
        # Calculate Western planets & houses
        planets = engine.calculate_natal_planets(birth_date, birth_time, timezone_str)
        houses_and_angles = engine.calculate_houses(
            birth_date, birth_time, timezone_str, latitude, longitude
        )
        
        # Calculate Eastern BaZi
        bazi_pillars = bazi.calculate_bazi(birth_date, birth_time, timezone_str, longitude)
        
        # Calculate Geometric Aspects from planetary coordinates
        aspect_grid = aspect_scanner.calculate_aspects(planets)  # <-- 3. SCAN PLANETS
        
        return jsonify({
            "status": "success",
            "message": "Full analytics matrix compiled successfully.",
            "western": {
                "planets": planets,
                "angles": houses_and_angles["angles"],
                "houses": houses_and_angles["houses"],
                "aspects": aspect_grid  # <-- 4. OUTPUT RESULTS
            },
            "eastern_bazi": bazi_pillars
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
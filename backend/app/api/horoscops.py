from flask import Blueprint, request, jsonify
from app import db
from app.models.user import HoroscopeCache
from app.utils.time_handlers import calculate_horizon_expiration
# Assuming you have your Groq client configured under app.utils
from app.utils.groq_client import generate_llm_horoscope 

horoscope_bp = Blueprint('horoscope', __name__)

@horoscope_bp.route('/api/horoscope', methods=['POST'])
def get_horoscope():
    data = request.get_json()
    
    sign = data.get('sign')          # e.g., 'Pisces'
    system = data.get('system')      # 'western' or 'eastern'
    horizon = data.get('horizon')    # 'daily', 'weekly', etc.
    force_refresh = data.get('force_refresh', False) # For that manual 'Regenerate' button
    
    if not all([sign, system, horizon]):
        return jsonify({"error": "Missing lookup coordinates"}), 400

    # 1. Query Cache Table
    cache_entry = HoroscopeCache.query.filter_by(
        sign_name=sign,
        system_type=system,
        time_horizon=horizon
    ).first()

    # 2. Check Cache Validity
    if cache_entry and not cache_entry.is_expired() and not force_refresh:
        return jsonify({
            "source": "cache",
            "reading": cache_entry.reading_text,
            "expires_at": cache_entry.expires_at.isoformat()
        }), 200

    # 3. Cache Miss / Expired -> Trigger Groq LPU
    try:
        fresh_reading = generate_llm_horoscope(sign, system, horizon)
        expiration_timestamp = calculate_horizon_expiration(horizon)
        
        if cache_entry:
            # Update existing expired row
            cache_entry.reading_text = fresh_reading
            cache_entry.generated_at = datetime.utcnow()
            cache_entry.expires_at = expiration_timestamp
        else:
            # Create fresh cache entity
            new_cache = HoroscopeCache(
                sign_name=sign,
                system_type=system,
                time_horizon=horizon,
                reading_text=fresh_reading,
                expires_at=expiration_timestamp
            )
            db.session.add(new_cache)
            
        db.session.commit()
        
        return jsonify({
            "source": "groq_engine",
            "reading": fresh_reading,
            "expires_at": expiration_timestamp.isoformat()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to compile cosmic telemetry: {str(e)}"}), 500
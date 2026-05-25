from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.services.astrology_engine import AstrologyEngine
from app.services.bazi_engine import BaziEngine
from app.services.aspect_engine import AspectEngine
from datetime import datetime, timedelta, date, time
import werkzeug.security as security
import jwt
import os
from app.utils.auth_decorators import token_required, JWT_SECRET_KEY
from app.services.dynamic_interpretation_engine import DynamicInterpretationEngine
from app.services.transit_engine import TransitEngine

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Use environment variable for JWT secret, fallback to dev key
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-cosmic-secret-key-1982')

def encode_auth_token(user_id):
    """Generates a secure stateless JWT token valid for 24 hours."""
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': str(user_id)
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
    except Exception as e:
        return str(e)

def decode_auth_token(auth_header):
    """Decodes the JWT token from the Authorization header."""
    if not auth_header or not auth_header.startswith('Bearer '):
        return "Missing or malformed token."
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['sub']
    except jwt.ExpiredSignatureError:
        return "Signature expired. Please log in again."
    except jwt.InvalidTokenError:
        return "Invalid token. Please log in again."


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Simplified registration - only requires email and password"""
    data = request.get_json() or {}
    
    if 'email' not in data or 'password' not in data:
        return jsonify({"error": "Missing required email or password fields."}), 400

    # Check for existing user
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "An account with this email address already exists."}), 409

    # Validate password strength
    if len(data['password']) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    try:
        new_user = User(
            email=data['email'],
            password_hash=security.generate_password_hash(data['password'])
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Auto-login after registration
        token = encode_auth_token(new_user.id)
        
        return jsonify({
            "status": "success",
            "message": "User account created successfully.",
            "token": token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create account: {str(e)}"}), 500
    
@auth_bp.route('/register-complete', methods=['POST'])
def register_complete():
    """Complete registration with birth data and automatic chart calculation"""
    data = request.get_json() or {}
    
    # Validate required fields
    required_fields = ['email', 'password', 'birth_date', 'birth_time', 
                      'timezone', 'latitude', 'longitude']
    
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Check for existing user
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "An account with this email address already exists."}), 409

    # Validate password strength
    if len(data['password']) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    try:
        from datetime import datetime as dt
        
        # Parse birth data
        birth_date = dt.strptime(data['birth_date'], '%Y-%m-%d').date()
        birth_time = dt.strptime(data['birth_time'], '%H:%M').time()
        
        # Create user
        new_user = User(
            email=data['email'],
            password_hash=security.generate_password_hash(data['password']),
            birth_date=birth_date,
            birth_time=birth_time,
            timezone=data['timezone'],
            latitude=data['latitude'],
            longitude=data['longitude']
        )
        
        # Calculate natal chart
        try:
            astro_engine = AstrologyEngine()
            bazi_engine = BaziEngine()
            aspect_engine = AspectEngine()
            
            # Western chart - use correct method names
            planets = astro_engine.calculate_natal_planets(
                birth_date,
                birth_time,
                data['timezone']
            )
            
            houses = astro_engine.calculate_houses(
                birth_date,
                birth_time,
                data['timezone'],
                data['latitude'],
                data['longitude']
            )
            
            # Calculate aspects from planets
            aspects = aspect_engine.calculate_aspects(planets)
            
            # Eastern BaZi
            bazi_pillars = bazi_engine.compute_four_pillars(
                birth_date,
                birth_time,
                data['timezone'],
                data['longitude']
            )
            
            # Store calculated data
            new_user.planetary_positions = planets
            new_user.house_cusps = houses
            new_user.planetary_aspects = aspects
            new_user.bazi_pillars = bazi_pillars
            
            # Extract angles from houses if available
            if houses and 'angles' in houses:
                new_user.chart_angles = houses['angles']
            
        except Exception as calc_error:
            # Log error but allow registration to succeed
            print(f"⚠️  Chart calculation error: {calc_error}")
            # User can still login, charts calculated later
        
        db.session.add(new_user)
        db.session.commit()
        
        # Auto-login
        token = encode_auth_token(new_user.id)
        
        # Get preview data
        sun_sign = "Unknown"
        moon_sign = "Unknown"
        rising_sign = "Unknown"
        day_master = "Unknown"
        
        if new_user.planetary_positions:
            sun_sign = new_user.planetary_positions.get('Sun', {}).get('zodiac_sign', 'Unknown')
            moon_sign = new_user.planetary_positions.get('Moon', {}).get('zodiac_sign', 'Unknown')
        
        if new_user.chart_angles and 'Ascendant' in new_user.chart_angles:
            rising_sign = new_user.chart_angles['Ascendant'].get('zodiac_sign', 'Unknown')
        
        if new_user.bazi_pillars and 'Day_Pillar' in new_user.bazi_pillars:
            day_master = new_user.bazi_pillars['Day_Pillar'].get('Stem', 'Unknown')
        
        return jsonify({
            "status": "success",
            "message": "Account created and natal chart calculated!",
            "token": token,
            "chart_preview": {
                "sun_sign": sun_sign,
                "moon_sign": moon_sign,
                "rising_sign": rising_sign,
                "day_master": day_master
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"error": f"Invalid date/time format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create account: {str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticates a user and returns their secure token."""
    data = request.get_json() or {}
    if 'email' not in data or 'password' not in data:
        return jsonify({"error": "Missing email or password"}), 400

    user = User.query.filter_by(email=data['email']).first()
    if user and security.check_password_hash(user.password_hash, data['password']):
        token = encode_auth_token(user.id)
        return jsonify({
            "message": "Login successful",
            "token": token
        }), 200
    
    return jsonify({"error": "Invalid email or password"}), 401


# ============================================================================
# USER PROFILE ENDPOINTS
# ============================================================================

@auth_bp.route('/current-chart', methods=['GET'])
@token_required
def get_current_chart(current_user):
    """
    Returns the user's complete astrological profile.
    If birth data exists, returns calculations. Otherwise returns basic profile.
    """
    
    response_data = {
        "status": "success",
        "email": current_user.email,
        "billing_status": current_user.billing_status,
    }

    # Check if user has birth data
    if current_user.birth_date and current_user.birth_time:
        response_data["birth_telemetry"] = {
            "date": current_user.birth_date.isoformat(),
            "time": current_user.birth_time.strftime('%H:%M:%S'),
            "timezone": current_user.timezone,
            "coordinates": {
                "latitude": current_user.latitude, 
                "longitude": current_user.longitude
            }
        }
        
        response_data["western_chart"] = {
            "planets": current_user.planetary_positions or {},
            "houses": current_user.house_cusps or {},
            "angles": current_user.chart_angles or {},
            "aspects": current_user.planetary_aspects or []
        }
        
        response_data["eastern_bazi"] = current_user.bazi_pillars or {}
        
        # Generate comprehensive interpretation if not already generated
        if current_user.planetary_positions and current_user.bazi_pillars:
            interpreter = DynamicInterpretationEngine()
            response_data["authentic_horoscope"] = interpreter.generate_authentic_horoscope(current_user)
    else:
        # User hasn't provided birth data yet
        response_data["birth_telemetry"] = None
        response_data["western_chart"] = {"planets": {"Sun": {"zodiac_sign": "Unknown"}}}
        response_data["eastern_bazi"] = {"Year_Pillar": {"Branch": "Unknown"}}

    return jsonify(response_data), 200


@auth_bp.route('/current-sky', methods=['GET'])
@token_required
def get_current_sky(current_user):
    """
    Returns current planetary positions and interpretation of today's celestial configuration
    """
    from datetime import datetime
    
    # Get current planetary positions
    current_positions = get_current_planetary_positions()
    today = datetime.now().date()
    
    # Generate interpretation of current sky
    interpreter = DynamicInterpretationEngine()
    sky_interpretation = interpreter.generate_sky_interpretation(current_positions, today)
    
    return jsonify({
        "status": "success",
        "current_date": today.isoformat(),
        "current_positions": current_positions,
        "interpretation": sky_interpretation
    }), 200


# ============================================================================
# HOROSCOPE GENERATION ENDPOINT (NEW UNIFIED ENDPOINT)
# ============================================================================

@auth_bp.route('/horoscope', methods=['GET'])
@token_required
def get_horoscope(current_user):
    """
    Unified horoscope endpoint that handles:
    - Different time periods: daily, weekly, monthly, yearly
    - Different systems: western, chinese
    - Different signs: user's sign or any other sign
    - Caching: returns cached if valid, generates new if expired
    """
    
    # Get parameters from query string
    period = request.args.get('period', 'daily')  # daily, weekly, monthly, yearly
    system = request.args.get('system', 'western')  # western, chinese
    sign = request.args.get('sign', 'your-sign')  # 'your-sign' or specific sign name
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    # Get today's date
    today = datetime.now().date()
    
    # Check cache
    if not force_refresh:
        cached_reading = get_cached_reading(current_user, period, system, sign, today)
        if cached_reading:
            return jsonify(cached_reading), 200
    
    # Generate new reading
    interpreter = DynamicInterpretationEngine()
    
    # Determine which sign to read
    if sign == 'your-sign':
        # Use user's actual sign
        if system == 'western':
            if current_user.planetary_positions and 'Sun' in current_user.planetary_positions:
                target_sign = current_user.planetary_positions['Sun']['zodiac_sign']
            else:
                target_sign = 'Pisces'  # Default
        else:  # chinese
            if current_user.bazi_pillars and 'Year_Pillar' in current_user.bazi_pillars:
                target_sign = current_user.bazi_pillars['Year_Pillar']['Branch']
            else:
                target_sign = 'Dragon'  # Default
    else:
        target_sign = sign
    
    # Generate reading based on period
    if period == 'daily':
        reading_data = generate_daily_reading(current_user, system, target_sign, interpreter)
    elif period == 'weekly':
        reading_data = generate_weekly_reading(current_user, system, target_sign, interpreter)
    elif period == 'monthly':
        reading_data = generate_monthly_reading(current_user, system, target_sign, interpreter)
    elif period == 'yearly':
        reading_data = generate_yearly_reading(current_user, system, target_sign, interpreter)
    else:
        return jsonify({"error": "Invalid period specified"}), 400
    
    # Cache the reading
    cache_reading(current_user, period, system, sign, today, reading_data)
    
    return jsonify(reading_data), 200


# ============================================================================
# READING GENERATION HELPERS
# ============================================================================

def generate_daily_reading(user, system, sign, interpreter):
    """Generate daily horoscope with transits"""
    today = datetime.now().date()
    
    # Get current sky positions (real-time)
    current_sky = get_current_planetary_positions()
    
    # Calculate transits if user has natal chart
    active_transits = []
    if user.planetary_positions:
        transit_calc = TransitEngine()
        active_transits = transit_calc.calculate_transit_aspects(
            user.planetary_positions, 
            current_sky
        )
    
    # Generate reading
    if system == 'western':
        reading = interpreter.generate_western_daily(sign, active_transits, today)
    else:  # chinese
        reading = interpreter.generate_chinese_daily(sign, today)
    
    return {
        "status": "success",
        "period": "daily",
        "system": system,
        "sign": sign,
        "date_today": today.isoformat(),
        "horoscope": reading,
        "active_geometric_transits": active_transits if system == 'western' else []
    }


def generate_weekly_reading(user, system, sign, interpreter):
    """Generate weekly horoscope"""
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    if system == 'western':
        reading = interpreter.generate_western_weekly(sign, week_start, week_end)
    else:
        reading = interpreter.generate_chinese_weekly(sign, week_start, week_end)
    
    return {
        "status": "success",
        "period": "weekly",
        "system": system,
        "sign": sign,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "horoscope": reading
    }


def generate_monthly_reading(user, system, sign, interpreter):
    """Generate monthly horoscope"""
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    if system == 'western':
        reading = interpreter.generate_western_monthly(sign, month_start)
    else:
        reading = interpreter.generate_chinese_monthly(sign, month_start)
    
    return {
        "status": "success",
        "period": "monthly",
        "system": system,
        "sign": sign,
        "month": month_start.strftime("%B %Y"),
        "horoscope": reading
    }


def generate_yearly_reading(user, system, sign, interpreter):
    """Generate yearly horoscope"""
    today = datetime.now().date()
    year = today.year
    
    if system == 'western':
        reading = interpreter.generate_western_yearly(sign, year)
    else:
        reading = interpreter.generate_chinese_yearly(sign, year)
    
    return {
        "status": "success",
        "period": "yearly",
        "system": system,
        "sign": sign,
        "year": year,
        "horoscope": reading
    }


# ============================================================================
# CACHING SYSTEM
# ============================================================================

# In-memory cache (in production, use Redis)
horoscope_cache = {}

def get_cache_key(user_id, period, system, sign, date_obj):
    """Generate cache key"""
    if period == 'daily':
        date_str = date_obj.isoformat()
    elif period == 'weekly':
        # Use week start date
        week_start = date_obj - timedelta(days=date_obj.weekday())
        date_str = week_start.isoformat()
    elif period == 'monthly':
        date_str = f"{date_obj.year}-{date_obj.month:02d}"
    elif period == 'yearly':
        date_str = str(date_obj.year)
    else:
        date_str = date_obj.isoformat()
    
    return f"{user_id}_{period}_{system}_{sign}_{date_str}"


def get_cached_reading(user, period, system, sign, date_obj):
    """Retrieve cached reading if valid"""
    cache_key = get_cache_key(user.id, period, system, sign, date_obj)
    return horoscope_cache.get(cache_key)


def cache_reading(user, period, system, sign, date_obj, reading_data):
    """Store reading in cache"""
    cache_key = get_cache_key(user.id, period, system, sign, date_obj)
    horoscope_cache[cache_key] = reading_data


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_current_planetary_positions():
    """Get real-time planetary positions"""
    engine = AstrologyEngine()
    now = datetime.now()
    
    # Calculate current positions
    try:
        current_positions = engine.calculate_natal_planets(
            now.date(),
            now.time(),
            'UTC'
        )
        return current_positions
    except Exception as e:
        # Fallback to mock data if calculation fails
        return {
            "Mars": {"absolute_degree": 142.5},
            "Mercury": {"absolute_degree": 54.1},
            "Sun": {"absolute_degree": 60.2}
        }


# ============================================================================
# LEGACY ENDPOINT (for backwards compatibility)
# ============================================================================

@auth_bp.route('/daily-forecast', methods=['GET'])
@token_required
def get_daily_forecast(current_user):
    """
    Legacy endpoint - redirects to new unified endpoint
    """
    return get_horoscope(current_user)

@auth_bp.route('/test-engine', methods=['GET'])
def test_engine():
    """Temporary test to see what methods exist"""
    astro_engine = AstrologyEngine()
    
    # Get all methods
    methods = [method for method in dir(astro_engine) if not method.startswith('_')]
    
    return jsonify({
        "available_methods": methods
    })
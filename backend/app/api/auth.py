from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from app.services.astrology_engine import AstrologyEngine
from app.services.bazi_engine import BaziEngine
from app.services.aspect_engine import AspectEngine
from datetime import datetime, timedelta
import werkzeug.security as security
import jwt
from app.utils.auth_decorators import token_required, JWT_SECRET_KEY
from app.services.dynamic_interpretation_engine import DynamicInterpretationEngine
from app.services.transit_engine import TransitEngine

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

JWT_SECRET_KEY = "super-secret-celestial-key-change-me"

def encode_auth_token(user_id):
    """Generates a secure stateless JWT token valid for 24 hours."""
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': str(user_id)  # <-- FORCE TO STRING FORMAT
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        if isinstance(token, bytes):
            return token.decode('utf-8')
        return token
    except Exception as e:
        return str(e)

def encode_auth_token(user_id):
    """Generates a secure stateless JWT token valid for 24 hours."""
    try:
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
    except Exception as e:
        return str(e)

def decode_auth_token(auth_header):
    """Decodes the JWT token from the Authorization header."""
    if not auth_header or not auth_header.startswith('Bearer '):
        return "Missing or malformed token."
    
    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['sub']  # Returns the user_id
    except jwt.ExpiredSignatureError:
        return "Signature expired. Please log in again."
    except jwt.InvalidTokenError:
        return "Invalid token. Please log in again."


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    required_fields = ['email', 'password', 'birth_date', 'birth_time', 'timezone', 'latitude', 'longitude']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required user profile or birth telemetry fields"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    try:
        parsed_date = datetime.strptime(data['birth_date'], '%Y-%m-%d').date()
        parsed_time = datetime.strptime(data['birth_time'], '%H:%M:%S').time()
        
        western_engine = AstrologyEngine()
        bazi_engine = BaziEngine()
        aspect_engine = AspectEngine()
        
        planets = western_engine.calculate_natal_planets(parsed_date, parsed_time, data['timezone'])
        houses_data = western_engine.calculate_houses(
            parsed_date, parsed_time, data['timezone'], float(data['latitude']), float(data['longitude'])
        )
        bazi_data = bazi_engine.calculate_bazi(
            parsed_date, parsed_time, data['timezone'], float(data['longitude'])
        )
        aspect_data = aspect_engine.calculate_aspects(planets)

        new_user = User(
            email=data['email'],
            password_hash=security.generate_password_hash(data['password']),
            birth_date=parsed_date,
            birth_time=parsed_time,
            timezone=data['timezone'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            planetary_positions=planets,
            house_cusps=houses_data['houses'],
            chart_angles=houses_data['angles'],
            bazi_pillars=bazi_data,
            planetary_aspects=aspect_data
        )

        db.session.add(new_user)
        db.session.commit()

        # Issue token right away upon successful signup so they are logged in automatically
        token = encode_auth_token(new_user.id)

        return jsonify({
            "message": "Registration and calculations complete.",
            "token": token,
            "preview_signs": {
                "western_sun": planets['Sun']['zodiac_sign'],
                "bazi_year_animal": bazi_data['Year_Pillar']['Branch']
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to process registration: {str(e)}"}), 500


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


@auth_bp.route('/current-chart', methods=['GET'])
@token_required
def get_current_chart(current_user):
    """
    Secure endpoint executing true real-time, AI-driven horoscope synthesis
    by feeding precise database coordinates directly into a secure GenAI pipeline.
    """
    pipeline = DynamicInterpretationEngine()
    
    # Run the live cryptographic API handshake to interpret the data blocks
    authentic_reading = pipeline.generate_authentic_horoscope(current_user)

    return jsonify({
        "status": "success",
        "email": current_user.email,
        "billing_status": current_user.billing_status,
        "birth_telemetry": {
            "date": current_user.birth_date.isoformat(),
            "time": current_user.birth_time.strftime('%H:%M:%S'),
            "timezone": current_user.timezone,
            "coordinates": {"latitude": current_user.latitude, "longitude": current_user.longitude}
        },
        "authentic_horoscope": authentic_reading,  # <-- LIVE GENERATED TEXT OUTPUT
        "western_chart": {
            "planets": current_user.planetary_positions,
            "houses": current_user.house_cusps,
            "angles": current_user.chart_angles,
            "aspects": current_user.planetary_aspects
        },
        "eastern_bazi": current_user.bazi_pillars
    }), 200

@auth_bp.route('/daily-forecast', methods=['GET'])
@token_required
def get_daily_forecast(current_user):
    """
    Computes active real-time planetary transits against the user's profile
    and fires it down the Groq LPU pipeline for a sub-second daily horoscope.
    """
    # 1. Mocking the current sky positions for testing purposes.
    # In a later step, we can hook this up to a live ephemeris scraper or Swiss Ephemeris wrapper.
    mock_current_sky = {
        "Mars": {"absolute_degree": 142.5},   # Moving through Leo
        "Mercury": {"absolute_degree": 54.1}, # Moving through Taurus, right over their natal Moon!
        "Sun": {"absolute_degree": 60.2}      # Moving through Gemini
    }

    # 2. Instantiate engines
    transit_calc = TransitEngine()
    interpreter = DynamicInterpretationEngine()

    # 3. Compute active intersections
    natal_planets = current_user.planetary_positions or {}
    active_transits = transit_calc.calculate_transit_aspects(natal_planets, mock_current_sky)

    # 4. Generate the reading
    daily_reading = interpreter.generate_daily_horoscope(current_user, active_transits)

    return jsonify({
        "status": "success",
        "date_today": "2026-05-21",
        "active_geometric_transits": active_transits,
        "daily_horoscope": daily_reading
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register_user():
    """
    Public registration endpoint to securely provision new user profiles
    into the database cluster.
    """
    from app.models.user import User
    from app import db

    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    # Validate inputs
    if not email or not password:
        return jsonify({"error": "Missing required email or password fields."}), 400

    # Check for existing user collisions
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email address already exists."}), 400

    try:
        new_user = User(email=email)
        new_user.set_password(password) # Automatically hashes the raw password
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "User account created successfully."
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create account due to a database exception."}), 500
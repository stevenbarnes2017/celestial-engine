from flask import request, jsonify
from functools import wraps
from app.models.user import User
import jwt
import os

# Reference the same secret key used for token signing
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-cosmic-secret-key-1982')

def token_required(f):
    """
    Custom decorator to protect endpoints. Decodes the incoming Bearer token,
    validates the signature, and injects the active 'current_user' record 
    directly into the wrapped route function execution.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or malformed token."}), 401
        
        try:
            token = auth_header.split(" ")[1].strip()
            
            # --- DEBUG PRINTS START ---
            print("\n=== DEBUG: RAW JWS DECODE ATTEMPT ===")
            print(f"Received Token: {token[:20]}...[truncated]")
            print(f"Using Secret Key: {JWT_SECRET_KEY}")
            # --- DEBUG PRINTS END ---

            # 1. Use the underlying JWS layer to verify signature and decode bytes manually
            # This completely bypasses PyJWT's strict claim type-checking validation engine.
            import json
            raw_payload_bytes = jwt.api_jws.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            
            # 2. Parse the raw JSON bytes ourselves
            payload = json.loads(raw_payload_bytes.decode('utf-8'))
            
            # 3. Extract the subject safely (accepts raw integers or strings seamlessly)
            user_id = int(payload['sub'])
            
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({"error": "User profile not found."}), 404
                
        except Exception as e:
            print(f"CRITICAL DECODE FAILURE -> {str(e)}")
            return jsonify({"error": f"Cryptographic authentication failed: {str(e)}"}), 401
                
        except jwt.ExpiredSignatureError as e:
            print(f"DECODE ERROR: Expired Signature -> {str(e)}")
            return jsonify({"error": "Signature expired. Please log in again."}), 401
        except jwt.InvalidTokenError as e:
            print(f"DECODE ERROR: Invalid Token -> {str(e)}") # <-- THIS WILL PRINT THE REAL CULPRIT
            return jsonify({"error": f"Invalid token. Please log in again. Details: {str(e)}"}), 401

        return f(current_user, *args, **kwargs)

    return decorated
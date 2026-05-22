from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash # <-- ADD THIS IMPORT

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    billing_status = db.Column(db.String(20), default='free_beta')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Core Birth Telemetry (Inputs)
    birth_date = db.Column(db.Date, nullable=False)
    birth_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Calculated Astronomical Profiles
    planetary_positions = db.Column(db.JSON, nullable=True)
    house_cusps = db.Column(db.JSON, nullable=True)
    chart_angles = db.Column(db.JSON, nullable=True)
    bazi_pillars = db.Column(db.JSON, nullable=True)
    planetary_aspects = db.Column(db.JSON, nullable=True)

    # --- ADD THESE PASSWORD METHODS AT THE BOTTOM OF THE CLASS ---
    # --- INSIDE YOUR USER CLASS IN user.py ---

    def set_password(self, password):
        """
        Forces Werkzeug to use PBKDF2 with SHA-256, generating a tight
        93-character hash string that safely fits a VARCHAR(128) column.
        """
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(
            password, 
            method='pbkdf2:sha256:600000', 
            salt_length=16
        )

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.email}>"
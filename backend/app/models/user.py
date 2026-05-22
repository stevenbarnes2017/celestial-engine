from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    billing_status = db.Column(db.String(20), default='free_beta')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Core Birth Telemetry (Inputs)
    birth_date = db.Column(db.Date, nullable=False)
    birth_time = db.Column(db.Time, nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Calculated Astronomical Profiles (Outputs stored as JSON blocks)
    planetary_positions = db.Column(db.JSON, nullable=True)
    house_cusps = db.Column(db.JSON, nullable=True)
    chart_angles = db.Column(db.JSON, nullable=True)
    bazi_pillars = db.Column(db.JSON, nullable=True)
    planetary_aspects = db.Column(db.JSON, nullable=True)  # <-- ADD THIS LINE

    def __repr__(self):
        return f"<User {self.email}>"
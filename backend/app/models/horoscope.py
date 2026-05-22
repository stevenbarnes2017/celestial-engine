from app import db

class HoroscopeCache(db.Model):
    __tablename__ = 'horoscope_cache'

    id = db.Column(db.Integer, primary_key=True)
    
    # Core lookup identifiers
    sign_name = db.Column(db.String(50), nullable=False)       # e.g., 'Pisces' or 'Horse'
    system_type = db.Column(db.String(20), nullable=False)     # 'western' or 'eastern'
    time_horizon = db.Column(db.String(20), nullable=False)    # 'daily', 'weekly', 'monthly', 'yearly'
    
    # The actual payload
    reading_text = db.Column(db.Text, nullable=False)          # The LLM generated text block
    
    # Idempotency / Expiration Management
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)        # The hard boundary timestamp

    def is_expired(self):
        """Checks if the current time has passed the validation window boundary."""
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<HoroscopeCache {self.system_type}:{self.sign_name} [{self.time_horizon}]>"
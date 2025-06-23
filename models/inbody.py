from . import db  # Import db from models/__init__.py
from datetime import datetime

class InBody(db.Model):
    __tablename__ = 'inbody_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(80), nullable=False) # Assuming user_id is a string, adjust if it's a foreign key to a users table
    weight = db.Column(db.Float, nullable=False)
    body_fat_percentage = db.Column(db.Float, nullable=True)
    muscle_mass = db.Column(db.Float, nullable=True)
    measurement_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<InBody {self.id} for user {self.user_id} on {self.measurement_date}>'

    def to_dict(self):
        """Serializes the InBody object to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'weight': self.weight,
            'body_fat_percentage': self.body_fat_percentage,
            'muscle_mass': self.muscle_mass,
            'measurement_date': self.measurement_date.isoformat() if self.measurement_date else None
        }

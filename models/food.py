from . import db  # Import db from models/__init__.py

class Food(db.Model):
    __tablename__ = 'food_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Food names should be unique
    calories = db.Column(db.Float, nullable=False) # Per serving or standard unit (e.g., 100g)
    protein = db.Column(db.Float, nullable=True) # In grams
    carbohydrates = db.Column(db.Float, nullable=True) # In grams
    fat = db.Column(db.Float, nullable=True) # In grams

    def __repr__(self):
        return f'<Food {self.name}>'

    def to_dict(self):
        """Serializes the Food object to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'calories': self.calories,
            'protein': self.protein,
            'carbohydrates': self.carbohydrates,
            'fat': self.fat
        }

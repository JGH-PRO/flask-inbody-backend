from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError # For handling potential DB errors
import datetime # For default timestamp

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://inbodyuser:inbodypassword@localhost:5432/inbodydb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the InBodyRecord model
class InBodyRecord(db.Model):
    __tablename__ = 'inbody_records' # Optional: specify table name

    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # Auto-incrementing primary key
    user_id = db.Column(db.String(80), nullable=False, index=True) # Added index for faster user lookups
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    weight_kg = db.Column(db.Float, nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    body_fat_percentage = db.Column(db.Float, nullable=False)
    skeletal_muscle_mass_kg = db.Column(db.Float, nullable=False)
    body_water_percentage = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<InBodyRecord id={self.id} user_id={self.user_id} timestamp={self.timestamp}>'

    # Add a method to convert model to dictionary, useful for JSON responses
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat() + 'Z', # ISO format with Z for UTC
            'weight_kg': self.weight_kg,
            'height_cm': self.height_cm,
            'body_fat_percentage': self.body_fat_percentage,
            'skeletal_muscle_mass_kg': self.skeletal_muscle_mass_kg,
            'body_water_percentage': self.body_water_percentage
        }

# In-memory data store - This will be removed/replaced by DB models
# inbody_data = {}

# Example:
# inbody_data = {
# "user123": [
# {
# "timestamp": "2023-10-27T10:00:00Z",
# "weight_kg": 70.5,
# "height_cm": 175.0,
# "body_fat_percentage": 15.2,
# "skeletal_muscle_mass_kg": 30.1,
# "body_water_percentage": 58.0
# },
# # ... more records for user123
# ]
# }
# import uuid # Not strictly needed now with DB auto-increment IDs

@app.route('/')
def hello():
    return "InBody API - Now with PostgreSQL!"

# CRUD operations will be refactored in a later step.
# For now, just ensure the app initializes with SQLAlchemy.

# Example: Add a temporary route to test DB connection (optional, can be removed later)
@app.route('/db_test')
def db_test():
    try:
        db.session.execute(text('SELECT 1'))
        return "Database connection successful!"
    except Exception as e:
        return f"Database connection failed: {str(e)}"

# CLI command to create database tables
@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    # Ensure this is called within app context, though @app.cli.command usually handles this.
    # For explicit safety, especially if called programmatically elsewhere:
    with app.app_context():
        db.create_all()
    print('Initialized the database.')

# === Refactored CRUD Operations ===

@app.route('/inbody/<string:user_id>', methods=['POST'])
def add_inbody_record(user_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid input, JSON data required"}), 400

    required_fields = ["timestamp", "weight_kg", "height_cm", "body_fat_percentage", "skeletal_muscle_mass_kg", "body_water_percentage"]
    if not all(field in data for field in required_fields):
        # More specific error about which fields are missing could be useful
        missing_fields = [field for field in required_fields if field not in data]
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    # Convert timestamp string to datetime object if it's a string
    # Assuming ISO format like "2023-10-28T10:00:00Z"
    try:
        timestamp_str = data['timestamp']
        if timestamp_str.endswith('Z'): # Python's fromisoformat doesn't like 'Z' before 3.11
            timestamp_str = timestamp_str[:-1] + '+00:00'
        record_timestamp = datetime.datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid timestamp format. Use ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."}), 400

    new_record = InBodyRecord(
        user_id=user_id,
        timestamp=record_timestamp,
        weight_kg=data['weight_kg'],
        height_cm=data['height_cm'],
        body_fat_percentage=data['body_fat_percentage'],
        skeletal_muscle_mass_kg=data['skeletal_muscle_mass_kg'],
        body_water_percentage=data['body_water_percentage']
    )

    try:
        db.session.add(new_record)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201
    except IntegrityError: # Catch potential DB errors, e.g., constraint violations
        db.session.rollback()
        return jsonify({"error": "Database integrity error. Check your input values."}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding record: {e}") # Log the error
        return jsonify({"error": "Could not save record to database."}), 500

@app.route('/inbody/<string:user_id>', methods=['GET'])
def get_inbody_records(user_id):
    records = InBodyRecord.query.filter_by(user_id=user_id).order_by(InBodyRecord.timestamp.desc()).all()
    if not records:
        # Return 200 with empty list if user exists but has no records, or 404 if user concept needs checking
        # For simplicity, we return empty list. If user must exist first, an additional check is needed.
        return jsonify([]), 200
    return jsonify([record.to_dict() for record in records]), 200

@app.route('/inbody/record/<int:record_id>', methods=['GET'])
def get_inbody_record_by_id(record_id):
    record = InBodyRecord.query.get(record_id)
    if record:
        return jsonify(record.to_dict()), 200
    else:
        return jsonify({"error": "Record not found"}), 404

@app.route('/inbody/record/<int:record_id>', methods=['PUT'])
def update_inbody_record_by_id(record_id):
    record = InBodyRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid input, JSON data required"}), 400

    # Update fields if they are provided in the request data
    if 'user_id' in data: # Allow changing user_id if necessary
        record.user_id = data['user_id']
    if 'timestamp' in data:
        try:
            timestamp_str = data['timestamp']
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            record.timestamp = datetime.datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid timestamp format"}), 400

    for field in ['weight_kg', 'height_cm', 'body_fat_percentage', 'skeletal_muscle_mass_kg', 'body_water_percentage']:
        if field in data:
            setattr(record, field, data[field])

    try:
        db.session.commit()
        return jsonify(record.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database integrity error during update."}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating record {record_id}: {e}")
        return jsonify({"error": "Could not update record in database."}), 500

@app.route('/inbody/record/<int:record_id>', methods=['DELETE'])
def delete_inbody_record_by_id(record_id):
    record = InBodyRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({"message": "Record deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting record {record_id}: {e}")
        return jsonify({"error": "Could not delete record from database."}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

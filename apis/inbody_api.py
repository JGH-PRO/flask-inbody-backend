from flask import Blueprint, jsonify, request
from app import db # Import db from the main app
from models.inbody import InBody # Import the InBody model
from datetime import datetime

inbody_bp = Blueprint('inbody_bp', __name__, url_prefix='/inbody') # Added url_prefix

# Create operation: Add new in-body information
@inbody_bp.route('', methods=['POST'])
def add_inbody_record():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    # Basic validation for required fields
    required_fields = ["user_id", "weight"] # measurement_date is default, others nullable
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: user_id, weight"}), 400

    try:
        new_record = InBody(
            user_id=data['user_id'],
            weight=float(data['weight']),
            body_fat_percentage=data.get('body_fat_percentage'),
            muscle_mass=data.get('muscle_mass'),
            # measurement_date is handled by default in model if not provided
            # If provided, it should be in ISO format.
            measurement_date=datetime.fromisoformat(data['measurement_date']) if data.get('measurement_date') else datetime.utcnow()
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201
    except ValueError as e: # Catches float conversion errors or date parsing errors
        db.session.rollback()
        return jsonify({"error": f"Invalid data format: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        # Log the exception e for debugging
        return jsonify({"error": "Could not process request"}), 500

# Read operation: Retrieve all in-body records for a specific user
@inbody_bp.route('/user/<string:user_id>', methods=['GET'])
def get_inbody_records_for_user(user_id):
    records = InBody.query.filter_by(user_id=user_id).order_by(InBody.measurement_date.desc()).all()
    if records:
        return jsonify([record.to_dict() for record in records]), 200
    else:
        # Return empty list if no records, not a 404, as the user might exist but have no records
        return jsonify([]), 200

# Read operation: Retrieve a specific in-body record by its ID
@inbody_bp.route('/<int:record_id>', methods=['GET'])
def get_inbody_record_by_id(record_id):
    record = InBody.query.get(record_id)
    if record:
        return jsonify(record.to_dict()), 200
    else:
        return jsonify({"error": "Record not found"}), 404

# Update operation: Update an existing in-body record by its ID
@inbody_bp.route('/<int:record_id>', methods=['PUT'])
def update_inbody_record(record_id):
    record = InBody.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        if 'user_id' in data: record.user_id = data['user_id']
        if 'weight' in data: record.weight = float(data['weight'])
        if 'body_fat_percentage' in data: record.body_fat_percentage = data.get('body_fat_percentage')
        if 'muscle_mass' in data: record.muscle_mass = data.get('muscle_mass')
        if 'measurement_date' in data: record.measurement_date = datetime.fromisoformat(data['measurement_date'])

        db.session.commit()
        return jsonify(record.to_dict()), 200
    except ValueError as e: # Catches float conversion errors or date parsing errors
        db.session.rollback()
        return jsonify({"error": f"Invalid data format: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({"error": "Could not update record"}), 500

# Delete operation: Delete a specific in-body record by its ID
@inbody_bp.route('/<int:record_id>', methods=['DELETE'])
def delete_inbody_record(record_id):
    record = InBody.query.get(record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404

    try:
        db.session.delete(record)
        db.session.commit()
        return jsonify({"message": "Record deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({"error": "Could not delete record"}), 500

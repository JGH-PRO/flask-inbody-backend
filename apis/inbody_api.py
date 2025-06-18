from flask import Blueprint, jsonify, request

inbody_bp = Blueprint('inbody_bp', __name__)

# In-memory data store
inbody_data = {}

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
# import uuid # For generating unique IDs for records if needed, though not used in this snippet

# Create operation: Add new in-body information for a user
@inbody_bp.route('/inbody/<string:user_id>', methods=['POST'])
def add_inbody_record(user_id):
    data = request.get_json(silent=True)
    if data is None: # Changed from "if not data"
        return jsonify({"error": "Invalid input"}), 400

    # Basic validation for required fields (can be expanded)
    required_fields = ["timestamp", "weight_kg", "height_cm", "body_fat_percentage", "skeletal_muscle_mass_kg", "body_water_percentage"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    if user_id not in inbody_data:
        inbody_data[user_id] = []

    # Potentially add a unique ID to each record if needed, e.g. data['record_id'] = str(uuid.uuid4())
    inbody_data[user_id].append(data)
    return jsonify({"message": "Record added successfully", "user_id": user_id, "record_index": len(inbody_data[user_id]) -1 }), 201

# Read operation: Retrieve all in-body records for a user
@inbody_bp.route('/inbody/<string:user_id>', methods=['GET'])
def get_inbody_records(user_id):
    if user_id in inbody_data:
        return jsonify(inbody_data[user_id]), 200
    else:
        return jsonify({"error": "User not found"}), 404

# Update operation: Update an existing in-body record for a user by its index
@inbody_bp.route('/inbody/<string:user_id>/<int:record_index>', methods=['PUT'])
def update_inbody_record(user_id, record_index):
    if user_id not in inbody_data:
        return jsonify({"error": "User not found"}), 404

    if record_index < 0 or record_index >= len(inbody_data[user_id]):
        return jsonify({"error": "Record not found"}), 404

    data = request.get_json(silent=True)
    if data is None: # Changed from "if not data"
        return jsonify({"error": "Invalid input"}), 400

    # Update the specific record. We can add more specific field validation here if needed.
    inbody_data[user_id][record_index].update(data)
    return jsonify({"message": "Record updated successfully", "user_id": user_id, "record_index": record_index}), 200

# Delete operation: Delete a specific in-body record for a user by its index
@inbody_bp.route('/inbody/<string:user_id>/<int:record_index>', methods=['DELETE'])
def delete_inbody_record(user_id, record_index):
    if user_id not in inbody_data:
        return jsonify({"error": "User not found"}), 404

    if record_index < 0 or record_index >= len(inbody_data[user_id]):
        return jsonify({"error": "Record not found or already deleted"}), 404

    deleted_record = inbody_data[user_id].pop(record_index)
    return jsonify({"message": "Record deleted successfully", "deleted_record": deleted_record}), 200

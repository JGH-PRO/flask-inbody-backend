from flask import Blueprint, jsonify, request

food_bp = Blueprint('food_bp', __name__)

# In-memory data store
food_data = {}

# Food Data CRUD Operations

# Create operation: Add new food information for a user
@food_bp.route('/food/<string:user_id>', methods=['POST'])
def add_food_record(user_id):
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid input"}), 400

    required_fields = ["food_type", "total_calories", "carbohydrate_g", "fat_g", "protein_g"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    if user_id not in food_data:
        food_data[user_id] = []

    food_data[user_id].append(data)
    return jsonify({"message": "Food record added successfully", "user_id": user_id, "record_index": len(food_data[user_id]) - 1}), 201


# Read operation: Retrieve all food records for a user
@food_bp.route('/food/<string:user_id>', methods=['GET'])
def get_food_records(user_id):
    if user_id not in food_data:
        return jsonify({"error": "User not found"}), 404

    records_with_ratios = []
    for record in food_data[user_id]:
        total_calories = record.get("total_calories")
        if total_calories and total_calories > 0:
            record["carbohydrate_ratio"] = (record.get("carbohydrate_g", 0) * 4) / total_calories
            record["fat_ratio"] = (record.get("fat_g", 0) * 9) / total_calories
            record["protein_ratio"] = (record.get("protein_g", 0) * 4) / total_calories
        else:
            record["carbohydrate_ratio"] = 0
            record["fat_ratio"] = 0
            record["protein_ratio"] = 0
        records_with_ratios.append(record)
    return jsonify(records_with_ratios), 200


# Read operation: Retrieve a specific food record for a user
@food_bp.route('/food/<string:user_id>/<int:record_index>', methods=['GET'])
def get_food_record(user_id, record_index):
    if user_id not in food_data:
        return jsonify({"error": "User not found"}), 404

    if record_index < 0 or record_index >= len(food_data[user_id]):
        return jsonify({"error": "Record not found"}), 404

    record = food_data[user_id][record_index]
    total_calories = record.get("total_calories")
    if total_calories and total_calories > 0:
        record["carbohydrate_ratio"] = (record.get("carbohydrate_g", 0) * 4) / total_calories
        record["fat_ratio"] = (record.get("fat_g", 0) * 9) / total_calories
        record["protein_ratio"] = (record.get("protein_g", 0) * 4) / total_calories
    else:
        record["carbohydrate_ratio"] = 0
        record["fat_ratio"] = 0
        record["protein_ratio"] = 0
    return jsonify(record), 200


# Update operation: Update an existing food record
@food_bp.route('/food/<string:user_id>/<int:record_index>', methods=['PUT'])
def update_food_record(user_id, record_index):
    if user_id not in food_data:
        return jsonify({"error": "User not found"}), 404

    if record_index < 0 or record_index >= len(food_data[user_id]):
        return jsonify({"error": "Record not found"}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid input"}), 400

    # Basic validation for field types (can be expanded)
    for field in ["total_calories", "carbohydrate_g", "fat_g", "protein_g"]:
        if field in data and not isinstance(data[field], (int, float)):
            return jsonify({"error": f"Invalid data type for {field}"}), 400

    food_data[user_id][record_index].update(data)
    return jsonify({"message": "Record updated successfully", "user_id": user_id, "record_index": record_index}), 200


# Delete operation: Delete a specific food record
@food_bp.route('/food/<string:user_id>/<int:record_index>', methods=['DELETE'])
def delete_food_record(user_id, record_index):
    if user_id not in food_data:
        return jsonify({"error": "User not found"}), 404

    if record_index < 0 or record_index >= len(food_data[user_id]):
        return jsonify({"error": "Record not found or already deleted"}), 404

    deleted_record = food_data[user_id].pop(record_index)
    return jsonify({"message": "Record deleted successfully", "deleted_record": deleted_record}), 200

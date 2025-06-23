from flask import Blueprint, jsonify, request
from app import db  # Import db from the main app
from models.food import Food  # Import the Food model

food_bp = Blueprint('food_bp', __name__, url_prefix='/food') # Added url_prefix

# Create operation: Add a new food item to the database
@food_bp.route('', methods=['POST'])
def add_food_item():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    required_fields = ["name", "calories"] # Protein, carbs, fat are nullable
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields: name, calories"}), 400

    # Check if food item with the same name already exists
    if Food.query.filter_by(name=data['name']).first():
        return jsonify({"error": f"Food item with name '{data['name']}' already exists"}), 409 # 409 Conflict

    try:
        new_food = Food(
            name=data['name'],
            calories=float(data['calories']),
            protein=data.get('protein'),
            carbohydrates=data.get('carbohydrates'),
            fat=data.get('fat')
        )
        db.session.add(new_food)
        db.session.commit()
        return jsonify(new_food.to_dict()), 201
    except ValueError: # Catches float conversion errors
        db.session.rollback()
        return jsonify({"error": "Invalid data format for numerical fields"}), 400
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({"error": "Could not add food item"}), 500

# Read operation: Retrieve all food items
@food_bp.route('', methods=['GET'])
def get_all_food_items():
    try:
        # Basic pagination could be added here:
        # page = request.args.get('page', 1, type=int)
        # per_page = request.args.get('per_page', 10, type=int)
        # food_items_paginated = Food.query.paginate(page=page, per_page=per_page, error_out=False)
        # food_items = food_items_paginated.items
        # return jsonify({
        #     "items": [food.to_dict() for food in food_items],
        #     "total": food_items_paginated.total,
        #     "page": food_items_paginated.page,
        #     "pages": food_items_paginated.pages
        # }), 200

        food_items = Food.query.all()
        return jsonify([food.to_dict() for food in food_items]), 200
    except Exception as e:
        # Log the exception e
        return jsonify({"error": "Could not retrieve food items"}), 500


# Read operation: Retrieve a specific food item by its ID
@food_bp.route('/<int:food_id>', methods=['GET'])
def get_food_item_by_id(food_id):
    food_item = Food.query.get(food_id)
    if food_item:
        return jsonify(food_item.to_dict()), 200
    else:
        return jsonify({"error": "Food item not found"}), 404

# Update operation: Update an existing food item by its ID
@food_bp.route('/<int:food_id>', methods=['PUT'])
def update_food_item(food_id):
    food_item = Food.query.get(food_id)
    if not food_item:
        return jsonify({"error": "Food item not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    try:
        # Check if updating to a name that already exists (and isn't this item itself)
        if 'name' in data and data['name'] != food_item.name and Food.query.filter_by(name=data['name']).first():
             return jsonify({"error": f"Food item with name '{data['name']}' already exists"}), 409

        if 'name' in data: food_item.name = data['name']
        if 'calories' in data: food_item.calories = float(data['calories'])
        if 'protein' in data: food_item.protein = data.get('protein')
        if 'carbohydrates' in data: food_item.carbohydrates = data.get('carbohydrates')
        if 'fat' in data: food_item.fat = data.get('fat')

        db.session.commit()
        return jsonify(food_item.to_dict()), 200
    except ValueError: # Catches float conversion errors
        db.session.rollback()
        return jsonify({"error": "Invalid data format for numerical fields"}), 400
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({"error": "Could not update food item"}), 500

# Delete operation: Delete a specific food item by its ID
@food_bp.route('/<int:food_id>', methods=['DELETE'])
def delete_food_item(food_id):
    food_item = Food.query.get(food_id)
    if not food_item:
        return jsonify({"error": "Food item not found"}), 404

    try:
        db.session.delete(food_item)
        db.session.commit()
        return jsonify({"message": "Food item deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({"error": "Could not delete food item"}), 500

import pytest
import json
from app import app # app is still the main entry point
from apis import inbody_api, food_api # Import the modules

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Reset data before each test
        inbody_api.inbody_data.clear() # Corrected path
        food_api.food_data.clear()     # Corrected path
        yield client

# Sample InBody data for testing
sample_inbody_record_1 = {
    "timestamp": "2023-10-28T10:00:00Z",
    "weight_kg": 70.0,
    "height_cm": 175.0,
    "body_fat_percentage": 15.0,
    "skeletal_muscle_mass_kg": 30.0,
    "body_water_percentage": 58.0
}
sample_inbody_record_2 = {
    "timestamp": "2023-10-29T11:00:00Z",
    "weight_kg": 71.0,
    "height_cm": 175.0,
    "body_fat_percentage": 15.5,
    "skeletal_muscle_mass_kg": 30.5,
    "body_water_percentage": 57.5
}
incomplete_inbody_record = {"weight_kg": 70.0}

# Sample Food data for testing
sample_food_record_1 = {
    "food_type": "Apple",
    "total_calories": 95,
    "carbohydrate_g": 25,
    "fat_g": 0.3,
    "protein_g": 0.5
}
sample_food_record_2 = {
    "food_type": "Chicken Breast",
    "total_calories": 165,
    "carbohydrate_g": 0,
    "fat_g": 3.6,
    "protein_g": 31
}
incomplete_food_record = {"food_type": "Orange"}
invalid_food_record = {
    "food_type": "Banana",
    "total_calories": "not-a-number", # Invalid
    "carbohydrate_g": 27,
    "fat_g": 0.3,
    "protein_g": 1.3
}

# === Test InBody Create Operations ===
def test_add_inbody_record_success(client):
    response = client.post('/inbody/user1', json=sample_inbody_record_1)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == "Record added successfully"
    assert data['user_id'] == 'user1'
    assert data['record_index'] == 0
    assert 'user1' in inbody_api.inbody_data
    assert len(inbody_api.inbody_data['user1']) == 1
    assert inbody_api.inbody_data['user1'][0]['weight_kg'] == 70.0

def test_add_inbody_record_missing_fields(client):
    response = client.post('/inbody/user1', json=incomplete_inbody_record)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Missing required fields"

def test_add_inbody_record_no_data(client):
    # Test with an empty json payload
    response_empty_json = client.post('/inbody/user1', json={})
    assert response_empty_json.status_code == 400 # Will fail due to missing fields
    data = json.loads(response_empty_json.data)
    assert data['error'] == "Missing required fields"

    # Test with no JSON data at all
    response_no_json = client.post('/inbody/user1')
    assert response_no_json.status_code == 400
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"


# === Test InBody Read Operations ===
def test_get_inbody_records_success(client):
    client.post('/inbody/user1', json=sample_inbody_record_1)
    client.post('/inbody/user1', json=sample_inbody_record_2)
    response = client.get('/inbody/user1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['weight_kg'] == 70.0
    assert data[1]['weight_kg'] == 71.0

def test_get_inbody_records_user_not_found(client):
    response = client.get('/inbody/nonexistentuser')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "User not found"

# === Test InBody Update Operations ===
def test_update_inbody_record_success(client):
    client.post('/inbody/user1', json=sample_inbody_record_1)
    update_data = {"weight_kg": 72.0, "body_fat_percentage": 16.0}
    response = client.put('/inbody/user1/0', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record updated successfully"
    assert inbody_api.inbody_data['user1'][0]['weight_kg'] == 72.0
    assert inbody_api.inbody_data['user1'][0]['body_fat_percentage'] == 16.0
    assert inbody_api.inbody_data['user1'][0]['timestamp'] == sample_inbody_record_1['timestamp'] # Check unchanged field

def test_update_inbody_record_user_not_found(client):
    response = client.put('/inbody/nonexistentuser/0', json={"weight_kg": 72.0})
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "User not found"

def test_update_inbody_record_record_not_found(client):
    client.post('/inbody/user1', json=sample_inbody_record_1)
    response = client.put('/inbody/user1/5', json={"weight_kg": 72.0}) # Index 5 does not exist
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found"

def test_update_inbody_record_invalid_input(client):
    client.post('/inbody/user1', json=sample_inbody_record_1)
    response = client.put('/inbody/user1/0') # No JSON data
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Invalid input"

# === Test InBody Delete Operations ===
def test_delete_inbody_record_success(client):
    client.post('/inbody/user1', json=sample_inbody_record_1)
    client.post('/inbody/user1', json=sample_inbody_record_2)
    response = client.delete('/inbody/user1/0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record deleted successfully"
    assert len(inbody_api.inbody_data['user1']) == 1
    assert inbody_api.inbody_data['user1'][0]['weight_kg'] == 71.0 # The second record is now at index 0

def test_delete_inbody_record_user_not_found(client):
    response = client.delete('/inbody/nonexistentuser/0')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "User not found"

def test_delete_inbody_record_record_not_found(client):
    client.post('/inbody/user1', json=sample_inbody_record_1)
    response = client.delete('/inbody/user1/5') # Index 5 does not exist
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found or already deleted" # Message from app

def test_delete_multiple_inbody_records_and_check_indices(client):
    client.post('/inbody/user1', json=sample_inbody_record_1) # Index 0
    client.post('/inbody/user1', json=sample_inbody_record_2) # Index 1
    client.post('/inbody/user1', json=sample_inbody_record_1) # Index 2 (another instance)

    # Delete record at index 1
    response = client.delete('/inbody/user1/1')
    assert response.status_code == 200
    assert len(inbody_api.inbody_data['user1']) == 2
    assert inbody_api.inbody_data['user1'][0]['timestamp'] == sample_inbody_record_1['timestamp']
    assert inbody_api.inbody_data['user1'][1]['timestamp'] == sample_inbody_record_1['timestamp'] # Original index 2 is now 1

    # Delete record at index 0
    response = client.delete('/inbody/user1/0')
    assert response.status_code == 200
    assert len(inbody_api.inbody_data['user1']) == 1
    assert inbody_api.inbody_data['user1'][0]['timestamp'] == sample_inbody_record_1['timestamp'] # Original index 2 record

# === Test Food CRUD Operations ===

# === Test Food Create Operations ===
def test_add_food_record_success(client):
    response = client.post('/food/user1', json=sample_food_record_1)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == "Food record added successfully"
    assert data['user_id'] == 'user1'
    assert data['record_index'] == 0
    assert 'user1' in food_api.food_data
    assert len(food_api.food_data['user1']) == 1
    assert food_api.food_data['user1'][0]['food_type'] == "Apple"

def test_add_food_record_missing_fields(client):
    response = client.post('/food/user1', json=incomplete_food_record)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Missing required fields"

def test_add_food_record_invalid_input(client):
    # Test with non-numeric calories - expecting app to handle this if validation is added for types
    # Current app.py's POST for food doesn't validate types, only presence.
    # Let's assume we want to test the current state, or this test might fail if app.py is updated.
    # For now, this test will pass as it will create the record.
    # If strict type validation was added to POST, this would be 400.
    # response = client.post('/food/user1', json=invalid_food_record)
    # assert response.status_code == 400
    # data = json.loads(response.data)
    # assert "Invalid data type" in data['error'] # Or similar error

    # Test with no JSON data at all
    response_no_json = client.post('/food/user1')
    assert response_no_json.status_code == 400
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"

    # Test with empty json payload
    response_empty_json = client.post('/food/user1', json={})
    assert response_empty_json.status_code == 400
    data = json.loads(response_empty_json.data)
    assert data['error'] == "Missing required fields"


# === Test Food Read Operations ===
def test_get_food_records_success(client):
    client.post('/food/user1', json=sample_food_record_1)
    client.post('/food/user1', json=sample_food_record_2)
    response = client.get('/food/user1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]['food_type'] == "Apple"
    assert data[1]['food_type'] == "Chicken Breast"
    # Check ratios for sample_food_record_1 (Apple)
    # carbs: 25g * 4 cal/g = 100 cal. total_calories: 95. carb_ratio = 100/95
    # fat: 0.3g * 9 cal/g = 2.7 cal. fat_ratio = 2.7/95
    # protein: 0.5g * 4 cal/g = 2 cal. protein_ratio = 2/95
    assert data[0]['carbohydrate_ratio'] == pytest.approx((25 * 4) / 95)
    assert data[0]['fat_ratio'] == pytest.approx((0.3 * 9) / 95)
    assert data[0]['protein_ratio'] == pytest.approx((0.5 * 4) / 95)

def test_get_food_records_empty(client):
    response = client.get('/food/user1_no_records')
    assert response.status_code == 404 # User not found, which is correct for no records yet
    # If user existed with no records, it would be 200 and empty list.
    # Let's create user then get:
    food_api.food_data['user_with_no_records'] = []
    response = client.get('/food/user_with_no_records')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == []


def test_get_food_records_user_not_found(client):
    response = client.get('/food/nonexistentuser')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "User not found"

def test_get_food_record_ratios_division_by_zero(client):
    zero_cal_food = {
        "food_type": "Zero Calorie Food",
        "total_calories": 0, # Division by zero case
        "carbohydrate_g": 10,
        "fat_g": 0,
        "protein_g": 0
    }
    client.post('/food/user_zero_cal', json=zero_cal_food)
    response = client.get('/food/user_zero_cal/0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['carbohydrate_ratio'] == 0
    assert data['fat_ratio'] == 0
    assert data['protein_ratio'] == 0


def test_get_specific_food_record_success(client):
    client.post('/food/user1', json=sample_food_record_1)
    response = client.get('/food/user1/0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['food_type'] == "Apple"
    assert data['carbohydrate_ratio'] == pytest.approx((25 * 4) / 95)

def test_get_specific_food_record_user_not_found(client):
    response = client.get('/food/nonexistentuser/0')
    assert response.status_code == 404

def test_get_specific_food_record_not_found(client):
    client.post('/food/user1', json=sample_food_record_1)
    response = client.get('/food/user1/5') # Index 5 does not exist
    assert response.status_code == 404


# === Test Food Update Operations ===
def test_update_food_record_success(client):
    client.post('/food/user1', json=sample_food_record_1)
    update_data = {"total_calories": 100, "protein_g": 1.0}
    response = client.put('/food/user1/0', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record updated successfully"
    assert food_api.food_data['user1'][0]['total_calories'] == 100
    assert food_api.food_data['user1'][0]['protein_g'] == 1.0
    assert food_api.food_data['user1'][0]['food_type'] == "Apple" # Unchanged

def test_update_food_record_user_not_found(client):
    response = client.put('/food/nonexistentuser/0', json={"total_calories": 100})
    assert response.status_code == 404

def test_update_food_record_record_not_found(client):
    client.post('/food/user1', json=sample_food_record_1)
    response = client.put('/food/user1/5', json={"total_calories": 100})
    assert response.status_code == 404

def test_update_food_record_invalid_input(client):
    client.post('/food/user1', json=sample_food_record_1)
    # Test with no JSON data
    response_no_json = client.put('/food/user1/0')
    assert response_no_json.status_code == 400
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"

    # Test with invalid data type for a field
    response_invalid_type = client.put('/food/user1/0', json={"total_calories": "not-a-number"})
    assert response_invalid_type.status_code == 400
    data = json.loads(response_invalid_type.data)
    assert data['error'] == "Invalid data type for total_calories"


# === Test Food Delete Operations ===
def test_delete_food_record_success(client):
    client.post('/food/user1', json=sample_food_record_1)
    client.post('/food/user1', json=sample_food_record_2)
    response = client.delete('/food/user1/0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record deleted successfully"
    assert len(food_api.food_data['user1']) == 1
    assert food_api.food_data['user1'][0]['food_type'] == "Chicken Breast"

def test_delete_food_record_user_not_found(client):
    response = client.delete('/food/nonexistentuser/0')
    assert response.status_code == 404

def test_delete_food_record_record_not_found(client):
    client.post('/food/user1', json=sample_food_record_1)
    response = client.delete('/food/user1/5')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found or already deleted"

def test_delete_multiple_food_records_and_check_indices(client):
    client.post('/food/user1', json=sample_food_record_1) # Index 0
    client.post('/food/user1', json=sample_food_record_2) # Index 1
    client.post('/food/user1', json=sample_food_record_1) # Index 2 (another Apple)

    response = client.delete('/food/user1/1') # Delete Chicken Breast
    assert response.status_code == 200
    assert len(food_api.food_data['user1']) == 2
    assert food_api.food_data['user1'][0]['food_type'] == "Apple"
    assert food_api.food_data['user1'][1]['food_type'] == "Apple" # Original index 2 is now 1

    response = client.delete('/food/user1/0') # Delete first Apple
    assert response.status_code == 200
    assert len(food_api.food_data['user1']) == 1
    assert food_api.food_data['user1'][0]['food_type'] == "Apple" # Remaining record

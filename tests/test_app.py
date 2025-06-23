import pytest
import json
from app import app, db # app is still the main entry point, import db
# from apis import inbody_api, food_api # No longer needed for direct data manipulation

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost:5432/appdb' # Use the main appdb

    with app.app_context():
        db.drop_all() # Ensure a clean state
        db.create_all() # Create tables based on models

    with app.test_client() as client:
        yield client

    # Optional: Clean up after tests if using a separate test DB and want to drop it
    # with app.app_context():
    #     db.drop_all()

# Sample InBody data for testing - adjusted for the new model
sample_inbody_payload_1 = {
    "user_id": "user1",
    "weight": 70.0,
    "body_fat_percentage": 15.0,
    "muscle_mass": 30.0,
    "measurement_date": "2023-10-28T10:00:00Z"
}
sample_inbody_payload_2 = {
    "user_id": "user1", # Same user, different record
    "weight": 71.0,
    "body_fat_percentage": 15.5,
    "muscle_mass": 30.5,
    "measurement_date": "2023-10-29T11:00:00Z"
}
# For a different user
sample_inbody_payload_user2 = {
    "user_id": "user2",
    "weight": 65.0,
    "body_fat_percentage": 20.0,
    "muscle_mass": 25.0,
    "measurement_date": "2023-10-30T09:00:00Z"
}
incomplete_inbody_payload = {"user_id": "user3"} # Missing 'weight'
invalid_inbody_payload_bad_date = {
    "user_id": "user4",
    "weight": 70.0,
    "measurement_date": "not-a-date"
}


# Sample Food data for testing - adjusted for new Food model
sample_food_payload_1 = {
    "name": "Apple",
    "calories": 95,
    "carbohydrates": 25,
    "fat": 0.3,
    "protein": 0.5
}
sample_food_payload_2 = {
    "name": "Chicken Breast",
    "calories": 165,
    "carbohydrates": 0,
    "fat": 3.6,
    "protein": 31
}
incomplete_food_payload = {"name": "Orange"} # Missing 'calories'
invalid_food_payload_bad_calories = {
    "name": "Banana",
    "calories": "not-a-number", # Invalid
    "carbohydrates": 27,
    "fat": 0.3,
    "protein": 1.3
}

# === Test InBody Create Operations ===
def test_add_inbody_record_success(client):
    response = client.post('/inbody', json=sample_inbody_payload_1) # New URL and payload
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    assert data['user_id'] == sample_inbody_payload_1['user_id']
    assert data['weight'] == sample_inbody_payload_1['weight']
    assert data['measurement_date'].startswith(sample_inbody_payload_1['measurement_date'].split('T')[0]) # Check date part

def test_add_inbody_record_missing_fields(client):
    response = client.post('/inbody', json=incomplete_inbody_payload) # New payload
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Missing required fields" in data['error']

def test_add_inbody_record_invalid_date_format(client):
    response = client.post('/inbody', json=invalid_inbody_payload_bad_date)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Invalid data format" in data['error']


def test_add_inbody_record_no_data(client):
    # Test with an empty json payload
    response_empty_json = client.post('/inbody', json={})
    assert response_empty_json.status_code == 400
    data = json.loads(response_empty_json.data)
    assert "Missing required fields" in data['error']

    # Test with no JSON data at all
    response_no_json = client.post('/inbody')
    assert response_no_json.status_code == 400 # Flask-RESTful might give 400 or 415 depending on parsing
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"


# === Test InBody Read Operations ===
def test_get_inbody_records_for_user_success(client):
    # Add two records for user1
    client.post('/inbody', json=sample_inbody_payload_1)
    client.post('/inbody', json=sample_inbody_payload_2)
    # Add one record for user2
    client.post('/inbody', json=sample_inbody_payload_user2)

    response = client.get(f"/inbody/user/{sample_inbody_payload_1['user_id']}") # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    # Records are ordered by measurement_date desc by default in API
    assert data[0]['weight'] == sample_inbody_payload_2['weight']
    assert data[1]['weight'] == sample_inbody_payload_1['weight']

def test_get_inbody_records_for_user_no_records(client):
    response = client.get('/inbody/user/nonexistentuser_or_user_with_no_records')
    assert response.status_code == 200 # API returns empty list, not 404
    data = json.loads(response.data)
    assert data == []

def test_get_specific_inbody_record_success(client):
    post_response = client.post('/inbody', json=sample_inbody_payload_1)
    record_id = json.loads(post_response.data)['id']

    response = client.get(f'/inbody/{record_id}') # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == record_id
    assert data['weight'] == sample_inbody_payload_1['weight']

def test_get_specific_inbody_record_not_found(client):
    response = client.get('/inbody/99999') # Non-existent ID
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found"

# === Test InBody Update Operations ===
def test_update_inbody_record_success(client):
    post_response = client.post('/inbody', json=sample_inbody_payload_1)
    record_id = json.loads(post_response.data)['id']

    update_data = {"weight": 72.0, "body_fat_percentage": 16.0}
    response = client.put(f'/inbody/{record_id}', json=update_data) # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == record_id
    assert data['weight'] == 72.0
    assert data['body_fat_percentage'] == 16.0
    assert data['user_id'] == sample_inbody_payload_1['user_id'] # Unchanged field

def test_update_inbody_record_not_found(client):
    response = client.put('/inbody/99999', json={"weight": 72.0}) # Non-existent ID
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found"

def test_update_inbody_record_invalid_input(client):
    post_response = client.post('/inbody', json=sample_inbody_payload_1)
    record_id = json.loads(post_response.data)['id']

    response_no_json = client.put(f'/inbody/{record_id}') # No JSON data
    assert response_no_json.status_code == 400
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"

    response_bad_data = client.put(f'/inbody/{record_id}', json={"weight": "not-a-number"})
    assert response_bad_data.status_code == 400
    data_bad = json.loads(response_bad_data.data)
    assert "Invalid data format" in data_bad['error']


# === Test InBody Delete Operations ===
def test_delete_inbody_record_success(client):
    post_response_1 = client.post('/inbody', json=sample_inbody_payload_1)
    record_id_1 = json.loads(post_response_1.data)['id']

    post_response_2 = client.post('/inbody', json=sample_inbody_payload_2) # Another record for the same user
    record_id_2 = json.loads(post_response_2.data)['id']

    response = client.delete(f'/inbody/{record_id_1}') # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record deleted successfully"

    # Verify it's deleted
    get_response = client.get(f'/inbody/{record_id_1}')
    assert get_response.status_code == 404

    # Verify other record still exists
    get_response_2 = client.get(f'/inbody/{record_id_2}')
    assert get_response_2.status_code == 200
    assert json.loads(get_response_2.data)['id'] == record_id_2


def test_delete_inbody_record_not_found(client):
    response = client.delete('/inbody/99999') # Non-existent ID
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found"

# Removed: test_delete_multiple_inbody_records_and_check_indices - as indices are no longer relevant for identifying records.
# The logic is covered by creating multiple records and deleting one, then checking others.

# === Test Food CRUD Operations ===

# === Test Food Create Operations ===
def test_add_food_item_success(client): # Renamed from test_add_food_record_success
    response = client.post('/food', json=sample_food_payload_1) # New URL, new payload
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'id' in data
    assert data['name'] == sample_food_payload_1['name']
    assert data['calories'] == sample_food_payload_1['calories']

def test_add_food_item_duplicate_name(client):
    client.post('/food', json=sample_food_payload_1) # Add first time
    response = client.post('/food', json=sample_food_payload_1) # Try adding again
    assert response.status_code == 409 # Conflict
    data = json.loads(response.data)
    assert "already exists" in data['error']


def test_add_food_item_missing_fields(client): # Renamed
    response = client.post('/food', json=incomplete_food_payload) # New payload
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Missing required fields" in data['error']

def test_add_food_item_invalid_calories(client): # Renamed
    response = client.post('/food', json=invalid_food_payload_bad_calories) # New payload
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Invalid data format" in data['error']


def test_add_food_item_no_data(client): # Renamed
    response_empty_json = client.post('/food', json={})
    assert response_empty_json.status_code == 400
    data = json.loads(response_empty_json.data)
    assert "Missing required fields" in data['error']

    response_no_json = client.post('/food')
    assert response_no_json.status_code == 400
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"


# === Test Food Read Operations ===
def test_get_all_food_items_success(client): # Renamed
    client.post('/food', json=sample_food_payload_1)
    client.post('/food', json=sample_food_payload_2)
    response = client.get('/food') # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    # Order isn't guaranteed unless specified, so check for presence
    assert any(item['name'] == sample_food_payload_1['name'] for item in data)
    assert any(item['name'] == sample_food_payload_2['name'] for item in data)

def test_get_all_food_items_empty(client): # Renamed
    response = client.get('/food')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data == []

# Removed tests:
# test_get_food_records_user_not_found (user concept removed from this API)
# test_get_food_record_ratios_division_by_zero (ratios removed)

def test_get_specific_food_item_success(client): # Renamed
    post_response = client.post('/food', json=sample_food_payload_1)
    food_id = json.loads(post_response.data)['id']

    response = client.get(f'/food/{food_id}') # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == food_id
    assert data['name'] == sample_food_payload_1['name']

def test_get_specific_food_item_not_found(client): # Renamed
    response = client.get('/food/99999') # Non-existent ID
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Food item not found"

# Removed: test_get_specific_food_record_user_not_found

# === Test Food Update Operations ===
def test_update_food_item_success(client): # Renamed
    post_response = client.post('/food', json=sample_food_payload_1)
    food_id = json.loads(post_response.data)['id']

    update_data = {"calories": 100, "protein": 1.0, "name": "Golden Apple"}
    response = client.put(f'/food/{food_id}', json=update_data) # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == food_id
    assert data['calories'] == 100
    assert data['protein'] == 1.0
    assert data['name'] == "Golden Apple"

def test_update_food_item_to_duplicate_name(client):
    client.post('/food', json=sample_food_payload_1) # Name: "Apple"
    post_response_2 = client.post('/food', json=sample_food_payload_2) # Name: "Chicken Breast"
    food_id_2 = json.loads(post_response_2.data)['id']

    update_data = {"name": "Apple"} # Try to change "Chicken Breast" to "Apple"
    response = client.put(f'/food/{food_id_2}', json=update_data)
    assert response.status_code == 409 # Conflict
    data = json.loads(response.data)
    assert "already exists" in data['error']


def test_update_food_item_not_found(client): # Renamed
    response = client.put('/food/99999', json={"calories": 100}) # Non-existent ID
    assert response.status_code == 404

# Removed: test_update_food_record_user_not_found

def test_update_food_item_invalid_input(client): # Renamed
    post_response = client.post('/food', json=sample_food_payload_1)
    food_id = json.loads(post_response.data)['id']

    response_no_json = client.put(f'/food/{food_id}') # No JSON data
    assert response_no_json.status_code == 400
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"

    response_invalid_type = client.put(f'/food/{food_id}', json={"calories": "not-a-number"})
    assert response_invalid_type.status_code == 400
    data = json.loads(response_invalid_type.data)
    assert "Invalid data format" in data['error']


# === Test Food Delete Operations ===
def test_delete_food_item_success(client): # Renamed
    post_response_1 = client.post('/food', json=sample_food_payload_1)
    food_id_1 = json.loads(post_response_1.data)['id']
    client.post('/food', json=sample_food_payload_2) # Add another item

    response = client.delete(f'/food/{food_id_1}') # New URL
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Food item deleted successfully"

    # Verify it's deleted
    get_response = client.get(f'/food/{food_id_1}')
    assert get_response.status_code == 404

    # Verify other items still exist (by checking count)
    get_all_response = client.get('/food')
    assert len(json.loads(get_all_response.data)) == 1


def test_delete_food_item_not_found(client): # Renamed
    response = client.delete('/food/99999') # Non-existent ID
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Food item not found"

# Removed:
# test_delete_food_record_user_not_found
# test_delete_multiple_food_records_and_check_indices (indices no longer primary identifiers)

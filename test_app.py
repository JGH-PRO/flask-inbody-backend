import pytest
import json
from app import app, inbody_data # Import your Flask app and the inbody_data store

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Reset data before each test
        inbody_data.clear()
        yield client

# Sample data for testing
sample_record_1 = {
    "timestamp": "2023-10-28T10:00:00Z",
    "weight_kg": 70.0,
    "height_cm": 175.0,
    "body_fat_percentage": 15.0,
    "skeletal_muscle_mass_kg": 30.0,
    "body_water_percentage": 58.0
}
sample_record_2 = {
    "timestamp": "2023-10-29T11:00:00Z",
    "weight_kg": 71.0,
    "height_cm": 175.0,
    "body_fat_percentage": 15.5,
    "skeletal_muscle_mass_kg": 30.5,
    "body_water_percentage": 57.5
}
incomplete_record = {"weight_kg": 70.0}

# === Test Create Operations ===
def test_add_inbody_record_success(client):
    response = client.post('/inbody/user1', json=sample_record_1)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == "Record added successfully"
    assert data['user_id'] == 'user1'
    assert data['record_index'] == 0
    assert 'user1' in inbody_data
    assert len(inbody_data['user1']) == 1
    assert inbody_data['user1'][0]['weight_kg'] == 70.0

def test_add_inbody_record_missing_fields(client):
    response = client.post('/inbody/user1', json=incomplete_record)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Missing required fields"

def test_add_inbody_record_no_data(client):
    response = client.post('/inbody/user1', data=json.dumps(sample_record_1)) # Not sending content_type='application/json'
    # Depending on Flask version and setup, this might be handled differently.
    # For this setup, request.get_json() will return None if content_type is not application/json
    # or if data is malformed. If data is None, our code returns 400.
    # If we send data without json=... or content_type, request.get_json(silent=True) would be None.
    # Let's test with an empty json payload
    response_empty_json = client.post('/inbody/user1', json={})
    assert response_empty_json.status_code == 400 # Will fail due to missing fields
    data = json.loads(response_empty_json.data)
    assert data['error'] == "Missing required fields"

    # Test with no JSON data at all
    response_no_json = client.post('/inbody/user1')
    assert response_no_json.status_code == 400
    data = json.loads(response_no_json.data)
    assert data['error'] == "Invalid input"


# === Test Read Operations ===
def test_get_inbody_records_success(client):
    client.post('/inbody/user1', json=sample_record_1)
    client.post('/inbody/user1', json=sample_record_2)
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

# === Test Update Operations ===
def test_update_inbody_record_success(client):
    client.post('/inbody/user1', json=sample_record_1)
    update_data = {"weight_kg": 72.0, "body_fat_percentage": 16.0}
    response = client.put('/inbody/user1/0', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record updated successfully"
    assert inbody_data['user1'][0]['weight_kg'] == 72.0
    assert inbody_data['user1'][0]['body_fat_percentage'] == 16.0
    assert inbody_data['user1'][0]['timestamp'] == sample_record_1['timestamp'] # Check unchanged field

def test_update_inbody_record_user_not_found(client):
    response = client.put('/inbody/nonexistentuser/0', json={"weight_kg": 72.0})
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "User not found"

def test_update_inbody_record_record_not_found(client):
    client.post('/inbody/user1', json=sample_record_1)
    response = client.put('/inbody/user1/5', json={"weight_kg": 72.0}) # Index 5 does not exist
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found"

def test_update_inbody_record_invalid_input(client):
    client.post('/inbody/user1', json=sample_record_1)
    response = client.put('/inbody/user1/0') # No JSON data
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['error'] == "Invalid input"

# === Test Delete Operations ===
def test_delete_inbody_record_success(client):
    client.post('/inbody/user1', json=sample_record_1)
    client.post('/inbody/user1', json=sample_record_2)
    response = client.delete('/inbody/user1/0')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record deleted successfully"
    assert len(inbody_data['user1']) == 1
    assert inbody_data['user1'][0]['weight_kg'] == 71.0 # The second record is now at index 0

def test_delete_inbody_record_user_not_found(client):
    response = client.delete('/inbody/nonexistentuser/0')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "User not found"

def test_delete_inbody_record_record_not_found(client):
    client.post('/inbody/user1', json=sample_record_1)
    response = client.delete('/inbody/user1/5') # Index 5 does not exist
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found or already deleted" # Message from app

def test_delete_multiple_records_and_check_indices(client):
    client.post('/inbody/user1', json=sample_record_1) # Index 0
    client.post('/inbody/user1', json=sample_record_2) # Index 1
    client.post('/inbody/user1', json=sample_record_1) # Index 2 (another instance)

    # Delete record at index 1
    response = client.delete('/inbody/user1/1')
    assert response.status_code == 200
    assert len(inbody_data['user1']) == 2
    assert inbody_data['user1'][0]['timestamp'] == sample_record_1['timestamp']
    assert inbody_data['user1'][1]['timestamp'] == sample_record_1['timestamp'] # Original index 2 is now 1

    # Delete record at index 0
    response = client.delete('/inbody/user1/0')
    assert response.status_code == 200
    assert len(inbody_data['user1']) == 1
    assert inbody_data['user1'][0]['timestamp'] == sample_record_1['timestamp'] # Original index 2 record

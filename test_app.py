import pytest
import json
import datetime
from app import app, db, InBodyRecord # Import db and InBodyRecord model

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Using localhost as docker run will map the port to the host
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://inbodyuser:inbodypassword@localhost:5432/inbodydb_test'

    with app.app_context(): # Ensure operations are within app context
        db.create_all() # Create tables for each test session

    with app.test_client() as client:
        yield client # Tests run here

    # Teardown: drop all tables to leave a clean state
    with app.app_context():
        db.session.remove() # Ensure session is properly closed
        db.drop_all()

# Sample data for testing - adjust timestamp format if needed by your app's parsing
# Using datetime objects for direct model creation in some tests, and strings for API calls
now_iso_str = datetime.datetime.utcnow().isoformat() + "Z"

sample_record_api_1 = {
    "timestamp": now_iso_str,
    "weight_kg": 70.0,
    "height_cm": 175.0,
    "body_fat_percentage": 15.0,
    "skeletal_muscle_mass_kg": 30.0,
    "body_water_percentage": 58.0
}

sample_record_api_2 = {
    "timestamp": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat() + "Z",
    "weight_kg": 71.0,
    "height_cm": 175.0,
    "body_fat_percentage": 15.5,
    "skeletal_muscle_mass_kg": 30.5,
    "body_water_percentage": 57.5
}

incomplete_record_api = {"weight_kg": 70.0}

# === Test Create Operations ===
def test_add_inbody_record_success(client):
    response = client.post('/inbody/user123', json=sample_record_api_1)
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['user_id'] == 'user123'
    assert data['weight_kg'] == sample_record_api_1['weight_kg']
    assert 'id' in data
    # Check if it's in the DB
    with app.app_context():
        record = InBodyRecord.query.get(data['id'])
        assert record is not None
        assert record.user_id == 'user123'

def test_add_inbody_record_missing_fields(client):
    response = client.post('/inbody/user123', json=incomplete_record_api)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Missing required fields" in data['error']

def test_add_inbody_record_invalid_timestamp(client):
    invalid_ts_record = sample_record_api_1.copy()
    invalid_ts_record['timestamp'] = "not-a-timestamp"
    response = client.post('/inbody/user123', json=invalid_ts_record)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Invalid timestamp format" in data['error']

# === Test Read Operations ===
def test_get_inbody_records_for_user_success(client):
    client.post('/inbody/user1', json=sample_record_api_1) # Record 1 for user1
    client.post('/inbody/user1', json=sample_record_api_2) # Record 2 for user1
    client.post('/inbody/user2', json=sample_record_api_1) # Record 1 for user2

    response = client.get('/inbody/user1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    # Records should be ordered by timestamp desc by default (as per app logic)
    assert data[0]['weight_kg'] == sample_record_api_2['weight_kg']
    assert data[1]['weight_kg'] == sample_record_api_1['weight_kg']

def test_get_inbody_records_for_user_no_records(client):
    response = client.get('/inbody/user_with_no_records')
    assert response.status_code == 200 # Returns empty list
    data = json.loads(response.data)
    assert data == []

def test_get_inbody_record_by_id_success(client):
    post_response = client.post('/inbody/user1', json=sample_record_api_1)
    record_id = json.loads(post_response.data)['id']

    response = client.get(f'/inbody/record/{record_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == record_id
    assert data['weight_kg'] == sample_record_api_1['weight_kg']

def test_get_inbody_record_by_id_not_found(client):
    response = client.get('/inbody/record/99999') # Non-existent ID
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['error'] == "Record not found"

# === Test Update Operations ===
def test_update_inbody_record_success(client):
    post_response = client.post('/inbody/user1', json=sample_record_api_1)
    record_id = json.loads(post_response.data)['id']

    update_data = {"weight_kg": 75.0, "body_fat_percentage": 18.0}
    response = client.put(f'/inbody/record/{record_id}', json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == record_id
    assert data['weight_kg'] == 75.0
    assert data['body_fat_percentage'] == 18.0

    # Verify in DB
    with app.app_context():
        record = InBodyRecord.query.get(record_id)
        assert record.weight_kg == 75.0

def test_update_inbody_record_not_found(client):
    response = client.put('/inbody/record/99999', json={"weight_kg": 75.0})
    assert response.status_code == 404

def test_update_inbody_record_invalid_timestamp(client):
    post_response = client.post('/inbody/user1', json=sample_record_api_1)
    record_id = json.loads(post_response.data)['id']
    update_data = {"timestamp": "invalid-date"}
    response = client.put(f'/inbody/record/{record_id}', json=update_data)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "Invalid timestamp format" in data['error']

# === Test Delete Operations ===
def test_delete_inbody_record_success(client):
    post_response = client.post('/inbody/user1', json=sample_record_api_1)
    record_id = json.loads(post_response.data)['id']

    response = client.delete(f'/inbody/record/{record_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == "Record deleted successfully"

    # Verify it's deleted from DB
    with app.app_context():
        record = InBodyRecord.query.get(record_id)
        assert record is None

def test_delete_inbody_record_not_found(client):
    response = client.delete('/inbody/record/99999')
    assert response.status_code == 404

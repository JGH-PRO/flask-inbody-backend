# Health Services API

This project provides API endpoints for InBody data and Food items. It uses Python, Flask, SQLAlchemy, and PostgreSQL.

## Prerequisites

*   Python 3.7+
*   Docker and Docker Compose
*   `pip` for installing Python packages

## Setup and Running the Application

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  **Set up the PostgreSQL Database with Docker:**
    Ensure Docker is running. Then, start the PostgreSQL container:
    ```bash
    docker-compose up -d
    ```
    This will start a PostgreSQL server on port 5432.
    *   Database Name: `appdb`
    *   Username: `user`
    *   Password: `password` (These are defaults from `docker-compose.yml`)

3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Flask Application:**
    ```bash
    python app.py
    ```
    The application will start, and `db.create_all()` will create the necessary database tables in the PostgreSQL database if they don't already exist.
    The API will be available at `http://localhost:5000`.

    *   InBody API endpoints are under `/inbody`.
    *   Food API endpoints are under `/food`.

## Running Tests

(Instructions for running tests would go here if tests specific to the new DB functionality were added. Currently, `tests/test_app.py` might need updates.)
To run existing tests (if any):
```bash
pytest
```

## Stopping the Database Container
To stop the PostgreSQL container:
```bash
docker-compose down
```
If you want to remove the data volume as well (all data will be lost):
```bash
docker-compose down -v
```

## Project Structure
```
.
├── apis/                 # Contains API Blueprints (food_api.py, inbody_api.py)
├── models/               # Contains SQLAlchemy database models (food.py, inbody.py)
├── tests/                # Contains test files
├── app.py                # Main Flask application file, initializes DB and registers blueprints
├── docker-compose.yml    # Docker Compose configuration for PostgreSQL
├── requirements.txt      # Python package dependencies
└── README.md             # This file
```

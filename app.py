from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# Blueprints will be imported after db is defined to avoid circular imports if they need db
# from apis.inbody_api import inbody_bp
# from apis.food_api import food_bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost:5432/appdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # silence the warning
db = SQLAlchemy(app) # db is now defined

# Now import blueprints
from apis.inbody_api import inbody_bp
from apis.food_api import food_bp

# Register Blueprints
app.register_blueprint(inbody_bp)
app.register_blueprint(food_bp)

@app.route('/')
def hello():
    # Changed the welcome message to be more generic
    return "Welcome to the Health Services API"

if __name__ == '__main__':
    with app.app_context():
        # This is a common place to create tables for development.
        # For production, migrations are preferred.
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

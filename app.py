from flask import Flask
from apis.inbody_api import inbody_bp
from apis.food_api import food_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(inbody_bp)
app.register_blueprint(food_bp)

@app.route('/')
def hello():
    return "InBody API" # Or a more generic welcome message like "Welcome to the API"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

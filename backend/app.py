from pathlib import Path
from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, jsonify
import os

from routes.goals import goals_bp
from routes.skills import skills_bp
from routes.applications import applications_bp

# Load the .env file from the backend folder.
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

app = Flask(__name__)
CORS(app, origins=[
    os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
])
app.register_blueprint(goals_bp)
app.register_blueprint(skills_bp)
app.register_blueprint(applications_bp)

# Health endpoint
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "message": "CareerTrack API is running"
    }), 200

# Start development server
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
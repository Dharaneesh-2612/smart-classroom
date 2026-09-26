from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = "classroom_data.json"


# ------------------------------------------
# Create database file if it doesn't exist
# ------------------------------------------

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as file:
        json.dump([], file)


# ------------------------------------------
# Save sensor data
# ------------------------------------------

def save_data(data):

    with open(DATA_FILE, "r") as file:
        records = json.load(file)

    records.append(data)

    # Keep latest 500 records
    records = records[-500:]

    with open(DATA_FILE, "w") as file:
        json.dump(records, file, indent=4)


# ------------------------------------------
# Dashboard
# ------------------------------------------

@app.route("/")
def dashboard():
    return render_template("index.html")


# ------------------------------------------
# ESP32 sends sensor data here
# ------------------------------------------

@app.route("/api/data", methods=["POST"])
def receive_data():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    data["timestamp"] = datetime.now().isoformat()

    save_data(data)

    print("\n========== ESP32 DATA ==========")
    print("Zone 1:", data.get("zone1"))
    print("Zone 2:", data.get("zone2"))
    print("Zone 3:", data.get("zone3"))
    print("Temperature:", data.get("temperature"))
    print("Humidity:", data.get("humidity"))
    print("Light 1:", data.get("light1"))
    print("Light 2:", data.get("light2"))
    print("Light 3:", data.get("light3"))
    print("Fan:", data.get("fan"))
    print("AC:", data.get("ac"))
    print("================================")

    return jsonify({
        "success": True,
        "message": "Data received successfully"
    })


# ------------------------------------------
# Get latest classroom data
# ------------------------------------------

@app.route("/api/data", methods=["GET"])
def get_data():

    with open(DATA_FILE, "r") as file:
        records = json.load(file)

    if len(records) == 0:
        return jsonify({
            "message": "No data available"
        })

    return jsonify(records[-1])


# ------------------------------------------
# Get all historical data
# ------------------------------------------

@app.route("/api/history", methods=["GET"])
def get_history():

    with open(DATA_FILE, "r") as file:
        records = json.load(file)

    return jsonify(records)


# ------------------------------------------
# Run server
# ------------------------------------------

if __name__ == "__main__":
    print("======================================")
    print("   SMART CLASSROOM PYTHON SERVER")
    print("======================================")
    print("Server running on port 5000")
    print("======================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
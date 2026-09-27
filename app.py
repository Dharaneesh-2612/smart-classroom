from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ==========================================
# SENSOR DATA STORAGE
# ==========================================

records = []

# ==========================================
# POWER CONFIGURATION
# ==========================================

LIGHT_POWER = 40
FAN_POWER = 75
AC_POWER = 1500

NUMBER_OF_LIGHTS = 3

MAX_POWER = (
    LIGHT_POWER * NUMBER_OF_LIGHTS
    + FAN_POWER
    + AC_POWER
)

ELECTRICITY_TARIFF = 8.0


# ==========================================
# MANUAL CONTROL
# ==========================================

manual_controls = {
    "light1": 0,
    "light2": 0,
    "light3": 0,
    "fan": 0,
    "ac": 0
}


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# RECEIVE ESP32 DATA
# ==========================================

@app.route("/api/data", methods=["POST"])
def receive_data():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400

    try:

        record = {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "zone1": int(data.get("zone1", 0)),
            "zone2": int(data.get("zone2", 0)),
            "zone3": int(data.get("zone3", 0)),

            "temperature": float(
                data.get("temperature", 0)
            ),

            "humidity": float(
                data.get("humidity", 0)
            ),

            "light1": int(data.get("light1", 0)),
            "light2": int(data.get("light2", 0)),
            "light3": int(data.get("light3", 0)),

            "fan": int(data.get("fan", 0)),
            "ac": int(data.get("ac", 0))
        }

        records.append(record)

        # Keep latest 500 records
        if len(records) > 500:
            records.pop(0)

        print()
        print("======================================")
        print("ESP32 DATA RECEIVED")
        print("======================================")
        print(record)

        return jsonify({
            "success": True,
            "message": "Data received successfully",
            "data": record
        })

    except Exception as e:

        print("Data error:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 400


# ==========================================
# GET LATEST DATA
# ==========================================

@app.route("/api/data", methods=["GET"])
def get_data():

    if not records:
        return jsonify({
            "success": True,
            "data": None
        })

    return jsonify({
        "success": True,
        "data": records[-1]
    })


# ==========================================
# GET HISTORY
# ==========================================

@app.route("/api/history", methods=["GET"])
def get_history():

    return jsonify({
        "success": True,
        "records": records
    })


# ==========================================
# ENERGY CALCULATION
# ==========================================

@app.route("/api/energy", methods=["GET"])
def get_energy():

    if not records:

        return jsonify({
            "average_power": 0,
            "current_power": 0,
            "energy_consumed_kwh": 0,
            "energy_saved_kwh": 0,
            "energy_saving_percentage": 0,
            "estimated_cost": 0,
            "maximum_possible_power": MAX_POWER,
            "maximum_power": 0,
            "minimum_power": 0,
            "electricity_tariff": ELECTRICITY_TARIFF,
            "total_records": 0
        })

    power_values = []

    for record in records:

        power = 0

        power += record["light1"] * LIGHT_POWER
        power += record["light2"] * LIGHT_POWER
        power += record["light3"] * LIGHT_POWER

        power += record["fan"] * FAN_POWER
        power += record["ac"] * AC_POWER

        power_values.append(power)

    current_power = power_values[-1]

    average_power = (
        sum(power_values) / len(power_values)
    )

    maximum_power = max(power_values)
    minimum_power = min(power_values)

    # Each ESP32 reading is approximately 5 seconds apart
    interval_hours = 5 / 3600

    energy_consumed_kwh = (
        sum(power_values)
        * interval_hours
        / 1000
    )

    energy_saved_kwh = (
        max(
            0,
            MAX_POWER * len(power_values)
            - sum(power_values)
        )
        * interval_hours
        / 1000
    )

    saving_percentage = 0

    if MAX_POWER > 0:

        saving_percentage = (
            energy_saved_kwh
            /
            (
                MAX_POWER
                * len(power_values)
                * interval_hours
                / 1000
            )
        ) * 100

    estimated_cost = (
        energy_consumed_kwh
        * ELECTRICITY_TARIFF
    )

    return jsonify({

        "average_power": round(
            average_power,
            2
        ),

        "current_power": round(
            current_power,
            2
        ),

        "energy_consumed_kwh": round(
            energy_consumed_kwh,
            4
        ),

        "energy_saved_kwh": round(
            energy_saved_kwh,
            4
        ),

        "energy_saving_percentage": round(
            saving_percentage,
            2
        ),

        "estimated_cost": round(
            estimated_cost,
            2
        ),

        "maximum_possible_power": MAX_POWER,

        "maximum_power": maximum_power,

        "minimum_power": minimum_power,

        "electricity_tariff":
            ELECTRICITY_TARIFF,

        "total_records":
            len(records)
    })


# ==========================================
# MANUAL CONTROL - POST
# ==========================================

@app.route("/api/control", methods=["POST"])
def manual_control():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "No control data received"
        }), 400

    device = data.get("device")
    state = data.get("state")

    # Check device
    if device not in manual_controls:

        return jsonify({
            "success": False,
            "message": "Invalid device"
        }), 400

    # Check state
    if state not in [0, 1]:

        return jsonify({
            "success": False,
            "message": "Invalid state"
        }), 400

    manual_controls[device] = state

    print()
    print("======================================")
    print("          MANUAL CONTROL")
    print("======================================")

    print("Device:", device)

    print(
        "State:",
        "ON" if state == 1 else "OFF"
    )

    print("======================================")

    return jsonify({

        "success": True,

        "device": device,

        "state": state,

        "message":
            device
            + " turned "
            + (
                "ON"
                if state == 1
                else "OFF"
            )
    })


# ==========================================
# MANUAL CONTROL - GET
# ==========================================

@app.route("/api/control", methods=["GET"])
def get_manual_control():

    return jsonify({

        "success": True,

        "controls": manual_controls
    })


# ==========================================
# RESET MANUAL CONTROLS
# ==========================================

@app.route("/api/control/reset", methods=["POST"])
def reset_manual_control():

    for device in manual_controls:

        manual_controls[device] = 0

    return jsonify({

        "success": True,

        "message":
            "All manual controls reset",

        "controls":
            manual_controls
    })


# ==========================================
# SERVER
# ==========================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
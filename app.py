from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =====================================================
# IN-MEMORY DATABASE
# =====================================================

records = []


# =====================================================
# POWER CALCULATION
# =====================================================

def calculate_power(data):

    # Estimated appliance power
    LIGHT_POWER = 40       # W per light
    FAN_POWER = 75         # W
    AC_POWER = 1500        # W

    light1 = int(data.get("light1", 0))
    light2 = int(data.get("light2", 0))
    light3 = int(data.get("light3", 0))
    fan = int(data.get("fan", 0))
    ac = int(data.get("ac", 0))

    light_power = (
        light1 * LIGHT_POWER +
        light2 * LIGHT_POWER +
        light3 * LIGHT_POWER
    )

    fan_power = fan * FAN_POWER

    ac_power = ac * AC_POWER

    total_power = (
        light_power +
        fan_power +
        ac_power
    )

    return {
        "light_power": light_power,
        "fan_power": fan_power,
        "ac_power": ac_power,
        "total_power": total_power
    }


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
def dashboard():
    return render_template("index.html")


# =====================================================
# RECEIVE ESP32 DATA
# =====================================================

@app.route("/api/data", methods=["POST"])
def receive_data():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "No data received"
        }), 400


    # -------------------------------------------------
    # TIMESTAMP
    # -------------------------------------------------

    data["timestamp"] = datetime.now().isoformat()


    # -------------------------------------------------
    # POWER
    # -------------------------------------------------

    power = calculate_power(data)

    data["light_power"] = power["light_power"]
    data["fan_power"] = power["fan_power"]
    data["ac_power"] = power["ac_power"]
    data["total_power"] = power["total_power"]


    # -------------------------------------------------
    # OCCUPANCY
    # -------------------------------------------------

    zone1 = int(data.get("zone1", 0))
    zone2 = int(data.get("zone2", 0))
    zone3 = int(data.get("zone3", 0))

    human_present = (
        zone1 == 1 or
        zone2 == 1 or
        zone3 == 1
    )

    data["occupancy"] = (
        "OCCUPIED"
        if human_present
        else "EMPTY"
    )


    # -------------------------------------------------
    # ENERGY SAVING
    # -------------------------------------------------

    data["energy_saving_active"] = not human_present


    # -------------------------------------------------
    # SAVE RECORD
    # -------------------------------------------------

    records.append(data)

    # Keep latest 500 records
    if len(records) > 500:
        records.pop(0)


    # -------------------------------------------------
    # TERMINAL
    # -------------------------------------------------

    print()
    print("======================================")
    print("       ESP32 DATA RECEIVED")
    print("======================================")

    print("Zone 1:", zone1)
    print("Zone 2:", zone2)
    print("Zone 3:", zone3)

    print("Temperature:",
          data.get("temperature"))

    print("Humidity:",
          data.get("humidity"))

    print("Light 1:",
          data.get("light1"))

    print("Light 2:",
          data.get("light2"))

    print("Light 3:",
          data.get("light3"))

    print("Fan:",
          data.get("fan"))

    print("AC:",
          data.get("ac"))

    print()
    print("Light Power:",
          data["light_power"], "W")

    print("Fan Power:",
          data["fan_power"], "W")

    print("AC Power:",
          data["ac_power"], "W")

    print("TOTAL POWER:",
          data["total_power"], "W")

    print()
    print("Occupancy:",
          data["occupancy"])

    print("Energy Saving:",
          "ACTIVE"
          if data["energy_saving_active"]
          else "INACTIVE")

    print("Records stored:",
          len(records))

    print("======================================")


    return jsonify({
        "success": True,
        "message": "Data received successfully",
        "power": power,
        "occupancy": data["occupancy"],
        "energy_saving_active":
            data["energy_saving_active"]
    })


# =====================================================
# GET LATEST DATA
# =====================================================

@app.route("/api/data", methods=["GET"])
def get_data():

    if len(records) == 0:

        return jsonify({
            "message": "No data available"
        })


    return jsonify(records[-1])


# =====================================================
# GET HISTORY
# =====================================================

@app.route("/api/history", methods=["GET"])
def get_history():

    return jsonify(records)


# =====================================================
# ENERGY SUMMARY
# =====================================================

@app.route("/api/energy", methods=["GET"])
def energy_summary():

    if len(records) == 0:

        return jsonify({
            "total_records": 0,
            "current_power": 0,
            "average_power": 0,
            "maximum_power": 0,
            "minimum_power": 0
        })


    power_values = []

    for record in records:

        power = float(
            record.get("total_power", 0)
        )

        power_values.append(power)


    current_power = power_values[-1]

    average_power = (
        sum(power_values) /
        len(power_values)
    )

    maximum_power = max(power_values)

    minimum_power = min(power_values)


    return jsonify({

        "total_records":
            len(records),

        "current_power":
            current_power,

        "average_power":
            round(average_power, 2),

        "maximum_power":
            maximum_power,

        "minimum_power":
            minimum_power
    })


# =====================================================
# SERVER
# =====================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("      SMART CLASSROOM SERVER")
    print("======================================")

    print("Server running on port 5000")

    print("======================================")


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =====================================================
# DATA STORAGE
# =====================================================

records = []


# =====================================================
# POWER SETTINGS
# =====================================================

LIGHT_POWER = 40       # Watts per light
FAN_POWER = 75         # Watts
AC_POWER = 1500        # Watts

NUMBER_OF_LIGHTS = 3

MAX_POWER = (
    (LIGHT_POWER * NUMBER_OF_LIGHTS)
    + FAN_POWER
    + AC_POWER
)

# Prototype electricity tariff
# Change this to your actual tariff later
ELECTRICITY_TARIFF = 8.0   # ₹ per kWh


# =====================================================
# CALCULATE CURRENT POWER
# =====================================================

def calculate_power(data):

    light1 = int(data.get("light1", 0))
    light2 = int(data.get("light2", 0))
    light3 = int(data.get("light3", 0))

    fan = int(data.get("fan", 0))
    ac = int(data.get("ac", 0))


    # Light power
    light_power = (
        (light1 + light2 + light3)
        * LIGHT_POWER
    )


    # Fan power
    fan_power = fan * FAN_POWER


    # AC power
    ac_power = ac * AC_POWER


    # Total instantaneous power
    total_power = (
        light_power
        + fan_power
        + ac_power
    )


    return {
        "light_power": light_power,
        "fan_power": fan_power,
        "ac_power": ac_power,
        "total_power": total_power
    }


# =====================================================
# CALCULATE ENERGY FROM RECORDS
# =====================================================

def calculate_energy():

    if len(records) < 2:

        return {
            "energy_consumed_kwh": 0,
            "energy_saved_kwh": 0,
            "estimated_cost": 0,
            "energy_saving_percentage": 0
        }


    consumed_wh = 0
    saved_wh = 0


    for i in range(1, len(records)):

        previous = records[i - 1]
        current = records[i]


        # ---------------------------------------------
        # Time difference
        # ---------------------------------------------

        try:

            previous_time = datetime.fromisoformat(
                previous["timestamp"]
            )

            current_time = datetime.fromisoformat(
                current["timestamp"]
            )

            seconds = (
                current_time - previous_time
            ).total_seconds()

        except Exception:

            seconds = 5


        # Prevent abnormal time intervals
        if seconds <= 0 or seconds > 300:
            seconds = 5


        hours = seconds / 3600


        # ---------------------------------------------
        # Current power
        # ---------------------------------------------

        current_power = float(
            current.get("total_power", 0)
        )


        # ---------------------------------------------
        # Energy actually consumed
        # ---------------------------------------------

        consumed_wh += (
            current_power * hours
        )


        # ---------------------------------------------
        # Energy that would have been consumed
        # if maximum equipment was continuously ON
        # ---------------------------------------------

        saved_power = max(
            0,
            MAX_POWER - current_power
        )


        saved_wh += (
            saved_power * hours
        )


    # Convert Wh → kWh

    consumed_kwh = (
        consumed_wh / 1000
    )

    saved_kwh = (
        saved_wh / 1000
    )


    # Estimated electricity cost

    estimated_cost = (
        consumed_kwh
        * ELECTRICITY_TARIFF
    )


    # Saving percentage

    total_possible_energy = (
        consumed_kwh + saved_kwh
    )


    if total_possible_energy > 0:

        saving_percentage = (
            saved_kwh
            / total_possible_energy
        ) * 100

    else:

        saving_percentage = 0


    return {

        "energy_consumed_kwh":
            round(consumed_kwh, 4),

        "energy_saved_kwh":
            round(saved_kwh, 4),

        "estimated_cost":
            round(estimated_cost, 2),

        "energy_saving_percentage":
            round(saving_percentage, 2)
    }


# =====================================================
# CLASSROOM DASHBOARD
# =====================================================

@app.route("/")
def dashboard():

    return render_template(
        "index.html"
    )


# =====================================================
# RECEIVE ESP32 DATA
# =====================================================

@app.route(
    "/api/data",
    methods=["POST"]
)
def receive_data():

    data = request.get_json()


    # ---------------------------------------------
    # Validate data
    # ---------------------------------------------

    if not data:

        return jsonify({

            "success": False,

            "message":
                "No data received"

        }), 400


    # ---------------------------------------------
    # Timestamp
    # ---------------------------------------------

    data["timestamp"] = (
        datetime.now().isoformat()
    )


    # ---------------------------------------------
    # Calculate power
    # ---------------------------------------------

    power = calculate_power(
        data
    )


    data["light_power"] = (
        power["light_power"]
    )

    data["fan_power"] = (
        power["fan_power"]
    )

    data["ac_power"] = (
        power["ac_power"]
    )

    data["total_power"] = (
        power["total_power"]
    )


    # ---------------------------------------------
    # Occupancy
    # ---------------------------------------------

    zone1 = int(
        data.get("zone1", 0)
    )

    zone2 = int(
        data.get("zone2", 0)
    )

    zone3 = int(
        data.get("zone3", 0)
    )


    human_present = (
        zone1 == 1
        or zone2 == 1
        or zone3 == 1
    )


    if human_present:

        data["occupancy"] = "OCCUPIED"

        data["energy_saving_active"] = False

    else:

        data["occupancy"] = "EMPTY"

        data["energy_saving_active"] = True


    # ---------------------------------------------
    # Store record
    # ---------------------------------------------

    records.append(data)


    # Keep latest 500 records

    if len(records) > 500:

        records.pop(0)


    # ---------------------------------------------
    # Calculate energy
    # ---------------------------------------------

    energy = calculate_energy()


    # ---------------------------------------------
    # Print information
    # ---------------------------------------------

    print()
    print("======================================")
    print("       SMART CLASSROOM DATA")
    print("======================================")

    print(
        "Temperature:",
        data.get("temperature"),
        "°C"
    )

    print(
        "Humidity:",
        data.get("humidity"),
        "%"
    )

    print(
        "Zone 1:",
        zone1
    )

    print(
        "Zone 2:",
        zone2
    )

    print(
        "Zone 3:",
        zone3
    )

    print(
        "Light 1:",
        data.get("light1")
    )

    print(
        "Light 2:",
        data.get("light2")
    )

    print(
        "Light 3:",
        data.get("light3")
    )

    print(
        "Fan:",
        data.get("fan")
    )

    print(
        "AC:",
        data.get("ac")
    )

    print(
        "Current Power:",
        data["total_power"],
        "W"
    )

    print(
        "Energy Consumed:",
        energy["energy_consumed_kwh"],
        "kWh"
    )

    print(
        "Energy Saved:",
        energy["energy_saved_kwh"],
        "kWh"
    )

    print(
        "Estimated Cost: ₹",
        energy["estimated_cost"]
    )

    print(
        "Energy Saving:",
        energy["energy_saving_percentage"],
        "%"
    )

    print(
        "Occupancy:",
        data["occupancy"]
    )

    print(
        "Total Records:",
        len(records)
    )

    print(
        "======================================"
    )


    # ---------------------------------------------
    # Response
    # ---------------------------------------------

    return jsonify({

        "success": True,

        "message":
            "Data received successfully",

        "power": power,

        "energy": energy,

        "occupancy":
            data["occupancy"],

        "energy_saving_active":
            data["energy_saving_active"]

    })


# =====================================================
# GET LATEST DATA
# =====================================================

@app.route(
    "/api/data",
    methods=["GET"]
)
def get_data():

    if len(records) == 0:

        return jsonify({

            "message":
                "No data available"

        })


    latest = records[-1]


    # Add current energy information

    energy = calculate_energy()


    response = dict(latest)


    response["energy_consumed_kwh"] = (
        energy["energy_consumed_kwh"]
    )

    response["energy_saved_kwh"] = (
        energy["energy_saved_kwh"]
    )

    response["estimated_cost"] = (
        energy["estimated_cost"]
    )

    response["energy_saving_percentage"] = (
        energy["energy_saving_percentage"]
    )

    response["maximum_possible_power"] = (
        MAX_POWER
    )


    return jsonify(response)


# =====================================================
# GET HISTORY
# =====================================================

@app.route(
    "/api/history",
    methods=["GET"]
)
def get_history():

    return jsonify(records)


# =====================================================
# ENERGY SUMMARY
# =====================================================

@app.route(
    "/api/energy",
    methods=["GET"]
)
def energy_summary():

    energy = calculate_energy()


    if len(records) == 0:

        return jsonify({

            "total_records": 0,

            "current_power": 0,

            "average_power": 0,

            "maximum_power": 0,

            "minimum_power": 0,

            "energy_consumed_kwh": 0,

            "energy_saved_kwh": 0,

            "estimated_cost": 0,

            "energy_saving_percentage": 0,

            "maximum_possible_power":
                MAX_POWER,

            "electricity_tariff":
                ELECTRICITY_TARIFF

        })


    # ---------------------------------------------
    # Power values
    # ---------------------------------------------

    power_values = [

        float(
            record.get(
                "total_power",
                0
            )
        )

        for record in records

    ]


    return jsonify({

        "total_records":
            len(records),

        "current_power":
            power_values[-1],

        "average_power":
            round(
                sum(power_values)
                / len(power_values),
                2
            ),

        "maximum_power":
            max(power_values),

        "minimum_power":
            min(power_values),

        "energy_consumed_kwh":
            energy[
                "energy_consumed_kwh"
            ],

        "energy_saved_kwh":
            energy[
                "energy_saved_kwh"
            ],

        "estimated_cost":
            energy[
                "estimated_cost"
            ],

        "energy_saving_percentage":
            energy[
                "energy_saving_percentage"
            ],

        "maximum_possible_power":
            MAX_POWER,

        "electricity_tariff":
            ELECTRICITY_TARIFF

    })


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
from flask import Flask, request, jsonify, render_template_string
import sqlite3
import psutil
from datetime import datetime

app = Flask(__name__)
DATABASE = "traffic.db"


def create_database():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            time TEXT,
            vehicles INTEGER,
            prediction TEXT,
            created_at TEXT
        )
    """)
    connection.commit()
    connection.close()


def predict_traffic(vehicles):
    if vehicles < 300:
        return "Low"
    elif vehicles < 700:
        return "Medium"
    else:
        return "High"


@app.route("/")
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Traffic Prediction System</title>
        <style>
            body {
                font-family: Arial;
                background: #f2f2f2;
                text-align: center;
                padding: 30px;
            }
            .container {
                background: white;
                max-width: 600px;
                margin: auto;
                padding: 30px;
                border-radius: 15px;
            }
            input {
                width: 90%;
                padding: 12px;
                margin: 8px;
                border-radius: 6px;
                border: 1px solid #ccc;
            }
            button {
                padding: 12px 25px;
                background: #222;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
            }
            .system {
                margin-top: 25px;
                background: #eee;
                padding: 15px;
                border-radius: 10px;
            }
            #result {
                margin-top: 20px;
                font-size: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Traffic Prediction System</h1>
            <input id="location" placeholder="Enter Location">
            <input id="time" placeholder="Enter Time (Example: 18:00)">
            <input id="vehicles" type="number" min="0"
                   placeholder="Number of Vehicles">
            <br>
            <button onclick="predictTraffic()">Predict Traffic</button>
            <div id="result"></div>

            <div class="system">
                <h2>OS / System Information</h2>
                <p id="cpu">CPU: Loading...</p>
                <p id="memory">Memory: Loading...</p>
                <p id="process">Processes: Loading...</p>
                <p>Server: Running</p>
            </div>
        </div>

        <script>
            async function predictTraffic() {
                const location = document.getElementById("location").value;
                const time = document.getElementById("time").value;
                const vehicles = document.getElementById("vehicles").value;

                if (!location || !time || vehicles === "" || Number(vehicles) < 0) {
                    document.getElementById("result").innerText =
                        "Please enter location, time, and a valid vehicle count.";
                    return;
                }

                const response = await fetch("/predict", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({
                        location: location,
                        time: time,
                        vehicles: vehicles
                    })
                });

                const data = await response.json();
                if (!response.ok) {
                    document.getElementById("result").innerText =
                        data.error || "Could not predict traffic.";
                    return;
                }

                document.getElementById("result").innerHTML =
                    "Location: " + data.location +
                    "<br>Time: " + data.time +
                    "<br>Vehicles: " + data.vehicles +
                    "<br>Prediction: " + data.traffic_prediction;
            }

            async function systemInfo() {
                try {
                    const response = await fetch("/system");
                    const data = await response.json();
                    document.getElementById("cpu").innerText =
                        "CPU Usage: " + data.cpu_usage + "%";
                    document.getElementById("memory").innerText =
                        "Memory Usage: " + data.memory_usage + "%";
                    document.getElementById("process").innerText =
                        "Running Processes: " + data.processes;
                } catch (error) {
                    document.getElementById("cpu").innerText =
                        "System information unavailable";
                }
            }

            setInterval(systemInfo, 2000);
            systemInfo();
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}

    location = str(data.get("location", "Unknown")).strip() or "Unknown"
    time_value = str(data.get("time", "Unknown")).strip() or "Unknown"

    try:
        vehicles = int(data.get("vehicles", 0))
        if vehicles < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Vehicle count must be a non-negative whole number."}), 400

    prediction = predict_traffic(vehicles)

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO traffic_data
        (location, time, vehicles, prediction, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        location,
        time_value,
        vehicles,
        prediction,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    connection.commit()
    connection.close()

    return jsonify({
        "location": location,
        "time": time_value,
        "vehicles": vehicles,
        "traffic_prediction": prediction
    })


@app.route("/system")
def system_info():
    return jsonify({
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "processes": len(psutil.pids())
    })


@app.route("/records")
def records():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM traffic_data ORDER BY id DESC")
    data = cursor.fetchall()
    connection.close()
    return jsonify(data)


if __name__ == "__main__":
    create_database()
    print("TRAFFIC PREDICTION SYSTEM")
    print("Backend + Database + OS")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True)

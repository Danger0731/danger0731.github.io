from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# API URLs
STOP_URL = "https://data.etabus.gov.hk/v1/transport/kmb/stop"
ETA_URL = "https://data.etabus.gov.hk/v1/transport/kmb/stop-eta/{}"

def fetch_stop_data():
    """Fetch stop data from the API."""
    response = requests.get(STOP_URL)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

def fetch_eta(stop_id):
    """Fetch ETA data for a given stop ID."""
    response = requests.get(ETA_URL.format(stop_id))
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

def calculate_countdown(eta_time):
    """Convert ETA timestamp into a countdown."""
    try:
        eta_dt = datetime.strptime(eta_time, "%Y-%m-%dT%H:%M:%S%z")
        current_time = datetime.now(eta_dt.tzinfo)
        countdown = eta_dt - current_time
        minutes, seconds = divmod(countdown.total_seconds(), 60)
        return f"{int(minutes)} min {int(seconds)} sec"
    except Exception:
        return "ETA unavailable"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/search_stop", methods=["GET"])
def search_stop():
    query = request.args.get("query", "").lower()
    stops = fetch_stop_data()
    results = [stop for stop in stops if query in stop.get("name_en", "").lower()]
    return jsonify(results)

@app.route("/get_routes", methods=["GET"])
def get_routes():
    stop_id = request.args.get("stop_id")
    eta_data = fetch_eta(stop_id)
    available_routes = sorted(set((entry["route"], entry["dest_en"]) for entry in eta_data)) if eta_data else []
    return jsonify(available_routes)

@app.route("/get_eta", methods=["GET"])
def get_eta():
    stop_id = request.args.get("stop_id")
    route_number = request.args.get("route_number")
    eta_data = fetch_eta(stop_id)
    eta_entries = [entry for entry in eta_data if entry["route"] == route_number]

    for entry in eta_entries:
        entry["countdown"] = calculate_countdown(entry.get("eta"))
        entry["remarks"] = entry.get("rmk_en", "No remarks")

    return jsonify(eta_entries)

if __name__ == "__main__":
    app.run(debug=True)
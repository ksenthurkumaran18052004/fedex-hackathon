
from flask import Flask, render_template, request, jsonify
import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# OPEN_WEATHER_API_KEY = "01fecea7c070babba3ef42c3cb86c9c2"
# TOMTOM_API_KEY = "C9sIdQTP5usyf5ljhEkh3jyK6vsblkED"
# GOOGLE_API_KEY = "AIzaSyCtG6ml7N5iNN6cPKOz5li8mjewsNxSiH0"

# Load API keys from environment variables
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")
TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def get_weather_forecast(lat, lon):
    try:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPEN_WEATHER_API_KEY}&units=metric"
        weather_response = requests.get(weather_url).json()

        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_API_KEY}"
        geocode_response = requests.get(geocode_url).json()
        city_name = "Unknown Location"
        if geocode_response["status"] == "OK" and geocode_response["results"]:
            city_name = geocode_response["results"][0]["formatted_address"]

        weather_description = weather_response.get("weather", [{}])[0].get("description", "Unknown")
        return {"location": city_name, "weather": weather_description}
    except Exception as e:
        return {"location": "Error", "weather": str(e)}

def get_traffic_data(origin, destination):
    url = f"https://api.tomtom.com/routing/1/calculateRoute/{origin}:{destination}/json?traffic=true&key={TOMTOM_API_KEY}"
    response = requests.get(url)
    try:
        if response.status_code == 200:
            return response.json().get("routes", [])
        else:
            return []
    except Exception as e:
        return {"error": str(e)}

def get_location_name(lat, lon):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLE_API_KEY}"
        response = requests.get(url).json()
        if response["status"] == "OK" and response["results"]:
            return response["results"][0]["formatted_address"]
        return "Unknown Location"
    except Exception as e:
        return "Error Fetching Location"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/optimize", methods=["POST"])
def optimize():
    try:
        data = request.json
        origin = data["origin"]
        destination = data["destination"]
        fuel_efficiency = float(data["fuel_efficiency"])
        emission_factor = float(data["emission_factor"])

        traffic_data = get_traffic_data(
            f"{origin['lat']},{origin['lng']}",
            f"{destination['lat']},{destination['lng']}"
        )
        if not traffic_data:
            return jsonify({"error": "No traffic data available"})

        routes = []
        for idx, route in enumerate(traffic_data[:3]): 
            route_summary = route.get("summary", {})
            distance_km = route_summary.get("lengthInMeters", 0) / 1000
            duration_sec = route_summary.get("travelTimeInSeconds", 0)
            traffic_delay = route_summary.get("trafficDelayInSeconds", 0)
            emissions = (distance_km / fuel_efficiency) * emission_factor

            route_points = [{"latitude": point["latitude"], "longitude": point["longitude"]}
                            for leg in route.get("legs", [])
                            for point in leg.get("points", [])]

            traffic_locations = [get_location_name(point["latitude"], point["longitude"]) for point in route_points[::100]]

            weather_data = [get_weather_forecast(point["latitude"], point["longitude"]) for point in route_points[::100]]

            routes.append({
                "route_index": idx + 1,
                "distance": f"{distance_km:.2f} km",
                "duration": f"{duration_sec // 3600} hours {duration_sec % 3600 // 60} mins",
                "traffic_delay": f"{traffic_delay // 60} mins" if traffic_delay > 0 else "No delay",
                "emissions": f"{emissions:.2f} kg CO2",
                "traffic_locations": traffic_locations[:5],  
                "weather_data": weather_data,
                "route_points": route_points 
            })

        return jsonify({"routes": routes})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)

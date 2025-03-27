from flask import Flask, render_template, request
import requests
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Replace with your ORS API key
ORS_API_KEY = "5b3ce3597851110001cf624882e76173985f4cfaa6282130d090ef18"  # Replace with your actual key

def geocode_address(address):
    """Convert an address to coordinates using ORS Geocoding API, restricted to India."""
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": ORS_API_KEY,
        "text": address,
        "boundary.country": "IND"  # Restrict to India
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data["features"]:
            coords = data["features"][0]["geometry"]["coordinates"]  # [lon, lat]
            logger.debug(f"Geocoded {address} to {coords}")
            return coords
        else:
            logger.error(f"No coordinates found for {address}. Response: {data}")
            raise ValueError(f"No coordinates found for {address}")
    except requests.RequestException as e:
        error_detail = e.response.text if e.response else str(e)
        logger.error(f"Geocoding error for {address}: {error_detail}")
        raise ValueError(f"Geocoding failed: {error_detail}")

def get_route(depot, deliveries):
    """Calculate a one-way route using ORS Directions API."""
    # Geocode depot and deliveries
    coordinates = [geocode_address(depot)]
    for delivery in deliveries:
        if delivery:
            coordinates.append(geocode_address(delivery))
    # No round-trip: do not append depot again

    url = "https://api.openrouteservice.org/v2/directions/driving-car/json"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "coordinates": coordinates,
        "geometry": True,
        "instructions": False,
        "units": "m"
    }
    
    logger.debug(f"Sending payload to ORS Directions: {payload}")
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        logger.debug(f"ORS Directions Response: {data}")
        
        if "routes" not in data or not data["routes"]:
            raise ValueError("No routes found in response")
        
        route = data["routes"][0]
        total_dist = route["summary"]["distance"] / 1000  # Convert meters to km
        geometry = route["geometry"]  # Encoded polyline
        co2_emissions = total_dist * 0.2  # 0.2 kg CO2 per km
        
        # Log geometry for debugging
        logger.debug(f"Route Geometry: {geometry}")
        
        return {
            "total_dist": total_dist,
            "geometry": geometry,
            "co2_emissions": co2_emissions,
            "coords": coordinates
        }
    except requests.RequestException as e:
        error_detail = e.response.text if e.response else str(e)
        logger.error(f"Route calculation error: {error_detail}")
        raise ValueError(f"API error: {error_detail}")
    except KeyError as e:
        logger.error(f"Invalid response format: {str(e)}")
        raise ValueError(f"Invalid response format: {str(e)}")

@app.route("/", methods=["GET", "POST"])
def index():
    sample_data = {
        "depot": "Chennai International Airport, Chennai, India",
        "deliveries": [
            "Guindy Railway Station, Chennai, India",
            "Phoenix MarketCity, Chennai, India",
            "", "", ""
        ]
    }

    if request.method == "POST":
        depot = request.form.get("depot")
        deliveries = [request.form.get(f"delivery_{i}") for i in range(1, 6)]
        deliveries = [d for d in deliveries if d]  # Filter out empty deliveries

        if not depot:
            return render_template("index.html", error="Depot address is required", **sample_data)
        if not deliveries:
            return render_template("index.html", error="At least one delivery address is required", **sample_data)

        try:
            route_data = get_route(depot, deliveries)
            return render_template(
                "result.html",
                total_dist=round(route_data["total_dist"], 2),
                co2_emissions=round(route_data["co2_emissions"], 2),
                geometry=route_data["geometry"],
                coords=route_data["coords"],
                ors_api_key=ORS_API_KEY
            )
        except ValueError as e:
            return render_template("index.html", error=str(e), **sample_data)

    return render_template("index.html", **sample_data)

if __name__ == "__main__":
    app.run(debug=True)
import requests
import json # You'll need this to handle the response body later if you want to inspect it

from flask import Blueprint, jsonify, send_from_directory, redirect, request
# Assuming these imports are correct for your project
from helpers import get_high_risk_asteroid_data, format_results_to_dictionary, get_palermo_leaderboard, get_vi_data
from orbit import orbital_elements_to_3d_points # Your orbital calculation function

# Initialize Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# for those who don't know: Blueprint url prefix makes it so
# to access this route you need to go: http://host/api/neo_data/
# this is similar for all other api.routes due to the url_prefix parameter
@api.route('/neo_data/', methods=['POST'])
def neo_data():
    content = request.json

    if content is None:
        return jsonify({"error": "Missing or invalid JSON body"}), 400
    
    #ip_min = content.get('ip_min')
    #approach_date = content.get('approach_date')
    limit = content.get('limit') or 10
    data = get_high_risk_asteroid_data(limit)
    data_dict = format_results_to_dictionary(data[0])
    
    print( jsonify({'data': data_dict, 'list_of_des': data[1]}))

    return jsonify({'data': data_dict, 'list_of_des': data[1]})
    # parse the content for key info: filters, api to request

@api.route('/vi_data/')
def vi_data():
    des = request.args.get('des')
    if not des:
        return {'error': 'Must include \'des\' argument'}, 400
    
    result = None
    for i in range(5):
        try:
            result = get_vi_data(des)
            break
        except Exception as e:
            print(f'Exception Occured {e}')
            print("Retrying...")
    
    if not result:
        return {'error': 'Exceptions occurred, check stdout for more info'}, 400
    
    return jsonify(result)


@api.route('/neo_data_test/<limit>')
def neo_data_test(limit: int):
    limit = int(limit)
    data = get_high_risk_asteroid_data(limit)
    data_dict = format_results_to_dictionary(data[0])
    #print( jsonify({'data': data_dict, 'list_of_des': data[1]}))
    return jsonify({'data': data_dict, 'list_of_des': data[1]})

# Define the six required Keplerian element short names
# We'll map the NASA API names to their commonly used names for clarity
KEPLERIAN_ELEMENTS = {
    'e': 'e',       # Eccentricity
    'a': 'a_au',    # Semi-major axis (in AU)
    'i': 'i_deg',   # Inclination (degrees)
    'om': 'RAAN_deg', # Longitude of Ascending Node (Omega)
    'w': 'argp_deg',  # Argument of Perihelion (omega)
    'tp': 'tp'      # Time of Perihelion Passage (used for mean anomaly/position)
}

# The endpoint used by the frontend to fetch orbits
@api.route('/get_neo_orbits/', methods=['GET']) 
def get_neo_orbits():
    """
    Fetches Keplerian orbital elements for a list of designations,
    calculates their 3D orbit points, and returns data for Three.js.
    
    Expects a query string like: /api/get_neo_orbits/?des=Eros&des=Vesta
    
    Returns:
        JSON array: [{semiMajorAxis: ..., eccentricity: ..., orbitPoints: [...]}, ...]
    """
    
    # --- 1. Get List of Designations ---
    list_of_des = request.args.getlist('des')
    if not list_of_des:
        # Example: if the client calls /api/neo_data/ first, they get the DES list from there
        return {'error': f'No list of designations (\'des\') given in query parameters.'}, 400
    
    # --- 2. API Setup ---
    API_URL = 'https://ssd-api.jpl.nasa.gov/sbdb.api'
    results_for_frontend = []
    
    # --- 3. Process Each Designation ---
    for des in list_of_des:
        params = {'des': des, 'full': 'true'} # 'full=true' often ensures all elements are present

        try:
            # API Call
            response = requests.get(API_URL, params=params)
            response.raise_for_status() 
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {des}: {e}")
            # Skip this object and continue with the next
            continue 

        # --- 4. Data Extraction and Calculation ---
        try:
            all_elements = data.get("orbit", {}).get("elements", [])
            extracted_params = {}

            # Extract and map the required orbital elements
            for el in all_elements:
                name = el.get("name")
                if name in KEPLERIAN_ELEMENTS:
                    # Convert value to float immediately
                    extracted_params[KEPLERIAN_ELEMENTS[name]] = float(el.get("value"))
            
            # Ensure all required elements for calculation are present
            required_keys = ['a_au', 'e', 'i_deg', 'RAAN_deg', 'argp_deg']
            if not all(key in extracted_params for key in required_keys):
                print(f"Skipping {des}: Missing required orbital elements.")
                continue

            # Calculate 3D orbit points using your Python script
            orbit_points = orbital_elements_to_3d_points(
                    a_au = extracted_params['a_au'], 
                    e = extracted_params['e'], 
                    i_deg = extracted_params['i_deg'], 
                    RAAN_deg = extracted_params['RAAN_deg'], 
                    argp_deg = extracted_params['argp_deg'],
            )
            
            # --- 5. Format Output for Three.js Frontend ---
            neo_data_for_threejs = {
                "designation": des,
                "semiMajorAxis": extracted_params['a_au'],
                "eccentricity": extracted_params['e'],
                # Mean longitude (L) calculation requires Time of Perihelion (tp) 
                # and current time, which is complex. For static orbits, we just use a placeholder
                # or calculate the mean anomaly (M0) from 'tp' if a reference date is available.
                # Since you only need the orbit line now, we prioritize that.
                "orbitPoints": orbit_points 
            }
            
            results_for_frontend.append(neo_data_for_threejs)

        except Exception as e:
            print(f"Error processing data for {des}: {e}")
            continue # Continue to the next designation

    # --- 6. Return Final JSON Array ---
    return jsonify(results_for_frontend)
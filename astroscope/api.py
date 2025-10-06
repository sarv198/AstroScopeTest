import requests

from flask import Blueprint, jsonify, send_from_directory, redirect, request
from helpers import get_high_risk_asteroid_data, format_results_to_dictionary, get_palermo_leaderboard, get_vi_data
import json
# from orbit import orbital_elements_to_3d_points  # No longer needed


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
KEPLERIAN_ELEMENTS = ['e', 'a', 'i', 'om', 'w', 'tp']

@api.route('/orbital_params/', methods=['GET']) 
def get_orbital_params():
    """
    Retrieves the six Keplerian orbital elements for a given designation (des).

    Args:
        des (str): The object's designation (e.g., 'Eros', '2001 FO32').
    
    Returns:
        dict: A dictionary containing the orbital parameters (a, e, i, omega, varpi, MO).
    """
    
    # --- API Call ---
    # The 'des' query parameter is required to specify the asteroid/NEO.
    API_URL = 'https://ssd-api.jpl.nasa.gov/sbdb.api'
    list_of_des = request.args.getlist('des')
    if not list_of_des:
        return {'error': f'No list of des given'}, 400
    
    full_response = {}
    for des in list_of_des:
        
        params = {'des': des}


        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
            data = response.json()
        except requests.exceptions.RequestException as e:
            # Handle API connection or HTTP errors
            return {"error": f"API request failed: {e}"}

        # --- Data Extraction and Filtering ---

        try:
            # data["orbit"]["elements"] is a list of dictionaries, where each dict is an element.
            
            all_elements = data.get("orbit", {}).get("elements", [])
            print(all_elements)
            keplerian_params = {}
            # Iterate through all available elements in the API response
            for el in all_elements:
                name = el.get("name")
                
                # Check if the element is one of the six required Keplerian parameters
                if name in KEPLERIAN_ELEMENTS:
                    # Store the full details (value, label, units)
                    print(name)
                    keplerian_params[name] = float(el.get("value"))

            # Return the orbital parameters directly instead of converting to 3D points
            orbital_params = {
                'a': keplerian_params['a'],      # Semi-major axis
                'e': keplerian_params['e'],      # Eccentricity
                'i': keplerian_params['i'],      # Inclination
                'Omega': keplerian_params['om'], # Longitude of ascending node (RAAN)
                'varpi': keplerian_params['w'],  # Argument of periapsis
                'MO': keplerian_params['tp']     # Mean anomaly at epoch
            }
            print(orbital_params) # for testing
            full_response[des] = orbital_params


        except Exception as e:
            return {"error": f"Error parsing API response: {e}"}, 400
    #print(full_response)
    return jsonify(full_response)

@api.route('/combined_orbital_data/', methods=['POST'])
def combined_orbital_data():
    """
    Handles a single request to get high-risk asteroid designations (des) 
    and their corresponding Keplerian orbital parameters.

    The client posts a JSON body to this endpoint, similar to /neo_data/.
    It then internally calls the logic for /neo_data/ and /orbital_params/.
    """
    
    # 1. Get initial data (including list of 'des') from the request body
    content = request.json
    if content is None:
        return jsonify({"error": "Missing or invalid JSON body"}), 400
    
    limit = content.get('limit') or 10
    
    # Use existing helper function to get the base data
    try:
        data_tuple = get_high_risk_asteroid_data(limit)
        # data_tuple[0] is the list of high-risk NEO data
        # data_tuple[1] is the list of designations (des)
        list_of_des = data_tuple[1]
    except Exception as e:
        return jsonify({"error": f"Error fetching high-risk asteroid data: {e}"}), 500

    if not list_of_des:
        return jsonify({'data': {}, 'list_of_des': []}), 200 # Return empty but successful

    # 2. Fetch Orbital Parameters for all 'des' (Logic from get_orbital_params)
    
    API_URL = 'https://ssd-api.jpl.nasa.gov/sbdb.api'
    KEPLERIAN_ELEMENTS = ['e', 'a', 'i', 'om', 'w', 'tp']
    full_orbital_response = {}

    for des in list_of_des:
        params = {'des': des}

        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status() 
            data = response.json()
        except requests.exceptions.RequestException as e:
            # Note: We continue if one fails, but log the error
            print(f"Warning: API request failed for {des}: {e}")
            continue # Skip to the next designation

        # --- Data Extraction and Filtering ---
        try:
            all_elements = data.get("orbit", {}).get("elements", [])
            keplerian_params = {}
            for el in all_elements:
                name = el.get("name")
                if name in KEPLERIAN_ELEMENTS:
                    # Store the float value
                    keplerian_params[name] = float(el.get("value"))

            # Format the required parameters
            orbital_params = {
                'a': keplerian_params.get('a'),      # Semi-major axis
                'e': keplerian_params.get('e'),      # Eccentricity
                'i': keplerian_params.get('i'),      # Inclination
                'Omega': keplerian_params.get('om'), # Longitude of ascending node (RAAN)
                'varpi': keplerian_params.get('w'),  # Argument of periapsis
                'MO': keplerian_params.get('tp')     # Mean anomaly at epoch
            }
            # Add to the master dictionary, keyed by designation
            full_orbital_response[des] = orbital_params

        except Exception as e:
            print(f"Warning: Error parsing API response for {des}: {e}")
            continue # Skip to the next designation

    # 3. Combine and Return the final result
    
    # We return the list of des and the map of orbital params
    return jsonify({
        'list_of_des': list_of_des,
        'orbital_data': full_orbital_response 
    })

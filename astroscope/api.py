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

# ... (all your existing API code) ...


# ... (all your existing imports and API routes) ...

# ----------------------------------------------------------------------
#                         TEST FUNCTION ADDED HERE (UPDATED)
# ----------------------------------------------------------------------

def test_get_orbital_params():
    """
    1. Fetches a list of high-risk asteroid designations using the helper function.
    2. Simulates a client request to /api/orbital_params/ using that list.
    3. Prints the resulting orbital parameters for all objects.
    """
    
    print("\n" + "="*50)
    print("--- Running Test: get_orbital_params (Full Workflow) ---")
    
    # 1. Get the list of designations (Simulating the first step of /api/neo_data/)
    TEST_LIMIT = 5  # Fetch the top 5 high-risk NEOs
    try:
        data, list_of_des = get_high_risk_asteroid_data(TEST_LIMIT)
        print(f"Retrieved {len(list_of_des)} designations: {list_of_des}")
    except Exception as e:
        print(f"❌ TEST FAILED at designation retrieval: {e}")
        print("="*50 + "\n")
        return
    
    # 2. Correctly mock the Flask request object to handle request.args.getlist('des')
    class RequestMock:
        def __init__(self, des_list):
            self.des_list = des_list
            self.args = self # Mock object acts as 'request.args'
        
        def getlist(self, key):
            if key == 'des':
                return self.des_list
            return []

    # Temporarily replace the global request object
    global request
    original_request = request 
    
    # Pass the retrieved list of designations to the mock request
    request = RequestMock(list_of_des)
    
    # 3. Call the actual route handler function
    try:
        response = get_orbital_params()
        
        # Determine if the handler returned the tuple (response, status_code) or just the response
        if isinstance(response, tuple):
             data_response = response[0]
             status_code = response[1]
        else:
             data_response = response
             status_code = 200 

        if status_code != 200:
             print(f"\n❌ TEST FAILED - HTTP Status: {status_code}")
             # data_response is a dict if an error occurred
             print(f"Error Details: {data_response}")
        else:
            # data_response is a Flask Response object from jsonify(), extract the JSON bytes
            json_data = json.loads(data_response.data.decode('utf-8'))
            print("\n✅ TEST PASSED - Successfully retrieved all orbital parameters:")
            # Use json.dumps for pretty printing the resulting dictionary
            print(json.dumps(json_data, indent=4))
            
    except Exception as e:
        print(f"\n❌ TEST FAILED - Unhandled exception during orbital params call: {e}")
        
    finally:
        # 4. Restore the original request object
        request = original_request 
        print("="*50 + "\n")


# ----------------------------------------------------------------------
# Execution 
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # Make sure this is in your main application file's entry point 
    # if api.py is a blueprint, or here if api.py is the main script.
    
    test_get_orbital_params() 
    
    # ... your Flask app run command would follow here ...

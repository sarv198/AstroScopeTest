from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import requests

app = Flask(__name__)
CORS(app)

@app.route("/api/hello")
def hello_world():
    return jsonify({'message': "Hello World"})

@app.route('/api/neo')
def neo_data():
    content = request.json
    # parse the content for key info: filters, api to request
    # ...
    
    # use the nasa_api.py
    # TODO: Implement NEO data retrieval logic
    
    return jsonify({'data': 'NEO data endpoint - implementation needed'})

# Define the six required Keplerian element short names
KEPLERIAN_ELEMENTS = ['e', 'a', 'i', 'om', 'w', 'tp']
API_URL = 'https://ssd-api.jpl.nasa.gov/sbdb.api'

# Note: The @app.route decorator implies a web framework (like Flask/Django). 
# This completed function provides the necessary data retrieval logic.
@app.route('/orbital_params/<string:des>', methods=['GET']) 
def get_orbital_params(des):
    """
    Retrieves the six Keplerian orbital elements for a given designation (des).

    Args:
        des (str): The object's designation (e.g., 'Eros', '2001 FO32').
    
    Returns:
        dict: A dictionary containing the filtered orbital parameters.
    """
    
    # --- API Call ---
    # The 'des' query parameter is required to specify the asteroid/NEO.
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
        
        keplerian_params = {}
        # Iterate through all available elements in the API response
        for el in all_elements:
            name = el.get("name")
            
            # Check if the element is one of the six required Keplerian parameters
            if name in KEPLERIAN_ELEMENTS:
                # Store the full details (value, label, units)
                keplerian_params[name] = {
                    "value": el.get("value"),
                    "label": el.get("label"),
                    "units": el.get("units")
                }

        # Original list comprehension requested in the prompt (adapted to the correct structure):
        # element_names = [el["name"] for el in data["orbit"]["elements"] if el["name"] in KEPLERIAN_ELEMENTS]
        # return element_names 
        
        return keplerian_params

    except Exception as e:
        return {"error": f"Error parsing API response: {e}"}

# Example of how you would call this function:
# params_eros = get_orbital_params('Eros') 
# print(json.dumps(params_eros, indent=2))
 

if __name__ == "__main__":
    app.run(debug=True)



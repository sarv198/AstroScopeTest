import requests

from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from asteroid import get_high_risk_asteroid_data, format_results_to_dictionary
from orbit import orbital_elements_to_3d_points
# set up flask app:

app = Flask(__name__)
CORS(app)


@app.route("/api/hello")
def hello_world():
    return jsonify({'message': "Hello World"})

@app.route("/home")
def home():
    return "AstroScope"

@app.route('/main')
def main_page():
    path = 'index.html'
    print(path)
    return send_from_directory('static', path=path)

@app.route('/map')
def impact_map():
    path = 'impact_map.html'
    print(path)
    return send_from_directory('static', path=path)

@app.route('/')
def base():
    return redirect('/main')

@app.route('/api/neo_data/', methods=['POST'])
def neo_data():
    content = request.json

    if content is None:
        return jsonify({"error": "Missing or invalid JSON body"}), 400
    
    #ip_min = content.get('ip_min')
    #approach_date = content.get('approach_date')
    limit = content.get('limit') or 10
    data = get_high_risk_asteroid_data(limit)
    data_dict = format_results_to_dictionary(data[0])
    
    return jsonify({'data': data_dict, 'list_of_des': data[1]})
    # parse the content for key info: filters, api to request


#@app.route('/api/neo_stat/<des>', methods=['POST'])
def neo_stat(des):
    '''
    Grab stats for one object using des. Similar style as neo_data, instead just grabbing data.
    Use cache to grab: any des visible to Frontend should have gone through neo_data, thus cached
    '''

    
    pass

# Define the six required Keplerian element short names
KEPLERIAN_ELEMENTS = ['e', 'a', 'i', 'om', 'w', 'tp']

@app.route('/orbital_params/', methods=['GET']) 
def get_orbital_params():
    """
    Retrieves the six Keplerian orbital elements for a given designation (des).

    Args:
        des (str): The object's designation (e.g., 'Eros', '2001 FO32').
    
    Returns:
        dict: A dictionary containing the filtered orbital parameters.
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

            p_r = orbital_elements_to_3d_points(
                    a = keplerian_params['a'], 
                    e = keplerian_params['e'], 
                    i_deg = keplerian_params['i'], 
                    RAAN_deg = keplerian_params['om'], 
                    argp_deg= keplerian_params['w'],
            )
            print(p_r) # for testing
            full_response[des] = p_r


        except Exception as e:
            return {"error": f"Error parsing API response: {e}"}, 400
    #print(full_response)
    return jsonify(full_response)

# Example of how you would call this function:
# params_eros = get_orbital_params('Eros') 
# print(json.dumps(params_eros, indent=2))

if __name__ == "__main__":
    app.run(debug=True)



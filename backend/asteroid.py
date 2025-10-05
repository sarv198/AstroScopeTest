import requests
import sys
import json
from typing import List, Dict, Any

# Base URLs for the NASA JPL APIs
CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
SENTRY_URL = "https://ssd-api.jpl.nasa.gov/sentry.api"

def get_high_risk_asteroid_data(limit: int = 10) -> List[Dict[str, str]]:
    """
    Fetches the list of objects from the Sentry Risk Table (Impact Probability > 0)
    and retrieves risk data (including Palermo Scale), close-approach details (CAD), 
    and Diameter (SBDB) for them.
    
    Returns a list of dictionaries, where the 'Name' key holds the asteroid's designation ('des').
    """
    
    # --- 1. FILTER: Get the list of objects with IP > 0 from Sentry API ---
    print("1. Filtering: Fetching high-risk objects from Sentry Risk Table (IP > 0)...")
    try:
        sentry_response = requests.get(SENTRY_URL)
        sentry_response.raise_for_status() 
        sentry_data = sentry_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: Initial Sentry API call failed. {e}. Please try again later, as the JPL API may be temporarily down.", file=sys.stderr)
        return []

    sentry_list = sentry_data.get('data', [])
    if not sentry_list:
        print("Sentry API returned an empty list. No objects currently pose a high impact risk.")
        return []

    # Sentry API returns data as list of dictionaries
    if sentry_list and isinstance(sentry_list[0], dict):
        required_sentry_fields = ['des', 'ip', 'diameter', 'ps_max'] 
        available_fields = list(sentry_list[0].keys())
        if not all(field in available_fields for field in required_sentry_fields):
            print(f"Sentry API response format error: Missing required fields {required_sentry_fields}. Available fields: {available_fields}", file=sys.stderr)
            return []
    else:
        print("Sentry API response format error: Expected list of dictionaries", file=sys.stderr)
        return []

    results = []
    
    print(f"2. Retrieving additional data (CAD/SBDB) for the top {limit} high-risk objects...")

    # --- 2. Iterate and fetch supplemental data for filtered asteroids ---
    for item in sentry_list:
        if len(results) >= limit:
            break
            
        # Extract risk data from the Sentry list item (dictionary format)
        name = item.get('des') # This is the 'des' value from the API
        cumulative_prob = item.get('ip')
        diameter_km = item.get('diameter')
        palermo_scale_val = item.get('ps_max') 

        # Velocity is available directly from Sentry API
        velocity_km_s = item.get('v_inf')
        velocity = f"{float(velocity_km_s):.3f} km/s" if velocity_km_s is not None else "N/A"
        
        # Get MOID (Minimum Orbit Intersection Distance) from SBDB API
        distance = "N/A"
        try:
            sbdb_params = {"sstr": name}
            sbdb_response = requests.get(SBDB_URL, params=sbdb_params, timeout=5)
            sbdb_response.raise_for_status()
            sbdb_data = sbdb_response.json()
            
            orbit_data = sbdb_data.get('orbit', {})
            moid_au = orbit_data.get('moid')
            if moid_au is not None:
                distance = f"{float(moid_au):.6f} au (MOID)"
            
        except requests.exceptions.RequestException:
            pass 

        # --- 2B. Format diameter from Sentry data ---
        diameter = f"{float(diameter_km):.3f} km" if diameter_km is not None else "Unknown"
            
        # --- 3. Format and store the data ---
        
        # Format Impact Probability (guaranteed > 0)
        prob_float = float(cumulative_prob) if cumulative_prob is not None else 0.0
        impact_prob_str = f"{prob_float:.2e}"

        # FORMATTING: Format Palermo Scale (using ps_max)
        palermo_scale_str = f"{float(palermo_scale_val):.2f}" if palermo_scale_val is not None else "N/A"

        kinetic_energy_str = "N/A (Not in Sentry summary fields)"


        results.append({
            # The 'Name' key holds the 'des' value (the asteroid's official designation)
            "des": name, 
            "Close Approach Distance": distance,
            "Velocity": velocity,
            "Diameter": diameter,
            "Impact Probability": impact_prob_str,
            "Palermo Scale": palermo_scale_str, 
            "Kinetic Energy": kinetic_energy_str
        })
        
    return results

def format_results_to_dictionary(asteroid_list: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    Converts the list of asteroid dictionaries into a single dictionary 
    keyed by the asteroid's designation ('des').
    """
    
    final_dict = {}
    for item in asteroid_list:
        # Use the value under the 'des' key as the dictionary key
        name_key = item.pop("des") 
        final_dict[name_key] = item
        
    return final_dict

'''
# --- Run the function and give the results in a dictionary ---
asteroid_list = get_high_risk_asteroid_data(limit=10)

if asteroid_list:
    # Convert the list of results into the final dictionary format
    results_dictionary = format_results_to_dictionary(asteroid_list)

    # Print the resulting dictionary
    print("\n" + "="*80)
    print("Final Results Dictionary (Keyed by Asteroid Designation - 'des')")
    print("="*80)
    # Using json.dumps for clean, readable output of the dictionary
    print(json.dumps(results_dictionary, indent=4))
else:
    print("\nCould not retrieve high-risk asteroid data or the risk list is empty.")


def get_sentry_des(impact_probability = 1e-5):
    sentry_url = "https://ssd-api.jpl.nasa.gov/sentry.api"
    params = {
        'all':'1',
        'ip-min':str(impact_probability)
    }

    response = requests.get(sentry_url, params = params)

    try:
        response.raise_for_status()
    except requests.HTTPError:
        print(f"Error {response.status_code}")
    
    data_list = response.json()['data']

    list_of_des = [row["des"] for row in data_list]

    return list_of_des

# print(get_sentry_des())
'''
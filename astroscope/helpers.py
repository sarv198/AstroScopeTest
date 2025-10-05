'''
Purpose:
Interacting with NASA NEO APIs such as Sentry, NEOWS, SCOUT APIs

Methods:
- HTTPS GET requests for data
- Pass filters to requests

'''

import requests
import sys
from typing import List, Dict, Any
from extensions import cache

# Base URLs for the NASA JPL APIs
CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
SENTRY_URL = "https://ssd-api.jpl.nasa.gov/sentry.api"


@cache.memoize(timeout=3600)
def get_high_risk_asteroid_data(limit: int = 10):
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
    list_of_des = []
    print(f"2. Retrieving additional data (CAD/SBDB) for the top {limit} high-risk objects...")

    # --- 2. Iterate and fetch supplemental data for filtered asteroids ---
    for item in sentry_list:
        if len(results) >= limit:
            break
            
        # Extract risk data from the Sentry list item (dictionary format)
        name = item.get('des') # This is the 'des' value from the API
        list_of_des.append(name)
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
        
    return (results, list_of_des)

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


@cache.memoize(timeout=36000)
def get_neo_data_single(des: str) -> dict:
    """Fetch detailed data for one asteroid (includes fullname). Caches for 10 hours"""

    # Sentry API
    try:
        sentry_resp = requests.get(SENTRY_URL, timeout=10)
        sentry_resp.raise_for_status()
        sentry_list = sentry_resp.json().get("data", [])
        sentry_obj = next((o for o in sentry_list if o.get("des") == des), None)
        if not sentry_obj:
            raise RuntimeError(f"{des} not found in Sentry data")
    except requests.RequestException as e:
        raise RuntimeError(f"Sentry fetch failed for {des}: {e}")

    # SBDB API
    try:
        sbdb_resp = requests.get(SBDB_URL, params={"sstr": des}, timeout=5)
        sbdb_resp.raise_for_status()
        sbdb_data = sbdb_resp.json()
        orbit_data = sbdb_data.get("orbit", {})
        moid = orbit_data.get("moid")
        fullname = sbdb_data.get("object", {}).get("fullname", des)
        moid_str = f"{float(moid):.6f} au (MOID)" if moid is not None else "N/A"
    except requests.RequestException as e:
        raise RuntimeError(f"SBDB fetch failed for {des}: {e}")

    data = {
        "des": des,
        "Full Name": fullname,
        "Diameter": f"{float(sentry_obj.get('diameter', 0)):.3f} km",
        "Velocity": f"{float(sentry_obj.get('v_inf', 0)):.3f} km/s",
        "Impact Probability": f"{float(sentry_obj.get('ip', 0)):.2e}",
        "Palermo Scale": f"{float(sentry_obj.get('ps_max', 0)):.2f}",
        "Close Approach Distance": moid_str,
    }

    return data

@cache.memoize(timeout=36000)
def get_vi_data(des: str) -> dict:
    """
    Returns kinetic energy, impact date, and distance for a given asteroid.
    Caches per-object results for 10 hour.
    """
    try:
        r = requests.get(SENTRY_URL, params={"des": des}, timeout=5)
        r.raise_for_status()
        vi_list = r.json().get("data", [])
        if not vi_list:
            return {"energy": "N/A", "date": "N/A", "dist": "N/A"}

        # Choose highest-energy virtual impactor (worst case)
        top_vi = max(vi_list, key=lambda v: v.get("energy", 0) or 0)

        return {
            "energy": f"{float(top_vi.get('energy', 0)):.2f} Mt",
            "date": top_vi.get("date", "N/A"),
            "dist": f"{float(top_vi.get('dist', 0)):.6f} au" if top_vi.get("dist") else "N/A"
        }

    except requests.RequestException:
        return {"energy": "N/A", "date": "N/A", "dist": "N/A"}


@cache.memoize(timeout=3600)
def get_palermo_leaderboard(limit: int = 10):
    """
    Builds a leaderboard of the most dangerous asteroids,
    sorted by Palermo Scale (descending).
    """
    try:
        r = requests.get(SENTRY_URL, timeout=10)
        r.raise_for_status()
        sentry_list = r.json().get("data", [])
    except requests.RequestException as e:
        print(f"Sentry API fetch failed: {e}", file=sys.stderr)
        return []

    if not sentry_list:
        print("No active impact-risk objects in Sentry data.")
        return []

    # Sort by Palermo Scale (descending) 
    sentry_list.sort(
        key=lambda o: float(o.get("ps_max", -99) or -99),
        reverse=True
    )

    leaderboard = []
    for obj in sentry_list[:limit]:
        des = obj.get("des")
        vi_info = get_vi_data(des)

        leaderboard.append({
            "des": des,
            "Palermo Scale": f"{float(obj.get('ps_max', -99)):.2f}",
            "Impact Probability": f"{float(obj.get('ip', 0.0)):.2e}",
            "Velocity": f"{float(obj.get('v_inf', 0.0)):.3f} km/s",
            "Diameter": f"{float(obj.get('diameter', 0.0)):.3f} km",
            "Kinetic Energy": vi_info.get("energy"),
            "Impact Date": vi_info.get("date"),
            "Approach Distance": vi_info.get("dist")
        })

    return leaderboard



'''
# TESTING and DEPRECIATED CODE
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
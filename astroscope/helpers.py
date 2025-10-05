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

def get_high_risk_asteroid_data(limit: int = 30):
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

@cache.memoize(timeout=36000)  # 10 hours
def get_vi_data(des: str) -> dict:
    """
    Returns merged Sentry + VI information for one asteroid.

    Includes:
      - des
      - Palermo Scale
      - Impact Probability
      - Velocity
      - Diameter
      - Kinetic Energy (highest-energy VI)
      - Impact Date
      - Approach Distance

    Caches per-object results for 10 hours.
    """
    try:
        r = requests.get(SENTRY_URL, params={"des": des}, timeout=10)
        r.raise_for_status()
        data = r.json()

        summary = data.get("summary", {})
        vi_list = data.get("data", [])

        # Pick the highest-risk virtual impactor (worst-case scenario)
        top_vi = max(vi_list, key=lambda v: v.get("ps", -99) or -99) if vi_list else {}

        return {
            "des": summary.get("des", des),
            "Full Name": summary.get("fullname", des),
            "Impact Probability": f"{float(summary.get('ip', 0)):.2e}",
            "Palermo Scale": f"{float(summary.get('ps_max', -99)):.2f}",
            "Velocity": f"{float(summary.get('v_inf', 0)):.3f} km/s",
            "Diameter": f"{float(summary.get('diameter', 0)):.3f} km",
            "Kinetic Energy": f"{float(top_vi.get('energy', 0)):.2f} Mt" if top_vi else "N/A",
            "Potential Impact Date": top_vi.get("date", "N/A"),
            "Approach Distance": (
                f"{float(top_vi.get('dist', 0)):.6f} au"
                if top_vi.get("dist") else "N/A"
            )
        }

    except requests.RequestException as e:
        print(f"Sentry VI API fetch failed: {e}")
        raise e


@cache.memoize(timeout=36000)
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

    # Sort by Palermo Scale descending
    sentry_list.sort(key=lambda o: float(o.get("ps_max", -99) or -99), reverse=True)
    leaderboard = []
    for obj in sentry_list[:limit]:
        des = obj.get("des")
        full_name = obj.get("fullname") or obj.get("des", "Unknown Object")
        vi_info = get_vi_data(des) or {}
        if not vi_info:
            limit+=1
            continue
        #print(vi_info)



        leaderboard.append({
            "Full Name": full_name,
            "Palermo Scale": f"{float(vi_info.get('Palermo Scale', -99)):.2f}",
            "Impact Probability": f"{float(vi_info.get('Impact Probability', 0.0)):.2e}",
            "Velocity": f"{float(vi_info.get('Velocity', 0.0).split()[0]):.3f} km/s",
            "Diameter": f"{float(vi_info.get('Diameter', 0.0).split()[0]):.3f} km",
            "Kinetic Energy": vi_info.get("Kinetic Energy", "N/A"),
            "Potential Impact Date": str(vi_info.get("Potential Impact Date", "N/A")).split('.')[0]
        })

    return leaderboard

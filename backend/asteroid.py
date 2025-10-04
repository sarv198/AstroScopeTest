import requests
import sys

# Base URLs for the NASA JPL APIs
CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"
SENTRY_URL = "https://ssd-api.jpl.nasa.gov/sentry.api"

def get_high_risk_asteroid_data(limit=10):
    """
    Fetches the list of objects from the Sentry Risk Table (Impact Probability > 0)
    and then retrieves close-approach details (CAD) and Diameter (SBDB) for them.
    """
    
    # --- 1. FILTER: Get the list of objects with IP > 0 from Sentry API ---
    # FIX: Removed invalid 'mode=summary' parameter. Sentry API returns data as list of dictionaries.
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

    # Sentry API returns data as list of dictionaries, not arrays
    # Verify that the essential fields for risk data are present in the first item
    if sentry_list and isinstance(sentry_list[0], dict):
        required_sentry_fields = ['des', 'ip', 'diameter']
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
        name = item.get('des')
        cumulative_prob = item.get('ip')
        diameter_km = item.get('diameter')  # Diameter is already available from Sentry 

        # --- 2A. Get velocity from Sentry and distance from SBDB ---
        # Velocity is available directly from Sentry API
        velocity_km_s = item.get('v_inf')
        if velocity_km_s is not None:
            velocity = f"{float(velocity_km_s):.3f} km/s"
        else:
            velocity = "N/A"
        
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
        if diameter_km is not None:
            diameter = f"{float(diameter_km):.3f} km"
        else:
            diameter = "Unknown"
            
        # --- 3. Format and store the data ---
        
        # Format Impact Probability (guaranteed > 0)
        prob_float = float(cumulative_prob) if cumulative_prob is not None else 0.0
        impact_prob_str = f"{prob_float:.2e}"

        results.append({
            "Name": name,
            "Close Approach Distance": distance,
            "Velocity": velocity,
            "Diameter": diameter,
            "Impact Probability": impact_prob_str
        })
        
    return results

# --- Run the function and display results ---
asteroid_list = get_high_risk_asteroid_data(limit=10)

if asteroid_list:
    print("\n" + "="*120)
    print(f"Top {len(asteroid_list)} Asteroids on Sentry Risk Table (Impact Probability > 0)")
    print("="*120)

    # Calculate max width for clean, formatted output
    max_name = max([len(a['Name']) for a in asteroid_list])
    max_dist = max([len(a['Close Approach Distance']) for a in asteroid_list])
    max_velo = max([len(a['Velocity']) for a in asteroid_list])
    max_diam = max([len(a['Diameter']) for a in asteroid_list])
    max_prob = max([len(a['Impact Probability']) for a in asteroid_list])

    # Print header
    header = (
        f"{'Name':<{max_name}} | {'Distance (au)':<{max_dist}} | {'Velocity (km/s)':<{max_velo}} | "
        f"{'Diameter':<{max_diam}} | {'Impact Probability':<{max_prob}}"
    )
    print(header)
    print("-" * len(header))

    # Print data
    for item in asteroid_list:
        print(
            f"{item['Name']:<{max_name}} | "
            f"{item['Close Approach Distance']:<{max_dist}} | "
            f"{item['Velocity']:<{max_velo}} | "
            f"{item['Diameter']:<{max_diam}} | "
            f"{item['Impact Probability']:<{max_prob}}"
        )
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

# import requests
# import sys

# # Base URLs for the NASA JPL APIs
# CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
# SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"

# def get_asteroid_data(limit=10):
#     """
#     Fetches close-approach data for a specified number of NEOs and 
#     retrieves the diameter for each one by calling the SBDB API.
#     """
    
#     print(f"1. Fetching the top {limit} upcoming close approaches from CAD API...")
    
#     # Use CAD to get a LIST of the next 10 NEO close approaches
#     cad_params = {
#         "limit": limit,
#         "neo": "true",
#         "date-min": "now",
#         "sort": "date"
#     }
    
#     try:
#         cad_response = requests.get(CAD_URL, params=cad_params)
#         cad_response.raise_for_status() 
#         cad_data = cad_response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"Error fetching data from CAD API: {e}", file=sys.stderr)
#         return []

#     if not cad_data.get('data'):
#         print("CAD API returned no close approach data.", file=sys.stderr)
#         return []

#     # Map the field names to their array index for safety (CAD API returns data as lists within lists)
#     fields = cad_data.get('fields', [])
#     indices = {field: i for i, field in enumerate(fields)}
    
#     # The fields we need from CAD: 'des' (Name), 'dist' (Distance), 'v_inf' (Velocity)
#     required_fields = ['des', 'dist', 'v_inf']
#     if not all(field in indices for field in required_fields):
#         print(f"CAD API response is missing required fields: {required_fields}", file=sys.stderr)
#         return []

#     results = []
    
#     print("2. Retrieving diameter for each object from SBDB API...")
#     for approach in cad_data['data'][:limit]:
#         # Extract data available in CAD response
#         name = approach[indices['des']]
#         distance = approach[indices['dist']] # in Astronomical Units (au)
#         velocity = approach[indices['v_inf']] # in km/s
        
#         # --- SBDB API call for Physical Parameters (including absolute magnitude) ---
#         sbdb_params = {
#             "sstr": name,
#             "phys-par": "true"  # Request physical parameters including absolute magnitude
#         }
        
#         try:
#             sbdb_response = requests.get(SBDB_URL, params=sbdb_params)
#             sbdb_response.raise_for_status()
#             sbdb_data = sbdb_response.json()
            
#             # Extract absolute magnitude (H) from phys_par
#             phys_par = sbdb_data.get('phys_par', [])
#             absolute_magnitude = None
            
#             for param in phys_par:
#                 if param.get('name') == 'H':  # H is the absolute magnitude
#                     absolute_magnitude = float(param.get('value'))
#                     break
            
#             if absolute_magnitude is not None:
#                 # Estimate diameter from absolute magnitude using the formula:
#                 # D = 1329 * 10^(-H/5) km (for asteroids)
#                 diameter_km = 1329 * (10 ** (-absolute_magnitude / 5))
#                 diameter = f"{diameter_km:.3f} km"
#             else:
#                 diameter = "Unknown (no H magnitude)"
                
#         except requests.exceptions.RequestException:
#             diameter = "N/A" # Handle API or network errors
#         except (ValueError, TypeError):
#             diameter = "Unknown (invalid H magnitude)"
            
#         # --- Combine and store the data ---
#         results.append({
#             "Name": name,
#             "Close Approach Distance": f"{float(distance):.6f} au",
#             "Velocity": f"{float(velocity):.3f} km/s",
#             "Diameter": diameter
#         })
        
#     return results

# # --- Run the function and display results ---
# asteroid_list = get_asteroid_data(limit=10)

# if asteroid_list:
#     print("\n" + "="*80)
#     print(f"Top {len(asteroid_list)} Upcoming NEO Close Approaches with Required Data")
#     print("="*80)

#     # Calculate max width for clean, formatted output
#     max_name = max([len(a['Name']) for a in asteroid_list])
#     max_dist = max([len(a['Close Approach Distance']) for a in asteroid_list])
#     max_velo = max([len(a['Velocity']) for a in asteroid_list])
#     max_diam = max([len(a['Diameter']) for a in asteroid_list])

#     # Print header
#     header = f"{'Name':<{max_name}} | {'Distance':<{max_dist}} | {'Velocity':<{max_velo}} | {'Diameter':<{max_diam}}"
#     print(header)
#     print("-" * len(header))

#     # Print data
#     for item in asteroid_list:
#         print(
#             f"{item['Name']:<{max_name}} | "
#             f"{item['Close Approach Distance']:<{max_dist}} | "
#             f"{item['Velocity']:<{max_velo}} | "
#             f"{item['Diameter']:<{max_diam}}"
#         )
# else:
#     print("\nCould not retrieve asteroid data.")

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
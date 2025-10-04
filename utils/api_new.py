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
    # FIX: Explicitly using 'mode=summary'. While this sometimes caused issues, it is the documented 
    # way to request the risk table and is necessary if the empty-param call is failing.
    sentry_params = {
        "mode": "summary"
    }
    
    print("1. Filtering: Fetching up to 100 high-risk objects from Sentry Risk Table (IP > 0)...")
    try:
        sentry_response = requests.get(SENTRY_URL, params=sentry_params)
        sentry_response.raise_for_status() 
        sentry_data = sentry_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: Initial Sentry API call failed. {e}. Please try again later, as the JPL API may be temporarily down.", file=sys.stderr)
        return []

    sentry_list = sentry_data.get('data', [])
    if not sentry_list:
        print("Sentry API returned an empty list. No objects currently pose a high impact risk.")
        return []

    # Map Sentry fields once
    sentry_fields = sentry_data.get('fields', [])
    sentry_indices = {field: i for i, field in enumerate(sentry_fields)}
    
    # Verify that the essential fields for risk data are present
    required_sentry_fields = ['des', 'ip', 'energy']
    if not all(field in sentry_indices for field in required_sentry_fields):
         # This error indicates a non-standard response from Sentry, even if status code was 200.
         print(f"Sentry API response format error: Missing required fields {required_sentry_fields}. Available fields: {sentry_fields}", file=sys.stderr)
         return []

    results = []
    
    print(f"2. Retrieving additional data (CAD/SBDB) for the top {limit} high-risk objects...")

    # --- 2. Iterate and fetch supplemental data for filtered asteroids ---
    for item in sentry_list:
        if len(results) >= limit:
            break
            
        # Extract risk data from the Sentry list item
        # We must assume the field order from 'sentry_fields' is correct
        name = item[sentry_indices['des']]
        cumulative_prob = item[sentry_indices['ip']]
        kinetic_energy_mt = item[sentry_indices['energy']] 

        # --- 2A. CAD API call for Close Approach Details (Distance & Velocity) ---
        distance = "N/A"
        velocity = "N/A"
        
        try:
            cad_params = {"des": name, "date-min": "now", "limit": 1}
            cad_response = requests.get(CAD_URL, params=cad_params, timeout=5)
            cad_response.raise_for_status()
            cad_data = cad_response.json()
            
            fields = cad_data.get('fields', [])
            indices = {field: i for i, field in enumerate(fields)}
            
            if cad_data.get('data') and indices.get('dist') is not None and indices.get('v_inf') is not None:
                approach_data = cad_data['data'][0]
                dist_val = float(approach_data[indices['dist']])
                velo_val = float(approach_data[indices['v_inf']])
                distance = f"{dist_val:.6f} au"
                velocity = f"{velo_val:.3f} km/s"
            
        except requests.exceptions.RequestException:
            pass 

        # --- 2B. SBDB API call for Diameter (via H magnitude) ---
        diameter = "N/A"
        try:
            sbdb_params = {"sstr": name, "phys-par": "true"}
            sbdb_response = requests.get(SBDB_URL, params=sbdb_params)
            sbdb_response.raise_for_status()
            sbdb_data = sbdb_response.json()
            
            phys_par = sbdb_data.get('phys_par', [])
            absolute_magnitude = None
            for param in phys_par:
                if param.get('name') == 'H':
                    absolute_magnitude = float(param.get('value'))
                    break
            
            if absolute_magnitude is not None:
                diameter_km = 1329 * (10 ** (-absolute_magnitude / 5))
                diameter = f"{diameter_km:.3f} km"
            else:
                diameter = "Unknown (no H magnitude)"
                
        except requests.exceptions.RequestException:
            diameter = "N/A (SBDB Error)"
        except (ValueError, TypeError):
            diameter = "Unknown (invalid H magnitude)"
            
        # --- 3. Format and store the data ---
        
        # Format Impact Probability (guaranteed > 0)
        prob_float = float(cumulative_prob) if cumulative_prob is not None else 0.0
        impact_prob_str = f"{prob_float:.2e}"
        
        # Format Kinetic Energy (guaranteed > negligible)
        energy_float = float(kinetic_energy_mt) if kinetic_energy_mt is not None else 0.0
        kinetic_energy_str = f"{energy_float:.3f} Mt"

        results.append({
            "Name": name,
            "Close Approach Distance": distance,
            "Velocity": velocity,
            "Diameter": diameter,
            "Kinetic Energy": kinetic_energy_str,
            "Impact Probability": impact_prob_str
        })
        
    return results

# --- Run the function and display results ---
asteroid_list = get_high_risk_asteroid_data(limit=10)

if asteroid_list:
    print("\n" + "="*140)
    print(f"Top {len(asteroid_list)} Asteroids on Sentry Risk Table (Impact Probability > 0)")
    print("="*140)

    # Calculate max width for clean, formatted output
    max_name = max([len(a['Name']) for a in asteroid_list])
    max_dist = max([len(a['Close Approach Distance']) for a in asteroid_list])
    max_velo = max([len(a['Velocity']) for a in asteroid_list])
    max_diam = max([len(a['Diameter']) for a in asteroid_list])
    max_energy = max([len(a['Kinetic Energy']) for a in asteroid_list])
    max_prob = max([len(a['Impact Probability']) for a in asteroid_list])

    # Print header
    header = (
        f"{'Name':<{max_name}} | {'Distance (au)':<{max_dist}} | {'Velocity (km/s)':<{max_velo}} | "
        f"{'Diameter':<{max_diam}} | {'Kinetic Energy (Mt)':<{max_energy}} | {'Impact Probability':<{max_prob}}"
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
            f"{item['Kinetic Energy']:<{max_energy}} | "
            f"{item['Impact Probability']:<{max_prob}}"
        )
else:
    print("\nCould not retrieve high-risk asteroid data or the risk list is empty.")
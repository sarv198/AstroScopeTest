import requests
import sys

# Base URLs for the NASA JPL APIs
CAD_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
SBDB_URL = "https://ssd-api.jpl.nasa.gov/sbdb.api"

def get_asteroid_data(limit=10):
    """
    Fetches close-approach data for a specified number of NEOs and 
    retrieves the diameter for each one by calling the SBDB API.
    """
    
    print(f"1. Fetching the top {limit} upcoming close approaches from CAD API...")
    
    # Use CAD to get a LIST of the next 10 NEO close approaches
    cad_params = {
        "limit": limit,
        "neo": "true",
        "date-min": "now",
        "sort": "date"
    }
    
    try:
        cad_response = requests.get(CAD_URL, params=cad_params)
        cad_response.raise_for_status() 
        cad_data = cad_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CAD API: {e}", file=sys.stderr)
        return []

    if not cad_data.get('data'):
        print("CAD API returned no close approach data.", file=sys.stderr)
        return []

    # Map the field names to their array index for safety (CAD API returns data as lists within lists)
    fields = cad_data.get('fields', [])
    indices = {field: i for i, field in enumerate(fields)}
    
    # The fields we need from CAD: 'des' (Name), 'dist' (Distance), 'v_inf' (Velocity)
    required_fields = ['des', 'dist', 'v_inf']
    if not all(field in indices for field in required_fields):
        print(f"CAD API response is missing required fields: {required_fields}", file=sys.stderr)
        return []

    results = []
    
    print("2. Retrieving diameter for each object from SBDB API...")
    for approach in cad_data['data'][:limit]:
        # Extract data available in CAD response
        name = approach[indices['des']]
        distance = approach[indices['dist']] # in Astronomical Units (au)
        velocity = approach[indices['v_inf']] # in km/s
        
        # --- SBDB API call for Physical Parameters (including absolute magnitude) ---
        sbdb_params = {
            "sstr": name,
            "phys-par": "true"  # Request physical parameters including absolute magnitude
        }
        
        try:
            sbdb_response = requests.get(SBDB_URL, params=sbdb_params)
            sbdb_response.raise_for_status()
            sbdb_data = sbdb_response.json()
            
            # Extract absolute magnitude (H) from phys_par
            phys_par = sbdb_data.get('phys_par', [])
            absolute_magnitude = None
            
            for param in phys_par:
                if param.get('name') == 'H':  # H is the absolute magnitude
                    absolute_magnitude = float(param.get('value'))
                    break
            
            if absolute_magnitude is not None:
                # Estimate diameter from absolute magnitude using the formula:
                # D = 1329 * 10^(-H/5) km (for asteroids)
                diameter_km = 1329 * (10 ** (-absolute_magnitude / 5))
                diameter = f"{diameter_km:.3f} km"
            else:
                diameter = "Unknown (no H magnitude)"
                
        except requests.exceptions.RequestException:
            diameter = "N/A" # Handle API or network errors
        except (ValueError, TypeError):
            diameter = "Unknown (invalid H magnitude)"
            
        # --- Combine and store the data ---
        results.append({
            "Name": name,
            "Close Approach Distance": f"{float(distance):.6f} au",
            "Velocity": f"{float(velocity):.3f} km/s",
            "Diameter": f"diameter"
        })
        
    return results

# --- Run the function and display results ---
asteroid_list = get_asteroid_data(limit=10)

if asteroid_list:
    print("\n" + "="*80)
    print(f"Top {len(asteroid_list)} Upcoming NEO Close Approaches with Required Data")
    print("="*80)

    # Calculate max width for clean, formatted output
    max_name = max([len(a['Name']) for a in asteroid_list])
    max_dist = max([len(a['Close Approach Distance']) for a in asteroid_list])
    max_velo = max([len(a['Velocity']) for a in asteroid_list])
    max_diam = max([len(a['Diameter']) for a in asteroid_list])

    # Print header
    header = f"{'Name':<{max_name}} | {'Distance':<{max_dist}} | {'Velocity':<{max_velo}} | {'Diameter':<{max_diam}}"
    print(header)
    print("-" * len(header))

    # Print data
    for item in asteroid_list:
        print(
            f"{item['Name']:<{max_name}} | "
            f"{item['Close Approach Distance']:<{max_dist}} | "
            f"{item['Velocity']:<{max_velo}} | "
            f"{item['Diameter']:<{max_diam}}"
        )
else:
    print("\nCould not retrieve asteroid data.")

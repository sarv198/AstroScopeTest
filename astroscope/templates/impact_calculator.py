"""
Impact Calculator - Asteroid Impact Radius and Damage Assessment

This module provides functions to calculate impact radius, damage zones,
and classification for asteroid impacts based on physical parameters.

Based on scientific models for impact cratering and blast radius calculations.
"""

import math


def calculate_impact_radius(density, speed, diameter):
    """
    Calculate impact radius and damage classification for an asteroid impact.
    
    Args:
        density (float): Asteroid density in kg/m^3
        speed (float): Impact speed in m/s
        diameter (float): Asteroid diameter in meters
    
    Returns:
        dict: Dictionary containing kinetic energy, impact radii, and damage classification
    """
    
    # Input validation
    if not all(isinstance(x, (int, float)) for x in [density, speed, diameter]):
        raise ValueError("All inputs must be numeric values")
    
    if density <= 0:
        raise ValueError("Density must be positive")
    if speed <= 0:
        raise ValueError("Speed must be positive")
    if diameter <= 0:
        raise ValueError("Diameter must be positive")
    
    # Calculate kinetic energy: E = (π / 12) * density * diameter^3 * speed^2
    kinetic_energy = (math.pi / 12) * density * (diameter ** 3) * (speed ** 2)
    
    # Calculate impact radii using different damage coefficients
    # R = k * E^(1/3)
    severe_k = 1.8e-4
    moderate_k = 4.0e-4
    light_k = 8.0e-4
    
    # Calculate radii in meters first
    severe_radius_m = severe_k * (kinetic_energy ** (1/3))
    moderate_radius_m = moderate_k * (kinetic_energy ** (1/3))
    light_radius_m = light_k * (kinetic_energy ** (1/3))
    
    # Convert to kilometers
    severe_radius_km = severe_radius_m / 1000
    moderate_radius_km = moderate_radius_m / 1000
    light_radius_km = light_radius_m / 1000
    
    # Determine damage classification
    if severe_radius_km > 5:
        classification = "Severe"
    elif moderate_radius_km > 2:
        classification = "Moderate"
    else:
        classification = "Light"
    
    # Create result dictionary
    result = {
        "kinetic_energy_joules": kinetic_energy,
        "kinetic_energy_megatons": kinetic_energy / (4.184e15),  # Convert to megatons TNT
        "severe_radius_km": severe_radius_km,
        "moderate_radius_km": moderate_radius_km,
        "light_radius_km": light_radius_km,
        "damage_classification": classification,
        "input_parameters": {
            "density_kg_m3": density,
            "speed_m_s": speed,
            "diameter_m": diameter
        }
    }
    
    return result


def calculate_crater_dimensions(diameter, speed, density):
    """
    Calculate crater dimensions based on impact parameters.
    
    Args:
        diameter (float): Asteroid diameter in meters
        speed (float): Impact speed in m/s
        density (float): Asteroid density in kg/m^3
    
    Returns:
        dict: Crater dimensions and characteristics
    """
    
    # Input validation
    if not all(isinstance(x, (int, float)) for x in [diameter, speed, density]):
        raise ValueError("All inputs must be numeric values")
    
    if any(x <= 0 for x in [diameter, speed, density]):
        raise ValueError("All inputs must be positive values")
    
    # Calculate kinetic energy
    kinetic_energy = (math.pi / 12) * density * (diameter ** 3) * (speed ** 2)
    
    # Crater scaling laws (simplified model)
    # These are empirical relationships based on impact crater studies
    crater_diameter_m = 1.2 * (kinetic_energy / 1e12) ** 0.294  # D_crater in meters
    crater_depth_m = crater_diameter_m * 0.2  # Typical depth-to-diameter ratio
    
    return {
        "crater_diameter_m": crater_diameter_m,
        "crater_diameter_km": crater_diameter_m / 1000,
        "crater_depth_m": crater_depth_m,
        "crater_depth_km": crater_depth_m / 1000,
        "crater_volume_m3": math.pi * (crater_diameter_m / 2) ** 2 * crater_depth_m,
        "kinetic_energy_joules": kinetic_energy
    }


def estimate_casualties(severe_radius_km, moderate_radius_km, light_radius_km, population_density=100):
    """
    Estimate casualties and damage based on impact location and population density.
    
    Args:
        severe_radius_km (float): Severe damage radius in kilometers
        moderate_radius_km (float): Moderate damage radius in kilometers
        light_radius_km (float): Light damage radius in kilometers
        population_density (float): Population density in people per km² (default: 100)
    
    Returns:
        dict: Estimated casualties and affected area
    """
    
    # Input validation
    if not all(isinstance(x, (int, float)) for x in [severe_radius_km, moderate_radius_km, light_radius_km, population_density]):
        raise ValueError("All inputs must be numeric values")
    
    if any(x < 0 for x in [severe_radius_km, moderate_radius_km, light_radius_km, population_density]):
        raise ValueError("All inputs must be non-negative values")
    
    # Calculate areas
    severe_area_km2 = math.pi * severe_radius_km * severe_radius_km
    moderate_area_km2 = math.pi * moderate_radius_km * moderate_radius_km
    light_area_km2 = math.pi * light_radius_km * light_radius_km
    
    # Estimate casualties (simplified model)
    # Severe zone: 90% fatality rate
    # Moderate zone: 30% fatality rate  
    # Light zone: 5% fatality rate
    severe_casualties = severe_area_km2 * population_density * 0.9
    moderate_casualties = moderate_area_km2 * population_density * 0.3
    light_casualties = light_area_km2 * population_density * 0.05
    
    total_casualties = severe_casualties + moderate_casualties + light_casualties
    
    return {
        "severe_casualties": round(severe_casualties),
        "moderate_casualties": round(moderate_casualties),
        "light_casualties": round(light_casualties),
        "total_casualties": round(total_casualties),
        "affected_areas": {
            "severe_area_km2": severe_area_km2,
            "moderate_area_km2": moderate_area_km2,
            "light_area_km2": light_area_km2,
            "total_area_km2": severe_area_km2 + moderate_area_km2 + light_area_km2
        }
    }


def convert_nasa_data_to_parameters(nasa_data):
    """
    Convert asteroid data from NASA format to calculation parameters.
    
    Args:
        nasa_data (dict): Data from NASA API (Sentry/SBDB)
    
    Returns:
        dict: Parameters suitable for impact calculations
    """
    
    # Extract and convert NASA data
    diameter_km = 0
    velocity_km_s = 0
    
    # Handle different possible data formats
    if 'Diameter' in nasa_data:
        diameter_str = nasa_data['Diameter']
        if isinstance(diameter_str, str):
            diameter_km = float(diameter_str.split(' ')[0])
        else:
            diameter_km = float(diameter_str)
    
    if 'Velocity' in nasa_data:
        velocity_str = nasa_data['Velocity']
        if isinstance(velocity_str, str):
            velocity_km_s = float(velocity_str.split(' ')[0])
        else:
            velocity_km_s = float(velocity_str)
    
    # Convert to meters and m/s
    diameter_m = diameter_km * 1000
    velocity_m_s = velocity_km_s * 1000
    
    # Assume typical asteroid density (kg/m³)
    # This could be improved with actual density data if available
    density_kg_m3 = 3000  # Typical stony asteroid density
    
    return {
        "diameter_m": diameter_m,
        "velocity_m_s": velocity_m_s,
        "density_kg_m3": density_kg_m3,
        "original_data": nasa_data
    }


def comprehensive_impact_assessment(nasa_data, population_density=100):
    """
    Comprehensive impact assessment combining all calculations.
    
    Args:
        nasa_data (dict): Data from NASA API
        population_density (float): Population density in people per km² (optional)
    
    Returns:
        dict: Complete impact assessment
    """
    
    try:
        # Convert NASA data to calculation parameters
        params = convert_nasa_data_to_parameters(nasa_data)
        
        # Calculate impact radius and damage
        impact_results = calculate_impact_radius(
            params["density_kg_m3"],
            params["velocity_m_s"],
            params["diameter_m"]
        )
        
        # Calculate crater dimensions
        crater_results = calculate_crater_dimensions(
            params["diameter_m"],
            params["velocity_m_s"],
            params["density_kg_m3"]
        )
        
        # Estimate casualties
        casualty_results = estimate_casualties(
            impact_results["severe_radius_km"],
            impact_results["moderate_radius_km"],
            impact_results["light_radius_km"],
            population_density
        )
        
        return {
            "asteroid_info": {
                "designation": nasa_data.get('des', nasa_data.get('Full Name', 'Unknown')),
                "diameter_km": params["diameter_m"] / 1000,
                "velocity_km_s": params["velocity_m_s"] / 1000,
                "density_kg_m3": params["density_kg_m3"]
            },
            "impact_assessment": impact_results,
            "crater_analysis": crater_results,
            "casualty_estimation": casualty_results,
            "nasa_data": nasa_data
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "nasa_data": nasa_data
        }


def print_impact_summary(density, speed, diameter):
    """
    Calculate and print a formatted summary of the impact analysis.
    
    Args:
        density (float): Asteroid density in kg/m^3
        speed (float): Impact speed in m/s
        diameter (float): Asteroid diameter in meters
    """
    try:
        result = calculate_impact_radius(density, speed, diameter)
        
        print("=" * 60)
        print("ASTEROID IMPACT ANALYSIS")
        print("=" * 60)
        print(f"Input Parameters:")
        print(f"  Density:    {density:,.0f} kg/m³")
        print(f"  Speed:      {speed:,.0f} m/s")
        print(f"  Diameter:   {diameter:,.0f} m")
        print()
        print(f"Calculated Results:")
        print(f"  Kinetic Energy: {result['kinetic_energy_joules']:.2e} Joules")
        print(f"  Kinetic Energy: {result['kinetic_energy_megatons']:.2f} Megatons TNT")
        print()
        print(f"Impact Radii:")
        print(f"  Severe Damage:   {result['severe_radius_km']:.2f} km")
        print(f"  Moderate Damage: {result['moderate_radius_km']:.2f} km")
        print(f"  Light Damage:    {result['light_radius_km']:.2f} km")
        print()
        print(f"Overall Classification: {result['damage_classification']}")
        print("=" * 60)
        
    except ValueError as e:
        print(f"Error: {e}")


# Example usage
if __name__ == "__main__":
    # Example: Iron asteroid with typical impact parameters
    example_density = 7800  # kg/m^3 (iron)
    example_speed = 17000   # m/s (typical impact speed)
    example_diameter = 50   # meters
    
    print_impact_summary(example_density, example_speed, example_diameter)
    
    # Example with NASA data format
    example_nasa_data = {
        'des': '1979 XB',
        'Diameter': '0.500 km',
        'Velocity': '20.000 km/s',
        'Impact Probability': '1.23e-04',
        'Palermo Scale': '-2.50'
    }
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE ASSESSMENT EXAMPLE")
    print("=" * 60)
    assessment = comprehensive_impact_assessment(example_nasa_data, population_density=150)
    
    if 'error' in assessment:
        print(f"Error: {assessment['error']}")
    else:
        print(f"Asteroid: {assessment['asteroid_info']['designation']}")
        print(f"Classification: {assessment['impact_assessment']['damage_classification']}")
        print(f"Severe Radius: {assessment['impact_assessment']['severe_radius_km']:.2f} km")
        print(f"Total Casualties: {assessment['casualty_estimation']['total_casualties']:,}")

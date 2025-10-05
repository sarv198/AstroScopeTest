/**
 * Impact Calculator - Asteroid Impact Radius and Damage Assessment
 * 
 * This module provides functions to calculate impact radius, damage zones,
 * and classification for asteroid impacts based on physical parameters.
 * 
 * Based on scientific models for impact cratering and blast radius calculations.
 */

/**
 * Calculate impact radius and damage classification for an asteroid impact.
 * 
 * @param {number} density - Asteroid density in kg/m^3 (typical range: 2000-8000)
 * @param {number} speed - Impact speed in m/s (typical range: 11000-70000)
 * @param {number} diameter - Asteroid diameter in meters
 * @returns {object} Dictionary containing kinetic energy, impact radii, and damage classification
 */
function calculateImpactRadius(density, speed, diameter) {
    // --- Input Validation (Ensuring numbers are valid) ---
    const numericInputs = [density, speed, diameter].map(Number); // Convert to number
    
    if (numericInputs.some(isNaN)) {
        throw new Error("All inputs must be numeric values.");
    }
    
    const [d, s, dia] = numericInputs; // Destructure the converted values

    if (d <= 0 || s <= 0 || dia <= 0) {
        throw new Error("Density, Speed, and Diameter must be positive values.");
    }

    // --- Calculation ---
    
    // Calculate volume and kinetic energy
    // E = (π / 12) * density * diameter^3 * speed^2
    const kineticEnergy = (Math.PI / 12) * d * (dia ** 3) * (s ** 2);

    // Calculate impact radii using different damage coefficients
    // R = k * E^(1/3)
    const severe_k = 1.8e-4;
    const moderate_k = 4.0e-4;
    const light_k = 8.0e-4;

    const impactPowerThird = Math.cbrt(kineticEnergy); // Cube root of kinetic energy

    // Calculate radii in meters
    const severe_radius_m = severe_k * impactPowerThird;
    const moderate_radius_m = moderate_k * impactPowerThird;
    const light_radius_m = light_k * impactPowerThird;

    // Convert to kilometers
    const severe_radius_km = severe_radius_m / 1000;
    const moderate_radius_km = moderate_radius_m / 1000;
    const light_radius_km = light_radius_m / 1000;

    // --- Damage Classification ---
    let classification;
    if (severe_radius_km > 5) {
        classification = "Severe";
    } else if (moderate_radius_km > 2) {
        classification = "Moderate";
    } else {
        classification = "Light";
    }

    // --- Result Object ---
    const result = {
        kinetic_energy_joules: kineticEnergy,
        kinetic_energy_megatons: kineticEnergy / (4.184e15), // Convert to megatons TNT
        severe_radius_km: severe_radius_km,
        moderate_radius_km: moderate_radius_km,
        light_radius_km: light_radius_km,
        damage_classification: classification,
        input_parameters: {
            density_kg_m3: d,
            speed_m_s: s,
            diameter_m: dia
        }
    };

    return result;
}

/**
 * Calculate crater dimensions based on impact parameters.
 * 
 * @param {number} diameter - Asteroid diameter in meters
 * @param {number} speed - Impact speed in m/s
 * @param {number} density - Asteroid density in kg/m^3
 * @returns {object} Crater dimensions and characteristics
 */
function calculateCraterDimensions(diameter, speed, density) {
    const numericInputs = [diameter, speed, density].map(Number);
    
    if (numericInputs.some(isNaN) || numericInputs.some(x => x <= 0)) {
        throw new Error("All inputs must be positive numeric values.");
    }
    
    const [dia, s, d] = numericInputs;
    
    // Calculate kinetic energy
    const kineticEnergy = (Math.PI / 12) * d * (dia ** 3) * (s ** 2);
    
    // Crater scaling laws (simplified model)
    // These are empirical relationships based on impact crater studies
    const crater_diameter_m = 1.2 * Math.pow(kineticEnergy / 1e12, 0.294); // D_crater in meters
    const crater_depth_m = crater_diameter_m * 0.2; // Typical depth-to-diameter ratio
    
    return {
        crater_diameter_m: crater_diameter_m,
        crater_diameter_km: crater_diameter_m / 1000,
        crater_depth_m: crater_depth_m,
        crater_depth_km: crater_depth_m / 1000,
        crater_volume_m3: Math.PI * Math.pow(crater_diameter_m / 2, 2) * crater_depth_m,
        kinetic_energy_joules: kineticEnergy
    };
}

/**
 * Estimate casualties and damage based on impact location and population density.
 * 
 * @param {number} severe_radius_km - Severe damage radius in kilometers
 * @param {number} moderate_radius_km - Moderate damage radius in kilometers
 * @param {number} light_radius_km - Light damage radius in kilometers
 * @param {number} population_density - Population density in people per km²
 * @returns {object} Estimated casualties and affected area
 */
function estimateCasualties(severe_radius_km, moderate_radius_km, light_radius_km, population_density = 100) {
    const numericInputs = [severe_radius_km, moderate_radius_km, light_radius_km, population_density].map(Number);
    
    if (numericInputs.some(isNaN) || numericInputs.some(x => x < 0)) {
        throw new Error("All inputs must be non-negative numeric values.");
    }
    
    const [severe_r, moderate_r, light_r, pop_density] = numericInputs;
    
    // Calculate areas
    const severe_area_km2 = Math.PI * severe_r * severe_r;
    const moderate_area_km2 = Math.PI * moderate_r * moderate_r;
    const light_area_km2 = Math.PI * light_r * light_r;
    
    // Estimate casualties (simplified model)
    // Severe zone: 90% fatality rate
    // Moderate zone: 30% fatality rate  
    // Light zone: 5% fatality rate
    const severe_casualties = severe_area_km2 * pop_density * 0.9;
    const moderate_casualties = moderate_area_km2 * pop_density * 0.3;
    const light_casualties = light_area_km2 * pop_density * 0.05;
    
    const total_casualties = severe_casualties + moderate_casualties + light_casualties;
    
    return {
        severe_casualties: Math.round(severe_casualties),
        moderate_casualties: Math.round(moderate_casualties),
        light_casualties: Math.round(light_casualties),
        total_casualties: Math.round(total_casualties),
        affected_areas: {
            severe_area_km2: severe_area_km2,
            moderate_area_km2: moderate_area_km2,
            light_area_km2: light_area_km2,
            total_area_km2: severe_area_km2 + moderate_area_km2 + light_area_km2
        }
    };
}

/**
 * Convert asteroid data from NASA format to calculation parameters.
 * 
 * @param {object} nasaData - Data from NASA API (Sentry/SBDB)
 * @returns {object} Parameters suitable for impact calculations
 */
function convertNasaDataToParameters(nasaData) {
    // Extract and convert NASA data
    const diameter_km = parseFloat(nasaData.Diameter?.split(' ')[0]) || 0;
    const velocity_km_s = parseFloat(nasaData.Velocity?.split(' ')[0]) || 0;
    
    // Convert to meters and m/s
    const diameter_m = diameter_km * 1000;
    const velocity_m_s = velocity_km_s * 1000;
    
    // Assume typical asteroid density (kg/m³)
    // This could be improved with actual density data if available
    const density_kg_m3 = 3000; // Typical stony asteroid density
    
    return {
        diameter_m: diameter_m,
        velocity_m_s: velocity_m_s,
        density_kg_m3: density_kg_m3,
        original_data: nasaData
    };
}

/**
 * Comprehensive impact assessment combining all calculations.
 * 
 * @param {object} nasaData - Data from NASA API
 * @param {number} population_density - Population density in people per km² (optional)
 * @returns {object} Complete impact assessment
 */
function comprehensiveImpactAssessment(nasaData, population_density = 100) {
    try {
        // Convert NASA data to calculation parameters
        const params = convertNasaDataToParameters(nasaData);
        
        // Calculate impact radius and damage
        const impactResults = calculateImpactRadius(
            params.density_kg_m3,
            params.velocity_m_s,
            params.diameter_m
        );
        
        // Calculate crater dimensions
        const craterResults = calculateCraterDimensions(
            params.diameter_m,
            params.velocity_m_s,
            params.density_kg_m3
        );
        
        // Estimate casualties
        const casualtyResults = estimateCasualties(
            impactResults.severe_radius_km,
            impactResults.moderate_radius_km,
            impactResults.light_radius_km,
            population_density
        );
        
        return {
            asteroid_info: {
                designation: nasaData.des || nasaData.Full_Name || 'Unknown',
                diameter_km: params.diameter_m / 1000,
                velocity_km_s: params.velocity_m_s / 1000,
                density_kg_m3: params.density_kg_m3
            },
            impact_assessment: impactResults,
            crater_analysis: craterResults,
            casualty_estimation: casualtyResults,
            nasa_data: nasaData
        };
        
    } catch (error) {
        return {
            error: error.message,
            nasa_data: nasaData
        };
    }
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        calculateImpactRadius,
        calculateCraterDimensions,
        estimateCasualties,
        convertNasaDataToParameters,
        comprehensiveImpactAssessment
    };
} else {
    // Browser environment - attach to window object
    window.ImpactCalculator = {
        calculateImpactRadius,
        calculateCraterDimensions,
        estimateCasualties,
        convertNasaDataToParameters,
        comprehensiveImpactAssessment
    };
}

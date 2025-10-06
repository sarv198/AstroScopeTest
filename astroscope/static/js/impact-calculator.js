/**
 * Toggles the visibility of the detailed asteroid information.
 * This is used by the onclick handler in the leaderboard HTML.
 * @param {number} index - The zero-based index of the asteroid in the list.
 */
function toggleDetails(index) {
    const el = document.getElementById(`details-${index}`);
    el.classList.toggle('hidden');
}

// =======================================================
// PALERMO SCALE CALCULATOR LOGIC
// =======================================================

// DOM helpers
const $ = (id) => document.getElementById(id);

// Inputs
const modeEnergyEl = $('mode-energy');
const modeSizeEl = $('mode-size');
const blockEnergy = $('block-energy');
const blockSize = $('block-size');
const piEl = $('calc-pi');
const tiEl = $('calc-ti');
const EmtEl = $('calc-E-mt');
const dEl = $('calc-diam');
const vEl = $('calc-vel');
const rhoEl = $('calc-rho');
const fbEl = $('calc-fb');
const autoFbEl = $('calc-auto-fb');

// Outputs
const energyMtEl = $('calc-energy-mt');
const energyJEl = $('calc-energy-j');
const fbEchoEl = $('calc-fb-echo');
const fbNoteEl = $('calc-fb-note');
const psEl = $('calc-ps');
const psInterpEl = $('calc-ps-interp');

// Constants
const MT_J = 4.184e15; // Joules per Megaton of TNT
const PI = Math.PI;

// Background Frequency Constants (from NASA/JPL Sentry Documentation)
// Based on Diameter (D in km)
const A_d = 6.3e-3; 
const b_d = 2.7;
// Based on Energy (E in Mt)
const A_e = 1.1774080373049495e-2;
const alpha_e = 0.9;

/**
 * Estimates background impact frequency (f_B) based on asteroid diameter.
 * f_B = A_d * D^-b_d (where D is in km)
 * @param {number} d_m - Diameter in meters.
 * @returns {number|null} Estimated f_B in impacts/year.
 */
function estimateFBfromDiameter(d_m) {
    if (!d_m || d_m <= 0) return null;
    const d_km = d_m / 1000;
    const fb = A_d * Math.pow(d_km, -b_d);
    return (isFinite(fb) && fb > 0) ? fb : null;
}

/**
 * Estimates background impact frequency (f_B) based on kinetic energy.
 * f_B = A_e * E^-alpha_e (where E is in Mt)
 * @param {number} E_mt - Kinetic energy in Megatons of TNT.
 * @returns {number|null} Estimated f_B in impacts/year.
 */
function estimateFBfromEnergy(E_mt) {
    if (!E_mt || E_mt <= 0) return null;
    const fb = A_e * Math.pow(E_mt, -alpha_e);
    return (isFinite(fb) && fb > 0) ? fb : null;
}

/**
 * Calculates kinetic energy in Megatons from physical parameters.
 * E = 0.5 * m * v^2
 * @param {number} d_m - Diameter in meters.
 * @param {number} rho - Density in kg/m³.
 * @param {number} v_kms - Velocity in km/s.
 * @returns {number} Kinetic Energy in Megatons.
 */
function energyFromSizeMt(d_m, rho, v_kms) {
    if (!d_m || !rho || !v_kms || d_m <= 0 || rho <= 0 || v_kms <= 0) return NaN;
    // Volume (m³) * Density (kg/m³) = Mass (kg)
    const m = (PI / 6) * rho * Math.pow(d_m, 3);
    // Convert velocity to m/s
    const v = v_kms * 1000;
    // Energy in Joules
    const EJ = 0.5 * m * v * v;
    // Convert to Megatons
    return EJ / MT_J;
}

// Formatting functions
const fmtSci = (x) => (!isFinite(x) || x <= 0) ? '—' : x.toExponential(2).replace('+', '');
const fmtNum = (x, n = 2) => isFinite(x) ? Number(x).toFixed(n) : '—';

/**
 * Recalculates all output fields based on current input values.
 */
function recalc() {
    const Pi = parseFloat(piEl.value);
    const Ti = parseFloat(tiEl.value);
    let E_mt = NaN;
    let fbVal = parseFloat(fbEl.value);
    let fbSrc = 'manual';

    const usingEnergy = modeEnergyEl.checked;

    if (usingEnergy) {
        // 1. Get E_mt directly from the input
        E_mt = parseFloat(EmtEl.value);
        if (autoFbEl.checked) {
            // 2. Auto-estimate f_B from energy
            const est = estimateFBfromEnergy(E_mt);
            if (est) {
                fbVal = est;
                fbSrc = 'auto (from energy)';
                fbEl.value = est.toExponential(2);
            }
        }
    } else {
        // 1. Calculate E_mt from size/density/velocity
        const D = parseFloat(dEl.value);
        const v = parseFloat(vEl.value);
        const rho = parseFloat(rhoEl.value);
        E_mt = energyFromSizeMt(D, rho, v);
        
        if (autoFbEl.checked) {
            // 2. Auto-estimate f_B from diameter
            const est = estimateFBfromDiameter(D);
            if (est) {
                fbVal = est;
                fbSrc = 'auto (from diameter)';
                fbEl.value = est.toExponential(2);
            }
        }
    }

    // --- Energy Output ---
    const EJ = isFinite(E_mt) ? (E_mt * MT_J) : NaN;
    energyMtEl.textContent = isFinite(E_mt) ? `${fmtNum(E_mt, 2)} Mt` : '—';
    energyJEl.textContent = isFinite(EJ) ? `${fmtSci(EJ)} J` : '—';
    
    // --- f_B Output ---
    fbEchoEl.textContent = isFinite(fbVal) ? `${fmtSci(fbVal)} /yr` : '—';
    fbNoteEl.textContent = `source: ${fbSrc}`;

    // --- Palermo Scale Calculation ---
    let PS = NaN;
    if (isFinite(Pi) && Pi > 0 && isFinite(Ti) && Ti > 0 && isFinite(fbVal) && fbVal > 0) {
        // PS = log10( (Pi / Ti) / fB )
        PS = Math.log10((Pi / Ti) / fbVal);
    }
    
    // --- PS Output and Interpretation ---
    psEl.textContent = isFinite(PS) ? fmtNum(PS, 2) : '—';
    psInterpEl.textContent =
        isFinite(PS)
            ? (PS > 0 ? 'Above background risk' : (PS > -2 ? 'Comparable to background' : 'Well below background'))
            : '—';
}

/**
 * Synchronizes the visibility of the Energy and Size input blocks.
 */
function syncModeUI() {
    const usingEnergy = modeEnergyEl.checked;
    blockEnergy.classList.toggle('hidden', !usingEnergy);
    blockSize.classList.toggle('hidden', usingEnergy);
    recalc();
}

// Attach event listeners for mode changes
[modeEnergyEl, modeSizeEl].forEach(el => el.addEventListener('change', syncModeUI));

// Attach event listeners for input changes
['calc-pi', 'calc-ti', 'calc-E-mt', 'calc-diam', 'calc-vel', 'calc-rho', 'calc-fb', 'calc-auto-fb']
    .forEach(id => $(id)?.addEventListener('input', recalc));

// Initial setup and calculation on page load
document.addEventListener('DOMContentLoaded', () => {
    syncModeUI();
});
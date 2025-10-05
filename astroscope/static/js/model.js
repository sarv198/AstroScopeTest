import * as THREE from 'three';
let scene, camera, renderer, controls;
let clock = new THREE.Clock();
let simulationTime = new Date();
let timeSpeed = 1;
let isPaused = false;
let targetObject = null;
let desiredCameraOffset = new THREE.Vector3();

// Constants
const AU = 149597870.7; // 1 Astronomical Unit in Kilometers
const SUN_DIAMETER = 1392700; // Sun diameter in Kilometers
const J2000 = new Date('2000-01-01T12:00:00Z');

// TRUE SCALE FACTOR: 1 scene unit represents 10 million km.
const TRUE_SCALE_KM_PER_UNIT = 10000000;

// Orbital and Physical Data
const planetaryData = {
    mercury: { name: "Mercury", diameter: 4879, rotationPeriod: 1407.6, obliquity: 0.034, texture: '/static/assets/textures/mercury.jpg', a: 0.387098, e: 0.205630, i: 7.005, L: 252.25084, varpi: 77.45645, Omega: 48.33167, orbitalPeriod: 87.9691 },
    venus: { name: "Venus", diameter: 12104, rotationPeriod: -5832.5, obliquity: 177.4, texture: '/static/assets/textures/venus.jpg', a: 0.723332, e: 0.006772, i: 3.395, L: 181.97973, varpi: 131.53298, Omega: 76.68069, orbitalPeriod: 224.701 },
    earth: { name: "Earth", diameter: 12756, rotationPeriod: 23.9345, obliquity: 23.439, texture: '/static/assets/textures/earth.jpg', cloudTexture: '/static/assets/textures/earth-cloud.jpg', a: 1.000002, e: 0.016708, i: 0.000, L: 100.46435, varpi: 102.94719, Omega: 0.0, orbitalPeriod: 365.256 },
    mars: { name: "Mars", diameter: 6792, rotationPeriod: 24.6229, obliquity: 25.19, texture: '/static/assets/textures/mars.jpg', a: 1.523679, e: 0.09340, i: 1.850, L: 355.45332, varpi: 336.04084, Omega: 49.57854, orbitalPeriod: 686.980 },
    jupiter: { name: "Jupiter", diameter: 142984, rotationPeriod: 9.925, obliquity: 3.13, texture: '/static/assets/textures/jupiter.jpg', a: 5.2044, e: 0.0489, i: 1.303, L: 34.3964, varpi: 14.7284, Omega: 100.492, orbitalPeriod: 4332.59 },
    saturn: { name: "Saturn", diameter: 120536, rotationPeriod: 10.656, obliquity: 26.73, texture: '/static/assets/textures/saturn.jpg', ringTexture: '/static/assets/textures/saturn-rings.jpg', a: 9.5826, e: 0.0565, i: 2.485, L: 49.94432, varpi: 92.5988, Omega: 113.665, orbitalPeriod: 10759.22 },
    uranus: { name: "Uranus", diameter: 51118, rotationPeriod: -17.24, obliquity: 97.77, texture: '/static/assets/textures/uranus.jpg', a: 19.2294, e: 0.0457, i: 0.772, L: 313.23218, varpi: 170.96424, Omega: 74.22988, orbitalPeriod: 30688.5 },
    neptune: { name: "Neptune", diameter: 49528, rotationPeriod: 16.11, obliquity: 28.32, texture: '/static/assets/textures/neptune.jpg', a: 30.10366, e: 0.0113, i: 1.769, L: 304.88003, varpi: 44.97135, Omega: 131.72169, orbitalPeriod: 60182 },
    // pluto: { name: "Pluto", diameter: 2376, rotationPeriod: -153.3, obliquity: 122.5, texture: 'p', a: 39.482, e: 0.2488, i: 17.16, L: 238.9288, varpi: 224.06676, Omega: 110.30347, orbitalPeriod: 90560 }
};
const celestialObjects = {};
let scaleMode = 'enhanced';

// --- SCALE DEFINITIONS ---
// Enhanced scale uses logarithmic scaling for better visualization of small bodies/inner system
// Arbritary Scaling
const enhancedScale = {
    distance: (d) => Math.log10(d * AU / 1e6) * Math.sqrt(d) * 40 + 10 * Math.cbrt(Math.log10(d * AU / 1e4)),
    size: (s) => Math.log2(s)
};

// True Scale uses a consistent factor for both size and distance (1 unit = 10,000,000 km)
const trueScale = {
    distance: (d) => (d * AU) / TRUE_SCALE_KM_PER_UNIT,
    size: (s) => s / TRUE_SCALE_KM_PER_UNIT
};

let currentScale = enhancedScale;
// -------------------------


// Loading Manager for UI
const loadingManager = new THREE.LoadingManager();
const textureLoader = new THREE.TextureLoader(loadingManager);
loadingManager.onLoad = () => { setTimeout(() => { document.getElementById('loading-screen').style.opacity = '0'; document.getElementById('loading-screen').addEventListener('transitionend', () => document.getElementById('loading-screen').style.display = 'none'); }, 500); };
loadingManager.onProgress = (url, itemsLoaded, itemsTotal) => { document.getElementById('loading-bar').style.width = (itemsLoaded / itemsTotal) * 100 + '%'; };

function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x010409);
    camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 50000);
    camera.position.set(0, 400, 1200);
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    document.body.appendChild(renderer.domElement);
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    scene.add(new THREE.AmbientLight(0xffffff, 0.2));
    createSun(); createPlanets(); createNEOs(); createStars();
    setupUI();

    // Raycaster for object picking
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    window.addEventListener('click', (event) => {
        if (event.target.closest('.ui-panel')) return;
        mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        mouse.y = - (event.clientY / window.innerHeight) * 2 + 1;
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(scene.children, true);
        if (intersects.length > 0) {
            let clickedObject = intersects[0].object;
            // Traverse up to find the group with the celestial object key
            while (clickedObject.parent && !clickedObject.userData.key) { clickedObject = clickedObject.parent; }

            // Check if it's a planet or the sun
            if (clickedObject.userData.key && planetaryData[clickedObject.userData.key]) {
                displayInfo(planetaryData[clickedObject.userData.key]);
                targetObject = celestialObjects[clickedObject.userData.key].group;
                const targetRadius = currentScale.size(planetaryData[clickedObject.userData.key].diameter) / 2;
                // Set camera offset based on the scaled radius
                desiredCameraOffset.set(0, targetRadius * 40, targetRadius * 100);
            }
            // Handle NEO clicks
            if (clickedObject.userData && clickedObject.userData.designation) {
                targetObject = clickedObject.parent; // Focus on the asteroid group
                populateStatsPanel();
                // Set camera offset for NEOs
                desiredCameraOffset.set(0, 5, 10); // Fixed small offset for tiny NEOs
            }
            // Legacy NEO handling (fallback)
            else if (clickedObject.userData && clickedObject.userData.a) {
                targetObject = clickedObject;
                desiredCameraOffset.set(0, 5, 10); // Fixed small offset for tiny NEOs
            }
        }
    });

    window.addEventListener('resize', onWindowResize);
    animate();
}

function createSun() {
    // FIX: Use unit geometry and apply scale in updateScales for consistency
    const sunGeometry = new THREE.SphereGeometry(1, 64, 64);
    const sunMaterial = new THREE.MeshBasicMaterial({ map: textureLoader.load('/static/assets/textures/sun.jpg'), color: 0xffddaa });
    const sun = new THREE.Mesh(sunGeometry, sunMaterial);
    sun.name = "Sun";
    sun.userData.key = 'sun';
    sun.userData.diameter = SUN_DIAMETER; // Store the true physical diameter
    scene.add(sun);
    celestialObjects.sun = { group: sun };
    // Add a point light at the Sun's position
    sun.add(new THREE.PointLight(0xffffff, 1.8, 40000));
}

function makeTextSprite(message, opts) {
    const parameters = opts || {};
    const fontface = parameters.fontface || 'Roboto Mono';
    const fontsize = parameters.fontsize || 18;
    const textColor = parameters.textColor || { r: 201, g: 209, d: 217, a: 1.0 };
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    context.font = `Bold ${fontsize}px ${fontface}`;
    const metrics = context.measureText(message);
    const textWidth = metrics.width;
    canvas.width = textWidth + 10;
    canvas.height = fontsize + 10;
    context.font = `Bold ${fontsize}px ${fontface}`;
    context.fillStyle = `rgba(${textColor.r}, ${textColor.g}, ${textColor.d}, ${textColor.a})`;
    context.fillText(message, 5, fontsize);
    const texture = new THREE.Texture(canvas);
    texture.needsUpdate = true;
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture, depthTest: false });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(canvas.width / 4, canvas.height / 4, 1.0);
    return sprite;
}

function createPlanets() {
    Object.keys(planetaryData).forEach(key => {
        const data = planetaryData[key];
        const planetGroup = new THREE.Group();
        planetGroup.name = data.name;
        planetGroup.userData.key = key;

        // Planet Mesh (unit sphere geometry)
        const geometry = new THREE.SphereGeometry(1, 64, 64);
        const material = new THREE.MeshStandardMaterial({ map: textureLoader.load(data.texture), roughness: 0.8, metalness: 0.1 });
        const planet = new THREE.Mesh(geometry, material);
        planet.castShadow = true; planet.receiveShadow = true;
        planet.rotation.z = THREE.MathUtils.degToRad(data.obliquity); // Axial tilt
        planetGroup.add(planet);

        // Additional features (Clouds, Rings)
        if (data.cloudTexture) {
            // Use a slightly larger radius for the clouds
            const clouds = new THREE.Mesh(new THREE.SphereGeometry(1.01, 64, 64), new THREE.MeshStandardMaterial({ map: textureLoader.load(data.cloudTexture), transparent: true, opacity: 0.8, depthWrite: false }));
            planetGroup.add(clouds);
            celestialObjects.earthClouds = clouds;
        }
        if (data.ringTexture) {
            const ring = new THREE.Mesh(new THREE.RingGeometry(1.2, 2, 64), new THREE.MeshBasicMaterial({ map: textureLoader.load(data.ringTexture), side: THREE.DoubleSide, transparent: true, opacity: 0.9 }));
            ring.rotation.x = Math.PI / 2;
            planetGroup.add(ring);
        }

        // ORBIT PATH GENERATION
        const a = currentScale.distance(data.a), b = a * Math.sqrt(1 - data.e ** 2);
        const curve = new THREE.EllipseCurve(-a * data.e, 0, a, b, 0, 2 * Math.PI, false, 0);
        const points = curve.getPoints(200);

        // Transform the 2D Ecliptic (X, Y) points into the 3D Three.js (X, 0, -Y) plane
        const transformedPoints = points.map(p => new THREE.Vector3(p.x, 0, -p.y));

        const orbitGeometry = new THREE.BufferGeometry().setFromPoints(transformedPoints);
        const orbitMaterial = new THREE.LineBasicMaterial({ color: 0x30363d });
        const orbit = new THREE.Line(orbitGeometry, orbitMaterial);

        // Set up the correct Group hierarchy for the Ecliptic rotations (Z(omega) -> X(i) -> Z(Omega)).
        const omega = data.varpi - data.Omega; // Argument of Perihelion (ω)

        // 1. Innermost rotation: Argument of Perihelion (ω) - Rot Y (in Three.js)
        const group_omega = new THREE.Group();
        group_omega.rotation.y = THREE.MathUtils.degToRad(omega);
        group_omega.add(orbit);

        // 2. Middle rotation: Inclination (i) - Rot X (in Three.js)
        const group_i = new THREE.Group();
        group_i.rotation.x = THREE.MathUtils.degToRad(data.i);
        group_i.add(group_omega);

        // 3. Outermost rotation: Longitude of Ascending Node (Ω) - Rot Y (in Three.js)
        const group_Omega = new THREE.Group();
        group_Omega.rotation.y = THREE.MathUtils.degToRad(data.Omega);
        group_Omega.add(group_i);

        scene.add(group_Omega);

        // Label and final setup
        const label = makeTextSprite(data.name);
        planetGroup.add(label);
        scene.add(planetGroup);

        // Store the outermost group as the orbit for visibility/scaling
        celestialObjects[key] = { group: planetGroup, planet: planet, orbit: group_Omega, label: label };
    });
    updateScales();
}

async function createNEOs() {
    const neosGroup = new THREE.Group();
    neosGroup.name = "NEOs"; neosGroup.userData.key = "neos";
    
    try {
        // Step 1: Fetch NEO data from Flask backend
        console.log("Fetching NEO data from backend...");
        const response = await fetch('/api/neo_data/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: 20 }) // Limit to 20 for performance
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const neoData = await response.json();
        console.log("NEO data received:", neoData);
        
        // Step 2: Extract list of designations
        const designations = neoData.list_of_des || [];
        console.log(`Found ${designations.length} asteroid designations`);
        
        if (designations.length === 0) {
            console.warn("No asteroid designations found");
            scene.add(neosGroup);
            celestialObjects.neos = { group: neosGroup };
            return;
        }
        
        // Step 3: Query orbital parameters for each designation
        const orbitalParamsUrl = `/api/orbital_params/?${designations.map(des => `des=${encodeURIComponent(des)}`).join('&')}`;
        console.log("Fetching orbital parameters...");
        
        const orbitalResponse = await fetch(orbitalParamsUrl);
        if (!orbitalResponse.ok) {
            throw new Error(`Orbital params HTTP error! status: ${orbitalResponse.status}`);
        }
        
        const orbitalData = await orbitalResponse.json();
        console.log("Orbital data received:", orbitalData);
        
        // Step 4: Create orbital paths and asteroid markers
        let createdCount = 0;
        for (const des of designations) {
            if (orbitalData[des] && orbitalData[des].length > 0) {
                const orbitPoints = orbitalData[des];
                createAsteroidOrbit(des, orbitPoints, neosGroup, neoData.data[des]);
                createdCount++;
            }
        }
        
        console.log(`Created ${createdCount} asteroid orbits out of ${designations.length} designations`);
        
    } catch (error) {
        console.error("Error loading real NEO data:", error);
        // Fallback to creating a few fake NEOs if real data fails
        console.log("Creating fallback fake NEOs...");
        createFallbackNEOs(neosGroup);
    }
    
    scene.add(neosGroup);
    celestialObjects.neos = { group: neosGroup };
}

function createAsteroidOrbit(designation, orbitPoints, parentGroup, neoInfo) {
    // Create orbital path geometry
    const orbitGeometry = new THREE.BufferGeometry().setFromPoints(orbitPoints);
    const orbitMaterial = new THREE.LineBasicMaterial({ 
        color: 0x87CEEB, // Light blue
        opacity: 0.6,
        transparent: true
    });
    const orbitLine = new THREE.Line(orbitGeometry, orbitMaterial);
    orbitLine.name = `${designation} Orbit`;
    
    // Create asteroid marker
    const enhancedRadius = 0.8; // Base size for visibility
    const asteroid = new THREE.Mesh(
        new THREE.SphereGeometry(enhancedRadius, 8, 6),
        new THREE.MeshStandardMaterial({ 
            color: 0xcc3333, 
            roughness: 0.8, 
            metalness: 0.2 
        })
    );
    asteroid.name = designation;
    asteroid.userData = {
        key: designation,
        designation: designation,
        enhancedRadius: enhancedRadius,
        neoInfo: neoInfo || {}
    };
    
    // Position asteroid at first point of orbit
    if (orbitPoints.length > 0) {
        asteroid.position.copy(orbitPoints[0]);
    }
    
    // Create a group for this asteroid and its orbit
    const asteroidGroup = new THREE.Group();
    asteroidGroup.name = `${designation} Group`;
    asteroidGroup.add(asteroid);
    asteroidGroup.add(orbitLine);
    
    parentGroup.add(asteroidGroup);
    
    console.log(`Created orbit for ${designation}`);
}

function createFallbackNEOs(neosGroup) {
    // Fallback function to create fake NEOs if real data fails
    const neoCount = 10;
    for (let i = 0; i < neoCount; i++) {
        const enhancedRadius = Math.random() * 1.5 + 0.5;
        const neo = new THREE.Mesh(
            new THREE.DodecahedronGeometry(enhancedRadius, 0),
            new THREE.MeshStandardMaterial({ color: 0xcc3333, roughness: 0.8, metalness: 0.2 })
        );

        const a_au = Math.random() * 3 + 0.5, e = Math.random() * 0.7 + 0.1, inc = Math.random() * 20, M0 = Math.random() * 360;
        const Omega = Math.random() * 360, varpi = Math.random() * 360;
        const period = Math.sqrt(a_au ** 3) * 365.25;

        neo.userData = { a: a_au, e, i: inc, L: (M0 + varpi) % 360, varpi, Omega, orbitalPeriod: period, enhancedRadius };
        neosGroup.add(neo);
    }
}

function createStars() {
    const starVertices = [];
    for (let i = 0; i < 10000; i++) starVertices.push((Math.random() - 0.5) * 20000, (Math.random() - 0.5) * 20000, (Math.random() - 0.5) * 20000);
    const starGeometry = new THREE.BufferGeometry();
    starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starVertices, 3));
    // Dimmed the stars by changing color to 0x888888 and size to 1.0
    scene.add(new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: 0x888888, size: 1.0, sizeAttenuation: false })));
}

function setupUI() {
    document.getElementById('date-display').textContent = simulationTime.toUTCString().replace("GMT", "UTC");
    document.getElementById('scale-enhanced-btn').addEventListener('click', () => { scaleMode = 'enhanced'; currentScale = enhancedScale; updateScales(); document.getElementById('scale-enhanced-btn').classList.add('active'); document.getElementById('scale-true-btn').classList.remove('active'); });
    document.getElementById('scale-true-btn').addEventListener('click', () => { scaleMode = 'true'; currentScale = trueScale; updateScales(); document.getElementById('scale-true-btn').classList.add('active'); document.getElementById('scale-enhanced-btn').classList.remove('active'); });
    const slider = document.getElementById('time-speed-slider'), speedLabel = document.getElementById('time-speed-label');
    const updateSpeed = () => { const val = parseInt(slider.value), minp = 0, maxp = 1000, minv = Math.log(1), maxv = Math.log(86400 * 365 * 20), scale = (maxv - minv) / (maxp - minp); timeSpeed = Math.exp(minv + scale * (val - minp)); speedLabel.textContent = formatTimeSpeed(timeSpeed); };
    slider.addEventListener('input', updateSpeed);
    timeSpeed = 86400; const minp = 0, maxp = 1000, minv = Math.log(1), maxv = Math.log(86400 * 365 * 20), scale = (maxv - minv) / (maxp - minp); slider.value = (Math.log(timeSpeed) - minv) / scale + minp; updateSpeed();
    document.getElementById('play-pause-btn').addEventListener('click', () => { isPaused = !isPaused; document.getElementById('play-pause-btn').innerHTML = isPaused ? '&#9658;' : '&#10074;&#10074;'; });
    document.getElementById('time-forward-btn').addEventListener('click', () => { slider.value = Math.min(parseInt(slider.value) + 50, 1000); slider.dispatchEvent(new Event('input')); });
    document.getElementById('time-backward-btn').addEventListener('click', () => { slider.value = Math.max(parseInt(slider.value) - 50, 0); slider.dispatchEvent(new Event('input')); });


    document.getElementById('info-close-btn').addEventListener('click', () => { document.getElementById('info-panel').style.display = 'none'; targetObject = null; });
    document.getElementById('stats-close-btn').addEventListener('click', () => { document.getElementById('stats-panel').style.display = 'none'; targetObject = null; });
    document.getElementById('focus-sun-btn').addEventListener('click', () => { targetObject = celestialObjects.sun.group; desiredCameraOffset.set(0, 100, 250); });
    document.getElementById('focus-earth-btn').addEventListener('click', () => { targetObject = celestialObjects.earth.group; desiredCameraOffset.set(0, 40, 135); });
    document.getElementById('labels-on-btn').addEventListener('click', (e) => { setLabelsVisible(true); e.target.classList.add('active'); document.getElementById('labels-off-btn').classList.remove('active'); });
    document.getElementById('labels-off-btn').addEventListener('click', (e) => { setLabelsVisible(false); e.target.classList.add('active'); document.getElementById('labels-on-btn').classList.remove('active'); });
    document.getElementById('planet-on-btn').addEventListener('click', (e) => { setPlanetVisible(true); e.target.classList.add('active'); document.getElementById('planet-off-btn').classList.remove('active'); });
    document.getElementById('planet-off-btn').addEventListener('click', (e) => { setPlanetVisible(false); e.target.classList.add('active'); document.getElementById('planet-on-btn').classList.remove('active'); });
    document.getElementById('planet-tra-on-btn').addEventListener('click', (e) => { setPlanetTraVisible(true); e.target.classList.add('active'); document.getElementById('planet-tra-off-btn').classList.remove('active'); });
    document.getElementById('planet-tra-off-btn').addEventListener('click', (e) => { setPlanetTraVisible(false); e.target.classList.add('active'); document.getElementById('planet-tra-on-btn').classList.remove('active'); });
    document.getElementById('neo-on-btn').addEventListener('click', (e) => { setNEOVisible(true); e.target.classList.add('active'); document.getElementById('neo-off-btn').classList.remove('active'); });
    document.getElementById('neo-off-btn').addEventListener('click', (e) => { setNEOVisible(false); e.target.classList.add('active'); document.getElementById('neo-on-btn').classList.remove('active'); });
    document.getElementById('neo-tra-on-btn').addEventListener('click', (e) => { setNEOTraVisible(true); e.target.classList.add('active'); document.getElementById('neo-tra-off-btn').classList.remove('active'); });
    document.getElementById('neo-tra-off-btn').addEventListener('click', (e) => { setNEOTraVisible(false); e.target.classList.add('active'); document.getElementById('neo-tra-on-btn').classList.remove('active'); });
    populateStatsPanel();
}

function populateStatsPanel() {
    // Data from CNEOS NEO Discovery Totals vs. Time for 2025-10-03
    const stats = {
        "Total NEOs": "39,689",
        "Total NEAs": "39,566",
        "Potentially Hazardous (PHA)": "2,511",
        "Atens": "3,183",
        "Apollos": "22,425",
        "Amors": "13,920"
    };
    const content = document.getElementById('stats-content');
    content.innerHTML = `<div class="info-item"><span class="info-label text-xs">CNEOS Data as of 2025-10-03</span></div>`;
    for (const [key, value] of Object.entries(stats)) {
        content.innerHTML += `<div class="info-item"><span class="info-label">${key}</span><span class="info-value">${value}</span></div>`;
    }
}

function setLabelsVisible(visible) { Object.keys(planetaryData).forEach(key => { if (celestialObjects[key] && celestialObjects[key].label) celestialObjects[key].label.visible = visible; }); }
function setPlanetVisible(visible) { Object.keys(planetaryData).forEach(key => { if (celestialObjects[key] && celestialObjects[key].group) celestialObjects[key].group.visible = visible; }); }
function setPlanetTraVisible(visible) { Object.keys(planetaryData).forEach(key => { if (celestialObjects[key] && celestialObjects[key].orbit) celestialObjects[key].orbit.visible = visible; }); }
function setNEOVisible(visible) {
    if (celestialObjects.neos && celestialObjects.neos.group) {
        celestialObjects.neos.group.children.forEach(neoGroup => {
            if (neoGroup.children && neoGroup.children.length > 0) {
                const asteroid = neoGroup.children.find(child => child.userData && child.userData.enhancedRadius);
                if (asteroid) asteroid.visible = visible;
            }
        });
    }
}
function setNEOTraVisible(visible) {
    if (celestialObjects.neos && celestialObjects.neos.group) {
        celestialObjects.neos.group.children.forEach(neoGroup => {
            if (neoGroup.children && neoGroup.children.length > 0) {
                const orbitLine = neoGroup.children.find(child => child.name && child.name.includes('Orbit'));
                if (orbitLine) orbitLine.visible = visible;
            }
        });
    }
}
function formatTimeSpeed(speed) { if (speed < 60) return `${speed.toFixed(1)} sec/sec`; if (speed < 3600) return `${(speed / 60).toFixed(1)} min/sec`; if (speed < 86400) return `${(speed / 3600).toFixed(1)} hours/sec`; if (speed < 86400 * 30.44) return `${(speed / 86400).toFixed(1)} days/sec`; if (speed < 86400 * 365.25) return `${(speed / (86400 * 30.44)).toFixed(1)} months/sec`; return `${(speed / (86400 * 365.25)).toFixed(1)} years/sec`; }

function displayInfo(data) { document.getElementById('info-title').textContent = data.name; document.getElementById('info-content').innerHTML = `<div class="info-item"><span class="info-label">Diameter</span><span class="info-value">${data.diameter.toLocaleString()} km</span></div><div class="info-item"><span class="info-label">Orbital Period</span><span class="info-value">${data.orbitalPeriod.toFixed(2)} days</span></div><div class="info-item"><span class="info-label">Rotation Period</span><span class="info-value">${Math.abs(data.rotationPeriod)} hours</span></div><div class="info-item"><span class="info-label">Axial Tilt</span><span class="info-value">${data.obliquity}°</span></div><div class="info-item"><span class="info-label">Eccentricity</span><span class="info-value">${data.e}</span></div>`; document.getElementById('info-panel').style.display = 'block'; document.getElementById('stats-panel').style.display = 'none'; }


function updateScales() {
    // SUN SCALING
    const scaledSunSize = currentScale.size(SUN_DIAMETER); // Calculate scaled radius
    celestialObjects.sun.group.scale.setScalar(scaledSunSize);

    // PLANET SCALING
    Object.keys(planetaryData).forEach(key => {
        const data = planetaryData[key], obj = celestialObjects[key], scaledSize = currentScale.size(data.diameter);

        // Planet and Cloud Scaling
        obj.planet.scale.set(scaledSize, scaledSize, scaledSize);
        if (key === 'earth' && celestialObjects.earthClouds) celestialObjects.earthClouds.scale.set(scaledSize, scaledSize, scaledSize);

        // Ring Scaling (scale is based on planet size)
        if (data.ringTexture) {
            const ring = obj.group.children.find(c => c.geometry instanceof THREE.RingGeometry);
            if (ring) ring.scale.set(scaledSize, scaledSize, scaledSize);
        }

        // Orbit Path Scaling
        const a = currentScale.distance(data.a), b = a * Math.sqrt(1 - data.e ** 2);
        const curve = new THREE.EllipseCurve(-a * data.e, 0, a, b, 0, 2 * Math.PI, false, 0);

        // Re-calculate and transform points to match the scaling change
        const points = curve.getPoints(200);
        const transformedPoints = points.map(p => new THREE.Vector3(p.x, 0, -p.y));

        // The actual THREE.Line object is deep in the group hierarchy
        if (obj.orbit && obj.orbit.children.length > 0 && obj.orbit.children[0].children.length > 0 && obj.orbit.children[0].children[0].children.length > 0) {
            const lineObject = obj.orbit.children[0].children[0].children[0];
            lineObject.geometry.setFromPoints(transformedPoints);
        }
    });

    // NEO SCALING
    if (celestialObjects.neos && celestialObjects.neos.group) {
        celestialObjects.neos.group.children.forEach(neoGroup => {
            if (neoGroup.children && neoGroup.children.length > 0) {
                const asteroid = neoGroup.children.find(child => child.userData && child.userData.enhancedRadius);
                if (asteroid && asteroid.userData) {
                    const data = asteroid.userData;
                    if (scaleMode === 'enhanced') {
                        // In Enhanced mode, the geometry is already sized correctly, so we set the scale back to 1.
                        asteroid.scale.setScalar(1);
                    } else if (scaleMode === 'true') {
                        // In True Scale mode, we scale them down significantly to a representative 1km size.
                        const TRUE_NEO_DIAMETER_KM = 1;
                        const scaledTrueRadius = trueScale.size(TRUE_NEO_DIAMETER_KM) / 2;

                        // Scale factor = (Target True Radius) / (Current Enhanced Radius)
                        const scaleFactor = scaledTrueRadius / data.enhancedRadius;
                        asteroid.scale.setScalar(scaleFactor);
                    }
                }
            }
        });
    }
}

function updatePositions(elapsedTime) {
    if (isPaused) return;
    simulationTime = new Date(simulationTime.getTime() + elapsedTime * timeSpeed * 1000);
    document.getElementById('date-display').textContent = simulationTime.toUTCString().replace("GMT", "UTC");
    const daysSinceJ2000 = (simulationTime.getTime() - J2000.getTime()) / 86400000;

    // Collect all bodies (planets and NEOs) for position update
    let neoDataList = [];
    if (celestialObjects.neos && celestialObjects.neos.group) {
        // Extract NEO data from the new group structure
        neoDataList = celestialObjects.neos.group.children
            .filter(child => child.children && child.children.length > 0)
            .map(neoGroup => neoGroup.children.find(child => child.userData && child.userData.enhancedRadius))
            .filter(neo => neo && neo.userData)
            .map(neo => neo.userData);
    }
    const allBodies = { ...planetaryData, ...Object.fromEntries(neoDataList.map((data, i) => [`neo_${i}`, data])) };

    Object.keys(allBodies).forEach(key => {
        const data = allBodies[key];
        const isNeo = key.startsWith('neo');
        const objGroup = isNeo ? celestialObjects.neos.group.children[parseInt(key.split('_')[1])] : celestialObjects[key].group;
        if (!objGroup) return;

        // Calculate Mean Anomaly (M)
        const M0 = data.L - data.varpi;
        const n = 360 / data.orbitalPeriod;
        const M = (M0 + n * daysSinceJ2000) % 360;

        // Solve Kepler's equation for Eccentric Anomaly (E)
        const E = solveKepler(THREE.MathUtils.degToRad(M), data.e);

        // Calculate orbital coordinates (x_orb, y_orb) in the orbital plane (x-axis toward perihelion)
        const a_scaled = currentScale.distance(data.a);
        const x_orb = a_scaled * (Math.cos(E) - data.e);
        const y_orb = a_scaled * Math.sqrt(1 - data.e ** 2) * Math.sin(E);

        const omega = data.varpi - data.Omega;

        // Define rotation matrices (Z(omega) -> X(i) -> Z(Omega))
        const mOmega = new THREE.Matrix4().makeRotationZ(THREE.MathUtils.degToRad(data.Omega));
        const mI = new THREE.Matrix4().makeRotationX(THREE.MathUtils.degToRad(data.i));
        const m_omega = new THREE.Matrix4().makeRotationZ(THREE.MathUtils.degToRad(omega));

        // Apply rotations to transform from Orbital Plane to Ecliptic Plane
        const pos = new THREE.Vector3(x_orb, y_orb, 0);
        pos.applyMatrix4(m_omega).applyMatrix4(mI).applyMatrix4(mOmega);

        // Map Ecliptic (X, Y, Z) to Three.js World (X, Z, -Y)
        objGroup.position.set(pos.x, pos.z, -pos.y);

        if (!isNeo) {
            const rotation = (elapsedTime * (timeSpeed / (data.rotationPeriod * 3600))) * 2 * Math.PI;
            celestialObjects[key].planet.rotation.y += rotation;
            if (key === 'earth' && celestialObjects.earthClouds) celestialObjects.earthClouds.rotation.y += rotation * 1.2;
            // Label position based on scaled diameter
            const scaledDiameter = currentScale.size(data.diameter);
            celestialObjects[key].label.position.y = scaledDiameter * 1.5 + 5;
        }
    });
}

// Kepler solver for E from M
function solveKepler(M, e) { let E = M; for (let i = 0; i < 7; i++) E = E - (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E)); return E; }

function onWindowResize() { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); }

function animate() {
    requestAnimationFrame(animate);
    const elapsedTime = clock.getDelta();
    updatePositions(elapsedTime);

    // Camera follow logic
    if (targetObject) {
        const targetPosition = new THREE.Vector3();
        targetObject.getWorldPosition(targetPosition);

        // Position camera offset from target based on current scaling
        const desiredPosition = targetPosition.clone().add(desiredCameraOffset);

        camera.position.lerp(desiredPosition, 0.05);
        controls.target.lerp(targetPosition, 0.05);
    }
    controls.update();
    renderer.render(scene, camera);
}
init();

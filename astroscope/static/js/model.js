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
    mercury: { name: "Mercury", diameter: 4879, rotationPeriod: 1407.6, obliquity: 0.034, texture: '/static/assets/mercury.jpg', a: 0.387098, e: 0.205630, i: 7.005, L: 252.25084, varpi: 77.45645, Omega: 48.33167, orbitalPeriod: 87.9691 },
    venus: { name: "Venus", diameter: 12104, rotationPeriod: -5832.5, obliquity: 177.4, texture: '/static/assets/venus.jpg', a: 0.723332, e: 0.006772, i: 3.395, L: 181.97973, varpi: 131.53298, Omega: 76.68069, orbitalPeriod: 224.701 },
    earth: { name: "Earth", diameter: 12756, rotationPeriod: 23.9345, obliquity: 23.439, texture: '/static/assets/earth.jpg', cloudTexture: '/static/assets/earth-cloud.jpg', a: 1.000002, e: 0.016708, i: 0.000, L: 100.46435, varpi: 102.94719, Omega: 0.0, orbitalPeriod: 365.256 },
    mars: { name: "Mars", diameter: 6792, rotationPeriod: 24.6229, obliquity: 25.19, texture: '/static/assets/mars.jpg', a: 1.523679, e: 0.09340, i: 1.850, L: 355.45332, varpi: 336.04084, Omega: 49.57854, orbitalPeriod: 686.980 },
    jupiter: { name: "Jupiter", diameter: 142984, rotationPeriod: 9.925, obliquity: 3.13, texture: '/static/assets/jupiter.jpg', a: 5.2044, e: 0.0489, i: 1.303, L: 34.3964, varpi: 14.7284, Omega: 100.492, orbitalPeriod: 4332.59 },
    saturn: { name: "Saturn", diameter: 120536, rotationPeriod: 10.656, obliquity: 26.73, texture: '/static/assets/saturn.jpg', ringTexture: '/static/assets/saturn-rings.jpg', a: 9.5826, e: 0.0565, i: 2.485, L: 49.94432, varpi: 92.5988, Omega: 113.665, orbitalPeriod: 10759.22 },
    uranus: { name: "Uranus", diameter: 51118, rotationPeriod: -17.24, obliquity: 97.77, texture: '/static/assets/uranus.jpg', a: 19.2294, e: 0.0457, i: 0.772, L: 313.23218, varpi: 170.96424, Omega: 74.22988, orbitalPeriod: 30688.5 },
    neptune: { name: "Neptune", diameter: 49528, rotationPeriod: 16.11, obliquity: 28.32, texture: '/static/assets/neptune.jpg', a: 30.10366, e: 0.0113, i: 1.769, L: 304.88003, varpi: 44.97135, Omega: 131.72169, orbitalPeriod: 60182 },
    // pluto: { name: "Pluto", diameter: 2376, rotationPeriod: -153.3, obliquity: 122.5, texture: 'p', a: 39.482, e: 0.2488, i: 17.16, L: 238.9288, varpi: 224.06676, Omega: 110.30347, orbitalPeriod: 90560 }
};
const celestialObjects = {};
let scaleMode = 'enhanced';


// Orbital data


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
            if (clickedObject.userData.key && celestialObjects.neo[clickedObject.userData.key]) {
                targetObject = celestialObjects.neo[clickedObject.userData.key].group;
                populateStatsPanel();
                const targetRadius = currentScale.size(planetaryData[clickedObject.userData.key].diameter) / 2;
                // Set camera offset based on the scaled radius
                desiredCameraOffset.set(0, targetRadius * 40, targetRadius * 100);
            }
            // NEOs don't have detailed info, but we can still focus on them.
            else if (clickedObject.userData.a) {
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
    const sunMaterial = new THREE.MeshBasicMaterial({ map: textureLoader.load('/static/assets/sun.jpg'), color: 0xffddaa });
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

// Function to create a THREE.Line object from the flattened array of coordinates
function createOrbitLine(flattenedPoints) {
    // 1. Create a Float32Array for better performance
    const positions = new Float32Array(flattenedPoints);

    // 2. Create the Geometry
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    // 3. Create the Material (light blue for the orbit line)
    const material = new THREE.LineBasicMaterial({ color: 0x3399ff, linewidth: 1 });

    // 4. Create the Line object
    const line = new THREE.Line(geometry, material);
    return line;
}

// Ensure this function is declared as async to use await
async function createNEOs() {
    // 1. Placeholder data (or use your fetch logic)
const neoData = [
        {
            "name": "1979 XB",
            "a": 2.23,
            "e": 0.708,
            "i": 24.7,
            "Omega": 86.1,
            "varpi": 75.6,
            "M0": 2444267.667
        },
        {
            "name": "2022 KK2",
            "a": 1.2,
            "e": 0.513,
            "i": 3.12,
            "Omega": 58.9,
            "varpi": 75.3,
            "M0": 2459660.086
        },
        {
            "name": "2000 SG344",
            "a": 0.977,
            "e": 0.0669,
            "i": 0.113,
            "Omega": 192.0,
            "varpi": 276.0,
            "M0": 2461083.186
        },
        {
            "name": "2012 VS76",
            "a": 0.991,
            "e": 0.386,
            "i": 0.807,
            "Omega": 242.0,
            "varpi": 285.0,
            "M0": 2461000.873
        }
    ];

    const neosGroup = new THREE.Group();
    neosGroup.name = "NEOs";
    neosGroup.userData.key = "neos";
    
    // An array to hold all the NEO groups, which will be the children of neosGroup
    const neoGroups = []; 

    // 2. Iterate through the Keplerian data to create meshes and orbits
    neoData.forEach((data, index) => {
        const enhancedRadius = 0.8; 
        const a_au = data.a;
        const orbitalPeriod = Math.sqrt(a_au ** 3) * 365.25;
        const L = data.M0 !== undefined ? (data.M0 + data.varpi) % 360 : data.L || 0;

        // --- NEO MESH SETUP ---
        const neoMesh = new THREE.Mesh(
            new THREE.DodecahedronGeometry(enhancedRadius, 0),
            new THREE.MeshStandardMaterial({ 
                color: 0xcc3333, // Red color
                roughness: 0.8, metalness: 0.2 
            })
        );
        neoMesh.userData = { 
            a: a_au, e: data.e, i: data.i, L: L, 
            varpi: data.varpi || 0, Omega: data.Omega || 0, 
            orbitalPeriod: orbitalPeriod, enhancedRadius: enhancedRadius 
        };
        
        // NEO GROUP (Holds the mesh and the label)
        const neoGroup = new THREE.Group();
        neoGroup.name = data.name;
        neoGroup.userData = neoMesh.userData; // Group holds the orbital data
        neoGroup.add(neoMesh);
        // Position set by updatePositions() later
        
        // --- ORBIT PATH GENERATION (Matching Planet Logic) ---
        
        // Initial setup for the geometry. The points will be set in updateScales().
        // We use a dummy point count here, which will be updated immediately.
        const orbitGeometry = new THREE.BufferGeometry(); 
        const orbitMaterial = new THREE.LineBasicMaterial({ color: 0x3399ff, linewidth: 1 });
        const orbit = new THREE.Line(orbitGeometry, orbitMaterial);
        orbit.name = `OrbitLine_${index}`;
        
        // Store the orbit line in the NEO group's userData for easy access in updateScales()
        neoGroup.userData.orbitLine = orbit;

        // Set up the correct Group hierarchy for the Ecliptic rotations
        const omega = data.varpi; 

        // 1. Innermost rotation: Argument of Perihelion (ω) - Rot Y (in Three.js)
        // NOTE: Planets use varpi - Omega here, but for NEOs, we'll align the
        // rotation logic with the single-matrix approach for simplicity and performance,
        // which often assumes 'varpi' is the true rotation angle in the ecliptic.
        // HOWEVER, to match your planet logic:
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

        // Add the rotation hierarchy (which contains the orbit line) to the scene
        scene.add(group_Omega);

        // Store the outermost rotation group for visibility/scaling updates
        neoGroup.userData.orbitRotationGroup = group_Omega;
        
        // Add the NEO group (which contains the mesh) to the parent NEOs group
        neosGroup.add(neoGroup);
    });

    // 3. Final Setup
    scene.add(neosGroup);
    // Store the main NEOs group and the inner groups for easy access
    celestialObjects.neos = { group: neosGroup, neoGroups: neoGroups };
    
    // Call updateScales() to immediately generate the orbit paths and scale meshes
    updateScales(); 
    
    return neosGroup;
}

// Fallback function (optional, for error handling)
function createNEOsRandomFallback() {
    const neoCount = 150, neosGroup = new THREE.Group();
    neosGroup.name = "NEOs"; neosGroup.userData.key = "neos";
    for (let i = 0; i < neoCount; i++) {
        // Increased base size for Enhanced mode visibility (Radius 0.5 to 2.0)
        const enhancedRadius = Math.random() * 1.5 + 0.5;

        // NEO meshes are now red (0xcc3333) and use the larger enhancedRadius
        const neo = new THREE.Mesh(new THREE.DodecahedronGeometry(enhancedRadius, 0),
            new THREE.MeshStandardMaterial({ color: 0xcc3333, roughness: 0.8, metalness: 0.2 }));

        const a_au = Math.random() * 3 + 0.5, e = Math.random() * 0.7 + 0.1, inc = Math.random() * 20, M0 = Math.random() * 360;
        const Omega = Math.random() * 360, varpi = Math.random() * 360;
        const period = Math.sqrt(a_au ** 3) * 365.25;

        // Store the base size for reference and orbital data
        neo.userData = { a: a_au, e, i: inc, L: (M0 + varpi) % 360, varpi, Omega, orbitalPeriod: period, enhancedRadius };
        neosGroup.add(neo);
    }
    scene.add(neosGroup);
    celestialObjects.neos = { group: neosGroup };
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
    document.getElementById('neo-tra-on-btn').addEventListener('click', (e) => { setNEOVisible(true); e.target.classList.add('active'); document.getElementById('neo-tra-off-btn').classList.remove('active'); });
    document.getElementById('neo-tra-off-btn').addEventListener('click', (e) => { setNEOVisible(false); e.target.classList.add('active'); document.getElementById('neo-tra-on-btn').classList.remove('active'); });
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
    Object.keys({ neos: { name: "NEOs" } }).forEach(key => { if (celestialObjects[key] && celestialObjects[key].group) celestialObjects[key].group.visible = visible; });
}
function setNEOTraVisible(visible) { Object.keys({ neos: { name: "NEOs" } }).forEach(key => { if (celestialObjects[key] && celestialObjects[key].group) celestialObjects[key].orbit.visible = visible; }); }
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

    // Inside updateScales()

    // ... (Planet Scaling Logic) ...

    // --- NEO ORBIT SCALING LOGIC ---
    const neosGroup = celestialObjects.neos ? celestialObjects.neos.group : null;

    if (neosGroup) {
        neosGroup.children.forEach(neoGroup => {
            const userData = neoGroup.userData;
            if (userData && userData.a) {
                const neoMesh = neoGroup.children.find(c => c.isMesh);
                
                // 1. Scale the NEO mesh size
                const scaledSize = currentScale.size(userData.enhancedRadius);
                neoMesh.scale.set(scaledSize, scaledSize, scaledSize);

                // 2. REGENERATE THE ORBIT GEOMETRY
                
                // Re-calculate ellipse parameters based on new scale
                const a = currentScale.distance(userData.a);
                const b = a * Math.sqrt(1 - userData.e ** 2);
                const curve = new THREE.EllipseCurve(-a * userData.e, 0, a, b, 0, 2 * Math.PI, false, 0);

                // Re-calculate and transform points to match the scaling change
                const points = curve.getPoints(100);
                const transformedPoints = points.map(p => new THREE.Vector3(p.x, 0, -p.y));

                // Find the orbit line object (it's stored in the hierarchy under userData.orbitLine)
                const orbitLine = userData.orbitRotationGroup.getObjectByName(`OrbitLine_${neosGroup.children.indexOf(neoGroup)}`);
                
                if (orbitLine && orbitLine.isLine) {
                    // Dispose and set new geometry
                    if (orbitLine.geometry) {
                        orbitLine.geometry.dispose();
                    }
                    orbitLine.geometry.setFromPoints(transformedPoints);
                }
            }
        });
    }
    // ------------------------------
}

function updatePositions(elapsedTime) {
    if (isPaused) return;
    simulationTime = new Date(simulationTime.getTime() + elapsedTime * timeSpeed * 1000);
    document.getElementById('date-display').textContent = simulationTime.toUTCString().replace("GMT", "UTC");
    const daysSinceJ2000 = (simulationTime.getTime() - J2000.getTime()) / 86400000;

    // Collect all bodies (planets and NEOs) for position update
    const neoDataList = celestialObjects.neos.group.children.map((neo, i) => neo.userData);
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

        // Calculate orbital coordinates (x_orb, y_orb) in the orbital plane (focal point is the Sun)
        const a_scaled = currentScale.distance(data.a);
        const x_orb = a_scaled * (Math.cos(E) - data.e);
        const y_orb = a_scaled * Math.sqrt(1 - data.e ** 2) * Math.sin(E);

        // --- UNIFIED POSITION CALCULATION ---

        // Step 1: Define the position in the orbital plane (X-axis toward perihelion).
        // Use the X-Z plane convention (like the orbit curve uses X, 0, -Y)
        const pos_orbit_plane = new THREE.Vector3(x_orb, 0, -y_orb);

        // Step 2: Define the combined rotation matrix
        // The rotation sequence is (Ω) around Y, then (i) around X, then (ω) around Y.
        const i_rad = THREE.MathUtils.degToRad(data.i);
        const Omega_rad = THREE.MathUtils.degToRad(data.Omega);
        const varpi_rad = THREE.MathUtils.degToRad(data.varpi);

        const rotationMatrix = new THREE.Matrix4();
        // Rotation around the Ecliptic Z-axis (Longitude of Ascending Node)
        rotationMatrix.makeRotationY(Omega_rad); 
        // Rotation around the Nodal Line (Inclination)
        rotationMatrix.multiply(new THREE.Matrix4().makeRotationX(i_rad));
        // Rotation in the orbital plane (Argument of Perihelion)
        rotationMatrix.multiply(new THREE.Matrix4().makeRotationY(varpi_rad)); 

        // Step 3: Apply the rotation to transform the vector to the Ecliptic J2000 frame (X, Y, Z)
        pos_orbit_plane.applyMatrix4(rotationMatrix);

        // Step 4: Map the resulting vector directly to the object group's position
        // The result is already in the Ecliptic/Three.js coordinate system (relative to the Sun/Origin)
        objGroup.position.copy(pos_orbit_plane); 
        // objGroup.position.set(pos_orbit_plane.x, pos_orbit_plane.y, pos_orbit_plane.z);
        // objGroup.position.set(pos.x, pos.z, -pos.y); <--- This is now OBSOLETE.

        // -----------------------------------

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
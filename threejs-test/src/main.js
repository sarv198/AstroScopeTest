import './style.css'

import * as THREE from 'three';

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

const renderer = new THREE.WebGLRenderer({
  canvas: document.querySelector('#bg'),
});

renderer.setPixelRatio( window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
camera.position.setZ(30);

// Asteroid object 
const radius = 7;
const detail = 3;
const geometry = new THREE.TetrahedronGeometry(radius, detail );

//Load texture
const textureLoader = new THREE.TextureLoader();
const texture = textureLoader.load('/asteroid.jpg');
texture.colorSpace = THREE.SRGBColorSpace;


const asteroidTexture = new THREE.MeshBasicMaterial({
  color: 0xFF8844,
  map: texture,
});

const asteroid = new THREE.Mesh(geometry, asteroidTexture);

scene.add(asteroid)

function animate() {
  requestAnimationFrame( animate);
  renderer.render(scene, camera);
}
animate();


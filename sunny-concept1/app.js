import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const host = document.querySelector('#canvas-host');
const loading = document.querySelector('#loading');
const loadingText = document.querySelector('#loading-text');
const errorBox = document.querySelector('#error');
const buttons = [...document.querySelectorAll('.view-controls button')];
buttons.forEach(button => { button.disabled = true; });
document.querySelector('#retry').addEventListener('click', () => location.reload());

let renderer, scene, camera, controls;
let ready = false;
let animationFrame = 0;
let environmentTexture;
const focus = new THREE.Vector3(0, 52, 0);
const homeOffset = new THREE.Vector3(-40, 75, 170);
const mobile = matchMedia('(max-width: 700px)');

function fail(error) {
  console.error('Product viewer:', error);
  loading.classList.add('done');
  loading.setAttribute('aria-hidden', 'true');
  errorBox.hidden = false;
  document.querySelector('#viewer').dataset.status = 'error';
}

function requestRender() {
  if (!animationFrame && !document.hidden) animationFrame = requestAnimationFrame(frame);
}

function frame() {
  if (document.hidden || !renderer) { animationFrame = 0; return; }
  // Keep the scheduled-frame marker until rendering finishes: controls.update()
  // can emit change synchronously, which must not start a second render loop.
  controls.update();
  renderer.render(scene, camera);
  renderer.domElement.dataset.azimuth = String(Math.round(THREE.MathUtils.radToDeg(controls.getAzimuthalAngle())));
  renderer.domElement.dataset.distance = String(Math.round(camera.position.distanceTo(controls.target)));
  animationFrame = 0;
}

function resetView() {
  const portrait = host.clientWidth / host.clientHeight < .85;
  camera.position.copy(focus).addScaledVector(homeOffset, portrait ? 1.35 : 1);
  controls.target.copy(focus);
  controls.update();
  requestRender();
}

function resize() {
  if (!renderer) return;
  const width = host.clientWidth, height = host.clientHeight;
  if (!width || !height) return;
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  requestRender();
}

function zoom(factor) {
  const offset = camera.position.clone().sub(controls.target);
  offset.setLength(THREE.MathUtils.clamp(offset.length() * factor, controls.minDistance, controls.maxDistance));
  camera.position.copy(controls.target).add(offset);
  controls.update();
  requestRender();
}

function keyboard(event) {
  if (!ready) return;
  const actions = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '=', '-', '_', 'Home'];
  if (!actions.includes(event.key)) return;
  event.preventDefault();
  if (event.key === 'Home') return resetView();
  if (event.key === '+' || event.key === '=') return zoom(.86);
  if (event.key === '-' || event.key === '_') return zoom(1.16);
  const spherical = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
  const step = Math.PI / 18;
  if (event.key === 'ArrowLeft') spherical.theta -= step;
  if (event.key === 'ArrowRight') spherical.theta += step;
  if (event.key === 'ArrowUp') spherical.phi -= step;
  if (event.key === 'ArrowDown') spherical.phi += step;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi, controls.minPolarAngle, controls.maxPolarAngle);
  camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(spherical));
  controls.update();
  requestRender();
}

async function start() {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.AgXToneMapping;
  renderer.toneMappingExposure = 1.25;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.VSMShadowMap;
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('role', 'img');
  renderer.domElement.setAttribute('aria-label', 'Gold hearing cuff floating above a white platform on a clear acrylic holder. Drag to rotate.');
  renderer.domElement.setAttribute('aria-describedby', 'keyboard-help');
  host.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  scene.background = new THREE.Color('#eeeae3');
  camera = new THREE.PerspectiveCamera(20, 1, .1, 3000);
  controls = new OrbitControls(camera, renderer.domElement);
  // Direct tracking avoids easing lag while dragging; render only on changes.
  controls.enableDamping = false;
  controls.enablePan = false;
  controls.rotateSpeed = .65;
  controls.zoomSpeed = .8;
  controls.minDistance = 72;
  controls.maxDistance = 420;
  controls.minPolarAngle = .09;
  controls.maxPolarAngle = Math.PI / 2 - .05;
  controls.addEventListener('change', requestRender);

  // A quiet studio environment gives the metal broad, clean reflections.
  const room = new RoomEnvironment();
  for (const object of [...room.children]) if (object.isInstancedMesh) room.remove(object);
  const pmrem = new THREE.PMREMGenerator(renderer);
  environmentTexture = pmrem.fromScene(room, .05).texture;
  scene.environment = environmentTexture;
  scene.environmentIntensity = 1.05;
  scene.environmentRotation.y = Math.PI / 5;
  room.dispose();
  pmrem.dispose();

  const key = new THREE.DirectionalLight(0xfff4e0, 2.8);
  key.position.set(-80, 180, 100);
  key.target.position.set(0, 40, 0);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  key.shadow.camera.left = -110; key.shadow.camera.right = 110;
  key.shadow.camera.top = 120; key.shadow.camera.bottom = -100;
  key.shadow.camera.near = 1; key.shadow.camera.far = 500;
  key.shadow.bias = -.00015;
  key.shadow.normalBias = .04;
  key.shadow.radius = 5;
  key.shadow.blurSamples = 12;
  scene.add(key, key.target);
  const fill = new THREE.DirectionalLight(0xeaf2ff, .6);
  fill.position.set(70, 80, -60);
  scene.add(fill);

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(1600, 1600), new THREE.ShadowMaterial({ color: 0x615746, opacity: .13 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -.06;
  ground.receiveShadow = true;
  scene.add(ground);

  resize();
  resetView();
  const gltf = await new GLTFLoader().loadAsync('./assets/sunny-ears-cuff.glb', progress => {
    if (progress.total) loadingText.textContent = `Preparing your view… ${Math.round(progress.loaded / progress.total * 100)}%`;
  });
  const model = gltf.scene;
  model.name = 'Sunny Ears / device and display';
  model.scale.setScalar(1000);
  let meshes = 0;
  model.traverse(object => {
    if (!object.isMesh) return;
    meshes++;
    const sourceName = object.userData.source_name || object.name;
    object.castShadow = true;
    object.receiveShadow = true;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials) {
      material.envMapIntensity = 1;
      if (sourceName === '01 / Single sculpted gold housing') {
        material.color.setRGB(.82, .50, .18);
        material.roughness = .16;
      }
      if (sourceName.startsWith('Acrylic holder')) {
        material.color.setRGB(1, 1, 1);
        material.metalness = 0;
        material.roughness = .035;
        material.transmission = 1;
        material.ior = 1.49;
        material.thickness = .0016;
        material.attenuationColor?.setRGB(1, 1, 1);
        material.attenuationDistance = Infinity;
        material.transparent = false;
        material.opacity = 1;
        object.castShadow = false;
      }
      material.needsUpdate = true;
    }
  });
  scene.add(model);
  // Only the camera moves, so the light-space shadows can be reused on every drag.
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true;
  await renderer.compileAsync(scene, camera);
  renderer.render(scene, camera);
  loading.classList.add('done');
  loading.setAttribute('aria-hidden', 'true');
  buttons.forEach(button => { button.disabled = false; });
  ready = true;
  document.querySelector('#viewer').dataset.status = 'ready';
  renderer.domElement.dataset.meshes = String(meshes);
  requestRender();

  document.querySelector('#zoom-in').addEventListener('click', () => zoom(.82));
  document.querySelector('#zoom-out').addEventListener('click', () => zoom(1.22));
  document.querySelector('#reset-view').addEventListener('click', resetView);
  renderer.domElement.addEventListener('keydown', keyboard);
  renderer.domElement.addEventListener('webglcontextlost', event => { event.preventDefault(); fail(new Error('The graphics connection was interrupted.')); });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) requestRender(); });
  new ResizeObserver(resize).observe(host);
  mobile.addEventListener('change', resetView);
  if (matchMedia('(pointer: coarse)').matches) document.querySelector('#gesture-hint').innerHTML = 'Drag to rotate<span aria-hidden="true"> · </span>Pinch to zoom';
}

start().catch(fail);

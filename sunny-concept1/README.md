# Sunny Ears concept 1

Standalone interactive product viewer published at `/sunny-concept1/` by the existing GitHub Pages workflow. The viewer includes its model and browser libraries and uses relative asset paths, so it works under this subdirectory without an external service or sign-in.

Drag to rotate; scroll or pinch to zoom. The buttons reset or zoom the camera, and the canvas supports arrow keys, plus/minus, and Home. Rendering is event-driven with one pending frame and cached static shadows. Local drag testing of this version measured 60 fps at a 1552 × 2628 drawing-buffer resolution; actual performance depends on the device.

The exported GLB contains the gold cuff, clear holder, and display platform. It comes from the preserved Sunny Ears Blender concept. The geometry is a visual concept, not a manufacturing specification.

Source version: Sunny Ears viewer commit `52f2943f6a1101c8c6d762aa4bcafdb556efe870` from the separately preserved product-viewer project. The model file is 2,110,672 bytes. Keep `index.html`, `app.js`, `style.css`, `assets/`, and `vendor/` together when updating.

## Third-party notices

- Three.js 0.186.1 is bundled under the MIT license included at `vendor/three/LICENSE`.
- The fallback image `assets/product-still.png` is an existing Blender render. Its blurred background uses [Apple Store (No props, only furniture)](https://sketchfab.com/3d-models/apple-store-no-props-only-furniture-9b8ab93b30014795b7c3909bdc7da182) by danyl.missoum, under the downloaded asset's Sketchfab Free Standard license. The retail environment model is not included in this website's GLB.

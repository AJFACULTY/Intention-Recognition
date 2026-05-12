# Dev Log – Intention‑Recognition

## 2026‑05‑07
- Added `cognition_ws` branch: initial workspace backup of cognition (perception, brain, simulation).
  - Excluded `pi5_car.stl` (115 MB) from tracking via `.gitignore`.
  - Committed with "Add cognition workspace source files and update .gitignore".

## 2026‑05‑08
- Updated `cognition_ws` branch:
  - Added `scan_republisher`, `ekf.yaml`, `slam_toolbox.yaml`.
  - Updated launch/URDF to reference `yahboomcar_jazzy_ws` for meshes and description.
  - Added ignore rules for temporary backup files (`*.broken3`, `*.primitive_backup`).

## 2026‑05‑08
- Added `yahboomcar-jazzy` branch: factory Yahboom workspace.
  - Excluded `shape_predictor_68_face_landmarks.dat` (96 MB) and `build/install/log/` from version control.
  - Kept embedded `robot_localization` repository on disk only; not tracked as submodule (simpler for now).
  - Linked by cognition workspace URDF/launch files via absolute paths (to be revisited later).

## 2026‑05‑08
- Added branch descriptions to `README.md` on `main` (Ros2_dev, cognition_ws, MATLAB-FILES, yahboomcar-jazzy).
- Branch naming convention: workspace‑per‑branch (`Ros2_dev`, `cognition_ws`, `yahboomcar-jazzy`, `MATLAB-FILES`).

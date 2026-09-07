# Visual K-Map Solver — Android APK

This project converts the K-Map solver into a Kivy Android app.

## Easiest build method

1. Create a GitHub account if you do not already have one.
2. Create a new repository, for example `visual-kmap-solver`.
3. Upload **all files and folders** from this project.
4. Go to the repository's **Actions** tab.
5. Select **Build Android APK**.
6. Click **Run workflow**.
7. Wait for the workflow to finish.
8. Open the completed workflow run.
9. Under **Artifacts**, download `Visual-KMap-Solver-APK`.
10. Extract the downloaded ZIP and install the APK on your Android phone.

The workflow builds a debug APK automatically. No Android Studio is required on your computer.

## Files

- `main.py` — Kivy Android application
- `buildozer.spec` — Android packaging configuration
- `.github/workflows/build-apk.yml` — automatic cloud APK builder

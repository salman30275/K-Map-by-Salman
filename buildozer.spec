[app]
title = K-MAP Solver by Salman
package.name = kmapsolverbysalman
package.domain = org.kmap
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.ndk = 27c
android.archs = arm64-v8a, armeabi-v7a
android.debug_artifact = apk
android.release_artifact = apk
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1

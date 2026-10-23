[app]
title = Spis gier
package.name = spisgier
package.domain = pl.michalowice
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
source.exclude_dirs = bin, .buildozer, .github, tests
version = 1.0
requirements = python3,kivy==2.3.0
orientation = portrait
fullscreen = 0

# uprawnienia do zapisu pliku statystyk w folderze Dokumenty/SpisGier
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

android.api = 34
android.minapi = 24
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.allow_backup = True
android.enable_androidx = True

# ikona (opcjonalnie): odkomentuj i dodaj pliki
#icon.filename = %(source.dir)s/icon.png
#presplash.filename = %(source.dir)s/presplash.png
android.presplash_color = #0E2620

[buildozer]
log_level = 2
warn_on_root = 1

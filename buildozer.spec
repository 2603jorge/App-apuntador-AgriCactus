[app]
title = AgriCactus Apuntador
package.name = apuntadoragricactus
package.domain = org.agricactus
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

requirements = python3,kivy,kivymd==1.1.1,plyer,pillow,android,pyjnius

android.permissions = INTERNET,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.build_tools_version = 33.0.2
android.gradle_dependencies = androidx.core:core:1.9.0, com.journeyapps:zxing-android-embedded:4.3.0
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1

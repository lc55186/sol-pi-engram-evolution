@echo off
SETLOCAL EnableExtensions

rem === Force Java 17 by absolute path ===
SET "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
SET "ANDROID_HOME=C:\Android\android-sdk"
SET "GRADLE_HOME=C:\Gradle\gradle-8.2"
SET "PATH=%JAVA_HOME%\bin;%GRADLE_HOME%\bin;C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem"

cd /d "C:\Users\liuchao\Desktop\sol-pi-engram-evolution\boss-ai-r-android"

echo ========================================
echo BOSS-AI-R APK Builder
echo ========================================
echo JAVA_HOME: %JAVA_HOME%
echo ANDROID_HOME: %ANDROID_HOME%
echo.

"%GRADLE_HOME%\bin\gradle.bat" assembleDebug --no-daemon 2>&1

echo.
echo ========================================
echo Result
echo ========================================

IF EXIST "app\build\outputs\apk\debug\app-debug.apk" (
    echo [SUCCESS] APK generated!
) ELSE (
    echo [FAIL] APK not generated.
)

ENDLOCAL

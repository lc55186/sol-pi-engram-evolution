rem Build APK using pre-installed Gradle and Java 17
rem This script must be run from the project directory

@echo off
setlocal enabledelayedexpansion

rem === Force Java 17 by modifying system environment ===
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot" /m >nul 2>&1
setx ANDROID_HOME "C:\Android\android-sdk" /m >nul 2>&1
setx ANDROID_SDK_ROOT "C:\Android\android-sdk" /m >nul 2>&1
setx GRADLE_HOME "C:\Gradle\gradle-8.2" /m >nul 2>&1

rem === Set process-level environment ===
set "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
set "ANDROID_HOME=C:\Android\android-sdk"
set "ANDROID_SDK_ROOT=C:\Android\android-sdk"
set "GRADLE_HOME=C:\Gradle\gradle-8.2"

rem === Build clean PATH ===
set "PATH=%JAVA_HOME%\bin;%GRADLE_HOME%\bin;C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem"

rem === Navigate to project ===
cd /d "%~dp0boss-ai-r-android"

echo.
echo ========================================
echo BOSS-AI-R APK Builder
echo ========================================
echo.
echo JAVA_HOME: %JAVA_HOME%
echo ANDROID_HOME: %ANDROID_HOME%
echo.

rem === Verify Java ===
java -version 2>&1
echo.

rem === Run build ===
echo Starting gradle build...
echo.

gradle assembleDebug --no-daemon --stacktrace 2>&1

echo.
echo ========================================
echo Build Complete
echo ========================================
echo.

if exist "app\build\outputs\apk\debug\app-debug.apk" (
    echo SUCCESS: APK generated!
    for %%A in ("app\build\outputs\apk\debug\app-debug.apk") do (
        echo Size: %%~zA bytes
        echo Path: %%~fA
    )
) else (
    echo APK not generated. Check output above.
)

endlocal
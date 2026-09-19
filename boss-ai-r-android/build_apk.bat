@echo off
SETLOCAL EnableExtensions

echo ========================================
echo BOSS-AI-R Android APK Builder
echo ========================================
echo.

REM === Setup Java 17 ===
SET "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
SET "PATH=%JAVA_HOME%\bin;%PATH%"

REM === Setup Android SDK ===
SET "ANDROID_HOME=C:\Android\android-sdk"
SET "ANDROID_SDK_ROOT=C:\Android\android-sdk"

REM === Use pre-installed Gradle ===
SET "GRADLE_HOME=C:\Gradle\gradle-8.2"
SET "PATH=%GRADLE_HOME%\bin;%PATH%"

REM Verify
echo Java version:
"%JAVA_HOME%\bin\java.exe" -version 2>&1
echo.
echo ANDROID_HOME: %ANDROID_HOME%
echo JAVA_HOME: %JAVA_HOME%
echo.

REM Navigate to project
cd /d "C:\Users\liuchao\Desktop\sol-pi-engram-evolution\boss-ai-r-android"

REM Run gradle build
echo ========================================
echo Starting Gradle Build
echo ========================================
echo.

gradle assembleDebug --no-daemon --stacktrace 2>&1

echo.
echo ========================================
echo Build Complete
echo ========================================
echo.
echo APK should be at:
echo   app\build\outputs\apk\debug\app-debug.apk
echo.

IF EXIST "app\build\outputs\apk\debug\app-debug.apk" (
    echo [SUCCESS] APK generated!
    FOR %%A IN ("app\build\outputs\apk\debug\app-debug.apk") DO (
        echo Size: %%~zA bytes
    )
) ELSE (
    echo [FAIL] APK not found. Check build output above.
)

ENDLOCAL
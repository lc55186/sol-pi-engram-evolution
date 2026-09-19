@echo off
SETLOCAL EnableExtensions

REM === CRITICAL: Force Java 17 and clean PATH ===
SET "JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
SET "ANDROID_HOME=C:\Android\android-sdk"
SET "ANDROID_SDK_ROOT=C:\Android\android-sdk"
SET "GRADLE_HOME=C:\Gradle\gradle-8.2"

REM Clean PATH - Java 17 first, then system, then Gradle
SET "PATH=%JAVA_HOME%\bin;C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem;%GRADLE_HOME%\bin"

echo ========================================
echo Environment Check
echo ========================================
echo JAVA_HOME: %JAVA_HOME%
echo ANDROID_HOME: %ANDROID_HOME%
echo GRADLE_HOME: %GRADLE_HOME%
echo.

"%JAVA_HOME%\bin\java.exe" -version 2>&1
echo.

REM Navigate to project
cd /d "C:\Users\liuchao\Desktop\sol-pi-engram-evolution\boss-ai-r-android"

echo ========================================
echo Gradle Build - BOSS-AI-R APK
echo ========================================
echo.

gradle assembleDebug --no-daemon --stacktrace 2>&1

echo.
echo ========================================
echo Build Complete
echo ========================================
echo.

IF EXIST "app\build\outputs\apk\debug\app-debug.apk" (
    echo [SUCCESS] APK generated!
    FOR %%A IN ("app\build\outputs\apk\debug\app-debug.apk") DO (
        echo Size: %%~zA bytes
        echo Path: %%~fA
    )
) ELSE (
    echo [INFO] APK may not have been generated. Check output above.
)

ENDLOCAL

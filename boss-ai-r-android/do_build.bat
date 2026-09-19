@echo off
SETLOCAL EnableExtensions

REM === Completely clean PATH - remove Java 8, MSYS, and Oracle javapath ===
SET "JAVA_17=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
SET "GRADLE=C:\Gradle\gradle-8.2"
SET "ANDROID_SDK=C:\Android\android-sdk"

REM Build PATH manually - no Oracle Java, no MSYS
SET "PATH=%JAVA_17%\bin"
SET "PATH=%PATH%;%GRADLE%\bin"
SET "PATH=%PATH%;%ANDROID_SDK%\platform-tools"
SET "PATH=%PATH%;C:\Windows\System32"
SET "PATH=%PATH%;C:\Windows"
SET "PATH=%PATH%;C:\Windows\System32\Wbem"

REM Set environment
SET "JAVA_HOME=%JAVA_17%"
SET "ANDROID_HOME=%ANDROID_SDK%"
SET "ANDROID_SDK_ROOT=%ANDROID_SDK%"
SET "GRADLE_HOME=%GRADLE%"

echo ========================================
echo BOSS-AI-R Build
echo ========================================
echo PATH: %PATH%
echo.

cd /d "C:\Users\liuchao\Desktop\sol-pi-engram-evolution\boss-ai-r-android"

echo Building...
echo.

"%GRADLE%\bin\gradle.bat" assembleDebug --no-daemon --stacktrace 2>&1

echo.
echo ========================================
echo Result
echo ========================================
IF EXIST "app\build\outputs\apk\debug\app-debug.apk" (
    echo [SUCCESS]
    FOR %%F IN ("app\build\outputs\apk\debug\app-debug.apk") DO echo Size: %%~zF bytes
) ELSE (
    echo [FAIL]
)

ENDLOCAL

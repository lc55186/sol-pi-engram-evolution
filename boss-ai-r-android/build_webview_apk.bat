@echo off
chcp 65001 >nul
title BOSS-AI-R V0.1 APK 构建工具
echo ========================================
echo   老板口袋军师 V0.1 — APK 构建
echo ========================================
echo.

set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot
set ANDROID_HOME=C:\Android\android-sdk
set PATH=%JAVA_HOME%\bin;%ANDROID_HOME%\platform-tools;%PATH%

cd /d "C:\Users\liuchao\Desktop\sol-pi-engram-evolution\boss-ai-r-android"

echo [1/3] 清理旧构建...
call gradlew clean --no-daemon 2>&1

echo.
echo [2/3] 构建 debug APK...
call gradlew assembleDebug --no-daemon --stacktrace 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [3/3] ✅ 构建成功！
    copy /Y "app\build\outputs\apk\debug\app-debug.apk" "C:\Users\liuchao\Desktop\BOSS-AI-R-v0.1-webview.apk" 2>nul
    echo APK 已复制到桌面: BOSS-AI-R-v0.1-webview.apk
    for %%I in ("C:\Users\liuchao\Desktop\BOSS-AI-R-v0.1-webview.apk") do echo 大小: %%~zI bytes
) else (
    echo.
    echo ❌ 构建失败，请查看上方错误信息
)

echo.
pause

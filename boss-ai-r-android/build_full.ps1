$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot"
$env:ANDROID_HOME = "C:\Android\android-sdk"
$env:ANDROID_SDK_ROOT = "C:\Android\android-sdk"
$env:GRADLE_HOME = "C:\Gradle\gradle-8.2"
$env:PATH = "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot\bin;C:\Gradle\gradle-8.2\bin;C:\Windows\System32;C:\Windows;C:\Windows\System32\Wbem"

Set-Location "C:\Users\liuchao\Desktop\sol-pi-engram-evolution\boss-ai-r-android"

Write-Host "Java version:"
& "C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot\bin\java.exe" -version 2>&1
Write-Host ""

Write-Host "Starting gradle build with stacktrace..."
& "C:\Gradle\gradle-8.2\bin\gradle.bat" assembleDebug --no-daemon --stacktrace 2>&1 | Tee-Object -FilePath "build_full.log"

Write-Host ""
if (Test-Path "app\build\outputs\apk\debug\app-debug.apk") {
    $size = (Get-Item "app\build\outputs\apk\debug\app-debug.apk").Length / 1MB
    Write-Host "[SUCCESS] APK generated: $($size.ToString('N2')) MB"
} else {
    Write-Host "[FAIL] APK not generated"
    Write-Host ""
    Write-Host "=== Last 100 lines of build.log ==="
    if (Test-Path "build_full.log") {
        Get-Content "build_full.log" -Tail 100
    }
}
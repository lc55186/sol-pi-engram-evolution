package com.bossair.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.os.Vibrator
import android.webkit.*
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat

class MainActivity : ComponentActivity() {

    private lateinit var webView: WebView

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            webView.evaluateJavascript("window.NativeBridge && window.NativeBridge.onPermissionGranted()", null)
        } else {
            Toast.makeText(this, "需要麦克风权限", Toast.LENGTH_LONG).show()
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.mediaPlaybackRequiresUserGesture = false
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            settings.setSupportZoom(false)
            settings.builtInZoomControls = false

            webViewClient = object : WebViewClient() {
                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    // Initialize native bridge
                    evaluateJavascript("""
                        window.NativeBridge = {
                            startRecording: function() { AndroidBridge.startRecording() },
                            stopRecording: function() { AndroidBridge.stopRecording() },
                            vibrate: function(ms) { AndroidBridge.vibrate(ms) },
                            postTranscript: function(text, speaker) { AndroidBridge.postTranscript(text, speaker) },
                            getBatteryLevel: function() { return AndroidBridge.getBatteryLevel() },
                            getNetworkType: function() { return AndroidBridge.getNetworkType() }
                        };
                        if (window.onNativeBridgeReady) window.onNativeBridgeReady();
                    """.trimIndent(), null)
                }
            }

            webChromeClient = object : WebChromeClient() {
                override fun onPermissionRequest(request: PermissionRequest?) {
                    runOnUiThread {
                        request?.grant(request.resources)
                    }
                }
            }

            addJavascriptInterface(object {
                @JavascriptInterface
                fun startRecording() {
                    runOnUiThread {
                        if (ContextCompat.checkSelfPermission(this@MainActivity, Manifest.permission.RECORD_AUDIO)
                            == PackageManager.PERMISSION_GRANTED) {
                            webView.evaluateJavascript("window.NativeBridge.onRecordingStarted()", null)
                        } else {
                            requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                        }
                    }
                }

                @JavascriptInterface
                fun stopRecording() {
                    runOnUiThread {
                        webView.evaluateJavascript("window.NativeBridge.onRecordingStopped()", null)
                    }
                }

                @JavascriptInterface
                fun vibrate(milliseconds: Long) {
                    val vibrator = getSystemService(VIBRATOR_SERVICE) as Vibrator
                    vibrator.vibrate(milliseconds)
                }

                @JavascriptInterface
                fun postTranscript(text: String, speaker: String) {
                    // TODO: Send to ASR service
                }

                @JavascriptInterface
                fun getBatteryLevel(): Int {
                    return 85 // Placeholder
                }

                @JavascriptInterface
                fun getNetworkType(): String {
                    return "wifi"
                }
            }, "AndroidBridge")

            loadUrl("file:///android_asset/index.html")
        }

        setContentView(webView)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    override fun onDestroy() {
        webView.destroy()
        super.onDestroy()
    }
}

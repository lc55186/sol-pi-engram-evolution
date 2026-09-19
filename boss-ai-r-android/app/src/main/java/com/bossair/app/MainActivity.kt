package com.bossair.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.core.content.ContextCompat
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.bossair.app.service.AudioRecordService
import com.bossair.app.ui.screens.RealtimeScreen
import com.bossair.app.ui.theme.BossAITheme

class MainActivity : ComponentActivity() {
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            startRecordingService()
        } else {
            Toast.makeText(this, "需要麦克风权限才能录音", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            BossAITheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainScreen { checkPermissionAndRecord() }
                }
            }
        }
    }

    private fun checkPermissionAndRecord() {
        when {
            ContextCompat.checkSelfPermission(
                this, Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED -> {
                startRecordingService()
            }
            else -> {
                requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        }
    }

    private fun startRecordingService() {
        val intent = Intent(this, AudioRecordService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }
}

@Composable
fun MainScreen(onStartRecording: () -> Unit) {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = "realtime") {
        composable("realtime") {
            RealtimeScreen()
        }
        composable("dashboard") {
            DashboardScreen()
        }
        composable("settings") {
            SettingsScreen()
        }
    }
}

@Composable
fun DashboardScreen() {
    // Placeholder for dashboard
    Text("经营外脑 - 开发中")
}

@Composable
fun SettingsScreen() {
    // Placeholder for settings
    Text("设置 - 开发中")
}

@Preview(showBackground = true)
@Composable
fun DefaultPreview() {
    BossAITheme {
        MainScreen(onStartRecording = {})
    }
}
package com.bossair.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val BossColorScheme = darkColorScheme(
    primary = Color(0xFFD32F2F),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFB71C1C),
    secondary = Color(0xFF455A64),
    onSecondary = Color.White,
    background = Color(0xFF121212),
    surface = Color(0xFF1E1E1E),
    onBackground = Color.White,
    onSurface = Color.White,
)

@Composable
fun BossAITheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = BossColorScheme,
        content = content
    )
}
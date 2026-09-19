# Add project specific ProGuard rules here.
-keepattributes Signature
-keepattributes *Annotation*
-keep class com.bossair.app.** { *; }
-keepclassmembers class com.bossair.app.** { *; }

# Keep Kotlin metadata
-keep class kotlin.Metadata { *; }
-keepclassmembers class kotlin.Metadata { *; }

# OkHttp
-dontwarn okhttp3.internal.platform.**

# Compose
-keep class androidx.compose.** { *; }
-dontwarn androidx.compose.**

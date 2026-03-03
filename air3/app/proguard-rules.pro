# Velaris Air3 ProGuard Rules

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }

# JSON
-keep class org.json.** { *; }

# Velaris data classes
-keep class com.velaris.air3.velaris.** { *; }

package com.velaris.air3.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.Typography
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/**
 * Velaris Air3 theme — dark, minimal, optimized for AR waveguide display.
 *
 * Key considerations for INMO Air3:
 * - Dark background = transparent on waveguide (black pixels are see-through)
 * - High contrast text for 600 nit display
 * - Compact layout for 36° FOV
 */

val VelarisPink = Color(0xFFCC4280)
val VelarisDark = Color(0xFF0A0A12)
val VelarisSurface = Color(0xFF121220)
val VelarisText = Color(0xFFE0E0F0)
val VelarisTextDim = Color(0x99E0E0F0)

private val VelarisColorScheme = darkColorScheme(
    primary = VelarisPink,
    onPrimary = Color.White,
    background = Color.Black, // transparent on waveguide!
    surface = VelarisSurface,
    onSurface = VelarisText,
    onBackground = VelarisText,
    secondary = VelarisPink.copy(alpha = 0.7f),
    onSecondary = Color.White,
)

private val VelarisTypography = Typography(
    // Main conversation text
    bodyLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 22.sp,
        color = VelarisText,
    ),
    // Status text
    bodyMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 13.sp,
        color = VelarisTextDim,
    ),
    // Section labels
    labelMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        color = VelarisTextDim,
    ),
    // Large status (event names)
    headlineSmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 20.sp,
        color = VelarisText,
    ),
)

@Composable
fun VelarisAir3Theme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = VelarisColorScheme,
        typography = VelarisTypography,
        content = content,
    )
}

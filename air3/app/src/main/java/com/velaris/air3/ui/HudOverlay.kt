package com.velaris.air3.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.velaris.air3.velaris.EmotionalState

/**
 * AR HUD overlay for the INMO Air3 waveguide display.
 *
 * Layout (36° FOV, landscape):
 * ┌─────────────────────────────────────────────────┐
 * │ [status]                     [emotional color] ○ │
 * │                                                  │
 * │              conversation text                   │
 * │              (Velaris response)                   │
 * │                                                  │
 * │ [partial speech]              [event indicator]  │
 * └─────────────────────────────────────────────────┘
 *
 * Black pixels are transparent on waveguide, so we use a pure black
 * background with high-contrast colored text and indicators.
 */

@Composable
fun HudOverlay(
    status: String,
    conversationText: String,
    partialSpeech: String,
    emotionalState: EmotionalState,
    eventText: String,
    isListening: Boolean,
    isConnected: Boolean,
    modifier: Modifier = Modifier,
) {
    val emotionalColor = remember(emotionalState.color) {
        parseHexColor(emotionalState.color)
    }

    // Pulsing animation for listening indicator
    val pulseAlpha by rememberInfiniteTransition(label = "pulse").animateFloat(
        initialValue = 0.4f,
        targetValue = 1.0f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = EaseInOut),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulseAlpha",
    )

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(Color.Black) // transparent on waveguide
            .padding(horizontal = 24.dp, vertical = 16.dp)
    ) {
        // --- Top bar: status + emotional color indicator ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.TopCenter),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Status indicator
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                // Connection dot
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(
                            if (isConnected) Color(0xFF4CAF50)
                            else Color(0xFFE91E63)
                        )
                )

                Text(
                    text = status,
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (isListening) {
                        Color(0xFF4CAF50).copy(alpha = pulseAlpha)
                    } else {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                    },
                )
            }

            // Emotional color orb
            Box(
                modifier = Modifier
                    .size(24.dp)
                    .clip(CircleShape)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                emotionalColor,
                                emotionalColor.copy(alpha = 0.3f),
                                Color.Transparent,
                            )
                        )
                    )
                    .border(1.dp, emotionalColor.copy(alpha = 0.5f), CircleShape)
            )
        }

        // --- Center: Conversation text ---
        AnimatedVisibility(
            visible = conversationText.isNotBlank(),
            enter = fadeIn(tween(300)) + slideInVertically(tween(300)),
            exit = fadeOut(tween(500)),
            modifier = Modifier.align(Alignment.Center),
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth(0.85f)
                    .background(
                        Color(0x22FFFFFF),
                        RoundedCornerShape(12.dp),
                    )
                    .border(
                        1.dp,
                        emotionalColor.copy(alpha = 0.2f),
                        RoundedCornerShape(12.dp),
                    )
                    .padding(horizontal = 20.dp, vertical = 14.dp)
            ) {
                Text(
                    text = conversationText,
                    style = MaterialTheme.typography.bodyLarge,
                    color = Color.White,
                    textAlign = TextAlign.Center,
                    maxLines = 4,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }

        // --- Bottom bar: partial speech + event indicator ---
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.BottomCenter),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Partial speech text (what user is currently saying)
            AnimatedVisibility(
                visible = partialSpeech.isNotBlank(),
                enter = fadeIn(tween(150)),
                exit = fadeOut(tween(150)),
            ) {
                Text(
                    text = partialSpeech,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Color(0xFF4CAF50).copy(alpha = 0.7f),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.fillMaxWidth(0.6f),
                )
            }

            // Event indicator (fades in/out)
            AnimatedVisibility(
                visible = eventText.isNotBlank(),
                enter = fadeIn(tween(200)) + scaleIn(tween(200)),
                exit = fadeOut(tween(1000)),
            ) {
                Text(
                    text = eventText,
                    style = MaterialTheme.typography.labelMedium,
                    color = emotionalColor,
                )
            }
        }
    }
}

/**
 * Parse a hex color string (#cc4280) to Compose Color.
 */
private fun parseHexColor(hex: String): Color {
    return try {
        val cleaned = hex.removePrefix("#")
        val colorInt = cleaned.toLong(16)
        Color(
            red = ((colorInt shr 16) and 0xFF) / 255f,
            green = ((colorInt shr 8) and 0xFF) / 255f,
            blue = (colorInt and 0xFF) / 255f,
        )
    } catch (e: Exception) {
        Color(0xFFCC4280) // fallback Velaris pink
    }
}

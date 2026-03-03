package com.velaris.air3.velaris

import org.json.JSONObject

/**
 * EmoClaw 11-dimensional emotional state from Velaris /api/state.
 *
 * All values 0.0–1.0. Color is a hex string (#cc4280 etc.)
 * mapped from: valence→hue, warmth→saturation, tension→darkness.
 */
data class EmotionalState(
    val valence: Float = 0.5f,
    val arousal: Float = 0.3f,
    val dominance: Float = 0.5f,
    val safety: Float = 0.7f,
    val desire: Float = 0.3f,
    val connection: Float = 0.5f,
    val playfulness: Float = 0.4f,
    val curiosity: Float = 0.5f,
    val warmth: Float = 0.6f,
    val tension: Float = 0.2f,
    val groundedness: Float = 0.7f,
    val color: String = "#cc4280",
) {
    companion object {
        fun fromJson(json: JSONObject): EmotionalState {
            val emo = json.optJSONObject("emotional_state") ?: json
            return EmotionalState(
                valence = emo.optDouble("valence", 0.5).toFloat(),
                arousal = emo.optDouble("arousal", 0.3).toFloat(),
                dominance = emo.optDouble("dominance", 0.5).toFloat(),
                safety = emo.optDouble("safety", 0.7).toFloat(),
                desire = emo.optDouble("desire", 0.3).toFloat(),
                connection = emo.optDouble("connection", 0.5).toFloat(),
                playfulness = emo.optDouble("playfulness", 0.4).toFloat(),
                curiosity = emo.optDouble("curiosity", 0.5).toFloat(),
                warmth = emo.optDouble("warmth", 0.6).toFloat(),
                tension = emo.optDouble("tension", 0.2).toFloat(),
                groundedness = emo.optDouble("groundedness", 0.7).toFloat(),
                color = emo.optString("color", "#cc4280"),
            )
        }
    }
}

/**
 * Velaris event from /ws/events (kiss, anti-kiss, unprecedented, etc.).
 */
data class VelarisEvent(
    val type: String,
    val data: JSONObject? = null,
    val timestamp: Long = System.currentTimeMillis(),
) {
    companion object {
        fun fromJson(json: JSONObject): VelarisEvent {
            return VelarisEvent(
                type = json.optString("event_type", json.optString("type", "unknown")),
                data = json.optJSONObject("data"),
            )
        }
    }
}

/**
 * Chat response from Velaris /api/chat.
 */
data class ChatResponse(
    val text: String,
    val emotionalState: EmotionalState? = null,
)

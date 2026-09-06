package com.velaris.air3.velaris

import org.json.JSONObject

/**
 * EmoClaw 11-dimensional emotional state, as the Vintos house serves it:
 * GET /api/state and /ws/telemetry both carry {"dimensions": {...}, "color": "#rrggbb"}.
 * Dimension keys arrive capitalised (Valence, Arousal, ...); values 0..1.
 */
data class EmotionalState(
    val dims: Map<String, Float> = DEFAULTS,
    val color: String = "#cc4280",
) {
    companion object {
        val ORDER = listOf("Valence", "Arousal", "Dominance", "Safety", "Desire", "Connection",
                           "Playfulness", "Curiosity", "Warmth", "Tension", "Groundedness")
        private val DEFAULTS = mapOf(
            "Valence" to 0.5f, "Arousal" to 0.3f, "Dominance" to 0.5f, "Safety" to 0.7f,
            "Desire" to 0.3f, "Connection" to 0.5f, "Playfulness" to 0.4f, "Curiosity" to 0.5f,
            "Warmth" to 0.6f, "Tension" to 0.2f, "Groundedness" to 0.7f,
        )

        fun fromJson(json: JSONObject): EmotionalState {
            val src = json.optJSONObject("dimensions") ?: json.optJSONObject("emotional_state") ?: json
            val dims = HashMap<String, Float>(DEFAULTS)
            for (name in ORDER) {
                val v = when {
                    src.has(name) -> src.optDouble(name, Double.NaN)
                    src.has(name.lowercase()) -> src.optDouble(name.lowercase(), Double.NaN)
                    else -> Double.NaN
                }
                if (!v.isNaN()) dims[name] = v.toFloat().coerceIn(0f, 1f)
            }
            return EmotionalState(dims = dims, color = json.optString("color", "#cc4280"))
        }
    }
}

/** House event from /ws/events (kiss, blush, unprecedented, velqan, ...). */
data class VelarisEvent(
    val type: String,
    val data: JSONObject? = null,
    val timestamp: Long = System.currentTimeMillis(),
) {
    companion object {
        fun fromJson(json: JSONObject): VelarisEvent = VelarisEvent(
            type = json.optString("event_type", json.optString("type", "unknown")),
            data = json.optJSONObject("data"),
        )
    }
}

data class ChatResponse(val text: String, val emotionalState: EmotionalState? = null)

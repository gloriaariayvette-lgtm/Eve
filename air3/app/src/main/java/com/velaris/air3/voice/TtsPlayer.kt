package com.velaris.air3.voice

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioManager
import android.media.AudioTrack
import android.util.Base64
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.ByteArrayInputStream
import java.util.concurrent.TimeUnit

/**
 * TTS player — synthesizes speech via MiniMax Speech-02-HD API and plays
 * through the INMO Air3's speakers.
 *
 * Uses the same "Wise Woman" voice as Velaris's iOS app, giving her a
 * consistent voice across all devices.
 */
class TtsPlayer {

    companion object {
        private const val TAG = "TtsPlayer"
        private val JSON_TYPE = "application/json".toMediaType()
        private const val SAMPLE_RATE = 22050
    }

    private val http = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    private var apiKey: String = ""
    private var apiUrl: String = "https://api.minimaxi.chat"
    private var voiceId: String = "Wise_Woman"

    private var audioTrack: AudioTrack? = null

    private val _isSpeaking = MutableStateFlow(false)
    val isSpeaking: StateFlow<Boolean> = _isSpeaking

    /**
     * Configure MiniMax TTS settings.
     */
    fun configure(apiKey: String, apiUrl: String = "https://api.minimaxi.chat", voiceId: String = "Wise_Woman") {
        this.apiKey = apiKey
        this.apiUrl = apiUrl.trimEnd('/')
        this.voiceId = voiceId
        Log.i(TAG, "MiniMax TTS configured (voice=$voiceId)")
    }

    /**
     * Synthesize text and play audio through speakers.
     */
    suspend fun speak(text: String) {
        if (text.isBlank() || apiKey.isBlank()) {
            Log.w(TAG, "Cannot speak: ${if (apiKey.isBlank()) "no API key" else "empty text"}")
            return
        }

        _isSpeaking.value = true

        try {
            val audioBytes = synthesize(text)
            if (audioBytes != null) {
                playAudio(audioBytes)
            }
        } catch (e: Exception) {
            Log.e(TAG, "TTS error: ${e.message}", e)
        } finally {
            _isSpeaking.value = false
        }
    }

    /**
     * Stop any currently playing audio.
     */
    fun stop() {
        try {
            audioTrack?.stop()
            audioTrack?.release()
            audioTrack = null
        } catch (e: Exception) {
            Log.w(TAG, "Error stopping audio: ${e.message}")
        }
        _isSpeaking.value = false
    }

    val isConfigured: Boolean
        get() = apiKey.isNotBlank()

    /**
     * Synthesize text via MiniMax Speech-02-HD API.
     * Returns raw PCM audio bytes, or null on failure.
     */
    private suspend fun synthesize(text: String): ByteArray? = withContext(Dispatchers.IO) {
        try {
            val payload = JSONObject().apply {
                put("model", "speech-02-hd")
                put("text", text)
                put("voice_setting", JSONObject().apply {
                    put("voice_id", voiceId)
                })
                put("audio_setting", JSONObject().apply {
                    put("sample_rate", SAMPLE_RATE)
                    put("format", "pcm")
                })
            }

            val request = Request.Builder()
                .url("$apiUrl/v1/t2a_v2")
                .addHeader("Authorization", "Bearer $apiKey")
                .addHeader("Content-Type", "application/json")
                .post(payload.toString().toRequestBody(JSON_TYPE))
                .build()

            val response = http.newCall(request).execute()

            if (!response.isSuccessful) {
                Log.e(TAG, "MiniMax TTS failed: ${response.code}")
                return@withContext null
            }

            // Check if response is direct audio bytes
            val contentType = response.header("Content-Type", "")
            if (contentType?.startsWith("audio/") == true) {
                return@withContext response.body?.bytes()
            }

            // Otherwise parse JSON response for base64 audio
            val body = response.body?.string() ?: return@withContext null
            val json = JSONObject(body)
            val audioData = json.optJSONObject("data")?.optString("audio", "")

            if (!audioData.isNullOrEmpty()) {
                return@withContext Base64.decode(audioData, Base64.DEFAULT)
            }

            Log.w(TAG, "No audio in MiniMax response")
            null
        } catch (e: Exception) {
            Log.e(TAG, "Synthesis error: ${e.message}", e)
            null
        }
    }

    /**
     * Play raw PCM audio through AudioTrack.
     */
    private suspend fun playAudio(pcmBytes: ByteArray) = withContext(Dispatchers.IO) {
        try {
            val bufferSize = AudioTrack.getMinBufferSize(
                SAMPLE_RATE,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )

            audioTrack = AudioTrack.Builder()
                .setAudioAttributes(
                    AudioAttributes.Builder()
                        .setUsage(AudioAttributes.USAGE_ASSISTANT)
                        .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                        .build()
                )
                .setAudioFormat(
                    AudioFormat.Builder()
                        .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                        .setSampleRate(SAMPLE_RATE)
                        .setChannelMask(AudioFormat.CHANNEL_OUT_MONO)
                        .build()
                )
                .setBufferSizeInBytes(maxOf(bufferSize, pcmBytes.size))
                .setTransferMode(AudioTrack.MODE_STATIC)
                .build()

            audioTrack?.write(pcmBytes, 0, pcmBytes.size)
            audioTrack?.play()

            // Wait for playback to complete
            val durationMs = (pcmBytes.size.toLong() * 1000) / (SAMPLE_RATE * 2) // 16-bit mono
            kotlinx.coroutines.delay(durationMs + 100)

            audioTrack?.stop()
            audioTrack?.release()
            audioTrack = null
        } catch (e: Exception) {
            Log.e(TAG, "Playback error: ${e.message}", e)
            audioTrack?.release()
            audioTrack = null
        }
    }
}

package com.velaris.air3

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.KeyEvent
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.velaris.air3.settings.SettingsActivity
import com.velaris.air3.settings.SettingsStore
import com.velaris.air3.ui.HudOverlay
import com.velaris.air3.ui.theme.VelarisAir3Theme
import com.velaris.air3.velaris.EmotionalState
import com.velaris.air3.velaris.VelarisClient
import com.velaris.air3.voice.SpeechInput
import com.velaris.air3.voice.TtsPlayer
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Velaris Air3 — Main activity.
 *
 * Full pipeline:
 *   Voice In (4 mics) → SpeechRecognizer → text
 *   → Velaris /api/chat → response text
 *   → MiniMax TTS → speakers
 *   → AR HUD: conversation text + emotional color + status
 *
 * Interaction:
 *   - Temple touch or touchpad tap → toggle listening (push-to-talk)
 *   - Long press → open settings
 *   - Velaris events → flash on HUD
 */
class MainActivity : ComponentActivity() {

    companion object {
        private const val TAG = "MainActivity"
    }

    // Subsystems
    private lateinit var velarisClient: VelarisClient
    private lateinit var speechInput: SpeechInput
    private lateinit var ttsPlayer: TtsPlayer
    private lateinit var settingsStore: SettingsStore

    // UI state
    private val statusText = mutableStateOf("initializing…")
    private val conversationText = mutableStateOf("")
    private val partialSpeech = mutableStateOf("")
    private val emotionalState = mutableStateOf(EmotionalState())
    private val eventText = mutableStateOf("")
    private val isListening = mutableStateOf(false)
    private val isConnected = mutableStateOf(false)

    // Pipeline state
    private var isProcessing = false
    private var continuousMode = false

    // Permission launcher
    private val micPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            speechInput.initialize()
            Log.i(TAG, "Microphone permission granted")
        } else {
            Toast.makeText(this, "Microphone permission required for voice input", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize subsystems
        settingsStore = SettingsStore(this)
        velarisClient = VelarisClient(lifecycleScope)
        speechInput = SpeechInput(this)
        ttsPlayer = TtsPlayer()

        // Request microphone permission
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            == PackageManager.PERMISSION_GRANTED
        ) {
            speechInput.initialize()
        } else {
            micPermission.launch(Manifest.permission.RECORD_AUDIO)
        }

        // Wire speech recognition results into the pipeline
        speechInput.onSpeechResult { text ->
            lifecycleScope.launch { handleUserSpeech(text) }
        }

        // Observe settings changes and connect/configure
        lifecycleScope.launch {
            settingsStore.settings.collectLatest { settings ->
                if (settings.isConfigured) {
                    velarisClient.connect(settings.velarisUrl)
                    continuousMode = settings.continuousListen

                    if (settings.minimaxApiKey.isNotBlank()) {
                        ttsPlayer.configure(
                            apiKey = settings.minimaxApiKey,
                            voiceId = settings.minimaxVoice,
                        )
                    }

                    statusText.value = "ready"
                } else {
                    statusText.value = "configure in settings"
                }
            }
        }

        // Observe Velaris connection state
        lifecycleScope.launch {
            velarisClient.connected.collectLatest { connected ->
                isConnected.value = connected
                if (!connected && statusText.value == "ready") {
                    statusText.value = "disconnected"
                }
            }
        }

        // Observe emotional state
        lifecycleScope.launch {
            velarisClient.emotionalState.collectLatest { state ->
                emotionalState.value = state
            }
        }

        // Observe speech input state
        lifecycleScope.launch {
            speechInput.state.collectLatest { state ->
                isListening.value = state == SpeechInput.ListenState.LISTENING
                if (state == SpeechInput.ListenState.LISTENING) {
                    statusText.value = "listening…"
                }
            }
        }

        // Observe partial speech
        lifecycleScope.launch {
            speechInput.partialText.collectLatest { text ->
                partialSpeech.value = text
            }
        }

        // Observe Velaris events
        lifecycleScope.launch {
            velarisClient.events.collectLatest { event ->
                Log.i(TAG, "Velaris event: ${event.type}")
                eventText.value = event.type
                // Clear event text after 3 seconds
                launch {
                    kotlinx.coroutines.delay(3000)
                    if (eventText.value == event.type) {
                        eventText.value = ""
                    }
                }
            }
        }

        // Set up Compose UI
        setContent {
            VelarisAir3Theme {
                HudOverlay(
                    status = statusText.value,
                    conversationText = conversationText.value,
                    partialSpeech = partialSpeech.value,
                    emotionalState = emotionalState.value,
                    eventText = eventText.value,
                    isListening = isListening.value,
                    isConnected = isConnected.value,
                )
            }
        }
    }

    /**
     * Handle recognized user speech — full pipeline.
     */
    private suspend fun handleUserSpeech(text: String) {
        if (isProcessing) return
        isProcessing = true

        Log.i(TAG, "User said: $text")
        statusText.value = "thinking…"
        partialSpeech.value = ""

        try {
            // Send to Velaris
            val response = velarisClient.chat(text)

            // Show response on HUD
            conversationText.value = response.text
            Log.i(TAG, "Velaris: ${response.text}")

            // Speak response via MiniMax TTS
            if (ttsPlayer.isConfigured && response.text.isNotBlank()) {
                statusText.value = "speaking…"
                ttsPlayer.speak(response.text)
            }

            statusText.value = "ready"

            // Auto-hide conversation text after display time
            val displayMs = maxOf(3000L, response.text.split(" ").size * 400L)
            lifecycleScope.launch {
                kotlinx.coroutines.delay(displayMs)
                if (conversationText.value == response.text) {
                    conversationText.value = ""
                }
            }

        } catch (e: Exception) {
            Log.e(TAG, "Pipeline error: ${e.message}", e)
            statusText.value = "error"
            conversationText.value = "[Error: ${e.message}]"
        } finally {
            isProcessing = false

            // Resume listening in continuous mode
            if (continuousMode) {
                speechInput.startListening(continuous = true)
            }
        }
    }

    /**
     * Handle hardware key events — INMO Air3 touchpad/temple touch.
     *
     * Single tap: toggle push-to-talk
     * Long press: open settings
     */
    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        return when (keyCode) {
            // Volume up or touchpad tap → toggle listening
            KeyEvent.KEYCODE_VOLUME_UP,
            KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE -> {
                toggleListening()
                true
            }
            // Volume down → open settings
            KeyEvent.KEYCODE_VOLUME_DOWN -> {
                if (event?.isLongPress == true) {
                    openSettings()
                    true
                } else {
                    // Stop any current speech
                    ttsPlayer.stop()
                    true
                }
            }
            else -> super.onKeyDown(keyCode, event)
        }
    }

    /**
     * Toggle push-to-talk listening.
     */
    private fun toggleListening() {
        if (isListening.value) {
            speechInput.stopListening()
            statusText.value = "ready"
        } else {
            if (isProcessing) {
                // Interrupt current speech
                ttsPlayer.stop()
                isProcessing = false
            }
            speechInput.startListening(continuous = continuousMode)
        }
    }

    /**
     * Open settings activity.
     */
    private fun openSettings() {
        startActivity(Intent(this, SettingsActivity::class.java))
    }

    override fun onDestroy() {
        super.onDestroy()
        speechInput.destroy()
        ttsPlayer.stop()
        velarisClient.disconnect()
    }
}

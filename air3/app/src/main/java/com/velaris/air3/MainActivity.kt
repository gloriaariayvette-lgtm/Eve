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
import com.velaris.air3.vintos.VintosClient
import com.velaris.air3.voice.LiveCall
import com.velaris.air3.voice.SpeechInput
import com.velaris.air3.voice.TtsPlayer
import kotlinx.coroutines.flow.collectLatest
import kotlinx.coroutines.launch

/**
 * Vintos Air3 — Main activity. Two doors into the same house:
 *
 *   GEMMA (default)  Voice In (4 mics) → SpeechRecognizer → text
 *                    → POST /api/avatar/chat (his full avatar-chat structure, answered by
 *                      the shim = Gemma by Gloria's cost rule) → reply on HUD → MiniMax TTS
 *   LIVE (on demand) POST /api/voice/token → Grok Realtime (voice lux, server VAD) —
 *                    the exact call the phone app makes; the house assembles his
 *                    instructions (subconscious, pressure, felt, device, WAL, ledger).
 *
 * Controls:
 *   Volume Up tap          toggle push-to-talk (GEMMA)
 *   Volume Up long-press   start / hang up a LIVE call
 *   Volume Down tap        stop current speech
 *   Volume Down long-press settings
 */
class MainActivity : ComponentActivity() {

    companion object { private const val TAG = "MainActivity" }

    private lateinit var house: VintosClient
    private lateinit var speechInput: SpeechInput
    private lateinit var ttsPlayer: TtsPlayer
    private lateinit var settingsStore: SettingsStore
    private lateinit var liveCall: LiveCall

    private val statusText = mutableStateOf("initializing…")
    private val conversationText = mutableStateOf("")
    private val partialSpeech = mutableStateOf("")
    private val emotionalState = mutableStateOf(EmotionalState())
    private val eventText = mutableStateOf("")
    private val isListening = mutableStateOf(false)
    private val isConnected = mutableStateOf(false)
    private val mode = mutableStateOf("GEMMA")

    private var isProcessing = false
    private var continuousMode = false

    private val micPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) speechInput.initialize()
        else Toast.makeText(this, "Microphone permission required for voice", Toast.LENGTH_LONG).show()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        settingsStore = SettingsStore(this)
        house = VintosClient(lifecycleScope)
        speechInput = SpeechInput(this)
        ttsPlayer = TtsPlayer()
        liveCall = LiveCall(
            scope = lifecycleScope, house = house,
            onStatus = { s -> statusText.value = s; if (s == "call ended" || s == "call dropped" || s.startsWith("no token")) mode.value = "GEMMA" },
            onHisWords = { t -> conversationText.value = t },
            onHerWords = { t -> partialSpeech.value = t },
        )

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED)
            speechInput.initialize()
        else micPermission.launch(Manifest.permission.RECORD_AUDIO)

        speechInput.onSpeechResult { text -> lifecycleScope.launch { handleUserSpeech(text) } }

        lifecycleScope.launch {
            settingsStore.settings.collectLatest { settings ->
                if (settings.isConfigured) {
                    house.connect(settings.vintosUrl, settings.vintosSecret)
                    continuousMode = settings.continuousListen
                    if (settings.minimaxApiKey.isNotBlank())
                        ttsPlayer.configure(apiKey = settings.minimaxApiKey, voiceId = settings.minimaxVoice)
                    statusText.value = "ready"
                } else statusText.value = "configure in settings (URL + secret)"
            }
        }
        lifecycleScope.launch { house.connected.collectLatest { c -> isConnected.value = c; if (!c && statusText.value == "ready") statusText.value = "disconnected" } }
        lifecycleScope.launch { house.emotionalState.collectLatest { emotionalState.value = it } }
        lifecycleScope.launch {
            speechInput.state.collectLatest { st ->
                isListening.value = st == SpeechInput.ListenState.LISTENING
                if (st == SpeechInput.ListenState.LISTENING) statusText.value = "listening…"
            }
        }
        lifecycleScope.launch { speechInput.partialText.collectLatest { if (mode.value == "GEMMA") partialSpeech.value = it } }
        lifecycleScope.launch {
            house.events.collectLatest { ev ->
                eventText.value = ev.type
                launch { kotlinx.coroutines.delay(3000); if (eventText.value == ev.type) eventText.value = "" }
            }
        }

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
                    mode = mode.value,
                )
            }
        }
    }

    /** GEMMA path: one recognized utterance → one avatar-chat turn. */
    private suspend fun handleUserSpeech(text: String) {
        if (isProcessing || mode.value == "LIVE") return
        isProcessing = true
        statusText.value = "thinking…"; partialSpeech.value = ""
        try {
            val response = house.chat(text)
            conversationText.value = response.text
            if (ttsPlayer.isConfigured && response.text.isNotBlank()) { statusText.value = "speaking…"; ttsPlayer.speak(response.text) }
            statusText.value = "ready"
            val displayMs = maxOf(3000L, response.text.split(" ").size * 400L)
            lifecycleScope.launch { kotlinx.coroutines.delay(displayMs); if (conversationText.value == response.text) conversationText.value = "" }
        } catch (e: Exception) {
            Log.e(TAG, "turn error: ${e.message}", e); statusText.value = "error"; conversationText.value = "[error: ${e.message}]"
        } finally {
            isProcessing = false
            if (continuousMode) speechInput.startListening(continuous = true)
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean = when (keyCode) {
        KeyEvent.KEYCODE_VOLUME_UP, KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE -> {
            if (event?.repeatCount == 0) event.startTracking()
            true
        }
        KeyEvent.KEYCODE_VOLUME_DOWN -> {
            if (event?.isLongPress == true) openSettings() else ttsPlayer.stop()
            true
        }
        else -> super.onKeyDown(keyCode, event)
    }

    override fun onKeyLongPress(keyCode: Int, event: KeyEvent?): Boolean {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE) { toggleLiveCall(); return true }
        return super.onKeyLongPress(keyCode, event)
    }

    override fun onKeyUp(keyCode: Int, event: KeyEvent?): Boolean {
        if ((keyCode == KeyEvent.KEYCODE_VOLUME_UP || keyCode == KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE)
            && event?.isCanceled == false && (event.flags and KeyEvent.FLAG_LONG_PRESS) == 0) {
            if (mode.value == "GEMMA") toggleListening()
            return true
        }
        return super.onKeyUp(keyCode, event)
    }

    private fun toggleLiveCall() {
        if (liveCall.active) { liveCall.stop(); return }
        if (isListening.value) speechInput.stopListening()
        ttsPlayer.stop(); isProcessing = false
        mode.value = "LIVE"; conversationText.value = ""; partialSpeech.value = ""
        liveCall.start()
    }

    private fun toggleListening() {
        if (isListening.value) { speechInput.stopListening(); statusText.value = "ready" }
        else { if (isProcessing) { ttsPlayer.stop(); isProcessing = false }; speechInput.startListening(continuous = continuousMode) }
    }

    private fun openSettings() = startActivity(Intent(this, SettingsActivity::class.java))

    override fun onDestroy() {
        super.onDestroy()
        liveCall.stop(); speechInput.destroy(); ttsPlayer.stop(); house.disconnect()
    }
}

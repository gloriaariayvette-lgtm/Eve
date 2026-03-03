package com.velaris.air3.voice

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Voice input using Android's SpeechRecognizer.
 *
 * Uses the INMO Air3's 4 built-in microphones for speech-to-text.
 * Supports continuous listening with auto-restart, or push-to-talk mode.
 */
class SpeechInput(private val context: Context) {

    companion object {
        private const val TAG = "SpeechInput"
    }

    enum class ListenState {
        IDLE,
        LISTENING,
        PROCESSING,
        ERROR,
    }

    private var recognizer: SpeechRecognizer? = null
    private var onResult: ((String) -> Unit)? = null
    private var continuousMode = false

    private val _state = MutableStateFlow(ListenState.IDLE)
    val state: StateFlow<ListenState> = _state

    // Partial results for HUD display
    private val _partialText = MutableStateFlow("")
    val partialText: StateFlow<String> = _partialText

    /**
     * Initialize the speech recognizer.
     */
    fun initialize() {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            Log.e(TAG, "Speech recognition not available on this device")
            _state.value = ListenState.ERROR
            return
        }

        recognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
            setRecognitionListener(createListener())
        }

        Log.i(TAG, "SpeechRecognizer initialized")
    }

    /**
     * Set callback for when speech is recognized.
     */
    fun onSpeechResult(callback: (String) -> Unit) {
        onResult = callback
    }

    /**
     * Start listening for speech (single utterance or continuous).
     */
    fun startListening(continuous: Boolean = false) {
        continuousMode = continuous
        _state.value = ListenState.LISTENING
        _partialText.value = ""

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            // Longer silence threshold for natural pauses
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 2000L)
            putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_MINIMUM_LENGTH_MILLIS, 500L)
        }

        try {
            recognizer?.startListening(intent)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start listening: ${e.message}")
            _state.value = ListenState.ERROR
        }
    }

    /**
     * Stop listening.
     */
    fun stopListening() {
        continuousMode = false
        recognizer?.stopListening()
        _state.value = ListenState.IDLE
        _partialText.value = ""
    }

    /**
     * Release resources.
     */
    fun destroy() {
        recognizer?.destroy()
        recognizer = null
    }

    private fun createListener(): RecognitionListener = object : RecognitionListener {
        override fun onReadyForSpeech(params: Bundle?) {
            Log.d(TAG, "Ready for speech")
            _state.value = ListenState.LISTENING
        }

        override fun onBeginningOfSpeech() {
            Log.d(TAG, "Speech started")
        }

        override fun onRmsChanged(rmsdB: Float) {
            // Could use for audio level visualization
        }

        override fun onBufferReceived(buffer: ByteArray?) {}

        override fun onEndOfSpeech() {
            Log.d(TAG, "Speech ended")
            _state.value = ListenState.PROCESSING
        }

        override fun onError(error: Int) {
            val errorMsg = when (error) {
                SpeechRecognizer.ERROR_NO_MATCH -> "No speech detected"
                SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Speech timeout"
                SpeechRecognizer.ERROR_AUDIO -> "Audio error"
                SpeechRecognizer.ERROR_NETWORK -> "Network error"
                SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                else -> "Error code: $error"
            }
            Log.w(TAG, "Recognition error: $errorMsg")

            _state.value = ListenState.IDLE
            _partialText.value = ""

            // Auto-restart in continuous mode (except for audio errors)
            if (continuousMode && error != SpeechRecognizer.ERROR_AUDIO) {
                startListening(continuous = true)
            }
        }

        override fun onResults(results: Bundle?) {
            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            val text = matches?.firstOrNull()?.trim() ?: ""

            Log.i(TAG, "Recognized: $text")
            _partialText.value = ""

            if (text.isNotEmpty()) {
                onResult?.invoke(text)
            }

            _state.value = ListenState.IDLE

            // Auto-restart in continuous mode
            if (continuousMode) {
                startListening(continuous = true)
            }
        }

        override fun onPartialResults(partialResults: Bundle?) {
            val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            val partial = matches?.firstOrNull()?.trim() ?: ""
            if (partial.isNotEmpty()) {
                _partialText.value = partial
            }
        }

        override fun onEvent(eventType: Int, params: Bundle?) {}
    }
}

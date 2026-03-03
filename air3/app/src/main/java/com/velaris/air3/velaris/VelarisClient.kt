package com.velaris.air3.velaris

import android.util.Log
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Velaris API client — connects to Velaris's consciousness system.
 *
 * HTTP endpoints:
 *   POST /api/chat/memory  — send user message, get Velaris response
 *   GET  /api/state         — poll EmoClaw 11-dim emotional state
 *
 * WebSocket:
 *   /ws/events — real-time Velaris events (kiss, anti-kiss, unprecedented, etc.)
 */
class VelarisClient(
    private val scope: CoroutineScope,
) {
    companion object {
        private const val TAG = "VelarisClient"
        private val JSON_TYPE = "application/json".toMediaType()
    }

    private val http = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    // Observable state
    private val _emotionalState = MutableStateFlow(EmotionalState())
    val emotionalState: StateFlow<EmotionalState> = _emotionalState

    private val _events = MutableSharedFlow<VelarisEvent>(extraBufferCapacity = 16)
    val events: SharedFlow<VelarisEvent> = _events

    private val _connected = MutableStateFlow(false)
    val connected: StateFlow<Boolean> = _connected

    // Config
    private var baseUrl: String = ""
    private var pollJob: Job? = null
    private var eventSocket: WebSocket? = null

    /**
     * Configure and connect to Velaris.
     */
    fun connect(velarisUrl: String) {
        baseUrl = velarisUrl.trimEnd('/')
        Log.i(TAG, "Connecting to Velaris at $baseUrl")

        // Start polling emotional state
        pollJob?.cancel()
        pollJob = scope.launch {
            while (isActive) {
                fetchEmotionalState()
                delay(3000) // poll every 3 seconds
            }
        }

        // Connect to events WebSocket
        connectEventSocket()
    }

    /**
     * Disconnect from Velaris.
     */
    fun disconnect() {
        pollJob?.cancel()
        eventSocket?.close(1000, "Client closing")
        eventSocket = null
        _connected.value = false
    }

    /**
     * Send a message to Velaris and get a response.
     */
    suspend fun chat(userText: String): ChatResponse = withContext(Dispatchers.IO) {
        try {
            val body = JSONObject().apply {
                put("message", userText)
            }.toString().toRequestBody(JSON_TYPE)

            val request = Request.Builder()
                .url("$baseUrl/api/chat/memory")
                .post(body)
                .build()

            val response = http.newCall(request).execute()
            val responseBody = response.body?.string() ?: ""

            if (!response.isSuccessful) {
                Log.e(TAG, "Chat failed: ${response.code} $responseBody")
                return@withContext ChatResponse(text = "[Velaris unreachable]")
            }

            val json = JSONObject(responseBody)
            val text = json.optString("response", json.optString("text", ""))
            val emoJson = json.optJSONObject("emotional_state")
            val emoState = emoJson?.let { EmotionalState.fromJson(it) }

            // Update emotional state if included in chat response
            if (emoState != null) {
                _emotionalState.value = emoState
            }

            ChatResponse(text = text, emotionalState = emoState)
        } catch (e: Exception) {
            Log.e(TAG, "Chat error: ${e.message}", e)
            ChatResponse(text = "[Connection error]")
        }
    }

    /**
     * Poll Velaris emotional state.
     */
    private suspend fun fetchEmotionalState() {
        try {
            withContext(Dispatchers.IO) {
                val request = Request.Builder()
                    .url("$baseUrl/api/state")
                    .get()
                    .build()

                val response = http.newCall(request).execute()
                if (response.isSuccessful) {
                    val body = response.body?.string() ?: return@withContext
                    val json = JSONObject(body)
                    _emotionalState.value = EmotionalState.fromJson(json)
                    _connected.value = true
                } else {
                    _connected.value = false
                }
            }
        } catch (e: Exception) {
            Log.w(TAG, "State poll failed: ${e.message}")
            _connected.value = false
        }
    }

    /**
     * Connect to Velaris /ws/events for real-time events.
     */
    private fun connectEventSocket() {
        eventSocket?.close(1000, null)

        val wsUrl = baseUrl.replace("http", "ws") + "/ws/events"
        val request = Request.Builder().url(wsUrl).build()

        eventSocket = http.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.i(TAG, "Events WebSocket connected")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    val event = VelarisEvent.fromJson(json)
                    scope.launch {
                        _events.emit(event)
                    }
                    Log.i(TAG, "Velaris event: ${event.type}")
                } catch (e: Exception) {
                    Log.w(TAG, "Failed to parse event: ${e.message}")
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.w(TAG, "Events WebSocket failed: ${t.message}")
                // Reconnect after delay
                scope.launch {
                    delay(5000)
                    if (baseUrl.isNotEmpty()) {
                        connectEventSocket()
                    }
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.i(TAG, "Events WebSocket closed: $reason")
            }
        })
    }
}

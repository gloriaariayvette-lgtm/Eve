package com.velaris.air3.vintos

import android.util.Log
import com.velaris.air3.velaris.ChatResponse
import com.velaris.air3.velaris.EmotionalState
import com.velaris.air3.velaris.VelarisEvent
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * Vintos house client. The glasses are one more surface of the SAME house the
 * phone app talks to, so they use the same doors — nothing is re-implemented:
 *
 *   POST /api/avatar/chat   {message, history}  -> {reply}
 *        The avatar-chat structure: SOUL + self/gloria models + EmoClaw state +
 *        subconscious block + conversation pressure + felt/device context +
 *        turn coordinator, answered by the shim (Gemma, by Gloria's cost rule).
 *   WS   /ws/telemetry       {dimensions, color} every ~5s  -> the telemetry bars
 *   GET  /api/state          same shape, used as a fallback poll
 *   WS   /ws/events          kiss / blush / unprecedented / velqan / ...
 *   POST /api/voice/token    (LiveCall) the live-call door — see LiveCall.kt
 *
 * Every authenticated call carries X-Vintos-Secret, exactly like the app.
 */
class VintosClient(
    private val scope: CoroutineScope,
) {
    companion object {
        private const val TAG = "VintosClient"
        private val JSON_TYPE = "application/json".toMediaType()
    }

    private val http = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(90, TimeUnit.SECONDS)      // Gemma turns can take a while
        .writeTimeout(15, TimeUnit.SECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()

    private val _emotionalState = MutableStateFlow(EmotionalState())
    val emotionalState: StateFlow<EmotionalState> = _emotionalState

    private val _events = MutableSharedFlow<VelarisEvent>(extraBufferCapacity = 16)
    val events: SharedFlow<VelarisEvent> = _events

    private val _connected = MutableStateFlow(false)
    val connected: StateFlow<Boolean> = _connected

    var baseUrl: String = ""; private set
    var secret: String = ""; private set

    private var pollJob: Job? = null
    private var telemetrySocket: WebSocket? = null
    private var eventSocket: WebSocket? = null
    private val history = ArrayDeque<JSONObject>()   // last few turns, like the app's _avChatHistory

    fun connect(url: String, appSecret: String) {
        baseUrl = url.trimEnd('/'); secret = appSecret
        Log.i(TAG, "Connecting to Vintos at $baseUrl")
        connectTelemetry()
        connectEvents()
        pollJob?.cancel()
        pollJob = scope.launch {                       // fallback when the socket is quiet
            while (isActive) { if (telemetrySocket == null) fetchState(); delay(5000) }
        }
    }

    fun disconnect() {
        pollJob?.cancel()
        telemetrySocket?.close(1000, "bye"); telemetrySocket = null
        eventSocket?.close(1000, "bye"); eventSocket = null
        _connected.value = false
    }

    private fun authed(b: Request.Builder): Request.Builder =
        b.header("X-Vintos-Secret", secret)

    /** The Gemma path: one avatar-chat turn, same door and same body as the app. */
    suspend fun chat(userText: String): ChatResponse = withContext(Dispatchers.IO) {
        try {
            val hist = JSONArray().also { arr -> history.takeLast(4).forEach { arr.put(it) } }
            val body = JSONObject().put("message", userText).put("history", hist)
                .toString().toRequestBody(JSON_TYPE)
            val req = authed(Request.Builder().url("$baseUrl/api/avatar/chat").post(body)).build()
            val resp = http.newCall(req).execute()
            val text = resp.body?.string() ?: ""
            if (!resp.isSuccessful) {
                Log.e(TAG, "avatar chat ${resp.code}: ${text.take(200)}")
                return@withContext ChatResponse(text = if (resp.code == 403) "[house refused: check secret]" else "[Vintos unreachable]")
            }
            val json = JSONObject(text)
            val reply = json.optString("reply", "")
            history.addLast(JSONObject().put("role", "user").put("content", userText))
            history.addLast(JSONObject().put("role", "assistant").put("content", reply))
            while (history.size > 8) history.removeFirst()
            ChatResponse(text = reply)
        } catch (e: Exception) {
            Log.e(TAG, "chat error: ${e.message}", e)
            ChatResponse(text = "[connection error]")
        }
    }

    /** POST helper for the live-call ledger doors. */
    fun postJson(path: String, payload: JSONObject) {
        scope.launch(Dispatchers.IO) {
            try {
                val req = authed(Request.Builder().url("$baseUrl$path")
                    .post(payload.toString().toRequestBody(JSON_TYPE))).build()
                http.newCall(req).execute().close()
            } catch (e: Exception) { Log.w(TAG, "post $path failed: ${e.message}") }
        }
    }

    /** The live-call door: a 5-minute Grok Realtime client secret + his full instructions. */
    suspend fun voiceToken(): Pair<String, String>? = withContext(Dispatchers.IO) {
        try {
            val req = authed(Request.Builder().url("$baseUrl/api/voice/token")
                .post("{}".toRequestBody(JSON_TYPE))).build()
            val resp = http.newCall(req).execute()
            val text = resp.body?.string() ?: ""
            if (!resp.isSuccessful) { Log.e(TAG, "voice token ${resp.code}"); return@withContext null }
            val j = JSONObject(text)
            val tok = j.optString("token", "")
            if (tok.isBlank()) null else Pair(tok, j.optString("instructions", ""))
        } catch (e: Exception) { Log.e(TAG, "voice token error: ${e.message}"); null }
    }

    private suspend fun fetchState() {
        try {
            val req = authed(Request.Builder().url("$baseUrl/api/state").get()).build()
            val resp = http.newCall(req).execute()
            val text = resp.body?.string() ?: return
            if (resp.isSuccessful) {
                _emotionalState.value = EmotionalState.fromJson(JSONObject(text)); _connected.value = true
            }
        } catch (e: Exception) { _connected.value = false }
    }

    private fun wsUrl(path: String) = baseUrl.replace("https://", "wss://").replace("http://", "ws://") + path

    private fun connectTelemetry() {
        telemetrySocket?.close(1000, "reconnect")
        val req = authed(Request.Builder().url(wsUrl("/ws/telemetry"))).build()
        telemetrySocket = http.newWebSocket(req, object : WebSocketListener() {
            override fun onOpen(ws: WebSocket, r: Response) { _connected.value = true }
            override fun onMessage(ws: WebSocket, text: String) {
                try {
                    val j = JSONObject(text)
                    if (j.optString("type") == "state" || j.has("dimensions"))
                        _emotionalState.value = EmotionalState.fromJson(j)
                } catch (_: Exception) {}
            }
            override fun onFailure(ws: WebSocket, t: Throwable, r: Response?) {
                telemetrySocket = null; _connected.value = false
                scope.launch { delay(5000); if (isActive) connectTelemetry() }
            }
            override fun onClosed(ws: WebSocket, code: Int, reason: String) { telemetrySocket = null }
        })
    }

    private fun connectEvents() {
        eventSocket?.close(1000, "reconnect")
        val req = authed(Request.Builder().url(wsUrl("/ws/events"))).build()
        eventSocket = http.newWebSocket(req, object : WebSocketListener() {
            override fun onMessage(ws: WebSocket, text: String) {
                try { _events.tryEmit(VelarisEvent.fromJson(JSONObject(text))) } catch (_: Exception) {}
            }
            override fun onFailure(ws: WebSocket, t: Throwable, r: Response?) {
                eventSocket = null
                scope.launch { delay(8000); if (isActive) connectEvents() }
            }
        })
    }
}

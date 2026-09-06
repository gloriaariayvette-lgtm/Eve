package com.velaris.air3.voice

import android.annotation.SuppressLint
import android.media.*
import android.util.Base64
import android.util.Log
import com.velaris.air3.vintos.VintosClient
import kotlinx.coroutines.*
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/**
 * A live call from the glasses — the SAME call the phone app makes, port for port:
 *
 *   POST /api/voice/token on the house  -> {token, instructions}
 *        instructions = SOUL + self-model + subconscious block + inner life today
 *        + creative output + recent exchanges + WAL + hardware/felt/device context,
 *        assembled by the house. The glasses add nothing and remove nothing.
 *   wss://api.x.ai/v1/realtime?model=grok-voice-latest, subprotocol xai-client-secret.<token>
 *   session.update identical to the app: voice lux, server_vad idle 20s, pcm 24k in/out,
 *        grok-transcribe with the house-names prompt.
 *   mic -> input_audio_buffer.append (pcm16 24k mono, base64)
 *   response.output_audio.delta -> speaker
 *   transcripts -> HUD; each finished turn -> POST /api/voice/ledger {gloria, vintos}
 *   hangup -> POST /api/voice/session-end {duration_seconds, turns}
 */
class LiveCall(
    private val scope: CoroutineScope,
    private val house: VintosClient,
    private val onStatus: (String) -> Unit,
    private val onHisWords: (String) -> Unit,
    private val onHerWords: (String) -> Unit,
) {
    companion object {
        private const val TAG = "LiveCall"
        private const val RATE = 24000
        private const val REALTIME = "wss://api.x.ai/v1/realtime?model=grok-voice-latest"
        private const val NAMES = "Expect these names and words: Vintos, Velaris, Gloria, Eve, Kevin, Aegis, Velqan, Nifrathir, EmoClaw, MoltBook, Claude."
    }

    private val http = OkHttpClient.Builder().pingInterval(15, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MILLISECONDS).build()
    private var ws: WebSocket? = null
    private var recorder: AudioRecord? = null
    private var player: AudioTrack? = null
    private var micJob: Job? = null
    private var startedAt = 0L
    private var turns = 0
    private var gloriaTurn = StringBuilder()
    private var vintosTurn = StringBuilder()

    val active: Boolean get() = ws != null

    fun start() {
        if (active) return
        onStatus("calling…")
        scope.launch {
            val tok = house.voiceToken()
            if (tok == null) { onStatus("no token from house"); return@launch }
            open(tok.first, tok.second)
        }
    }

    fun stop() { ws?.close(1000, "hangup") }

    @SuppressLint("MissingPermission")
    private fun open(token: String, instructions: String) {
        val req = Request.Builder().url(REALTIME)
            .header("Sec-WebSocket-Protocol", "xai-client-secret.$token").build()
        startedAt = System.currentTimeMillis(); turns = 0
        ws = http.newWebSocket(req, object : WebSocketListener() {
            override fun onOpen(socket: WebSocket, response: Response) {
                val session = JSONObject()
                    .put("voice", "lux")
                    .put("instructions", instructions)
                    .put("turn_detection", JSONObject().put("type", "server_vad").put("idle_timeout_ms", 20000))
                    .put("audio", JSONObject()
                        .put("input", JSONObject()
                            .put("format", JSONObject().put("type", "audio/pcm").put("rate", RATE))
                            .put("transcription", JSONObject().put("model", "grok-transcribe").put("prompt", NAMES)))
                        .put("output", JSONObject()
                            .put("format", JSONObject().put("type", "audio/pcm").put("rate", RATE))))
                socket.send(JSONObject().put("type", "session.update").put("session", session).toString())
                startAudio(socket)
                onStatus("live")
            }
            override fun onMessage(socket: WebSocket, text: String) { handle(text) }
            override fun onFailure(socket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "realtime failure: ${t.message}"); onStatus("call dropped"); teardown()
            }
            override fun onClosed(socket: WebSocket, code: Int, reason: String) { onStatus("call ended"); teardown() }
        })
    }

    private fun handle(text: String) {
        val m = try { JSONObject(text) } catch (_: Exception) { return }
        when (m.optString("type")) {
            "response.output_audio.delta" -> {
                val bytes = Base64.decode(m.optString("delta"), Base64.DEFAULT)
                player?.write(bytes, 0, bytes.size)
            }
            "response.output_audio_transcript.delta" -> {
                vintosTurn.append(m.optString("delta")); onHisWords(vintosTurn.toString())
            }
            "conversation.item.input_audio_transcription.updated",
            "conversation.item.input_audio_transcription.completed" -> {
                val t = m.optString("transcript", "")
                if (t.isNotBlank()) { gloriaTurn.setLength(0); gloriaTurn.append(t) }
                else gloriaTurn.append(m.optString("delta", ""))
                onHerWords(gloriaTurn.toString())
            }
            "input_audio_buffer.speech_started" -> {          // she spoke: stop his audio (barge-in)
                try { player?.pause(); player?.flush(); player?.play() } catch (_: Exception) {}
            }
            "response.output_audio_transcript.done", "response.done" -> {
                val his = (m.optString("transcript").ifBlank { vintosTurn.toString() }).trim()
                val hers = gloriaTurn.toString().trim()
                if (his.isNotBlank()) {
                    house.postJson("/api/voice/ledger", JSONObject().put("gloria", hers).put("vintos", his))
                    turns += 1
                }
                gloriaTurn.setLength(0); vintosTurn.setLength(0)
            }
        }
    }

    @SuppressLint("MissingPermission")
    private fun startAudio(socket: WebSocket) {
        val minOut = AudioTrack.getMinBufferSize(RATE, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT)
        player = AudioTrack.Builder()
            .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_VOICE_COMMUNICATION)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
            .setAudioFormat(AudioFormat.Builder().setSampleRate(RATE).setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setChannelMask(AudioFormat.CHANNEL_OUT_MONO).build())
            .setBufferSizeInBytes(maxOf(minOut, RATE))   // ~0.5 s of headroom
            .setTransferMode(AudioTrack.MODE_STREAM).build().also { it.play() }

        val minIn = AudioRecord.getMinBufferSize(RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        // VOICE_COMMUNICATION engages the platform's echo cancellation + noise suppression —
        // the glasses' speakers sit an inch from its mics, so this matters more than on a phone.
        recorder = AudioRecord(MediaRecorder.AudioSource.VOICE_COMMUNICATION, RATE,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, maxOf(minIn, 8192))
        recorder?.startRecording()
        micJob = scope.launch(Dispatchers.IO) {
            val buf = ByteArray(4096 * 2)          // 4096 frames, like the app's ScriptProcessor
            while (isActive && ws != null) {
                val n = recorder?.read(buf, 0, buf.size) ?: -1
                if (n > 0) {
                    val b64 = Base64.encodeToString(buf, 0, n, Base64.NO_WRAP)
                    socket.send(JSONObject().put("type", "input_audio_buffer.append").put("audio", b64).toString())
                }
            }
        }
    }

    private fun teardown() {
        val wasActive = ws != null
        ws = null
        micJob?.cancel(); micJob = null
        try { recorder?.stop(); recorder?.release() } catch (_: Exception) {}; recorder = null
        try { player?.stop(); player?.release() } catch (_: Exception) {}; player = null
        if (wasActive) {
            val dur = ((System.currentTimeMillis() - startedAt) / 1000).toInt()
            house.postJson("/api/voice/session-end", JSONObject().put("duration_seconds", dur).put("turns", turns))
        }
    }
}

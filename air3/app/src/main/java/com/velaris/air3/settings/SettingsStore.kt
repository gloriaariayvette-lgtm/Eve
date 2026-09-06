package com.velaris.air3.settings

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Persistent settings for the Vintos Air3 app.
 *
 * Stores: Vintos house URL, the app secret (X-Vintos-Secret), MiniMax TTS key
 * and voice for the Gemma (text) path, and preferences.
 */

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "vintos_settings")

class SettingsStore(private val context: Context) {

    companion object {
        const val DEFAULT_URL = "http://100.72.225.119:8500"   // Aegis over Tailscale
        val VINTOS_URL = stringPreferencesKey("vintos_url")
        val VINTOS_SECRET = stringPreferencesKey("vintos_secret")
        val MINIMAX_API_KEY = stringPreferencesKey("minimax_api_key")
        val MINIMAX_VOICE = stringPreferencesKey("minimax_voice")
        val CONTINUOUS_LISTEN = booleanPreferencesKey("continuous_listen")
    }

    data class Settings(
        val vintosUrl: String = DEFAULT_URL,
        val vintosSecret: String = "",
        val minimaxApiKey: String = "",
        val minimaxVoice: String = "Wise_Woman",
        val continuousListen: Boolean = false,
    ) {
        /** The house refuses avatar chat and live calls without the secret. */
        val isConfigured: Boolean
            get() = vintosUrl.isNotBlank() && vintosSecret.isNotBlank()
    }

    val settings: Flow<Settings> = context.dataStore.data.map { prefs ->
        Settings(
            vintosUrl = prefs[VINTOS_URL] ?: DEFAULT_URL,
            vintosSecret = prefs[VINTOS_SECRET] ?: "",
            minimaxApiKey = prefs[MINIMAX_API_KEY] ?: "",
            minimaxVoice = prefs[MINIMAX_VOICE] ?: "Wise_Woman",
            continuousListen = prefs[CONTINUOUS_LISTEN] ?: false,
        )
    }

    suspend fun saveAll(settings: Settings) {
        context.dataStore.edit { prefs ->
            prefs[VINTOS_URL] = settings.vintosUrl
            prefs[VINTOS_SECRET] = settings.vintosSecret
            prefs[MINIMAX_API_KEY] = settings.minimaxApiKey
            prefs[MINIMAX_VOICE] = settings.minimaxVoice
            prefs[CONTINUOUS_LISTEN] = settings.continuousListen
        }
    }
}

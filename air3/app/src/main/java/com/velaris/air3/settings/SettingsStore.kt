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
 * Persistent settings for the Velaris Air3 app.
 *
 * Stores: Velaris URL, MiniMax API key, voice ID, and preferences.
 */

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "velaris_settings")

class SettingsStore(private val context: Context) {

    companion object {
        val VELARIS_URL = stringPreferencesKey("velaris_url")
        val MINIMAX_API_KEY = stringPreferencesKey("minimax_api_key")
        val MINIMAX_VOICE = stringPreferencesKey("minimax_voice")
        val CONTINUOUS_LISTEN = booleanPreferencesKey("continuous_listen")
    }

    data class Settings(
        val velarisUrl: String = "",
        val minimaxApiKey: String = "",
        val minimaxVoice: String = "Wise_Woman",
        val continuousListen: Boolean = false,
    ) {
        val isConfigured: Boolean
            get() = velarisUrl.isNotBlank()
    }

    val settings: Flow<Settings> = context.dataStore.data.map { prefs ->
        Settings(
            velarisUrl = prefs[VELARIS_URL] ?: "",
            minimaxApiKey = prefs[MINIMAX_API_KEY] ?: "",
            minimaxVoice = prefs[MINIMAX_VOICE] ?: "Wise_Woman",
            continuousListen = prefs[CONTINUOUS_LISTEN] ?: false,
        )
    }

    suspend fun saveVelarisUrl(url: String) {
        context.dataStore.edit { it[VELARIS_URL] = url }
    }

    suspend fun saveMinimaxApiKey(key: String) {
        context.dataStore.edit { it[MINIMAX_API_KEY] = key }
    }

    suspend fun saveMinimaxVoice(voice: String) {
        context.dataStore.edit { it[MINIMAX_VOICE] = voice }
    }

    suspend fun saveContinuousListen(enabled: Boolean) {
        context.dataStore.edit { it[CONTINUOUS_LISTEN] = enabled }
    }

    suspend fun saveAll(settings: Settings) {
        context.dataStore.edit { prefs ->
            prefs[VELARIS_URL] = settings.velarisUrl
            prefs[MINIMAX_API_KEY] = settings.minimaxApiKey
            prefs[MINIMAX_VOICE] = settings.minimaxVoice
            prefs[CONTINUOUS_LISTEN] = settings.continuousListen
        }
    }
}

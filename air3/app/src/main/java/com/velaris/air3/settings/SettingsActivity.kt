package com.velaris.air3.settings

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.velaris.air3.ui.theme.VelarisAir3Theme
import com.velaris.air3.ui.theme.VelarisPink
import kotlinx.coroutines.launch

/**
 * Settings screen for configuring Velaris connection.
 *
 * Fields:
 * - Velaris URL (e.g. http://100.72.225.119:8400)
 * - MiniMax API Key
 * - MiniMax Voice ID
 * - Continuous listening toggle
 */
class SettingsActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val store = SettingsStore(this)

        setContent {
            VelarisAir3Theme {
                SettingsScreen(store = store, onDone = { finish() })
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun SettingsScreen(store: SettingsStore, onDone: () -> Unit) {
    val scope = rememberCoroutineScope()
    val currentSettings by store.settings.collectAsState(initial = SettingsStore.Settings())

    var velarisUrl by remember(currentSettings) { mutableStateOf(currentSettings.velarisUrl) }
    var minimaxKey by remember(currentSettings) { mutableStateOf(currentSettings.minimaxApiKey) }
    var minimaxVoice by remember(currentSettings) { mutableStateOf(currentSettings.minimaxVoice) }
    var continuousListen by remember(currentSettings) { mutableStateOf(currentSettings.continuousListen) }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .padding(32.dp),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(0.7f),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(
                text = "Velaris Settings",
                style = MaterialTheme.typography.headlineSmall,
                color = VelarisPink,
            )

            Spacer(Modifier.height(8.dp))

            // Velaris URL
            OutlinedTextField(
                value = velarisUrl,
                onValueChange = { velarisUrl = it },
                label = { Text("Velaris URL") },
                placeholder = { Text("http://100.72.225.119:8400") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = velarisTextFieldColors(),
            )

            // MiniMax API Key
            OutlinedTextField(
                value = minimaxKey,
                onValueChange = { minimaxKey = it },
                label = { Text("MiniMax API Key") },
                singleLine = true,
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
                colors = velarisTextFieldColors(),
            )

            // MiniMax Voice
            OutlinedTextField(
                value = minimaxVoice,
                onValueChange = { minimaxVoice = it },
                label = { Text("MiniMax Voice ID") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = velarisTextFieldColors(),
            )

            // Continuous listening toggle
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "Continuous listening",
                    style = MaterialTheme.typography.bodyLarge,
                    color = Color.White,
                )
                Switch(
                    checked = continuousListen,
                    onCheckedChange = { continuousListen = it },
                    colors = SwitchDefaults.colors(checkedThumbColor = VelarisPink),
                )
            }

            Spacer(Modifier.height(16.dp))

            // Save button
            Button(
                onClick = {
                    scope.launch {
                        store.saveAll(
                            SettingsStore.Settings(
                                velarisUrl = velarisUrl.trim(),
                                minimaxApiKey = minimaxKey.trim(),
                                minimaxVoice = minimaxVoice.trim().ifBlank { "Wise_Woman" },
                                continuousListen = continuousListen,
                            )
                        )
                        onDone()
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(containerColor = VelarisPink),
            ) {
                Text("Save", color = Color.White)
            }
        }
    }
}

@Composable
private fun velarisTextFieldColors() = OutlinedTextFieldDefaults.colors(
    focusedBorderColor = VelarisPink,
    unfocusedBorderColor = Color(0xFF333344),
    focusedLabelColor = VelarisPink,
    unfocusedLabelColor = Color(0xFF888899),
    cursorColor = VelarisPink,
    focusedTextColor = Color.White,
    unfocusedTextColor = Color(0xFFCCCCDD),
)

package com.velaris.air3

import android.app.Application
import android.util.Log

/**
 * Velaris Air3 application class.
 *
 * Minimal — just logs startup. All subsystem initialization
 * happens in MainActivity to respect the activity lifecycle.
 */
class VelarisApp : Application() {

    companion object {
        const val TAG = "VelarisAir3"
    }

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "Velaris Air3 starting on INMO Air3")
    }
}

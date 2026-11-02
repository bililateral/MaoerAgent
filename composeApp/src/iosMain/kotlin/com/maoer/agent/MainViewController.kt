package com.maoer.agent

import androidx.compose.ui.window.ComposeUIViewController
import org.koin.compose.KoinApplication
import com.maoer.agent.di.appModule
import com.maoer.agent.di.platformModule

fun MainViewController() = ComposeUIViewController {
    KoinApplication(application = { modules(appModule, platformModule) }) { App() }
}

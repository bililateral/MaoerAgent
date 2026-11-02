package com.maoer.agent

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import cafe.adriel.voyager.navigator.Navigator
import com.maoer.agent.ui.home.HomeScreen

/** Android initializes its application-scoped dependencies in MaoerApplication. */
@Composable
fun App() {
    MaterialTheme { Navigator(HomeScreen) }
}

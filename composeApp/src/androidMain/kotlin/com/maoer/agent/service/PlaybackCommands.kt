package com.maoer.agent.service

/** Session command/extras shared by the Android service and its controller. */
object PlaybackCommands {
    const val SLEEP_TIMER = "com.maoer.agent.SLEEP_TIMER"
    const val MINUTES = "minutes"
    const val REMAINING_MS = "sleep_remaining_ms"
    const val END_OF_EPISODE = "sleep_end_of_episode"
}

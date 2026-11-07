package com.maoer.agent.data.agent

import com.maoer.agent.data.manager.PlayerManager
import com.maoer.agent.data.podcast.PodcastRepository
import com.maoer.agent.data.library.ListeningLibrary
import com.maoer.agent.data.download.Downloads

/** Stable session-facing facade; execution durability is separate from business tools. */
class AgentTools(repository: PodcastRepository, player: PlayerManager, storage: AgentStorage, api: AgentApi, library: ListeningLibrary, downloads: Downloads) {
    private val state = PlaybackStateReader(repository, player)
    private val catalog = CatalogToolHandler(repository)
    private val playback = PlaybackToolHandler(repository, player, state)
    private val personal = LibraryToolHandler(repository, library, downloads)
    private val favorites = FavoriteToolHandler(repository, library)
    private val executor = AgentToolExecutor(storage,
        claim = { run, call -> api.claim(run, call); Unit },
        perform = { call -> when {
            call.name == "query_library" -> personal.perform(call)
            call.name == "set_favorite" -> favorites.perform(call)
            call.name in CatalogToolHandler.names -> catalog.perform(call)
            else -> playback.perform(call)
        } },
        snapshot = state::read)

    suspend fun execute(run: String, call: AgentCall, conversationId: String = ""): AgentReceipt =
        executor.execute(run, call, conversationId)

    suspend fun unsubmittedReceipts(run: AgentRun): List<AgentReceipt> = executor.unsubmittedReceipts(run)
}

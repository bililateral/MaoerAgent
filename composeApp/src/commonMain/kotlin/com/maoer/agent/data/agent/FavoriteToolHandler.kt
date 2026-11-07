package com.maoer.agent.data.agent

import com.maoer.agent.data.library.ListeningLibrary
import com.maoer.agent.data.podcast.PodcastRepository
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.json.*

/** Library writes use verified catalog identities and the existing durable library. */
internal class FavoriteToolHandler(private val repository: PodcastRepository, private val library: ListeningLibrary) {
    suspend fun perform(call: AgentCall): JsonObject {
        val args = call.arguments
        require(args.keys.all { it in setOf("kind", "podcast_id", "episode_id", "favorite") })
        val kind = args.getValue("kind").jsonPrimitive.content
        val podcastId = args.getValue("podcast_id").jsonPrimitive.content
        val episodeId = args["episode_id"]?.jsonPrimitive?.content.orEmpty()
        val favorite = args.getValue("favorite").jsonPrimitive.boolean
        require(kind in setOf("podcast", "episode") && (kind == "episode") == episodeId.isNotEmpty())
        val source = repository.source(podcastId)
        return try {
            val title = if (kind == "podcast") {
                library.setBookmark(podcastId, favorite)
                source.title
            } else {
                val saved = library.entry(episodeId)?.audio?.takeIf { it.podcastId == podcastId }
                val audio = saved ?: run {
                    val feed = repository.cached(podcastId) ?: repository.refresh(podcastId)
                    feed.episodes.firstOrNull { it.id == episodeId }?.asAudio(feed)
                } ?: return agentToolError("未找到指定分集。", "episode_missing")
                library.setFavorite(audio, favorite)
                audio.title
            }
            val actual = if (kind == "podcast") podcastId in library.bookmarks.value
                else library.entry(episodeId)?.favorite == true
            buildJsonObject {
                put("status", if (actual == favorite) "ok" else "unknown")
                put("kind", kind); put("podcast_id", podcastId); put("episode_id", episodeId)
                put("favorite", actual); put("title", title.take(300))
                put("note", if (actual != favorite) "无法确认收藏状态。" else if (favorite) "已收藏。" else "已取消收藏。")
            }
        } catch (e: CancellationException) { throw e }
        catch (_: Exception) { agentToolError("收藏设置失败。", "favorite_write_failed") }
    }
}

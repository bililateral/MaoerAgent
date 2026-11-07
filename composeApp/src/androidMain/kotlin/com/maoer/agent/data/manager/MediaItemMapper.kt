package com.maoer.agent.data.manager

import android.net.Uri
import android.os.Bundle
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import com.maoer.agent.data.model.Audio

/** Media metadata for queued items; standalone playback uses the same current Audio model. */
internal fun Audio.toQueueMediaItem(playbackUri: String): MediaItem {
    val metadata = MediaMetadata.Builder()
        .setTitle(title)
        .setArtist(author)
        .setDescription(description.take(512))
        .setAlbumTitle(podcastId)
        .setExtras(Bundle().apply { putString("originalAudioUrl", audioUrl) })
        .setArtworkUri(Uri.parse(coverUrl))
        .build()
    return MediaItem.Builder().setMediaId(id).setUri(playbackUri).setMediaMetadata(metadata).build()
}

internal fun Audio.toStandaloneMediaItem(): MediaItem {
    val metadata = MediaMetadata.Builder().setTitle(title).setArtist(author)
        .setArtworkUri(Uri.parse(coverUrl)).build()
    return MediaItem.Builder().setMediaId(id).setUri(audioUrl).setMediaMetadata(metadata).build()
}

internal fun MediaItem.asAudio() = Audio(mediaId, mediaMetadata.title?.toString().orEmpty(),
    mediaMetadata.artist?.toString().orEmpty(), mediaMetadata.artworkUri?.toString().orEmpty(),
    audioUrl = mediaMetadata.extras?.getString("originalAudioUrl") ?: localConfiguration?.uri?.toString().orEmpty(),
    description = mediaMetadata.description?.toString().orEmpty(), podcastId = mediaMetadata.albumTitle?.toString().orEmpty())

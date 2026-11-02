package com.maoer.agent.di

import com.maoer.agent.data.manager.IosMediaPlayerController
import com.maoer.agent.data.manager.MediaPlayerController
import com.maoer.agent.data.download.Downloads
import com.maoer.agent.data.download.UnavailableDownloads
import org.koin.dsl.module

actual val platformModule = module {
    single<Downloads> { UnavailableDownloads() }
    single<MediaPlayerController> { IosMediaPlayerController() }
}

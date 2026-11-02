package com.maoer.agent.di

import com.maoer.agent.data.manager.AndroidMediaPlayerController
import com.maoer.agent.data.manager.MediaPlayerController
import com.maoer.agent.data.download.Downloads
import com.maoer.agent.data.download.AndroidDownloads
import org.koin.dsl.module

actual val platformModule = module {
    // Android 端注入真实的播放控制器：通过 MediaController 连接后台 Media3 Service。
    single<Downloads> { AndroidDownloads(get()) }
    single<MediaPlayerController> { AndroidMediaPlayerController(get()) }
}

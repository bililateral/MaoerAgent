package com.maoer.agent.data.local

import com.maoer.agent.MaoerApplication

actual fun getDataStorePath(): String {
    val context = MaoerApplication.instance
    // 使用 app 私有目录 filesDir，避免外部存储权限与多进程可见性问题。
    return context.filesDir.resolve(DATA_STORE_FILE_NAME).absolutePath
}

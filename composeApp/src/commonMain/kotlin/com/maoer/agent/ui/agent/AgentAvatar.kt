package com.maoer.agent.ui.agent

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.addPathNodes
import androidx.compose.ui.unit.dp

@Composable
internal fun AgentAvatar(modifier: Modifier = Modifier) {
    Image(avatar, contentDescription = "点播助手头像", modifier = modifier.size(36.dp))
}

// Gemini 3.8 Flash option D, selected by the user: 星芒共鸣.
private val avatar: ImageVector by lazy {
    val paper = SolidColor(Color(0xFFFAF7F2))
    val accent = SolidColor(Color(0xFFB83D36))
    ImageVector.Builder("AgentAvatar", 36.dp, 36.dp, 120f, 120f).apply {
        addPath(addPathNodes("M34 0 H86 A34 34 0 0 1 120 34 V86 A34 34 0 0 1 86 120 H34 A34 34 0 0 1 0 86 V34 A34 34 0 0 1 34 0 Z"), fill = paper)
        addPath(addPathNodes("M34 2 H86 A32 32 0 0 1 118 34 V86 A32 32 0 0 1 86 118 H34 A32 32 0 0 1 2 86 V34 A32 32 0 0 1 34 2 Z"),
            stroke = SolidColor(Color(0xFFEAE4DC)), strokeLineWidth = 1.5f)
        addPath(addPathNodes(circle(60f, 60f, 40f)), fill = SolidColor(Color(0xFFF4E6DF)), fillAlpha = 0.6f)
        addPath(addPathNodes("M33 67 C31 46 42 31 48 24 C51 29 56 36 60 40 C64 36 69 29 72 24 C78 31 89 46 87 67"),
            stroke = Brush.linearGradient(listOf(Color(0xFFC7443D), Color(0xFFDE6B59)), Offset(33f, 24f), Offset(87f, 67f)),
            strokeLineWidth = 4.5f, strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round)
        addPath(addPathNodes("M44 68 C43 57 49 48 53 43 C55 46 58 50 60 52 C62 50 65 46 67 43 C71 48 77 57 76 68"),
            stroke = accent, strokeAlpha = 0.45f, strokeLineWidth = 2.5f,
            strokeLineCap = StrokeCap.Round, strokeLineJoin = StrokeJoin.Round)
        addPath(addPathNodes("M60 51 Q60 63 72 63 Q60 63 60 75 Q60 63 48 63 Q60 63 60 51 Z"), fill = accent)
        addPath(addPathNodes(circle(60f, 63f, 2.5f)), fill = paper)
        listOf(48f to 0.4f, 54f to 0.7f, 60f to 1f, 66f to 0.7f, 72f to 0.4f).forEach { (x, alpha) ->
            addPath(addPathNodes(circle(x, 83f, 2.2f)), fill = accent, fillAlpha = alpha)
        }
    }.build()
}

private fun circle(x: Float, y: Float, radius: Float): String =
    "M${x - radius} $y A$radius $radius 0 1 0 ${x + radius} $y A$radius $radius 0 1 0 ${x - radius} $y Z"

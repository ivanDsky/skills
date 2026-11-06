package com.example.ui.tag

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/** Public defaults of [Tag] and [TagGroup]: callers that wrap them can reproduce every default. */
object TagDefaults {
    val MinHeight: Dp = 32.dp
    val IconSpacing: Dp = 8.dp
    val GroupSpacing: Dp = 8.dp
    val ContentPadding: PaddingValues = PaddingValues(horizontal = 12.dp)
    val Shape: Shape = RoundedCornerShape(8.dp)

    @Composable
    fun colors(
        containerColor: Color = MaterialTheme.colorScheme.surfaceVariant,
        contentColor: Color = MaterialTheme.colorScheme.onSurfaceVariant,
        selectedContainerColor: Color = MaterialTheme.colorScheme.secondaryContainer,
        selectedContentColor: Color = MaterialTheme.colorScheme.onSecondaryContainer,
    ): TagColors = TagColors(
        containerColor = containerColor,
        contentColor = contentColor,
        selectedContainerColor = selectedContainerColor,
        selectedContentColor = selectedContentColor,
    )
}

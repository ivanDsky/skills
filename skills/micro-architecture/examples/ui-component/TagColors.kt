package com.example.ui.tag

import androidx.compose.runtime.Immutable
import androidx.compose.ui.graphics.Color

/** Container and content colors of a [Tag], per selection state. Built by [TagDefaults.colors]. */
@Immutable
class TagColors(
    private val containerColor: Color,
    private val contentColor: Color,
    private val selectedContainerColor: Color,
    private val selectedContentColor: Color,
) {
    fun containerColor(selected: Boolean): Color =
        if (selected) selectedContainerColor else containerColor

    fun contentColor(selected: Boolean): Color =
        if (selected) selectedContentColor else contentColor

    // Value equality keeps Tag skippable when TagDefaults.colors() returns a new instance.
    override fun equals(other: Any?): Boolean =
        other is TagColors &&
            containerColor == other.containerColor &&
            contentColor == other.contentColor &&
            selectedContainerColor == other.selectedContainerColor &&
            selectedContentColor == other.selectedContentColor

    override fun hashCode(): Int {
        var result = containerColor.hashCode()
        result = 31 * result + contentColor.hashCode()
        result = 31 * result + selectedContainerColor.hashCode()
        result = 31 * result + selectedContentColor.hashCode()
        return result
    }
}

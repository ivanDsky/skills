package com.example.ui.tag

import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.Saver
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue

/**
 * Selection of a [TagGroup]: which keys are selected, capped at [maxSelected].
 * Plain UI-logic holder, no ViewModel; unit-test it without composing UI.
 */
@Stable
class TagGroupState(
    initialSelection: Set<String> = emptySet(),
    val maxSelected: Int = Int.MAX_VALUE,
) {
    var selection: Set<String> by mutableStateOf(initialSelection.take(maxSelected).toSet())
        private set

    val isFull: Boolean get() = selection.size >= maxSelected

    fun isSelected(key: String): Boolean = key in selection

    /** Selects or deselects [key]; selecting while [isFull] is ignored. */
    fun toggle(key: String) {
        selection = when {
            key in selection -> selection - key
            isFull -> selection
            else -> selection + key
        }
    }

    fun clear() {
        selection = emptySet()
    }

    companion object {
        /** Saves the selection only; [maxSelected] comes back from the call site. */
        fun Saver(maxSelected: Int): Saver<TagGroupState, *> = listSaver(
            save = { it.selection.toList() },
            restore = { TagGroupState(initialSelection = it.toSet(), maxSelected = maxSelected) },
        )
    }
}

/** Remembers a [TagGroupState] that survives configuration change and process death. */
@Composable
fun rememberTagGroupState(
    initialSelection: Set<String> = emptySet(),
    maxSelected: Int = Int.MAX_VALUE,
): TagGroupState = rememberSaveable(maxSelected, saver = TagGroupState.Saver(maxSelected)) {
    TagGroupState(initialSelection, maxSelected)
}

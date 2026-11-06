package com.example.ui.tag

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview

/**
 * Wrapping row of [Tag]s with capped multi-selection.
 *
 * @param tags the keys to show, also used as labels.
 * @param modifier applied to the root, first in the chain.
 * @param state selection holder; hoist it with [rememberTagGroupState] to read or reset it.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun TagGroup(
    tags: List<String>,
    modifier: Modifier = Modifier,
    state: TagGroupState = rememberTagGroupState(),
) {
    FlowRow(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(TagDefaults.GroupSpacing),
        verticalArrangement = Arrangement.spacedBy(TagDefaults.GroupSpacing),
    ) {
        tags.forEach { tag ->
            val selected = state.isSelected(tag)
            Tag(
                selected = selected,
                onSelectedChange = { state.toggle(tag) },
                label = { Text(tag) },
                enabled = selected || !state.isFull,
            )
        }
    }
}

@Preview
@Composable
private fun TagGroupCappedPreview() {
    MaterialTheme {
        TagGroup(
            tags = listOf("Kotlin", "Compose", "Koin", "Room"),
            state = TagGroupState(initialSelection = setOf("Kotlin", "Koin"), maxSelected = 2),
        )
    }
}

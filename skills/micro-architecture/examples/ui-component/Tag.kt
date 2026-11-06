package com.example.ui.tag

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ProvideTextStyle
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.tooling.preview.Preview

/**
 * Design-system tag: a selectable label with an optional leading icon, built on [BasicTag].
 *
 * @param selected whether the tag is selected; the caller owns this state.
 * @param onSelectedChange called with the requested new selection.
 * @param label the tag's text; any composable, styled with the tag's text style and color.
 * @param modifier applied to the root, first in the chain.
 * @param enabled whether the tag reacts to input.
 * @param leadingIcon optional icon before the label; `null` removes it and its spacing.
 * @param colors container and content colors per selection state.
 */
@Composable
fun Tag(
    selected: Boolean,
    onSelectedChange: (Boolean) -> Unit,
    label: @Composable () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    leadingIcon: (@Composable () -> Unit)? = null,
    colors: TagColors = TagDefaults.colors(),
) {
    BasicTag(
        selected = selected,
        onSelectedChange = onSelectedChange,
        modifier = modifier
            .heightIn(min = TagDefaults.MinHeight)
            .clip(TagDefaults.Shape)
            .background(colors.containerColor(selected))
            .padding(TagDefaults.ContentPadding),
        enabled = enabled,
    ) {
        CompositionLocalProvider(LocalContentColor provides colors.contentColor(selected)) {
            if (leadingIcon != null) {
                leadingIcon()
                Spacer(Modifier.width(TagDefaults.IconSpacing))
            }
            ProvideTextStyle(MaterialTheme.typography.labelLarge, label)
        }
    }
}

@Preview
@Composable
private fun TagSelectedPreview() {
    MaterialTheme { Tag(selected = true, onSelectedChange = {}, label = { Text("Selected") }) }
}

@Preview
@Composable
private fun TagUnselectedPreview() {
    MaterialTheme {
        Tag(
            selected = false,
            onSelectedChange = {},
            label = { Text("With icon") },
            leadingIcon = { Text("#") },
        )
    }
}

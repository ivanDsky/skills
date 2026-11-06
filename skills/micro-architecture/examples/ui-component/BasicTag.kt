package com.example.ui.tag

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.selection.toggleable
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.tooling.preview.Preview

/**
 * Unstyled toggleable row: selection semantics and click handling, no design opinion.
 * Wrap it to build a styled tag; [Tag] is the design-system version.
 *
 * @param selected whether the tag is selected; the caller owns this state.
 * @param onSelectedChange called with the requested new selection.
 * @param modifier applied to the root, first in the chain.
 * @param enabled whether the tag reacts to input.
 * @param content the row's children; [RowScope] lets callers weight or align them.
 */
@Composable
fun BasicTag(
    selected: Boolean,
    onSelectedChange: (Boolean) -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    content: @Composable RowScope.() -> Unit,
) {
    Row(
        modifier = modifier.toggleable(
            value = selected,
            enabled = enabled,
            role = Role.Checkbox,
            onValueChange = onSelectedChange,
        ),
        verticalAlignment = Alignment.CenterVertically,
        content = content,
    )
}

@Preview
@Composable
private fun BasicTagPreview() {
    BasicTag(selected = true, onSelectedChange = {}) { Text("Unstyled") }
}

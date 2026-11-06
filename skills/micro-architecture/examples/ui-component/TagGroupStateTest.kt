package com.example.ui.tag

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class TagGroupStateTest {

    @Test
    fun toggleSelectsThenDeselects() {
        val state = TagGroupState()
        state.toggle("kotlin")
        assertTrue(state.isSelected("kotlin"))
        state.toggle("kotlin")
        assertFalse(state.isSelected("kotlin"))
    }

    @Test
    fun selectingPastTheCapIsIgnored() {
        val state = TagGroupState(initialSelection = setOf("a", "b"), maxSelected = 2)
        state.toggle("c")
        assertEquals(setOf("a", "b"), state.selection)
        assertTrue(state.isFull)
    }

    @Test
    fun deselectingWhileFullFreesASlot() {
        val state = TagGroupState(initialSelection = setOf("a", "b"), maxSelected = 2)
        state.toggle("a")
        state.toggle("c")
        assertEquals(setOf("b", "c"), state.selection)
    }

    @Test
    fun initialSelectionIsTrimmedToTheCap() {
        val state = TagGroupState(initialSelection = setOf("a", "b", "c"), maxSelected = 2)
        assertEquals(2, state.selection.size)
    }
}

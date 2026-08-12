from pathlib import Path

header_path = Path("Source/PluginEditor.h")
cpp_path = Path("Source/PluginEditor.cpp")

if not header_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.h not found")

if not cpp_path.exists():
    raise SystemExit("ERROR: Source/PluginEditor.cpp not found")

header = header_path.read_text(encoding="utf-8")
cpp = cpp_path.read_text(encoding="utf-8")


# -----------------------------------------------------------------------------
# 1. Patch PluginEditor.h: add pitch-drag helper declaration.
# -----------------------------------------------------------------------------

old_header = '''    void startMelodyDurationDrag(int stepIndex, int midiNote);
    void updateMelodyDragDurationAtMousePosition(juce::Point<int> position);

    bool melodyStepRangeOverlapsExistingNote(int patternIndex,
'''

new_header = '''    void startMelodyDurationDrag(int stepIndex, int midiNote);
    void updateMelodyDragDurationAtMousePosition(juce::Point<int> position);
    void updateMelodyDragPitchAtMousePosition(juce::Point<int> position);

    bool melodyStepRangeOverlapsExistingNote(int patternIndex,
'''

if old_header not in header:
    raise SystemExit("ERROR: Could not patch PluginEditor.h pitch helper declaration")

header = header.replace(old_header, new_header, 1)
header_path.write_text(header, encoding="utf-8")


# -----------------------------------------------------------------------------
# Helper for replacing whole function by marker boundaries.
# -----------------------------------------------------------------------------

def replace_function(text, signature_start, next_function_start, replacement):
    start = text.find(signature_start)
    if start < 0:
        raise SystemExit(f"ERROR: Could not find function start: {signature_start}")

    end = text.find(next_function_start, start)
    if end < 0:
        raise SystemExit(f"ERROR: Could not find next function marker after: {signature_start}")

    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


# -----------------------------------------------------------------------------
# 2. Insert updateMelodyDragPitchAtMousePosition() after duration-drag function.
# -----------------------------------------------------------------------------

insert_marker = '''void MidiPatternLauncherAudioProcessorEditor::updateSelectedStepFromMousePosition(juce::Point<int> position)
'''

if "void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragPitchAtMousePosition(" in cpp:
    raise SystemExit("ERROR: updateMelodyDragPitchAtMousePosition() already exists")

pitch_drag_function = r'''void MidiPatternLauncherAudioProcessorEditor::updateMelodyDragPitchAtMousePosition(
    juce::Point<int> position)
{
    if (!isDraggingMelodyDuration)
        return;

    const int gridStepCount = audioProcessor.getGridStepCount();

    if (melodyDragPattern < 0 || melodyDragPattern >= 3)
        return;

    if (melodyDragStartStep < 0 || melodyDragStartStep >= gridStepCount)
        return;

    int hoverStepIndex = -1;
    int hoverMidiNote = -1;

    if (!getMelodyPaintCellAtPosition(position, hoverStepIndex, hoverMidiNote))
        return;

    const int velocity = audioProcessor.stepHasNote(melodyDragPattern, melodyDragStartStep)
        ? juce::jlimit(1, 127, audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep))
        : melodyDragOriginalVelocity;

    int requestedDuration = audioProcessor.stepHasNote(melodyDragPattern, melodyDragStartStep)
        ? juce::jlimit(1, gridStepCount - melodyDragStartStep, audioProcessor.getStepDurationSteps(melodyDragPattern, melodyDragStartStep))
        : melodyDragOriginalDuration;

    if (melodyEditDragMode == MelodyEditDragMode::MoveExistingPitchAndDuration)
    {
        const int endStep = juce::jlimit(melodyDragStartStep, gridStepCount - 1, hoverStepIndex);

        requestedDuration = juce::jlimit(
            1,
            gridStepCount - melodyDragStartStep,
            endStep - melodyDragStartStep + 1);
    }

    applyMelodyNoteEditSafely(
        melodyDragPattern,
        melodyDragStartStep,
        hoverMidiNote,
        velocity,
        requestedDuration,
        melodyDragStartStep);
}

'''

if insert_marker not in cpp:
    raise SystemExit("ERROR: Could not find insertion marker for pitch drag function")

cpp = cpp.replace(insert_marker, pitch_drag_function + insert_marker, 1)


# -----------------------------------------------------------------------------
# 3. Patch mouseDown() Melody branch.
# -----------------------------------------------------------------------------

old_mouse_down_block = '''        if (getMelodyPaintCellAtPosition(position, melodyStepIndex, melodyMidiNote))
        {
            const bool rightClickErase = event.mods.isRightButtonDown();

            if (rightClickErase)
            {
                dragPaintValue = false;
                isDraggingPatternStepEdit = true;
                setMelodyPaintCellValue(melodyStepIndex, melodyMidiNote, false);
            }
            else
            {
                dragPaintValue = true;
                isDraggingPatternStepEdit = false;
                startMelodyDurationDrag(melodyStepIndex, melodyMidiNote);
            }

            return;
        }
'''

new_mouse_down_block = '''        if (getMelodyPaintCellAtPosition(position, melodyStepIndex, melodyMidiNote))
        {
            const bool rightClickErase = event.mods.isRightButtonDown();
            const bool shiftDown = event.mods.isShiftDown();
            const bool altDown = event.mods.isAltDown();

            const int melodyPattern = getDisplayedPattern();
            const int existingNoteStart = findMelodyNoteStartAtCell(
                melodyPattern,
                melodyStepIndex,
                melodyMidiNote);

            if (rightClickErase)
            {
                dragPaintValue = false;
                isDraggingPatternStepEdit = true;
                setMelodyPaintCellValue(melodyStepIndex, melodyMidiNote, false);
            }
            else if (altDown && existingNoteStart >= 0)
            {
                melodyDragPattern = melodyPattern;
                melodyDragStartStep = existingNoteStart;
                melodyDragStartNote = audioProcessor.getStepNote(melodyDragPattern, melodyDragStartStep);

                melodyDragOriginalStep = melodyDragStartStep;
                melodyDragOriginalNote = melodyDragStartNote;
                melodyDragOriginalDuration = juce::jlimit(
                    1,
                    audioProcessor.getGridStepCount(),
                    audioProcessor.getStepDurationSteps(melodyDragPattern, melodyDragStartStep));
                melodyDragOriginalVelocity = juce::jlimit(
                    1,
                    127,
                    audioProcessor.getStepVelocity(melodyDragPattern, melodyDragStartStep));

                isDraggingMelodyDuration = true;
                isDraggingPatternStepEdit = false;
                melodyEditDragMode = shiftDown
                    ? MelodyEditDragMode::MoveExistingPitchAndDuration
                    : MelodyEditDragMode::MoveExistingPitch;

                selectedEditPattern = melodyDragPattern;
                selectedStep = melodyDragStartStep;

                audioProcessor.setTargetPatternAndStep(selectedEditPattern, selectedStep);
                audioProcessor.updateTargetParametersFromStep();

                updateEditPatternButtonHighlights();
                repaint();
            }
            else
            {
                dragPaintValue = true;
                isDraggingPatternStepEdit = false;

                startMelodyDurationDrag(melodyStepIndex, melodyMidiNote);

                if (shiftDown && existingNoteStart >= 0)
                    melodyEditDragMode = MelodyEditDragMode::ResizeExistingDuration;
            }

            return;
        }
'''

if old_mouse_down_block not in cpp:
    raise SystemExit("ERROR: Could not patch mouseDown() Melody cell block")

cpp = cpp.replace(old_mouse_down_block, new_mouse_down_block, 1)


# -----------------------------------------------------------------------------
# 4. Patch mouseDrag() Melody branch to route pitch edit modes.
# -----------------------------------------------------------------------------

old_mouse_drag_block = '''        if (isDraggingMelodyDuration)
        {
            updateMelodyDragDurationAtMousePosition(event.getPosition());
            return;
        }
'''

new_mouse_drag_block = '''        if (isDraggingMelodyDuration)
        {
            if (melodyEditDragMode == MelodyEditDragMode::MoveExistingPitch
                || melodyEditDragMode == MelodyEditDragMode::MoveExistingPitchAndDuration)
            {
                updateMelodyDragPitchAtMousePosition(event.getPosition());
                return;
            }

            updateMelodyDragDurationAtMousePosition(event.getPosition());
            return;
        }
'''

if old_mouse_drag_block not in cpp:
    raise SystemExit("ERROR: Could not patch mouseDrag() Melody duration block")

cpp = cpp.replace(old_mouse_drag_block, new_mouse_drag_block, 1)


cpp_path.write_text(cpp, encoding="utf-8")

print("v1.16.0 Patch 3 applied: Alt pitch edit and Alt+Shift pitch-duration edit.")
